"""
HWISTOCK-UNIT-010 focused tests for the continuous KIS paper runner.
No real KIS network call is made; tests use an injected fake transport.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import paper_trading_ledger as ledger  # noqa: E402
from service import HwiStockRunnerService as base_runner  # noqa: E402
from service import kis_paper_continuous_runner as continuous  # noqa: E402
from service.kis_paper_adapter import (  # noqa: E402
    KisPaperAdapter,
    KisPaperAdapterError,
    describeKisPaperEnv,
    summarizeKisBalancePayload,
    summarizeKisRealizedPnlPayload,
    validatePaperBaseUrl,
)


class FakeTransport:
    def __init__(self, *, order_status="pass"):
        self.calls = []
        self.order_status = order_status

    def request_json(self, method, url, *, headers=None, body=None, timeout=20):
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {}), "body": dict(body or {}) if body else None})
        if url.endswith("/oauth2/tokenP"):
            return {"http_status": 200, "payload": {"rt_cd": "0", "access_token": "fake-token"}}
        if "/uapi/domestic-stock/v1/trading/order-cash" in url:
            rt_cd = "0" if self.order_status == "pass" else "1"
            return {"http_status": 200, "payload": {"rt_cd": rt_cd, "msg_cd": "ok" if rt_cd == "0" else "reject"}}
        if "/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl" in url:
            return {
                "http_status": 200,
                "payload": {
                    "rt_cd": "0",
                    "msg_cd": "ok",
                    "output1": [{"pdno": "005930", "rlzt_pfls": "12000"}],
                    "output2": {"rlzt_pfls": "34000", "real_evlu_pfls": "34000", "evlu_pfls_smtl_amt": "-84200"},
                },
            }
        if "/uapi/domestic-stock/v1/trading/inquire-balance" in url:
            return {
                "http_status": 200,
                "payload": {
                    "rt_cd": "0",
                    "msg_cd": "ok",
                    "output1": [{"pdno": "005930"}, {"pdno": "000660"}],
                    "output2": [
                        {
                            "dnca_tot_amt": "1860000",
                            "tot_evlu_amt": "2140000",
                            "scts_evlu_amt": "280000",
                            "evlu_pfls_smtl_amt": "-84200",
                        }
                    ],
                },
            }
        if "/uapi/domestic-stock/v1/trading/inquire-psbl-order" in url:
            return {
                "http_status": 200,
                "payload": {"rt_cd": "0", "msg_cd": "ok", "output": {"ord_psbl_cash": "1720000"}},
            }
        return {"http_status": 200, "payload": {"rt_cd": "0", "msg_cd": "ok", "output1": [{"row": 1}]}}


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    base_runner.reset_runtime_for_tests()
    continuous.resetContinuousPaperRunnerForTests()
    for key in (
        "HWISTOCK_KIS_PAPER_NETWORK_ENABLED",
        "HWISTOCK_KIS_PAPER_ORDER_ENABLED",
        "HWISTOCK_MARKET_DATA_SOURCE",
        "HWISTOCK_CALENDAR_PATH",
        "HWISTOCK_KILL_SWITCH",
        "HWISTOCK_DATA_DIR",
        "HWISTOCK_KIS_PAPER_STATE_FILE",
        "HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID",
        "HWISTOCK_ORDER_APPROVAL_FILE",
    ):
        monkeypatch.delenv(key, raising=False)
    yield
    base_runner.reset_runtime_for_tests()
    continuous.resetContinuousPaperRunnerForTests()


def _env():
    return {
        "KIS_PAPER_APP_KEY": "paper-app-key",
        "KIS_PAPER_APP_SECRET": "paper-app-secret",
        "KIS_PAPER_ACCOUNT_NO": "12345678",
        "KIS_PAPER_ACCOUNT_PRODUCT_CODE": "01",
        "KIS_PAPER_BASE_URL": "https://openapivts.koreainvestment.com:29443",
        "HWISTOCK_KIS_PAPER_NETWORK_ENABLED": "true",
        "HWISTOCK_MARKET_DATA_SOURCE": "local_fixture",
        "HWISTOCK_KIS_MIN_CALL_GAP_SEC": "0",
    }


def _calendar(tmp_path: Path, monkeypatch):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps({"validUntil": "2099-12-31T23:59:59+09:00"}), encoding="utf-8")
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(path))
    return path


def _order_approval(tmp_path: Path, env: dict, *, run_id: str = "approved-order-run-1") -> Path:
    path = tmp_path / f"{run_id}.approval.json"
    path.write_text(
        json.dumps(
            {
                "approved_order_run_id": run_id,
                "allow_paper_orders": True,
                "valid_until_kst": "2099-12-31T23:59:59+09:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    env["HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID"] = run_id
    env["HWISTOCK_ORDER_APPROVAL_FILE"] = str(path)
    return path


def test_default_systemd_runner_does_not_enable_orders():
    service_path = Path(__file__).resolve().parents[2] / "ops" / "systemd" / "user" / "hwistock-kis-paper-runner.service"
    service_text = service_path.read_text(encoding="utf-8")
    assert "--allow-paper-orders" not in service_text
    assert "Environment=HWISTOCK_KIS_PAPER_ORDER_ENABLED=true" not in service_text
    assert "Environment=HWISTOCK_KIS_PAPER_ORDER_ENABLED=false" in service_text


def test_paper_domain_guard_rejects_live_domain():
    assert validatePaperBaseUrl("https://openapivts.koreainvestment.com:29443").endswith(":29443")
    with pytest.raises(KisPaperAdapterError):
        validatePaperBaseUrl("https://openapi.koreainvestment.com:9443")


def test_env_summary_never_prints_values():
    summary = describeKisPaperEnv({"KIS_PAPER_APP_KEY": "x"})
    rendered = json.dumps(summary, ensure_ascii=False)
    assert "KIS_PAPER_APP_KEY" in rendered
    assert "paper-app-secret" not in rendered
    assert summary["credentialValuesPrinted"] is False


def test_adapter_blocks_missing_env_without_network():
    transport = FakeTransport()
    adapter = KisPaperAdapter(env={}, transport=transport)
    result = adapter.issueToken()
    assert result["status"] == "blocked_missing_env"
    assert transport.calls == []


def test_adapter_allows_only_krx_cash_order_with_fake_transport():
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=_env(), transport=transport)
    token_result, token = adapter.issueTokenWithValue()
    assert token_result["token_present"] is True
    assert token == "fake-token"

    blocked = adapter.placeCashOrder(token, {"symbol": "005930", "side": "buy", "quantity": 1, "venue_route": "NXT"})
    assert blocked["status"] == "blocked"
    assert blocked["broker_endpoint_called"] is False

    order = adapter.placeCashOrder(token, {"symbol": "005930", "side": "buy", "quantity": 1, "venue_route": "KRX"})
    assert order["broker_endpoint_called"] is True
    assert order["route"] == "KRX"
    assert any("/uapi/domestic-stock/v1/trading/order-cash" in call["url"] for call in transport.calls)


def test_adapter_account_summary_for_dashboard_extracts_display_values_without_raw_payload():
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=_env(), transport=transport)
    token_result, token = adapter.issueTokenWithValue()
    assert token_result["token_present"] is True

    summary = adapter.inquireAccountSummaryForDashboard(token, "005930")

    assert summary["status"] == "pass"
    assert summary["account_label"] == "12345678-01"
    assert summary["cash_balance_krw"] == 1_720_000
    assert summary["total_eval_krw"] == 2_140_000
    assert summary["stock_eval_krw"] == 280_000
    assert summary["today_pnl_krw"] == -84_200
    assert summary["positions_count"] == 2
    assert summary["credential_values_printed"] is False
    assert summary["raw_response_stored"] is False


def test_adapter_balance_summary_preserves_zero_pnl_value():
    summary = summarizeKisBalancePayload(
        {
            "http_status": 200,
            "payload": {
                "rt_cd": "0",
                "output1": [],
                "output2": [
                    {
                        "dnca_tot_amt": 10_000_000,
                        "tot_evlu_amt": 10_000_000,
                        "scts_evlu_amt": 0,
                        "evlu_pfls_smtl_amt": 0,
                    }
                ],
            },
        }
    )

    assert summary["cash_balance_krw"] == 10_000_000
    assert summary["stock_eval_krw"] == 0
    assert summary["today_pnl_krw"] == 0
    assert summary["positions_count"] == 0


def test_adapter_realized_pnl_uses_documented_endpoint_and_extracts_values():
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=_env(), transport=transport)
    token_result, token = adapter.issueTokenWithValue()
    assert token_result["token_present"] is True

    result = adapter.inquireRealizedPnl(token)

    assert result["status"] == "pass"
    assert result["step"] == "realized_pnl_inquire"
    assert result["row_count"] == 1
    assert result["dashboard_realized_pnl_summary"]["realized_pnl_krw"] == 34_000
    assert result["dashboard_realized_pnl_summary"]["real_eval_pnl_krw"] == 34_000
    assert result["dashboard_realized_pnl_summary"]["eval_pnl_sum_krw"] == -84_200
    realized_call = [call for call in transport.calls if "inquire-balance-rlz-pl" in call["url"]][0]
    assert "INQR_DVSN=00" in realized_call["url"]
    assert realized_call["headers"]["tr_id"] == "TTTC8494R"


def test_adapter_realized_pnl_summary_preserves_zero_value():
    summary = summarizeKisRealizedPnlPayload(
        {
            "http_status": 200,
            "payload": {
                "rt_cd": "0",
                "output2": {
                    "rlzt_pfls": 0,
                    "real_evlu_pfls": 0,
                    "evlu_pfls_smtl_amt": 0,
                },
            },
        }
    )

    assert summary["realized_pnl_krw"] == 0
    assert summary["real_eval_pnl_krw"] == 0
    assert summary["eval_pnl_sum_krw"] == 0


def test_observation_manifest_is_operator_controlled_not_fixed_duration():
    manifest = ledger.buildObservationWindowManifest(
        started_at_kst="2026-06-05T09:00:00+09:00",
        ended_at_kst="2026-06-05T10:00:00+09:00",
        operator_note="manual window",
    )
    assert manifest["duration_policy"] == "operator_selected"
    assert manifest["fixed_duration_days"] is None
    assert manifest["auto_stop_on_duration"] is False
    assert manifest["elapsed_seconds"] == 3600


def test_ledger_rejects_fake_broker_and_calculates_system_fields():
    snapshot = ledger.buildLedgerSnapshot(
        [
            {"event_kind": "fill", "symbol": "005930", "side": "buy", "quantity": 2, "price_krw": 10000},
            {"event_kind": "fill", "symbol": "000660", "side": "buy", "quantity": 1, "price_krw": 120000},
            {"event_kind": "fill", "symbol": "bad", "side": "buy", "quantity": 1, "price_krw": 1, "fake_fill": True},
        ],
        account_no="12345678",
    )
    assert snapshot["calculation_source"] == "system"
    assert snapshot["cash_krw"] == 1_860_000
    assert snapshot["positions"]["005930"]["quantity"] == 2
    assert snapshot["account_alias"].endswith("***5678")
    assert "forbidden_fake_field:fake_fill" in snapshot["errors"]
    assert snapshot["fake_broker_used"] is False


def test_continuous_status_exposes_false_readiness():
    status = continuous.evaluateContinuousPaperRunnerStatus(env={})
    assert status["continuousService"] is True
    assert status["paperRunReady"] is False
    assert status["operationalTradingReadiness"] is False
    assert status["durationPolicy"]["fixedDurationDays"] is None
    assert status["paperOrderEnabled"] is False


def test_order_flag_requires_operator_approval_file(tmp_path):
    env = {"HWISTOCK_KIS_PAPER_ORDER_ENABLED": "true"}
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env)
    assert status["paperOrderRequested"] is True
    assert status["paperOrderEnabled"] is False
    assert status["paperOrderApproval"]["reason"] == "HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID_missing"

    env["HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID"] = "approved-order-run-1"
    env["HWISTOCK_ORDER_APPROVAL_FILE"] = str(tmp_path / "missing.approval.json")
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env)
    assert status["paperOrderEnabled"] is False
    assert status["paperOrderApproval"]["reason"] == "HWISTOCK_ORDER_APPROVAL_FILE_not_found"

    _order_approval(tmp_path, env)
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env)
    assert status["paperOrderEnabled"] is True
    assert status["paperOrderApproval"]["reason"] == "operator_order_approval_verified"


def test_tick_stays_idle_when_paper_network_disabled():
    payload = continuous.runContinuousPaperTick(env={})
    assert payload["status"] == "idle_paper_network_disabled"
    assert payload["fixed_duration_days"] is None
    assert payload["live_domain_calls_made"] is False
    assert payload["fake_broker_used"] is False


def test_tick_blocks_intent_when_paper_order_flag_disabled(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    env = _env()
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(tmp_path / "data")
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
            "intent_id": "test-disabled-1",
            "idempotency_key": "test-disabled-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "venue_route": "KRX",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
        },
    )
    rendered = json.dumps(payload, ensure_ascii=False)
    assert payload["status"] == "ok"
    assert "paper-app-secret" not in rendered
    assert any(step.get("step") == "cash_order" and step.get("status") == "blocked_paper_order_disabled" for step in payload["steps"])
    assert not any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_with_fake_transport_processes_safe_krx_paper_intent_when_order_enabled(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(tmp_path / "data")
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
            "intent_id": "test-enabled-1",
            "idempotency_key": "test-enabled-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "venue_route": "KRX",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
        },
    )
    rendered = json.dumps(payload, ensure_ascii=False)
    assert payload["status"] == "ok"
    assert "paper-app-secret" not in rendered
    assert any(step.get("step") == "cash_order" and step.get("broker_endpoint_called") is True for step in payload["steps"])
    assert any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_blocks_non_krx_or_reserve_breach_before_order(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    env = _env()
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(tmp_path / "data")
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
            "intent_id": "test-risk-block-1",
            "idempotency_key": "test-risk-block-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "venue_route": "NXT",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 1_600_000,
            "current_holdings_count": 0,
        },
    )
    cash_order = [step for step in payload["steps"] if step.get("step") == "cash_order"][-1]
    assert cash_order["status"] == "blocked_risk_overlay"
    assert "kis_paper_order_route_must_be_krx" in cash_order["errors"]
    assert "minimum_cash_reserve_breach" in cash_order["errors"]
    order_calls = [call for call in transport.calls if "/order-cash" in call["url"]]
    assert order_calls == []


def test_tick_blocks_paper_order_outside_krx_regular_session(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(tmp_path / "data")
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T16:10:00",
        intent={
            "intent_id": "test-nxt-block-1",
            "idempotency_key": "test-nxt-block-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "order_price": 70000,
            "venue_route": "KRX",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    cash_order = [step for step in payload["steps"] if step.get("step") == "cash_order"][-1]
    assert cash_order["status"] == "blocked_risk_overlay"
    assert "kis_paper_order_requires_krx_regular_session" in cash_order["errors"]
    assert not any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_auto_loads_latest_intent_queue_and_persists_only_passed_order(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    intent_dir = data_root / "intents" / "2026-06-05"
    intent_dir.mkdir(parents=True)
    intent = {
        "schema_version": "paper_order_intent/v0",
        "intent_id": "intent-queue-1",
        "idempotency_key": "intent-queue-1",
        "flash_trade_document_ref": "flash-queue-1",
        "symbol": "005930",
        "side": "buy",
        "quantity": 1,
        "order_price": 70000,
        "venue_route": "KRX",
        "available_cash_krw": 2_000_000,
        "planned_order_cash_krw": 100_000,
        "current_holdings_count": 0,
        "valid_until_kst": "2026-06-05T09:50:00+09:00",
        "paper_only": True,
    }
    (intent_dir / "paper-order-intents-latest.jsonl").write_text(json.dumps(intent, ensure_ascii=False) + "\n", encoding="utf-8")

    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(data_root)
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
    )
    assert payload["intent_source"] == "latest_intent_queue"
    assert any(step.get("step") == "cash_order" and step.get("status") == "pass" for step in payload["steps"])
    state_path = data_root / "state" / "kis-paper-runner-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "intent-queue-1" in state["consumed_intent_keys"]
    assert state["pending_orders"][0]["symbol"] == "005930"


def test_tick_does_not_mark_intent_consumed_when_broker_warns(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(data_root)
    transport = FakeTransport(order_status="warn")
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
            "intent_id": "intent-warn-1",
            "idempotency_key": "intent-warn-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "order_price": 70000,
            "venue_route": "KRX",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    assert any(step.get("step") == "cash_order" and step.get("status") == "warn" for step in payload["steps"])
    assert any(
        step.get("step") == "local_state" and step.get("status") == "ambiguous_submit_requires_reconciliation"
        for step in payload["steps"]
    )
    state_path = data_root / "state" / "kis-paper-runner-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "intent-warn-1" not in state["consumed_intent_keys"]
    assert "intent-warn-1" in state["ambiguous_intent_keys"]

    retry_transport = FakeTransport(order_status="pass")
    retry_adapter = KisPaperAdapter(env=env, transport=retry_transport)
    retry_payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=retry_adapter,
        at_kst="2026-06-05T09:31:00",
        intent={
            "intent_id": "intent-warn-1",
            "idempotency_key": "intent-warn-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "order_price": 70000,
            "venue_route": "KRX",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    assert retry_payload["executionPreflight"]["ok"] is False
    assert "ambiguous_submit_requires_reconciliation" in retry_payload["executionPreflight"]["errors"]
    assert not any("/order-cash" in call["url"] for call in retry_transport.calls)
