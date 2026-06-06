"""
hwiStock runtime mode, feed, schedule, and exposure policy.

This module is intentionally stdlib-only and side-effect free. It centralizes
the paper/mock experiment defaults so runner, market-data, AI, and tests do not
carry conflicting copies of the same trading windows or feed authority rules.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import Any, Dict, Mapping, Optional

KST = timezone(timedelta(hours=9))

PAPER_INVESTMENT_MODE = "paper"
LIVE_INVESTMENT_MODE = "live"

OPERATION_MODE_PAPER_EXPERIMENT = "paper_experiment"
OPERATION_MODE_LIVE_PRODUCTION = "live_production"

MARKET_ANALYSIS_FEED_INTEGRATED = "integrated"
EXECUTION_VENUE_KRX_ONLY = "krx_only"
EXECUTION_VENUE_KRX_NXT = "krx_nxt"

PAPER_ORDER_OPEN = time(9, 0)
PAPER_ORDER_CLOSE = time(15, 0)
PAPER_MARKET_CONTEXT_CLOSE = time(15, 30)
PAPER_FIRST_FLASH_BUCKET = time(9, 0)

LIVE_ORDER_OPEN = time(8, 0)
LIVE_ORDER_CLOSE = time(20, 0)
LIVE_FIRST_FLASH_BUCKET = time(8, 0)

GPT_MORNING_WATCHLIST_START = time(7, 15)
MAX_SIMULTANEOUS_HOLDINGS = 5
MAX_CASH_DEPLOYMENT_RATIO = 0.75
DEFAULT_RISK_OVERLAY_CAPITAL_KRW = 2_000_000


def normalizeInvestmentMode(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"live", "real", "real_investment", "prod", "production", "cash"}:
        return LIVE_INVESTMENT_MODE
    return PAPER_INVESTMENT_MODE


def normalizeMarketAnalysisFeedMode(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"integrated", "통합", "kis_integrated", "kis_integrated_realtime"}:
        return MARKET_ANALYSIS_FEED_INTEGRATED
    return MARKET_ANALYSIS_FEED_INTEGRATED


def normalizeExecutionVenueMode(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"krx_nxt", "nxt", "integrated_execution"}:
        return EXECUTION_VENUE_KRX_NXT
    return EXECUTION_VENUE_KRX_ONLY


def envBool(env: Mapping[str, str], key: str, default: bool = False) -> bool:
    raw = str(env.get(key, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def nxtRoutingEnabled(env: Optional[Mapping[str, str]] = None) -> bool:
    source = env or {}
    return (
        envBool(source, "HWISTOCK_NXT_ENABLED", False)
        and envBool(source, "HWISTOCK_NXT_READY_SET_APPROVED", False)
    )


def runtimePolicyFromEnv(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    source = env or {}
    investment_mode = normalizeInvestmentMode(
        source.get("HWISTOCK_INVESTMENT_MODE")
        or source.get("HWISTOCK_KIS_INVESTMENT_MODE")
        or source.get("HWISTOCK_TRADING_MODE")
        or PAPER_INVESTMENT_MODE
    )
    market_analysis_feed_mode = normalizeMarketAnalysisFeedMode(
        source.get("HWISTOCK_MARKET_ANALYSIS_FEED_MODE")
        or source.get("HWISTOCK_KIS_MARKET_ANALYSIS_FEED_MODE")
        or MARKET_ANALYSIS_FEED_INTEGRATED
    )
    execution_venue_mode = normalizeExecutionVenueMode(
        source.get("HWISTOCK_EXECUTION_VENUE_MODE")
        or source.get("HWISTOCK_KIS_EXECUTION_VENUE_MODE")
        or EXECUTION_VENUE_KRX_ONLY
    )
    nxt_enabled = (
        investment_mode == LIVE_INVESTMENT_MODE
        and execution_venue_mode == EXECUTION_VENUE_KRX_NXT
        and nxtRoutingEnabled(source)
    )
    return {
        "schema_version": "hwistock_runtime_policy/v0",
        "investment_mode": investment_mode,
        "market_analysis_feed_mode": market_analysis_feed_mode,
        "execution_venue_mode": EXECUTION_VENUE_KRX_NXT if nxt_enabled else EXECUTION_VENUE_KRX_ONLY,
        "nxt_enabled": nxt_enabled,
        "analysis_authority": "KIS integrated realtime feeds",
        "execution_authority": "KIS KRX quote/session/order window",
        "paper_order_window_kst": {"open": "09:00", "close": "15:00"},
        "paper_market_context_window_kst": {"open": "09:00", "close": "15:30"},
        "gpt_morning_watchlist_start_kst": "07:15",
        "max_simultaneous_holdings": MAX_SIMULTANEOUS_HOLDINGS,
        "max_cash_deployment_ratio": MAX_CASH_DEPLOYMENT_RATIO,
        "risk_overlay_capital_krw": DEFAULT_RISK_OVERLAY_CAPITAL_KRW,
    }


def orderWindowForMode(mode: Any) -> tuple[time, time]:
    if normalizeInvestmentMode(mode) == LIVE_INVESTMENT_MODE:
        return LIVE_ORDER_OPEN, LIVE_ORDER_CLOSE
    return PAPER_ORDER_OPEN, PAPER_ORDER_CLOSE


def marketContextWindowForMode(mode: Any) -> tuple[time, time]:
    if normalizeInvestmentMode(mode) == LIVE_INVESTMENT_MODE:
        return LIVE_ORDER_OPEN, LIVE_ORDER_CLOSE
    return PAPER_ORDER_OPEN, PAPER_MARKET_CONTEXT_CLOSE


def firstFlashBucketForMode(mode: Any) -> time:
    if normalizeInvestmentMode(mode) == LIVE_INVESTMENT_MODE:
        return LIVE_FIRST_FLASH_BUCKET
    return PAPER_FIRST_FLASH_BUCKET


def isOrderWindowOpen(at: datetime, *, investment_mode: Any = PAPER_INVESTMENT_MODE) -> bool:
    local = at.astimezone(KST)
    start, end = orderWindowForMode(investment_mode)
    return start <= local.time() < end


def isMarketContextOpen(at: datetime, *, investment_mode: Any = PAPER_INVESTMENT_MODE) -> bool:
    local = at.astimezone(KST)
    start, end = marketContextWindowForMode(investment_mode)
    return start <= local.time() < end


def isFirstFlashBucket(at: datetime, *, investment_mode: Any = PAPER_INVESTMENT_MODE) -> bool:
    local = at.astimezone(KST)
    bucket_start = local.replace(
        minute=(local.minute // 10) * 10,
        second=0,
        microsecond=0,
    ).time()
    return bucket_start == firstFlashBucketForMode(investment_mode)


def routeForExecutionAt(
    at: datetime,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    policy = runtimePolicyFromEnv(env)
    local = at.astimezone(KST)
    order_open = isOrderWindowOpen(local, investment_mode=policy["investment_mode"])
    market_context_open = isMarketContextOpen(local, investment_mode=policy["investment_mode"])

    if order_open:
        venue = "KRX"
        session = "krx_regular_order"
    elif market_context_open:
        venue = "idle"
        session = "krx_close_context_only"
    else:
        venue = "idle"
        session = "off_hours"

    return {
        "atKst": local.isoformat(),
        "dateKst": local.date().isoformat(),
        "venue": venue,
        "session": session,
        "inTradingEnvelope": order_open,
        "orderWindowOpen": order_open,
        "marketAnalysisContextOpen": market_context_open,
        "marketAnalysisFeedMode": policy["market_analysis_feed_mode"],
        "executionVenueMode": policy["execution_venue_mode"],
        "nxtEnabled": policy["nxt_enabled"],
        "routingPolicy": (
            "analysis=integrated feed; execution=KRX-only; "
            "paper/mock order window 09:00-15:00 KST; "
            "15:00-15:30 close/context only; NXT disabled unless future approved"
        ),
    }


def proHourlyInputWindow(at: datetime) -> Dict[str, Any]:
    end = at.astimezone(KST).replace(microsecond=0)
    start = end - timedelta(hours=1)
    return {
        "start_kst": start.isoformat(),
        "end_kst": end.isoformat(),
        "window_seconds": 3600,
    }


def coerceKrw(value: Any) -> int:
    try:
        parsed = int(float(str(value).strip().replace(",", "")))
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


def evaluateDynamicExposureCap(
    *,
    current_position_value_krw: Any,
    pending_buy_notional_krw: Any,
    new_order_notional_krw: Any,
    effective_total_deposit_krw: Any,
    risk_overlay_capital_krw: int = DEFAULT_RISK_OVERLAY_CAPITAL_KRW,
) -> Dict[str, Any]:
    current_value = coerceKrw(current_position_value_krw)
    pending_buy = coerceKrw(pending_buy_notional_krw)
    new_order = coerceKrw(new_order_notional_krw)
    effective_total = coerceKrw(effective_total_deposit_krw)
    capped_base = min(effective_total, int(risk_overlay_capital_krw)) if effective_total > 0 else 0
    max_deployable = int(capped_base * MAX_CASH_DEPLOYMENT_RATIO)
    projected = current_value + pending_buy + new_order
    missing_truth = effective_total <= 0
    return {
        "ok": not missing_truth and projected <= max_deployable,
        "missing_account_truth": missing_truth,
        "current_position_value_krw": current_value,
        "pending_buy_notional_krw": pending_buy,
        "new_order_notional_krw": new_order,
        "effective_total_deposit_krw": effective_total,
        "risk_overlay_capital_krw": int(risk_overlay_capital_krw),
        "effective_exposure_base_krw": capped_base,
        "max_cash_deployment_ratio": MAX_CASH_DEPLOYMENT_RATIO,
        "max_deployable_notional_krw": max_deployable,
        "projected_deployed_notional_krw": projected,
    }
