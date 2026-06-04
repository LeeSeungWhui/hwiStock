"""
HWISTOCK-UNIT-006 current-authority rebaseline trading engine/order-state
foundation skeleton.

Stdlib-only deterministic local helpers for:
- condition_card/v0 validation and compilation
- UNIT-004 risk-gate delegation
- no-order dry-run decision records
- explicit order-state transition validation
- KIS paper capability/route metadata and fixture evidence representation

This module never places broker orders, never performs network calls, and never
simulates fills, balances, or PnL.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    from lib import strategy_risk as sr
except ImportError:  # pragma: no cover - fallback for package-style imports
    from backend.lib import strategy_risk as sr

KST = timezone(timedelta(hours=9))

CONDITION_CARD_SCHEMA_VERSION = "condition_card/v0"
COMPILED_WATCH_SCHEMA_VERSION = "compiled_watch/v0"
NO_ORDER_DRY_RUN = "no_order_dry_run"

ALLOWED_VENUE_ROUTES = frozenset({"KRX", "NXT", "SOR", "AUTO_SESSION"})
ALLOWED_WATCH_CONDITION_TYPES = frozenset(
    {
        "price_cross",
        "price_between",
        "volume_spike",
        "vwap_relation",
        "moving_average_relation",
        "orderbook_spread",
        "source_freshness",
        "event_context_present",
        "risk_flag_absent",
    }
)
VAGUE_WATCH_CONDITION_TYPES = frozenset({"free_text", "natural_language", "looks_good"})
ORDER_STATES = (
    "draft_intent",
    "compiled_watch",
    "eligible",
    "blocked",
    "dry_run_recorded",
    "submitted",
    "accepted",
    "partial_fill",
    "filled",
    "cancel_requested",
    "cancelled",
    "rejected",
    "retrying",
    "failed",
)
LATE_EXECUTABLE_STATES = frozenset(
    {
        "submitted",
        "accepted",
        "partial_fill",
        "filled",
        "cancel_requested",
        "cancelled",
        "rejected",
        "retrying",
        "failed",
    }
)
REPRESENTABLE_EVENT_ORDER_STATES = frozenset(
    {
        "submitted",
        "accepted",
        "partial_fill",
        "filled",
        "cancel_requested",
        "cancelled",
        "rejected",
        "retrying",
        "failed",
    }
)
TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+09:00$"
)
BROKERISH_ORDER_ID_PATTERN = re.compile(
    r"(?:\bkis\b|\bbroker\b|\bord(?:er)?[_-]?no\b|\back\b|\btx\b)",
    re.IGNORECASE,
)
FORBIDDEN_RECORD_FIELD_FRAGMENTS = (
    "broker_order_id",
    "submitted_at",
    "accepted_at",
    "fill_price",
    "fill_qty",
    "filled_qty",
    "filled_at",
    "fake_fill",
    "fake_balance",
    "fake_pnl",
    "fake_fill_generated",
    "fake_balance_generated",
    "fake_pnl_generated",
)
TRANSITIONS: Dict[str, frozenset[str]] = {
    "draft_intent": frozenset({"compiled_watch", "blocked"}),
    "compiled_watch": frozenset({"eligible", "blocked", "dry_run_recorded"}),
    "eligible": frozenset({"blocked", "dry_run_recorded", "submitted"}),
    "blocked": frozenset({"dry_run_recorded", "retrying"}),
    "dry_run_recorded": frozenset({"submitted"}),
    "submitted": frozenset({"accepted", "rejected", "retrying", "failed", "cancel_requested"}),
    "accepted": frozenset({"partial_fill", "filled", "cancel_requested", "failed"}),
    "partial_fill": frozenset({"filled", "cancel_requested", "failed"}),
    "filled": frozenset(),
    "cancel_requested": frozenset({"cancelled", "failed"}),
    "cancelled": frozenset(),
    "rejected": frozenset({"retrying", "failed"}),
    "retrying": frozenset({"submitted", "failed", "blocked"}),
    "failed": frozenset(),
}


def loadTradingEngineConfig() -> Dict[str, Any]:
    return {
        "module_id": "HWISTOCK-MOD-005",
        "version": "2026-06-04-rebaseline",
        "execution_mode": NO_ORDER_DRY_RUN,
        "condition_card_schema_version": CONDITION_CARD_SCHEMA_VERSION,
        "compiled_watch_schema_version": COMPILED_WATCH_SCHEMA_VERSION,
        "allowed_watch_condition_types": sorted(ALLOWED_WATCH_CONDITION_TYPES),
        "allowed_venue_routes": sorted(ALLOWED_VENUE_ROUTES),
        "order_states": list(ORDER_STATES),
        "late_executable_states": sorted(LATE_EXECUTABLE_STATES),
        "representation_only_states": sorted(REPRESENTABLE_EVENT_ORDER_STATES),
        "paper_adapter_enabled": False,
        "live_adapter_enabled": False,
        "same_state_machine_routes": ["KRX", "NXT", "SOR", "AUTO_SESSION"],
        "boundaries": {
            "broker_calls_allowed": False,
            "paper_orders_allowed": False,
            "live_orders_allowed": False,
            "fill_simulation_allowed": False,
            "balance_simulation_allowed": False,
            "pnl_simulation_allowed": False,
        },
        "strategy_risk_rulebook_id": sr.loadStrategyRiskConfig()["rulebook_id"],
    }


def validateConditionCard(
    card: Optional[Mapping[str, Any]],
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    payload = deepcopy(dict(card or {}))
    errors: List[str] = []

    if payload.get("schema_version") != CONDITION_CARD_SCHEMA_VERSION:
        errors.append("schema_version_must_be_condition_card_v0")

    for field_name in ("candidate_id", "symbol", "venue_route"):
        if not str(payload.get(field_name) or "").strip():
            errors.append(f"{field_name}_required")

    route = str(payload.get("venue_route") or "").strip()
    if route and route not in ALLOWED_VENUE_ROUTES:
        errors.append("venue_route_invalid")

    source_ids = payload.get("source_ids")
    if not isinstance(source_ids, list) or not source_ids:
        errors.append("source_ids_required")
    elif any(not str(item or "").strip() for item in source_ids):
        errors.append("source_ids_must_not_be_empty")

    risk_refs = payload.get("risk_refs")
    if isinstance(risk_refs, list):
        if not risk_refs:
            errors.append("risk_refs_required")
    elif isinstance(risk_refs, Mapping):
        if not risk_refs:
            errors.append("risk_refs_required")
    else:
        errors.append("risk_refs_required")

    if not isinstance(payload.get("entry_intent"), Mapping):
        errors.append("entry_intent_required")
    if not isinstance(payload.get("exit_plan"), Mapping):
        errors.append("exit_plan_required")

    created_at = _parse_kst_timestamp(payload.get("created_at_kst"), "created_at_kst", errors)
    valid_until = _parse_kst_timestamp(payload.get("valid_until_kst"), "valid_until_kst", errors)
    reference_now = _resolve_now_kst(now_kst, errors)
    if created_at and valid_until and valid_until <= created_at:
        errors.append("valid_until_kst_must_be_after_created_at_kst")
    if valid_until and reference_now and valid_until <= reference_now:
        errors.append("condition_card_expired")

    watch_conditions = payload.get("watch_conditions")
    if not isinstance(watch_conditions, list) or not watch_conditions:
        errors.append("watch_conditions_required")
    else:
        for index, condition in enumerate(watch_conditions):
            if not isinstance(condition, Mapping):
                errors.append(f"watch_condition_not_mapping:{index}")
                continue
            watch_type = str(condition.get("type") or "").strip()
            if not watch_type:
                errors.append(f"watch_condition_type_required:{index}")
                continue
            if watch_type in VAGUE_WATCH_CONDITION_TYPES:
                errors.append(f"watch_condition_vague_natural_language_only:{index}")
                continue
            if watch_type not in ALLOWED_WATCH_CONDITION_TYPES:
                errors.append(f"watch_condition_type_unknown:{index}:{watch_type}")
                continue
            if _contains_vague_condition_text(condition):
                errors.append(f"watch_condition_vague_natural_language_only:{index}")

    if not isAiCandidateNonExecutable(payload):
        errors.append("candidate_must_remain_non_executable")

    return {
        "ok": not errors,
        "errors": errors,
        "card": payload,
    }


def compileConditionCard(
    card: Optional[Mapping[str, Any]],
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    validation = validateConditionCard(card, now_kst=now_kst)
    if not validation["ok"]:
        return {
            "ok": False,
            "errors": list(validation["errors"]),
            "card": validation["card"],
            "compiled_watch": None,
        }

    payload = deepcopy(validation["card"])
    compiled_at_kst = now_kst or payload["created_at_kst"]
    compiled_watch = {
        "schema_version": COMPILED_WATCH_SCHEMA_VERSION,
        "condition_card_id": payload.get("condition_card_id") or payload["candidate_id"],
        "candidate_id": payload["candidate_id"],
        "symbol": payload["symbol"],
        "source_ids": list(payload["source_ids"]),
        "created_at_kst": payload["created_at_kst"],
        "valid_until_kst": payload["valid_until_kst"],
        "compiled_at_kst": compiled_at_kst,
        "venue_route": payload["venue_route"],
        "watch_state": "compiled_watch",
        "watch_conditions": [
            {
                "watch_condition_id": f"{payload['candidate_id']}:{index}",
                "type": condition["type"],
                "definition": deepcopy(dict(condition)),
            }
            for index, condition in enumerate(payload["watch_conditions"])
        ],
        "risk_refs": deepcopy(payload["risk_refs"]),
        "entry_intent": deepcopy(payload["entry_intent"]),
        "exit_plan": deepcopy(payload["exit_plan"]),
        "no_broker_call": True,
        "non_executable": True,
        "approved_adapter_enabled": False,
    }
    return {
        "ok": True,
        "errors": [],
        "card": payload,
        "compiled_watch": compiled_watch,
    }


def isAiCandidateNonExecutable(candidate_or_card: Optional[Mapping[str, Any]]) -> bool:
    if candidate_or_card is None:
        return True

    payload = dict(candidate_or_card)
    state = str(payload.get("order_state") or payload.get("watch_state") or payload.get("state") or "").strip()
    if state in LATE_EXECUTABLE_STATES:
        return False

    explicit_exec_markers = (
        payload.get("broker_order_id"),
        payload.get("submitted_at"),
        payload.get("accepted_at"),
        payload.get("fill_qty"),
        payload.get("filled_qty"),
    )
    if any(marker not in (None, "", [], {}) for marker in explicit_exec_markers):
        return False

    for required_false in (
        "no_broker_call",
        "no_simulated_fill",
        "no_simulated_balance",
        "no_simulated_pnl",
        "no_paper_order",
        "no_live_order",
    ):
        if required_false in payload and payload.get(required_false) is False:
            return False

    if payload.get("approved_adapter_enabled") is True:
        return False

    return True


def evaluateEntryRiskGate(
    entry_intent: Optional[Mapping[str, Any]],
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    payload = deepcopy(dict(entry_intent or {}))
    venue_resolution = _resolve_risk_gate_venue_route(payload)
    blocked_reasons = list(venue_resolution["errors"])

    if blocked_reasons:
        return {
            "ok": False,
            "risk_gate_result": "blocked",
            "blocked_reasons": blocked_reasons,
            "next_state": "blocked",
            "requested_venue_route": venue_resolution["requested_venue_route"],
            "risk_gate_venue_route": venue_resolution["risk_gate_venue_route"],
            "venue_resolution_status": venue_resolution["venue_resolution_status"],
            "validation": None,
        }

    normalized_intent = deepcopy(payload)
    normalized_intent["venue_route"] = venue_resolution["risk_gate_venue_route"]
    validation = sr.validateEntryIntent(normalized_intent, now_kst=now_kst)
    return {
        "ok": validation["ok"],
        "risk_gate_result": "pass" if validation["ok"] else "blocked",
        "blocked_reasons": list(validation["errors"]),
        "next_state": "eligible" if validation["ok"] else "blocked",
        "requested_venue_route": venue_resolution["requested_venue_route"],
        "risk_gate_venue_route": venue_resolution["risk_gate_venue_route"],
        "venue_resolution_status": venue_resolution["venue_resolution_status"],
        "validation": validation,
    }


def validateOrderStateTransition(
    from_state: str,
    to_state: str,
    approved_adapter_enabled: bool = False,
) -> Dict[str, Any]:
    start = str(from_state or "").strip()
    target = str(to_state or "").strip()

    errors: List[str] = []
    if start not in TRANSITIONS:
        errors.append("from_state_invalid")
    if target not in TRANSITIONS:
        errors.append("to_state_invalid")
    if errors:
        return {
            "ok": False,
            "errors": errors,
            "from_state": start,
            "to_state": target,
            "approved_adapter_enabled": approved_adapter_enabled,
        }

    if target not in TRANSITIONS[start]:
        return {
            "ok": False,
            "errors": ["order_state_transition_not_allowed"],
            "from_state": start,
            "to_state": target,
            "approved_adapter_enabled": approved_adapter_enabled,
        }

    if target in LATE_EXECUTABLE_STATES and not approved_adapter_enabled:
        return {
            "ok": False,
            "errors": ["foundation_scope_rejects_submitted_or_later"],
            "from_state": start,
            "to_state": target,
            "approved_adapter_enabled": approved_adapter_enabled,
        }

    return {
        "ok": True,
        "errors": [],
        "from_state": start,
        "to_state": target,
        "approved_adapter_enabled": approved_adapter_enabled,
        "state_update_executed": False,
        "execution_boundary": (
            "representation_only_adapter_metadata"
            if target in LATE_EXECUTABLE_STATES
            else "no_order_dry_run_foundation"
        ),
    }


def buildNoOrderDryRunDecisionRecord(
    *,
    candidate_id: str,
    condition_card_id: str,
    decision: str,
    would_venue_route: str,
    would_order_side: str,
    would_order_price_type: str,
    would_cash_amount_krw: int,
    risk_gate_result: Any,
    blocked_reasons: Optional[Sequence[str]] = None,
    created_at_kst: Optional[str] = None,
) -> Dict[str, Any]:
    timestamp = created_at_kst or _current_kst_timestamp()
    return {
        "mode": NO_ORDER_DRY_RUN,
        "candidate_id": candidate_id,
        "condition_card_id": condition_card_id,
        "decision": decision,
        "would_venue_route": would_venue_route,
        "would_order_side": would_order_side,
        "would_order_price_type": would_order_price_type,
        "would_cash_amount_krw": int(would_cash_amount_krw),
        "risk_gate_result": deepcopy(risk_gate_result),
        "blocked_reasons": list(blocked_reasons or []),
        "no_broker_call": True,
        "no_simulated_fill": True,
        "no_simulated_balance": True,
        "no_simulated_pnl": True,
        "no_paper_order": True,
        "no_live_order": True,
        "created_at_kst": timestamp,
    }


def validateNoOrderDryRunDecisionRecord(
    record: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    payload = deepcopy(dict(record or {}))
    errors: List[str] = []

    required_fields = (
        "mode",
        "candidate_id",
        "condition_card_id",
        "decision",
        "would_venue_route",
        "would_order_side",
        "would_order_price_type",
        "would_cash_amount_krw",
        "risk_gate_result",
        "blocked_reasons",
        "no_broker_call",
        "no_simulated_fill",
        "no_simulated_balance",
        "no_simulated_pnl",
        "no_paper_order",
        "no_live_order",
        "created_at_kst",
    )
    for field_name in required_fields:
        if field_name not in payload:
            errors.append(f"missing_record_field:{field_name}")

    if payload.get("mode") != NO_ORDER_DRY_RUN:
        errors.append("mode_must_be_no_order_dry_run")
    if payload.get("decision") not in {"would_watch", "would_enter", "would_exit", "blocked"}:
        errors.append("decision_invalid")

    route = str(payload.get("would_venue_route") or "").strip()
    if route not in ALLOWED_VENUE_ROUTES:
        errors.append("would_venue_route_invalid")

    if not isinstance(payload.get("blocked_reasons"), list):
        errors.append("blocked_reasons_must_be_list")

    for field_name in (
        "candidate_id",
        "condition_card_id",
        "would_order_side",
        "would_order_price_type",
    ):
        if not str(payload.get(field_name) or "").strip():
            errors.append(f"{field_name}_required")

    if payload.get("no_broker_call") is not True:
        errors.append("no_broker_call_must_be_true")
    if payload.get("no_simulated_fill") is not True:
        errors.append("no_simulated_fill_must_be_true")
    if payload.get("no_simulated_balance") is not True:
        errors.append("no_simulated_balance_must_be_true")
    if payload.get("no_simulated_pnl") is not True:
        errors.append("no_simulated_pnl_must_be_true")
    if payload.get("no_paper_order") is not True:
        errors.append("no_paper_order_must_be_true")
    if payload.get("no_live_order") is not True:
        errors.append("no_live_order_must_be_true")

    _parse_kst_timestamp(payload.get("created_at_kst"), "created_at_kst", errors)

    if "broker_order_id" in payload:
        errors.append("broker_order_id_forbidden")

    order_id = str(payload.get("order_id") or "").strip()
    if order_id and BROKERISH_ORDER_ID_PATTERN.search(order_id):
        errors.append("broker_like_order_id_forbidden")

    for field_path, _ in _iter_nested_fields(payload):
        if any(fragment in field_path for fragment in FORBIDDEN_RECORD_FIELD_FRAGMENTS):
            errors.append(f"forbidden_record_field:{field_path}")

    if not isAiCandidateNonExecutable(payload):
        errors.append("record_must_remain_non_executable")

    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "record": payload,
    }


def loadKisPaperCapabilityFlags() -> Dict[str, Any]:
    return {
        "supports_paper_krx_order": True,
        "supports_paper_nxt_order": False,
        "supports_paper_sor_order": False,
        "supports_paper_krx_realtime": True,
        "supports_paper_nxt_realtime": False,
        "supports_paper_integrated_realtime": False,
        "supports_paper_cancel_order": True,
        "supports_paper_cancelable_query": False,
        "supports_paper_sellable_quantity_query": False,
        "supports_paper_realized_pnl_query": False,
        "supports_paper_holiday_query": False,
        "unsupported_branch_policy": {
            "nxt_order": "disabled_branch",
            "sor_order": "disabled_branch",
            "nxt_realtime": "disabled_branch",
            "integrated_realtime": "disabled_branch",
            "cancelable_query": "local_fallback",
            "sellable_quantity_query": "local_fallback",
            "realized_pnl_query": "local_fallback",
            "holiday_query": "local_fallback",
        },
    }


def resolveVenueRoute(route: str, mode: str = NO_ORDER_DRY_RUN) -> Dict[str, Any]:
    normalized_route = str(route or "").strip().upper()
    if normalized_route not in ALLOWED_VENUE_ROUTES:
        return {
            "ok": False,
            "errors": ["venue_route_invalid"],
            "route": normalized_route,
            "mode": mode,
        }

    capabilities = loadKisPaperCapabilityFlags()
    branch_status = "local_fallback"
    capability_key = None
    if mode == "kis_paper":
        if normalized_route == "KRX":
            branch_status = "capability_available"
            capability_key = "supports_paper_krx_order"
        elif normalized_route in {"NXT", "SOR"}:
            branch_status = "disabled_branch"
            capability_key = (
                "supports_paper_nxt_order"
                if normalized_route == "NXT"
                else "supports_paper_sor_order"
            )
        else:
            branch_status = "local_fallback"
    elif mode == NO_ORDER_DRY_RUN:
        branch_status = "local_fallback"

    return {
        "ok": True,
        "errors": [],
        "mode": mode,
        "route": normalized_route,
        "state_machine": list(ORDER_STATES),
        "branch_status": branch_status,
        "broker_capability_key": capability_key,
        "broker_capability_enabled": (
            capabilities.get(capability_key, False) if capability_key else False
        ),
        "no_broker_call": True,
        "state_update_executed": False,
    }


def representBrokerEventState(event: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    return representKisPaperEvidenceEvent(event)


def representKisPaperEvidenceEvent(event: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    payload = deepcopy(dict(event or {}))
    event_kind = str(payload.get("event_kind") or payload.get("kind") or "").strip().lower()
    if not event_kind:
        raise ValueError("event_kind_required")

    base = {
        "representation_type": "kis_paper_evidence_event/v0",
        "event_kind": event_kind,
        "raw_event": payload,
        "no_broker_call": True,
        "state_update_executed": False,
        "no_simulated_fill": True,
        "no_simulated_balance": True,
        "no_simulated_pnl": True,
    }

    if event_kind in {"order", "fill", "cancel"}:
        mapped_order_state = str(payload.get("mapped_order_state") or "").strip()
        allowed_states = _allowed_mapped_states_for_event_kind(event_kind)
        if mapped_order_state not in allowed_states:
            raise ValueError("mapped_order_state_required_for_order_fill_cancel")
        base["mapped_order_state"] = mapped_order_state
        return base

    if event_kind == "balance":
        if payload.get("mapped_order_state") not in (None, ""):
            raise ValueError("balance_event_cannot_set_order_state")
        base["mapped_order_state"] = None
        base["balance_only"] = True
        return base

    if event_kind in {"disabled_branch", "local_fallback"}:
        if payload.get("mapped_order_state") not in (None, ""):
            raise ValueError("fallback_event_cannot_set_order_state")
        base["mapped_order_state"] = None
        return base

    if event_kind == "helper":
        if payload.get("mapped_order_state") not in (None, ""):
            raise ValueError("helper_event_cannot_set_order_state")
        base["event_kind"] = "local_fallback"
        base["helper_name"] = str(payload.get("helper_name") or "").strip() or "unsupported_helper"
        base["mapped_order_state"] = None
        return base

    raise ValueError(f"event_kind_unsupported:{event_kind}")


def _resolve_now_kst(now_kst: Optional[str], errors: List[str]) -> datetime:
    if now_kst:
        parsed = _parse_kst_timestamp(now_kst, "now_kst", errors)
        if parsed is not None:
            return parsed
    return datetime.now(tz=KST)


def _parse_kst_timestamp(value: Any, label: str, errors: List[str]) -> Optional[datetime]:
    if value in (None, ""):
        errors.append(f"{label}_required")
        return None
    raw = str(value).strip()
    if not TIMESTAMP_PATTERN.match(raw):
        errors.append(f"{label}_must_be_kst_iso")
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        errors.append(f"{label}_must_be_kst_iso")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != KST.utcoffset(None):
        errors.append(f"{label}_must_be_kst_iso")
        return None
    return parsed


def _resolve_risk_gate_venue_route(entry_intent: Mapping[str, Any]) -> Dict[str, Any]:
    requested_venue_route = str(entry_intent.get("venue_route") or "").strip().upper()
    if requested_venue_route not in ALLOWED_VENUE_ROUTES:
        return {
            "requested_venue_route": requested_venue_route,
            "risk_gate_venue_route": requested_venue_route,
            "venue_resolution_status": "blocked_invalid_requested_route",
            "errors": ["venue_route_invalid"],
        }

    if requested_venue_route in {"KRX", "NXT"}:
        return {
            "requested_venue_route": requested_venue_route,
            "risk_gate_venue_route": requested_venue_route,
            "venue_resolution_status": "direct_foundation_route",
            "errors": [],
        }

    if requested_venue_route == "SOR":
        return {
            "requested_venue_route": requested_venue_route,
            "risk_gate_venue_route": "KRX",
            "venue_resolution_status": "normalized_sor_to_krx_for_foundation",
            "errors": [],
        }

    session_venue_hint = str(entry_intent.get("session_venue_hint") or "").strip().upper()
    if requested_venue_route == "AUTO_SESSION":
        if session_venue_hint in {"KRX", "NXT"}:
            return {
                "requested_venue_route": requested_venue_route,
                "risk_gate_venue_route": session_venue_hint,
                "venue_resolution_status": "resolved_auto_session_from_hint",
                "errors": [],
            }
        return {
            "requested_venue_route": requested_venue_route,
            "risk_gate_venue_route": None,
            "venue_resolution_status": "blocked_auto_session_unresolved",
            "errors": ["auto_session_requires_resolved_underlying_venue"],
        }

    return {
        "requested_venue_route": requested_venue_route,
        "risk_gate_venue_route": None,
        "venue_resolution_status": "blocked_unhandled_requested_route",
        "errors": ["venue_route_invalid"],
    }


def _allowed_mapped_states_for_event_kind(event_kind: str) -> frozenset[str]:
    if event_kind == "order":
        return frozenset({"submitted", "accepted", "rejected", "retrying", "failed"})
    if event_kind == "fill":
        return frozenset({"partial_fill", "filled"})
    if event_kind == "cancel":
        return frozenset({"cancel_requested", "cancelled", "rejected", "failed"})
    return REPRESENTABLE_EVENT_ORDER_STATES


def _contains_vague_condition_text(condition: Mapping[str, Any]) -> bool:
    text_values = list(_iter_string_values(condition))
    if not text_values:
        return False
    lowered = [value.lower() for value in text_values]
    return any(
        token in value
        for value in lowered
        for token in ("looks good", "natural language", "free text", "free_text")
    )


def _iter_string_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            yield stripped
        return
    if isinstance(value, Mapping):
        for nested in value.values():
            yield from _iter_string_values(nested)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            yield from _iter_string_values(nested)


def _iter_nested_fields(value: Any, prefix: str = "") -> Iterable[Tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield next_prefix.lower(), nested_value
            yield from _iter_nested_fields(nested_value, next_prefix)
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            next_prefix = f"{prefix}[{index}]"
            yield from _iter_nested_fields(nested_value, next_prefix)


def _current_kst_timestamp() -> str:
    return datetime.now(tz=KST).replace(microsecond=0).isoformat()
