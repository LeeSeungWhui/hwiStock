"""
UNIT-002 focused tests: runner skeleton, routing, bind, systemd templates.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

baseDir = os.path.dirname(os.path.dirname(__file__))
repoRoot = os.path.dirname(baseDir)
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from service import HwiStockRunnerService as runner  # noqa: E402

KST = ZoneInfo("Asia/Seoul")
OPS_SYSTEMD = Path(repoRoot) / "ops" / "systemd"


@pytest.fixture(autouse=True)
def reset_runner_state():
    runner.reset_runtime_for_tests()
    prev_kill = os.environ.pop("HWISTOCK_KILL_SWITCH", None)
    prev_source = os.environ.pop("HWISTOCK_MARKET_DATA_SOURCE", None)
    prev_bind = os.environ.pop("HWISTOCK_BIND_HOST", None)
    yield
    runner.reset_runtime_for_tests()
    if prev_kill is not None:
        os.environ["HWISTOCK_KILL_SWITCH"] = prev_kill
    if prev_source is not None:
        os.environ["HWISTOCK_MARKET_DATA_SOURCE"] = prev_source
    if prev_bind is not None:
        os.environ["HWISTOCK_BIND_HOST"] = prev_bind


def _kst(hour: int, minute: int) -> str:
    return f"2026-06-04T{hour:02d}:{minute:02d}:00"


def test_run_py_defaults_to_local_bind():
    text = (Path(baseDir) / "run.py").read_text(encoding="utf-8")
    assert "127.0.0.1" in text
    assert 'host="0.0.0.0"' not in text
    assert "resolve_bind_host" in text


def test_run_sh_defaults_to_local_bind():
    text = (Path(baseDir) / "run.sh").read_text(encoding="utf-8")
    assert "127.0.0.1" in text
    assert "--host 0.0.0.0" not in text
    assert "resolve_bind_host" in text


def test_resolve_bind_host_rejects_public_default():
    assert runner.resolve_bind_host("0.0.0.0") == "127.0.0.1"
    assert runner.resolve_bind_host() == "127.0.0.1"


@pytest.mark.parametrize(
    "unsafe_host",
    [
        "192.168.1.10",
        "10.0.0.5",
        "172.16.0.1",
        "8.8.8.8",
        "203.0.113.9",
        "example.com",
    ],
)
def test_resolve_bind_host_coerces_unsafe_config_values(unsafe_host):
    assert runner.resolve_bind_host(unsafe_host) == "127.0.0.1"


@pytest.mark.parametrize(
    "unsafe_host",
    ["0.0.0.0", "192.168.0.1", "8.8.8.8"],
)
def test_resolve_bind_host_coerces_unsafe_env_values(unsafe_host, monkeypatch):
    monkeypatch.setenv("HWISTOCK_BIND_HOST", unsafe_host)
    assert runner.resolve_bind_host() == "127.0.0.1"


def test_resolve_bind_host_allows_localhost_literals():
    assert runner.resolve_bind_host("127.0.0.1") == "127.0.0.1"
    assert runner.resolve_bind_host("localhost") == "localhost"
    assert runner.normalize_loopback_bind_host("::1") == "::1"


@pytest.mark.parametrize(
    "at_kst,expected_venue",
    [
        (_kst(8, 30), "NXT"),
        (_kst(9, 30), "KRX"),
        (_kst(15, 30), "NXT"),
        (_kst(20, 30), "idle"),
    ],
)
def test_kst_routing_windows(at_kst, expected_venue):
    at = datetime.fromisoformat(at_kst).replace(tzinfo=KST)
    route = runner.route_venue_at_kst(at)
    assert route["venue"] == expected_venue


def test_kill_switch_blocks_no_order_intent(tmp_path, monkeypatch):
    cal = tmp_path / "calendar.json"
    cal.write_text(
        json.dumps({"validUntil": "2099-12-31T23:59:59+09:00"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(cal))
    monkeypatch.setenv("HWISTOCK_MARKET_DATA_SOURCE", "local_skeleton")
    runner.set_kill_switch(True)
    status = runner.get_runner_status(_kst(9, 30))
    assert status["killSwitch"]["active"] is True
    assert status["orderGate"] == "blocked_kill_switch"

    record = runner.record_no_order_intent({"symbol": "005930", "side": "buy", "quantity": 1}, _kst(9, 30))
    assert record["blocked"] is True
    assert record["noBrokerCall"] is True
    assert record["fakeFillCreated"] is False
    assert record["fakeBalanceCreated"] is False
    assert record["fakePnlCreated"] is False
    assert record["recorded"] is False


def test_audit_log_categories_metadata_qa005():
    meta = runner.audit_log_categories_metadata()
    assert meta["externalDelivery"] is False
    assert meta["policy"] == "AC-05_QA-005_category_separation"
    ids = set(meta["categoryIds"])
    assert ids == {
        "signal",
        "decision",
        "risk_reject",
        "dry_run_order_intent",
        "error",
        "calendar",
        "kill_switch",
        "system_lifecycle",
        "system_status",
    }
    assert len(meta["categories"]) == len(ids)
    assert all(c["distinguishable"] for c in meta["categories"])
    by_id = {c["id"]: c for c in meta["categories"]}
    assert by_id["dry_run_order_intent"]["localPathHint"] == "data/audit/dry_run_order_intent"
    assert by_id["kill_switch"]["localPathHint"] == "data/audit/kill_switch"


def test_runner_status_exposes_audit_log_categories():
    status = runner.get_runner_status(_kst(9, 30))
    audit = status["auditLog"]
    assert audit["policy"] == "AC-05_QA-005_category_separation"
    assert "dry_run_order_intent" in audit["categoryIds"]
    assert "system_status" in audit["categoryIds"]


def test_no_order_intent_uses_explicit_audit_category(tmp_path, monkeypatch):
    cal = tmp_path / "calendar.json"
    cal.write_text(
        json.dumps({"validUntil": "2099-12-31T23:59:59+09:00"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(cal))
    monkeypatch.setenv("HWISTOCK_MARKET_DATA_SOURCE", "local_skeleton")
    record = runner.record_no_order_intent({"symbol": "005930", "side": "buy", "quantity": 1}, _kst(9, 30))
    assert record["auditCategory"] == "dry_run_order_intent"
    assert record["auditCategory"] in runner.audit_log_categories_metadata()["categoryIds"]


def test_no_order_intent_dry_run_metadata(tmp_path, monkeypatch):
    cal = tmp_path / "calendar.json"
    cal.write_text(
        json.dumps({"validUntil": "2099-12-31T23:59:59+09:00"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(cal))
    monkeypatch.setenv("HWISTOCK_MARKET_DATA_SOURCE", "local_skeleton")
    record = runner.record_no_order_intent({"symbol": "005930", "side": "buy", "quantity": 1}, _kst(9, 30))
    assert record["dryRun"] is True
    assert record["noBrokerCall"] is True
    assert record["fakeFillCreated"] is False
    assert record["fakeBalanceCreated"] is False
    assert record["fakePnlCreated"] is False
    assert record["recorded"] is True
    assert record["auditCategory"] == "dry_run_order_intent"


def test_missing_calendar_idle(tmp_path, monkeypatch):
    missing = tmp_path / "missing-calendar.json"
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(missing))
    cal = runner.evaluate_calendar_state()
    assert cal["state"] == "calendar_unconfigured"
    assert cal["tradingAllowed"] is False

    status = runner.get_runner_status(_kst(9, 30))
    assert status["orderGate"] == "blocked_calendar_unconfigured"


def test_stale_calendar_idle(tmp_path, monkeypatch):
    stale = tmp_path / "stale-calendar.json"
    stale.write_text(
        json.dumps({"validUntil": "2020-01-01T00:00:00+09:00"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(stale))
    cal = runner.evaluate_calendar_state()
    assert cal["state"] == "calendar_stale"
    status = runner.get_runner_status(_kst(9, 30))
    assert status["orderGate"] == "blocked_calendar_stale"


def test_source_unconfigured_idle(tmp_path, monkeypatch):
    cal = tmp_path / "calendar.json"
    cal.write_text(
        json.dumps({"validUntil": "2099-12-31T23:59:59+09:00"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HWISTOCK_CALENDAR_PATH", str(cal))
    status = runner.get_runner_status(_kst(9, 30))
    assert status["marketData"]["state"] == "source_unconfigured"
    assert status["orderGate"] == "blocked_source_unconfigured"


def test_alert_metadata_local_only():
    alerts = runner.alert_channels_metadata()
    assert alerts["externalDelivery"] is False
    paths = [c.get("path", "") for c in alerts["channels"]]
    assert any("data/alerts/" in p for p in paths)


def test_daily_close_template_shape():
    template = runner.daily_close_template()
    assert template["reportName"] == "daily-close-2000.md"
    assert template["externalDelivery"] is False
    assert "runtime_duration" in template["sections"]


def test_paper_observation_template_is_operator_selected():
    gate = runner.paper_observation_template()
    assert gate["durationPolicy"] == "operator_selected"
    assert gate["fixedDurationDays"] is None
    assert gate["autoStopOnDuration"] is False
    assert gate["profitThresholdRequired"] is False
    assert "operator-selected observation-window metadata present" in gate["passCriteria"]


def test_runner_status_paper_defaults():
    status = runner.get_runner_status(_kst(9, 30))
    assert status["mode"] == "paper_sandbox"
    assert status["liveOrdersEnabled"] is False
    assert status["brokerCallsEnabled"] is False
    assert status["readiness"]["liveRunnerReady"] is False


def test_systemd_api_service_template():
    path = OPS_SYSTEMD / "hwistock-api.service"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "/data/workspace/My/hwiStock" in text
    assert "EnvironmentFile=/home/hwi/.config/hwistock/hwistock.env" in text
    assert "127.0.0.1" in text


def test_systemd_runner_service_template():
    path = OPS_SYSTEMD / "hwistock-runner.service"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "/data/workspace/My/hwiStock" in text
    assert "EnvironmentFile=/home/hwi/.config/hwistock/hwistock.env" in text
    assert "time.sleep" not in text
    assert "HwiStockRunnerService.py" in text
    assert "--once" in text


def test_runner_once_entrypoint_exits_zero_with_local_status():
    script = Path(baseDir) / "service" / "HwiStockRunnerService.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--once"],
        cwd=baseDir,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["event"] == "runner_once"
    assert payload["status"]["brokerCallsEnabled"] is False
    assert payload["status"]["liveOrdersEnabled"] is False
    assert payload["auditLog"]["externalDelivery"] is False
