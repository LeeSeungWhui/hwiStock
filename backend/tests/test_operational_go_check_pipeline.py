"""
Focused Go-Check coverage for HWISTOCK-UNIT-012/013/014/015.

All tests are no-network and paper-safe. They prove the operational file-driven
pipeline contracts without calling AI providers or KIS order transports.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import ai_orchestration as ao  # noqa: E402
from lib import operator_console_runtime as operator_console  # noqa: E402
from lib import trading_engine as engine  # noqa: E402
from service import HwiStockRunnerService as runner  # noqa: E402
from service import kis_market_data_collector as kis_collector  # noqa: E402
from service import kis_paper_continuous_runner as executor  # noqa: E402

NOW = "2026-06-05T09:40:00+09:00"


def _compiled_watch(symbol: str = "005930"):
    return {
        "schema_version": "compiled_watch/v0",
        "artifact_id": f"art_watch_{symbol}",
        "condition_card_id": f"condition_{symbol}",
        "candidate_id": f"candidate_{symbol}",
        "symbol": symbol,
        "source_ids": ["naver:news:1", "dart:disclosure:1"],
        "entry_intent": {
            "entry_zone": [10000, 10100],
            "take_profit": 10500,
            "stop_loss": 9800,
            "trailing_stop_pct": 1.2,
            "position_size_pct": 20,
            "planned_order_cash_krw": 100000,
        },
        "exit_plan": {"stop_loss": 9800, "take_profit": 10500, "trailing_stop_pct": 1.2},
        "valid_until_kst": "2026-06-05T09:50:00+09:00",
    }


def _flash_doc(symbol: str = "005930"):
    return ao.buildFlashTradeDocument(
        pro_artifact={"artifact_id": "art_pro_hourly_20260605_0900"},
        recent_events=[{"source_event_id": "naver:news:1"}, {"source_event_id": "dart:disclosure:1"}],
        kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260605_0939"}],
        compiled_watch=[_compiled_watch(symbol)],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        produced_at_kst=NOW,
    )


def test_unit013_kis_collector_is_six_input_bounded_and_blocks_extra_endpoint():
    config = kis_collector.loadKisSignalCollectorConfig(
        {"HWISTOCK_KIS_SIGNAL_INPUTS": "rest_volume_rank,order-cash"}
    )
    validation = kis_collector.validateKisSignalInputScope(config)
    assert validation["ok"] is False
    assert "kis_signal_input_not_in_six_input_allowlist:order-cash" in validation["errors"]
    assert "kis_signal_input_forbidden_order_surface:order-cash" in validation["errors"]

    payload = kis_collector.collectKisMarketDataOnce(env={})
    assert payload["schema_version"] == "kis_market_snapshot/v0"
    assert payload["status"] == "safe_block_paper_read_network_disabled"
    assert payload["six_input_allowlist"] == list(kis_collector.ALLOWED_SIGNAL_INPUTS)
    assert payload["order_cancel_modify_called"] is False


def test_unit013_flash_document_to_intent_requires_compiled_universe_and_refs():
    doc = _flash_doc("005930")
    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        now_kst=NOW,
    )
    assert pipeline["accepted_count"] == 1
    intent = pipeline["accepted_intents"][0]
    assert intent["schema_version"] == "paper_order_intent/v0"
    assert intent["flash_trade_document_ref"] == doc["artifact_id"]
    assert intent["source_refs"]
    assert intent["market_data_refs"]
    assert intent["portfolio_snapshot_ref"].startswith("art_portfolio")
    assert intent["order_state_snapshot_ref"].startswith("art_order_state")
    assert intent["broker_endpoint_called"] is False


def test_unit013_rejects_off_universe_and_portfolio_conflict_without_intent():
    doc = _flash_doc("005930")
    doc["actions"][0]["ticker"] = "999999"
    off_universe = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"holdings": []},
        order_state_snapshot={"pending_orders": []},
        now_kst=NOW,
    )
    assert off_universe["accepted_count"] == 0
    assert "off_universe_ticker" in off_universe["rejected_actions"][0]["reasons"]

    conflict_doc = _flash_doc("005930")
    conflict = engine.generatePaperOrderIntentsFromFlashDocument(
        conflict_doc,
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"holdings": [{"symbol": "005930"}]},
        order_state_snapshot={"pending_orders": []},
        now_kst=NOW,
    )
    assert conflict["accepted_count"] == 0
    assert "already_holding_symbol" in conflict["rejected_actions"][0]["reasons"]


def test_unit014_execution_preflight_idempotency_and_realtime_exit():
    executor.resetContinuousPaperRunnerForTests()
    doc = _flash_doc("005930")
    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        now_kst=NOW,
    )
    intent = pipeline["accepted_intents"][0]
    status = runner.get_runner_status("2026-06-05T09:40:00")
    status["calendar"]["tradingAllowed"] = True
    status["calendar"]["state"] = "calendar_ready"
    status["marketData"]["state"] = "source_configured"
    status["routing"]["venue"] = "KRX"
    first = executor.evaluateIntentExecutionPreflight(intent, status=status)
    assert first["ok"] is True, first["errors"]
    executor.markIntentConsumed(intent["idempotency_key"])
    second = executor.evaluateIntentExecutionPreflight(intent, status=status)
    assert second["ok"] is False
    assert "duplicate_intent_idempotency_key" in second["errors"]

    exit_decision = executor.evaluateRealtimeExitDecision(
        {"symbol": "005930", "stop_loss": 9800, "take_profit": 10500, "highest_price": 10400, "trailing_stop_pct": 1.2},
        {"price": 9790},
    )
    assert exit_decision["exit_required"] is True
    assert exit_decision["exit_reason"] == "stop_loss"
    assert exit_decision["depends_on_next_flash_tick"] is False


def test_unit015_operator_snapshot_is_read_only_and_masks_readiness(tmp_path: Path):
    snapshot = operator_console.buildOperatorConsoleSnapshot("2026-06-05T09:40:00", dataRoot=tmp_path)
    assert snapshot["schema_version"] == "operator_console_snapshot/v0"
    assert snapshot["safety"]["readOnlyDashboard"] is True
    assert snapshot["safety"]["buySellControlsExposed"] is False
    assert snapshot["safety"]["rawAccountDisplayed"] is False
    assert snapshot["readiness"]["operationalTradingReadiness"] is False
    assert snapshot["summary"]["accountId"] == "paper_account_alias:masked"

    report = operator_console.writeObservationReport(
        startedAtKst="2026-06-05T09:00:00+09:00",
        endedAtKst="2026-06-05T10:00:00+09:00",
        operatorNote="focused unit test",
        dataRoot=tmp_path,
    )
    assert report["durationPolicy"] == "operator_selected"
    assert report["fixedDurationDays"] is None
    assert report["readiness"]["operationalTradingReadiness"] is False
    assert Path(report["reportPath"]).is_file()
