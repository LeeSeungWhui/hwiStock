"""
Focused runtime tests for the file-driven Pro/Flash AI analysis runner.

No real provider, browser, broker, or KIS network calls are made.
"""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sys

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import ai_analysis_runtime as runtime  # noqa: E402
from lib import ai_orchestration as ao  # noqa: E402


MAX_TOKEN_ENV_NAMES = [
    "HWISTOCK_DEEPSEEK_MAX_TOKENS_OVERRIDE",
    "HWISTOCK_DEEPSEEK_PRO_MAX_TOKENS_OVERRIDE",
    "HWISTOCK_DEEPSEEK_FLASH_MAX_TOKENS_OVERRIDE",
    "HWISTOCK_DEEPSEEK_LEGACY_MAX_TOKENS_OVERRIDE",
    "HWISTOCK_AI_MAX_OUTPUT_TOKENS",
    "HWISTOCK_DEEPSEEK_PRO_MAX_TOKENS",
    "HWISTOCK_DEEPSEEK_FLASH_MAX_TOKENS",
    "HWISTOCK_DEEPSEEK_LEGACY_MAX_TOKENS",
]


class _FakeDeepSeekResponse:
    status = 200

    def __init__(self, content: dict | None = None):
        self.content = content or {
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(_pro_v1_payload(), ensure_ascii=False)}}],
            "model": "deepseek-v4-pro",
            "usage": {"completion_tokens": 10},
        }

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.content, ensure_ascii=False).encode("utf-8")


def _clear_max_token_envs(monkeypatch) -> None:
    for name in MAX_TOKEN_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def _capture_deepseek_request(monkeypatch) -> list[dict]:
    captured: list[dict] = []

    def _fake_urlopen(request, timeout):  # noqa: ARG001
        captured.append(json.loads(request.data.decode("utf-8")))
        return _FakeDeepSeekResponse()

    monkeypatch.setenv("DEEPSEEK_API_KEY", "unit-test-key")
    monkeypatch.setattr(runtime.urllib.request, "urlopen", _fake_urlopen)
    return captured


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_calendar(path: Path, *, day: str, trading: bool) -> None:
    path.write_text(
        json.dumps(
            {
                "validUntil": "2099-12-31T23:59:59+09:00",
                "sourceAuthority": "unit_test_calendar",
                "days": {
                    day: {
                        "dateKst": day,
                        "isTradingDay": trading,
                        "reason": "weekend" if not trading else None,
                        "krx": {
                            "regularOpen": "09:00",
                            "regularClose": "15:30",
                            "orderOpen": "09:00",
                            "orderClose": "15:00",
                        },
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _write_calendar_days(path: Path, days: dict[str, dict]) -> None:
    normalized = {}
    for day, row in days.items():
        payload = {
            "dateKst": day,
            "isTradingDay": bool(row.get("trading", row.get("isTradingDay", False))),
            "reason": row.get("reason"),
            "krx": {
                "regularOpen": row.get("regularOpen", "09:00"),
                "regularClose": row.get("regularClose", "15:30"),
                "orderOpen": row.get("orderOpen", "09:00"),
                "orderClose": row.get("orderClose", "15:00"),
            },
        }
        normalized[day] = payload
    path.write_text(
        json.dumps(
            {
                "validUntil": "2099-12-31T23:59:59+09:00",
                "sourceAuthority": "unit_test_calendar",
                "days": normalized,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_provider_prompts_require_korean_natural_language_values():
    events = [{"event_id": "event-1", "title": "삼성전자 반도체 투자 확대", "event_type": "news"}]
    kis_snapshots = [{"artifact_id": "snap-1", "status": "ok", "input_results": []}]
    pro_prompt = runtime._build_pro_hourly_prompt(  # noqa: SLF001
        events,
        kis_snapshots,
        produced_at_kst="2026-06-08T09:00:00+09:00",
    )
    flash_prompt = runtime._build_flash_prompt(  # noqa: SLF001
        pro_artifact={"artifact_id": "art_pro", "summary": "프로 분석"},
        events=events,
        kis_snapshots=kis_snapshots,
        compiled_watch=[{"symbol": "005930", "name": "삼성전자"}],
        portfolio={},
        order_state={},
        produced_at_kst="2026-06-08T09:10:00+09:00",
    )

    assert "단순 뉴스 요약 금지" in pro_prompt
    assert "pro_hourly_market_analysis/v1" in pro_prompt
    assert "다음 10분 매매문서" in flash_prompt
    assert "flash_trade_document/v1" in flash_prompt


def test_default_order_state_snapshot_includes_reconciled_holdings(tmp_path: Path):
    data_root = tmp_path / "data"
    state_path = data_root / "state" / "kis-paper-runner-state.json"
    _write_json(
        state_path,
        {
            "schema_version": "kis_paper_runner_state/v0",
            "pending_orders": [],
            "holdings": [
                {
                    "symbol": "005930",
                    "position_state": "holding_confirmed",
                    "quantity": 2,
                    "target_price": 72100,
                    "stop_loss_price": 67900,
                }
            ],
            "active_exits": [{"symbol": "005930", "side": "sell"}],
            "consumed_intent_keys": ["intent-1"],
        },
    )
    now = datetime.fromisoformat("2026-06-08T09:10:00+09:00")

    snapshot = runtime._default_order_state_snapshot(now, data_root=data_root)  # noqa: SLF001

    assert snapshot["pending_orders"] == []
    assert snapshot["holdings"][0]["symbol"] == "005930"
    assert snapshot["holdings"][0]["position_state"] == "holding_confirmed"
    assert snapshot["active_exits"][0]["symbol"] == "005930"
    assert snapshot["consumed_intent_keys"] == ["intent-1"]
    assert snapshot["consumed_trade_document_ids"] == []
    assert snapshot["legacy_consumed_trade_document_ids"] == []


def test_default_order_state_snapshot_ignores_legacy_consumed_trade_document_ids_for_siblings(tmp_path: Path):
    data_root = tmp_path / "data"
    state_path = data_root / "state" / "kis-paper-runner-state.json"
    _write_json(
        state_path,
        {
            "schema_version": "kis_paper_runner_state/v0",
            "pending_orders": [],
            "holdings": [],
            "active_exits": [],
            "consumed_intent_keys": ["intent-1"],
            "consumed_trade_document_ids": ["flash-same-doc"],
        },
    )
    now = datetime.fromisoformat("2026-06-08T09:10:00+09:00")

    snapshot = runtime._default_order_state_snapshot(now, data_root=data_root)  # noqa: SLF001

    assert snapshot["consumed_intent_keys"] == ["intent-1"]
    assert snapshot["consumed_trade_document_ids"] == []
    assert snapshot["legacy_consumed_trade_document_ids"] == ["flash-same-doc"]
    assert snapshot["legacy_consumed_trade_document_ids_ignored_for_sibling_intents"] is True


def test_deepseek_payload_omits_max_tokens_by_default(monkeypatch):
    _clear_max_token_envs(monkeypatch)
    captured = _capture_deepseek_request(monkeypatch)

    provider = runtime._call_deepseek("{}", model="deepseek-v4-pro", job="pro-hourly")  # noqa: SLF001

    assert captured
    assert "max_tokens" not in captured[0]
    assert provider["request"]["max_tokens_sent"] is False
    assert provider["request"]["max_tokens_source_env"] is None


def test_explicit_max_tokens_override_is_respected(monkeypatch):
    _clear_max_token_envs(monkeypatch)
    monkeypatch.setenv("HWISTOCK_DEEPSEEK_PRO_MAX_TOKENS_OVERRIDE", "7777")
    captured = _capture_deepseek_request(monkeypatch)

    provider = runtime._call_deepseek("{}", model="deepseek-v4-pro", job="pro-hourly")  # noqa: SLF001

    assert captured[0]["max_tokens"] == 7777
    assert provider["request"]["max_tokens_sent"] is True
    assert provider["request"]["max_tokens_source_env"] == "HWISTOCK_DEEPSEEK_PRO_MAX_TOKENS_OVERRIDE"
    assert provider["warnings"] == []


def test_systemd_services_do_not_set_ai_max_output_tokens():
    service_paths = [
        Path("ops/systemd/user/hwistock-ai-analysis.service"),
        Path("ops/systemd/user/hwistock-ai-flash.service"),
    ]
    forbidden = {
        "HWISTOCK_AI_MAX_OUTPUT_TOKENS",
        "HWISTOCK_DEEPSEEK_PRO_MAX_TOKENS",
        "HWISTOCK_DEEPSEEK_FLASH_MAX_TOKENS",
    }

    for path in service_paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text


def test_flash_timer_runs_only_paper_krx_decision_window():
    text = Path("ops/systemd/user/hwistock-ai-flash.timer").read_text(encoding="utf-8")

    assert "OnCalendar=Mon..Fri *-*-* 09..14:00/10:00" in text
    assert "OnCalendar=*:0/10" not in text
    assert "OnBootSec=" not in text
    assert "Persistent=false" in text


def test_legacy_global_max_tokens_env_adds_deprecated_warning(tmp_path: Path, monkeypatch):
    _clear_max_token_envs(monkeypatch)
    monkeypatch.setenv("HWISTOCK_AI_MAX_OUTPUT_TOKENS", "3333")
    captured = _capture_deepseek_request(monkeypatch)
    now = datetime.fromisoformat("2026-06-08T09:00:00+09:00")
    calendar = tmp_path / "calendar.json"
    _write_calendar(calendar, day="2026-06-08", trading=True)
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(calendar))
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-08" / "events.jsonl",
        [{"event_id": "event-1", "title": "삼성전자 투자 확대", "published_at_kst": "2026-06-08T08:50:00+09:00"}],
    )

    result = runtime.run_pro_hourly_once(data_root=tmp_path, at=now, model="deepseek-v4-pro")

    assert captured[0]["max_tokens"] == 3333
    assert result["provider"]["request"]["max_tokens_sent"] is True
    assert result["provider"]["request"]["max_tokens_source_env"] == "HWISTOCK_AI_MAX_OUTPUT_TOKENS"
    assert "deprecated_max_tokens_env:HWISTOCK_AI_MAX_OUTPUT_TOKENS" in result["warnings"]


def test_weekend_pro_hourly_downgrades_provider_kis_failure_claim(tmp_path: Path, monkeypatch):
    now = datetime.fromisoformat("2026-06-06T10:00:00+09:00")
    calendar = tmp_path / "calendar.json"
    _write_calendar(calendar, day="2026-06-06", trading=False)
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(calendar))
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-06" / "events.jsonl",
        [{"event_id": "event-1", "title": "주말 점검 뉴스", "published_at_kst": "2026-06-06T09:10:00+09:00"}],
    )
    monkeypatch.setattr(
        runtime,
        "_call_deepseek",
        lambda *_args, **_kwargs: {
            "http_status": 200,
            "finish_reason": "stop",
            "model": "deepseek-v4-pro",
            "text": json.dumps(
                {
                    "summary": "KIS 실시간 데이터 미수신 장애",
                    "market_mode": "NO_TRADE",
                    "themes": ["점검"],
                    "risk_flags": ["KIS realtime failure"],
                    "order_safety": "no_order",
                },
                ensure_ascii=False,
            ),
            "usage": None,
            "error": None,
        },
    )

    result = runtime.run_pro_hourly_once(data_root=tmp_path, at=now, model="deepseek-v4-pro")

    assert result["calendar_context"]["kis_realtime_expected"] is False
    assert "provider_misclassified_expected_off_session_as_kis_failure" in result["warnings"]
    assert result["summary"] == "장 운영시간 밖이라 KIS 실시간 부재는 정상 상태로 처리했습니다."
    assert result["risk_flags"] == []
    assert result["investment_utility_status"] == "news_only_low_utility"


def test_publish_morning_watchlist_writes_target_trade_date_latest_paths(tmp_path: Path):
    produced_at = datetime.fromisoformat("2026-06-07T11:55:00+09:00")
    result = runtime.publish_morning_watchlist_artifact(
        payload={
            "schema_version": "morning_watchlist/v1",
            "artifact_id": "art_morning_watchlist_20260608_sunday",
            "route": "codex_cli_local_browser_use",
            "target_trade_date_kst": "2026-06-08",
            "reviewer": "chatgpt_pro",
            "analysis_language": "ko-KR",
            "generated_at_kst": "2026-06-07T11:33:00+09:00",
            "purpose": "monday_preopen_rehearsal_late",
            "requires_monday_refresh": True,
            "forbidden_actions_acknowledged": True,
            "market_open_plan": {
                "opening_bias": "selective_watch",
                "why": "주말 뉴스 이월 후보를 장초 확인합니다",
                "must_wait_for_market_confirmation": True,
                "first_flash_questions": ["거래대금이 붙는가?"],
            },
            "items": [
                {
                    "ticker": "005930",
                    "stance": "eligible_for_flash_review",
                    "thesis": "반도체 투자 뉴스 확인",
                    "opening_trigger_conditions": ["거래대금 상위 진입"],
                    "invalidation_conditions": ["거래대금 미발생"],
                    "source_refs": ["event-1"],
                    "confidence": 0.6,
                }
            ],
        },
        data_root=tmp_path,
        target_trade_date="2026-06-08",
        at=produced_at,
    )

    assert result["validation_status"] == "accepted"
    assert result["target_trade_date_kst"] == "2026-06-08"
    for path in (
        tmp_path / "morning-watchlist" / "2026-06-08" / "morning-watchlist-latest.json",
        tmp_path / "ai" / "2026-06-08" / "morning-watchlist-latest.json",
    ):
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["artifact_id"] == "art_morning_watchlist_20260608_sunday"
        assert payload["target_trade_date_kst"] == "2026-06-08"


def test_build_morning_watchlist_prompt_writes_default_prompt_paths(tmp_path: Path, monkeypatch):
    produced_at = datetime.fromisoformat("2026-06-07T20:00:00+09:00")
    calendar = tmp_path / "calendar.json"
    _write_calendar(calendar, day="2026-06-08", trading=True)
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(calendar))
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-07" / "events.jsonl",
        [
            {
                "event_id": "event-1",
                "event_type": "news",
                "title": "삼성전자 반도체 투자 확대",
                "published_at_kst": "2026-06-07T19:30:00+09:00",
            }
        ],
    )
    _write_json(
        tmp_path / "ai" / "2026-06-07" / "pro-hourly-latest.json",
        {
            "schema_version": "pro_hourly_market_analysis/v1",
            "artifact_id": "art_pro_hourly_20260607_2000",
            "produced_at_kst": "2026-06-07T20:00:00+09:00",
            "validation_status": "accepted",
            "summary": "반도체 뉴스와 거래대금 확인 필요",
            "market_regime": {"mode": "NEUTRAL", "confidence": 0.4},
            "theme_map": [{"theme": "반도체", "source_refs": ["event-1"]}],
        },
    )
    _write_json(
        tmp_path / "compiled-watch" / "2026-06-07" / "compiled-watch-latest.json",
        {
            "schema_version": "compiled_watch/v0",
            "items": [{"symbol": "005930", "name": "삼성전자", "source_ids": ["event-1"]}],
        },
    )

    result = runtime.build_morning_watchlist_prompt(
        data_root=tmp_path,
        target_trade_date="2026-06-08",
        at=produced_at,
        purpose="morning_watchlist_0715_local_browser_use",
    )

    assert result["status"] == "ok"
    assert result["schema_version"] == "gpt_morning_prompt/v0"
    assert result["input_counts"]["pro_hourly_artifacts"] == 1
    for path in (
        tmp_path / "ai" / "2026-06-08" / "gpt-morning-prompt-latest.txt",
        tmp_path / "prompts" / "2026-06-08" / "gpt-morning-watchlist-latest.txt",
    ):
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "morning_watchlist/v1" in text
        assert "strict JSON object" in text
        assert "art_pro_hourly_20260607_2000" in text
        assert "broker API 호출, 주문 제출" in text
        assert "top-level `items` 키를 리스트로 사용" in text
        assert "top-level `eligible_for_flash_review` 키는 만들지 마" in text
    assert Path(result["health_path"]).is_file()


def test_gpt_morning_input_window_uses_previous_trading_close_for_monday(tmp_path: Path, monkeypatch):
    produced_at = datetime.fromisoformat("2026-06-08T07:15:00+09:00")
    calendar = tmp_path / "calendar.json"
    _write_calendar_days(
        calendar,
        {
            "2026-06-05": {"trading": True},
            "2026-06-06": {"trading": False, "reason": "weekend"},
            "2026-06-07": {"trading": False, "reason": "weekend"},
            "2026-06-08": {"trading": True},
        },
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(calendar))
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-05" / "events.jsonl",
        [
            {"event_id": "before-close", "title": "장중 제외", "published_at_kst": "2026-06-05T14:50:00+09:00"},
            {"event_id": "after-close", "title": "금요일 투자 close 이후 포함", "published_at_kst": "2026-06-05T15:10:00+09:00"},
        ],
    )
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-07" / "events.jsonl",
        [{"event_id": "weekend-news", "title": "주말 뉴스 포함", "published_at_kst": "2026-06-07T11:00:00+09:00"}],
    )
    _write_json(
        tmp_path / "ai" / "2026-06-05" / "pro-hourly-152000.json",
        {"schema_version": "pro_hourly_market_analysis/v1", "artifact_id": "pro-before", "produced_at_kst": "2026-06-05T14:50:00+09:00"},
    )
    _write_json(
        tmp_path / "ai" / "2026-06-07" / "pro-hourly-200000.json",
        {"schema_version": "pro_hourly_market_analysis/v1", "artifact_id": "pro-weekend", "produced_at_kst": "2026-06-07T20:00:00+09:00"},
    )

    result = runtime.build_morning_watchlist_prompt(
        data_root=tmp_path,
        target_trade_date="2026-06-08",
        at=produced_at,
    )
    prompt = (tmp_path / "ai" / "2026-06-08" / "gpt-morning-prompt-latest.txt").read_text(encoding="utf-8")
    health = json.loads(Path(result["health_path"]).read_text(encoding="utf-8"))

    assert result["input_window_start_kst"] == "2026-06-05T15:00:00+09:00"
    assert result["input_window_end_kst"] == "2026-06-08T07:15:00+09:00"
    assert result["included_dates"] == ["2026-06-05", "2026-06-06", "2026-06-07", "2026-06-08"]
    assert result["non_trading_day_carryover"] is True
    assert health["input_window_start_kst"] == result["input_window_start_kst"]
    assert health["input_window_end_kst"] == result["input_window_end_kst"]
    assert health["included_dates"] == result["included_dates"]
    assert health["non_trading_day_carryover"] is True
    assert "after-close" in prompt
    assert "weekend-news" in prompt
    assert "before-close" not in prompt
    assert "pro-weekend" in prompt
    assert "pro-before" not in prompt


def test_default_calendar_supports_20260608_monday_morning_window(monkeypatch):
    monkeypatch.delenv("HWISTOCK_CALENDAR_PATH", raising=False)
    produced_at = datetime.fromisoformat("2026-06-08T07:15:00+09:00")

    result = runtime._morning_prompt_input_window(  # noqa: SLF001
        target_trade_date="2026-06-08",
        at=produced_at,
    )

    assert result["window_source"] == "calendar_previous_trading_close"
    assert result["input_window_start_kst"] == "2026-06-05T15:00:00+09:00"
    assert result["input_window_end_kst"] == "2026-06-08T07:15:00+09:00"
    assert result["included_dates"] == ["2026-06-05", "2026-06-06", "2026-06-07", "2026-06-08"]
    assert result["non_trading_day_carryover"] is True
    assert result["previous_trading_day"] == "2026-06-05"


def test_gpt_morning_input_window_handles_long_weekend_previous_trading_close(tmp_path: Path, monkeypatch):
    produced_at = datetime.fromisoformat("2026-06-09T07:15:00+09:00")
    calendar = tmp_path / "calendar.json"
    _write_calendar_days(
        calendar,
        {
            "2026-06-05": {"trading": True},
            "2026-06-06": {"trading": False, "reason": "weekend"},
            "2026-06-07": {"trading": False, "reason": "weekend"},
            "2026-06-08": {"trading": False, "reason": "holiday"},
            "2026-06-09": {"trading": True},
        },
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(calendar))
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-08" / "events.jsonl",
        [{"event_id": "holiday-carryover", "title": "휴일 이월 뉴스", "published_at_kst": "2026-06-08T12:00:00+09:00"}],
    )

    result = runtime.build_morning_watchlist_prompt(
        data_root=tmp_path,
        target_trade_date="2026-06-09",
        at=produced_at,
    )
    prompt = (tmp_path / "ai" / "2026-06-09" / "gpt-morning-prompt-latest.txt").read_text(encoding="utf-8")

    assert result["input_window_start_kst"] == "2026-06-05T15:00:00+09:00"
    assert result["included_dates"] == ["2026-06-05", "2026-06-06", "2026-06-07", "2026-06-08", "2026-06-09"]
    assert result["non_trading_day_carryover"] is True
    assert "holiday-carryover" in prompt


def test_flash_runtime_uses_exact_10m_window_and_provider_actions(tmp_path: Path, monkeypatch):
    now = datetime.fromisoformat("2026-06-08T09:00:00+09:00")
    calendar = tmp_path / "calendar.json"
    _write_calendar(calendar, day="2026-06-08", trading=True)
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(calendar))
    _write_json(
        tmp_path / "ai" / "2026-06-08" / "pro-hourly-latest.json",
        {
            "schema_version": "pro_hourly_market_analysis/v1",
            "artifact_id": "art_pro_hourly_20260608_0900",
            "validation_status": "accepted",
            "investment_utility_status": "actionable_context",
            "market_regime": {"mode": "NEUTRAL", "confidence": 0.5},
            "flash_guidance": {"preferred_bias": "selective_watch"},
        },
    )
    _write_json(
        tmp_path / "morning-watchlist" / "2026-06-08" / "morning-watchlist-latest.json",
        {
            "schema_version": "morning_watchlist/v1",
            "artifact_id": "art_morning_watchlist_20260608_0715",
            "route": "codex_cli_local_browser_use",
            "target_trade_date_kst": "2026-06-08",
            "reviewer": "chatgpt_pro",
            "generated_at_kst": "2026-06-08T07:15:00+09:00",
            "forbidden_actions_acknowledged": True,
            "market_open_plan": {
                "opening_bias": "selective_watch",
                "why": "장초 확인",
                "must_wait_for_market_confirmation": True,
                "first_flash_questions": ["거래대금 확인"],
            },
            "items": [
                {
                    "ticker": "005930",
                    "stance": "eligible_for_flash_review",
                    "thesis": "반도체 뉴스",
                    "opening_trigger_conditions": ["거래대금 상위"],
                    "invalidation_conditions": ["스프레드 과도"],
                    "source_refs": ["event-new"],
                    "confidence": 0.7,
                }
            ],
        },
    )
    _write_json(
        tmp_path / "compiled-watch" / "2026-06-08" / "compiled-watch-latest.json",
        {
            "schema_version": "compiled_watch/v0",
            "items": [
                {
                    "schema_version": "compiled_watch/v0",
                    "artifact_id": "art_watch_005930",
                    "symbol": "005930",
                    "source_ids": ["event-new"],
                    "entry_intent": {
                        "entry_zone": [10000, 10100],
                        "take_profit": 10500,
                        "stop_loss": 9800,
                        "position_size_pct": 10,
                    },
                    "valid_until_kst": "2026-06-08T09:10:00+09:00",
                }
            ],
        },
    )
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-08" / "events.jsonl",
        [
            {"event_id": "event-old", "title": "old", "published_at_kst": "2026-06-08T08:45:00+09:00"},
            {"event_id": "event-new", "title": "new", "published_at_kst": "2026-06-08T08:55:00+09:00"},
        ],
    )
    _write_json(
        tmp_path / "kis-market" / "2026-06-08" / "old.json",
        {"schema_version": "kis_market_snapshot/v0", "artifact_id": "snap-old", "produced_at_kst": "2026-06-08T08:45:00+09:00"},
    )
    _write_json(
        tmp_path / "kis-market" / "2026-06-08" / "new.json",
        {"schema_version": "kis_market_snapshot/v0", "artifact_id": "snap-new", "produced_at_kst": "2026-06-08T08:55:00+09:00"},
    )

    monkeypatch.setattr(
        runtime,
        "_call_deepseek",
        lambda *_args, **_kwargs: {
            "http_status": 200,
            "finish_reason": "stop",
            "model": "deepseek-v4-flash",
            "text": json.dumps(
                {
                    "summary": "provider action",
                    "actions": [
                        {
                            "symbol": "005930",
                            "action": "BUY_NOW",
                            "entry_price_limit": 10200,
                            "target_price": 11000,
                            "stop_loss_price": 9900,
                            "planned_order_cash_krw": 120000,
                            "quantity": 11,
                            "confidence": 0.72,
                            "urgency": "medium",
                            "thesis": "거래대금 확인 기반 진입 후보",
                            "why_now": "개장 직후 수급 확인 구간",
                            "required_confirmations": ["KRX 호가 확인"],
                            "cancel_if": ["거래대금이 붙지 않으면 취소"],
                            "reason": "provider-selected next 10m action",
                        }
                    ],
                }
            ),
            "usage": None,
            "error": None,
        },
    )

    result = runtime.run_flash_trade_document_once(data_root=tmp_path, at=now, model="deepseek-v4-flash")

    assert result["validation_status"] == "accepted"
    assert result["input_window_kst"] == {
        "start_kst": "2026-06-08T08:50:00+09:00",
        "end_kst": "2026-06-08T09:00:00+09:00",
    }
    assert result["source_refs"] == ["event-new"]
    assert result["market_data_refs"] == ["snap-new"]
    assert result["actions"][0]["action_source"] == "deepseek_flash_provider"
    assert result["actions"][0]["action"] == "BUY_NOW"
    assert result["actions"][0]["entry_price_limit"] == 10200
    assert result["actions"][0]["target_price"] == 11000
    assert result["actions"][0]["stop_loss_price"] == 9900
    assert result["actions"][0]["position_size_pct"] == 10
    assert result["actions"][0]["planned_order_cash_krw"] == 0
    assert result["paper_intent_pipeline"]["accepted_count"] == 1
    intent = result["paper_intent_pipeline"]["accepted_intents"][0]
    assert intent["planned_order_cash_source"] == "position_size_pct"
    assert intent["planned_order_cash_krw"] == 200000


def _pro_v1_payload(**overrides):
    payload = {
        "schema_version": "pro_hourly_market_analysis/v1",
        "document_kind": "MARKET_STRATEGY_CONTEXT",
        "analysis_language": "ko-KR",
        "order_safety": "no_order",
        "ai_direct_order_allowed": False,
        "input_window_kst": {
            "start_kst": "2026-06-08T09:00:00+09:00",
            "end_kst": "2026-06-08T10:00:00+09:00",
            "window_seconds": 3600,
        },
        "data_quality": {
            "news_event_count": 1,
            "kis_market_snapshot_count": 1,
            "kis_data_status": "ok",
            "runtime_kis_failure_evidence_present": False,
            "missing_inputs": [],
            "warnings": [],
        },
        "market_regime": {
            "mode": "NEUTRAL",
            "confidence": 0.52,
            "why": [{"claim": "거래대금 확인 필요", "source_refs": ["event-1"], "market_data_refs": ["snap-1"]}],
        },
        "theme_map": [
            {
                "theme": "반도체",
                "direction": "positive_watch",
                "strength": 0.6,
                "freshness": "last_1h",
                "affected_groups": ["대형 반도체"],
                "avoid_groups": [],
                "why_it_matters": "뉴스와 시장 반응을 함께 확인해야 합니다",
                "source_refs": ["event-1"],
                "market_data_refs": ["snap-1"],
                "market_confirmation_status": "confirmed",
                "confirmation_signals_for_flash": ["거래대금 상위 진입"],
            }
        ],
        "flash_guidance": {
            "preferred_bias": "selective_watch",
            "max_aggression": "low",
            "candidate_focus": ["005930"],
            "avoid_focus": [],
            "must_check_before_buy": ["KRX 호가 확인"],
            "position_management_notes": [],
        },
        "no_trade_conditions": [],
        "contradiction_notes": [],
        "source_ref_map": [{"claim": "반도체 뉴스", "source_refs": ["event-1"], "market_data_refs": ["snap-1"], "confidence": 0.6}],
        "questions_for_next_flash": ["거래대금이 붙는가?"],
        "investment_utility_status": "actionable_context",
    }
    payload.update(overrides)
    return payload


def test_summary_only_pro_json_is_low_utility():
    result = ao.validateProHourlyMarketAnalysis(
        {
            "summary": "뉴스 요약입니다",
            "themes": ["반도체"],
            "risk_flags": ["변동성"],
            "order_safety": "no_order",
        }
    )

    assert result["ok"] is True
    assert result["document"]["validation_status"] == "accepted_with_warnings"
    assert result["document"]["investment_utility_status"] == "news_only_low_utility"
    assert "pro_hourly_low_utility_news_only" in result["warnings"]


def test_pro_v1_strategy_context_is_accepted():
    result = ao.validateProHourlyMarketAnalysis(_pro_v1_payload())

    assert result["ok"] is True
    assert result["document"]["validation_status"] == "accepted"


def test_pro_v1_requires_flash_guidance():
    payload = _pro_v1_payload()
    payload.pop("flash_guidance")

    result = ao.validateProHourlyMarketAnalysis(payload)

    assert result["ok"] is False
    assert "flash_guidance_required" in result["errors"]


def test_pro_v1_requires_source_ref_map():
    payload = _pro_v1_payload()
    payload.pop("source_ref_map")

    result = ao.validateProHourlyMarketAnalysis(payload)

    assert result["ok"] is False
    assert "source_ref_map_required" in result["errors"]


def test_provider_finish_reason_length_is_not_accepted(tmp_path: Path, monkeypatch):
    now = datetime.fromisoformat("2026-06-08T09:00:00+09:00")
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-08" / "events.jsonl",
        [{"event_id": "event-1", "title": "삼성전자 투자 확대", "published_at_kst": "2026-06-08T08:50:00+09:00"}],
    )
    _write_json(
        tmp_path / "kis-market" / "2026-06-08" / "snap.json",
        {"schema_version": "kis_market_snapshot/v0", "artifact_id": "snap-1", "produced_at_kst": "2026-06-08T08:59:00+09:00"},
    )
    monkeypatch.setattr(
        runtime,
        "_call_deepseek",
        lambda *_args, **_kwargs: {
            "http_status": 200,
            "finish_reason": "length",
            "model": "deepseek-v4-pro",
            "text": json.dumps(_pro_v1_payload(), ensure_ascii=False),
            "usage": {"completion_tokens": 2000},
            "error": None,
        },
    )

    result = runtime.run_pro_hourly_once(data_root=tmp_path, at=now, model="deepseek-v4-pro")

    assert result["validation_status"] == "accepted_with_warnings"
    assert result["investment_utility_status"] == "truncated_low_utility"
    assert result["flash_usable"] is False
    assert "provider_output_truncated" in result["validation_warnings"]


def test_accepted_with_warnings_exit_zero_and_health_marks_quality_degraded(tmp_path: Path, monkeypatch):
    now = datetime.fromisoformat("2026-06-08T09:00:00+09:00")
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-08" / "events.jsonl",
        [{"event_id": "event-1", "title": "삼성전자 투자 확대", "published_at_kst": "2026-06-08T08:50:00+09:00"}],
    )
    _write_json(
        tmp_path / "kis-market" / "2026-06-08" / "snap.json",
        {"schema_version": "kis_market_snapshot/v0", "artifact_id": "snap-1", "produced_at_kst": "2026-06-08T08:59:00+09:00"},
    )
    monkeypatch.setattr(runtime, "_now_kst", lambda: now)
    monkeypatch.setattr(
        runtime,
        "_call_deepseek",
        lambda *_args, **_kwargs: {
            "http_status": 200,
            "finish_reason": "length",
            "model": "deepseek-v4-pro",
            "text": json.dumps(_pro_v1_payload(), ensure_ascii=False),
            "usage": {"completion_tokens": 2000},
            "error": None,
        },
    )

    code = runtime.main(["--once", "--job", "pro-hourly", "--data-root", str(tmp_path), "--model", "deepseek-v4-pro"])
    artifact = json.loads((tmp_path / "ai" / "2026-06-08" / "pro-hourly-latest.json").read_text(encoding="utf-8"))
    health = json.loads((tmp_path / "evidence" / "2026-06-08" / "pro-hourly-latest-health.json").read_text(encoding="utf-8"))

    assert code == 0
    assert artifact["validation_status"] == "accepted_with_warnings"
    assert artifact["quality_degraded"] is True
    assert artifact["flash_usable"] is False
    assert "provider_output_truncated" in artifact["warnings"]
    assert health["quality_degraded"] is True
    assert health["flash_usable"] is False
    assert "provider_output_truncated" in health["warnings"]


def test_provider_error_exit_one(tmp_path: Path, monkeypatch):
    now = datetime.fromisoformat("2026-06-08T09:00:00+09:00")
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-08" / "events.jsonl",
        [{"event_id": "event-1", "title": "삼성전자 투자 확대", "published_at_kst": "2026-06-08T08:50:00+09:00"}],
    )
    monkeypatch.setattr(runtime, "_now_kst", lambda: now)

    def _raise_provider(*_args, **_kwargs):
        raise RuntimeError("provider boom")

    monkeypatch.setattr(runtime, "_call_deepseek", _raise_provider)

    code = runtime.main(["--once", "--job", "pro-hourly", "--data-root", str(tmp_path), "--model", "deepseek-v4-pro"])

    assert code == 1


def test_generic_pro_summary_is_low_utility():
    payload = _pro_v1_payload(summary="근거 입력을 바탕으로 생성한 DeepSeek Pro 시간별 시장 분석입니다")

    result = ao.validateProHourlyMarketAnalysis(payload)

    assert result["document"]["validation_status"] == "accepted_with_warnings"
    assert result["document"]["investment_utility_status"] == "news_only_low_utility"
    assert result["document"]["flash_usable"] is False
    assert "low_investment_utility" in result["warnings"]
    assert "generic_pro_summary" in result["warnings"]


def test_generic_theme_map_is_low_utility():
    payload = _pro_v1_payload(
        theme_map=[
            {
                "theme": "최근 1시간 입력 기반 감시",
                "direction": "neutral",
                "strength": 0.3,
                "freshness": "last_1h",
                "affected_groups": [],
                "avoid_groups": [],
                "why_it_matters": "시장 반응 확인 필요",
                "source_refs": ["event-1"],
                "market_data_refs": ["snap-1"],
                "market_confirmation_status": "confirmed",
            }
        ]
    )

    result = ao.validateProHourlyMarketAnalysis(payload)

    assert result["document"]["validation_status"] == "accepted_with_warnings"
    assert result["document"]["investment_utility_status"] == "news_only_low_utility"
    assert "generic_theme_map" in result["warnings"]
    assert "theme_map_empty_groups" in result["warnings"]


def test_empty_no_trade_conditions_off_session_is_low_utility():
    payload = _pro_v1_payload(
        calendar_context={"kis_realtime_expected": False, "market_context_open": False},
        no_trade_conditions=[],
    )

    result = ao.validateProHourlyMarketAnalysis(payload)

    assert result["document"]["validation_status"] == "accepted_with_warnings"
    assert result["document"]["flash_usable"] is False
    assert result["document"]["no_trade_conditions"]
    assert "off_session_no_trade_conditions_required" in result["warnings"]


def test_off_session_market_confirmation_confirmed_is_invalid():
    payload = _pro_v1_payload(
        calendar_context={"kis_realtime_expected": False, "market_context_open": False},
        no_trade_conditions=[
            {
                "condition": "개장 후 KRX 거래대금/체결강도 확인 전 BUY_NOW 금지",
                "reason": "오프세션",
            }
        ],
    )

    result = ao.validateProHourlyMarketAnalysis(payload)

    assert result["document"]["validation_status"] == "accepted_with_warnings"
    assert result["document"]["theme_map"][0]["market_confirmation_status"] == "awaiting_next_open"
    assert "off_session_market_confirmation_confirmed" in result["warnings"]


def test_off_session_kis_data_status_not_ok():
    payload = _pro_v1_payload(
        calendar_context={"kis_realtime_expected": False, "market_context_open": False},
        data_quality={
            "news_event_count": 3,
            "kis_market_snapshot_count": 2,
            "kis_artifact_count": 2,
            "kis_realtime_snapshot_count": 0,
            "kis_safe_skip_count": 2,
            "valid_market_confirmation_count": 0,
            "kis_data_status": "ok",
            "market_confirmation_status": "confirmed",
            "runtime_kis_failure_evidence_present": False,
            "missing_inputs": [],
            "warnings": [],
        },
        no_trade_conditions=[
            {
                "condition": "개장 후 KRX 거래대금/체결강도 확인 전 BUY_NOW 금지",
                "reason": "오프세션",
            }
        ],
    )

    result = ao.validateProHourlyMarketAnalysis(payload)
    data_quality = result["document"]["data_quality"]

    assert data_quality["kis_data_status"] in {"expected_off_session_no_realtime", "off_session_context_only"}
    assert data_quality["kis_data_status"] != "ok"
    assert data_quality["market_confirmation_status"] != "confirmed"
    assert result["document"]["theme_map"][0]["market_confirmation_status"] == "awaiting_next_open"


def test_off_session_requires_no_trade_condition():
    payload = _pro_v1_payload(
        calendar_context={"kis_realtime_expected": False, "market_context_open": False},
        theme_map=[
            {
                "theme": "정책 carryover",
                "direction": "positive_watch",
                "strength": 0.5,
                "freshness": "carryover",
                "affected_groups": ["건설"],
                "avoid_groups": ["개장 전 BUY_NOW"],
                "why_it_matters": "월요일 장초 수급 확인 대상",
                "source_refs": ["event-1"],
                "market_data_refs": [],
                "market_confirmation_status": "awaiting_next_open",
            }
        ],
        no_trade_conditions=[],
    )

    result = ao.validateProHourlyMarketAnalysis(payload)

    assert result["document"]["no_trade_conditions"][0]["condition"] == "개장 후 KRX 거래대금/체결강도 확인 전 BUY_NOW 금지"
    assert result["document"]["validation_status"] == "accepted_with_warnings"


def test_weekend_pro_hourly_uses_derived_weekend_reason(tmp_path: Path, monkeypatch):
    now = datetime.fromisoformat("2026-06-07T22:00:00+09:00")
    calendar = tmp_path / "calendar.json"
    _write_calendar(calendar, day="2026-06-08", trading=True)
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(calendar))
    _append_jsonl(
        tmp_path / "normalized" / "2026-06-07" / "events.jsonl",
        [{"event_id": "event-1", "title": "주말 carryover 점검", "published_at_kst": "2026-06-07T21:30:00+09:00"}],
    )
    _write_json(
        tmp_path / "kis-market" / "2026-06-07" / "safe-skip.json",
        {
            "schema_version": "kis_market_snapshot/v0",
            "artifact_id": "snap-safe-skip",
            "status": "safe_skip_market_session_gate",
            "produced_at_kst": "2026-06-07T21:59:00+09:00",
            "input_results": [
                {
                    "input_id": "market_operation",
                    "status": "safe_skip_calendar_day_missing",
                    "row_count": 0,
                    "endpoint_called": False,
                }
            ],
        },
    )
    provider_payload = _pro_v1_payload(
        data_quality={
            "news_event_count": 1,
            "kis_market_snapshot_count": 1,
            "kis_data_status": "ok",
            "market_confirmation_status": "confirmed",
            "runtime_kis_failure_evidence_present": False,
            "missing_inputs": [],
            "warnings": [],
        },
        no_trade_conditions=[
            {
                "condition": "개장 후 KRX 거래대금/체결강도 확인 전 BUY_NOW 금지",
                "reason": "주말 carryover",
                "source_refs": ["event-1"],
                "market_data_refs": ["snap-safe-skip"],
            }
        ],
    )
    monkeypatch.setattr(
        runtime,
        "_call_deepseek",
        lambda *_args, **_kwargs: {
            "http_status": 200,
            "finish_reason": "stop",
            "model": "deepseek-v4-pro",
            "text": json.dumps(provider_payload, ensure_ascii=False),
            "usage": None,
            "error": None,
        },
    )

    result = runtime.run_pro_hourly_once(data_root=tmp_path, at=now, model="deepseek-v4-pro")

    assert result["calendar_context"]["calendar_status"] == "derived_weekend_non_trading"
    assert result["calendar_context"]["reason"] == "weekend_non_trading_day"
    assert result["calendar_context"]["raw_calendar_status"] == "calendar_day_missing"
    assert result["kis_call_gate"]["calendar_context"]["reason"] == "calendar_day_missing"
    assert result["data_quality"]["kis_data_status"] == "expected_off_session_no_realtime"
    assert result["data_quality"]["kis_safe_skip_count"] == 1
    assert result["data_quality"]["valid_market_confirmation_count"] == 0


def test_pro_output_prompt_includes_hard_caps():
    prompt = runtime._build_pro_hourly_prompt(  # noqa: SLF001
        [{"event_id": "event-1", "title": "반도체 투자 확대", "event_type": "news"}],
        [{"artifact_id": "snap-1", "status": "safe_skip_market_session_gate", "input_results": []}],
        produced_at_kst="2026-06-07T22:00:00+09:00",
        calendar_context={"kis_realtime_expected": False, "market_context_open": False},
    )

    assert "theme_map 최대 5개" in prompt
    assert "source_ref_map 최대 5개" in prompt
    assert "no_trade_conditions 최대 5개" in prompt
    assert "questions_for_next_flash 최대 5개" in prompt
    assert "source_refs는 최대 3개" in prompt
    assert "market_data_refs는 최대 3개" in prompt
    assert "market_regime.why claim은 최대 2개" in prompt
    assert "data_quality.kis_data_status='ok' 금지" in prompt


def test_prompt_schema_hard_caps_remain_present():
    prompt = runtime._build_pro_hourly_prompt(  # noqa: SLF001
        [{"event_id": "event-1", "title": "반도체 투자 확대", "event_type": "news"}],
        [],
        produced_at_kst="2026-06-08T09:00:00+09:00",
        calendar_context={"kis_realtime_expected": True, "market_context_open": True},
    )

    assert "출력 hard cap" in prompt
    assert "theme_map 최대 5개" in prompt
    assert "source_ref_map 최대 5개" in prompt
    assert "no_trade_conditions 최대 5개" in prompt
    assert "questions_for_next_flash 최대 5개" in prompt
    assert "source_refs는 최대 3개" in prompt
    assert "market_data_refs는 최대 3개" in prompt


def test_provider_refs_are_limited_per_item():
    refs = [f"event-{index}" for index in range(8)]
    market_refs = [f"snap-{index}" for index in range(8)]
    payload = _pro_v1_payload(
        market_regime={
            "mode": "NEUTRAL",
            "confidence": 0.52,
            "why": [
                {"claim": f"판단 근거 {index}", "source_refs": refs, "market_data_refs": market_refs}
                for index in range(4)
            ],
        },
        theme_map=[
            {
                "theme": f"테마 {index}",
                "direction": "positive_watch",
                "strength": 0.5,
                "freshness": "last_1h",
                "affected_groups": ["종목군"],
                "avoid_groups": [],
                "why_it_matters": f"테마 {index} 확인 필요",
                "source_refs": refs,
                "market_data_refs": market_refs,
                "market_confirmation_status": "confirmed",
            }
            for index in range(7)
        ],
        no_trade_conditions=[
            {
                "condition": f"조건 {index}",
                "reason": "확인 필요",
                "source_refs": refs,
                "market_data_refs": market_refs,
            }
            for index in range(7)
        ],
        source_ref_map=[
            {
                "claim": f"테마 {index} 판단 근거",
                "source_refs": refs,
                "market_data_refs": market_refs,
                "confidence": 0.6,
            }
            for index in range(7)
        ],
        questions_for_next_flash=[f"질문 {index}" for index in range(7)],
    )

    result = ao.validateProHourlyMarketAnalysis(payload)
    document = result["document"]

    assert len(document["theme_map"]) == 5
    assert len(document["source_ref_map"]) == 5
    assert len(document["no_trade_conditions"]) == 5
    assert len(document["questions_for_next_flash"]) == 5
    assert len(document["theme_map"][0]["source_refs"]) == 3
    assert len(document["theme_map"][0]["market_data_refs"]) == 3
    assert len(document["source_ref_map"][0]["source_refs"]) == 3
    assert len(document["no_trade_conditions"][0]["market_data_refs"]) == 3
    assert len(document["market_regime"]["why"]) == 2
    assert len(document["market_regime"]["why"][0]["source_refs"]) == 3


def test_truncated_pro_sets_flash_usable_false():
    payload = _pro_v1_payload(provider={"finish_reason": "length"})

    result = ao.validateProHourlyMarketAnalysis(payload)
    document = result["document"]

    assert document["validation_status"] == "accepted_with_warnings"
    assert document["investment_utility_status"] == "truncated_low_utility"
    assert document["flash_usable"] is False
    assert document["flash_aggression_cap"] == "no_buy_now"
    assert "provider_output_truncated" in result["warnings"]


def test_finish_reason_length_still_marks_truncated_low_utility():
    result = ao.validateProHourlyMarketAnalysis(_pro_v1_payload(provider={"finish_reason": "length"}))

    assert result["document"]["investment_utility_status"] == "truncated_low_utility"
    assert result["document"]["flash_usable"] is False
    assert result["document"]["flash_aggression_cap"] == "no_buy_now"
    assert result["document"]["validation_status"] == "accepted_with_warnings"


def test_clustered_source_prompt_limits_raw_event_count():
    events = [
        {"event_id": f"event-{index}", "title": f"반도체 투자 확대 {index}", "event_type": "news", "query": "반도체"}
        for index in range(60)
    ]

    prompt = runtime._build_pro_hourly_prompt(  # noqa: SLF001
        events,
        [],
        produced_at_kst="2026-06-08T09:00:00+09:00",
        calendar_context={"kis_realtime_expected": True},
    )

    assert "top_news_clusters" in prompt
    assert "뉴스/공시=" not in prompt
    assert prompt.count("event-") <= 5


def test_good_off_session_strategy_context_is_accepted_with_selective_watch():
    payload = _pro_v1_payload(
        calendar_context={"kis_realtime_expected": False, "market_context_open": False},
        theme_map=[
            {
                "theme": "정책/건설 carryover",
                "direction": "positive_watch",
                "strength": 0.52,
                "freshness": "carryover",
                "affected_groups": ["건설", "시멘트"],
                "avoid_groups": ["개장 전 BUY_NOW"],
                "why_it_matters": "주말 정책 뉴스가 월요일 장초 수급 확인 대상입니다",
                "source_refs": ["event-1"],
                "market_data_refs": [],
                "market_confirmation_status": "awaiting_next_open",
                "confirmation_signals_for_flash": ["09:00 이후 거래대금 상위 진입"],
            }
        ],
        flash_guidance={
            "preferred_bias": "selective_watch",
            "max_aggression": "low",
            "candidate_focus": ["정책 carryover 테마"],
            "avoid_focus": ["개장 전 BUY_NOW"],
            "must_check_before_buy": ["KRX execution quote", "거래대금/체결강도 확인"],
            "position_management_notes": [],
        },
        no_trade_conditions=[
            {
                "condition": "개장 후 KRX 거래대금/체결강도 확인 전 BUY_NOW 금지",
                "reason": "휴장일 뉴스 기반 carryover만으로는 장초 수급 확인이 불가능함",
            }
        ],
        source_ref_map=[
            {
                "claim": "정책/건설 carryover는 월요일 장초 거래대금 확인 전 관찰 대상입니다",
                "source_refs": ["event-1"],
                "market_data_refs": [],
                "confidence": 0.55,
            }
        ],
        questions_for_next_flash=["정책 테마 후보가 09:00 이후 거래대금 상위에 진입하는가?"],
    )

    result = ao.validateProHourlyMarketAnalysis(payload)

    assert result["ok"] is True
    assert result["document"]["validation_status"] == "accepted"
    assert result["document"]["investment_utility_status"] == "actionable_context"


def test_good_market_open_strategy_context_is_actionable_context():
    result = ao.validateProHourlyMarketAnalysis(_pro_v1_payload())

    assert result["ok"] is True
    assert result["document"]["validation_status"] == "accepted"
    assert result["document"]["investment_utility_status"] == "actionable_context"


def test_flash_forbids_buy_now_when_pro_context_low_utility():
    doc = ao.buildFlashTradeDocument(
        pro_artifact={
            "artifact_id": "art_pro_low",
            "investment_utility_status": "truncated_low_utility",
            "flash_usable": False,
            "market_regime": {"mode": "NEUTRAL"},
            "flash_guidance": {"preferred_bias": "selective_watch"},
        },
        recent_events=[{"event_id": "event-1"}],
        kis_market_snapshots=[{"artifact_id": "snap-1"}],
        compiled_watch=[
            {
                "schema_version": "compiled_watch/v0",
                "symbol": "005930",
                "source_ids": ["event-1"],
                "entry_intent": {"entry_zone": [10000], "take_profit": 10500, "stop_loss": 9800},
                "valid_until_kst": "2026-06-08T09:10:00+09:00",
            }
        ],
        portfolio_snapshot={"artifact_id": "portfolio-1", "holdings": []},
        order_state_snapshot={"artifact_id": "orders-1", "pending_orders": []},
        morning_watchlist={
            "schema_version": "morning_watchlist/v1",
            "artifact_id": "art_morning_20260608",
            "target_trade_date_kst": "2026-06-08",
            "generated_at_kst": "2026-06-08T07:15:00+09:00",
        },
        provider_actions=[{"symbol": "005930", "action": "BUY_NOW", "confidence": 0.8}],
        produced_at_kst="2026-06-08T09:00:00+09:00",
    )

    assert doc["actions"][0]["action"] == "WAIT_BUY"
    assert "pro_context_low_utility" in doc["global_risk_flags"]


def test_flash_provider_called_with_morning_fallback_universe(tmp_path: Path, monkeypatch):
    data_root = tmp_path / "data"
    day = "2026-06-08"
    calendar = tmp_path / "calendar.json"
    _write_calendar(calendar, day=day, trading=True)
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(calendar))
    _write_json(
        data_root / "ai" / day / "pro-hourly-latest.json",
        _pro_v1_payload(artifact_id="art_pro_hourly_20260608_0900"),
    )
    _write_json(
        data_root / "morning-watchlist" / day / "morning-watchlist-latest.json",
        {
            "schema_version": "morning_watchlist/v1",
            "artifact_id": "art_morning_watchlist_20260608_0715",
            "target_trade_date_kst": day,
            "generated_at_kst": "2026-06-08T07:15:00+09:00",
            "items": [
                {
                    "ticker": "005930",
                    "name": "삼성전자",
                    "stance": "eligible_for_flash_review",
                    "thesis": "장전 후보",
                    "source_refs": ["event-1"],
                    "confidence": 0.6,
                }
            ],
            "market_open_plan": {"opening_bias": "selective_watch", "why": "테스트", "must_wait_for_market_confirmation": True},
        },
    )
    calls: list[dict] = []

    def _fake_deepseek(prompt, **kwargs):
        calls.append({"prompt": prompt, "kwargs": kwargs})
        return {
            "http_status": 200,
            "finish_reason": "stop",
            "model": kwargs.get("model"),
            "usage": {"completion_tokens": 10},
            "text": json.dumps(
                {
                    "actions": [
                        {
                            "symbol": "005930",
                            "action": "BUY_NOW",
                            "entry_price_limit": 70000,
                            "target_price": 72100,
                            "stop_loss_price": 67900,
                            "planned_order_cash_krw": 100000,
                            "confidence": 0.8,
                        }
                    ]
                },
                ensure_ascii=False,
            ),
        }

    monkeypatch.setattr(runtime, "_call_deepseek", _fake_deepseek)

    artifact = runtime.run_flash_trade_document_once(
        data_root=data_root,
        at=datetime.fromisoformat("2026-06-08T09:10:00+09:00"),
        model="deepseek-v4-flash",
    )

    assert calls
    assert "005930" in calls[0]["prompt"]
    assert artifact["provider_status"] == "ok"
    assert artifact["candidate_universe_source"] == "gpt_morning_watchlist_provisional"
    assert artifact["candidate_universe_count"] == 1
    assert artifact["actions"][0]["action"] == "WAIT_BUY"
    assert artifact["actions"][0]["kis_quote_confirmed"] is False
    assert artifact["paper_intent_pipeline"]["accepted_count"] == 0
    assert "kis_quote_confirmation_required_before_paper_intent" in artifact["paper_intent_pipeline"]["rejected_actions"][0]["reasons"]


def _flash_v1_document(**action_overrides):
    action = {
        "action_id": "act_005930_0900_01",
        "symbol": "005930",
        "ticker": "005930",
        "name": "삼성전자",
        "side": "BUY",
        "action": "BUY_NOW",
        "quantity": 10,
        "planned_order_cash_krw": 120000,
        "entry_price_limit": 10200,
        "target_price": 11000,
        "stop_loss_price": 9900,
        "valid_from_kst": "2026-06-08T09:00:00+09:00",
        "valid_until_kst": "2026-06-08T09:10:00+09:00",
        "confidence": 0.72,
        "urgency": "medium",
        "action_source": "deepseek_flash_provider",
        "thesis": "거래대금 확인 기반 진입 후보",
        "why_now": "개장 직후 수급 확인 구간",
        "required_confirmations": ["KRX 호가 확인"],
        "cancel_if": ["거래대금이 붙지 않으면 취소"],
        "source_refs": ["event-1"],
        "pro_refs": ["art_pro"],
        "market_data_refs": ["snap-1"],
        "portfolio_state_refs": ["portfolio-1", "orders-1"],
        "paper_only": True,
        "no_live_order": True,
    }
    action.update(action_overrides)
    return {
        "schema_version": "flash_trade_document/v1",
        "artifact_id": "art_flash_tdoc_20260608_090000",
        "artifact_type": "flash_trade_document",
        "document_kind": "TRADE_ACTIONS",
        "job_id": "deepseek_flash_trade_document_10m",
        "model_name": "deepseek-v4-flash",
        "produced_at_kst": "2026-06-08T09:00:00+09:00",
        "investment_mode": "paper",
        "market_analysis_feed_mode": "integrated",
        "execution_venue_mode": "krx_only",
        "order_safety": "no_direct_order",
        "ai_direct_broker_call_allowed": False,
        "ai_direct_order_allowed": False,
        "pro_hourly_report_ref": "art_pro",
        "market_context": {"market_context_open": True, "broker_order_open": True, "kis_realtime_expected": True},
        "candidate_universe_symbols": ["005930"],
        "actions": [action],
        "no_broker_call": True,
        "no_order_submission": True,
    }


def test_flash_v1_accepts_provider_grounded_buy_action():
    result = ao.validateFlashTradeDocument(_flash_v1_document())

    assert result["ok"] is True
    assert result["document"]["validation_status"] == "accepted"


def test_flash_v1_rejects_quantity_zero_buy_now():
    result = ao.validateFlashTradeDocument(_flash_v1_document(quantity=0, planned_order_cash_krw=0))

    assert result["ok"] is False
    assert "actions_item_0_buy_now_size_required" in result["errors"]


def test_flash_v1_rejects_missing_target_or_stop():
    result = ao.validateFlashTradeDocument(_flash_v1_document(target_price=0, stop_loss_price=0))

    assert result["ok"] is False
    assert "actions_item_0_target_price_required" in result["errors"]
    assert "actions_item_0_stop_loss_price_required" in result["errors"]


def test_flash_v1_rejects_universe_outside_symbol():
    result = ao.validateFlashTradeDocument(_flash_v1_document(symbol="999999", ticker="999999"))

    assert result["ok"] is False
    assert "actions_item_0_off_universe_ticker" in result["errors"]


def test_flash_v1_rejects_source_ref_less_buy():
    result = ao.validateFlashTradeDocument(_flash_v1_document(source_refs=[], market_data_refs=[]))

    assert result["ok"] is False
    assert "actions_item_0_source_refs_required" in result["errors"]
    assert "actions_item_0_market_data_refs_required" in result["errors"]


def test_flash_v1_blocks_paper_after_1500():
    doc = _flash_v1_document()
    doc["produced_at_kst"] = "2026-06-08T15:05:00+09:00"
    doc["market_context"] = {"market_context_open": True, "broker_order_open": False, "kis_realtime_expected": True}

    result = ao.validateFlashTradeDocument(doc)

    assert result["ok"] is False
    assert "actions_item_0_paper_buy_sell_after_1500_forbidden" in result["errors"]


def test_flash_validator_rejects_buy_now_when_pro_context_low_utility():
    doc = _flash_v1_document()
    doc["global_risk_flags"] = ["pro_context_low_utility"]

    result = ao.validateFlashTradeDocument(doc)

    assert result["ok"] is False
    assert "actions_item_0_buy_now_forbidden_when_pro_context_low_utility" in result["errors"]


def test_morning_v1_requires_market_open_plan(tmp_path: Path):
    result = runtime.publish_morning_watchlist_artifact(
        payload={
            "schema_version": "morning_watchlist/v1",
            "artifact_id": "art_morning_watchlist_20260608_missing_plan",
            "route": "codex_cli_local_browser_use",
            "target_trade_date_kst": "2026-06-08",
            "reviewer": "chatgpt_pro",
            "forbidden_actions_acknowledged": True,
            "items": [],
        },
        data_root=tmp_path,
        target_trade_date="2026-06-08",
        at=datetime.fromisoformat("2026-06-07T12:00:00+09:00"),
    )

    assert result["validation_status"] == "safe_block"
    assert "market_open_plan_required" in result["validation_errors"]


def test_morning_v1_rejects_top_level_eligible_for_flash_review_alias(tmp_path: Path):
    result = runtime.publish_morning_watchlist_artifact(
        payload={
            "schema_version": "morning_watchlist/v1",
            "artifact_id": "art_morning_watchlist_20260608_wrong_items_key",
            "route": "codex_cli_local_browser_use",
            "target_trade_date_kst": "2026-06-08",
            "reviewer": "chatgpt_pro",
            "forbidden_actions_acknowledged": True,
            "market_open_plan": {
                "opening_bias": "selective_watch",
                "why": "테스트",
                "must_wait_for_market_confirmation": True,
                "first_flash_questions": ["거래대금 확인"],
            },
            "eligible_for_flash_review": [
                {
                    "ticker": "005930",
                    "thesis": "잘못된 top-level 후보 배열",
                    "opening_trigger_conditions": ["거래대금"],
                    "invalidation_conditions": ["스프레드"],
                    "source_refs": ["event-1"],
                    "confidence": 0.6,
                }
            ],
        },
        data_root=tmp_path,
        target_trade_date="2026-06-08",
        at=datetime.fromisoformat("2026-06-08T07:29:31+09:00"),
    )

    assert result["validation_status"] == "safe_block"
    assert "top_level_eligible_for_flash_review_forbidden" in result["validation_errors"]
    assert "items_must_be_list" in result["validation_errors"]


def test_morning_v1_rejects_executable_order_fields(tmp_path: Path):
    result = runtime.publish_morning_watchlist_artifact(
        payload={
            "schema_version": "morning_watchlist/v1",
            "artifact_id": "art_morning_watchlist_20260608_order_field",
            "route": "codex_cli_local_browser_use",
            "target_trade_date_kst": "2026-06-08",
            "reviewer": "chatgpt_pro",
            "forbidden_actions_acknowledged": True,
            "market_open_plan": {
                "opening_bias": "selective_watch",
                "why": "테스트",
                "must_wait_for_market_confirmation": True,
                "first_flash_questions": ["거래대금 확인"],
            },
            "items": [
                {
                    "ticker": "005930",
                    "stance": "eligible_for_flash_review",
                    "thesis": "테스트",
                    "opening_trigger_conditions": ["거래대금"],
                    "invalidation_conditions": ["스프레드"],
                    "source_refs": ["event-1"],
                    "confidence": 0.6,
                    "quantity": 10,
                }
            ],
        },
        data_root=tmp_path,
        target_trade_date="2026-06-08",
        at=datetime.fromisoformat("2026-06-07T12:00:00+09:00"),
    )

    assert result["validation_status"] == "safe_block"
    assert any(error.startswith("executable_order_fields_forbidden") for error in result["validation_errors"])


def test_gpt_morning_wrapper_requires_top_level_items_validation():
    script = Path(__file__).resolve().parents[2] / "ops" / "gpt_pro_morning_watchlist.sh"
    text = script.read_text(encoding="utf-8")

    assert "top-level items 배열은 필수" in text
    assert "must be a JSON array, even when empty" in text
    assert "top_level_eligible_for_flash_review_forbidden" in text
    assert 'raise SystemExit("items_must_be_list")' in text
    assert 'obj.get("items") or []' not in text
