"""
Continuous KIS paper/mock runtime implementation for HWISTOCK-UNIT-010.

The service is duration-agnostic. It writes observation-window metadata and can
run bounded KIS paper actions only when explicitly enabled. No live domain, fake
broker state, AI provider call, or public exposure is performed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    from lib import market_session_gate as msg
    from lib import runtime_policy as rp
    from lib.kis_paper_token_cache import (
        invalidateKisPaperAccessToken,
        loadKisPaperAccessToken,
        tokenCacheRevokeSkippedStep,
    )
    from lib import paper_trading_ledger as ledger
    from service import HwiStockRunnerService as base_runner
    from service.kis_paper_adapter import (
        KisPaperAdapter,
        NetworkDisabledTransport,
        UrllibJsonTransport,
        describeKisPaperEnv,
        loadKisPaperCapabilityFlags,
    )
except ImportError:  # pragma: no cover
    from backend.lib import market_session_gate as msg
    from backend.lib import runtime_policy as rp
    from backend.lib.kis_paper_token_cache import (
        invalidateKisPaperAccessToken,
        loadKisPaperAccessToken,
        tokenCacheRevokeSkippedStep,
    )
    from backend.lib import paper_trading_ledger as ledger
    from backend.service import HwiStockRunnerService as base_runner
    from backend.service.kis_paper_adapter import (
        KisPaperAdapter,
        NetworkDisabledTransport,
        UrllibJsonTransport,
        describeKisPaperEnv,
        loadKisPaperCapabilityFlags,
    )

KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
_CONSUMED_INTENT_KEYS: set[str] = set()
PAPER_ORDER_BROKER_ADAPTERS = frozenset({"kis_paper"})
ORDER_GRADE_MARKET_DATA_SOURCES = frozenset(
    {"kis_paper_read", "kis_market_six_input", "kis_market_mode_aware"}
)
OPERATION_MODES = frozenset({"observe_only", "paper_experiment", "live_production"})
DEFAULT_MAX_DAILY_PAPER_ORDERS = 20
DEFAULT_MAX_PAPER_NOTIONAL_KRW = 2_000_000
PAPER_INTENT_RUNNER_INTERVAL_SECONDS = 300
PAPER_INTENT_RUNNER_PICKUP_GRACE_SECONDS = 60
DEFAULT_RUNNER_MAX_INTENTS_PER_TICK = 5
RUNNER_SNOOZE_RETRY_SECONDS = 180
SELLABLE_TRUTH_PASS_STATUSES = frozenset({"pass", "ok", "available", "confirmed"})
SELLABLE_TRUTH_PROVIDER_UNSUPPORTED_STATUSES = frozenset(
    {"", "none", "unknown", "skipped_provider_unsupported", "provider_unsupported", "paper_mock_unsupported"}
)
SELLABLE_TRUTH_ACCEPTED_STATUSES = frozenset(
    {
        "pass",
        "pass_balance_position_fallback",
        "pass_daily_fill_fallback",
        "provider_unsupported_with_balance_fallback",
    }
)


def _now_kst() -> datetime:
    return datetime.now(KST).replace(microsecond=0)


def _bool_env(env: Mapping[str, str], key: str, default: bool = False) -> bool:
    raw = str(env.get(key, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _float_env(env: Mapping[str, str], key: str, default: float) -> float:
    raw = str(env.get(key, "")).strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int_env(env: Mapping[str, str], key: str, default: int) -> int:
    raw = str(env.get(key, "")).strip().replace(",", "")
    if not raw:
        return default
    try:
        parsed = int(float(raw))
    except ValueError:
        return default
    return parsed if parsed >= 0 else default


def normalizeOperationMode(value: Any) -> str:
    mode = str(value or "").strip().lower()
    if mode in OPERATION_MODES:
        return mode
    return "observe_only"


def loadContinuousPaperRunnerConfig(
    env: Optional[Mapping[str, str]] = None,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    runtime_policy = rp.runtimePolicyFromEnv(source)
    operation_mode = normalizeOperationMode(source.get("HWISTOCK_OPERATION_MODE"))
    paper_order_requested = _bool_env(source, "HWISTOCK_KIS_PAPER_ORDER_ENABLED", False)
    paper_order_approval = loadPaperOrderApproval(
        source,
        requested=paper_order_requested,
        now=now,
        operation_mode=operation_mode,
    )
    paper_order_loop_enabled = (
        operation_mode == "paper_experiment"
        and paper_order_requested
        and paper_order_approval["approved"]
    )
    return {
        "runner_id": "hwistock-kis-paper-continuous-runner",
        "schema_version": "kis_paper_continuous_runner_config/v0",
        "operation_mode": operation_mode,
        "investment_mode": runtime_policy["investment_mode"],
        "market_analysis_feed_mode": runtime_policy["market_analysis_feed_mode"],
        "execution_venue_mode": runtime_policy["execution_venue_mode"],
        "nxt_enabled": runtime_policy["nxt_enabled"],
        "duration_policy": "operator_selected",
        "fixed_duration_days": None,
        "auto_stop_on_duration": False,
        "auto_pass_on_duration": False,
        "auto_fail_on_duration": False,
        "paper_network_enabled": _bool_env(source, "HWISTOCK_KIS_PAPER_NETWORK_ENABLED", False),
        "paper_order_requested": paper_order_requested,
        "paper_order_enabled": paper_order_loop_enabled,
        "paper_order_loop_enabled": paper_order_loop_enabled,
        "paper_order_approval": paper_order_approval,
        "max_daily_paper_orders": int(paper_order_approval.get("maxDailyOrders") or DEFAULT_MAX_DAILY_PAPER_ORDERS),
        "max_paper_notional_krw": int(paper_order_approval.get("maxNotionalKrw") or DEFAULT_MAX_PAPER_NOTIONAL_KRW),
        "intent_file": str(source.get("HWISTOCK_KIS_PAPER_INTENT_FILE", "")).strip(),
        "data_root": str(source.get("HWISTOCK_DATA_DIR", str(DEFAULT_DATA_ROOT))).strip(),
        "state_file": str(source.get("HWISTOCK_KIS_PAPER_STATE_FILE", "")).strip(),
        "max_intents_per_tick": max(1, _int_env(source, "HWISTOCK_RUNNER_MAX_INTENTS_PER_TICK", DEFAULT_RUNNER_MAX_INTENTS_PER_TICK)),
        "min_call_gap_sec": _float_env(source, "HWISTOCK_KIS_MIN_CALL_GAP_SEC", 1.35),
        "paper_env": describeKisPaperEnv(source),
        "capabilities": loadKisPaperCapabilityFlags(),
    }


def loadPaperOrderApproval(
    env: Optional[Mapping[str, str]] = None,
    *,
    requested: Optional[bool] = None,
    now: Optional[datetime] = None,
    operation_mode: Optional[str] = None,
) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    effective_now = now or _now_kst()
    mode = normalizeOperationMode(operation_mode or source.get("HWISTOCK_OPERATION_MODE"))
    request_flag = _bool_env(source, "HWISTOCK_KIS_PAPER_ORDER_ENABLED", False) if requested is None else bool(requested)
    run_id = str(source.get("HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID") or "").strip()
    approval_file = str(source.get("HWISTOCK_ORDER_APPROVAL_FILE") or "").strip()
    calendar_path = str(source.get("HWISTOCK_CALENDAR_PATH") or "").strip()
    market_data_source = str(source.get("HWISTOCK_MARKET_DATA_SOURCE") or "").strip()
    weekday_calendar_fallback = _bool_env(source, "HWISTOCK_ALLOW_WEEKDAY_CALENDAR_FALLBACK", False)
    result = {
        "requested": request_flag,
        "approved": False,
        "mode": mode,
        "approvalMode": None,
        "runIdPresent": bool(run_id),
        "approvalFilePresent": False,
        "approvalFilePathConfigured": bool(approval_file),
        "calendarPathConfigured": bool(calendar_path),
        "calendarFilePresent": bool(calendar_path and Path(calendar_path).is_file()),
        "marketDataSource": market_data_source or None,
        "weekdayCalendarFallbackAllowed": weekday_calendar_fallback,
        "validForDateKst": None,
        "validUntilKst": None,
        "maxDailyOrders": _int_env(source, "HWISTOCK_MAX_DAILY_PAPER_ORDERS", DEFAULT_MAX_DAILY_PAPER_ORDERS),
        "maxNotionalKrw": _int_env(source, "HWISTOCK_MAX_PAPER_NOTIONAL_KRW", DEFAULT_MAX_PAPER_NOTIONAL_KRW),
        "liveMoneyScope": "not_applicable",
        "reason": "paper_order_not_requested" if not request_flag else "order_approval_missing",
    }
    if not request_flag:
        return result
    if mode != "paper_experiment":
        result["reason"] = "operation_mode_not_paper_experiment"
        return result
    if not run_id:
        result["reason"] = "HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID_missing"
        return result
    if not approval_file:
        result["reason"] = "HWISTOCK_ORDER_APPROVAL_FILE_missing"
        return result
    path = Path(approval_file)
    result["approvalFilePresent"] = path.is_file()
    if not path.is_file():
        result["reason"] = "HWISTOCK_ORDER_APPROVAL_FILE_not_found"
        return result
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        result["reason"] = "order_approval_file_invalid_json"
        return result
    payload = dict(parsed) if isinstance(parsed, Mapping) else {}
    approved_run_id = str(payload.get("approved_order_run_id") or payload.get("run_id") or "").strip()
    if approved_run_id != run_id:
        result["reason"] = "order_approval_run_id_mismatch"
        return result
    approval_mode = normalizeOperationMode(payload.get("mode") or payload.get("operation_mode"))
    result["approvalMode"] = approval_mode
    if approval_mode != "paper_experiment":
        result["reason"] = "order_approval_mode_not_paper_experiment"
        return result
    if payload.get("allow_paper_orders") is not True:
        result["reason"] = "order_approval_allow_paper_orders_not_true"
        return result
    live_money_scope = str(payload.get("live_money_scope") or "not_applicable").strip().lower()
    result["liveMoneyScope"] = live_money_scope
    if live_money_scope != "not_applicable":
        result["reason"] = "order_approval_live_money_scope_must_be_not_applicable"
        return result
    valid_for_date = str(payload.get("valid_for_date_kst") or "").strip()
    if valid_for_date:
        result["validForDateKst"] = valid_for_date
        if valid_for_date != effective_now.astimezone(KST).date().isoformat():
            result["reason"] = "order_approval_valid_for_date_mismatch"
            return result
    valid_until = _parse_optional_kst_timestamp(payload.get("valid_until_kst") or payload.get("valid_until"))
    result["validUntilKst"] = valid_until.isoformat() if valid_until else None
    if valid_until and valid_until <= effective_now:
        result["reason"] = "order_approval_expired"
        return result
    if "max_daily_orders" in payload:
        result["maxDailyOrders"] = _coerce_nonnegative_int(payload.get("max_daily_orders"), result["maxDailyOrders"])
    if "max_notional_krw" in payload:
        result["maxNotionalKrw"] = _coerce_nonnegative_int(payload.get("max_notional_krw"), result["maxNotionalKrw"])
    if weekday_calendar_fallback:
        result["reason"] = "weekday_calendar_fallback_forbidden_for_paper_orders"
        return result
    if market_data_source not in ORDER_GRADE_MARKET_DATA_SOURCES:
        result["reason"] = "order_approval_market_data_source_not_order_grade"
        return result
    if not calendar_path:
        result["reason"] = "HWISTOCK_CALENDAR_PATH_missing_for_order_approval"
        return result
    if not Path(calendar_path).is_file():
        result["reason"] = "HWISTOCK_CALENDAR_PATH_not_found_for_order_approval"
        return result
    result["approved"] = True
    result["reason"] = "operator_order_approval_verified"
    return result


def _coerce_nonnegative_int(value: Any, default: int) -> int:
    try:
        parsed = int(float(str(value).strip().replace(",", "")))
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _symbol_matches(row: Mapping[str, Any], symbol: str) -> bool:
    expected = str(symbol or "").strip()
    if not expected:
        return False
    actual = str(row.get("symbol") or row.get("ticker") or row.get("pdno") or row.get("PDNO") or "").strip()
    return actual == expected


def _row_positive_quantity(row: Mapping[str, Any], keys: Sequence[str]) -> int:
    for key in keys:
        parsed = _coerce_nonnegative_int(row.get(key), 0)
        if parsed > 0:
            return parsed
    return 0


def normalizeSellableTruth(
    intent: Optional[Mapping[str, Any]],
    account_truth: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    payload = dict(intent or {})
    account = dict(account_truth or {})
    symbol = str(payload.get("symbol") or payload.get("ticker") or "").strip()
    requested_quantity = _coerce_nonnegative_int(payload.get("quantity"), 0)
    helper_status = str(account.get("sellable_status") or "").strip().lower()
    helper_quantity = _coerce_nonnegative_int(account.get("sellable_quantity"), 0)
    if helper_status in SELLABLE_TRUTH_PASS_STATUSES and helper_quantity > 0:
        return {
            "sellable_truth_status": "pass",
            "sellable_truth_source": "sellable_helper",
            "sellable_truth_accepted": requested_quantity <= 0 or helper_quantity >= requested_quantity,
            "sellable_quantity": helper_quantity,
            "sellable_helper_status": helper_status,
            "fallback_used": False,
            "sellable_truth_warnings": [],
        }

    for row in account.get("positions") or []:
        if not isinstance(row, Mapping) or not _symbol_matches(row, symbol):
            continue
        quantity = _row_positive_quantity(row, ("sellable_quantity", "ord_psbl_qty", "sll_psbl_qty", "quantity", "hldg_qty"))
        if quantity <= 0:
            continue
        source = str(row.get("source") or "kis_balance_position")
        status = (
            "provider_unsupported_with_balance_fallback"
            if helper_status in {"skipped_provider_unsupported", "provider_unsupported", "paper_mock_unsupported"}
            else "pass_balance_position_fallback"
        )
        return {
            "sellable_truth_status": status,
            "sellable_truth_source": source,
            "sellable_truth_accepted": requested_quantity <= 0 or quantity >= requested_quantity,
            "sellable_quantity": quantity,
            "sellable_helper_status": helper_status or None,
            "fallback_used": True,
            "sellable_truth_warnings": ["sellable_helper_unavailable_using_balance_position"],
        }

    for row in account.get("daily_order_fills") or []:
        if not isinstance(row, Mapping) or not _symbol_matches(row, symbol):
            continue
        if str(row.get("side") or "").strip().lower() not in {"", "buy"}:
            continue
        quantity = _row_positive_quantity(row, ("filled_quantity", "quantity", "order_quantity"))
        if quantity <= 0:
            continue
        return {
            "sellable_truth_status": "pass_daily_fill_fallback",
            "sellable_truth_source": str(row.get("source") or "kis_daily_ccld_output1"),
            "sellable_truth_accepted": requested_quantity <= 0 or quantity >= requested_quantity,
            "sellable_quantity": quantity,
            "sellable_helper_status": helper_status or None,
            "fallback_used": True,
            "sellable_truth_warnings": ["sellable_helper_unavailable_using_daily_fill"],
        }

    if helper_status in SELLABLE_TRUTH_PROVIDER_UNSUPPORTED_STATUSES:
        status = "provider_unsupported_no_fallback" if helper_status else "unknown"
    else:
        status = "blocked"
    return {
        "sellable_truth_status": status,
        "sellable_truth_source": "none",
        "sellable_truth_accepted": False,
        "sellable_quantity": helper_quantity,
        "sellable_helper_status": helper_status or None,
        "fallback_used": False,
        "sellable_truth_warnings": [],
    }


def enrichAccountTruthWithSellableTruth(
    account_truth: Optional[Mapping[str, Any]],
    intent: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    account = dict(account_truth or {})
    payload = dict(intent or {})
    if str(payload.get("side") or "buy").strip().lower() != "sell":
        return account
    truth = normalizeSellableTruth(payload, account)
    raw_status = account.get("raw_sellable_status", account.get("sellable_status"))
    raw_quantity = account.get("raw_sellable_quantity", account.get("sellable_quantity"))
    account.update(
        {
            "raw_sellable_status": raw_status,
            "raw_sellable_quantity": raw_quantity,
            "sellable_truth_status": truth.get("sellable_truth_status"),
            "sellable_truth_source": truth.get("sellable_truth_source"),
            "sellable_truth_accepted": truth.get("sellable_truth_accepted"),
            "sellable_truth_warnings": list(truth.get("sellable_truth_warnings") or []),
            "sellable_fallback_used": bool(truth.get("fallback_used")),
            "normalized_sellable_quantity": int(truth.get("sellable_quantity") or 0),
            "requested_quantity": _coerce_nonnegative_int(payload.get("quantity"), 0),
        }
    )
    return account


def _sellable_truth_normalization_step(intent: Mapping[str, Any], account_truth: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "step": "sellable_truth_normalization",
        "status": "pass" if account_truth.get("sellable_truth_accepted") is True else "blocked",
        "symbol": str(intent.get("symbol") or intent.get("ticker") or "").strip(),
        "side": str(intent.get("side") or "").strip().lower(),
        "raw_sellable_status": account_truth.get("raw_sellable_status"),
        "raw_sellable_quantity": account_truth.get("raw_sellable_quantity"),
        "sellable_status": account_truth.get("sellable_status"),
        "sellable_quantity": account_truth.get("normalized_sellable_quantity"),
        "requested_quantity": account_truth.get("requested_quantity"),
        "sellable_truth_status": account_truth.get("sellable_truth_status"),
        "sellable_truth_source": account_truth.get("sellable_truth_source"),
        "sellable_truth_accepted": account_truth.get("sellable_truth_accepted"),
        "sellable_truth_warnings": list(account_truth.get("sellable_truth_warnings") or []),
        "fallback_used": bool(account_truth.get("sellable_fallback_used")),
        "broker_endpoint_called": False,
        "raw_response_stored": False,
        "credential_values_printed": False,
    }


def evaluatePaperRiskOverlay(
    intent: Optional[Mapping[str, Any]],
    *,
    status: Optional[Mapping[str, Any]] = None,
    account_truth: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    payload = dict(intent or {})
    runner_status = dict(status or base_runner.get_runner_status())
    account = dict(account_truth or {})
    errors = []
    route = str(payload.get("venue_route") or payload.get("venue") or runner_status.get("routing", {}).get("venue") or "").upper()
    session_venue = str(runner_status.get("routing", {}).get("venue") or "").upper()
    side = str(payload.get("side") or "buy").lower()
    account_source = "intent_payload"
    account_truth_present = bool(account)
    if account_truth_present:
        account_source = str(account.get("source") or "kis_read_account_truth")
        available_cash = int(account.get("available_cash_krw") or account.get("buyable_cash_krw") or account.get("cash_balance_krw") or 0)
        current_holdings = int(account.get("current_holdings_count") or account.get("positions_count") or 0)
        current_position_value = int(account.get("current_position_value_krw") or account.get("stock_eval_krw") or 0)
        effective_total_deposit = int(
            account.get("effective_total_deposit_krw")
            or account.get("total_eval_krw")
            or (available_cash + current_position_value)
            or 0
        )
    else:
        available_cash = int(payload.get("available_cash_krw") or 0)
        current_holdings = int(payload.get("current_holdings_count") or 0)
        current_position_value = int(payload.get("current_position_value_krw") or payload.get("stock_eval_krw") or 0)
        effective_total_deposit = int(payload.get("effective_total_deposit_krw") or payload.get("total_deposit_krw") or 0)
    planned_cash = int(payload.get("planned_order_cash_krw") or 0)
    pending_buy_notional = int(payload.get("pending_buy_notional_krw") or 0)
    exposure = rp.evaluateDynamicExposureCap(
        current_position_value_krw=current_position_value,
        pending_buy_notional_krw=pending_buy_notional,
        new_order_notional_krw=planned_cash,
        effective_total_deposit_krw=effective_total_deposit,
        risk_overlay_capital_krw=base_runner.LIVE_CAPITAL_BASELINE_KRW,
    )

    if runner_status.get("killSwitch", {}).get("active"):
        errors.append("kill_switch_active")
    if runner_status.get("calendar", {}).get("tradingAllowed") is not True:
        errors.append("calendar_not_ready")
    if runner_status.get("calendar", {}).get("krxOrderSessionOpen") is not True:
        errors.append("krx_order_session_not_open")
    if runner_status.get("routing", {}).get("venue") == "idle":
        errors.append("off_session")
    if session_venue != "KRX":
        errors.append("kis_paper_order_requires_krx_regular_session")
    if route != "KRX":
        errors.append("kis_paper_order_route_must_be_krx")
    if not account_truth_present:
        errors.append("account_truth_required_for_order")
    if account_truth_present and account.get("balance_status") != "pass":
        errors.append("balance_truth_not_pass")
    if side == "buy" and account_truth_present and account.get("buyable_status") != "pass":
        errors.append("buyable_cash_truth_not_pass")
    sellable_truth = normalizeSellableTruth(payload, account) if side == "sell" and account_truth_present else {
        "sellable_truth_status": None,
        "sellable_truth_source": None,
        "sellable_truth_accepted": False,
        "sellable_quantity": 0,
        "sellable_helper_status": None,
        "fallback_used": False,
        "sellable_truth_warnings": [],
    }
    if side == "sell" and account_truth_present:
        sellable_quantity = int(sellable_truth.get("sellable_quantity") or 0)
        requested_quantity = int(payload.get("quantity") or 0)
        if requested_quantity <= 0:
            errors.append("sell_quantity_must_be_positive")
        elif not (
            sellable_truth.get("sellable_truth_accepted") is True
            or str(sellable_truth.get("sellable_truth_status") or "") in SELLABLE_TRUTH_ACCEPTED_STATUSES
        ):
            errors.append("sellable_truth_not_accepted")
        elif sellable_quantity < requested_quantity:
            errors.append("sellable_quantity_insufficient")
    if side == "buy" and current_holdings >= 5:
        errors.append("max_simultaneous_holdings_exceeded")
    if side == "buy" and planned_cash <= 0:
        errors.append("planned_order_cash_must_be_positive")
    if side == "buy" and available_cash <= 0:
        errors.append("available_cash_required")
    if side == "buy" and exposure["missing_account_truth"]:
        errors.append("effective_total_deposit_truth_required")
    if side == "buy" and not exposure["ok"]:
        errors.append("dynamic_exposure_cap_exceeded")

    return {
        "ok": not errors,
        "errors": errors,
        "risk_overlay": {
            "capital_mode": "cash_only",
            "live_capital_baseline_krw": base_runner.LIVE_CAPITAL_BASELINE_KRW,
            "max_cash_deployment_ratio": rp.MAX_CASH_DEPLOYMENT_RATIO,
            "dynamic_exposure_cap": exposure,
            "max_simultaneous_holdings": 5,
            "route": route,
            "session_venue": session_venue,
            "order_side": side,
            "account_truth_source": account_source,
            "account_truth_present": account_truth_present,
            "available_cash_krw": available_cash,
            "planned_order_cash_krw": planned_cash,
            "current_position_value_krw": current_position_value,
            "pending_buy_notional_krw": pending_buy_notional,
            "effective_total_deposit_krw": effective_total_deposit,
            "current_holdings_count": current_holdings,
            "sellable_quantity": int(sellable_truth.get("sellable_quantity") or 0) if account_truth_present else 0,
            "sellable_truth_status": sellable_truth.get("sellable_truth_status"),
            "sellable_truth_source": sellable_truth.get("sellable_truth_source"),
            "sellable_truth_accepted": sellable_truth.get("sellable_truth_accepted"),
            "sellable_truth_warnings": list(sellable_truth.get("sellable_truth_warnings") or []),
            "sellable_helper_status": sellable_truth.get("sellable_helper_status"),
            "fallback_used": bool(sellable_truth.get("fallback_used")),
        },
    }


def estimateIntentNotionalKrw(intent: Mapping[str, Any]) -> int:
    planned_cash = _int_or_none(intent.get("planned_order_cash_krw")) or 0
    quantity = _int_or_none(intent.get("quantity")) or 0
    order_price = _int_or_none(intent.get("order_price") or intent.get("price")) or 0
    computed = quantity * order_price if quantity > 0 and order_price > 0 else 0
    return max(planned_cash, computed)


def evaluatePaperSessionLimits(
    intent: Mapping[str, Any],
    state: Mapping[str, Any],
    approval: Mapping[str, Any],
    *,
    now: datetime,
) -> Dict[str, Any]:
    max_daily_orders = int(approval.get("maxDailyOrders") or DEFAULT_MAX_DAILY_PAPER_ORDERS)
    max_notional = int(approval.get("maxNotionalKrw") or DEFAULT_MAX_PAPER_NOTIONAL_KRW)
    today = now.astimezone(KST).date().isoformat()
    history_rows = [
        dict(row)
        for row in (state.get("submitted_order_history") or [])
        if isinstance(row, Mapping)
    ]
    pending_rows = [
        dict(row)
        for row in (state.get("pending_orders") or [])
        if isinstance(row, Mapping)
    ]
    submitted_today = [
        row for row in [*history_rows, *pending_rows]
        if str(row.get("submitted_at_kst") or row.get("recorded_at_kst") or "").startswith(today)
    ]
    side = _intent_side(intent)
    limits_apply = side == "buy"
    submitted_buy_today = [row for row in submitted_today if _intent_side(row) == "buy"]
    used_notional = sum(_coerce_nonnegative_int(row.get("notional_krw"), 0) for row in submitted_buy_today)
    intent_notional = estimateIntentNotionalKrw(intent)
    errors: list[str] = []
    if limits_apply and max_daily_orders > 0 and len(submitted_buy_today) >= max_daily_orders:
        errors.append("max_daily_paper_orders_exceeded")
    if limits_apply and max_notional > 0 and used_notional + intent_notional > max_notional:
        errors.append("max_paper_notional_krw_exceeded")
    return {
        "ok": not errors,
        "errors": errors,
        "dateKst": today,
        "side": side,
        "limitsApplyToSide": limits_apply,
        "submittedOrderCountToday": len(submitted_today),
        "submittedBuyOrderCountToday": len(submitted_buy_today),
        "maxDailyOrders": max_daily_orders,
        "usedNotionalKrw": used_notional,
        "notionalScope": "buy_orders_only",
        "intentNotionalKrw": intent_notional,
        "maxNotionalKrw": max_notional,
        "blocksPaperOrder": bool(errors),
    }


def resetContinuousPaperRunnerForTests() -> None:
    _CONSUMED_INTENT_KEYS.clear()


def _runner_state_requires_reconciliation(state: Mapping[str, Any]) -> bool:
    for key in ("pending_orders", "ambiguous_submits"):
        rows = state.get(key) or []
        if any(isinstance(row, Mapping) for row in rows):
            return True
    for key in ("submitting_intent_keys", "ambiguous_intent_keys", "claim_intent_keys"):
        values = state.get(key) or []
        if any(str(item or "").strip() for item in values):
            return True
    return False


def evaluateIntentExecutionPreflight(
    intent: Optional[Mapping[str, Any]],
    *,
    portfolio_snapshot: Optional[Mapping[str, Any]] = None,
    order_state_snapshot: Optional[Mapping[str, Any]] = None,
    status: Optional[Mapping[str, Any]] = None,
    account_truth: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    payload = dict(intent or {})
    portfolio = dict(portfolio_snapshot or {})
    order_state = dict(order_state_snapshot or {})
    errors: list[str] = []
    if payload.get("schema_version") not in (None, "paper_order_intent/v0"):
        errors.append("intent_schema_invalid")
    if payload.get("paper_only") is not True:
        errors.append("paper_only_guard_failed")
    broker_adapter = str(payload.get("broker_adapter") or "").strip()
    if broker_adapter not in PAPER_ORDER_BROKER_ADAPTERS:
        errors.append("broker_adapter_not_allowed_for_paper_order")
    if str(payload.get("venue_route") or payload.get("venue") or "").upper() != "KRX":
        errors.append("kis_paper_order_route_must_be_krx")
    symbol = str(payload.get("symbol") or payload.get("ticker") or "").strip()
    if not symbol:
        errors.append("symbol_required")
    held = _symbol_set_from_snapshot(portfolio, "holdings")
    pending = _symbol_set_from_snapshot(order_state, "pending_orders")
    exits = _symbol_set_from_snapshot(order_state, "active_exits")
    submitting_keys = {
        str(item or "").strip()
        for item in [
            *(order_state.get("submitting_intent_keys") or []),
            *(order_state.get("claim_intent_keys") or []),
        ]
        if str(item or "").strip()
    }
    ambiguous_keys = {
        str(item or "").strip()
        for item in (order_state.get("ambiguous_intent_keys") or [])
        if str(item or "").strip()
    }
    consumed_keys = {
        str(item or "").strip()
        for item in (order_state.get("consumed_intent_keys") or [])
        if str(item or "").strip()
    }
    if symbol and symbol in held and str(payload.get("side") or "buy").lower() == "buy":
        errors.append("already_holding_symbol")
    if symbol and symbol in pending:
        errors.append("pending_order_exists")
    side = str(payload.get("side") or "buy").lower()
    if symbol and symbol in exits:
        errors.append("active_exit_order_exists")
        if side == "sell":
            errors.append("active_sell_order_exists")
    created_at = _parse_optional_kst_timestamp(payload.get("created_at_kst") or payload.get("created_at"))
    expiry = _parse_optional_kst_timestamp(payload.get("valid_until_kst") or payload.get("valid_until"))
    reference_now = _status_reference_datetime(status)
    if created_at and expiry and expiry <= created_at:
        errors.append("valid_until_kst_must_be_after_created_at_kst")
        if side == "sell":
            errors.append("sell_intent_zero_ttl")
    if side == "sell" and created_at and expiry:
        ttl_seconds = int((expiry - created_at).total_seconds())
        min_sell_ttl = PAPER_INTENT_RUNNER_INTERVAL_SECONDS + PAPER_INTENT_RUNNER_PICKUP_GRACE_SECONDS
        if ttl_seconds < min_sell_ttl:
            errors.append("sell_intent_ttl_shorter_than_runner_pickup_window")
    if expiry and expiry <= reference_now:
        errors.append("intent_expired")
    risk_payload = dict(payload)
    if "pending_buy_notional_krw" not in risk_payload:
        risk_payload["pending_buy_notional_krw"] = sum(
            estimateIntentNotionalKrw(row)
            for row in (order_state.get("pending_orders") or [])
            if isinstance(row, Mapping) and str(row.get("side") or "buy").lower() == "buy"
        )
    normalized_account_truth = enrichAccountTruthWithSellableTruth(account_truth, risk_payload)
    risk = evaluatePaperRiskOverlay(risk_payload, status=status, account_truth=normalized_account_truth)
    errors.extend(risk.get("errors") or [])
    idempotency_key = str(payload.get("idempotency_key") or payload.get("intent_id") or "").strip()
    if not idempotency_key:
        errors.append("idempotency_key_required")
    if idempotency_key and (idempotency_key in _CONSUMED_INTENT_KEYS or idempotency_key in consumed_keys):
        errors.append("intent_idempotency_key_already_consumed")
    if idempotency_key and idempotency_key in ambiguous_keys:
        errors.append("ambiguous_submit_requires_reconciliation")
    if idempotency_key and idempotency_key in submitting_keys:
        errors.append("intent_submit_claim_in_progress")
    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "idempotency_key": idempotency_key,
        "symbol": symbol,
        "riskOverlay": risk,
        "accountTruth": normalized_account_truth,
        "broker_endpoint_called": False,
        "dashboard_account_summary_reused_for_order": False,
        "order_preflight_truth_source": "trading_account_truth",
    }


def markIntentConsumed(idempotency_key: str) -> None:
    key = str(idempotency_key or "").strip()
    if key:
        _CONSUMED_INTENT_KEYS.add(key)


def evaluateRealtimeExitDecision(
    position: Mapping[str, Any],
    quote: Mapping[str, Any],
) -> Dict[str, Any]:
    symbol = str(position.get("symbol") or position.get("ticker") or "").strip()
    price = float(quote.get("price") or quote.get("last_price") or 0)
    stop = float(position.get("stop_loss") or position.get("stop_loss_price") or 0)
    take = float(position.get("take_profit") or position.get("take_profit_price") or 0)
    high = float(position.get("highest_price") or price or 0)
    trailing_pct = float(position.get("trailing_stop_pct") or 0)
    trailing_trigger = high * (1 - trailing_pct / 100) if high and trailing_pct else 0
    reason = None
    if stop and price and price <= stop:
        reason = "stop_loss"
    elif take and price and price >= take:
        reason = "take_profit"
    elif trailing_trigger and price <= trailing_trigger:
        reason = "trailing_stop"
    return {
        "schema_version": "realtime_exit_decision/v0",
        "symbol": symbol,
        "price": price,
        "exit_required": reason is not None,
        "exit_reason": reason,
        "broker_endpoint_called": False,
        "depends_on_next_flash_tick": False,
    }


def buildPaperExperimentReadiness(
    config: Mapping[str, Any],
    status: Mapping[str, Any],
) -> Dict[str, Any]:
    approval = config.get("paper_order_approval") if isinstance(config.get("paper_order_approval"), Mapping) else {}
    calendar = status.get("calendar") if isinstance(status.get("calendar"), Mapping) else {}
    checks = {
        "paperNetworkEnabled": config.get("paper_network_enabled") is True,
        "paperOrderRequested": config.get("paper_order_requested") is True,
        "paperOrderLoopEnabled": config.get("paper_order_loop_enabled") is True,
        "sessionApproval": approval.get("approved") is True,
        "calendarConfigured": approval.get("calendarFilePresent") is True,
        "calendarReady": calendar.get("state") == "calendar_ready",
        "krxOrderSessionOpen": calendar.get("krxOrderSessionOpen") is True,
        "marketDataOrderGrade": approval.get("marketDataSource") in ORDER_GRADE_MARKET_DATA_SOURCES,
        "duplicateLockReady": True,
        "evidenceWriteReady": True,
    }
    ready = config.get("operation_mode") == "paper_experiment" and all(value is True for value in checks.values())
    return {
        "ready": ready,
        "checks": checks,
        "blockers": [key for key, value in checks.items() if value is not True],
        "operationMode": config.get("operation_mode") or "observe_only",
        "investmentMode": config.get("investment_mode") or "paper",
        "marketAnalysisFeedMode": config.get("market_analysis_feed_mode") or "integrated",
        "executionVenueMode": config.get("execution_venue_mode") or "krx_only",
        "nxtEnabled": config.get("nxt_enabled") is True,
    }


def evaluateContinuousPaperRunnerStatus(
    *,
    at_kst: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    reference_now = _parse_optional_kst_timestamp(at_kst) or _now_kst()
    config = loadContinuousPaperRunnerConfig(env, now=reference_now)
    status = base_runner.get_runner_status(at_kst)
    paper_readiness = buildPaperExperimentReadiness(config, status)
    paper_experiment_ready = paper_readiness["ready"]
    return {
        "runnerId": config["runner_id"],
        "mode": "kis_paper_mock",
        "operationMode": config["operation_mode"],
        "continuousService": True,
        "paperRunReady": paper_readiness["checks"]["paperNetworkEnabled"],
        "paperExperimentReady": paper_experiment_ready,
        "paperOrderLoopEnabled": config["paper_order_loop_enabled"],
        "operationalTradingReadiness": False,
        "operationalTradingReadinessBlocksPaperOperation": False,
        "liveMoneyTradingReady": {
            "state": "not_applicable",
            "liveApiAvailable": False,
            "blocksPaperOperation": False,
        },
        "productionQualityReady": {
            "state": "partial",
            "blocksPaperOperation": False,
        },
        "paperExperimentReadiness": {
            "ready": paper_experiment_ready,
            "checks": paper_readiness["checks"],
            "blockers": paper_readiness["blockers"],
        },
        "durationPolicy": {
            "type": config["duration_policy"],
            "fixedDurationDays": config["fixed_duration_days"],
            "autoStopOnDuration": config["auto_stop_on_duration"],
            "autoPassOnDuration": config["auto_pass_on_duration"],
            "autoFailOnDuration": config["auto_fail_on_duration"],
        },
        "paperNetworkEnabled": config["paper_network_enabled"],
        "paperOrderRequested": config["paper_order_requested"],
        "paperOrderEnabled": config["paper_order_enabled"],
        "maxDailyPaperOrders": config["max_daily_paper_orders"],
        "maxPaperNotionalKrw": config["max_paper_notional_krw"],
        "paperOrderApproval": config["paper_order_approval"],
        "paperEnv": config["paper_env"],
        "capabilities": config["capabilities"],
        "baseRunner": {
            "orderGate": status["orderGate"],
            "routing": status["routing"],
            "calendar": status["calendar"],
            "killSwitch": status["killSwitch"],
        },
    }


def _int_or_none(value: Any) -> Optional[int]:
    if value is None:
        return None
    raw = str(value).strip().replace(",", "")
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def _symbol_from_row(row: Mapping[str, Any]) -> str:
    for key in ("symbol", "ticker", "pdno", "PDNO", "stck_shrn_iscd", "mksc_shrn_iscd", "isu_cd", "code"):
        text = str(row.get(key) or "").strip()
        if text:
            return text
    return ""


def _positive_quantity_from_row(row: Mapping[str, Any]) -> int:
    for key in ("quantity", "filled_quantity", "hldg_qty", "hold_qty", "evlu_qty", "qty"):
        parsed = _int_or_none(row.get(key))
        if parsed is not None and parsed > 0:
            return parsed
    return 0


def _filled_quantity_from_row(row: Mapping[str, Any]) -> int:
    for key in ("filled_quantity", "tot_ccld_qty", "ccld_qty", "filled_qty"):
        parsed = _int_or_none(row.get(key))
        if parsed is not None and parsed > 0:
            return parsed
    return 0


def _order_number_from_row(row: Mapping[str, Any]) -> str:
    for key in ("broker_order_no", "order_no", "odno", "ODNO"):
        text = str(row.get(key) or "").strip()
        if text:
            return text
    return ""


def _remaining_quantity_from_row(row: Mapping[str, Any]) -> Optional[int]:
    for key in ("remaining_quantity", "rmn_qty", "unfilled_quantity", "unfilled_qty"):
        parsed = _int_or_none(row.get(key))
        if parsed is not None:
            return max(parsed, 0)
    return None


def _ten_minute_bucket_start(value: datetime) -> datetime:
    local = value.astimezone(KST)
    return local.replace(minute=(local.minute // 10) * 10, second=0, microsecond=0)


def _pending_submitted_at(row: Mapping[str, Any]) -> Optional[datetime]:
    return _parse_optional_kst_timestamp(
        row.get("submitted_at_kst")
        or row.get("created_at_kst")
        or row.get("recorded_at_kst")
    )


def _matching_daily_fill_for_pending(
    pending: Mapping[str, Any],
    account_truth: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    pending_order_no = _order_number_from_row(pending)
    pending_symbol = _symbol_from_row(pending)
    pending_side = str(pending.get("side") or "").strip().lower()
    for row in account_truth.get("daily_order_fills") or []:
        if not isinstance(row, Mapping):
            continue
        row_order_no = _order_number_from_row(row)
        row_symbol = _symbol_from_row(row)
        row_side = str(row.get("side") or "").strip().lower()
        if pending_order_no and row_order_no and row_order_no == pending_order_no:
            return dict(row)
        if not pending_order_no and pending_symbol and row_symbol == pending_symbol and row_side == pending_side:
            return dict(row)
    return None


def _pending_remaining_quantity(
    pending: Mapping[str, Any],
    account_truth: Mapping[str, Any],
) -> int:
    fill = _matching_daily_fill_for_pending(pending, account_truth)
    if fill:
        remaining = _remaining_quantity_from_row(fill)
        if remaining is not None:
            return remaining
        filled = _filled_quantity_from_row(fill)
        order_quantity = _coerce_nonnegative_int(fill.get("order_quantity"), 0)
        if order_quantity > 0:
            return max(order_quantity - filled, 0)
    local_remaining = _remaining_quantity_from_row(pending)
    if local_remaining is not None:
        return local_remaining
    return _positive_quantity_from_row(pending)


def _is_previous_timing_pending_order(
    pending: Mapping[str, Any],
    *,
    now: datetime,
) -> bool:
    if not _order_number_from_row(pending):
        return False
    submitted_at = _pending_submitted_at(pending)
    if submitted_at is None:
        return False
    return submitted_at < _ten_minute_bucket_start(now)


def _mark_pending_order_cancelled(
    state: Dict[str, Any],
    pending: Mapping[str, Any],
    cancel_step: Mapping[str, Any],
    *,
    now: datetime,
    reason: str,
    remaining_quantity: int,
) -> None:
    order_no = _order_number_from_row(pending)
    key = str(pending.get("idempotency_key") or "").strip()
    symbol = _symbol_from_row(pending)
    cancelled_row = {
        **dict(pending),
        "order_state": "cancelled",
        "cancel_status": cancel_step.get("status"),
        "cancelled_at_kst": now.isoformat(),
        "cancel_reason": reason,
        "remaining_quantity": remaining_quantity,
        "broker_cancel_endpoint_called": bool(cancel_step.get("broker_endpoint_called")),
        "order_cancel_modify_called": bool(cancel_step.get("order_cancel_modify_called")),
    }
    cancelled_rows = [
        dict(row)
        for row in (state.get("cancelled_orders") or [])
        if isinstance(row, Mapping)
    ]
    cancelled_rows.append(cancelled_row)
    state["cancelled_orders"] = cancelled_rows[-200:]

    history_rows: list[Dict[str, Any]] = []
    matched_history = False
    for row in state.get("submitted_order_history") or []:
        if not isinstance(row, Mapping):
            continue
        updated = dict(row)
        row_order_no = _order_number_from_row(updated)
        row_key = str(updated.get("idempotency_key") or "").strip()
        row_symbol = _symbol_from_row(updated)
        if (order_no and row_order_no == order_no) or (key and row_key == key) or (
            not order_no and not key and symbol and row_symbol == symbol
        ):
            updated.update(cancelled_row)
            matched_history = True
        history_rows.append(updated)
    if not matched_history:
        history_rows.append(cancelled_row)
    state["submitted_order_history"] = history_rows[-500:]
    state["last_updated_kst"] = now.isoformat()


def _mark_pending_order_terminal_cleanup(
    state: Dict[str, Any],
    pending: Mapping[str, Any],
    cancel_step: Mapping[str, Any],
    *,
    now: datetime,
    reason: str,
    remaining_quantity: int,
) -> None:
    order_no = _order_number_from_row(pending)
    key = str(pending.get("idempotency_key") or "").strip()
    symbol = _symbol_from_row(pending)
    terminal_row = {
        **dict(pending),
        "order_state": "broker_expired_or_not_found",
        "local_cleanup_reason": reason,
        "requires_runner_cancel": False,
        "terminal_cleanup_at_kst": now.isoformat(),
        "remaining_quantity": remaining_quantity,
        "broker_cancel_status": cancel_step.get("status"),
        "broker_cancel_msg_cd": cancel_step.get("msg_cd"),
        "broker_cancel_reason": cancel_step.get("reason"),
        "broker_cancel_endpoint_called": bool(cancel_step.get("broker_endpoint_called")),
        "order_cancel_modify_called": bool(cancel_step.get("order_cancel_modify_called")),
    }
    terminal_rows = [
        dict(row)
        for row in (state.get("terminal_orders") or [])
        if isinstance(row, Mapping)
    ]
    terminal_rows.append(terminal_row)
    state["terminal_orders"] = terminal_rows[-200:]

    history_rows: list[Dict[str, Any]] = []
    matched_history = False
    for row in state.get("submitted_order_history") or []:
        if not isinstance(row, Mapping):
            continue
        updated = dict(row)
        row_order_no = _order_number_from_row(updated)
        row_key = str(updated.get("idempotency_key") or "").strip()
        row_symbol = _symbol_from_row(updated)
        if (order_no and row_order_no == order_no) or (key and row_key == key) or (
            not order_no and not key and symbol and row_symbol == symbol
        ):
            updated.update(terminal_row)
            matched_history = True
        history_rows.append(updated)
    if not matched_history:
        history_rows.append(terminal_row)
    state["submitted_order_history"] = history_rows[-500:]
    state["last_updated_kst"] = now.isoformat()


def _remove_pending_by_order_no(rows: Sequence[Mapping[str, Any]], order_no: str) -> list[Dict[str, Any]]:
    target = str(order_no or "").strip()
    if not target:
        return [dict(row) for row in rows if isinstance(row, Mapping)]
    return [
        dict(row)
        for row in rows
        if isinstance(row, Mapping) and _order_number_from_row(row) != target
    ]


def _pending_order_is_previous_day(pending: Mapping[str, Any], *, now: datetime) -> bool:
    submitted_at = _pending_submitted_at(pending)
    if submitted_at is None:
        return False
    return submitted_at.astimezone(KST).date() < now.astimezone(KST).date()


def _cancel_failure_is_terminal(cancel_step: Mapping[str, Any]) -> bool:
    text = " ".join(
        str(cancel_step.get(key) or "")
        for key in ("reason", "msg_cd", "msg1", "message", "error", "rt_msg")
    ).lower()
    if not text.strip():
        return False
    terminal_fragments = (
        "not_found",
        "not found",
        "expired",
        "already",
        "no order",
        "not exist",
        "does not exist",
        "cannot cancel",
        "uncancelable",
        "cancel not allowed",
        "원주문",
        "주문번호",
        "없",
        "만료",
        "취소불가",
        "정정취소불가",
        "취소 가능 수량",
        "취소가능수량",
    )
    return any(fragment in text for fragment in terminal_fragments)


def _cancel_previous_timing_pending_orders(
    state: Dict[str, Any],
    account_truth: Mapping[str, Any],
    *,
    adapter: KisPaperAdapter,
    token: str,
    now: datetime,
    enabled: bool,
    gate: Mapping[str, Any],
) -> Dict[str, Any]:
    pending_rows = [
        dict(row)
        for row in (state.get("pending_orders") or [])
        if isinstance(row, Mapping)
    ]
    candidates: list[Dict[str, Any]] = []
    for pending in pending_rows:
        remaining_quantity = _pending_remaining_quantity(pending, account_truth)
        if remaining_quantity <= 0:
            continue
        if not _is_previous_timing_pending_order(pending, now=now):
            continue
        row = dict(pending)
        row["_remaining_quantity"] = remaining_quantity
        candidates.append(row)

    if not candidates:
        return {
            "step": "previous_timing_pending_order_cancellation",
            "status": "skipped_no_previous_timing_pending_orders",
            "broker_endpoint_called": False,
            "order_cancel_modify_called": False,
            "cancelled_count": 0,
            "failed_count": 0,
            "candidate_count": 0,
        }
    if not enabled:
        return {
            "step": "previous_timing_pending_order_cancellation",
            "status": "blocked_paper_order_disabled",
            "broker_endpoint_called": False,
            "order_cancel_modify_called": False,
            "candidate_count": len(candidates),
            "cancelled_count": 0,
            "failed_count": len(candidates),
            "reason": "paper_order_enabled_required_for_cancel",
        }
    gate_payload = gate.get("evidence_payload") if isinstance(gate.get("evidence_payload"), Mapping) else {}
    if gate.get("allowed") is not True:
        return {
            "step": "previous_timing_pending_order_cancellation",
            "status": "blocked_market_session_gate",
            "broker_endpoint_called": False,
            "order_cancel_modify_called": False,
            "candidate_count": len(candidates),
            "cancelled_count": 0,
            "failed_count": len(candidates),
            "reason": gate.get("reason"),
            "marketSessionGate": dict(gate_payload),
        }

    cancelled_order_numbers: list[str] = []
    cancelled_symbols: list[str] = []
    terminal_cleanup_order_numbers: list[str] = []
    terminal_cleanup_symbols: list[str] = []
    failed_symbols: list[str] = []
    cancel_results: list[Dict[str, Any]] = []
    pending_after = list(pending_rows)
    for candidate in candidates:
        order_no = _order_number_from_row(candidate)
        symbol = _symbol_from_row(candidate)
        remaining_quantity = _coerce_nonnegative_int(candidate.get("_remaining_quantity"), 0)
        if _pending_order_is_previous_day(candidate, now=now):
            cleanup_result = {
                "step": "cancel_order",
                "status": "terminal_cleanup",
                "broker_endpoint_called": False,
                "order_cancel_modify_called": False,
                "reason": "previous_day_unfilled_order_not_active",
            }
            cancel_results.append(
                {
                    **cleanup_result,
                    "symbol": symbol,
                    "side": str(candidate.get("side") or "").strip().lower(),
                    "original_order_no": order_no,
                    "remaining_quantity": remaining_quantity,
                    "submitted_at_kst": candidate.get("submitted_at_kst"),
                    "cancel_reason": "previous_day_unfilled_order_not_active",
                }
            )
            terminal_cleanup_order_numbers.append(order_no)
            terminal_cleanup_symbols.append(symbol)
            pending_after = _remove_pending_by_order_no(pending_after, order_no)
            _mark_pending_order_terminal_cleanup(
                state,
                candidate,
                cleanup_result,
                now=now,
                reason="previous_day_unfilled_order_not_active",
                remaining_quantity=remaining_quantity,
            )
            continue
        try:
            cancel_step = adapter.cancelOrder(
                token,
                original_order_no=order_no,
                original_order_orgno=str(candidate.get("krx_forwarding_order_orgno") or ""),
                quantity=remaining_quantity,
            )
        except Exception as exc:  # pragma: no cover - defensive network ambiguity boundary
            cancel_step = {
                "step": "cancel_order",
                "status": "warn",
                "broker_endpoint_called": "unknown",
                "order_cancel_modify_called": "unknown",
                "reason": "cancel_order_exception_requires_reconciliation",
                "error_type": type(exc).__name__,
            }
        cancel_result = {
            **dict(cancel_step),
            "symbol": symbol,
            "side": str(candidate.get("side") or "").strip().lower(),
            "original_order_no": order_no,
            "remaining_quantity": remaining_quantity,
            "submitted_at_kst": candidate.get("submitted_at_kst"),
            "cancel_reason": "previous_timing_unfilled_order",
        }
        cancel_results.append(cancel_result)
        if _broker_step_passed(cancel_step):
            cancelled_order_numbers.append(order_no)
            cancelled_symbols.append(symbol)
            pending_after = _remove_pending_by_order_no(pending_after, order_no)
            _mark_pending_order_cancelled(
                state,
                candidate,
                cancel_result,
                now=now,
                reason="previous_timing_unfilled_order",
                remaining_quantity=remaining_quantity,
            )
        elif _cancel_failure_is_terminal(cancel_result):
            terminal_cleanup_order_numbers.append(order_no)
            terminal_cleanup_symbols.append(symbol)
            pending_after = _remove_pending_by_order_no(pending_after, order_no)
            _mark_pending_order_terminal_cleanup(
                state,
                candidate,
                cancel_result,
                now=now,
                reason="broker_expired_or_not_found",
                remaining_quantity=remaining_quantity,
            )
        else:
            failed_symbols.append(symbol)

    if cancelled_order_numbers or terminal_cleanup_order_numbers:
        state["pending_orders"] = pending_after
        state["last_pending_cancel_sweep_kst"] = now.isoformat()
        state["last_updated_kst"] = now.isoformat()

    failed_count = len(failed_symbols)
    broker_endpoint_called = any(result.get("broker_endpoint_called") is True for result in cancel_results)
    order_cancel_modify_called = any(result.get("order_cancel_modify_called") is True for result in cancel_results)
    return {
        "step": "previous_timing_pending_order_cancellation",
        "status": "warn" if failed_count else "pass",
        "broker_endpoint_called": broker_endpoint_called,
        "order_cancel_modify_called": order_cancel_modify_called,
        "candidate_count": len(candidates),
        "cancelled_count": len(cancelled_order_numbers),
        "terminal_cleanup_count": len(terminal_cleanup_order_numbers),
        "failed_count": failed_count,
        "cancelled_order_numbers": cancelled_order_numbers,
        "cancelled_symbols": cancelled_symbols,
        "terminal_cleanup_order_numbers": terminal_cleanup_order_numbers,
        "terminal_cleanup_symbols": terminal_cleanup_symbols,
        "failed_symbols": failed_symbols,
        "cancel_results": cancel_results,
        "marketSessionGate": dict(gate_payload),
    }


def _account_truth_from_steps(steps: Sequence[Mapping[str, Any]], *, produced_at: datetime) -> Dict[str, Any]:
    balance_summary: Dict[str, Any] = {}
    buyable_summary: Dict[str, Any] = {}
    sellable_summary: Dict[str, Any] = {}
    cancelable_summary: Dict[str, Any] = {}
    positions: list[Dict[str, Any]] = []
    daily_fills: list[Dict[str, Any]] = []
    balance_status = None
    buyable_status = None
    sellable_status = None
    cancelable_status = None
    realized_status = None
    holiday_status = None
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        if step.get("step") == "balance_inquire":
            balance_status = step.get("status")
            if isinstance(step.get("dashboard_account_summary"), Mapping):
                balance_summary = dict(step["dashboard_account_summary"])
            if isinstance(step.get("dashboard_positions"), list):
                positions = [
                    dict(row)
                    for row in step["dashboard_positions"]
                    if isinstance(row, Mapping)
                ][:50]
        elif step.get("step") == "buyable_inquire_psbl_order":
            buyable_status = step.get("status")
            if isinstance(step.get("dashboard_buyable_summary"), Mapping):
                buyable_summary = dict(step["dashboard_buyable_summary"])
        elif step.get("step") == "sellable_inquire_psbl_sell":
            sellable_status = step.get("status")
            if isinstance(step.get("dashboard_sellable_summary"), Mapping):
                sellable_summary = dict(step["dashboard_sellable_summary"])
        elif step.get("step") == "cancelable_order_inquire":
            cancelable_status = step.get("status")
            if isinstance(step.get("dashboard_cancelable_summary"), Mapping):
                cancelable_summary = dict(step["dashboard_cancelable_summary"])
        elif step.get("step") == "realized_pnl_inquire":
            realized_status = step.get("status")
        elif step.get("step") == "holiday_inquire":
            holiday_status = step.get("status")
        elif step.get("step") == "daily_order_fill_inquire":
            if isinstance(step.get("dashboard_daily_fills"), list):
                daily_fills = [
                    dict(row)
                    for row in step["dashboard_daily_fills"]
                    if isinstance(row, Mapping)
                ][:100]
    buyable_cash = _int_or_none(buyable_summary.get("buyable_cash_krw"))
    cash_balance = _int_or_none(balance_summary.get("cash_balance_krw"))
    total_eval = _int_or_none(balance_summary.get("total_eval_krw"))
    stock_eval = _int_or_none(balance_summary.get("stock_eval_krw"))
    sellable_quantity = _int_or_none(sellable_summary.get("sellable_quantity"))
    positions_count = _int_or_none(balance_summary.get("positions_count")) or 0
    available_cash = buyable_cash if buyable_cash is not None else cash_balance
    return {
        "schema_version": "account_truth_snapshot/v0",
        "source": "kis_paper_read_steps",
        "produced_at_kst": produced_at.isoformat(),
        "balance_status": balance_status,
        "buyable_status": buyable_status,
        "sellable_status": sellable_status,
        "sellable_quantity": sellable_quantity,
        "cancelable_order_status": cancelable_status,
        "cancelable_order_count": _int_or_none(cancelable_summary.get("cancelable_order_count")) or 0,
        "cancelable_order_numbers": list(cancelable_summary.get("cancelable_order_numbers") or [])[:20],
        "holiday_status": holiday_status,
        "realized_pnl_status": realized_status,
        "cash_balance_krw": cash_balance,
        "buyable_cash_krw": buyable_cash,
        "available_cash_krw": available_cash,
        "stock_eval_krw": stock_eval,
        "current_position_value_krw": stock_eval,
        "total_eval_krw": total_eval,
        "effective_total_deposit_krw": total_eval,
        "current_holdings_count": positions_count,
        "positions_count": positions_count,
        "positions": positions,
        "daily_order_fills": daily_fills,
        "credential_values_printed": False,
        "raw_response_stored": False,
    }


def _reconcile_runner_state_from_account_truth(
    state: Dict[str, Any],
    account_truth: Mapping[str, Any],
    *,
    now: datetime,
) -> Dict[str, Any]:
    raw_positions = account_truth.get("positions") if isinstance(account_truth.get("positions"), list) else []
    positions_by_symbol: Dict[str, Dict[str, Any]] = {}
    for row in raw_positions:
        if not isinstance(row, Mapping):
            continue
        symbol = _symbol_from_row(row)
        quantity = _positive_quantity_from_row(row)
        if symbol and quantity > 0:
            positions_by_symbol[symbol] = dict(row)

    pending_rows = [
        dict(row)
        for row in (state.get("pending_orders") or [])
        if isinstance(row, Mapping)
    ]
    existing_holdings = [
        dict(row)
        for row in (state.get("holdings") or [])
        if isinstance(row, Mapping)
    ]
    holdings_by_symbol = {
        _symbol_from_row(row): dict(row)
        for row in existing_holdings
        if _symbol_from_row(row)
    }
    pending_buy_symbols_initial = {
        _symbol_from_row(row)
        for row in pending_rows
        if _symbol_from_row(row) and str(row.get("side") or "buy").strip().lower() == "buy"
    }
    sell_fills: list[Dict[str, Any]] = []
    buy_fills: list[Dict[str, Any]] = []
    for row in account_truth.get("daily_order_fills") or []:
        if not isinstance(row, Mapping):
            continue
        side = str(row.get("side") or "").strip().lower()
        if side not in {"buy", "sell"}:
            continue
        filled_quantity = _filled_quantity_from_row(row)
        remaining_quantity = _remaining_quantity_from_row(row)
        normalized_fill = {
            **dict(row),
            "side": side,
            "symbol": _symbol_from_row(row),
            "order_no": _order_number_from_row(row),
            "filled_quantity": filled_quantity,
            "remaining_quantity": remaining_quantity,
        }
        if side == "sell":
            if filled_quantity <= 0 and remaining_quantity != 0:
                continue
            sell_fills.append(normalized_fill)
            continue
        if filled_quantity <= 0 and remaining_quantity is None:
            continue
        buy_fills.append(normalized_fill)
    refreshed_symbols: list[str] = []
    balance_promoted_symbols: list[str] = []
    for symbol, position in positions_by_symbol.items():
        existing = holdings_by_symbol.get(symbol)
        if not existing:
            quantity = _positive_quantity_from_row(position)
            if quantity <= 0:
                continue
            holdings_by_symbol[symbol] = {
                "symbol": symbol,
                "ticker": symbol,
                "name": position.get("name") or symbol,
                "side": "buy",
                "quantity": quantity,
                "sellable_quantity": position.get("sellable_quantity"),
                "average_price": position.get("average_price"),
                "current_price": position.get("current_price"),
                "eval_amount_krw": position.get("eval_amount_krw"),
                "pnl_krw": position.get("pnl_krw"),
                "position_state": "holding_confirmed",
                "order_state": "holding_confirmed",
                "source": "kis_balance_reconciliation",
                "confirmed_at_kst": now.isoformat(),
                "last_reconciled_at_kst": now.isoformat(),
            }
            if symbol not in pending_buy_symbols_initial:
                balance_promoted_symbols.append(symbol)
            continue
        refreshed: Dict[str, Any] = dict(existing)
        refreshed.update(
            {
                "symbol": symbol,
                "ticker": symbol,
                "name": position.get("name") or existing.get("name") or symbol,
                "quantity": position.get("quantity") or existing.get("quantity"),
                "sellable_quantity": position.get("sellable_quantity"),
                "average_price": position.get("average_price") or existing.get("average_price"),
                "current_price": position.get("current_price"),
                "eval_amount_krw": position.get("eval_amount_krw"),
                "pnl_krw": position.get("pnl_krw"),
                "position_state": "holding_confirmed",
                "order_state": "holding_confirmed",
                "source": "kis_balance_reconciliation",
                "last_reconciled_at_kst": now.isoformat(),
            }
        )
        if refreshed != existing:
            holdings_by_symbol[symbol] = refreshed
            refreshed_symbols.append(symbol)

    remaining_pending: list[Dict[str, Any]] = []
    promoted_symbols: list[str] = []
    closed_sell_symbols: list[str] = []
    partial_sell_symbols: list[str] = []
    partial_buy_symbols: list[str] = []
    reconciled_sell_order_numbers: list[str] = []
    reconciled_buy_order_numbers: list[str] = []
    for pending in pending_rows:
        symbol = _symbol_from_row(pending)
        side = str(pending.get("side") or "buy").strip().lower()
        position = positions_by_symbol.get(symbol)
        if not symbol:
            remaining_pending.append(pending)
            continue
        if side == "sell":
            pending_order_no = _order_number_from_row(pending)
            matched_fill = next(
                (
                    row for row in sell_fills
                    if (
                        pending_order_no
                        and str(row.get("order_no") or "").strip() == pending_order_no
                    )
                    or (not pending_order_no and str(row.get("symbol") or "").strip() == symbol)
                ),
                None,
            )
            if not matched_fill:
                remaining_pending.append(pending)
                continue
            filled_quantity = _coerce_nonnegative_int(matched_fill.get("filled_quantity"), 0)
            remaining_quantity = matched_fill.get("remaining_quantity")
            if matched_fill.get("order_no"):
                reconciled_sell_order_numbers.append(str(matched_fill["order_no"]))
            existing = holdings_by_symbol.get(symbol)
            pending_quantity = _coerce_nonnegative_int(pending.get("quantity"), 0)
            inferred_remaining_quantity = (
                remaining_quantity
                if remaining_quantity is not None
                else max(pending_quantity - filled_quantity, 0)
            )
            if existing and filled_quantity > 0:
                existing_quantity = _positive_quantity_from_row(existing)
                next_quantity = max(existing_quantity - filled_quantity, 0)
                if next_quantity > 0 and inferred_remaining_quantity > 0:
                    updated = dict(existing)
                    updated.update(
                        {
                            "quantity": next_quantity,
                            "sellable_quantity": min(
                                _coerce_nonnegative_int(existing.get("sellable_quantity"), next_quantity),
                                next_quantity,
                            ),
                            "position_state": "holding_confirmed",
                            "order_state": "sell_partially_filled",
                            "last_reconciled_at_kst": now.isoformat(),
                            "last_sell_fill_order_no": matched_fill.get("order_no"),
                            "last_sell_filled_quantity": filled_quantity,
                        }
                    )
                    holdings_by_symbol[symbol] = updated
                    partial_sell_symbols.append(symbol)
                else:
                    holdings_by_symbol.pop(symbol, None)
                    closed_sell_symbols.append(symbol)
            if inferred_remaining_quantity > 0:
                updated_pending = dict(pending)
                updated_pending.update(
                    {
                        "filled_quantity": filled_quantity,
                        "remaining_quantity": inferred_remaining_quantity,
                        "last_reconciled_at_kst": now.isoformat(),
                    }
                )
                remaining_pending.append(updated_pending)
            continue
        matched_buy_fill = _matching_daily_fill_for_pending(pending, account_truth)
        if (
            matched_buy_fill
            and str(matched_buy_fill.get("side") or "").strip().lower()
            and str(matched_buy_fill.get("side") or "").strip().lower() != side
        ):
            matched_buy_fill = None
        buy_filled_quantity = _filled_quantity_from_row(matched_buy_fill) if matched_buy_fill else 0
        buy_remaining_quantity = _remaining_quantity_from_row(matched_buy_fill) if matched_buy_fill else None
        buy_order_quantity = (
            _coerce_nonnegative_int(
                matched_buy_fill.get("order_quantity") or matched_buy_fill.get("quantity"),
                0,
            )
            if matched_buy_fill
            else 0
        )
        if matched_buy_fill and buy_remaining_quantity is None and buy_order_quantity > 0:
            buy_remaining_quantity = max(buy_order_quantity - buy_filled_quantity, 0)
        if not position:
            if matched_buy_fill and buy_remaining_quantity is not None:
                updated_pending = dict(pending)
                updated_pending.update(
                    {
                        "filled_quantity": buy_filled_quantity,
                        "remaining_quantity": buy_remaining_quantity,
                        "last_reconciled_at_kst": now.isoformat(),
                    }
                )
                if buy_remaining_quantity > 0:
                    updated_pending["quantity"] = buy_remaining_quantity
                    if buy_filled_quantity > 0:
                        updated_pending["order_state"] = "partially_filled"
                remaining_pending.append(updated_pending)
                continue
            remaining_pending.append(pending)
            continue

        quantity = _positive_quantity_from_row(position)
        if quantity <= 0:
            remaining_pending.append(pending)
            continue
        if (
            matched_buy_fill
            and buy_filled_quantity <= 0
            and (buy_remaining_quantity is None or buy_remaining_quantity > 0)
        ):
            updated_pending = dict(pending)
            updated_pending.update(
                {
                    "filled_quantity": buy_filled_quantity,
                    "remaining_quantity": buy_remaining_quantity,
                    "last_reconciled_at_kst": now.isoformat(),
                }
            )
            if buy_remaining_quantity is not None and buy_remaining_quantity > 0:
                updated_pending["quantity"] = buy_remaining_quantity
            remaining_pending.append(updated_pending)
            continue

        existing = holdings_by_symbol.get(symbol, {})
        holding: Dict[str, Any] = {**existing, **pending}
        holding.update(
            {
                "symbol": symbol,
                "ticker": symbol,
                "name": position.get("name") or pending.get("name") or pending.get("symbol_name") or symbol,
                "side": "buy",
                "quantity": quantity,
                "sellable_quantity": position.get("sellable_quantity"),
                "average_price": position.get("average_price") or pending.get("order_price") or pending.get("entry_price_limit"),
                "current_price": position.get("current_price"),
                "eval_amount_krw": position.get("eval_amount_krw"),
                "pnl_krw": position.get("pnl_krw"),
                "position_state": "holding_confirmed",
                "order_state": "holding_confirmed",
                "source": "kis_balance_reconciliation",
                "confirmed_at_kst": existing.get("confirmed_at_kst") or now.isoformat(),
                "last_reconciled_at_kst": now.isoformat(),
                "pending_order_reconciled": True,
                "reconciled_from_pending_order": True,
            }
        )
        for key in (
            "target_price",
            "stop_loss_price",
            "take_profit",
            "stop_loss",
            "trailing_stop_pct",
            "idempotency_key",
            "flash_trade_document_ref",
            "broker_order_no",
            "krx_forwarding_order_orgno",
            "submitted_at_kst",
            "action_source",
            "intent_type",
        ):
            if holding.get(key) in (None, "") and pending.get(key) not in (None, ""):
                holding[key] = pending.get(key)
        holdings_by_symbol[symbol] = holding
        promoted_symbols.append(symbol)
        if matched_buy_fill:
            buy_order_no = _order_number_from_row(matched_buy_fill)
            if buy_order_no and buy_order_no not in reconciled_buy_order_numbers:
                reconciled_buy_order_numbers.append(buy_order_no)
        if buy_remaining_quantity is not None and buy_remaining_quantity > 0:
            updated_pending = dict(pending)
            updated_pending.update(
                {
                    "quantity": buy_remaining_quantity,
                    "filled_quantity": buy_filled_quantity,
                    "remaining_quantity": buy_remaining_quantity,
                    "order_state": (
                        "partially_filled"
                        if buy_filled_quantity > 0
                        else pending.get("order_state", "pending")
                    ),
                    "last_reconciled_at_kst": now.isoformat(),
                }
            )
            remaining_pending.append(updated_pending)
            if symbol not in partial_buy_symbols:
                partial_buy_symbols.append(symbol)

    stale_removed_symbols: list[str] = []
    if account_truth.get("balance_status") == "pass":
        pending_buy_symbols = {
            _symbol_from_row(row)
            for row in remaining_pending
            if isinstance(row, Mapping) and str(row.get("side") or "buy").strip().lower() == "buy"
        }
        for symbol in sorted(list(holdings_by_symbol)):
            if symbol and symbol not in positions_by_symbol and symbol not in pending_buy_symbols:
                holdings_by_symbol.pop(symbol, None)
                if symbol not in closed_sell_symbols:
                    stale_removed_symbols.append(symbol)

    if reconciled_sell_order_numbers or reconciled_buy_order_numbers:
        history_rows: list[Dict[str, Any]] = []
        fill_rows = sell_fills + buy_fills
        for row in state.get("submitted_order_history") or []:
            if not isinstance(row, Mapping):
                continue
            updated = dict(row)
            order_no = _order_number_from_row(updated)
            matched_fill = next(
                (fill for fill in fill_rows if order_no and str(fill.get("order_no") or "").strip() == order_no),
                None,
            )
            if matched_fill:
                updated.update(
                    {
                        "filled_quantity": matched_fill.get("filled_quantity"),
                        "remaining_quantity": matched_fill.get("remaining_quantity"),
                        "filled_price": matched_fill.get("filled_price"),
                        "fill_status": matched_fill.get("fill_status"),
                        "last_fill_reconciled_at_kst": now.isoformat(),
                    }
                )
            history_rows.append(updated)
        state["submitted_order_history"] = history_rows[-500:]

    changed = (
        bool(promoted_symbols)
        or bool(balance_promoted_symbols)
        or bool(refreshed_symbols)
        or bool(closed_sell_symbols)
        or bool(partial_sell_symbols)
        or bool(partial_buy_symbols)
        or bool(stale_removed_symbols)
        or len(remaining_pending) != len(pending_rows)
        or bool(reconciled_sell_order_numbers)
        or bool(reconciled_buy_order_numbers)
    )
    if changed:
        state["pending_orders"] = remaining_pending
        state["holdings"] = [
            holdings_by_symbol[symbol]
            for symbol in sorted(holdings_by_symbol)
        ][:50]
        state["last_reconciled_kst"] = now.isoformat()
        state["last_updated_kst"] = now.isoformat()

    return {
        "step": "local_state_reconciliation",
        "status": "pass" if changed else "skipped_no_confirmed_holding_match",
        "source": "kis_balance_reconciliation",
        "broker_endpoint_called": False,
        "raw_response_stored": False,
        "promoted_to_holdings_count": len(promoted_symbols),
        "promoted_symbols": promoted_symbols,
        "balance_promoted_symbols_count": len(balance_promoted_symbols),
        "balance_promoted_symbols": balance_promoted_symbols,
        "refreshed_holdings_count": len(refreshed_symbols),
        "refreshed_symbols": refreshed_symbols,
        "closed_sell_symbols_count": len(closed_sell_symbols),
        "closed_sell_symbols": closed_sell_symbols,
        "partial_sell_symbols_count": len(partial_sell_symbols),
        "partial_sell_symbols": partial_sell_symbols,
        "partial_buy_symbols_count": len(partial_buy_symbols),
        "partial_buy_symbols": partial_buy_symbols,
        "stale_removed_symbols_count": len(stale_removed_symbols),
        "stale_removed_symbols": stale_removed_symbols,
        "reconciled_sell_order_numbers": reconciled_sell_order_numbers,
        "reconciled_buy_order_numbers": reconciled_buy_order_numbers,
        "pending_remaining_count": len(remaining_pending),
        "holdings_count": len(state.get("holdings") or []),
    }


def _isInvalidTokenStep(step: Mapping[str, Any]) -> bool:
    return str(step.get("msg_cd") or "").strip() == "EGW00121"


def _runAccountStepWithTokenRefresh(
    *,
    adapter: KisPaperAdapter,
    source: Mapping[str, str],
    now: datetime,
    result: Dict[str, Any],
    token: str,
    tokenCacheManaged: bool,
    tokenResult: Mapping[str, Any],
    call: Callable[[str], Dict[str, Any]],
) -> tuple[Dict[str, Any], str, bool, Mapping[str, Any]]:
    step = call(token)
    if not (_isInvalidTokenStep(step) and tokenCacheManaged and tokenResult.get("cache_hit")):
        return step, token, tokenCacheManaged, tokenResult
    result["steps"].append(
        invalidateKisPaperAccessToken(
            source,
            reason=f"{step.get('step') or 'account_step'}_invalid_cached_token",
        )
    )
    refreshedResult, refreshedToken, refreshedManaged = loadKisPaperAccessToken(adapter, env=source, now=now)
    result["steps"].append(refreshedResult)
    if not refreshedResult.get("token_present") or not refreshedToken:
        return step, token, tokenCacheManaged, tokenResult
    return call(refreshedToken), refreshedToken, refreshedManaged, refreshedResult


def runContinuousPaperTick(
    *,
    intent: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
    adapter: Optional[KisPaperAdapter] = None,
    at_kst: Optional[str] = None,
) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    now = _now_kst()
    reference_now = _parse_optional_kst_timestamp(at_kst) or now
    config = loadContinuousPaperRunnerConfig(source, now=reference_now)
    status = _status_with_env_overrides(base_runner.get_runner_status(at_kst), source, at_kst=at_kst)
    paper_readiness = buildPaperExperimentReadiness(config, status)
    data_root = Path(config["data_root"])
    local_state = _load_runner_state(config, data_root=data_root)
    explicit_intent = intent is not None
    intent_source = "explicit_argument" if explicit_intent else "none"
    if intent is None:
        loaded = _load_next_intent_from_queue(data_root=data_root, at=reference_now, state=local_state)
        intent = loaded.get("intent")
        intent_source = str(loaded.get("source") or "none")
    result: Dict[str, Any] = {
        "event": "kis_paper_continuous_tick",
        "timestamp_kst": now.isoformat(),
        "runner_id": config["runner_id"],
        "operation_mode": config["operation_mode"],
        "investment_mode": config["investment_mode"],
        "market_analysis_feed_mode": config["market_analysis_feed_mode"],
        "execution_venue_mode": config["execution_venue_mode"],
        "nxt_enabled": config["nxt_enabled"],
        "continuous_service": True,
        "duration_policy": "operator_selected",
        "fixed_duration_days": None,
        "paper_network_enabled": config["paper_network_enabled"],
        "paper_order_requested": config["paper_order_requested"],
        "paper_order_enabled": config["paper_order_enabled"],
        "paper_order_loop_enabled": config["paper_order_loop_enabled"],
        "paper_order_approval": config["paper_order_approval"],
        "paper_experiment_ready": paper_readiness["ready"],
        "paper_experiment_readiness": paper_readiness,
        "live_money_trading_ready": {
            "state": "not_applicable",
            "blocks_paper_operation": False,
        },
        "production_quality_ready": {
            "state": "partial",
            "blocks_paper_operation": False,
        },
        "paper_domain_only": True,
        "paper_mock_operation_target": True,
        "live_domain_calls_made": False,
        "ai_provider_calls_made": False,
        "public_dashboard_exposed": False,
        "fake_broker_used": False,
        "credential_values_printed": False,
        "raw_responses_stored": False,
        "status": "pending",
        "intent_source": intent_source,
        "intent_loaded": bool(intent),
        "loaded_intent": dict(intent) if isinstance(intent, Mapping) else None,
        "base_runner_order_gate": status["orderGate"],
        "intent_priority_policy": "exit_intents_before_entry_fifo",
        "intent_drain_policy": "sell_exit_intents_only",
        "max_intents_per_tick": config["max_intents_per_tick"],
        "intent_processing_summary": {
            "intents_seen_this_tick": 0,
            "intents_submitted_this_tick": 0,
            "intents_quarantined_this_tick": 0,
            "intents_snoozed_this_tick": 0,
            "intents_invalid_this_tick": 0,
            "intents_remaining": None,
            "queue_starvation_detected": False,
        },
        "intent_dispositions": [],
        "steps": [],
        "observationWindow": ledger.buildObservationWindowManifest(
            started_at_kst=str(source.get("HWISTOCK_OBSERVATION_STARTED_AT_KST") or now.isoformat()),
            ended_at_kst=source.get("HWISTOCK_OBSERVATION_ENDED_AT_KST") or None,
            operator_note=source.get("HWISTOCK_OBSERVATION_NOTE") or None,
        ),
    }

    if not config["paper_network_enabled"]:
        result["status"] = "idle_paper_network_disabled"
        result["steps"].append({"step": "network", "status": "blocked", "reason": "HWISTOCK_KIS_PAPER_NETWORK_ENABLED_false"})
        return result

    reconciliation_required = _runner_state_requires_reconciliation(local_state)
    result["reconciliation_required"] = reconciliation_required

    if not intent and not reconciliation_required:
        result["status"] = "idle_no_order_intent"
        result["steps"].append(
            {
                "step": "trading_account_truth",
                "status": "skipped_no_order_intent",
                "reason": "fresh trading account truth is required only for an order preflight",
                "broker_endpoint_called": False,
                "dashboard_account_summary_reused_for_order": False,
            }
        )
        result["account_truth"] = {
            "schema_version": "account_truth_snapshot/v0",
            "source": "not_required_without_order_intent",
            "status": "skipped_no_order_intent",
            "produced_at_kst": reference_now.isoformat(),
            "broker_endpoint_called": False,
            "credential_values_printed": False,
        }
        return result

    if intent:
        order_gate = msg.evaluateKisCallGate(
            now_kst=reference_now,
            investment_mode=config["investment_mode"],
            call_family="kis_order_submit",
            env=source,
        )
        result["calendar_context"] = order_gate["calendar_context"]
        result["kis_order_submit_gate"] = order_gate["evidence_payload"]
        result["steps"].append(order_gate["evidence_payload"])
        if not order_gate["allowed"]:
            result["status"] = "warn"
            result["executionPreflight"] = {
                "schema_version": "paper_intent_execution_preflight/v0",
                "ok": False,
                "errors": ["market_session_gate_blocked_order_submit", str(order_gate["reason"])],
                "marketSessionGate": order_gate["evidence_payload"],
                "dashboard_account_summary_reused_for_order": False,
                "order_preflight_truth_source": "trading_account_truth",
                "broker_endpoint_called": False,
            }
            result["steps"].append(
                {
                    "step": "cash_order",
                    "status": "blocked_market_session_gate",
                    "reason": order_gate["reason"],
                    "marketSessionGate": order_gate["evidence_payload"],
                    "broker_endpoint_called": False,
                }
            )
            return result

        if not config["paper_order_enabled"]:
            result["status"] = "ok"
            result["steps"].append(
                {
                    "step": "cash_order",
                    "status": "blocked_paper_order_disabled"
                    if not config["paper_order_requested"]
                    else "blocked_paper_order_approval_missing",
                    "broker_endpoint_called": False,
                    "reason": "HWISTOCK_KIS_PAPER_ORDER_ENABLED_false"
                    if not config["paper_order_requested"]
                    else config["paper_order_approval"]["reason"],
                }
            )
            return result

        account_gate = msg.evaluateKisCallGate(
            now_kst=reference_now,
            investment_mode=config["investment_mode"],
            call_family="trading_account_truth",
            env=source,
        )
        result["trading_account_truth_gate"] = account_gate["evidence_payload"]
        result["steps"].append(account_gate["evidence_payload"])
        if not account_gate["allowed"]:
            result["status"] = "warn"
            result["account_truth"] = {
                "schema_version": "account_truth_snapshot/v0",
                "source": "trading_account_truth_gate",
                "status": account_gate["evidence_payload"]["status"],
                "reason": account_gate["reason"],
                "produced_at_kst": reference_now.isoformat(),
                "broker_endpoint_called": False,
                "credential_values_printed": False,
            }
            result["steps"].append(
                {
                    "step": "cash_order",
                    "status": "blocked_trading_account_truth_gate",
                    "reason": account_gate["reason"],
                    "broker_endpoint_called": False,
                }
            )
            return result

    else:
        reconciliation_gate = msg.evaluateKisCallGate(
            now_kst=reference_now,
            investment_mode=config["investment_mode"],
            call_family="kis_reconciliation",
            env=source,
            reconciliation_required=True,
        )
        result["calendar_context"] = reconciliation_gate["calendar_context"]
        result["kis_reconciliation_gate"] = reconciliation_gate["evidence_payload"]
        result["steps"].append(reconciliation_gate["evidence_payload"])
        if not reconciliation_gate["allowed"]:
            result["status"] = "warn"
            result["account_truth"] = {
                "schema_version": "account_truth_snapshot/v0",
                "source": "kis_reconciliation_gate",
                "status": reconciliation_gate["evidence_payload"]["status"],
                "reason": reconciliation_gate["reason"],
                "produced_at_kst": reference_now.isoformat(),
                "broker_endpoint_called": False,
                "credential_values_printed": False,
            }
            return result

    adapter = adapter or KisPaperAdapter(env=source, transport=UrllibJsonTransport())
    missing = adapter.missingEnvKeys()
    if missing:
        result["status"] = "blocked_missing_env"
        result["steps"].append({"step": "config", "status": "blocked_missing_env", "missing_env_keys": missing})
        return result

    token_result, token, token_cache_managed = loadKisPaperAccessToken(adapter, env=source, now=now)
    result["steps"].append(token_result)
    if not token_result.get("token_present") or not token:
        result["status"] = "blocked_token_missing"
        return result

    if _bool_env(source, "HWISTOCK_KIS_FILL_NOTICE_WS_ENABLED", True):
        approval_result, approval_key = adapter.issueWebsocketApprovalWithValue()
        result["steps"].append(approval_result)
        if approval_key:
            result["steps"].append(adapter.subscribeFillNotice(approval_key))
        else:
            result["steps"].append(
                {
                    "step": "ws_fill_notice",
                    "status": "blocked_websocket_approval_key_missing",
                    "tr_id": "H0STCNI9",
                    "ack_received": False,
                    "raw_response_stored": False,
                    "credential_values_printed": False,
                }
            )

    sample_symbol = str(
        (intent or {}).get("symbol")
        or (intent or {}).get("ticker")
        or source.get("HWISTOCK_KIS_HEALTH_SYMBOL", "005930")
    ).strip() or "005930"
    result["steps"].append(adapter.inquirePrice(token, sample_symbol))
    _sleepForKisCallGap(config)
    balanceStep, token, token_cache_managed, token_result = _runAccountStepWithTokenRefresh(
        adapter=adapter,
        source=source,
        now=now,
        result=result,
        token=token,
        tokenCacheManaged=token_cache_managed,
        tokenResult=token_result,
        call=adapter.inquireBalance,
    )
    result["steps"].append(balanceStep)
    _sleepForKisCallGap(config)
    buyableStep, token, token_cache_managed, token_result = _runAccountStepWithTokenRefresh(
        adapter=adapter,
        source=source,
        now=now,
        result=result,
        token=token,
        tokenCacheManaged=token_cache_managed,
        tokenResult=token_result,
        call=lambda value: adapter.inquireBuyable(value, sample_symbol),
    )
    result["steps"].append(buyableStep)
    _sleepForKisCallGap(config)
    result["steps"].append(adapter.inquireSellable(token, sample_symbol))
    _sleepForKisCallGap(config)
    result["steps"].append(adapter.inquireRealizedPnl(token))
    _sleepForKisCallGap(config)
    dailyStep, token, token_cache_managed, token_result = _runAccountStepWithTokenRefresh(
        adapter=adapter,
        source=source,
        now=now,
        result=result,
        token=token,
        tokenCacheManaged=token_cache_managed,
        tokenResult=token_result,
        call=lambda value: adapter.dailyOrderFillLookup(value, date_yyyymmdd=now.strftime("%Y%m%d")),
    )
    result["steps"].append(dailyStep)
    _sleepForKisCallGap(config)
    result["steps"].append(adapter.inquireCancelableOrders(token))
    _sleepForKisCallGap(config)
    result["steps"].append(
        {
            "step": "holiday_inquire",
            "status": "skipped_provider_unsupported",
            "reason": "CTCA0903R paper/mock unsupported; local cached KRX calendar is primary",
            "broker_endpoint_called": False,
            "paper_read_only": True,
            "raw_response_stored": False,
            "credential_values_printed": False,
        }
    )
    base_account_truth = _account_truth_from_steps(result["steps"], produced_at=reference_now)
    result["account_truth"] = (
        enrichAccountTruthWithSellableTruth(base_account_truth, intent)
        if intent
        else base_account_truth
    )
    reconciliation_step = _reconcile_runner_state_from_account_truth(
        local_state,
        base_account_truth,
        now=reference_now,
    )
    result["steps"].append(reconciliation_step)
    if reconciliation_step.get("status") == "pass":
        _write_runner_state(local_state, config, data_root=data_root)

    pending_cancel_gate = msg.evaluateKisCallGate(
        now_kst=reference_now,
        investment_mode=config["investment_mode"],
        call_family="kis_order_submit",
        env=source,
    )
    pending_cancel_step = _cancel_previous_timing_pending_orders(
        local_state,
        base_account_truth,
        adapter=adapter,
        token=token,
        now=reference_now,
        enabled=bool(config["paper_order_enabled"]),
        gate=pending_cancel_gate,
    )
    if pending_cancel_step.get("candidate_count"):
        result["steps"].append(pending_cancel_step)
    if (
        _coerce_nonnegative_int(pending_cancel_step.get("cancelled_count"), 0) > 0
        or _coerce_nonnegative_int(pending_cancel_step.get("terminal_cleanup_count"), 0) > 0
    ):
        _write_runner_state(local_state, config, data_root=data_root)

    current_intent = dict(intent) if isinstance(intent, Mapping) else None
    max_intents = 1 if explicit_intent else int(config["max_intents_per_tick"])
    processed_count = 0
    while current_intent and processed_count < max_intents:
        processed_count += 1
        key = _intent_key(current_intent)
        side = _intent_side(current_intent)
        symbol = _intent_symbol(current_intent)
        intent_account_truth = enrichAccountTruthWithSellableTruth(base_account_truth, current_intent)
        result["account_truth"] = intent_account_truth
        if side == "sell":
            result["steps"].append(_sellable_truth_normalization_step(current_intent, intent_account_truth))
        local_order_state = _order_state_snapshot_from_runner_state(local_state, now=now)
        preflight = evaluateIntentExecutionPreflight(
            current_intent,
            order_state_snapshot=local_order_state,
            status=status,
            account_truth=intent_account_truth,
        )
        result["executionPreflight"] = preflight
        result["riskOverlay"] = preflight.get("riskOverlay")
        disposition_step: Dict[str, Any] = {
            "step": "intent_disposition",
            "intent_key": key,
            "idempotency_key": key,
            "symbol": symbol,
            "side": side,
            "queue_continued": False,
            "next_intent_loaded": False,
            "broker_endpoint_called": False,
        }
        if not preflight["ok"]:
            result["steps"].append(
                {
                    "step": "cash_order",
                    "status": "blocked_risk_overlay",
                    "errors": preflight["errors"],
                    "broker_endpoint_called": False,
                }
            )
            disposition = _classify_preflight_disposition(
                current_intent,
                preflight,
                account_truth=intent_account_truth,
                now=reference_now,
            )
            disposition_name = str(disposition.get("intent_disposition") or "invalid_payload")
            if disposition_name in {"quarantined_terminal", "invalid_payload", "expired"}:
                _mark_runner_state_quarantined(local_state, current_intent, disposition, now=reference_now)
                _write_runner_state(local_state, config, data_root=data_root)
                result["intent_processing_summary"]["intents_quarantined_this_tick"] += 1
                if disposition_name == "invalid_payload":
                    result["intent_processing_summary"]["intents_invalid_this_tick"] += 1
            elif disposition_name in {"snoozed_retryable", "blocked_duplicate_active_exit"}:
                _mark_runner_state_snoozed(local_state, current_intent, disposition, now=reference_now)
                _write_runner_state(local_state, config, data_root=data_root)
                result["intent_processing_summary"]["intents_snoozed_this_tick"] += 1
            disposition_step.update(disposition)
        else:
            session_limit = evaluatePaperSessionLimits(
                current_intent,
                local_state,
                config["paper_order_approval"],
                now=reference_now,
            )
            result["paperSessionLimitPreflight"] = session_limit
            if not session_limit["ok"]:
                result["steps"].append(
                    {
                        "step": "cash_order",
                        "status": "blocked_paper_session_limit",
                        "broker_endpoint_called": False,
                        "errors": session_limit["errors"],
                        "sessionLimit": session_limit,
                    }
                )
                retry_after = reference_now + timedelta(seconds=RUNNER_SNOOZE_RETRY_SECONDS)
                disposition = {
                    "intent_disposition": "snoozed_retryable",
                    "intent_key": key,
                    "idempotency_key": key,
                    "symbol": symbol,
                    "side": side,
                    "reason": "paper_session_limit_blocked",
                    "retry_after_kst": retry_after.isoformat(),
                    "broker_endpoint_called": False,
                }
                _mark_runner_state_snoozed(local_state, current_intent, disposition, now=reference_now)
                _write_runner_state(local_state, config, data_root=data_root)
                result["intent_processing_summary"]["intents_snoozed_this_tick"] += 1
                disposition_step.update(disposition)
            else:
                claim = _acquire_intent_claim(key, data_root=data_root, now=now)
                result["steps"].append(claim)
                if claim["status"] != "pass":
                    result["steps"].append(
                        {
                            "step": "cash_order",
                            "status": "blocked_intent_claim",
                            "broker_endpoint_called": False,
                            "reason": claim.get("reason"),
                        }
                    )
                    retry_after = reference_now + timedelta(seconds=RUNNER_SNOOZE_RETRY_SECONDS)
                    disposition = {
                        "intent_disposition": "blocked_duplicate_active_exit",
                        "intent_key": key,
                        "idempotency_key": key,
                        "symbol": symbol,
                        "side": side,
                        "reason": claim.get("reason") or "intent_claim_already_exists",
                        "retry_after_kst": retry_after.isoformat(),
                        "broker_endpoint_called": False,
                    }
                    _mark_runner_state_snoozed(local_state, current_intent, disposition, now=reference_now)
                    _write_runner_state(local_state, config, data_root=data_root)
                    result["intent_processing_summary"]["intents_snoozed_this_tick"] += 1
                    disposition_step.update(disposition)
                else:
                    _mark_runner_state_submitting(local_state, current_intent, now=now)
                    _write_runner_state(local_state, config, data_root=data_root)
                    try:
                        cash_order = adapter.placeCashOrder(token, current_intent)
                    except Exception as exc:  # pragma: no cover - defensive network ambiguity boundary
                        cash_order = {
                            "step": "cash_order",
                            "status": "warn",
                            "broker_endpoint_called": "unknown",
                            "reason": "cash_order_exception_requires_reconciliation",
                            "error_type": type(exc).__name__,
                        }
                    result["steps"].append(cash_order)
                    if _broker_step_passed(cash_order):
                        markIntentConsumed(key)
                        _update_intent_claim_status(key, data_root=data_root, status="submitted", now=now)
                        _mark_runner_state_submitted(local_state, current_intent, cash_order, now=now)
                        _write_runner_state(local_state, config, data_root=data_root)
                        result["intent_processing_summary"]["intents_submitted_this_tick"] += 1
                        disposition_step.update(
                            {
                                "intent_disposition": "submitted",
                                "reason": "broker_order_submitted",
                                "broker_endpoint_called": True,
                                "broker_order_no": cash_order.get("broker_order_no") or "",
                            }
                        )
                    elif cash_order.get("broker_endpoint_called") is False:
                        _release_intent_claim(key, data_root=data_root)
                        _clear_runner_state_submitting(local_state, key, now=now)
                        retry_after = reference_now + timedelta(seconds=RUNNER_SNOOZE_RETRY_SECONDS)
                        disposition = {
                            "intent_disposition": "snoozed_retryable",
                            "intent_key": key,
                            "idempotency_key": key,
                            "symbol": symbol,
                            "side": side,
                            "reason": "cash_order_blocked_before_broker_endpoint",
                            "retry_after_kst": retry_after.isoformat(),
                            "broker_endpoint_called": False,
                        }
                        _mark_runner_state_snoozed(local_state, current_intent, disposition, now=reference_now)
                        _write_runner_state(local_state, config, data_root=data_root)
                        result["intent_processing_summary"]["intents_snoozed_this_tick"] += 1
                        result["steps"].append(
                            {
                                "step": "local_state",
                                "status": "not_marked_consumed",
                                "reason": "cash_order_blocked_before_broker_endpoint",
                                "broker_status": cash_order.get("status"),
                            }
                        )
                        disposition_step.update(disposition)
                    else:
                        _update_intent_claim_status(key, data_root=data_root, status="ambiguous", now=now)
                        _mark_runner_state_ambiguous(local_state, current_intent, cash_order, now=now)
                        _write_runner_state(local_state, config, data_root=data_root)
                        result["steps"].append(
                            {
                                "step": "local_state",
                                "status": "ambiguous_submit_requires_reconciliation",
                                "reason": "cash_order_not_passed_after_claim",
                                "broker_status": cash_order.get("status"),
                            }
                        )
                        disposition_step.update(
                            {
                                "intent_disposition": "snoozed_retryable",
                                "reason": "cash_order_ambiguous_requires_reconciliation",
                                "broker_endpoint_called": cash_order.get("broker_endpoint_called"),
                            }
                        )
        result["intent_processing_summary"]["intents_seen_this_tick"] += 1
        result["intent_dispositions"].append(dict(disposition_step))
        result["steps"].append(disposition_step)
        if explicit_intent or side != "sell" or processed_count >= max_intents:
            break
        loaded = _load_next_intent_from_queue(
            data_root=data_root,
            at=reference_now,
            state=local_state,
            exit_only=True,
        )
        next_intent = loaded.get("intent")
        disposition_step["queue_continued"] = bool(next_intent)
        disposition_step["next_intent_loaded"] = bool(next_intent)
        result["intent_dispositions"][-1] = dict(disposition_step)
        current_intent = dict(next_intent) if isinstance(next_intent, Mapping) else None

    result["intent_processing_summary"]["intents_remaining"] = _count_available_queue_intents(
        data_root=data_root,
        at=reference_now,
        state=local_state,
        exit_only=True,
    )

    if token_cache_managed:
        result["steps"].append(tokenCacheRevokeSkippedStep())
    else:
        result["steps"].append(adapter.revokeToken(token))
    step_statuses = {str(step.get("status") or "") for step in result["steps"]}
    if "fail" in step_statuses:
        result["status"] = "fail"
    elif (
        "warn" in step_statuses
        or "not_marked_consumed" in step_statuses
        or "ambiguous_submit_requires_reconciliation" in step_statuses
        or "blocked_intent_claim" in step_statuses
        or "blocked_market_session_gate" in step_statuses
        or "blocked_paper_order_disabled" in step_statuses
    ):
        result["status"] = "warn"
    else:
        result["status"] = "ok"
    return result


def writeContinuousPaperEvidence(
    payload: Mapping[str, Any],
    *,
    data_root: Optional[Path] = None,
    at: Optional[datetime] = None,
) -> Dict[str, str]:
    now = at or _now_kst()
    root = data_root or DEFAULT_DATA_ROOT
    evidence_dir = root / "evidence" / now.date().isoformat()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    latest = evidence_dir / "kis-paper-continuous-latest.json"
    stamped = evidence_dir / f"kis-paper-continuous-{now.strftime('%H%M%S')}.json"
    text = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    latest.write_text(text, encoding="utf-8")
    stamped.write_text(text, encoding="utf-8")
    return {"latest_path": str(latest), "stamped_path": str(stamped)}


def _load_intent_file(path: str) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8").strip()
    if not text:
        return None
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, Mapping):
            return dict(parsed)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, Mapping):
        return dict(parsed)
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, Mapping):
                return dict(item)
    return None


def _load_next_intent_from_queue(
    *,
    data_root: Path,
    at: datetime,
    state: Mapping[str, Any],
    exit_only: bool = False,
) -> Dict[str, Any]:
    path = data_root / "intents" / at.date().isoformat() / "paper-order-intents-latest.jsonl"
    if not path.is_file():
        return {"intent": None, "source": "next_intent_queue_missing", "path": str(path)}
    consumed = {
        str(item or "").strip()
        for item in (state.get("consumed_intent_keys") or [])
        if str(item or "").strip()
    }
    locked = {
        str(item or "").strip()
        for item in [
            *(state.get("submitting_intent_keys") or []),
            *(state.get("ambiguous_intent_keys") or []),
            *(state.get("claim_intent_keys") or []),
        ]
        if str(item or "").strip()
    }
    quarantined = {
        str(item or "").strip()
        for item in (state.get("quarantined_intent_keys") or [])
        if str(item or "").strip()
    }
    snoozed_until_by_key: dict[str, datetime] = {}
    for item in state.get("snoozed_intents") or []:
        if not isinstance(item, Mapping):
            continue
        key = str(item.get("idempotency_key") or item.get("intent_id") or "").strip()
        retry_after = _parse_optional_kst_timestamp(item.get("retry_after_kst"))
        if key and retry_after and retry_after > at:
            snoozed_until_by_key[key] = retry_after
    rows: list[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, Mapping):
            rows.append(dict(parsed))
    prioritized_rows = sorted(enumerate(rows), key=lambda item: (_intent_priority_rank(item[1]), item[0]))
    for _, row in prioritized_rows:
        if exit_only and _intent_priority_rank(row) != 0:
            continue
        key = str(row.get("idempotency_key") or row.get("intent_id") or "").strip()
        if key and key in consumed:
            continue
        if key and key in locked:
            continue
        if key and key in quarantined:
            continue
        if key and key in snoozed_until_by_key:
            continue
        expiry = _parse_optional_kst_timestamp(row.get("valid_until_kst") or row.get("valid_until"))
        if expiry and expiry <= at:
            continue
        return {"intent": row, "source": "next_intent_queue_exit_priority_fifo", "path": str(path)}
    return {"intent": None, "source": "next_intent_queue_empty_or_expired", "path": str(path)}


def _count_available_queue_intents(
    *,
    data_root: Path,
    at: datetime,
    state: Mapping[str, Any],
    exit_only: bool = False,
) -> int:
    path = data_root / "intents" / at.date().isoformat() / "paper-order-intents-latest.jsonl"
    if not path.is_file():
        return 0
    consumed = {
        str(item or "").strip()
        for item in (state.get("consumed_intent_keys") or [])
        if str(item or "").strip()
    }
    locked = {
        str(item or "").strip()
        for item in [
            *(state.get("submitting_intent_keys") or []),
            *(state.get("ambiguous_intent_keys") or []),
            *(state.get("claim_intent_keys") or []),
        ]
        if str(item or "").strip()
    }
    quarantined = {
        str(item or "").strip()
        for item in (state.get("quarantined_intent_keys") or [])
        if str(item or "").strip()
    }
    snoozed = set()
    for item in state.get("snoozed_intents") or []:
        if not isinstance(item, Mapping):
            continue
        key = str(item.get("idempotency_key") or item.get("intent_key") or "").strip()
        retry_after = _parse_optional_kst_timestamp(item.get("retry_after_kst"))
        if key and retry_after and retry_after > at:
            snoozed.add(key)
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, Mapping):
            continue
        row = dict(parsed)
        if exit_only and _intent_priority_rank(row) != 0:
            continue
        key = str(row.get("idempotency_key") or row.get("intent_id") or "").strip()
        if key and key in consumed.union(locked, quarantined, snoozed):
            continue
        expiry = _parse_optional_kst_timestamp(row.get("valid_until_kst") or row.get("valid_until"))
        if expiry and expiry <= at:
            continue
        count += 1
    return count


def _intent_priority_rank(row: Mapping[str, Any]) -> int:
    side = str(row.get("side") or "").strip().lower()
    action = str(row.get("action") or row.get("intent_action") or "").strip().upper()
    intent_type = str(row.get("intent_type") or row.get("type") or "").strip().lower()
    if side == "sell" or action == "SELL" or "exit" in intent_type:
        return 0
    return 1


def _runner_state_path(config: Mapping[str, Any], *, data_root: Path) -> Path:
    override = str(config.get("state_file") or "").strip()
    if override:
        path = Path(override)
        return path if path.is_absolute() else data_root / override
    return data_root / "state" / "kis-paper-runner-state.json"


def _load_runner_state(config: Mapping[str, Any], *, data_root: Path) -> Dict[str, Any]:
    path = _runner_state_path(config, data_root=data_root)
    if not path.is_file():
        state = {
            "schema_version": "kis_paper_runner_state/v0",
            "consumed_intent_keys": [],
            "consumed_trade_document_ids": [],
            "submitting_intent_keys": [],
            "ambiguous_intent_keys": [],
            "ambiguous_submits": [],
            "quarantined_intent_keys": [],
            "quarantined_intents": [],
            "snoozed_intents": [],
            "pending_orders": [],
            "holdings": [],
            "active_exits": [],
            "submitted_order_history": [],
            "last_updated_kst": None,
        }
        state["claim_intent_keys"] = sorted(_claim_keys_from_dir(data_root=data_root))
        return state
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        parsed = {}
    state = dict(parsed) if isinstance(parsed, Mapping) else {}
    state.setdefault("schema_version", "kis_paper_runner_state/v0")
    state.setdefault("consumed_intent_keys", [])
    state.setdefault("consumed_trade_document_ids", [])
    state.setdefault("submitting_intent_keys", [])
    state.setdefault("ambiguous_intent_keys", [])
    state.setdefault("ambiguous_submits", [])
    state.setdefault("quarantined_intent_keys", [])
    state.setdefault("quarantined_intents", [])
    state.setdefault("snoozed_intents", [])
    state.setdefault("pending_orders", [])
    state.setdefault("holdings", [])
    state.setdefault("active_exits", [])
    state.setdefault("submitted_order_history", [])
    for key in (
        "consumed_intent_keys",
        "consumed_trade_document_ids",
        "submitting_intent_keys",
        "ambiguous_intent_keys",
        "ambiguous_submits",
        "quarantined_intent_keys",
        "quarantined_intents",
        "snoozed_intents",
        "pending_orders",
        "holdings",
        "active_exits",
        "submitted_order_history",
    ):
        if not isinstance(state.get(key), list):
            state[key] = []
    state["claim_intent_keys"] = sorted(_claim_keys_from_dir(data_root=data_root))
    return state


def _write_runner_state(state: Mapping[str, Any], config: Mapping[str, Any], *, data_root: Path) -> None:
    path = _runner_state_path(config, data_root=data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(state), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _claim_dir(data_root: Path) -> Path:
    return data_root / "state" / "kis-paper-runner-claims"


def _claim_path(key: str, *, data_root: Path) -> Path:
    digest = hashlib.sha256(str(key).encode("utf-8")).hexdigest()
    return _claim_dir(data_root) / f"{digest}.json"


def _claim_keys_from_dir(*, data_root: Path) -> set[str]:
    root = _claim_dir(data_root)
    if not root.is_dir():
        return set()
    keys: set[str] = set()
    for path in root.glob("*.json"):
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(parsed, Mapping):
            key = str(parsed.get("idempotency_key") or "").strip()
            if key:
                keys.add(key)
    return keys


def _acquire_intent_claim(key: str, *, data_root: Path, now: datetime) -> Dict[str, Any]:
    idempotency_key = str(key or "").strip()
    if not idempotency_key:
        return {
            "step": "intent_claim",
            "status": "blocked",
            "reason": "idempotency_key_required",
            "broker_endpoint_called": False,
        }
    root = _claim_dir(data_root)
    root.mkdir(parents=True, exist_ok=True)
    path = _claim_path(idempotency_key, data_root=data_root)
    payload = {
        "schema_version": "kis_paper_intent_claim/v0",
        "idempotency_key": idempotency_key,
        "claimed_at_kst": now.isoformat(),
        "status": "submitting",
        "requires_reconciliation_before_retry": True,
    }
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return {
            "step": "intent_claim",
            "status": "blocked",
            "reason": "intent_claim_already_exists",
            "idempotency_key": idempotency_key,
            "broker_endpoint_called": False,
        }
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return {
        "step": "intent_claim",
        "status": "pass",
        "idempotency_key": idempotency_key,
        "claim_path": str(path),
        "broker_endpoint_called": False,
    }


def _release_intent_claim(key: str, *, data_root: Path) -> None:
    idempotency_key = str(key or "").strip()
    if not idempotency_key:
        return
    path = _claim_path(idempotency_key, data_root=data_root)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _update_intent_claim_status(key: str, *, data_root: Path, status: str, now: datetime) -> None:
    idempotency_key = str(key or "").strip()
    if not idempotency_key:
        return
    path = _claim_path(idempotency_key, data_root=data_root)
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        parsed = {}
    payload = dict(parsed) if isinstance(parsed, Mapping) else {}
    payload.update(
        {
            "schema_version": "kis_paper_intent_claim/v0",
            "idempotency_key": idempotency_key,
            "status": status,
            "updated_at_kst": now.isoformat(),
            "requires_reconciliation_before_retry": status != "submitted",
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _order_state_snapshot_from_runner_state(state: Mapping[str, Any], *, now: datetime) -> Dict[str, Any]:
    return {
        "schema_version": "order_state_snapshot/v0",
        "artifact_id": f"art_order_state_runner_{now.strftime('%Y%m%d_%H%M%S')}",
        "snapshot_id": f"order_state_runner_{now.strftime('%Y%m%d_%H%M%S')}",
        "produced_at_kst": now.isoformat(),
        "pending_orders": [
            dict(row)
            for row in (state.get("pending_orders") or [])
            if isinstance(row, Mapping)
        ],
        "holdings": [
            dict(row)
            for row in (state.get("holdings") or [])
            if isinstance(row, Mapping)
        ],
        "active_exits": [
            dict(row)
            for row in (state.get("active_exits") or [])
            if isinstance(row, Mapping)
        ],
        "cooldowns": [],
        "consumed_trade_document_ids": [],
        "legacy_consumed_trade_document_ids": [
            str(item)
            for item in (state.get("consumed_trade_document_ids") or [])
            if str(item).strip()
        ],
        "legacy_consumed_trade_document_ids_ignored_for_sibling_intents": bool(state.get("consumed_trade_document_ids") or []),
        "consumed_intent_keys": [
            str(item)
            for item in (state.get("consumed_intent_keys") or [])
            if str(item).strip()
        ],
        "submitting_intent_keys": [
            str(item)
            for item in (state.get("submitting_intent_keys") or [])
            if str(item).strip()
        ],
        "claim_intent_keys": [
            str(item)
            for item in (state.get("claim_intent_keys") or [])
            if str(item).strip()
        ],
        "ambiguous_intent_keys": [
            str(item)
            for item in (state.get("ambiguous_intent_keys") or [])
            if str(item).strip()
        ],
        "quarantined_intent_keys": [
            str(item)
            for item in (state.get("quarantined_intent_keys") or [])
            if str(item).strip()
        ],
        "snoozed_intents": [
            dict(row)
            for row in (state.get("snoozed_intents") or [])
            if isinstance(row, Mapping)
        ],
    }


def _mark_runner_state_submitting(
    state: Dict[str, Any],
    intent: Mapping[str, Any],
    *,
    now: datetime,
) -> None:
    key = str(intent.get("idempotency_key") or intent.get("intent_id") or "").strip()
    if key:
        state["submitting_intent_keys"] = sorted(set([*(state.get("submitting_intent_keys") or []), key]))
    state["last_updated_kst"] = now.isoformat()


def _clear_runner_state_submitting(state: Dict[str, Any], key: str, *, now: datetime) -> None:
    idempotency_key = str(key or "").strip()
    state["submitting_intent_keys"] = [
        str(item)
        for item in (state.get("submitting_intent_keys") or [])
        if str(item).strip() and str(item).strip() != idempotency_key
    ]
    state["last_updated_kst"] = now.isoformat()


def _mark_runner_state_ambiguous(
    state: Dict[str, Any],
    intent: Mapping[str, Any],
    cash_order: Mapping[str, Any],
    *,
    now: datetime,
) -> None:
    key = str(intent.get("idempotency_key") or intent.get("intent_id") or "").strip()
    symbol = str(intent.get("symbol") or intent.get("ticker") or "").strip()
    _clear_runner_state_submitting(state, key, now=now)
    if key:
        state["ambiguous_intent_keys"] = sorted(set([*(state.get("ambiguous_intent_keys") or []), key]))
        ambiguous_rows = [
            dict(row)
            for row in (state.get("ambiguous_submits") or [])
            if isinstance(row, Mapping) and str(row.get("idempotency_key") or "").strip() != key
        ]
        ambiguous_rows.append(
            {
                "idempotency_key": key,
                "symbol": symbol,
                "broker_status": cash_order.get("status"),
                "broker_endpoint_called": cash_order.get("broker_endpoint_called"),
                "recorded_at_kst": now.isoformat(),
                "requires_reconciliation_before_retry": True,
            }
        )
        state["ambiguous_submits"] = ambiguous_rows
    state["last_updated_kst"] = now.isoformat()


def _mark_runner_state_submitted(
    state: Dict[str, Any],
    intent: Mapping[str, Any],
    cash_order: Mapping[str, Any],
    *,
    now: datetime,
) -> None:
    key = str(intent.get("idempotency_key") or intent.get("intent_id") or "").strip()
    doc_ref = str(intent.get("flash_trade_document_ref") or "").strip()
    symbol = str(intent.get("symbol") or intent.get("ticker") or "").strip()
    if key:
        state["consumed_intent_keys"] = sorted(set([*(state.get("consumed_intent_keys") or []), key]))
        state["submitting_intent_keys"] = [
            str(item)
            for item in (state.get("submitting_intent_keys") or [])
            if str(item).strip() and str(item).strip() != key
        ]
        state["ambiguous_intent_keys"] = [
            str(item)
            for item in (state.get("ambiguous_intent_keys") or [])
            if str(item).strip() and str(item).strip() != key
        ]
        state["ambiguous_submits"] = [
            dict(row)
            for row in (state.get("ambiguous_submits") or [])
            if isinstance(row, Mapping) and str(row.get("idempotency_key") or "").strip() != key
        ]
    pending = [
        dict(row)
        for row in (state.get("pending_orders") or [])
        if isinstance(row, Mapping) and str(row.get("symbol") or row.get("ticker") or "").strip() != symbol
    ]
    pending.append(
        {
            "symbol": symbol,
            "ticker": symbol,
            "side": str(intent.get("side") or ""),
            "action": intent.get("action") or "",
            "intent_type": intent.get("intent_type") or "",
            "action_source": intent.get("action_source") or "",
            "quantity": intent.get("quantity"),
            "order_price": intent.get("order_price") or intent.get("price"),
            "entry_price_limit": intent.get("entry_price_limit") or intent.get("order_price") or intent.get("price"),
            "raw_order_price": intent.get("raw_order_price"),
            "target_price": intent.get("target_price") or intent.get("take_profit"),
            "stop_loss_price": intent.get("stop_loss_price") or intent.get("stop_loss"),
            "take_profit": intent.get("take_profit") or intent.get("target_price"),
            "stop_loss": intent.get("stop_loss") or intent.get("stop_loss_price"),
            "trailing_stop_pct": intent.get("trailing_stop_pct"),
            "notional_krw": estimateIntentNotionalKrw(intent),
            "idempotency_key": key,
            "flash_trade_document_ref": doc_ref,
            "submitted_at_kst": now.isoformat(),
            "broker_status": cash_order.get("status"),
            "broker_endpoint_called": bool(cash_order.get("broker_endpoint_called")),
            "broker_order_no": cash_order.get("broker_order_no") or "",
            "broker_order_no_present": bool(cash_order.get("broker_order_no")),
            "krx_forwarding_order_orgno": cash_order.get("krx_forwarding_order_orgno") or "",
        }
    )
    state["pending_orders"] = pending
    history = [
        dict(row)
        for row in (state.get("submitted_order_history") or [])
        if isinstance(row, Mapping) and str(row.get("idempotency_key") or "").strip() != key
    ]
    history.append(dict(pending[-1]))
    state["submitted_order_history"] = history[-500:]
    state["last_updated_kst"] = now.isoformat()


def _intent_key(intent: Mapping[str, Any]) -> str:
    return str(intent.get("idempotency_key") or intent.get("intent_id") or "").strip()


def _intent_symbol(intent: Mapping[str, Any]) -> str:
    return str(intent.get("symbol") or intent.get("ticker") or "").strip()


def _intent_side(intent: Mapping[str, Any]) -> str:
    return str(intent.get("side") or "buy").strip().lower()


def _account_truth_has_position(account_truth: Mapping[str, Any], symbol: str) -> bool:
    expected = str(symbol or "").strip()
    if not expected:
        return False
    for row in account_truth.get("positions") or []:
        if isinstance(row, Mapping) and _symbol_matches(row, expected) and _positive_quantity_from_row(row) > 0:
            return True
    return False


def _classify_preflight_disposition(
    intent: Mapping[str, Any],
    preflight: Mapping[str, Any],
    *,
    account_truth: Mapping[str, Any],
    now: datetime,
) -> Dict[str, Any]:
    errors = {str(item) for item in (preflight.get("errors") or []) if str(item)}
    side = _intent_side(intent)
    symbol = _intent_symbol(intent)
    key = _intent_key(intent)
    base: Dict[str, Any] = {
        "intent_key": key,
        "idempotency_key": key,
        "symbol": symbol,
        "side": side,
        "broker_endpoint_called": False,
    }
    if not errors:
        return {**base, "intent_disposition": "eligible"}
    if "intent_expired" in errors:
        return {**base, "intent_disposition": "expired", "reason": "intent_expired"}
    if errors.intersection(
        {
            "intent_schema_invalid",
            "paper_only_guard_failed",
            "broker_adapter_not_allowed_for_paper_order",
            "kis_paper_order_route_must_be_krx",
            "symbol_required",
            "idempotency_key_required",
            "sell_quantity_must_be_positive",
            "valid_until_kst_must_be_after_created_at_kst",
            "sell_intent_zero_ttl",
            "sell_intent_ttl_shorter_than_runner_pickup_window",
        }
    ):
        return {**base, "intent_disposition": "invalid_payload", "reason": sorted(errors)[0]}
    if side == "sell" and errors.intersection(
        {
            "active_exit_order_exists",
            "active_sell_order_exists",
            "pending_order_exists",
            "ambiguous_submit_requires_reconciliation",
            "intent_submit_claim_in_progress",
        }
    ):
        retry_after = now + timedelta(seconds=RUNNER_SNOOZE_RETRY_SECONDS)
        reason = "active_sell_order_exists" if "active_sell_order_exists" in errors else sorted(errors)[0]
        return {
            **base,
            "intent_disposition": "blocked_duplicate_active_exit",
            "reason": reason,
            "retry_after_kst": retry_after.isoformat(),
        }
    if side == "sell" and "sellable_truth_not_accepted" in errors:
        balance_ok = account_truth.get("balance_status") == "pass"
        symbol_in_positions = _account_truth_has_position(account_truth, symbol)
        normalized_sellable_quantity = _coerce_nonnegative_int(account_truth.get("normalized_sellable_quantity"), 0)
        truth_status = str(account_truth.get("sellable_truth_status") or "").strip()
        if balance_ok and not symbol_in_positions:
            return {
                **base,
                "intent_disposition": "quarantined_terminal",
                "reason": "no_holding_for_sell_symbol",
                "sellable_truth_status": truth_status or None,
                "sellable_quantity": normalized_sellable_quantity,
            }
        if balance_ok and normalized_sellable_quantity <= 0 and truth_status in {"provider_unsupported_no_fallback", "unknown", "blocked"}:
            return {
                **base,
                "intent_disposition": "quarantined_terminal",
                "reason": "sellable_quantity_zero_no_position",
                "sellable_truth_status": truth_status or None,
                "sellable_quantity": normalized_sellable_quantity,
            }
        retry_after = now + timedelta(seconds=RUNNER_SNOOZE_RETRY_SECONDS)
        return {
            **base,
            "intent_disposition": "snoozed_retryable",
            "reason": "sellable_truth_retryable",
            "retry_after_kst": retry_after.isoformat(),
            "sellable_truth_status": truth_status or None,
        }
    if errors.intersection({"account_truth_required_for_order", "balance_truth_not_pass", "buyable_cash_truth_not_pass"}):
        retry_after = now + timedelta(seconds=RUNNER_SNOOZE_RETRY_SECONDS)
        return {
            **base,
            "intent_disposition": "snoozed_retryable",
            "reason": sorted(errors)[0],
            "retry_after_kst": retry_after.isoformat(),
        }
    return {**base, "intent_disposition": "invalid_payload", "reason": sorted(errors)[0]}


def _mark_runner_state_quarantined(
    state: Dict[str, Any],
    intent: Mapping[str, Any],
    disposition: Mapping[str, Any],
    *,
    now: datetime,
) -> None:
    key = _intent_key(intent)
    if not key:
        return
    existing = [
        dict(row)
        for row in (state.get("quarantined_intents") or [])
        if isinstance(row, Mapping) and str(row.get("idempotency_key") or row.get("intent_key") or "").strip() != key
    ]
    row = {
        "idempotency_key": key,
        "intent_key": key,
        "intent_id": intent.get("intent_id"),
        "symbol": _intent_symbol(intent),
        "side": _intent_side(intent),
        "action": intent.get("action"),
        "disposition": disposition.get("intent_disposition"),
        "reason": disposition.get("reason"),
        "recorded_at_kst": now.isoformat(),
        "terminal": True,
    }
    existing.append(row)
    state["quarantined_intent_keys"] = sorted(set([*(state.get("quarantined_intent_keys") or []), key]))
    state["quarantined_intents"] = existing[-500:]
    state["last_updated_kst"] = now.isoformat()


def _mark_runner_state_snoozed(
    state: Dict[str, Any],
    intent: Mapping[str, Any],
    disposition: Mapping[str, Any],
    *,
    now: datetime,
) -> None:
    key = _intent_key(intent)
    if not key:
        return
    existing = [
        dict(row)
        for row in (state.get("snoozed_intents") or [])
        if isinstance(row, Mapping) and str(row.get("idempotency_key") or row.get("intent_key") or "").strip() != key
    ]
    existing.append(
        {
            "idempotency_key": key,
            "intent_key": key,
            "intent_id": intent.get("intent_id"),
            "symbol": _intent_symbol(intent),
            "side": _intent_side(intent),
            "action": intent.get("action"),
            "disposition": disposition.get("intent_disposition"),
            "reason": disposition.get("reason"),
            "retry_after_kst": disposition.get("retry_after_kst"),
            "recorded_at_kst": now.isoformat(),
        }
    )
    state["snoozed_intents"] = existing[-500:]
    state["last_updated_kst"] = now.isoformat()


def _broker_step_passed(step: Mapping[str, Any]) -> bool:
    return step.get("status") == "pass" and bool(step.get("broker_endpoint_called"))


def _parse_optional_kst_timestamp(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _status_reference_datetime(status: Optional[Mapping[str, Any]]) -> datetime:
    routing = (status or {}).get("routing") if isinstance(status, Mapping) else {}
    if isinstance(routing, Mapping):
        parsed = _parse_optional_kst_timestamp(routing.get("atKst"))
        if parsed:
            return parsed
    return _now_kst()


def _status_with_env_overrides(
    status: Mapping[str, Any],
    env: Mapping[str, str],
    *,
    at_kst: Optional[str],
) -> Dict[str, Any]:
    payload = json.loads(json.dumps(dict(status), ensure_ascii=False))
    market_source = str(env.get("HWISTOCK_MARKET_DATA_SOURCE") or "").strip()
    if market_source:
        payload["marketData"] = {
            "state": "source_configured",
            "source": market_source,
            "tradingLoopsActive": market_source in {"kis_paper_mock", *ORDER_GRADE_MARKET_DATA_SOURCES},
            "reason": "runner env market-data source override",
        }

    paper_order_requested = _bool_env(env, "HWISTOCK_KIS_PAPER_ORDER_ENABLED", False)
    if _bool_env(env, "HWISTOCK_ALLOW_WEEKDAY_CALENDAR_FALLBACK", False) and not paper_order_requested:
        calendar = payload.get("calendar") if isinstance(payload.get("calendar"), Mapping) else {}
        if calendar.get("tradingAllowed") is not True:
            ref = _parse_optional_kst_timestamp(at_kst) or _now_kst()
            payload["calendar"] = {
                **dict(calendar),
                "state": "calendar_weekday_fallback",
                "tradingAllowed": ref.weekday() < 5,
                "fallbackPolicy": "weekday_only_operator_enabled",
                "dateKst": ref.date().isoformat(),
            }
    elif _bool_env(env, "HWISTOCK_ALLOW_WEEKDAY_CALENDAR_FALLBACK", False) and paper_order_requested:
        calendar = payload.get("calendar") if isinstance(payload.get("calendar"), Mapping) else {}
        if calendar.get("tradingAllowed") is not True:
            ref = _parse_optional_kst_timestamp(at_kst) or _now_kst()
            payload["calendar"] = {
                **dict(calendar),
                "state": "calendar_weekday_fallback_forbidden_for_orders",
                "tradingAllowed": False,
                "fallbackPolicy": "weekday_fallback_disabled_for_order_path",
                "dateKst": ref.date().isoformat(),
            }

    kill_switch = bool((payload.get("killSwitch") or {}).get("active"))
    calendar_ready = (payload.get("calendar") or {}).get("tradingAllowed") is True
    source_ready = (payload.get("marketData") or {}).get("state") != "source_unconfigured"
    route = str((payload.get("routing") or {}).get("venue") or "idle")
    if kill_switch:
        payload["orderGate"] = "blocked_kill_switch"
    elif not calendar_ready:
        payload["orderGate"] = f"blocked_{(payload.get('calendar') or {}).get('state', 'calendar')}"
    elif not source_ready:
        payload["orderGate"] = "blocked_source_unconfigured"
    elif route == "idle":
        payload["orderGate"] = "blocked_off_session"
    else:
        payload["orderGate"] = "no_order_dry_run_only"
    return payload


def _sleepForKisCallGap(config: Mapping[str, Any]) -> None:
    gap = float(config.get("min_call_gap_sec") or 0)
    if gap > 0:
        time.sleep(gap)


def _symbol_set_from_snapshot(snapshot: Mapping[str, Any], key: str) -> set[str]:
    rows = snapshot.get(key)
    symbols: set[str] = set()
    if isinstance(rows, Mapping):
        iterable = rows.values()
    elif isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        iterable = rows
    else:
        iterable = []
    for row in iterable:
        if isinstance(row, Mapping):
            symbol = str(row.get("symbol") or row.get("ticker") or "").strip()
        else:
            symbol = str(row or "").strip()
        if symbol:
            symbols.add(symbol)
    return symbols


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="hwiStock continuous KIS paper runner")
    parser.add_argument("--once", action="store_true", help="Run one continuous-paper tick and exit")
    parser.add_argument("--write-evidence", action="store_true", help="Write sanitized tick evidence")
    parser.add_argument("--allow-paper-network", action="store_true", help="Enable KIS paper/mock network calls for this tick")
    parser.add_argument("--allow-paper-orders", action="store_true", help="Enable KIS paper/mock cash order submission for this tick")
    parser.add_argument("--intent-file", default=os.getenv("HWISTOCK_KIS_PAPER_INTENT_FILE", ""), help="Optional JSON/JSONL approved paper intent")
    parser.add_argument("--output-root", default=os.getenv("HWISTOCK_DATA_DIR", str(DEFAULT_DATA_ROOT)))
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.once:
        parser.print_help(sys.stderr)
        return 2
    env = dict(os.environ)
    if args.allow_paper_network:
        env["HWISTOCK_KIS_PAPER_NETWORK_ENABLED"] = "true"
    if args.allow_paper_orders:
        env["HWISTOCK_OPERATION_MODE"] = "paper_experiment"
        env["HWISTOCK_KIS_PAPER_ORDER_ENABLED"] = "true"
    env["HWISTOCK_DATA_DIR"] = str(args.output_root)
    intent = _load_intent_file(args.intent_file)
    payload = runContinuousPaperTick(intent=intent, env=env)
    if args.write_evidence:
        payload["evidencePaths"] = writeContinuousPaperEvidence(payload, data_root=Path(args.output_root))
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
