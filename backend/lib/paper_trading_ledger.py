"""
Paper trading ledger helpers for HWISTOCK-UNIT-010.

The ledger is system-calculated from explicit paper events. It rejects fake
broker events and does not infer fills or balances when KIS data is missing.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional


FORBIDDEN_FAKE_FIELDS = (
    "fake_fill",
    "fake_balance",
    "fake_pnl",
    "fake_fill_generated",
    "fake_balance_generated",
    "fake_pnl_generated",
)


def maskAccountAlias(account_no: Optional[str]) -> str:
    raw = str(account_no or "").strip()
    if not raw:
        return "paper_account_alias:unknown"
    return f"paper_account_alias:***{raw[-4:]}"


def buildObservationWindowManifest(
    *,
    started_at_kst: str,
    ended_at_kst: Optional[str] = None,
    operator_note: Optional[str] = None,
) -> Dict[str, Any]:
    manifest: Dict[str, Any] = {
        "schema_version": "paper_observation_window/v0",
        "duration_policy": "operator_selected",
        "fixed_duration_days": None,
        "auto_stop_on_duration": False,
        "auto_pass_on_duration": False,
        "auto_fail_on_duration": False,
        "started_at_kst": started_at_kst,
        "ended_at_kst": ended_at_kst,
        "operator_note": operator_note,
    }
    if ended_at_kst:
        manifest["elapsed_seconds"] = _elapsedSeconds(started_at_kst, ended_at_kst)
    return manifest


def validateNoFakeBrokerEvent(event: Mapping[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(dict(event))
    errors = []
    if str(payload.get("source") or "").lower() in {"fake_broker", "mock_broker_api"}:
        errors.append("fake_broker_source_forbidden")
    for field in FORBIDDEN_FAKE_FIELDS:
        if field in payload:
            errors.append(f"forbidden_fake_field:{field}")
    return {"ok": not errors, "errors": errors, "event": payload}


def buildLedgerSnapshot(
    events: Iterable[Mapping[str, Any]],
    *,
    starting_cash_krw: int = 2_000_000,
    account_no: Optional[str] = None,
) -> Dict[str, Any]:
    cash = int(starting_cash_krw)
    positions: Dict[str, Dict[str, Any]] = {}
    errors = []
    applied_events = []

    for raw_event in events:
        event = deepcopy(dict(raw_event))
        fake_check = validateNoFakeBrokerEvent(event)
        if not fake_check["ok"]:
            errors.extend(fake_check["errors"])
            continue

        kind = str(event.get("event_kind") or event.get("kind") or "").strip().lower()
        symbol = str(event.get("symbol") or "").strip()
        if kind == "fill":
            side = str(event.get("side") or "").strip().lower()
            qty = int(event.get("quantity") or 0)
            price = int(float(event.get("price_krw") or 0))
            if side not in {"buy", "sell"} or not symbol or qty <= 0 or price <= 0:
                errors.append("fill_event_invalid")
                continue
            gross = qty * price
            pos = positions.setdefault(symbol, {"quantity": 0, "cost_basis_krw": 0})
            if side == "buy":
                cash -= gross
                pos["quantity"] += qty
                pos["cost_basis_krw"] += gross
            else:
                cash += gross
                pos["quantity"] -= qty
                pos["cost_basis_krw"] = max(0, pos["cost_basis_krw"] - gross)
            applied_events.append({"event_kind": kind, "symbol": symbol, "side": side, "quantity": qty})
        elif kind in {"submitted", "accepted", "rejected", "cancelled", "balance", "buyable", "disabled_branch", "local_fallback"}:
            applied_events.append({"event_kind": kind, "symbol": symbol or None})
        else:
            errors.append(f"event_kind_unsupported:{kind or 'missing'}")

    positions = {symbol: value for symbol, value in positions.items() if int(value.get("quantity") or 0) != 0}
    exposure = sum(int(v.get("cost_basis_krw") or 0) for v in positions.values())
    return {
        "schema_version": "paper_ledger_snapshot/v0",
        "calculation_source": "system",
        "starting_cash_krw": int(starting_cash_krw),
        "cash_krw": cash,
        "exposure_cost_basis_krw": exposure,
        "positions": positions,
        "account_alias": maskAccountAlias(account_no),
        "errors": sorted(set(errors)),
        "ok": not errors,
        "fake_broker_used": False,
        "applied_event_count": len(applied_events),
        "applied_events": applied_events,
    }


def reconcilePaperEvidence(
    *,
    order_events: Iterable[Mapping[str, Any]],
    balance_snapshot: Optional[Mapping[str, Any]] = None,
    account_no: Optional[str] = None,
) -> Dict[str, Any]:
    ledger = buildLedgerSnapshot(order_events, account_no=account_no)
    balance = deepcopy(dict(balance_snapshot or {}))
    return {
        "schema_version": "paper_reconciliation/v0",
        "ok": ledger["ok"],
        "ledger": ledger,
        "balance_snapshot_present": bool(balance),
        "account_alias": maskAccountAlias(account_no),
        "raw_account_printed": False,
        "raw_response_stored": False,
        "errors": list(ledger["errors"]),
    }


def _elapsedSeconds(started_at: str, ended_at: str) -> int:
    start = datetime.fromisoformat(started_at)
    end = datetime.fromisoformat(ended_at)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return max(0, int((end - start).total_seconds()))
