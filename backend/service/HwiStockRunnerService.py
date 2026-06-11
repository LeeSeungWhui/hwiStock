"""
hwiStock home-server paper runner skeleton (UNIT-002).
Local-only, no-order, no broker/network calls.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

try:
    from lib import market_calendar_cache as mcal
    from lib import runtime_policy as rp
except ImportError:  # pragma: no cover - package-style imports
    from backend.lib import market_calendar_cache as mcal
    from backend.lib import runtime_policy as rp

KST = ZoneInfo("Asia/Seoul")
DEFAULT_BIND_HOST = "127.0.0.1"
_LOOPBACK_LITERALS = frozenset({"127.0.0.1", "localhost", "::1"})
PAPER_BUDGET_KRW = 10_000_000
LIVE_CAPITAL_BASELINE_KRW = 2_000_000

# AC-05 / QA-005: explicit local audit categories (metadata only; no log delivery).
_AUDIT_CATEGORY_SPECS: tuple[tuple[str, str, str], ...] = (
    ("signal", "Signal or candidate events before decision", "data/audit/signal"),
    ("decision", "Strategy or operator decisions", "data/audit/decision"),
    ("risk_reject", "Risk gate rejections", "data/audit/risk_reject"),
    ("dry_run_order_intent", "No-order dry-run order intents", "data/audit/dry_run_order_intent"),
    ("error", "Runtime and adapter errors", "data/audit/error"),
    ("calendar", "Market calendar state and transitions", "data/audit/calendar"),
    ("kill_switch", "Kill switch activation and enforcement", "data/audit/kill_switch"),
    ("system_lifecycle", "Service start, stop, and restart lifecycle", "data/audit/system_lifecycle"),
    ("system_status", "Health, readiness, and status evidence", "data/audit/system_status"),
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CALENDAR_PATH = mcal.DEFAULT_REPO_CALENDAR_PATH
_READY_CALENDAR_STATES = frozenset({"calendar_ready", "paper_autofilled"})


@dataclass
class RunnerRuntimeState:
    kill_switch_active: bool = False
    no_order_intents: List[Dict[str, Any]] = field(default_factory=list)


_runtime = RunnerRuntimeState()


def backendDir() -> Path:
    return Path(__file__).resolve().parents[1]


def normalizeLoopbackBindHost(host: Optional[str]) -> str:
    """
    Coerce bind values to loopback-only. Allows 127.0.0.1, localhost, and ::1.
    LAN, public, wildcard, and non-loopback hostnames resolve to 127.0.0.1.
    """
    raw = (host or "").strip()
    if not raw:
        return DEFAULT_BIND_HOST

    lowered = raw.lower()
    if lowered in _LOOPBACK_LITERALS:
        return raw if lowered != "localhost" else "localhost"

    if lowered in ("0.0.0.0", "*"):
        return DEFAULT_BIND_HOST

    try:
        addr = ipaddress.ip_address(raw)
        if addr.is_loopback:
            return str(addr)
        return DEFAULT_BIND_HOST
    except ValueError:
        pass

    return DEFAULT_BIND_HOST


def resolveBindHost(config_host: Optional[str] = None) -> str:
    """
    Local-only bind default. Env HWISTOCK_BIND_HOST overrides config when set.
    Rejects unsafe public/LAN bind values by coercing to loopback.
    """
    env_host = os.getenv("HWISTOCK_BIND_HOST", "").strip()
    if env_host:
        return normalizeLoopbackBindHost(env_host)
    if config_host and str(config_host).strip():
        return normalizeLoopbackBindHost(str(config_host).strip())
    return DEFAULT_BIND_HOST


def jsonText(value: Any, *, sortKeys: bool = False) -> str:
    encoder = json.JSONEncoder(ensure_ascii=False, indent=2, sort_keys=sortKeys)
    return encoder.encode(value)


def emitRunnerOnceStdout() -> Dict[str, Any]:
    """Local-only runner tick payload for --once (no broker/network/orders)."""
    return {
        "event": "runner_once",
        "timestamp": datetime.now(KST).isoformat(),
        "status": getRunnerStatus(),
        "auditLog": auditLogCategoriesMetadata(),
    }


def runtimeDateDir(output_root: Path, at: datetime) -> Path:
    return output_root / "evidence" / at.astimezone(KST).date().isoformat()


def writeRunnerEvidence(
    payload: Dict[str, Any],
    *,
    output_root: Optional[Path] = None,
    at: Optional[datetime] = None,
) -> Dict[str, str]:
    """Write latest and timestamped runner evidence without broker/order calls."""
    now = at or datetime.now(KST)
    root = output_root or Path(os.getenv("HWISTOCK_DATA_DIR", str(_REPO_ROOT / "data")))
    evidence_dir = runtimeDateDir(root, now)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%H%M%S")
    latest_path = evidence_dir / "runner-latest.json"
    stamped_path = evidence_dir / f"runner-{stamp}.json"
    text = jsonText(payload, sortKeys=True) + "\n"
    latest_path.write_text(text, encoding="utf-8")
    stamped_path.write_text(text, encoding="utf-8")
    return {
        "latest_path": str(latest_path),
        "stamped_path": str(stamped_path),
    }


def runOnceEntrypoint() -> int:
    payload = emitRunnerOnceStdout()
    sys.stdout.write(jsonText(payload) + "\n")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="hwiStock paper runner skeleton (UNIT-002)")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Emit local runner status/audit metadata to stdout and exit",
    )
    parser.add_argument(
        "--write-evidence",
        action="store_true",
        help="Also write latest/timestamped runner evidence under HWISTOCK_DATA_DIR.",
    )
    parser.add_argument(
        "--output-root",
        default=os.getenv("HWISTOCK_DATA_DIR", str(_REPO_ROOT / "data")),
        help="Runtime data root for --write-evidence.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.once:
        payload = emitRunnerOnceStdout()
        if args.write_evidence:
            payload["evidencePaths"] = writeRunnerEvidence(
                payload,
                output_root=Path(args.output_root),
            )
        sys.stdout.write(jsonText(payload, sortKeys=True) + "\n")
        return 0
    parser.print_help(sys.stderr)
    return 2


def parseKstTime(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now(KST)
    raw = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%H:%M"):
        try:
            parsed = datetime.strptime(raw, fmt)
            if fmt == "%H:%M":
                today = date.today()
                return datetime(today.year, today.month, today.day, parsed.hour, parsed.minute, tzinfo=KST)
            return parsed.replace(tzinfo=KST)
        except ValueError:
            continue
    raise ValueError(f"unsupported KST time format: {value}")


def routeVenueAtKst(at: datetime) -> Dict[str, Any]:
    """Execution route policy: integrated feed for analysis, KRX-only for paper orders."""
    return rp.routeForExecutionAt(at, env=os.environ)


def calendarPath() -> Path:
    return mcal.resolve_calendar_read_path(os.environ)


def parseCalendarTime(value: Any, defaultValue: time) -> time:
    raw = str(value or "").strip()
    if not raw:
        return defaultValue
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    return defaultValue


def calendarDayRows(payload: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return mcal.calendar_day_rows(payload)


def calendarSessionState(dayPayload: Mapping[str, Any], at: datetime) -> Dict[str, Any]:
    local = at.astimezone(KST)
    t = local.time()
    krxPayload = dayPayload.get("krx") if isinstance(dayPayload.get("krx"), Mapping) else {}
    nxtPayload = dayPayload.get("nxt") if isinstance(dayPayload.get("nxt"), Mapping) else {}
    krxOpen = parseCalendarTime(
        dayPayload.get("krxOpen") or dayPayload.get("krx_open") or krxPayload.get("regularOpen"),
        time(9, 0),
    )
    krxClose = parseCalendarTime(
        dayPayload.get("krxClose") or dayPayload.get("krx_close") or krxPayload.get("regularClose"),
        time(15, 30),
    )
    krxOrderOpen = parseCalendarTime(
        dayPayload.get("krxOrderOpen") or dayPayload.get("krx_order_open") or krxPayload.get("orderOpen"),
        time(9, 0),
    )
    krxOrderClose = parseCalendarTime(
        dayPayload.get("krxOrderClose") or dayPayload.get("krx_order_close") or krxPayload.get("orderClose"),
        time(15, 0),
    )
    nxtOpen = parseCalendarTime(
        dayPayload.get("nxtOpen") or dayPayload.get("nxt_open") or nxtPayload.get("open"),
        time(8, 0),
    )
    nxtClose = parseCalendarTime(
        dayPayload.get("nxtClose") or dayPayload.get("nxt_close") or nxtPayload.get("close"),
        time(20, 0),
    )
    krxSessionOpen = krxOpen <= t < krxClose
    krxOrderSessionOpen = krxOrderOpen <= t < krxOrderClose
    nxtSessionOpen = bool(dayPayload.get("nxtEnabled", dayPayload.get("nxt_enabled", False))) and nxtOpen <= t < nxtClose
    return {
        "sessionOpen": krxSessionOpen or nxtSessionOpen,
        "krxSessionOpen": krxSessionOpen,
        "krxOrderSessionOpen": krxOrderSessionOpen,
        "nxtSessionOpen": nxtSessionOpen,
        "krxSession": {"open": krxOpen.strftime("%H:%M"), "close": krxClose.strftime("%H:%M")},
        "krxOrderSession": {"open": krxOrderOpen.strftime("%H:%M"), "close": krxOrderClose.strftime("%H:%M")},
        "nxtSession": {"open": nxtOpen.strftime("%H:%M"), "close": nxtClose.strftime("%H:%M")},
    }


def evaluateCalendarState(now: Optional[datetime] = None) -> Dict[str, Any]:
    path = calendarPath()
    ref = (now or datetime.now(KST)).astimezone(KST)
    date_key = ref.date().isoformat()
    if not path.is_file():
        return {
            "state": "calendar_unconfigured",
            "path": str(path),
            "tradingAllowed": False,
            "dateKst": date_key,
            "isTradingDay": False,
            "sessionOpen": False,
            "krxOrderSessionOpen": False,
            "reason": "local calendar cache missing",
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "state": "calendar_unconfigured",
            "path": str(path),
            "tradingAllowed": False,
            "dateKst": date_key,
            "isTradingDay": False,
            "sessionOpen": False,
            "krxOrderSessionOpen": False,
            "reason": "calendar cache unreadable",
        }

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
                    "tradingAllowed": False,
                    "dateKst": date_key,
                    "isTradingDay": False,
                    "sessionOpen": False,
                    "krxOrderSessionOpen": False,
                    "validUntil": valid_until,
                    "reason": "calendar cache expired",
                }
        except ValueError:
            return {
                "state": "calendar_stale",
                "path": str(path),
                "tradingAllowed": False,
                "dateKst": date_key,
                "isTradingDay": False,
                "sessionOpen": False,
                "krxOrderSessionOpen": False,
                "reason": "calendar validUntil unparsable",
            }

    rows = calendarDayRows(payload if isinstance(payload, Mapping) else {})
    day_payload = rows.get(date_key)
    if not isinstance(day_payload, Mapping):
        return {
            "state": "calendar_day_missing",
            "path": str(path),
            "tradingAllowed": False,
            "dateKst": date_key,
            "isTradingDay": False,
            "sessionOpen": False,
            "krxOrderSessionOpen": False,
            "validUntil": valid_until or None,
            "reason": "calendar has no row for requested KST date",
            "sourceHierarchy": "local KRX/NXT cached calendar; date-specific row required",
        }

    is_trading_day = bool(
        day_payload.get("isTradingDay", day_payload.get("is_trading_day", day_payload.get("tradingAllowed", False)))
    )
    session_state = calendarSessionState(day_payload, ref)
    if not is_trading_day:
        return {
            "state": "calendar_non_trading_day",
            "path": str(path),
            "tradingAllowed": False,
            "dateKst": date_key,
            "isTradingDay": False,
            "sessionOpen": False,
            "krxOrderSessionOpen": False,
            "validUntil": valid_until or None,
            "reason": day_payload.get("reason") or "requested KST date is not a trading day",
            "sourceHierarchy": payload.get("sourceHierarchy") or "local KRX/NXT cached calendar",
        }

    state = "paper_autofilled" if mcal.is_paper_autofill_row(day_payload) else "calendar_ready"
    return {
        "state": state,
        "path": str(path),
        "tradingAllowed": True,
        "dateKst": date_key,
        "isTradingDay": True,
        "validUntil": valid_until or None,
        "reason": "paper autofilled calendar row ready" if state == "paper_autofilled" else "calendar row ready",
        "sourceAuthority": (
            day_payload.get("sourceAuthority")
            or day_payload.get("source")
            or payload.get("sourceAuthority")
            or payload.get("source")
            or "local_cache"
        ),
        "sourceHierarchy": (
            day_payload.get("sourceHierarchy")
            or payload.get("sourceHierarchy")
            or "local KRX/NXT cached calendar; KIS holiday lookup deferred"
        ),
        **session_state,
    }


def routeBlockedByCalendar(route: Dict[str, Any], calendar: Mapping[str, Any]) -> Dict[str, Any]:
    if calendar.get("state") in _READY_CALENDAR_STATES and calendar.get("isTradingDay") is True:
        return route
    blocked = dict(route)
    blocked.update(
        {
            "venue": "idle",
            "session": "market_closed",
            "inTradingEnvelope": False,
            "calendarBlocked": True,
            "calendarState": calendar.get("state"),
        }
    )
    return blocked


def evaluateMarketDataSource() -> Dict[str, Any]:
    source = os.getenv("HWISTOCK_MARKET_DATA_SOURCE", "").strip()
    if not source:
        return {
            "state": "source_unconfigured",
            "tradingLoopsActive": False,
            "reason": "market data source not configured",
        }
    order_grade_sources = {"kis_paper_mock", "kis_paper_read", "kis_market_six_input", "kis_market_mode_aware"}
    active = source in order_grade_sources
    return {
        "state": "source_configured",
        "source": source,
        "tradingLoopsActive": active,
        "reason": "order-grade market data source configured"
        if active
        else "configured source does not enable order routing",
    }


def setKillSwitch(active: bool) -> None:
    _runtime.kill_switch_active = bool(active)


def isKillSwitchActive() -> bool:
    env = os.getenv("HWISTOCK_KILL_SWITCH", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    return _runtime.kill_switch_active


def auditLogCategoriesMetadata() -> Dict[str, Any]:
    """Expose distinguishable local audit categories for AC-05 / QA-005 inspection."""
    categories = [
        {
            "id": cat_id,
            "description": description,
            "localPathHint": path_hint,
            "distinguishable": True,
        }
        for cat_id, description, path_hint in _AUDIT_CATEGORY_SPECS
    ]
    return {
        "policy": "AC-05_QA-005_category_separation",
        "externalDelivery": False,
        "categoryIds": [cat_id for cat_id, _, _ in _AUDIT_CATEGORY_SPECS],
        "categories": categories,
    }


def alertChannelsMetadata() -> Dict[str, Any]:
    today = date.today().isoformat()
    return {
        "delivery": "local_only",
        "externalDelivery": False,
        "channels": [
            {"type": "systemd_journal", "enabled": True},
            {"type": "file", "path": f"data/alerts/{today}/alerts.jsonl", "enabled": True},
            {"type": "dashboard_audit_panel", "enabled": False, "note": "when implemented"},
            {"type": "daily_close_report", "path": "daily-close-mode-aware.md", "enabled": True},
        ],
    }


def paperObservationTemplate() -> Dict[str, Any]:
    return {
        "evidenceRunner": "systemd",
        "durationPolicy": "operator_selected",
        "fixedDurationDays": None,
        "autoStopOnDuration": False,
        "autoPassOnDuration": False,
        "autoFailOnDuration": False,
        "profitThresholdRequired": False,
        "passCriteria": [
            "P0 safety controls enforced",
            "kill switch observable",
            "no-order dry-run boundary preserved",
            "local-only bind and alerts",
            "audit logs and daily summaries present",
            "operator-selected observation-window metadata present",
        ],
        "excludedEvidence": ["tmux", "screen", "manual shell-only sessions"],
    }


def getRunnerStatus(atKst: Optional[str] = None) -> Dict[str, Any]:
    at = parseKstTime(atKst)
    route = routeVenueAtKst(at)
    calendar = evaluateCalendarState(at)
    route = routeBlockedByCalendar(route, calendar)
    market_source = evaluateMarketDataSource()
    kill_switch = isKillSwitchActive()

    if kill_switch:
        order_gate = "blocked_kill_switch"
    elif calendar["state"] not in _READY_CALENDAR_STATES:
        order_gate = f"blocked_{calendar['state']}"
    elif market_source["state"] == "source_unconfigured":
        order_gate = "blocked_source_unconfigured"
    elif route["venue"] == "idle":
        order_gate = "blocked_off_session"
    else:
        order_gate = "no_order_dry_run_only"

    return {
        "runnerId": "hwistock-paper-runner-skeleton",
        "mode": "paper_sandbox",
        "operationMode": os.getenv("HWISTOCK_OPERATION_MODE", "observe_only"),
        "investmentMode": rp.runtimePolicyFromEnv(os.environ)["investment_mode"],
        "marketAnalysisFeedMode": rp.runtimePolicyFromEnv(os.environ)["market_analysis_feed_mode"],
        "executionVenueMode": rp.runtimePolicyFromEnv(os.environ)["execution_venue_mode"],
        "nxtEnabled": rp.runtimePolicyFromEnv(os.environ)["nxt_enabled"],
        "liveOrdersEnabled": False,
        "brokerCallsEnabled": False,
        "orderExecution": "no_order_dry_run",
        "liveMoneyTradingReady": {
            "state": "not_applicable",
            "liveApiAvailable": False,
            "blocksPaperOperation": False,
        },
        "productionQualityReady": {
            "state": "partial",
            "blocksPaperOperation": False,
        },
        "bindHostDefault": DEFAULT_BIND_HOST,
        "killSwitch": {"active": kill_switch, "blocksRouting": kill_switch},
        "routing": route,
        "calendar": calendar,
        "marketData": market_source,
        "orderGate": order_gate,
        "branches": {
            "marketIntelligence": {"uptime": "24h_capable", "canPlaceOrders": False},
            "trading": {"activeInEnvelopeOnly": True, "canPlaceOrders": False},
        },
        "budget": {
            "paperMockCandidateKrw": PAPER_BUDGET_KRW,
            "liveCapitalBaselineKrw": LIVE_CAPITAL_BASELINE_KRW,
        },
        "alerts": alertChannelsMetadata(),
        "auditLog": auditLogCategoriesMetadata(),
        "paperObservation": paperObservationTemplate(),
        "readiness": {
            "liveRunnerReady": False,
            "liveRunnerReadyBlocksPaperOperation": False,
            "paperObservationAccepted": False,
            "note": "live/production readiness is not applicable to KIS paper/mock experiment startup; paper experiment readiness is evaluated by the continuous KIS paper runner",
        },
        "currentReadiness": {
            "paper_experiment_start": "go_target",
            "paper_order_submission_ready": "conditional_go",
            "full_owner_defined_ai_loop_ready": "follow_up_required",
            "live_money_operational_readiness": "not_applicable",
            "production_quality_readiness": "partial_non_blocking",
        },
    }


def previewRoute(atKst: str) -> Dict[str, Any]:
    at = parseKstTime(atKst)
    route = routeVenueAtKst(at)
    status = getRunnerStatus(atKst)
    return {
        "preview": route,
        "orderGate": status["orderGate"],
        "killSwitchActive": status["killSwitch"]["active"],
    }


def dailyCloseTemplate() -> Dict[str, Any]:
    today = date.today().isoformat()
    return {
        "reportName": "daily-close-mode-aware.md",
        "date": today,
        "paperTargetKst": "15:30",
        "futureLiveTargetKst": "20:00",
        "sections": [
            "runtime_duration",
            "mode",
            "failures",
            "dry_run_intents",
            "risk_rejects",
            "kill_switch_events",
            "calendar_state",
            "alert_summary",
        ],
        "delivery": "local_file_only",
        "externalDelivery": False,
    }


def recordNoOrderIntent(intent: Dict[str, Any], atKst: Optional[str] = None) -> Dict[str, Any]:
    status = getRunnerStatus(atKst)
    blocked = status["orderGate"] != "no_order_dry_run_only"
    record = {
        "dryRun": True,
        "noBrokerCall": True,
        "fakeFillCreated": False,
        "fakeBalanceCreated": False,
        "fakePnlCreated": False,
        "recorded": not blocked,
        "blocked": blocked,
        "blockReason": status["orderGate"] if blocked else None,
        "intent": {
            "symbol": intent.get("symbol"),
            "side": intent.get("side"),
            "quantity": intent.get("quantity"),
            "venue": intent.get("venue") or status["routing"]["venue"],
            "note": intent.get("note"),
        },
        "auditCategory": "dry_run_order_intent",
    }
    if not blocked:
        _runtime.no_order_intents.append(record)
    return record


def listNoOrderIntents() -> List[Dict[str, Any]]:
    return list(_runtime.no_order_intents)


def resetRuntimeForTests() -> None:
    _runtime.kill_switch_active = False
    _runtime.no_order_intents.clear()


backend_dir = backendDir
emit_runner_once_stdout = emitRunnerOnceStdout
write_runner_evidence = writeRunnerEvidence
run_once_entrypoint = runOnceEntrypoint
route_venue_at_kst = routeVenueAtKst
evaluate_calendar_state = evaluateCalendarState
evaluate_market_data_source = evaluateMarketDataSource
set_kill_switch = setKillSwitch
is_kill_switch_active = isKillSwitchActive
audit_log_categories_metadata = auditLogCategoriesMetadata
alert_channels_metadata = alertChannelsMetadata
paper_observation_template = paperObservationTemplate
get_runner_status = getRunnerStatus
preview_route = previewRoute
daily_close_template = dailyCloseTemplate
record_no_order_intent = recordNoOrderIntent
list_no_order_intents = listNoOrderIntents
reset_runtime_for_tests = resetRuntimeForTests


if __name__ == "__main__":
    raise SystemExit(main())
