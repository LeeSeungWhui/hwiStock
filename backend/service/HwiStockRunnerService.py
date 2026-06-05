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
from typing import Any, Dict, List, Optional, Sequence
from zoneinfo import ZoneInfo

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
_DEFAULT_CALENDAR_PATH = _REPO_ROOT / "config" / "market-calendar" / "krx-nxt-trading-days.json"


@dataclass
class RunnerRuntimeState:
    kill_switch_active: bool = False
    no_order_intents: List[Dict[str, Any]] = field(default_factory=list)


_runtime = RunnerRuntimeState()


def backend_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def normalize_loopback_bind_host(host: Optional[str]) -> str:
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


def resolve_bind_host(config_host: Optional[str] = None) -> str:
    """
    Local-only bind default. Env HWISTOCK_BIND_HOST overrides config when set.
    Rejects unsafe public/LAN bind values by coercing to loopback.
    """
    env_host = os.getenv("HWISTOCK_BIND_HOST", "").strip()
    if env_host:
        return normalize_loopback_bind_host(env_host)
    if config_host and str(config_host).strip():
        return normalize_loopback_bind_host(str(config_host).strip())
    return DEFAULT_BIND_HOST


def emit_runner_once_stdout() -> Dict[str, Any]:
    """Local-only runner tick payload for --once (no broker/network/orders)."""
    return {
        "event": "runner_once",
        "timestamp": datetime.now(KST).isoformat(),
        "status": get_runner_status(),
        "auditLog": audit_log_categories_metadata(),
    }


def _runtime_date_dir(output_root: Path, at: datetime) -> Path:
    return output_root / "evidence" / at.astimezone(KST).date().isoformat()


def write_runner_evidence(
    payload: Dict[str, Any],
    *,
    output_root: Optional[Path] = None,
    at: Optional[datetime] = None,
) -> Dict[str, str]:
    """Write latest and timestamped runner evidence without broker/order calls."""
    now = at or datetime.now(KST)
    root = output_root or Path(os.getenv("HWISTOCK_DATA_DIR", str(_REPO_ROOT / "data")))
    evidence_dir = _runtime_date_dir(root, now)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%H%M%S")
    latest_path = evidence_dir / "runner-latest.json"
    stamped_path = evidence_dir / f"runner-{stamp}.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    latest_path.write_text(text, encoding="utf-8")
    stamped_path.write_text(text, encoding="utf-8")
    return {
        "latest_path": str(latest_path),
        "stamped_path": str(stamped_path),
    }


def run_once_entrypoint() -> int:
    payload = emit_runner_once_stdout()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
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
        payload = emit_runner_once_stdout()
        if args.write_evidence:
            payload["evidencePaths"] = write_runner_evidence(
                payload,
                output_root=Path(args.output_root),
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    parser.print_help(sys.stderr)
    return 2


def _parse_kst_time(value: Optional[str]) -> datetime:
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


def route_venue_at_kst(at: datetime) -> Dict[str, Any]:
    """Simple KRX/NXT/idle routing for 08:00-20:00 KST envelope."""
    local = at.astimezone(KST)
    t = local.time()
    nxt_pre = time(8, 0) <= t < time(9, 0)
    krx = time(9, 0) <= t < time(15, 0)
    nxt_post = time(15, 0) <= t < time(20, 0)
    in_envelope = time(8, 0) <= t < time(20, 0)

    if not in_envelope:
        venue = "idle"
        session = "off_hours"
    elif krx:
        venue = "KRX"
        session = "krx_regular"
    elif nxt_pre or nxt_post:
        venue = "NXT"
        session = "nxt_extended"
    else:
        venue = "idle"
        session = "off_hours"

    return {
        "atKst": local.isoformat(),
        "venue": venue,
        "session": session,
        "inTradingEnvelope": in_envelope,
        "routingPolicy": "KRX 09:00-15:00; NXT 08:00-09:00 and 15:00-20:00; idle otherwise",
    }


def _calendar_path() -> Path:
    override = os.getenv("HWISTOCK_CALENDAR_PATH", "").strip()
    if override:
        p = Path(override)
        return p if p.is_absolute() else _REPO_ROOT / override
    return _DEFAULT_CALENDAR_PATH


def evaluate_calendar_state(now: Optional[datetime] = None) -> Dict[str, Any]:
    path = _calendar_path()
    if not path.is_file():
        return {
            "state": "calendar_unconfigured",
            "path": str(path),
            "tradingAllowed": False,
            "reason": "local calendar cache missing",
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "state": "calendar_unconfigured",
            "path": str(path),
            "tradingAllowed": False,
            "reason": "calendar cache unreadable",
        }

    valid_until = str(payload.get("validUntil") or payload.get("valid_until") or "").strip()
    if valid_until:
        try:
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=KST)
            ref = (now or datetime.now(KST)).astimezone(KST)
            if ref > expiry.astimezone(KST):
                return {
                    "state": "calendar_stale",
                    "path": str(path),
                    "tradingAllowed": False,
                    "validUntil": valid_until,
                    "reason": "calendar cache expired",
                }
        except ValueError:
            return {
                "state": "calendar_stale",
                "path": str(path),
                "tradingAllowed": False,
                "reason": "calendar validUntil unparsable",
            }

    return {
        "state": "calendar_ready",
        "path": str(path),
        "tradingAllowed": True,
        "sourceHierarchy": "local KRX/NXT cached calendar; KIS holiday lookup deferred",
    }


def evaluate_market_data_source() -> Dict[str, Any]:
    source = os.getenv("HWISTOCK_MARKET_DATA_SOURCE", "").strip()
    if not source:
        return {
            "state": "source_unconfigured",
            "tradingLoopsActive": False,
            "reason": "market data source not configured",
        }
    return {
        "state": "source_configured",
        "source": source,
        "tradingLoopsActive": False,
        "reason": "skeleton: configured source does not enable order routing",
    }


def set_kill_switch(active: bool) -> None:
    _runtime.kill_switch_active = bool(active)


def is_kill_switch_active() -> bool:
    env = os.getenv("HWISTOCK_KILL_SWITCH", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    return _runtime.kill_switch_active


def audit_log_categories_metadata() -> Dict[str, Any]:
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


def alert_channels_metadata() -> Dict[str, Any]:
    today = date.today().isoformat()
    return {
        "delivery": "local_only",
        "externalDelivery": False,
        "channels": [
            {"type": "systemd_journal", "enabled": True},
            {"type": "file", "path": f"data/alerts/{today}/alerts.jsonl", "enabled": True},
            {"type": "dashboard_audit_panel", "enabled": False, "note": "when implemented"},
            {"type": "daily_close_report", "path": "daily-close-2000.md", "enabled": True},
        ],
    }


def paper_observation_template() -> Dict[str, Any]:
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


def get_runner_status(at_kst: Optional[str] = None) -> Dict[str, Any]:
    at = _parse_kst_time(at_kst)
    route = route_venue_at_kst(at)
    calendar = evaluate_calendar_state(at)
    market_source = evaluate_market_data_source()
    kill_switch = is_kill_switch_active()

    if kill_switch:
        order_gate = "blocked_kill_switch"
    elif calendar["state"] in ("calendar_unconfigured", "calendar_stale"):
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
        "liveOrdersEnabled": False,
        "brokerCallsEnabled": False,
        "orderExecution": "no_order_dry_run",
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
        "alerts": alert_channels_metadata(),
        "auditLog": audit_log_categories_metadata(),
        "paperObservation": paper_observation_template(),
        "readiness": {
            "liveRunnerReady": False,
            "paperObservationAccepted": False,
            "note": "runtime services may be active, but operational paper-trading readiness remains false until the full UNIT-011 through UNIT-015 queue passes Go/Check/Prove",
        },
    }


def preview_route(at_kst: str) -> Dict[str, Any]:
    at = _parse_kst_time(at_kst)
    route = route_venue_at_kst(at)
    status = get_runner_status(at_kst)
    return {
        "preview": route,
        "orderGate": status["orderGate"],
        "killSwitchActive": status["killSwitch"]["active"],
    }


def daily_close_template() -> Dict[str, Any]:
    today = date.today().isoformat()
    return {
        "reportName": "daily-close-2000.md",
        "date": today,
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


def record_no_order_intent(intent: Dict[str, Any], at_kst: Optional[str] = None) -> Dict[str, Any]:
    status = get_runner_status(at_kst)
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


def list_no_order_intents() -> List[Dict[str, Any]]:
    return list(_runtime.no_order_intents)


def reset_runtime_for_tests() -> None:
    _runtime.kill_switch_active = False
    _runtime.no_order_intents.clear()


if __name__ == "__main__":
    raise SystemExit(main())
