"""
Focused Go-Check coverage for HWISTOCK-UNIT-012/013/014/015.

All tests are no-network and paper-safe. They prove the operational file-driven
pipeline contracts without calling AI providers or KIS order transports.
"""

from __future__ import annotations

import os
import sys
import json
from datetime import datetime
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


def test_unit013_kis_collector_is_mode_aware_and_blocks_extra_endpoint():
    config = kis_collector.loadKisSignalCollectorConfig(
        {"HWISTOCK_KIS_SIGNAL_INPUTS": "rest_volume_rank,order-cash"}
    )
    validation = kis_collector.validateKisSignalInputScope(config)
    assert validation["ok"] is False
    assert "kis_signal_input_unknown:order-cash" in validation["errors"]
    assert "kis_signal_input_forbidden_order_surface:order-cash" in validation["errors"]

    payload = kis_collector.collectKisMarketDataOnce(env={})
    assert payload["schema_version"] == "kis_market_snapshot/v0"
    assert payload["status"] == "safe_block_paper_read_network_disabled"
    assert payload["signal_input_allowlist"] == list(kis_collector.ALLOWED_SIGNAL_INPUTS)
    assert payload["market_analysis_feed_mode"] == "integrated"
    assert payload["execution_venue_mode"] == "krx_only"
    assert payload["enabled_venues"] == ["INTEGRATED", "KRX"]
    assert payload["order_cancel_modify_called"] is False


def test_unit013_kis_collector_gates_nxt_by_investment_mode():
    paper_config = kis_collector.loadKisSignalCollectorConfig(
        {"HWISTOCK_KIS_SIGNAL_INPUTS": "nxt_realtime_trade_price_ws"}
    )
    paper_validation = kis_collector.validateKisSignalInputScope(paper_config)
    assert paper_config["investment_mode"] == "paper"
    assert paper_config["enabled_venues"] == ["INTEGRATED", "KRX"]
    assert paper_validation["ok"] is False
    assert "kis_signal_input_not_enabled_for_mode:nxt_realtime_trade_price_ws" in paper_validation["errors"]

    live_default_config = kis_collector.loadKisSignalCollectorConfig(
        {
            "HWISTOCK_KIS_INVESTMENT_MODE": "live",
            "HWISTOCK_KIS_SIGNAL_INPUTS": "nxt_realtime_trade_price_ws",
        }
    )
    live_default_validation = kis_collector.validateKisSignalInputScope(live_default_config)
    assert live_default_config["investment_mode"] == "live"
    assert live_default_config["enabled_venues"] == ["INTEGRATED", "KRX"]
    assert live_default_validation["ok"] is False
    assert "kis_signal_input_not_enabled_for_mode:nxt_realtime_trade_price_ws" in live_default_validation["errors"]

    real_config = kis_collector.loadKisSignalCollectorConfig(
        {
            "HWISTOCK_KIS_INVESTMENT_MODE": "real",
            "HWISTOCK_EXECUTION_VENUE_MODE": "krx_nxt",
            "HWISTOCK_NXT_ENABLED": "true",
            "HWISTOCK_NXT_READY_SET_APPROVED": "true",
            "HWISTOCK_KIS_SIGNAL_INPUTS": "nxt_realtime_trade_price_ws",
        }
    )
    real_validation = kis_collector.validateKisSignalInputScope(real_config)
    assert real_config["investment_mode"] == "live"
    assert real_config["enabled_venues"] == ["INTEGRATED", "KRX", "NXT"]
    assert real_validation["ok"] is True


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

    def issueWebsocketApprovalWithValue(self):
        self.calls.append("approval")
        return {"step": "websocket_approval", "status": "pass", "approval_key_present": True}, "fake-approval-key"

    def subscribeRealtime(self, approval_key, *, tr_id, tr_key, step, tr_type="1"):
        self.calls.append(("ws", tr_id, tr_key, step, tr_type, bool(approval_key)))
        return {
            "step": step,
            "status": "pass",
            "tr_id": tr_id,
            "tr_key": tr_key,
            "subscription_frame_ready": True,
            "ack_received": True,
            "endpoint_called": True,
            "broker_order_surface": False,
            "raw_response_stored": False,
        }

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


class FakePublicKisMarketAdapter:
    def __init__(self):
        self.requests = []
        self.calls = []

    def missingEnvKeys(self):
        return []

    def configSummary(self):
        return {"paperDomainOnly": True, "env": {"credentialValuesPrinted": False}}

    def issueTokenWithValue(self):
        self.calls.append("token")
        return {"step": "oauth_token", "status": "pass", "token_present": True}, "fake-token"

    def issueWebsocketApprovalWithValue(self):
        self.calls.append("approval")
        return {"step": "websocket_approval", "status": "pass", "approval_key_present": True}, "fake-approval-key"

    def authHeaders(self, token, tr_id):
        self.calls.append(("auth", token, tr_id))
        return {"authorization": f"Bearer {token}", "tr_id": tr_id}

    def requestBrokerJson(self, method, path_or_url, *, headers=None, body=None):
        self.requests.append({"method": method, "path": path_or_url, "headers": dict(headers or {}), "body": body})
        return {
            "http_status": 200,
            "payload": {
                "rt_cd": "0",
                "msg_cd": "ok",
                "output": [
                    {
                        "mksc_shrn_iscd": "000660",
                        "hts_kor_isnm": "SK하이닉스",
                        "stck_prpr": "180000",
                        "data_rank": "1",
                    }
                ],
            },
        }

    def revokeToken(self, token):
        self.calls.append("revoke")
        return {"step": "oauth_revoke", "status": "pass"}


class FakeNoMarketMethodAdapter:
    def missingEnvKeys(self):
        return []

    def issueTokenWithValue(self):
        return {"step": "oauth_token", "status": "pass", "token_present": True}, "fake-token"

    def issueWebsocketApprovalWithValue(self):
        return {"step": "websocket_approval", "status": "pass", "approval_key_present": True}, "fake-approval-key"

    def revokeToken(self, token):
        return {"step": "oauth_revoke", "status": "pass"}


def _write_trading_calendar(calendar: Path, day: str = "2026-06-05"):
    calendar.write_text(
        json.dumps(
            {
                "validUntil": "2099-12-31T23:59:59+09:00",
                "sourceAuthority": "unit_test_calendar",
                "days": {
                    day: {
                        "dateKst": day,
                        "isTradingDay": True,
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


def test_unit013_kis_collector_calls_paper_read_and_builds_compiled_watch(tmp_path: Path):
    calendar = tmp_path / "calendar.json"
    _write_trading_calendar(calendar)
    adapter = FakeKisMarketAdapter()
    payload = kis_collector.collectKisMarketDataOnce(
        env={
            "HWISTOCK_KIS_MARKET_READ_NETWORK_ENABLED": "true",
            "HWISTOCK_KIS_MIN_CALL_GAP_SEC": "0",
            "HWISTOCK_CALENDAR_PATH": str(calendar),
        },
        adapter=adapter,
        at=datetime.fromisoformat("2026-06-05T09:30:00+09:00"),
    )
    assert payload["status"] == "ok"
    assert payload["order_cancel_modify_called"] is False
    assert all(row["endpoint_called"] for row in payload["input_results"])
    assert any(row["tr_id"] == "H0UNCNT0" for row in payload["input_results"])
    assert payload["compiled_watch"]["candidate_count"] >= 1
    first = payload["compiled_watch"]["items"][0]
    assert first["schema_version"] == "compiled_watch/v0"
    assert first["entry_intent"]["entry_zone"]
    assert "order-cash" not in " ".join(map(str, adapter.calls))


def test_rest_market_read_uses_public_requestBrokerJson_authHeaders(tmp_path: Path):
    calendar = tmp_path / "calendar.json"
    _write_trading_calendar(calendar)
    adapter = FakePublicKisMarketAdapter()

    payload = kis_collector.collectKisMarketDataOnce(
        env={
            "HWISTOCK_KIS_MARKET_READ_NETWORK_ENABLED": "true",
            "HWISTOCK_KIS_MIN_CALL_GAP_SEC": "0",
            "HWISTOCK_KIS_SIGNAL_INPUTS": "rest_volume_rank",
            "HWISTOCK_CALENDAR_PATH": str(calendar),
        },
        adapter=adapter,
        at=datetime.fromisoformat("2026-06-05T09:30:00+09:00"),
    )

    row = payload["input_results"][0]
    assert row["status"] == "pass"
    assert row["endpoint_called"] is True
    assert row["request_boundary"] == "public_requestBrokerJson_authHeaders"
    assert row["tr_id"] == "FHPST01710000"
    assert "blocked_adapter_missing_market_method" not in json.dumps(payload, ensure_ascii=False)
    assert any("/uapi/domestic-stock/v1/quotations/volume-rank" in call["path"] for call in adapter.requests)
    assert adapter.requests[0]["headers"]["tr_id"] == "FHPST01710000"


def test_rest_volume_rank_rows_build_compiled_watch_candidates():
    compiled = kis_collector.buildCompiledWatchFromKisSnapshot(
        {
            "artifact_id": "art_kis_snapshot_rank_rows",
            "input_results": [
                {
                    "input_id": "rest_volume_rank",
                    "status": "pass",
                    "endpoint_called": True,
                    "row_count": 1,
                    "rows_preview": [
                        {
                            "mksc_shrn_iscd": "000660",
                            "hts_kor_isnm": "SK하이닉스",
                            "stck_prpr": "180000",
                            "data_rank": "1",
                        }
                    ],
                }
            ],
        },
        config={"default_order_cash_krw": 120_000, "position_size_pct": 8},
        at=datetime.fromisoformat("2026-06-05T09:30:00+09:00"),
    )

    assert compiled["candidate_count"] == 1
    candidate = compiled["items"][0]
    assert candidate["symbol"] == "000660"
    assert candidate["source_type"] == "kis_compiled_watch"
    assert candidate["entry_intent"]["entry_price_krw"] == 180000
    assert candidate["entry_intent"]["planned_order_cash_krw"] == 120000
    assert candidate["kis_quote_confirmed"] is True


def test_missing_market_method_does_not_mark_endpoint_called(tmp_path: Path):
    calendar = tmp_path / "calendar.json"
    _write_trading_calendar(calendar)

    payload = kis_collector.collectKisMarketDataOnce(
        env={
            "HWISTOCK_KIS_MARKET_READ_NETWORK_ENABLED": "true",
            "HWISTOCK_KIS_MIN_CALL_GAP_SEC": "0",
            "HWISTOCK_KIS_SIGNAL_INPUTS": "rest_volume_rank",
            "HWISTOCK_CALENDAR_PATH": str(calendar),
        },
        adapter=FakeNoMarketMethodAdapter(),
        at=datetime.fromisoformat("2026-06-05T09:30:00+09:00"),
    )

    row = payload["input_results"][0]
    assert row["status"] == "blocked_adapter_missing_market_method"
    assert row["endpoint_called"] is False


def test_unit013_kis_collector_weekend_safe_skips_without_transport(tmp_path: Path):
    calendar = tmp_path / "calendar.json"
    calendar.write_text(
        json.dumps(
            {
                "validUntil": "2099-12-31T23:59:59+09:00",
                "days": {
                    "2026-06-06": {
                        "dateKst": "2026-06-06",
                        "isTradingDay": False,
                        "reason": "Saturday",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    adapter = FakeKisMarketAdapter()

    payload = kis_collector.collectKisMarketDataOnce(
        env={
            "HWISTOCK_KIS_MARKET_READ_NETWORK_ENABLED": "true",
            "HWISTOCK_KIS_MIN_CALL_GAP_SEC": "0",
            "HWISTOCK_CALENDAR_PATH": str(calendar),
        },
        adapter=adapter,
        at=datetime.fromisoformat("2026-06-06T09:30:00+09:00"),
    )

    assert payload["status"] == "safe_skip_market_session_gate"
    assert payload["calendar_context"]["kis_realtime_expected"] is False
    assert all(row["endpoint_called"] is False for row in payload["input_results"])
    assert adapter.calls == []


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


def test_flash_valid_buy_now_generates_paper_order_intent():
    doc = ao.buildFlashTradeDocument(
        pro_artifact={"artifact_id": "art_pro_hourly_20260605_0900"},
        recent_events=[{"source_event_id": "naver:news:1"}],
        kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260605_0939"}],
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        provider_actions=[
            {
                "symbol": "005930",
                "action": "BUY_NOW",
                "quantity": 10,
                "entry_price_limit": 10000,
                "target_price": 10500,
                "stop_loss_price": 9800,
                "planned_order_cash_krw": 100000,
                "confidence": 0.8,
                "thesis": "KIS 후보와 소스가 일치한 BUY_NOW",
                "why_now": "거래대금 후보 확인",
            }
        ],
        produced_at_kst=NOW,
    )
    validation = ao.validateFlashTradeDocument(doc, compiled_watch=[_compiled_watch("005930")])
    assert validation["ok"], validation["errors"]

    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        validation["document"],
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        now_kst=NOW,
    )

    assert pipeline["accepted_count"] == 1
    intent = pipeline["accepted_intents"][0]
    assert intent["action"] == "BUY_NOW"
    assert intent["action_source"] == "deepseek_flash_provider"
    assert intent["entry_price_limit"] == 10000
    assert intent["target_price"] == 10500
    assert intent["stop_loss_price"] == 9800
    assert intent["paper_only"] is True
    assert intent["broker_adapter"] == "kis_paper"
    assert intent["venue_route"] == "KRX"


def test_gpt_fallback_without_kis_quote_rejects_paper_intent_even_after_wait_buy_downgrade():
    morning = {
        "schema_version": "morning_watchlist/v1",
        "artifact_id": "art_morning_watchlist_20260605_0715",
        "items": [{"ticker": "005930", "stance": "eligible_for_flash_review", "source_refs": ["naver:news:1"]}],
    }
    doc = ao.buildFlashTradeDocument(
        pro_artifact={"artifact_id": "art_pro_hourly_20260605_0900"},
        recent_events=[],
        kis_market_snapshots=[],
        compiled_watch=[],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        morning_watchlist=morning,
        provider_actions=[
            {
                "symbol": "005930",
                "action": "BUY_NOW",
                "entry_price_limit": 10000,
                "target_price": 10500,
                "stop_loss_price": 9800,
                "planned_order_cash_krw": 100000,
                "confidence": 0.8,
            }
        ],
        produced_at_kst=NOW,
    )
    assert doc["actions"][0]["action"] == "WAIT_BUY"

    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=ao.buildProvisionalCompiledWatchFromMorningWatchlist(
            morning,
            produced_at_kst=NOW,
        ),
        portfolio_snapshot={"holdings": []},
        order_state_snapshot={"pending_orders": []},
        now_kst=NOW,
    )

    assert pipeline["accepted_count"] == 0
    assert "kis_quote_confirmation_required_before_paper_intent" in pipeline["rejected_actions"][0]["reasons"]


def test_paper_intent_normalizes_krx_tick_size_before_cash_order():
    doc = ao.buildFlashTradeDocument(
        pro_artifact={"artifact_id": "art_pro_hourly_20260605_0900"},
        recent_events=[{"source_event_id": "naver:news:1"}],
        kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260605_0939"}],
        compiled_watch=[_compiled_watch("040350")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        provider_actions=[
            {
                "symbol": "040350",
                "action": "WAIT_BUY",
                "entry_price_limit": 9303,
                "target_price": 9630,
                "stop_loss_price": 9069,
                "planned_order_cash_krw": 100000,
                "confidence": 0.7,
            }
        ],
        produced_at_kst=NOW,
    )

    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=[_compiled_watch("040350")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        now_kst=NOW,
    )

    assert pipeline["accepted_count"] == 1
    intent = pipeline["accepted_intents"][0]
    assert intent["raw_order_price"] == 9303
    assert intent["order_price"] == 9300
    assert intent["entry_price_limit"] == 9300
    assert intent["krx_tick_size"] == 10
    assert intent["order_price_adjusted_to_krx_tick"] is True


def test_positive_int_parser_handles_decimal_price_strings_without_digit_concatenation():
    assert engine._parse_positive_int("9303.0") == 9303
    assert engine._parse_positive_int(9303.0) == 9303
    assert engine._parse_positive_int("9,303") == 9303
    assert engine._parse_positive_int("₩9,303") == 9303
    assert engine._parse_positive_int("9,303원") == 9303
    assert engine._parse_positive_int("2.0") == 2
    assert engine._parse_positive_int(True) == 0


def test_paper_intent_decimal_price_strings_do_not_expand_order_price_or_quantity():
    doc = ao.buildFlashTradeDocument(
        pro_artifact={"artifact_id": "art_pro_hourly_20260605_0900"},
        recent_events=[{"source_event_id": "naver:news:1"}],
        kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260605_0939"}],
        compiled_watch=[_compiled_watch("040350")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        provider_actions=[
            {
                "symbol": "040350",
                "action": "WAIT_BUY",
                "entry_price_limit": "9303.0",
                "target_price": "9,630.0원",
                "stop_loss_price": "₩9,069.0",
                "planned_order_cash_krw": "100,000.0",
                "confidence": 0.7,
            }
        ],
        produced_at_kst=NOW,
    )

    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=[_compiled_watch("040350")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0939", "pending_orders": []},
        now_kst=NOW,
    )

    assert pipeline["accepted_count"] == 1
    intent = pipeline["accepted_intents"][0]
    assert intent["raw_order_price"] == 9303
    assert intent["order_price"] == 9300
    assert intent["quantity"] == 10
    assert intent["target_price"] == 9630
    assert intent["stop_loss_price"] == 9069


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


def test_position_management_action_does_not_create_paper_intent():
    doc = ao.buildFlashTradeDocument(
        pro_artifact={"artifact_id": "art_pro_hourly_20260605_0900"},
        recent_events=[],
        kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260605_0939"}],
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0939", "holdings": []},
        order_state_snapshot={
            "artifact_id": "art_order_state_20260605_0939",
            "pending_orders": [
                {
                    "symbol": "005930",
                    "action": "WAIT_BUY",
                    "submitted_at_kst": "2026-06-05T09:32:00+09:00",
                    "entry_price_limit": 10000,
                    "target_price": 10500,
                    "stop_loss_price": 9800,
                    "quantity": 10,
                }
            ],
        },
        produced_at_kst=NOW,
    )

    assert doc["document_kind"] == "POSITION_MANAGEMENT"
    assert doc["actions"][0]["action"] == "NO_NEW_ENTRY"
    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=[_compiled_watch("005930")],
        portfolio_snapshot={"holdings": []},
        order_state_snapshot={"pending_orders": [{"symbol": "005930"}]},
        now_kst=NOW,
    )

    assert pipeline["accepted_count"] == 0
    assert "position_management_action_not_entry" in pipeline["rejected_actions"][0]["reasons"]


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
    status["calendar"]["isTradingDay"] = True
    status["calendar"]["krxOrderSessionOpen"] = True
    status["marketData"]["state"] = "source_configured"
    status["routing"]["venue"] = "KRX"
    first = executor.evaluateIntentExecutionPreflight(
        intent,
        status=status,
        account_truth={
            "source": "unit_test_kis_truth",
            "balance_status": "pass",
            "buyable_status": "pass",
            "available_cash_krw": 2_000_000,
            "current_holdings_count": 0,
        },
    )
    assert first["ok"] is True, first["errors"]
    executor.markIntentConsumed(intent["idempotency_key"])
    second = executor.evaluateIntentExecutionPreflight(
        intent,
        status=status,
        account_truth={
            "source": "unit_test_kis_truth",
            "balance_status": "pass",
            "buyable_status": "pass",
            "available_cash_krw": 2_000_000,
            "current_holdings_count": 0,
        },
    )
    assert second["ok"] is False
    assert "duplicate_intent_idempotency_key" in second["errors"]

    exit_decision = executor.evaluateRealtimeExitDecision(
        {"symbol": "005930", "stop_loss": 9800, "take_profit": 10500, "highest_price": 10400, "trailing_stop_pct": 1.2},
        {"price": 9790},
    )
    assert exit_decision["exit_required"] is True
    assert exit_decision["exit_reason"] == "stop_loss"
    assert exit_decision["depends_on_next_flash_tick"] is False


def _disable_dashboard_account_network(monkeypatch):
    monkeypatch.setenv("HWISTOCK_DASHBOARD_ACCOUNT_READ_ENABLED", "false")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_PRODUCT_CODE", "01")
    monkeypatch.delenv("HWISTOCK_CALENDAR_PATH", raising=False)


def test_unit015_operator_snapshot_is_read_only_and_exposes_local_account_summary(tmp_path: Path, monkeypatch):
    _disable_dashboard_account_network(monkeypatch)
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
    assert snapshot["safety"]["rawAccountDisplayed"] is True
    assert snapshot["readiness"]["operationalTradingReadiness"] is False
    assert snapshot["summary"]["accountId"] == "12345678-01"
    assert snapshot["summary"]["cashBalance"] == "잔고 조회 비활성"
    assert snapshot["summary"]["reserveBalance"] == 500_000
    assert snapshot["summary"]["realizedPnl"] == "실현손익 조회 비활성"
    assert snapshot["summary"]["accountRefreshStatus"] == "skipped_disabled_by_env"
    assert snapshot["summary"]["accountRefreshAttempted"] is False
    assert snapshot["summary"]["accountRefreshAllowedBySession"] is True
    assert snapshot["summary"]["dashboardAccountSummaryOnly"] is True
    assert snapshot["summary"]["usableForOrderPreflight"] is False
    assert snapshot["summary"]["dashboardAccountSummaryReusedForOrder"] is False
    assert snapshot["summary"]["orderPreflightTruthSource"] == "trading_account_truth"
    assert snapshot["summary"]["accountAsOfKst"] == "2026-06-05T09:40:00+09:00"
    assert snapshot["summary"]["dashboardSnapshotAtKst"] == "2026-06-05T09:40:00+09:00"
    assert snapshot["runtime"]["dashboardAccountSummary"]["accountRefreshStatus"] == "skipped_disabled_by_env"
    assert snapshot["runtime"]["dashboardAccountSummary"]["usableForOrderPreflight"] is False
    assert snapshot["readinessTruth"]["headline"] == "PAPER_EXPERIMENT_BLOCKED"
    assert snapshot["readinessTruth"]["serviceVisibilityIsNotReadiness"] is True
    assert snapshot["readinessTruth"]["paperNetworkEnabled"] is True
    assert snapshot["readinessTruth"]["paperOrderEnabled"] is False
    assert snapshot["readinessTruth"]["paperExperimentReady"] is False
    assert snapshot["readinessTruth"]["operationalTradingReadinessBlocksPaperOperation"] is False
    assert snapshot["readinessTruth"]["paperOrdersSubmitted"] is False
    assert snapshot["readinessTruth"]["paperObservationAccepted"] is False
    assert snapshot["readinessTruth"]["operationalTradingReadiness"] is False
    assert "paper_order_loop_disabled" in snapshot["readinessTruth"]["blockers"]
    assert "blocked_source_unconfigured" in snapshot["readinessTruth"]["blockers"]
    assert "paper_orders_not_submitted" in snapshot["readinessTruth"]["evidenceGaps"]

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


def test_unit015_account_summary_refreshes_stale_pnl_failure_cache(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HWISTOCK_DASHBOARD_ACCOUNT_READ_ENABLED", "true")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_PRODUCT_CODE", "01")
    monkeypatch.setenv("HWISTOCK_KIS_HEALTH_SYMBOL", "005930")
    cache_path = tmp_path / "account" / "dashboard-account-summary-latest.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": "dashboard_account_summary/v0",
                "accountId": "12345678-01",
                "cashBalance": 9_950_000,
                "reserveBalance": 500_000,
                "todayPnl": "손익 조회 실패",
                "realizedPnl": "실현손익 조회 실패",
                "openPositions": 0,
                "status": "warn",
                "source": "kis-live-read",
                "rawProviderPayloadDisplayed": False,
                "credentialValuesPrinted": False,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    fresh_mtime = operator_console.parseKstTime("2026-06-05T09:39:30+09:00").timestamp()
    os.utime(cache_path, (fresh_mtime, fresh_mtime))
    old_mtime = operator_console.parseKstTime("2026-06-05T09:00:00+09:00").timestamp()
    os.utime(cache_path, (old_mtime, old_mtime))

    class FakeDashboardAdapter:
        def __init__(self, *, env, transport):
            self.env = env
            self.transport = transport

        def missingEnvKeys(self):
            return []

        def inquireAccountSummaryForDashboard(self, token, symbol):
            assert token == "fake-token"
            assert symbol == "005930"
            return {
                "status": "warn",
                "account_label": "12345678-01",
                "cash_balance_krw": 9_950_000,
                "total_eval_krw": 9_950_000,
                "stock_eval_krw": 0,
                "today_pnl_krw": -84_200,
                "realized_pnl_krw": 12_000,
                "positions_count": 0,
                "balance_status": "pass",
                "buyable_status": "warn",
                "realized_pnl_status": "pass",
                "credential_values_printed": False,
                "raw_response_stored": False,
            }

    monkeypatch.setattr(operator_console, "KisPaperAdapter", FakeDashboardAdapter)
    monkeypatch.setattr(
        operator_console,
        "loadKisPaperAccessToken",
        lambda adapter, env, now: ({"status": "pass", "token_present": True}, "fake-token", True),
    )
    monkeypatch.setattr(operator_console, "tokenCacheRevokeSkippedStep", lambda: None)

    summary = operator_console.buildDashboardAccountSummary(
        operator_console.parseKstTime("2026-06-05T09:40:00+09:00"),
        dataRoot=tmp_path,
    )

    assert summary["source"] == "kis-live-read"
    assert summary["cashBalance"] == 9_950_000
    assert summary["todayPnl"] == -84_200
    assert summary["realizedPnl"] == 12_000
    assert summary["balanceStatus"] == "pass"
    assert summary["buyableStatus"] == "warn"
    assert summary["realizedPnlStatus"] == "pass"
    assert summary["accountRefreshAttempted"] is True
    assert summary["dashboardSnapshotAtKst"] == "2026-06-05T09:40:00+09:00"
    assert summary["accountAsOfKst"] == "2026-06-05T09:40:00+09:00"

    refreshed = json.loads(cache_path.read_text(encoding="utf-8"))
    assert refreshed["todayPnl"] == -84_200
    assert refreshed["realizedPnl"] == 12_000
    assert refreshed["credentialValuesPrinted"] is False


def test_unit015_fresh_cash_only_cache_is_display_usable_without_provider_refresh(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("HWISTOCK_DASHBOARD_ACCOUNT_READ_ENABLED", "true")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_PRODUCT_CODE", "01")
    cache_path = tmp_path / "account" / "dashboard-account-summary-latest.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": "dashboard_account_summary/v0",
                "accountId": "12345678-01",
                "cashBalance": 9_950_000,
                "reserveBalance": 500_000,
                "todayPnl": "손익 조회 실패",
                "realizedPnl": "실현손익 조회 실패",
                "openPositions": 0,
                "status": "warn",
                "source": "kis-live-read",
                "rawProviderPayloadDisplayed": False,
                "credentialValuesPrinted": False,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    fresh_mtime = operator_console.parseKstTime("2026-06-05T09:39:30+09:00").timestamp()
    os.utime(cache_path, (fresh_mtime, fresh_mtime))

    class ForbiddenDashboardAdapter:
        def __init__(self, *, env, transport):
            raise AssertionError("fresh cash-only dashboard cache must skip provider refresh")

    monkeypatch.setattr(operator_console, "KisPaperAdapter", ForbiddenDashboardAdapter)

    summary = operator_console.buildDashboardAccountSummary(
        operator_console.parseKstTime("2026-06-05T09:40:00+09:00"),
        dataRoot=tmp_path,
    )

    assert summary["source"] == "dashboard-account-cache"
    assert summary["cashBalance"] == 9_950_000
    assert summary["todayPnl"] == "손익 조회 실패"
    assert summary["accountRefreshStatus"] == "skipped_cache_ttl"
    assert summary["accountRefreshAttempted"] is False
    assert summary["accountRefreshAllowedBySession"] is True
    assert summary["dashboardSnapshotAtKst"] == "2026-06-05T09:40:00+09:00"
    assert summary["accountAsOfKst"] == "2026-06-05T09:39:30+09:00"


def test_unit015_weekend_dashboard_account_summary_uses_fresh_cache_without_market_session(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("HWISTOCK_DASHBOARD_ACCOUNT_READ_ENABLED", "true")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_PRODUCT_CODE", "01")
    cache_path = tmp_path / "account" / "dashboard-account-summary-latest.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": "dashboard_account_summary/v0",
                "accountId": "12345678-01",
                "cashBalance": 9_950_000,
                "reserveBalance": 500_000,
                "todayPnl": -84_200,
                "realizedPnl": 12_000,
                "openPositions": 0,
                "status": "cached_pass",
                "source": "kis-live-read",
                "rawProviderPayloadDisplayed": False,
                "credentialValuesPrinted": False,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    fresh_mtime = operator_console.parseKstTime("2026-06-06T11:29:30+09:00").timestamp()
    os.utime(cache_path, (fresh_mtime, fresh_mtime))

    class ForbiddenDashboardAdapter:
        def __init__(self, *, env, transport):
            raise AssertionError("fresh dashboard cache must skip provider account read")

    monkeypatch.setattr(operator_console, "KisPaperAdapter", ForbiddenDashboardAdapter)

    summary = operator_console.buildDashboardAccountSummary(
        operator_console.parseKstTime("2026-06-06T11:30:00+09:00"),
        dataRoot=tmp_path,
    )

    assert summary["source"] == "dashboard-account-cache"
    assert summary["cashBalance"] == 9_950_000
    assert summary["todayPnl"] == -84_200
    assert summary["marketSessionRequired"] is False
    assert summary["accountRefreshAllowed"] is True
    assert summary["accountRefreshAllowedBySession"] is True
    assert summary["accountRefreshAttempted"] is False
    assert summary["accountRefreshStatus"] == "skipped_cache_ttl"
    assert summary["dashboardSnapshotAtKst"] == "2026-06-06T11:30:00+09:00"
    assert summary["accountAsOfKst"] == "2026-06-06T11:29:30+09:00"
    assert summary["dashboardAccountSummaryOnly"] is True
    assert summary["usableForOrderPreflight"] is False
    assert summary["orderPreflightTruthSource"] == "trading_account_truth"
    assert summary["marketSessionGate"]["allowed"] is True
    assert summary["marketSessionGate"]["step"] == "dashboard_account_summary_market_session_gate"


def test_unit015_dashboard_account_summary_provider_failure_falls_back_to_last_cache(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("HWISTOCK_DASHBOARD_ACCOUNT_READ_ENABLED", "true")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_PRODUCT_CODE", "01")
    monkeypatch.setenv("HWISTOCK_KIS_HEALTH_SYMBOL", "005930")
    cache_path = tmp_path / "account" / "dashboard-account-summary-latest.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": "dashboard_account_summary/v0",
                "accountId": "12345678-01",
                "cashBalance": 8_880_000,
                "reserveBalance": 500_000,
                "todayPnl": -12_000,
                "realizedPnl": 3_000,
                "openPositions": 1,
                "status": "cached_pass",
                "source": "kis-live-read",
                "rawProviderPayloadDisplayed": False,
                "credentialValuesPrinted": False,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    old_mtime = operator_console.parseKstTime("2026-06-05T09:00:00+09:00").timestamp()
    os.utime(cache_path, (old_mtime, old_mtime))

    class FailingDashboardAdapter:
        def __init__(self, *, env, transport):
            self.env = env
            self.transport = transport

        def missingEnvKeys(self):
            return []

        def inquireAccountSummaryForDashboard(self, token, symbol):
            assert token == "fake-token"
            assert symbol == "005930"
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(operator_console, "KisPaperAdapter", FailingDashboardAdapter)
    monkeypatch.setattr(
        operator_console,
        "loadKisPaperAccessToken",
        lambda adapter, env, now: ({"status": "pass", "token_present": True}, "fake-token", True),
    )

    summary = operator_console.buildDashboardAccountSummary(
        operator_console.parseKstTime("2026-06-06T11:30:00+09:00"),
        dataRoot=tmp_path,
    )

    assert summary["status"] == "cached_provider_unavailable"
    assert summary["source"] == "dashboard-account-cache"
    assert summary["cashBalance"] == 8_880_000
    assert summary["todayPnl"] == -12_000
    assert summary["accountRefreshStatus"] == "provider_error_cache_fallback"
    assert summary["accountCacheStatus"] == "fallback_stale"
    assert summary["accountRefreshAttempted"] is True
    assert summary["accountRefreshAllowedBySession"] is True
    assert summary["dashboardSnapshotAtKst"] == "2026-06-06T11:30:00+09:00"
    assert summary["accountAsOfKst"] == "2026-06-05T09:00:00+09:00"
    assert summary["usableForOrderPreflight"] is False
    assert summary["errorType"] == "RuntimeError"


def test_unit015_account_summary_preserves_zero_pnl_from_runner_evidence(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_PRODUCT_CODE", "01")
    evidence_path = tmp_path / "evidence" / "2026-06-05" / "kis-paper-continuous-latest.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "step": "balance_inquire",
                        "status": "pass",
                        "dashboard_account_summary": {
                            "cash_balance_krw": 10_000_000,
                            "total_eval_krw": 10_000_000,
                            "stock_eval_krw": 0,
                            "today_pnl_krw": 0,
                            "positions_count": 0,
                        },
                    },
                    {
                        "step": "realized_pnl_inquire",
                        "status": "pass",
                        "dashboard_realized_pnl_summary": {
                            "realized_pnl_krw": 0,
                            "real_eval_pnl_krw": 0,
                            "eval_pnl_sum_krw": 0,
                        },
                    },
                    {
                        "step": "buyable_inquire_psbl_order",
                        "status": "warn",
                        "dashboard_buyable_summary": {"buyable_cash_krw": None},
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    summary = operator_console.buildDashboardAccountSummary(
        operator_console.parseKstTime("2026-06-05T09:40:00+09:00"),
        dataRoot=tmp_path,
        dayKey="2026-06-05",
    )

    assert summary["source"] == "kis-paper-runner-evidence"
    assert summary["cashBalance"] == 10_000_000
    assert summary["todayPnl"] == 0
    assert summary["realizedPnl"] == 0
    assert summary["openPositions"] == 0
    assert summary["balanceStatus"] == "pass"
    assert summary["buyableStatus"] == "warn"
    assert summary["realizedPnlStatus"] == "pass"
    assert summary["accountRefreshStatus"] == "skipped_runner_evidence"
    assert summary["accountCacheStatus"] == "runner_evidence"
    assert summary["accountRefreshAttempted"] is False
    assert summary["dashboardSnapshotAtKst"] == "2026-06-05T09:40:00+09:00"


def test_unit015_stale_runner_evidence_falls_back_after_provider_failure(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HWISTOCK_DASHBOARD_ACCOUNT_READ_ENABLED", "true")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_PAPER_ACCOUNT_PRODUCT_CODE", "01")
    monkeypatch.setenv("HWISTOCK_KIS_HEALTH_SYMBOL", "005930")
    evidence_path = tmp_path / "evidence" / "2026-06-05" / "kis-paper-continuous-latest.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(
        json.dumps(
            {
                "timestamp_kst": "2026-06-05T09:00:00+09:00",
                "steps": [
                    {
                        "step": "balance_inquire",
                        "status": "pass",
                        "dashboard_account_summary": {
                            "cash_balance_krw": 7_770_000,
                            "today_pnl_krw": None,
                            "positions_count": 2,
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    old_mtime = operator_console.parseKstTime("2026-06-05T09:00:00+09:00").timestamp()
    os.utime(evidence_path, (old_mtime, old_mtime))

    class FailingDashboardAdapter:
        def __init__(self, *, env, transport):
            self.env = env
            self.transport = transport

        def missingEnvKeys(self):
            return []

        def inquireAccountSummaryForDashboard(self, token, symbol):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(operator_console, "KisPaperAdapter", FailingDashboardAdapter)
    monkeypatch.setattr(
        operator_console,
        "loadKisPaperAccessToken",
        lambda adapter, env, now: ({"status": "pass", "token_present": True}, "fake-token", True),
    )

    summary = operator_console.buildDashboardAccountSummary(
        operator_console.parseKstTime("2026-06-05T09:40:00+09:00"),
        dataRoot=tmp_path,
        dayKey="2026-06-05",
    )

    assert summary["status"] == "stale_runner_evidence_provider_unavailable"
    assert summary["source"] == "kis-paper-runner-evidence"
    assert summary["cashBalance"] == 7_770_000
    assert summary["openPositions"] == 2
    assert summary["accountRefreshStatus"] == "provider_error_runner_evidence_fallback"
    assert summary["accountCacheStatus"] == "stale_runner_evidence_fallback"
    assert summary["accountRefreshAttempted"] is True
    assert summary["dashboardSnapshotAtKst"] == "2026-06-05T09:40:00+09:00"
    assert summary["accountAsOfKst"] == "2026-06-05T09:00:00+09:00"
    assert summary["usableForOrderPreflight"] is False
    assert summary["errorType"] == "RuntimeError"


def test_unit015_operator_snapshot_allows_order_enabled_paper_experiment_without_live_contradiction(tmp_path: Path, monkeypatch):
    _disable_dashboard_account_network(monkeypatch)
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
    assert snapshot["runtime"]["kisPaperRunnerServicePolicy"]["orderFlagContradictsReadiness"] is False
    assert "systemd_order_enabled_contradicts_readiness" not in snapshot["readinessTruth"]["blockers"]
    assert "live_production_readiness_not_applicable" in snapshot["readinessTruth"]["evidenceGaps"]
    assert any(entry["code"] == "SYSTEMD_ORDER_FLAG" and entry["message"] == "enabled" for entry in snapshot["auditLog"])


def test_unit015_operator_snapshot_uses_live_systemd_effective_policy(tmp_path: Path, monkeypatch):
    _disable_dashboard_account_network(monkeypatch)
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
    monkeypatch.setattr(operator_console, "DEFAULT_RUNNER_SERVICE_PATHS", (safe_unit,))
    monkeypatch.setattr(
        operator_console,
        "inspectLiveKisPaperRunnerPolicy",
        lambda: {
            "schema_version": "kis_paper_runner_live_policy/v0",
            "available": True,
            "source": "unit_test_live_systemd",
            "paperNetworkEnabledByLiveUnit": True,
            "paperOrderEnabledByLiveUnit": True,
            "activeState": "inactive",
            "subState": "dead",
            "timerActiveState": "active",
            "credentialValuesPrinted": False,
        },
    )

    snapshot = operator_console.buildOperatorConsoleSnapshot(
        "2026-06-05T09:40:00",
        dataRoot=tmp_path,
    )

    policy = snapshot["runtime"]["kisPaperRunnerServicePolicy"]
    assert policy["repoPolicy"]["paperOrderEnabledByService"] is False
    assert policy["livePolicy"]["available"] is True
    assert policy["paperOrderEnabledEffective"] is True
    assert snapshot["readinessTruth"]["paperOrderEnabled"] is True
    assert policy["orderFlagContradictsReadiness"] is False
    assert "systemd_order_enabled_contradicts_readiness" not in snapshot["readinessTruth"]["blockers"]
    assert "live_production_readiness_not_applicable" in snapshot["readinessTruth"]["evidenceGaps"]
    assert any(entry["code"] == "SYSTEMD_ORDER_FLAG" and entry["message"] == "enabled" for entry in snapshot["auditLog"])


def test_unit015_operator_snapshot_maps_runtime_artifacts_to_dashboard_rows(tmp_path: Path, monkeypatch):
    _disable_dashboard_account_network(monkeypatch)
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
    assert snapshot["runtime"]["artifactFreshness"]["allRequiredFresh"] is True
    assert snapshot["intelligence"][0]["source"] == "open_dart"
    assert snapshot["intelligence"][0]["title"] == "주요사항보고서"
    assert any("DeepSeek Pro" in row["subject"] for row in snapshot["aiThread"])
    assert any(entry["code"] == "KIS_rest_volume_rank" for entry in snapshot["auditLog"])


def test_unit015_operator_snapshot_marks_stale_runtime_artifact_as_blocker(tmp_path: Path, monkeypatch):
    _disable_dashboard_account_network(monkeypatch)
    (tmp_path / "kis-market" / "2026-06-05").mkdir(parents=True)
    kis_market = tmp_path / "kis-market" / "2026-06-05" / "kis-market-snapshot-latest.json"
    kis_market.write_text(
        json.dumps({"produced_at_kst": "2026-06-05T09:00:00+09:00", "input_results": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    os.utime(kis_market, (1, 1))

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
        "2026-06-05T09:40:00+09:00",
        dataRoot=tmp_path,
        serviceUnitPaths=[safe_unit],
    )

    freshness = snapshot["runtime"]["artifactFreshness"]
    assert freshness["artifacts"]["kisMarket"]["stale"] is True
    assert "artifact_stale:kisMarket" in snapshot["readinessTruth"]["evidenceGaps"]
    assert any(
        entry["code"] == "ARTIFACT_kisMarket" and entry["level"] == "warn" and "stale" in entry["message"]
        for entry in snapshot["auditLog"]
    )
