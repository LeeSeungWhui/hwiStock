"""
Market/session gate for KIS-facing runtime calls.

This module is intentionally side-effect free: it reads only the local cached
calendar file and environment-like mappings supplied by callers. Paper/mock
mode treats the local KRX calendar as the primary source of truth and never
requires the KIS holiday endpoint before deciding whether KIS transports are
expected.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

try:
    from lib import runtime_policy as rp
except ImportError:  # pragma: no cover
    from backend.lib import runtime_policy as rp

KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALENDAR_PATH = REPO_ROOT / "config" / "market-calendar" / "krx-nxt-trading-days.json"

ALWAYS_ALLOWED_CALL_FAMILIES = frozenset(
    {
        "calendar_refresh",
        "news_disclosure",
        "pro_hourly",
        "gpt_morning",
    }
)
MARKET_DATA_CALL_FAMILIES = frozenset({"kis_market_data", "kis_realtime"})
ACCOUNT_CONTEXT_CALL_FAMILIES = frozenset({"kis_account_truth", "kis_reconciliation"})
ORDER_CALL_FAMILIES = frozenset({"kis_order_submit"})


def parseKstDatetime(value: Optional[Any] = None) -> datetime:
    if value is None:
        return datetime.now(KST).replace(microsecond=0)
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value).strip()
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST).replace(microsecond=0)


def calendarPathFromEnv(env: Optional[Mapping[str, str]] = None) -> Path:
    source = env if env is not None else os.environ
    override = str(source.get("HWISTOCK_CALENDAR_PATH") or "").strip()
    if override:
        path = Path(override)
        return path if path.is_absolute() else REPO_ROOT / override
    return DEFAULT_CALENDAR_PATH


def _parse_calendar_time(value: Any, default_value: time) -> time:
    raw = str(value or "").strip()
    if not raw:
        return default_value
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    return default_value


def _calendar_day_rows(payload: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    for key in ("days", "tradingDays", "calendar"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            for day, row in value.items():
                if isinstance(row, Mapping):
                    rows[str(day)] = dict(row)
                elif isinstance(row, bool):
                    rows[str(day)] = {"isTradingDay": row}
        elif isinstance(value, list):
            for row in value:
                if isinstance(row, str):
                    rows[row] = {"isTradingDay": True}
                elif isinstance(row, Mapping):
                    day = str(row.get("dateKst") or row.get("date") or row.get("day") or "").strip()
                    if day:
                        rows[day] = dict(row)
    return rows


def _calendar_session_state(day_payload: Mapping[str, Any], at: datetime) -> Dict[str, Any]:
    local = at.astimezone(KST)
    current = local.time()
    krx_payload = day_payload.get("krx") if isinstance(day_payload.get("krx"), Mapping) else {}
    nxt_payload = day_payload.get("nxt") if isinstance(day_payload.get("nxt"), Mapping) else {}
    krx_open = _parse_calendar_time(
        day_payload.get("krxOpen") or day_payload.get("krx_open") or krx_payload.get("regularOpen"),
        time(9, 0),
    )
    krx_close = _parse_calendar_time(
        day_payload.get("krxClose") or day_payload.get("krx_close") or krx_payload.get("regularClose"),
        time(15, 30),
    )
    krx_order_open = _parse_calendar_time(
        day_payload.get("krxOrderOpen") or day_payload.get("krx_order_open") or krx_payload.get("orderOpen"),
        time(9, 0),
    )
    krx_order_close = _parse_calendar_time(
        day_payload.get("krxOrderClose") or day_payload.get("krx_order_close") or krx_payload.get("orderClose"),
        time(15, 0),
    )
    nxt_open = _parse_calendar_time(
        day_payload.get("nxtOpen") or day_payload.get("nxt_open") or nxt_payload.get("open"),
        time(8, 0),
    )
    nxt_close = _parse_calendar_time(
        day_payload.get("nxtClose") or day_payload.get("nxt_close") or nxt_payload.get("close"),
        time(20, 0),
    )
    nxt_enabled_for_day = bool(day_payload.get("nxtEnabled", day_payload.get("nxt_enabled", False)))
    return {
        "sessionOpen": (krx_open <= current < krx_close) or (nxt_enabled_for_day and nxt_open <= current < nxt_close),
        "krxSessionOpen": krx_open <= current < krx_close,
        "krxOrderSessionOpen": krx_order_open <= current < krx_order_close,
        "nxtSessionOpen": nxt_enabled_for_day and nxt_open <= current < nxt_close,
        "krxSession": {"open": krx_open.strftime("%H:%M"), "close": krx_close.strftime("%H:%M")},
        "krxOrderSession": {"open": krx_order_open.strftime("%H:%M"), "close": krx_order_close.strftime("%H:%M")},
        "nxtSession": {"open": nxt_open.strftime("%H:%M"), "close": nxt_close.strftime("%H:%M")},
    }


def evaluateCalendarState(
    now_kst: Optional[Any] = None,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    ref = parseKstDatetime(now_kst)
    date_key = ref.date().isoformat()
    path = calendarPathFromEnv(env)
    if not path.is_file():
        return {
            "state": "calendar_unconfigured",
            "path": str(path),
            "dateKst": date_key,
            "tradingAllowed": False,
            "isTradingDay": False,
            "sessionOpen": False,
            "krxOrderSessionOpen": False,
            "reason": "local calendar cache missing",
            "sourceHierarchy": "local KRX cached calendar required before KIS transport",
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "state": "calendar_unconfigured",
            "path": str(path),
            "dateKst": date_key,
            "tradingAllowed": False,
            "isTradingDay": False,
            "sessionOpen": False,
            "krxOrderSessionOpen": False,
            "reason": "calendar cache unreadable",
            "sourceHierarchy": "local KRX cached calendar required before KIS transport",
        }
    payload = payload if isinstance(payload, Mapping) else {}
    valid_until = str(payload.get("validUntil") or payload.get("valid_until") or "").strip()
    if valid_until:
        try:
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=KST)
            if ref > expiry.astimezone(KST):
                return {
                    "state": "calendar_stale",
                    "path": str(path),
                    "dateKst": date_key,
                    "tradingAllowed": False,
                    "isTradingDay": False,
                    "sessionOpen": False,
                    "krxOrderSessionOpen": False,
                    "validUntil": valid_until,
                    "reason": "calendar cache expired",
                    "sourceHierarchy": payload.get("sourceHierarchy") or "local KRX/NXT cached calendar",
                }
        except ValueError:
            return {
                "state": "calendar_stale",
                "path": str(path),
                "dateKst": date_key,
                "tradingAllowed": False,
                "isTradingDay": False,
                "sessionOpen": False,
                "krxOrderSessionOpen": False,
                "reason": "calendar validUntil unparsable",
                "sourceHierarchy": payload.get("sourceHierarchy") or "local KRX/NXT cached calendar",
            }

    day_payload = _calendar_day_rows(payload).get(date_key)
    if not isinstance(day_payload, Mapping):
        return {
            "state": "calendar_day_missing",
            "path": str(path),
            "dateKst": date_key,
            "tradingAllowed": False,
            "isTradingDay": False,
            "sessionOpen": False,
            "krxOrderSessionOpen": False,
            "validUntil": valid_until or None,
            "reason": "calendar has no row for requested KST date",
            "sourceHierarchy": payload.get("sourceHierarchy") or "local KRX/NXT cached calendar; date-specific row required",
        }

    is_trading_day = bool(
        day_payload.get("isTradingDay", day_payload.get("is_trading_day", day_payload.get("tradingAllowed", False)))
    )
    session_state = _calendar_session_state(day_payload, ref)
    if not is_trading_day:
        return {
            "state": "calendar_non_trading_day",
            "path": str(path),
            "dateKst": date_key,
            "tradingAllowed": False,
            "isTradingDay": False,
            "sessionOpen": False,
            "krxOrderSessionOpen": False,
            "validUntil": valid_until or None,
            "reason": day_payload.get("reason") or "requested KST date is not a trading day",
            "sourceAuthority": payload.get("sourceAuthority") or payload.get("source") or "local_cache",
            "sourceHierarchy": payload.get("sourceHierarchy") or "local KRX/NXT cached calendar",
            **session_state,
        }

    return {
        "state": "calendar_ready",
        "path": str(path),
        "dateKst": date_key,
        "tradingAllowed": True,
        "isTradingDay": True,
        "validUntil": valid_until or None,
        "reason": "calendar row ready",
        "sourceAuthority": payload.get("sourceAuthority") or payload.get("source") or "local_cache",
        "sourceHierarchy": payload.get("sourceHierarchy") or "local KRX/NXT cached calendar; KIS holiday lookup deferred",
        **session_state,
    }


def _context_reason(calendar: Mapping[str, Any], route: Mapping[str, Any], *, market_context_open: bool) -> str:
    state = str(calendar.get("state") or "")
    if state != "calendar_ready":
        return state or "calendar_unavailable"
    if calendar.get("isTradingDay") is not True:
        return "weekend_or_holiday"
    if not market_context_open:
        return "market_context_closed"
    if route.get("orderWindowOpen"):
        return "order_window_open"
    return "market_context_open_close_or_reconciliation_only"


def _evidence_status(*, allowed: bool, call_family: str, reason: str) -> str:
    if allowed:
        return "allowed"
    if reason.startswith("calendar_"):
        return f"safe_skip_{reason}"
    if reason in {"weekend_or_holiday", "market_context_closed"}:
        return f"safe_skip_{reason}"
    return f"blocked_{call_family}_{reason}"


def evaluateKisCallGate(
    now_kst: Optional[Any] = None,
    investment_mode: Optional[Any] = None,
    call_family: str = "kis_market_data",
    *,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    ref = parseKstDatetime(now_kst)
    policy = rp.runtimePolicyFromEnv(source)
    mode = rp.normalizeInvestmentMode(investment_mode or policy["investment_mode"])
    env_for_route = dict(source)
    env_for_route["HWISTOCK_INVESTMENT_MODE"] = mode
    route = rp.routeForExecutionAt(ref, env=env_for_route)
    calendar = evaluateCalendarState(ref, env=source)
    calendar_ready = calendar.get("state") == "calendar_ready" and calendar.get("isTradingDay") is True
    market_context_open = bool(calendar_ready and route.get("marketAnalysisContextOpen"))
    broker_order_open = bool(calendar_ready and route.get("orderWindowOpen") and calendar.get("krxOrderSessionOpen"))
    kis_realtime_expected = market_context_open
    reason = _context_reason(calendar, route, market_context_open=market_context_open)

    normalized_family = str(call_family or "").strip() or "unknown"
    if normalized_family in ALWAYS_ALLOWED_CALL_FAMILIES:
        allowed = True
    elif normalized_family in MARKET_DATA_CALL_FAMILIES:
        allowed = market_context_open
    elif normalized_family in ACCOUNT_CONTEXT_CALL_FAMILIES:
        allowed = market_context_open
    elif normalized_family in ORDER_CALL_FAMILIES:
        allowed = broker_order_open
        if calendar_ready and market_context_open and not broker_order_open:
            reason = "broker_order_window_closed"
    else:
        allowed = False
        reason = "unknown_call_family"

    if not calendar_ready and normalized_family not in ALWAYS_ALLOWED_CALL_FAMILIES:
        reason = str(calendar.get("state") or reason)
    elif normalized_family in MARKET_DATA_CALL_FAMILIES and calendar_ready and not market_context_open:
        reason = "market_context_closed"
    elif normalized_family in ACCOUNT_CONTEXT_CALL_FAMILIES and calendar_ready and not market_context_open:
        reason = "market_context_closed"

    calendar_context = {
        "schema_version": "calendar_context/v0",
        "date_kst": ref.date().isoformat(),
        "now_kst": ref.isoformat(),
        "investment_mode": mode,
        "call_family": normalized_family,
        "is_trading_day": bool(calendar.get("isTradingDay")),
        "calendar_source": calendar.get("sourceAuthority") or calendar.get("sourceHierarchy") or "local_cache",
        "calendar_status": calendar.get("state"),
        "calendar_reason": calendar.get("reason"),
        "market_context_open": market_context_open,
        "broker_order_open": broker_order_open,
        "calendar_session_open": bool(calendar.get("sessionOpen")),
        "calendar_krx_order_session_open": bool(calendar.get("krxOrderSessionOpen")),
        "route_session": route.get("session"),
        "route_venue": route.get("venue"),
        "kis_realtime_expected": kis_realtime_expected,
        "reason": reason,
        "nxt_enabled": bool(route.get("nxtEnabled")),
        "paper_order_window_kst": {"open": "09:00", "close": "15:00"},
        "paper_close_context_window_kst": {"open": "15:00", "close": "15:30"},
        "holiday_lookup_policy": (
            "paper_mock_uses_local_cached_krx_calendar_primary;"
            " CTCA0903R unsupported in paper/mock runtime"
        ),
    }
    evidence_payload = {
        "schema_version": "kis_call_gate_evidence/v0",
        "step": f"{normalized_family}_market_session_gate",
        "status": _evidence_status(allowed=allowed, call_family=normalized_family, reason=reason),
        "allowed": allowed,
        "reason": reason,
        "calendar_context": calendar_context,
        "calendar_path": calendar.get("path"),
        "broker_endpoint_called": False,
        "endpoint_called": False,
        "order_cancel_modify_called": False,
        "credential_values_printed": False,
        "raw_response_stored": False,
    }
    return {
        "schema_version": "kis_call_gate/v0",
        "allowed": allowed,
        "reason": reason,
        "call_family": normalized_family,
        "calendar": calendar,
        "routing": route,
        "calendar_context": calendar_context,
        "evidence_payload": evidence_payload,
    }


def evaluate_market_session(
    now_kst: Optional[Any] = None,
    *,
    investment_mode: Optional[Any] = None,
    call_family: str = "kis_market_data",
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    return evaluateKisCallGate(
        now_kst=now_kst,
        investment_mode=investment_mode,
        call_family=call_family,
        env=env,
    )
