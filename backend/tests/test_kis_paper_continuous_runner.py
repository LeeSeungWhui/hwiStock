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
    validatePaperBaseUrl,
)


class FakeTransport:
    def __init__(self):
        self.calls = []

    def request_json(self, method, url, *, headers=None, body=None, timeout=20):
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {}), "body": dict(body or {}) if body else None})
        if url.endswith("/oauth2/tokenP"):
            return {"http_status": 200, "payload": {"rt_cd": "0", "access_token": "fake-token"}}
        return {"http_status": 200, "payload": {"rt_cd": "0", "msg_cd": "ok", "output1": [{"row": 1}]}}


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    base_runner.reset_runtime_for_tests()
    for key in (
        "HWISTOCK_KIS_PAPER_NETWORK_ENABLED",
        "HWISTOCK_KIS_PAPER_ORDER_ENABLED",
        "HWISTOCK_MARKET_DATA_SOURCE",
        "HWISTOCK_CALENDAR_PATH",
        "HWISTOCK_KILL_SWITCH",
    ):
        monkeypatch.delenv(key, raising=False)
    yield
    base_runner.reset_runtime_for_tests()


def _env():
    return {
        "KIS_PAPER_APP_KEY": "paper-app-key",
        "KIS_PAPER_APP_SECRET": "paper-app-secret",
        "KIS_PAPER_ACCOUNT_NO": "12345678",
        "KIS_PAPER_ACCOUNT_PRODUCT_CODE": "01",
        "KIS_PAPER_BASE_URL": "https://openapivts.koreainvestment.com:29443",
        "HWISTOCK_KIS_PAPER_NETWORK_ENABLED": "true",
        "HWISTOCK_MARKET_DATA_SOURCE": "local_fixture",
    }


def _calendar(tmp_path: Path, monkeypatch):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps({"validUntil": "2099-12-31T23:59:59+09:00"}), encoding="utf-8")
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(path))
    return path


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
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
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
    env["HWISTOCK_CALENDAR_PATH"] = os.environ["HWISTOCK_CALENDAR_PATH"]
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
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
    transport = FakeTransport()
    adapter = KisPaperAdapter(env=env, transport=transport)
    payload = continuous.runContinuousPaperTick(
        env=env,
        adapter=adapter,
        at_kst="2026-06-05T09:30:00",
        intent={
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
