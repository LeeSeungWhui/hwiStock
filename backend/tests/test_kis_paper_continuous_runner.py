"""
HWISTOCK-UNIT-010 focused tests for the continuous KIS paper runner.
No real KIS network call is made; tests use an injected fake transport.
"""

from __future__ import annotations

from datetime import datetime
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import ai_orchestration as ao  # noqa: E402
from lib import kis_paper_continuous_runtime as continuous_runtime  # noqa: E402
from lib import paper_trading_ledger as ledger  # noqa: E402
from lib import trading_engine as engine  # noqa: E402
from lib.kis_paper_token_cache import loadKisPaperAccessToken  # noqa: E402
from service import HwiStockRunnerService as base_runner  # noqa: E402
from service import kis_paper_continuous_runner as continuous  # noqa: E402
from service.kis_paper_adapter import (  # noqa: E402
    KisPaperAdapter,
    KisPaperAdapterError,
    describeKisPaperEnv,
    extractKisBalancePositionsPayload,
    extractKisDailyFillRowsPayload,
    summarizeKisBalancePayload,
    summarizeKisRealizedPnlPayload,
    validatePaperBaseUrl,
)


class FakeTransport:
    def __init__(
        self,
        *,
        order_status="pass",
        sellable_quantity="10",
        invalid_balance_once=False,
        balance_positions=None,
        daily_fills=None,
    ):
        self.calls = []
        self.order_status = order_status
        self.sellable_quantity = sellable_quantity
        self.invalid_balance_once = invalid_balance_once
        self.invalid_balance_returned = False
        self.balance_positions = balance_positions if balance_positions is not None else [{"pdno": "005930"}, {"pdno": "000660"}]
        self.daily_fills = daily_fills if daily_fills is not None else [{"row": 1}]

    def requestJson(self, method, url, *, headers=None, body=None, timeout=20):
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {}), "body": dict(body or {}) if body else None})
        if url.endswith("/oauth2/tokenP"):
            return {"http_status": 200, "payload": {"rt_cd": "0", "access_token": "fake-token"}}
        if url.endswith("/oauth2/Approval"):
            return {"http_status": 200, "payload": {"rt_cd": "0", "approval_key": "fake-approval-key"}}
        if "/uapi/domestic-stock/v1/trading/order-cash" in url:
            rt_cd = "0" if self.order_status == "pass" else "1"
            return {
                "http_status": 200,
                "payload": {
                    "rt_cd": rt_cd,
                    "msg_cd": "ok" if rt_cd == "0" else "reject",
                    "output": {"ODNO": "1234567890", "KRX_FWDG_ORD_ORGNO": "00123"},
                },
            }
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
            if self.invalid_balance_once and not self.invalid_balance_returned:
                self.invalid_balance_returned = True
                return {"http_status": 500, "payload": {"rt_cd": "1", "msg_cd": "EGW00121", "msg1": "유효하지 않은 token 입니다."}}
            return {
                "http_status": 200,
                "payload": {
                    "rt_cd": "0",
                    "msg_cd": "ok",
                    "output1": self.balance_positions,
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
        if "/uapi/domestic-stock/v1/trading/inquire-psbl-sell" in url:
            return {
                "http_status": 200,
                "payload": {"rt_cd": "0", "msg_cd": "ok", "output": {"ord_psbl_qty": self.sellable_quantity}},
            }
        if "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl" in url:
            return {
                "http_status": 200,
                "payload": {"rt_cd": "0", "msg_cd": "ok", "output": [{"odno": "1234567890"}]},
            }
        if "/uapi/domestic-stock/v1/quotations/chk-holiday" in url:
            return {
                "http_status": 200,
                "payload": {"rt_cd": "0", "msg_cd": "ok", "output": [{"bass_dt": "20260605", "opnd_yn": "Y"}]},
            }
        if "/uapi/domestic-stock/v1/trading/inquire-daily-ccld" in url:
            return {"http_status": 200, "payload": {"rt_cd": "0", "msg_cd": "ok", "output1": self.daily_fills}}
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
        "HWISTOCK_OPERATION_MODE",
        "HWISTOCK_MAX_DAILY_PAPER_ORDERS",
        "HWISTOCK_MAX_PAPER_NOTIONAL_KRW",
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
    path.write_text(
        json.dumps(
            {
                "validUntil": "2099-12-31T23:59:59+09:00",
                "sourceAuthority": "unit_test_calendar",
                "days": {
                    "2026-06-05": {
                        "dateKst": "2026-06-05",
                        "isTradingDay": True,
                        "krx": {
                            "regularOpen": "09:00",
                            "regularClose": "15:30",
                            "orderOpen": "09:00",
                            "orderClose": "15:00",
                        },
                        "nxt": {"open": "08:00", "close": "20:00"},
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(path))
    return path


def _order_approval(tmp_path: Path, env: dict, *, run_id: str = "approved-order-run-1") -> Path:
    path = tmp_path / f"{run_id}.approval.json"
    env["HWISTOCK_OPERATION_MODE"] = "paper_experiment"
    path.write_text(
        json.dumps(
            {
                "mode": "paper_experiment",
                "approved_order_run_id": run_id,
                "allow_paper_orders": True,
                "valid_for_date_kst": "2026-06-05",
                "valid_until_kst": "2099-12-31T23:59:59+09:00",
                "max_daily_orders": 20,
                "max_notional_krw": 2_000_000,
                "live_money_scope": "not_applicable",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    env["HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID"] = run_id
    env["HWISTOCK_ORDER_APPROVAL_FILE"] = str(path)
    return path


def _mark_order_grade_source(env: dict) -> None:
    env["HWISTOCK_MARKET_DATA_SOURCE"] = "kis_market_mode_aware"


def _load_approval_helper_module():
    helper_path = Path(__file__).resolve().parents[2] / "ops" / "systemd" / "ensure_paper_order_approval.py"
    spec = importlib.util.spec_from_file_location("ensure_paper_order_approval", helper_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_token_cache_uses_request_broker_json_adapter_without_private_request(tmp_path: Path):
    class CacheableAdapter:
        def __init__(self):
            self.calls = 0

        def requestBrokerJson(self):
            raise AssertionError("requestBrokerJson is only used as a capability marker")

        def issueTokenWithValue(self):
            self.calls += 1
            return {"step": "oauth_token", "status": "pass", "token_present": True}, f"fake-token-{self.calls}"

    adapter = CacheableAdapter()
    env = {"HWISTOCK_KIS_TOKEN_CACHE_FILE": str(tmp_path / "kis-token-cache.json")}
    now = datetime.fromisoformat("2026-06-06T09:00:00+09:00")

    first_result, first_token, first_managed = loadKisPaperAccessToken(adapter, env=env, now=now)
    second_result, second_token, second_managed = loadKisPaperAccessToken(adapter, env=env, now=now)

    assert adapter.calls == 1
    assert first_token == "fake-token-1"
    assert second_token == "fake-token-1"
    assert first_managed is True
    assert second_managed is True
    assert first_result["cache_hit"] is False
    assert second_result["step"] == "oauth_token_cache"
    assert second_result["cache_hit"] is True


def test_tick_invalidates_cached_token_once_when_account_step_rejects_it(tmp_path: Path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    state_dir = data_root / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "kis-paper-runner-state.json").write_text(
        json.dumps(
            {
                "schema_version": "kis_paper_runner_state/v0",
                "consumed_intent_keys": [],
                "consumed_trade_document_ids": [],
                "submitting_intent_keys": [],
                "ambiguous_intent_keys": [],
                "ambiguous_submits": [],
                "pending_orders": [
                    {
                        "idempotency_key": "pending-reconcile-1",
                        "symbol": "005930",
                        "submitted_at_kst": "2026-06-05T09:01:00+09:00",
                        "broker_endpoint_called": True,
                    }
                ],
                "submitted_order_history": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    env = _env()
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(data_root)
    env["HWISTOCK_KIS_TOKEN_CACHE_FILE"] = str(tmp_path / "kis-token-cache.json")
    transport = FakeTransport(invalid_balance_once=True)
    adapter = KisPaperAdapter(env=env, transport=transport)

    cached_result, cached_token, cached_managed = loadKisPaperAccessToken(
        adapter,
        env=env,
    )
    assert cached_result["cache_hit"] is False
    assert cached_token == "fake-token"
    assert cached_managed is True

    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
    )

    assert payload["intent_loaded"] is False
    assert payload["reconciliation_required"] is True
    assert any(
        step.get("step") == "kis_reconciliation_market_session_gate" and step.get("allowed") is True
        for step in payload["steps"]
    )
    balance_steps = [step for step in payload["steps"] if step.get("step") == "balance_inquire"]
    assert len(balance_steps) == 1
    assert balance_steps[0]["status"] == "pass"
    assert any(step.get("step") == "oauth_token_cache" and step.get("cache_hit") is True for step in payload["steps"])
    assert any(step.get("step") == "oauth_token_cache_invalidate" and step.get("status") == "pass" for step in payload["steps"])
    assert any(step.get("step") == "oauth_token" and step.get("cache_hit") is False for step in payload["steps"])


def test_reconciliation_promotes_pending_buy_to_holding_from_kis_balance(tmp_path: Path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    state_dir = data_root / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "kis-paper-runner-state.json").write_text(
        json.dumps(
            {
                "schema_version": "kis_paper_runner_state/v0",
                "consumed_intent_keys": ["intent-reconcile-1"],
                "consumed_trade_document_ids": [],
                "submitting_intent_keys": [],
                "ambiguous_intent_keys": [],
                "ambiguous_submits": [],
                "pending_orders": [
                    {
                        "idempotency_key": "intent-reconcile-1",
                        "flash_trade_document_ref": "flash-reconcile-1",
                        "symbol": "005930",
                        "side": "buy",
                        "quantity": 2,
                        "order_price": 70000,
                        "entry_price_limit": 70000,
                        "target_price": 72100,
                        "stop_loss_price": 67900,
                        "take_profit": 72100,
                        "stop_loss": 67900,
                        "trailing_stop_pct": 1.5,
                        "broker_order_no": "1234567890",
                        "krx_forwarding_order_orgno": "00123",
                        "submitted_at_kst": "2026-06-05T09:01:00+09:00",
                        "broker_endpoint_called": True,
                    }
                ],
                "holdings": None,
                "active_exits": None,
                "submitted_order_history": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    env = _env()
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(data_root)
    transport = FakeTransport(
        balance_positions=[
            {
                "pdno": "005930",
                "prdt_name": "삼성전자",
                "hldg_qty": "2",
                "ord_psbl_qty": "2",
                "pchs_avg_pric": "70000",
                "prpr": "70500",
                "evlu_amt": "141000",
                "evlu_pfls_amt": "1000",
            }
        ],
        daily_fills=[
            {
                "pdno": "005930",
                "sll_buy_dvsn_cd": "02",
                "odno": "1234567890",
                "tot_ccld_qty": "2",
                "ord_qty": "2",
                "rmn_qty": "0",
                "avg_prvs": "70000",
            }
        ],
    )
    adapter = KisPaperAdapter(env=env, transport=transport)

    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
    )

    reconciliation = [step for step in payload["steps"] if step.get("step") == "local_state_reconciliation"][-1]
    assert reconciliation["status"] == "pass"
    assert reconciliation["promoted_to_holdings_count"] == 1
    assert reconciliation["promoted_symbols"] == ["005930"]
    assert payload["account_truth"]["positions"][0]["quantity"] == 2
    assert payload["account_truth"]["daily_order_fills"][0]["filled_quantity"] == 2
    state = json.loads((state_dir / "kis-paper-runner-state.json").read_text(encoding="utf-8"))
    assert state["pending_orders"] == []
    holding = state["holdings"][0]
    assert holding["symbol"] == "005930"
    assert holding["position_state"] == "holding_confirmed"
    assert holding["quantity"] == 2
    assert holding["target_price"] == 72100
    assert holding["stop_loss_price"] == 67900
    assert holding["trailing_stop_pct"] == 1.5
    assert holding["broker_order_no"] == "1234567890"
    snapshot = continuous_runtime._order_state_snapshot_from_runner_state(state, now=datetime.fromisoformat("2026-06-05T09:31:00+09:00"))  # noqa: SLF001
    assert snapshot["holdings"][0]["symbol"] == "005930"
    assert snapshot["pending_orders"] == []
    assert not any("/order-cash" in call["url"] for call in transport.calls)


def test_reconciliation_refreshes_existing_holding_price_from_kis_balance():
    state = {
        "schema_version": "kis_paper_runner_state/v0",
        "pending_orders": [],
        "holdings": [
            {
                "symbol": "005930",
                "quantity": 2,
                "sellable_quantity": 2,
                "average_price": 70000,
                "current_price": 70000,
                "target_price": 72100,
                "stop_loss_price": 67900,
                "position_state": "holding_confirmed",
            }
        ],
    }
    account_truth = {
        "positions": [
            {
                "symbol": "005930",
                "name": "삼성전자",
                "quantity": 2,
                "sellable_quantity": 2,
                "average_price": 70000,
                "current_price": 70500,
                "eval_amount_krw": 141000,
                "pnl_krw": 1000,
            }
        ]
    }

    step = continuous_runtime._reconcile_runner_state_from_account_truth(  # noqa: SLF001
        state,
        account_truth,
        now=datetime.fromisoformat("2026-06-05T09:30:00+09:00"),
    )

    assert step["status"] == "pass"
    assert step["promoted_to_holdings_count"] == 0
    assert step["refreshed_holdings_count"] == 1
    assert step["refreshed_symbols"] == ["005930"]
    assert state["holdings"][0]["current_price"] == 70500
    assert state["holdings"][0]["eval_amount_krw"] == 141000
    assert state["holdings"][0]["target_price"] == 72100
    assert state["last_reconciled_kst"] == "2026-06-05T09:30:00+09:00"


def test_tick_without_intent_or_reconciliation_does_not_call_kis_account_truth(tmp_path: Path, monkeypatch):
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
    )

    assert payload["status"] == "idle_no_order_intent"
    assert payload["reconciliation_required"] is False
    assert payload["account_truth"]["source"] == "not_required_without_order_intent"
    assert payload["account_truth"]["broker_endpoint_called"] is False
    assert transport.calls == []


def test_submitted_history_only_does_not_keep_reconciliation_loop_alive(tmp_path: Path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    state_dir = data_root / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "kis-paper-runner-state.json").write_text(
        json.dumps(
            {
                "schema_version": "kis_paper_runner_state/v0",
                "pending_orders": [],
                "holdings": [{"symbol": "005930", "position_state": "holding_confirmed", "quantity": 2}],
                "active_exits": [],
                "submitted_order_history": [{"symbol": "005930", "idempotency_key": "intent-done"}],
                "consumed_intent_keys": ["intent-done"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    env = _env()
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(data_root)
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)

    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
    )

    assert payload["status"] == "idle_no_order_intent"
    assert payload["reconciliation_required"] is False
    assert transport.calls == []


def test_systemd_runner_enables_paper_experiment_orders_with_session_gate():
    service_path = Path(__file__).resolve().parents[2] / "ops" / "systemd" / "user" / "hwistock-kis-paper-runner.service"
    service_text = service_path.read_text(encoding="utf-8")
    assert "EnvironmentFile=-/home/hwi/.config/hwistock/runtime-mode.env" in service_text
    assert "source ops/systemd/load_runtime_mode_env.sh" in service_text
    assert "ensure_paper_order_approval.py --emit-env --update-runtime-env" in service_text
    assert 'HWISTOCK_OPERATION_MODE="${HWISTOCK_OPERATION_MODE:-paper_experiment}"' in service_text
    assert "--allow-paper-orders" in service_text
    assert "Environment=HWISTOCK_KIS_PAPER_ORDER_ENABLED=true" in service_text
    assert "Environment=HWISTOCK_MAX_DAILY_PAPER_ORDERS=20" in service_text
    assert "Environment=HWISTOCK_MAX_PAPER_NOTIONAL_KRW=2000000" in service_text
    assert "export HWISTOCK_INVESTMENT_MODE=paper" not in service_text


def test_systemd_ai_and_market_ticks_use_shared_runtime_mode_policy():
    root = Path(__file__).resolve().parents[2] / "ops" / "systemd" / "user"
    for filename in [
        "hwistock-intel-collector.service",
        "hwistock-kis-market-data.service",
        "hwistock-ai-analysis.service",
        "hwistock-ai-flash.service",
    ]:
        service_text = (root / filename).read_text(encoding="utf-8")
        assert "EnvironmentFile=-/home/hwi/.config/hwistock/runtime-mode.env" in service_text
        assert "source ops/systemd/load_runtime_mode_env.sh" in service_text
        assert "export HWISTOCK_INVESTMENT_MODE=paper" not in service_text


def test_systemd_units_are_lf_delimited_and_structured():
    root = Path(__file__).resolve().parents[2] / "ops" / "systemd" / "user"
    unit_paths = sorted([*root.glob("hwistock-*.service"), *root.glob("hwistock-*.timer")])
    assert unit_paths
    for path in unit_paths:
        data = path.read_bytes()
        assert b"\r" not in data, f"{path} must use LF line endings only"
        text = data.decode("utf-8")
        wrapped = "\n" + text
        assert "\n[Unit]\n" in wrapped, f"{path} must have a line-delimited [Unit] section"
        if path.suffix == ".service":
            assert "\n[Service]\n" in wrapped, f"{path} must have a line-delimited [Service] section"
            assert "\nExecStart=" in wrapped, f"{path} must have a line-delimited ExecStart directive"
        if path.suffix == ".timer":
            assert "\n[Timer]\n" in wrapped, f"{path} must have a line-delimited [Timer] section"
            assert "\n[Install]\n" in wrapped, f"{path} must have a line-delimited [Install] section"


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


def test_adapter_sanitizes_balance_positions_and_daily_fills_without_raw_payload():
    balance_response = {
        "http_status": 200,
        "payload": {
            "rt_cd": "0",
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "2.0",
                    "ord_psbl_qty": "1",
                    "pchs_avg_pric": "70000.0",
                    "prpr": "70500",
                    "evlu_amt": "141000",
                    "evlu_pfls_amt": "1000",
                }
            ],
        },
    }
    fill_response = {
        "http_status": 200,
        "payload": {
            "rt_cd": "0",
            "output1": [
                {
                    "pdno": "005930",
                    "sll_buy_dvsn_cd": "02",
                    "odno": "1234567890",
                    "tot_ccld_qty": "2",
                    "ord_qty": "2",
                    "rmn_qty": "0",
                    "avg_prvs": "70000",
                }
            ],
        },
    }

    positions = extractKisBalancePositionsPayload(balance_response)
    fills = extractKisDailyFillRowsPayload(fill_response)

    assert positions == [
        {
            "symbol": "005930",
            "ticker": "005930",
            "name": "삼성전자",
            "quantity": 2,
            "sellable_quantity": 1,
            "average_price": 70000,
            "current_price": 70500,
            "eval_amount_krw": 141000,
            "pnl_krw": 1000,
            "source": "kis_balance_output1",
        }
    ]
    assert fills[0]["symbol"] == "005930"
    assert fills[0]["side"] == "buy"
    assert fills[0]["order_no"] == "1234567890"
    assert fills[0]["filled_quantity"] == 2
    assert fills[0]["remaining_quantity"] == 0
    rendered = json.dumps({"positions": positions, "fills": fills}, ensure_ascii=False)
    assert "KIS_PAPER" not in rendered


def test_adapter_realized_pnl_skips_paper_unsupported_endpoint():
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=_env(), transport=transport)
    token_result, token = adapter.issueTokenWithValue()
    assert token_result["token_present"] is True

    result = adapter.inquireRealizedPnl(token)

    assert result["status"] == "skipped_provider_unsupported"
    assert result["step"] == "realized_pnl_inquire"
    assert result["reason"] == "kis_paper_mock_tr_unsupported_by_local_reference"
    assert result["broker_endpoint_called"] is False
    assert result["dashboard_realized_pnl_summary"]["realized_pnl_krw"] is None
    assert not any("inquire-balance-rlz-pl" in call["url"] for call in transport.calls)


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
    assert status["operationMode"] == "observe_only"
    assert status["paperExperimentReady"] is False
    assert status["paperOrderLoopEnabled"] is False
    assert status["operationalTradingReadiness"] is False
    assert status["operationalTradingReadinessBlocksPaperOperation"] is False
    assert status["liveMoneyTradingReady"]["state"] == "not_applicable"
    assert status["liveMoneyTradingReady"]["blocksPaperOperation"] is False
    assert status["productionQualityReady"]["state"] == "partial"
    assert status["productionQualityReady"]["blocksPaperOperation"] is False
    assert status["durationPolicy"]["fixedDurationDays"] is None
    assert status["paperOrderEnabled"] is False


def test_order_flag_requires_operator_approval_file(tmp_path, monkeypatch):
    env = {"HWISTOCK_OPERATION_MODE": "paper_experiment", "HWISTOCK_KIS_PAPER_ORDER_ENABLED": "true"}
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env, at_kst="2026-06-05T09:30:00")
    assert status["paperOrderRequested"] is True
    assert status["paperOrderEnabled"] is False
    assert status["paperOrderApproval"]["reason"] == "HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID_missing"

    env["HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID"] = "approved-order-run-1"
    env["HWISTOCK_ORDER_APPROVAL_FILE"] = str(tmp_path / "missing.approval.json")
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env, at_kst="2026-06-05T09:30:00")
    assert status["paperOrderEnabled"] is False
    assert status["paperOrderApproval"]["reason"] == "HWISTOCK_ORDER_APPROVAL_FILE_not_found"

    _order_approval(tmp_path, env)
    _mark_order_grade_source(env)
    env["HWISTOCK_CALENDAR_PATH"] = str(_calendar(tmp_path, monkeypatch))
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env, at_kst="2026-06-05T09:30:00")
    assert status["paperOrderEnabled"] is True
    assert status["paperOrderApproval"]["reason"] == "operator_order_approval_verified"
    assert status["paperExperimentReady"] is False
    assert "paperNetworkEnabled" in status["paperExperimentReadiness"]["blockers"]

    env["HWISTOCK_KIS_PAPER_NETWORK_ENABLED"] = "true"
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env, at_kst="2026-06-05T09:30:00")
    assert status["paperExperimentReady"] is True
    assert status["paperExperimentReadiness"]["blockers"] == []


def test_daily_paper_order_approval_rollover_updates_date_and_runtime_env(tmp_path, monkeypatch, capsys):
    env = {"HWISTOCK_OPERATION_MODE": "paper_experiment", "HWISTOCK_KIS_PAPER_ORDER_ENABLED": "true"}
    old_path = _order_approval(tmp_path, env)
    _mark_order_grade_source(env)
    env["HWISTOCK_CALENDAR_PATH"] = str(_calendar(tmp_path, monkeypatch))
    runtime_env = tmp_path / "runtime-mode.env"
    runtime_env.write_text(
        "\n".join(
            [
                "HWISTOCK_OPERATION_MODE=paper_experiment",
                "HWISTOCK_KIS_PAPER_ORDER_ENABLED=true",
                f"HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID={env['HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID']}",
                f"HWISTOCK_ORDER_APPROVAL_FILE={old_path}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("HWISTOCK_MAX_DAILY_PAPER_ORDERS", "20")
    monkeypatch.setenv("HWISTOCK_MAX_PAPER_NOTIONAL_KRW", "2000000")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ensure_paper_order_approval.py",
            "--date-kst",
            "2026-06-10",
            "--emit-env",
            "--update-runtime-env",
            str(runtime_env),
        ],
    )

    helper = _load_approval_helper_module()
    assert helper.main() == 0

    emitted = capsys.readouterr()
    daily_path = tmp_path / "paper-20260610.approval.json"
    assert daily_path.is_file()
    assert f"export HWISTOCK_ORDER_APPROVAL_FILE={daily_path}" in emitted.out
    assert f"HWISTOCK_ORDER_APPROVAL_FILE={daily_path}" in runtime_env.read_text(encoding="utf-8")
    payload = json.loads(daily_path.read_text(encoding="utf-8"))
    assert payload["valid_for_date_kst"] == "2026-06-10"
    assert payload["approved_order_run_id"] == env["HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID"]
    assert payload["live_money_scope"] == "not_applicable"

    env["HWISTOCK_ORDER_APPROVAL_FILE"] = str(daily_path)
    approval = continuous_runtime.loadPaperOrderApproval(
        env,
        requested=True,
        now=datetime.fromisoformat("2026-06-10T09:30:00+09:00"),
        operation_mode="paper_experiment",
    )
    assert approval["approved"] is True
    assert approval["reason"] == "operator_order_approval_verified"


def test_order_approval_rejects_weekday_calendar_fallback(tmp_path, monkeypatch):
    env = {"HWISTOCK_OPERATION_MODE": "paper_experiment", "HWISTOCK_KIS_PAPER_ORDER_ENABLED": "true"}
    _order_approval(tmp_path, env)
    _mark_order_grade_source(env)
    env["HWISTOCK_CALENDAR_PATH"] = str(_calendar(tmp_path, monkeypatch))
    env["HWISTOCK_ALLOW_WEEKDAY_CALENDAR_FALLBACK"] = "true"

    status = continuous.evaluateContinuousPaperRunnerStatus(env=env, at_kst="2026-06-05T09:30:00")

    assert status["paperOrderEnabled"] is False
    assert status["paperOrderApproval"]["reason"] == "weekday_calendar_fallback_forbidden_for_paper_orders"


def test_order_approval_requires_order_grade_source_and_calendar(tmp_path, monkeypatch):
    env = {"HWISTOCK_OPERATION_MODE": "paper_experiment", "HWISTOCK_KIS_PAPER_ORDER_ENABLED": "true"}
    _order_approval(tmp_path, env)

    status = continuous.evaluateContinuousPaperRunnerStatus(env=env, at_kst="2026-06-05T09:30:00")
    assert status["paperOrderEnabled"] is False
    assert status["paperOrderApproval"]["reason"] == "order_approval_market_data_source_not_order_grade"

    _mark_order_grade_source(env)
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env, at_kst="2026-06-05T09:30:00")
    assert status["paperOrderEnabled"] is False
    assert status["paperOrderApproval"]["reason"] == "HWISTOCK_CALENDAR_PATH_missing_for_order_approval"

    env["HWISTOCK_CALENDAR_PATH"] = str(_calendar(tmp_path, monkeypatch))
    status = continuous.evaluateContinuousPaperRunnerStatus(env=env, at_kst="2026-06-05T09:30:00")
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
            "broker_adapter": "kis_paper",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
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
    _mark_order_grade_source(env)
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
            "broker_adapter": "kis_paper",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    rendered = json.dumps(payload, ensure_ascii=False)
    assert payload["status"] == "ok"
    assert "paper-app-secret" not in rendered
    assert payload["account_truth"]["source"] == "kis_paper_read_steps"
    assert payload["account_truth"]["buyable_cash_krw"] == 1_720_000
    assert payload["account_truth"]["sellable_status"] == "skipped_provider_unsupported"
    assert payload["account_truth"]["sellable_quantity"] is None
    assert payload["account_truth"]["cancelable_order_status"] == "skipped_provider_unsupported"
    assert payload["account_truth"]["cancelable_order_count"] == 0
    assert payload["paper_experiment_ready"] is True
    assert payload["paper_experiment_readiness"]["blockers"] == []
    assert payload["executionPreflight"]["riskOverlay"]["risk_overlay"]["account_truth_source"] == "kis_paper_read_steps"
    assert any(step.get("step") == "ws_fill_notice" and step.get("tr_id") == "H0STCNI9" for step in payload["steps"])
    assert any(
        step.get("step") == "sellable_inquire_psbl_sell"
        and step.get("status") == "skipped_provider_unsupported"
        and step.get("broker_endpoint_called") is False
        for step in payload["steps"]
    )
    assert any(
        step.get("step") == "cancelable_order_inquire"
        and step.get("status") == "skipped_provider_unsupported"
        and step.get("broker_endpoint_called") is False
        for step in payload["steps"]
    )
    assert any(step.get("step") == "cash_order" and step.get("broker_endpoint_called") is True for step in payload["steps"])
    assert any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_blocks_order_when_paper_session_notional_cap_exceeded(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    state_dir = data_root / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "kis-paper-runner-state.json").write_text(
        json.dumps(
            {
                "schema_version": "kis_paper_runner_state/v0",
                "submitted_order_history": [
                    {
                        "idempotency_key": "already-submitted-1",
                        "symbol": "000660",
                        "submitted_at_kst": "2026-06-05T09:10:00+09:00",
                        "notional_krw": 1_950_000,
                    }
                ],
                "pending_orders": [],
                "consumed_intent_keys": ["already-submitted-1"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(data_root)
    env["HWISTOCK_MAX_PAPER_NOTIONAL_KRW"] = "2000000"
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
            "intent_id": "test-session-cap-1",
            "idempotency_key": "test-session-cap-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "order_price": 70000,
            "venue_route": "KRX",
            "broker_adapter": "kis_paper",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    cash_order = [step for step in payload["steps"] if step.get("step") == "cash_order"][-1]
    assert cash_order["status"] == "blocked_paper_session_limit"
    assert "max_paper_notional_krw_exceeded" in cash_order["errors"]
    assert not any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_preflight_uses_kis_account_truth_not_intent_cash(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
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
            "intent_id": "test-account-truth-1",
            "idempotency_key": "test-account-truth-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "venue_route": "KRX",
            "broker_adapter": "kis_paper",
            "available_cash_krw": 99_000_000,
            "planned_order_cash_krw": 1_300_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    cash_order = [step for step in payload["steps"] if step.get("step") == "cash_order"][-1]
    assert cash_order["status"] == "blocked_risk_overlay"
    assert "dynamic_exposure_cap_exceeded" in cash_order["errors"]
    assert payload["executionPreflight"]["riskOverlay"]["risk_overlay"]["available_cash_krw"] == 1_720_000
    assert not any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_blocks_sell_when_provider_sellable_quantity_is_insufficient(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(tmp_path / "data")
    transport = FakeTransport(sellable_quantity="0")
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
            "intent_id": "test-sellable-block-1",
            "idempotency_key": "test-sellable-block-1",
            "symbol": "005930",
            "side": "sell",
            "quantity": 1,
            "venue_route": "KRX",
            "broker_adapter": "kis_paper",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 0,
            "current_holdings_count": 1,
            "paper_only": True,
        },
    )

    cash_order = [step for step in payload["steps"] if step.get("step") == "cash_order"][-1]
    assert cash_order["status"] == "blocked_risk_overlay"
    assert "sellable_truth_not_accepted" in cash_order["errors"]
    assert payload["account_truth"]["sellable_status"] == "skipped_provider_unsupported"
    assert payload["account_truth"]["sellable_quantity"] is None
    assert payload["executionPreflight"]["riskOverlay"]["risk_overlay"]["sellable_quantity"] == 0
    assert not any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_blocks_saturday_even_with_future_calendar_valid_until(tmp_path, monkeypatch):
    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "validUntil": "2099-12-31T23:59:59+09:00",
                "days": {
                    "2026-06-06": {"dateKst": "2026-06-06", "isTradingDay": False}
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(path))
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = str(path)
    env["HWISTOCK_DATA_DIR"] = str(tmp_path / "data")
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-06T09:30:00",
        intent={
            "intent_id": "test-saturday-block-1",
            "idempotency_key": "test-saturday-block-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "venue_route": "KRX",
            "broker_adapter": "kis_paper",
            "available_cash_krw": 99_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    assert payload["status"] == "warn"
    assert payload["calendar_context"]["is_trading_day"] is False
    assert payload["calendar_context"]["kis_realtime_expected"] is False
    assert any(
        step.get("step") == "kis_order_submit_market_session_gate"
        and step.get("status") == "safe_skip_calendar_non_trading_day"
        for step in payload["steps"]
    )
    assert transport.calls == []


def test_tick_blocks_non_krx_or_dynamic_exposure_breach_before_order(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
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
            "intent_id": "test-risk-block-1",
            "idempotency_key": "test-risk-block-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "venue_route": "NXT",
            "broker_adapter": "kis_paper",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 1_600_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    cash_order = [step for step in payload["steps"] if step.get("step") == "cash_order"][-1]
    assert cash_order["status"] == "blocked_risk_overlay"
    assert "kis_paper_order_route_must_be_krx" in cash_order["errors"]
    assert "dynamic_exposure_cap_exceeded" in cash_order["errors"]
    order_calls = [call for call in transport.calls if "/order-cash" in call["url"]]
    assert order_calls == []


def test_tick_blocks_paper_order_outside_krx_regular_session(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
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
            "broker_adapter": "kis_paper",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    assert payload["status"] == "warn"
    assert payload["calendar_context"]["is_trading_day"] is True
    assert payload["calendar_context"]["market_context_open"] is False
    assert any(
        step.get("step") == "kis_order_submit_market_session_gate"
        and step.get("status") == "safe_skip_market_context_closed"
        for step in payload["steps"]
    )
    assert transport.calls == []


def test_preflight_requires_paper_only_and_kis_paper_adapter(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    monkeypatch.setenv("HWISTOCK_MARKET_DATA_SOURCE", "kis_market_mode_aware")
    status = base_runner.get_runner_status("2026-06-05T09:30:00")

    preflight = continuous.evaluateIntentExecutionPreflight(
        {
            "intent_id": "intent-preflight-guard-1",
            "idempotency_key": "intent-preflight-guard-1",
            "symbol": "005930",
            "side": "buy",
            "quantity": 1,
            "venue_route": "KRX",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
        },
        status=status,
    )

    assert preflight["ok"] is False
    assert "paper_only_guard_failed" in preflight["errors"]
    assert "broker_adapter_not_allowed_for_paper_order" in preflight["errors"]


def test_runner_sell_preflight_accepts_balance_position_sellable_fallback(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    monkeypatch.setenv("HWISTOCK_MARKET_DATA_SOURCE", "kis_market_mode_aware")
    status = base_runner.get_runner_status("2026-06-05T09:30:00")

    preflight = continuous.evaluateIntentExecutionPreflight(
        {
            "schema_version": "paper_order_intent/v0",
            "intent_id": "intent-sell-fallback-1",
            "idempotency_key": "intent-sell-fallback-1",
            "symbol": "005930",
            "side": "sell",
            "quantity": 2,
            "venue_route": "KRX",
            "broker_adapter": "kis_paper",
            "planned_order_cash_krw": 0,
            "paper_only": True,
        },
        order_state_snapshot={"pending_orders": [], "active_exits": [], "consumed_intent_keys": []},
        status=status,
        account_truth={
            "source": "kis_paper_read_steps",
            "balance_status": "pass",
            "sellable_status": "skipped_provider_unsupported",
            "sellable_quantity": None,
            "current_holdings_count": 5,
            "positions_count": 5,
            "positions": [
                {
                    "symbol": "005930",
                    "quantity": 7,
                    "sellable_quantity": 7,
                    "source": "kis_balance_output1",
                }
            ],
        },
    )

    assert preflight["ok"] is True
    overlay = preflight["riskOverlay"]["risk_overlay"]
    assert overlay["sellable_quantity"] == 7
    assert overlay["sellable_truth_status"] == "provider_unsupported_with_balance_fallback"
    assert overlay["sellable_truth_source"] == "kis_balance_output1"
    assert overlay["sellable_truth_accepted"] is True
    assert overlay["sellable_helper_status"] == "skipped_provider_unsupported"
    assert overlay["fallback_used"] is True
    assert "sellable_helper_unavailable_using_balance_position" in overlay["sellable_truth_warnings"]
    account_truth = preflight["accountTruth"]
    assert account_truth["raw_sellable_status"] == "skipped_provider_unsupported"
    assert account_truth["sellable_truth_status"] == "provider_unsupported_with_balance_fallback"
    assert account_truth["sellable_truth_source"] == "kis_balance_output1"
    assert account_truth["sellable_truth_accepted"] is True
    assert account_truth["sellable_fallback_used"] is True
    assert account_truth["normalized_sellable_quantity"] == 7
    assert account_truth["requested_quantity"] == 2


def test_runner_sell_preflight_accepts_balance_position_fallback_when_sellable_status_none(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    monkeypatch.setenv("HWISTOCK_MARKET_DATA_SOURCE", "kis_market_mode_aware")
    status = base_runner.get_runner_status("2026-06-05T09:30:00")

    preflight = continuous.evaluateIntentExecutionPreflight(
        {
            "schema_version": "paper_order_intent/v0",
            "intent_id": "intent-sell-none-fallback-1",
            "idempotency_key": "intent-sell-none-fallback-1",
            "symbol": "005930",
            "side": "sell",
            "quantity": 2,
            "venue_route": "KRX",
            "broker_adapter": "kis_paper",
            "planned_order_cash_krw": 0,
            "paper_only": True,
        },
        order_state_snapshot={"pending_orders": [], "active_exits": [], "consumed_intent_keys": []},
        status=status,
        account_truth={
            "source": "kis_paper_read_steps",
            "balance_status": "pass",
            "sellable_status": "none",
            "sellable_quantity": None,
            "positions": [
                {"symbol": "005930", "quantity": 7, "sellable_quantity": 7, "source": "kis_balance_output1"}
            ],
        },
    )

    assert preflight["ok"] is True
    account_truth = preflight["accountTruth"]
    assert account_truth["raw_sellable_status"] == "none"
    assert account_truth["sellable_truth_status"] == "pass_balance_position_fallback"
    assert account_truth["sellable_truth_source"] == "kis_balance_output1"
    assert account_truth["sellable_truth_accepted"] is True
    assert account_truth["sellable_fallback_used"] is True
    assert account_truth["normalized_sellable_quantity"] == 7


def test_runner_sell_preflight_rejects_zero_ttl_sell_intent(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    monkeypatch.setenv("HWISTOCK_MARKET_DATA_SOURCE", "kis_market_mode_aware")
    status = base_runner.get_runner_status("2026-06-05T09:30:00")

    preflight = continuous.evaluateIntentExecutionPreflight(
        {
            "schema_version": "paper_order_intent/v0",
            "intent_id": "intent-sell-zero-ttl-1",
            "idempotency_key": "intent-sell-zero-ttl-1",
            "symbol": "005930",
            "side": "sell",
            "quantity": 2,
            "venue_route": "KRX",
            "broker_adapter": "kis_paper",
            "created_at_kst": "2026-06-05T09:30:00+09:00",
            "valid_until_kst": "2026-06-05T09:30:00+09:00",
            "planned_order_cash_krw": 0,
            "paper_only": True,
        },
        order_state_snapshot={"pending_orders": [], "active_exits": [], "consumed_intent_keys": []},
        status=status,
        account_truth={
            "source": "kis_paper_read_steps",
            "balance_status": "pass",
            "sellable_status": "none",
            "sellable_quantity": None,
            "positions": [
                {"symbol": "005930", "quantity": 7, "sellable_quantity": 7, "source": "kis_balance_output1"}
            ],
        },
    )

    assert preflight["ok"] is False
    assert "valid_until_kst_must_be_after_created_at_kst" in preflight["errors"]
    assert "sell_intent_zero_ttl" in preflight["errors"]
    assert "sell_intent_ttl_shorter_than_runner_pickup_window" in preflight["errors"]


def test_runner_sell_preflight_blocks_active_sell_duplicate_with_balance_fallback(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    monkeypatch.setenv("HWISTOCK_MARKET_DATA_SOURCE", "kis_market_mode_aware")
    status = base_runner.get_runner_status("2026-06-05T09:30:00")

    preflight = continuous.evaluateIntentExecutionPreflight(
        {
            "schema_version": "paper_order_intent/v0",
            "intent_id": "intent-sell-active-1",
            "idempotency_key": "intent-sell-active-1",
            "symbol": "005930",
            "side": "sell",
            "quantity": 2,
            "venue_route": "KRX",
            "broker_adapter": "kis_paper",
            "planned_order_cash_krw": 0,
            "paper_only": True,
        },
        order_state_snapshot={
            "pending_orders": [],
            "active_exits": [{"symbol": "005930", "side": "sell"}],
            "consumed_intent_keys": [],
        },
        status=status,
        account_truth={
            "source": "kis_paper_read_steps",
            "balance_status": "pass",
            "sellable_status": "skipped_provider_unsupported",
            "sellable_quantity": None,
            "positions": [{"symbol": "005930", "quantity": 7, "sellable_quantity": 7, "source": "kis_balance_output1"}],
        },
    )

    assert preflight["ok"] is False
    assert "active_sell_order_exists" in preflight["errors"]


def test_tick_auto_loads_next_fifo_intent_queue_and_persists_only_passed_order(tmp_path, monkeypatch):
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
        "target_price": 72100,
        "stop_loss_price": 67900,
        "take_profit": 72100,
        "stop_loss": 67900,
        "trailing_stop_pct": 1.5,
        "venue_route": "KRX",
        "broker_adapter": "kis_paper",
        "available_cash_krw": 2_000_000,
        "planned_order_cash_krw": 100_000,
        "current_holdings_count": 0,
        "valid_until_kst": "2026-06-05T09:50:00+09:00",
        "paper_only": True,
    }
    later_intent = {
        **intent,
        "intent_id": "intent-queue-2",
        "idempotency_key": "intent-queue-2",
        "flash_trade_document_ref": "flash-queue-2",
        "symbol": "000660",
    }
    (intent_dir / "paper-order-intents-latest.jsonl").write_text(
        json.dumps(intent, ensure_ascii=False)
        + "\n"
        + json.dumps(later_intent, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
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
    assert payload["intent_source"] == "next_intent_queue_exit_priority_fifo"
    assert any(step.get("step") == "cash_order" and step.get("status") == "pass" for step in payload["steps"])
    state_path = data_root / "state" / "kis-paper-runner-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "intent-queue-1" in state["consumed_intent_keys"]
    assert "intent-queue-2" not in state["consumed_intent_keys"]
    assert state["pending_orders"][0]["symbol"] == "005930"


def test_tick_consumes_same_flash_document_intents_individually(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    intent_dir = data_root / "intents" / "2026-06-05"
    intent_dir.mkdir(parents=True)
    first_intent = {
        "schema_version": "paper_order_intent/v0",
        "intent_id": "intent-same-doc-1",
        "idempotency_key": "intent-same-doc-1",
        "flash_trade_document_ref": "flash-same-doc",
        "symbol": "005930",
        "side": "buy",
        "quantity": 1,
        "order_price": 70000,
        "target_price": 72100,
        "stop_loss_price": 67900,
        "take_profit": 72100,
        "stop_loss": 67900,
        "trailing_stop_pct": 1.5,
        "venue_route": "KRX",
        "broker_adapter": "kis_paper",
        "available_cash_krw": 2_000_000,
        "planned_order_cash_krw": 100_000,
        "current_holdings_count": 0,
        "valid_until_kst": "2026-06-05T09:50:00+09:00",
        "paper_only": True,
    }
    second_intent = {
        **first_intent,
        "intent_id": "intent-same-doc-2",
        "idempotency_key": "intent-same-doc-2",
        "symbol": "000660",
        "order_price": 120000,
        "target_price": 124000,
        "stop_loss_price": 116500,
        "take_profit": 124000,
        "stop_loss": 116500,
    }
    (intent_dir / "paper-order-intents-latest.jsonl").write_text(
        json.dumps(first_intent, ensure_ascii=False)
        + "\n"
        + json.dumps(second_intent, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(data_root)

    first_transport = FakeTransport()
    first_payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=KisPaperAdapter(env=env, transport=first_transport),
        at_kst="2026-06-05T09:30:00",
    )
    assert first_payload["executionPreflight"]["idempotency_key"] == "intent-same-doc-1"
    assert any(step.get("step") == "cash_order" and step.get("status") == "pass" for step in first_payload["steps"])

    second_transport = FakeTransport()
    second_payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=KisPaperAdapter(env=env, transport=second_transport),
        at_kst="2026-06-05T09:31:00",
    )

    assert second_payload["intent_source"] == "next_intent_queue_exit_priority_fifo"
    assert second_payload["executionPreflight"]["ok"] is True
    assert second_payload["executionPreflight"]["idempotency_key"] == "intent-same-doc-2"
    assert "trade_document_already_consumed" not in second_payload["executionPreflight"]["errors"]
    assert any(step.get("step") == "cash_order" and step.get("status") == "pass" for step in second_payload["steps"])
    assert any("/order-cash" in call["url"] for call in second_transport.calls)

    state_path = data_root / "state" / "kis-paper-runner-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "intent-same-doc-1" in state["consumed_intent_keys"]
    assert "intent-same-doc-2" in state["consumed_intent_keys"]
    assert "flash-same-doc" not in state["consumed_trade_document_ids"]
    pending_by_symbol = {row["symbol"]: row for row in state["pending_orders"]}
    assert pending_by_symbol["005930"]["target_price"] == 72100
    assert pending_by_symbol["005930"]["stop_loss_price"] == 67900
    assert pending_by_symbol["005930"]["take_profit"] == 72100
    assert pending_by_symbol["005930"]["stop_loss"] == 67900
    assert pending_by_symbol["005930"]["trailing_stop_pct"] == 1.5
    assert pending_by_symbol["000660"]["target_price"] == 124000
    assert pending_by_symbol["000660"]["stop_loss_price"] == 116500
    duplicate_preflight = continuous.evaluateIntentExecutionPreflight(
        second_intent,
        order_state_snapshot={
            "pending_orders": [],
            "active_exits": [],
            "consumed_intent_keys": state["consumed_intent_keys"],
            "consumed_trade_document_ids": state["consumed_trade_document_ids"],
        },
        status=base_runner.get_runner_status("2026-06-05T09:32:00"),
    )
    assert "intent_idempotency_key_already_consumed" in duplicate_preflight["errors"]


def test_runner_consumes_flash_buy_intent_and_reaches_cash_order_step_with_fake_transport(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    doc = ao.buildFlashTradeDocument(
        pro_artifact={"artifact_id": "art_pro_hourly_20260605_0900"},
        recent_events=[{"source_event_id": "event-1"}],
        kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260605_0930"}],
        compiled_watch=[
            {
                "schema_version": "compiled_watch/v0",
                "symbol": "005930",
                "source_ids": ["event-1"],
                "entry_intent": {"entry_zone": [70000], "take_profit": 72100, "stop_loss": 67900, "position_size_pct": 10},
                "valid_until_kst": "2026-06-05T09:40:00+09:00",
            }
        ],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0930", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0930", "pending_orders": []},
        provider_actions=[
            {
                "symbol": "005930",
                "action": "BUY_NOW",
                "quantity": 1,
                "entry_price_limit": 70000,
                "target_price": 72100,
                "stop_loss_price": 67900,
                "position_size_pct": 10,
                "confidence": 0.8,
            }
        ],
        produced_at_kst="2026-06-05T09:30:00+09:00",
    )
    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=[{"symbol": "005930"}],
        portfolio_snapshot={"artifact_id": "art_portfolio_20260605_0930", "holdings": []},
        order_state_snapshot={"artifact_id": "art_order_state_20260605_0930", "pending_orders": []},
        now_kst="2026-06-05T09:30:00+09:00",
    )
    assert pipeline["accepted_count"] == 1
    intent = pipeline["accepted_intents"][0]
    assert intent["action_source"] == "deepseek_flash_provider"
    assert intent["paper_only"] is True
    assert intent["broker_adapter"] == "kis_paper"
    assert intent["venue_route"] == "KRX"

    intent_dir = data_root / "intents" / "2026-06-05"
    intent_dir.mkdir(parents=True)
    (intent_dir / "paper-order-intents-latest.jsonl").write_text(
        json.dumps(intent, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
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

    assert payload["intent_source"] == "next_intent_queue_exit_priority_fifo"
    assert any(step.get("step") == "cash_order" and step.get("status") == "pass" for step in payload["steps"])
    assert any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_prioritizes_exit_sell_intent_before_entry_fifo(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    intent_dir = data_root / "intents" / "2026-06-05"
    intent_dir.mkdir(parents=True)
    buy_intent = {
        "schema_version": "paper_order_intent/v0",
        "intent_id": "intent-buy-first",
        "idempotency_key": "intent-buy-first",
        "symbol": "005930",
        "side": "buy",
        "quantity": 1,
        "order_price": 70000,
        "venue_route": "KRX",
        "broker_adapter": "kis_paper",
        "available_cash_krw": 2_000_000,
        "planned_order_cash_krw": 100_000,
        "current_holdings_count": 0,
        "valid_until_kst": "2026-06-05T09:50:00+09:00",
        "paper_only": True,
    }
    sell_intent = {
        **buy_intent,
        "intent_id": "intent-sell-exit",
        "idempotency_key": "intent-sell-exit",
        "side": "sell",
        "intent_type": "realtime_exit",
        "symbol": "000660",
        "planned_order_cash_krw": 0,
    }
    (intent_dir / "paper-order-intents-latest.jsonl").write_text(
        json.dumps(buy_intent, ensure_ascii=False)
        + "\n"
        + json.dumps(sell_intent, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
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
    assert payload["intent_source"] == "next_intent_queue_exit_priority_fifo"
    assert payload["executionPreflight"]["idempotency_key"] == "intent-sell-exit"
    assert "sellable_truth_not_accepted" in payload["executionPreflight"]["errors"]
    assert not (data_root / "state" / "kis-paper-runner-state.json").exists()
    assert not any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_sell_exit_uses_balance_position_sellable_fallback(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    intent_dir = data_root / "intents" / "2026-06-05"
    intent_dir.mkdir(parents=True)
    sell_intent = {
        "schema_version": "paper_order_intent/v0",
        "intent_id": "intent-sell-balance-fallback",
        "idempotency_key": "intent-sell-balance-fallback",
        "side": "sell",
        "intent_type": "position_time_stop_exit",
        "symbol": "000660",
        "quantity": 3,
        "order_price": 120000,
        "venue_route": "KRX",
        "broker_adapter": "kis_paper",
        "planned_order_cash_krw": 0,
        "valid_until_kst": "2026-06-05T09:50:00+09:00",
        "paper_only": True,
    }
    (intent_dir / "paper-order-intents-latest.jsonl").write_text(
        json.dumps(sell_intent, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
    _order_approval(tmp_path, env)
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    env["HWISTOCK_DATA_DIR"] = str(data_root)
    transport = FakeTransport(
        balance_positions=[
            {
                "pdno": "000660",
                "hldg_qty": "5",
                "ord_psbl_qty": "5",
                "prpr": "120000",
                "pchs_avg_pric": "119000",
            }
        ]
    )
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
    )

    assert payload["executionPreflight"]["ok"] is True
    overlay = payload["executionPreflight"]["riskOverlay"]["risk_overlay"]
    assert overlay["sellable_truth_status"] == "provider_unsupported_with_balance_fallback"
    assert overlay["sellable_truth_source"] == "kis_balance_output1"
    assert overlay["sellable_quantity"] == 5
    assert overlay["fallback_used"] is True
    assert payload["account_truth"]["raw_sellable_status"] == "skipped_provider_unsupported"
    assert payload["account_truth"]["sellable_truth_status"] == "provider_unsupported_with_balance_fallback"
    assert payload["account_truth"]["sellable_truth_source"] == "kis_balance_output1"
    assert payload["account_truth"]["sellable_truth_accepted"] is True
    assert payload["account_truth"]["sellable_fallback_used"] is True
    assert payload["account_truth"]["normalized_sellable_quantity"] == 5
    normalization_step = [step for step in payload["steps"] if step.get("step") == "sellable_truth_normalization"][-1]
    assert normalization_step["status"] == "pass"
    assert normalization_step["sellable_truth_status"] == "provider_unsupported_with_balance_fallback"
    assert normalization_step["sellable_quantity"] == 5
    assert normalization_step["fallback_used"] is True
    assert any(step.get("step") == "cash_order" and step.get("status") == "pass" for step in payload["steps"])
    assert any("/order-cash" in call["url"] for call in transport.calls)


def test_tick_does_not_mark_intent_consumed_when_broker_warns(tmp_path, monkeypatch):
    _calendar(tmp_path, monkeypatch)
    data_root = tmp_path / "data"
    env = _env()
    env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    _mark_order_grade_source(env)
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
            "broker_adapter": "kis_paper",
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
            "broker_adapter": "kis_paper",
            "available_cash_krw": 2_000_000,
            "planned_order_cash_krw": 100_000,
            "current_holdings_count": 0,
            "paper_only": True,
        },
    )
    assert retry_payload["executionPreflight"]["ok"] is False
    assert "ambiguous_submit_requires_reconciliation" in retry_payload["executionPreflight"]["errors"]
    assert not any("/order-cash" in call["url"] for call in retry_transport.calls)


def test_runner_can_consume_sell_intent_five_minutes_after_creation(tmp_path: Path):
    doc = {
        "schema_version": "flash_trade_document/v1",
        "artifact_id": "art_flash_tdoc_20260605_0940",
        "bucket_id": "20260605T0940",
        "document_kind": "POSITION_MANAGEMENT",
        "produced_at_kst": "2026-06-05T09:40:00+09:00",
        "market_context": {"broker_order_open": True},
        "actions": [],
        "position_actions": [
            {
                "symbol": "005930",
                "ticker": "005930",
                "position_state": "holding_confirmed",
                "action": "SELL_NOW",
                "current_price": 10020,
                "quantity": 10,
                "sellable_quantity": 10,
                "sellable_status": "pass",
                "sellable_truth_status": "pass",
                "sellable_truth_accepted": True,
                "sell_allowed": True,
                "order_window_open": True,
                "time_exit_status": "hard_max_exceeded",
                "time_exit_reason": "hard_max_hold_exceeded",
                "market_data_refs": ["art_kis_snapshot_20260605_0939"],
            }
        ],
    }
    pipeline = engine.generatePaperOrderIntentsFromFlashDocument(
        doc,
        compiled_watch=[{"symbol": "005930"}],
        portfolio_snapshot={"holdings": [{"symbol": "005930", "quantity": 10, "sellable_quantity": 10}]},
        order_state_snapshot={"pending_orders": [], "active_exits": []},
        now_kst="2026-06-05T09:40:00+09:00",
    )
    intent = pipeline["accepted_intents"][0]
    queue_path = tmp_path / "intents" / "2026-06-05" / "paper-order-intents-latest.jsonl"
    queue_path.parent.mkdir(parents=True)
    queue_path.write_text(json.dumps(intent, ensure_ascii=False) + "\n", encoding="utf-8")

    loaded = continuous_runtime._load_next_intent_from_queue(
        data_root=tmp_path,
        at=datetime.fromisoformat("2026-06-05T09:45:00+09:00"),
        state={"consumed_intent_keys": [], "submitting_intent_keys": [], "ambiguous_intent_keys": []},
    )

    assert loaded["source"] == "next_intent_queue_exit_priority_fifo"
    assert loaded["intent"]["side"] == "sell"
    assert loaded["intent"]["action"] == "SELL_NOW"
    assert loaded["intent"]["valid_until_kst"] == "2026-06-05T09:52:00+09:00"
