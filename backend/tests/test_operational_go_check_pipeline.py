"""
Focused Go-Check coverage for HWISTOCK-UNIT-012/013/014/015.

All tests are no-network and paper-safe. They prove the operational file-driven
pipeline contracts without calling AI providers or KIS order transports.
"""

from __future__ import annotations

import os
import sys
import json
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


class FakeKisMarketAdapter:
    def __init__(self):
        self.calls = []

    def missingEnvKeys(self):
        return []

    def configSummary(self):
        return {"paperDomainOnly": True, "env": {"credentialValuesPrinted": False}}

    def issueTokenWithValue(self):
        self.calls.append("token")
        return {"step": "oauth_token", "status": "pass", "token_present": True}, "fake-token"

    def issueWebsocketApproval(self):
        self.calls.append("approval")
        return {"step": "websocket_approval", "status": "pass", "approval_key_present": True}

    def inquirePrice(self, token, symbol):
        self.calls.append(("price", symbol))
        return {
            "step": "quote_inquire_price",
            "status": "pass",
            "endpoint_called": True,
            "broker_order_surface": False,
            "rows_preview": [{"stck_shrn_iscd": symbol, "hts_kor_isnm": "삼성전자", "stck_prpr": "70000"}],
        }

    def inquireOrderbook(self, token, symbol):
        self.calls.append(("orderbook", symbol))
        return {
            "step": "quote_inquire_orderbook",
            "status": "pass",
            "endpoint_called": True,
            "broker_order_surface": False,
            "rows_preview": [{"stck_shrn_iscd": symbol, "askp1": "70100", "bidp1": "70000"}],
        }

    def volumeRank(self, token):
        self.calls.append("volume")
        return {
            "step": "rest_volume_rank",
            "status": "pass",
            "endpoint_called": True,
            "broker_order_surface": False,
            "row_count": 1,
            "rows_preview": [{"mksc_shrn_iscd": "000660", "hts_kor_isnm": "SK하이닉스", "stck_prpr": "180000", "data_rank": "1"}],
        }

    def volumePowerRank(self, token):
        self.calls.append("power")
        return {"step": "rest_volume_power_rank", "status": "pass", "endpoint_called": True, "rows_preview": []}

    def fluctuationRank(self, token):
        self.calls.append("fluctuation")
        return {"step": "rest_fluctuation_rank", "status": "pass", "endpoint_called": True, "rows_preview": []}

    def programTradeToday(self, token, *, market_class="K"):
        self.calls.append(("program", market_class))
        return {"step": f"rest_program_trading_aggregate_{market_class}", "status": "pass", "endpoint_called": True, "rows_preview": []}

    def revokeToken(self, token):
        self.calls.append("revoke")
        return {"step": "oauth_revoke", "status": "pass"}


def test_unit013_kis_collector_calls_paper_read_and_builds_compiled_watch():
    adapter = FakeKisMarketAdapter()
    payload = kis_collector.collectKisMarketDataOnce(
        env={
            "HWISTOCK_KIS_MARKET_READ_NETWORK_ENABLED": "true",
            "HWISTOCK_KIS_MIN_CALL_GAP_SEC": "0",
        },
        adapter=adapter,
    )
    assert payload["status"] == "ok"
    assert payload["order_cancel_modify_called"] is False
    assert all(row["endpoint_called"] for row in payload["input_results"])
    assert payload["compiled_watch"]["candidate_count"] >= 1
    first = payload["compiled_watch"]["items"][0]
    assert first["schema_version"] == "compiled_watch/v0"
    assert first["entry_intent"]["entry_zone"]
    assert "order-cash" not in " ".join(map(str, adapter.calls))


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
    assert intent["order_division"] == "00"
    assert intent["order_price"] == 10000
    assert intent["quantity"] == 10
    assert intent["broker_endpoint_called"] is False


def test_flash_document_ignores_expired_previous_wait_buy_documents():
    doc = ao.buildFlashTradeDocument(
        pro_artifact={"artifact_id": "art_pro_hourly_20260605_0900"},
        recent_events=[{"source_event_id": "naver:news:1"}],
        kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260605_0939"}],
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0951", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0951", "pending_orders": []},
        previous_trade_documents=[
            {
                "artifact_id": "old_flash",
                "valid_until": "2026-06-05T09:50:00+09:00",
                "actions": [{"ticker": "005930", "action": "WAIT_BUY"}],
            }
        ],
        produced_at_kst="2026-06-05T09:51:00+09:00",
    )
    assert doc["actions"][0]["ticker"] == "005930"
    assert doc["actions"][0]["action"] == "WAIT_BUY"
    assert doc["actions"][0]["portfolio_conflict"]["has_conflict"] is False


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
    safe_unit = tmp_path / "hwistock-kis-paper-runner.service"
    safe_unit.write_text(
        "\n".join(
            [
                "[Service]",
                "Environment=HWISTOCK_KIS_PAPER_ORDER_ENABLED=false",
                "ExecStart=python backend/service/kis_paper_continuous_runner.py --once --write-evidence --allow-paper-network",
            ]
        ),
        encoding="utf-8",
    )
    snapshot = operator_console.buildOperatorConsoleSnapshot(
        "2026-06-05T09:40:00",
        dataRoot=tmp_path,
        serviceUnitPaths=[safe_unit],
    )
    assert snapshot["schema_version"] == "operator_console_snapshot/v0"
    assert snapshot["safety"]["readOnlyDashboard"] is True
    assert snapshot["safety"]["buySellControlsExposed"] is False
    assert snapshot["safety"]["rawAccountDisplayed"] is False
    assert snapshot["readiness"]["operationalTradingReadiness"] is False
    assert snapshot["summary"]["accountId"] == "paper_account_alias:masked"
    assert snapshot["readinessTruth"]["headline"] == "NOT_READY_FOR_PAPER_TRADING"
    assert snapshot["readinessTruth"]["serviceVisibilityIsNotReadiness"] is True
    assert snapshot["readinessTruth"]["paperNetworkEnabled"] is True
    assert snapshot["readinessTruth"]["paperOrderEnabled"] is False
    assert snapshot["readinessTruth"]["paperOrdersSubmitted"] is False
    assert snapshot["readinessTruth"]["paperObservationAccepted"] is False
    assert snapshot["readinessTruth"]["operationalTradingReadiness"] is False
    assert "blocked_calendar_unconfigured" in snapshot["readinessTruth"]["blockers"]

    report = operator_console.writeObservationReport(
        startedAtKst="2026-06-05T09:00:00+09:00",
        endedAtKst="2026-06-05T10:00:00+09:00",
        operatorNote="focused unit test",
        dataRoot=tmp_path,
        serviceUnitPaths=[safe_unit],
    )
    assert report["durationPolicy"] == "operator_selected"
    assert report["fixedDurationDays"] is None
    assert report["readiness"]["operationalTradingReadiness"] is False
    assert Path(report["reportPath"]).is_file()


def test_unit015_operator_snapshot_detects_order_enabled_service_contradiction(tmp_path: Path):
    risky_unit = tmp_path / "hwistock-kis-paper-runner.service"
    risky_unit.write_text(
        "\n".join(
            [
                "[Service]",
                "Environment=HWISTOCK_KIS_PAPER_ORDER_ENABLED=true",
                "ExecStart=python backend/service/kis_paper_continuous_runner.py --once --allow-paper-network --allow-paper-orders",
            ]
        ),
        encoding="utf-8",
    )
    snapshot = operator_console.buildOperatorConsoleSnapshot(
        "2026-06-05T09:40:00",
        dataRoot=tmp_path,
        serviceUnitPaths=[risky_unit],
    )
    assert snapshot["readinessTruth"]["paperOrderEnabled"] is True
    assert snapshot["runtime"]["kisPaperRunnerServicePolicy"]["paperOrderEnabledByService"] is True
    assert "systemd_order_enabled_contradicts_readiness" in snapshot["readinessTruth"]["blockers"]
    assert any(entry["code"] == "SYSTEMD_ORDER_FLAG" and entry["message"] == "enabled" for entry in snapshot["auditLog"])


def test_unit015_operator_snapshot_maps_runtime_artifacts_to_dashboard_rows(tmp_path: Path):
    (tmp_path / "normalized" / "2026-06-05").mkdir(parents=True)
    (tmp_path / "compiled-watch" / "2026-06-05").mkdir(parents=True)
    (tmp_path / "ai" / "2026-06-05").mkdir(parents=True)
    (tmp_path / "trade-documents" / "2026-06-05").mkdir(parents=True)
    (tmp_path / "kis-market" / "2026-06-05").mkdir(parents=True)
    (tmp_path / "evidence" / "2026-06-05").mkdir(parents=True)

    (tmp_path / "normalized" / "2026-06-05" / "events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_type": "news_event",
                        "dedupe_key": "naver_search_news_api:https://example.test/1",
                        "title": "<b>삼성전자</b> 급락",
                        "published_at_kst": "2026-06-05T18:58:00+09:00",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "event_type": "disclosure_event",
                        "dedupe_key": "open_dart:corp:1",
                        "report_name": "주요사항보고서",
                        "published_at_kst": "2026-06-05T18:59:00+09:00",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "compiled-watch" / "2026-06-05" / "compiled-watch-latest.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "symbol": "005930",
                        "name": "삼성전자",
                        "condition_card_id": "condition_005930",
                        "entry_intent": {"entry_zone": [50000, 51000]},
                    }
                ],
                "produced_at_kst": "2026-06-05T19:00:00+09:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "ai" / "2026-06-05" / "pro-hourly-latest.json").write_text(
        json.dumps(
            {
                "summary": "시장 RISK_OFF",
                "market_regime": {"market_mode": "RISK_OFF"},
                "strong_conditions": ["인버스 강세"],
                "avoid_conditions": ["반도체 약세"],
                "produced_at_kst": "2026-06-05T19:00:01+09:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "trade-documents" / "2026-06-05" / "flash-trade-document-latest.json").write_text(
        json.dumps(
            {
                "actions": [
                    {
                        "action": "NO_TRADE",
                        "name": "삼성전자",
                        "entry_zone": [50000, 51000],
                        "portfolio_conflict": {"has_conflict": True, "reasons": ["prior_trade_document_still_valid"]},
                        "reason": "portfolio/order conflict",
                    }
                ],
                "validation_status": "pass",
                "produced_at_kst": "2026-06-05T19:10:00+09:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "kis-market" / "2026-06-05" / "kis-market-snapshot-latest.json").write_text(
        json.dumps(
            {
                "produced_at_kst": "2026-06-05T19:10:08+09:00",
                "input_results": [
                    {
                        "input_id": "rest_volume_rank",
                        "status": "pass",
                        "http_status": 200,
                        "row_count": 10,
                        "transport": "rest",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "evidence" / "2026-06-05" / "kis-paper-continuous-latest.json").write_text(
        json.dumps({"status": "warn", "steps": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    (tmp_path / "evidence" / "2026-06-05" / "runner-latest.json").write_text(
        json.dumps({"event": "runner_once"}, ensure_ascii=False),
        encoding="utf-8",
    )

    safe_unit = tmp_path / "hwistock-kis-paper-runner.service"
    safe_unit.write_text(
        "\n".join(
            [
                "[Service]",
                "Environment=HWISTOCK_KIS_PAPER_ORDER_ENABLED=false",
                "ExecStart=python backend/service/kis_paper_continuous_runner.py --once --allow-paper-network",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = operator_console.buildOperatorConsoleSnapshot(
        "2026-06-05T19:11:00+09:00",
        dataRoot=tmp_path,
        serviceUnitPaths=[safe_unit],
    )

    assert snapshot["candidates"][0]["symbol"] == "005930"
    assert snapshot["candidates"][0]["signal"] == "NO_TRADE"
    assert snapshot["summary"]["riskRejects"] == 1
    assert snapshot["intelligence"][0]["source"] == "open_dart"
    assert snapshot["intelligence"][0]["title"] == "주요사항보고서"
    assert any("DeepSeek Pro" in row["subject"] for row in snapshot["aiThread"])
    assert any(entry["code"] == "KIS_rest_volume_rank" for entry in snapshot["auditLog"])
