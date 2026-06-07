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
    assert Path(result["health_path"]).is_file()


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
                        "planned_order_cash_krw": 100000,
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
    assert result["paper_intent_pipeline"]["accepted_count"] == 1


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
