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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


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

    assert "사람이 읽는 모든 문자열 값은 한국어" in pro_prompt
    assert "schema key와 market_mode enum" in pro_prompt
    assert "사람이 읽는 모든 문자열 값은 한국어" in flash_prompt
    assert "action enum" in flash_prompt


def test_publish_morning_watchlist_writes_target_trade_date_latest_paths(tmp_path: Path):
    produced_at = datetime.fromisoformat("2026-06-07T11:55:00+09:00")
    result = runtime.publish_morning_watchlist_artifact(
        payload={
            "schema_version": "morning_watchlist/v0",
            "artifact_id": "art_morning_watchlist_20260608_sunday",
            "route": "codex_cli_local_browser_use",
            "target_trade_date_kst": "2026-06-08",
            "generated_at_kst": "2026-06-07T11:33:00+09:00",
            "purpose": "monday_preopen_rehearsal_late",
            "requires_monday_refresh": True,
            "forbidden_actions_acknowledged": True,
            "items": [{"ticker": "005930", "stance": "eligible_for_flash_review"}],
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


def test_flash_runtime_uses_exact_10m_window_and_provider_actions(tmp_path: Path, monkeypatch):
    now = datetime.fromisoformat("2026-06-08T09:00:00+09:00")
    _write_json(
        tmp_path / "ai" / "2026-06-08" / "pro-hourly-latest.json",
        {"schema_version": "pro_hourly_market_analysis/v0", "artifact_id": "art_pro_hourly_20260608_0900"},
    )
    _write_json(
        tmp_path / "morning-watchlist" / "2026-06-08" / "morning-watchlist-latest.json",
        {
            "schema_version": "morning_watchlist/v0",
            "artifact_id": "art_morning_watchlist_20260608_0715",
            "route": "codex_cli_local_browser_use",
            "target_trade_date_kst": "2026-06-08",
            "generated_at_kst": "2026-06-08T07:15:00+09:00",
            "forbidden_actions_acknowledged": True,
            "items": [{"ticker": "005930", "stance": "eligible_for_flash_review"}],
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
