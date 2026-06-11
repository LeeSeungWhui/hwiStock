"""
Focused tests for the common MarketSessionGate/KisApiGate policy.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import market_session_gate as gate  # noqa: E402


def _write_calendar(tmp_path: Path, *, valid_until: str = "2099-12-31T23:59:59+09:00") -> Path:
    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "validUntil": valid_until,
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
                    },
                    "2026-06-06": {
                        "dateKst": "2026-06-06",
                        "isTradingDay": False,
                        "reason": "Saturday",
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _env(path: Path, **overrides: str) -> dict[str, str]:
    return {"HWISTOCK_CALENDAR_PATH": str(path), **overrides}


def _write_paper_autofill_calendar(path: Path, *, day: str = "2026-06-11") -> Path:
    path.write_text(
        json.dumps(
            {
                "validUntil": "2026-06-25T23:59:59+09:00",
                "sourceAuthority": "paper_autofill_weekday_public_holiday_crosscheck",
                "days": {
                    day: {
                        "dateKst": day,
                        "isTradingDay": True,
                        "source": "paper_autofill_weekday_public_holiday_crosscheck",
                        "confidence": "paper_experiment",
                        "warnings": ["calendar_row_autofilled_for_paper_mode"],
                        "nxtEnabled": False,
                        "krx": {
                            "regularOpen": "09:00",
                            "regularClose": "15:30",
                            "orderOpen": "09:00",
                            "orderClose": "15:00",
                        },
                        "nxt": {"open": "08:00", "close": "20:00", "enabled": False},
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def test_weekend_kis_market_data_skips_but_pro_hourly_still_allowed(tmp_path: Path):
    calendar = _write_calendar(tmp_path)
    env = _env(calendar)

    market = gate.evaluateKisCallGate(
        "2026-06-06T09:30:00+09:00",
        call_family="kis_market_data",
        env=env,
    )
    pro = gate.evaluateKisCallGate(
        "2026-06-06T09:30:00+09:00",
        call_family="pro_hourly",
        env=env,
    )

    assert market["allowed"] is False
    assert market["calendar_context"]["kis_realtime_expected"] is False
    assert market["evidence_payload"]["broker_endpoint_called"] is False
    assert pro["allowed"] is True
    assert pro["calendar_context"]["is_trading_day"] is False
    assert pro["calendar_context"]["market_session_required"] is False


def test_weekend_dashboard_account_summary_allowed_without_market_session(tmp_path: Path):
    calendar = _write_calendar(tmp_path)
    env = _env(calendar)

    summary = gate.evaluateKisCallGate(
        "2026-06-06T11:30:00+09:00",
        call_family="dashboard_account_summary",
        env=env,
    )

    assert summary["allowed"] is True
    assert summary["calendar_context"]["is_trading_day"] is False
    assert summary["calendar_context"]["market_session_required"] is False
    assert summary["calendar_context"]["account_refresh_allowed"] is True
    assert summary["evidence_payload"]["broker_endpoint_called"] is False


def test_trading_account_truth_requires_order_window_but_reconciliation_can_be_pending(tmp_path: Path):
    calendar = _write_calendar(tmp_path)
    env = _env(calendar, HWISTOCK_INVESTMENT_MODE="paper")

    account_truth = gate.evaluateKisCallGate(
        "2026-06-05T15:10:00+09:00",
        call_family="trading_account_truth",
        env=env,
    )
    reconciliation = gate.evaluateKisCallGate(
        "2026-06-05T15:10:00+09:00",
        call_family="kis_reconciliation",
        reconciliation_required=True,
        env=env,
    )

    assert account_truth["allowed"] is False
    assert account_truth["reason"] == "broker_order_window_closed"
    assert reconciliation["allowed"] is True
    assert reconciliation["reason"] == "reconciliation_work_pending"
    assert reconciliation["calendar_context"]["market_session_required"] is False


def test_paper_mode_windows_use_0900_1500_orders_and_1530_context(tmp_path: Path):
    calendar = _write_calendar(tmp_path)
    env = _env(calendar, HWISTOCK_INVESTMENT_MODE="paper")

    preopen = gate.evaluateKisCallGate("2026-06-05T08:30:00+09:00", call_family="kis_market_data", env=env)
    open_market = gate.evaluateKisCallGate("2026-06-05T09:00:00+09:00", call_family="kis_market_data", env=env)
    before_close = gate.evaluateKisCallGate("2026-06-05T14:59:00+09:00", call_family="kis_order_submit", env=env)
    at_close = gate.evaluateKisCallGate("2026-06-05T15:00:00+09:00", call_family="kis_order_submit", env=env)
    close_context = gate.evaluateKisCallGate("2026-06-05T15:10:00+09:00", call_family="kis_reconciliation", env=env)
    late_context_order = gate.evaluateKisCallGate("2026-06-05T15:10:00+09:00", call_family="kis_order_submit", env=env)

    assert preopen["allowed"] is False
    assert open_market["allowed"] is True
    assert before_close["allowed"] is True
    assert at_close["allowed"] is False
    assert at_close["reason"] == "broker_order_window_closed"
    assert close_context["allowed"] is True
    assert late_context_order["allowed"] is False
    assert late_context_order["calendar_context"]["market_context_open"] is True


def test_missing_or_stale_calendar_blocks_order_submit(tmp_path: Path):
    missing = gate.evaluateKisCallGate(
        "2026-06-05T09:30:00+09:00",
        call_family="kis_order_submit",
        env=_env(tmp_path / "missing.json"),
    )
    stale_path = _write_calendar(tmp_path, valid_until="2026-06-04T23:59:59+09:00")
    stale = gate.evaluateKisCallGate(
        "2026-06-05T09:30:00+09:00",
        call_family="kis_order_submit",
        env=_env(stale_path),
    )

    assert missing["allowed"] is False
    assert missing["reason"] == "calendar_unconfigured"
    assert stale["allowed"] is False
    assert stale["reason"] == "calendar_stale"


def test_live_mode_does_not_enable_nxt_without_approval_flags(tmp_path: Path):
    calendar = _write_calendar(tmp_path)
    default_live = gate.evaluateKisCallGate(
        "2026-06-05T18:00:00+09:00",
        call_family="kis_market_data",
        env=_env(calendar, HWISTOCK_INVESTMENT_MODE="live", HWISTOCK_EXECUTION_VENUE_MODE="krx_nxt"),
    )
    approved_live = gate.evaluateKisCallGate(
        "2026-06-05T18:00:00+09:00",
        call_family="kis_market_data",
        env=_env(
            calendar,
            HWISTOCK_INVESTMENT_MODE="live",
            HWISTOCK_EXECUTION_VENUE_MODE="krx_nxt",
            HWISTOCK_NXT_ENABLED="true",
            HWISTOCK_NXT_READY_SET_APPROVED="true",
        ),
    )

    assert default_live["routing"]["nxtEnabled"] is False
    assert default_live["calendar_context"]["nxt_enabled"] is False
    assert approved_live["routing"]["nxtEnabled"] is True
    assert approved_live["calendar_context"]["nxt_enabled"] is True


def test_market_session_gate_uses_runtime_calendar_before_repo_seed(tmp_path: Path):
    repo = _write_calendar(tmp_path, valid_until="2026-06-10T23:59:59+09:00")
    runtime = _write_paper_autofill_calendar(tmp_path / "runtime-calendar.json")
    env = _env(repo, HWISTOCK_RUNTIME_CALENDAR_PATH=str(runtime), HWISTOCK_INVESTMENT_MODE="paper")

    result = gate.evaluateKisCallGate("2026-06-11T14:50:00+09:00", call_family="kis_order_submit", env=env)

    assert result["allowed"] is True
    assert result["calendar"]["path"] == str(runtime)
    assert result["calendar_context"]["calendar_status"] == "paper_autofilled"
    assert result["calendar_context"]["broker_order_open"] is True


def test_paper_1450_with_autofilled_row_opens_market_and_order_gate(tmp_path: Path):
    runtime = _write_paper_autofill_calendar(tmp_path / "runtime-calendar.json")
    result = gate.evaluateKisCallGate(
        "2026-06-11T14:50:00+09:00",
        call_family="kis_order_submit",
        env={"HWISTOCK_RUNTIME_CALENDAR_PATH": str(runtime), "HWISTOCK_INVESTMENT_MODE": "paper"},
    )

    assert result["allowed"] is True
    assert result["calendar_context"]["market_context_open"] is True
    assert result["calendar_context"]["broker_order_open"] is True


def test_paper_1510_with_autofilled_row_blocks_order_but_allows_close_context(tmp_path: Path):
    runtime = _write_paper_autofill_calendar(tmp_path / "runtime-calendar.json")
    env = {"HWISTOCK_RUNTIME_CALENDAR_PATH": str(runtime), "HWISTOCK_INVESTMENT_MODE": "paper"}
    order = gate.evaluateKisCallGate("2026-06-11T15:10:00+09:00", call_family="kis_order_submit", env=env)
    reconciliation = gate.evaluateKisCallGate("2026-06-11T15:10:00+09:00", call_family="kis_reconciliation", env=env)

    assert order["allowed"] is False
    assert order["reason"] == "broker_order_window_closed"
    assert order["calendar_context"]["market_context_open"] is True
    assert reconciliation["allowed"] is True
