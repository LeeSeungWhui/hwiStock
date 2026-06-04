"""
HWISTOCK-UNIT-004 current-authority rebaseline strategy/risk rulebook.
Stdlib-only deterministic config and validation helpers for no-order dry-run
entry intent review. No broker, network, credential, or fake fill/PnL behavior.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Mapping, Optional

KST = timezone(timedelta(hours=9))

NO_ORDER_DRY_RUN = "no_order_dry_run"
ALLOWED_SIGNAL_PATHS = frozenset({"event_first", "chart_first", "combined"})
ALLOWED_VENUES = frozenset({"KRX", "NXT"})
FORBIDDEN_EXECUTION_TOKENS = (
    "broker",
    "kis",
    "live",
    "paper",
    "fill",
    "submit",
    "accept",
    "mock_broker",
    "fake_broker",
)
TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+09:00$"
)
FORBIDDEN_SIMULATION_FLAGS = (
    "fake_fill",
    "fake_balance",
    "fake_pnl",
    "fake_fill_generated",
    "fake_balance_generated",
    "fake_pnl_generated",
)
MANUAL_BLOCK_FLAGS = (
    "manual_kill_switch_active",
    "kill_switch_active",
    "operator_halt_active",
    "manual_entry_block_active",
    "trading_halt_active",
    "safety_block_active",
    "entry_block_active",
    "operator_block_active",
)
MANUAL_BLOCK_CONTAINERS = ("operator_control", "safety_control")
MANUAL_BLOCK_ERROR = "manual_kill_switch_or_operator_block_active"


def loadStrategyRiskConfig() -> Dict[str, Any]:
    return {
        "rulebook_id": "HWISTOCK-MOD-003",
        "version": "2026-06-04-rebaseline",
        "execution_mode": NO_ORDER_DRY_RUN,
        "broker_adapter": NO_ORDER_DRY_RUN,
        "capital_mode": "cash_only",
        "starting_capital_krw": 2_000_000,
        "paper_planning_budget_krw": 10_000_000,
        "minimum_cash_reserve_ratio": 0.25,
        "max_simultaneous_holdings": 5,
        "max_stop_loss_pct": -0.05,
        "minimum_reward_risk_ratio": 1.2,
        "target_band_pct": {
            "min": 0.01,
            "max": 0.05,
            "label": "per_position_price_move",
        },
        "holding_window_minutes": {
            "hypothesis_min": 10,
            "hypothesis_max": 20,
            "hard_max": 30,
        },
        "day_end_flat_policy": {
            "new_entries_cutoff_kst": "19:30",
            "flat_by_kst": "19:50",
        },
        "signal_policy": {
            "allowed_paths": sorted(ALLOWED_SIGNAL_PATHS),
            "chart_confirmation_required_for_event_first": True,
            "allowed_chart_intervals": ["1m", "3m", "5m"],
            "stale_signal_after_seconds": 900,
            "max_stop_age_seconds": 900,
            "require_fresh_signal_for_reentry": True,
        },
        "ai_stop_policy": {
            "required": True,
            "source": "ai",
            "auditable_required": True,
            "fallback_allowed": False,
        },
        "boundaries": {
            "broker_calls_allowed": False,
            "paper_orders_allowed": False,
            "live_orders_allowed": False,
            "fake_broker_allowed": False,
            "fill_simulation_allowed": False,
            "balance_simulation_allowed": False,
            "pnl_simulation_allowed": False,
        },
    }


def validateStrategyRiskConfig(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    payload = deepcopy(dict(config or {}))
    errors: List[str] = []

    if payload.get("starting_capital_krw") != 2_000_000:
        errors.append("starting_capital_krw_must_be_2000000")
    if payload.get("capital_mode") != "cash_only":
        errors.append("capital_mode_must_be_cash_only")
    if payload.get("execution_mode") != NO_ORDER_DRY_RUN:
        errors.append("execution_mode_must_be_no_order_dry_run")
    if payload.get("broker_adapter") != NO_ORDER_DRY_RUN:
        errors.append("broker_adapter_must_be_no_order_dry_run")
    if payload.get("minimum_cash_reserve_ratio") != 0.25:
        errors.append("minimum_cash_reserve_ratio_must_be_0_25")
    if payload.get("max_simultaneous_holdings") != 5:
        errors.append("max_simultaneous_holdings_must_be_5")
    if payload.get("max_stop_loss_pct") != -0.05:
        errors.append("max_stop_loss_pct_must_be_minus_5pct")
    if payload.get("minimum_reward_risk_ratio") != 1.2:
        errors.append("minimum_reward_risk_ratio_must_be_1_2")

    target = payload.get("target_band_pct") or {}
    if target.get("min") != 0.01 or target.get("max") != 0.05:
        errors.append("target_band_pct_must_be_1_to_5_percent")
    if target.get("label") != "per_position_price_move":
        errors.append("target_band_label_must_be_per_position_price_move")

    hold = payload.get("holding_window_minutes") or {}
    if hold.get("hypothesis_min") != 10 or hold.get("hypothesis_max") != 20:
        errors.append("holding_window_hypothesis_must_be_10_to_20_minutes")
    if hold.get("hard_max") != 30:
        errors.append("holding_window_hard_max_must_be_30_minutes")

    signal_policy = payload.get("signal_policy") or {}
    if signal_policy.get("chart_confirmation_required_for_event_first") is not True:
        errors.append("event_first_chart_confirmation_required")
    if signal_policy.get("stale_signal_after_seconds") != 900:
        errors.append("stale_signal_after_seconds_must_be_900")
    if signal_policy.get("max_stop_age_seconds") != 900:
        errors.append("max_stop_age_seconds_must_be_900")
    if signal_policy.get("require_fresh_signal_for_reentry") is not True:
        errors.append("fresh_signal_required_for_reentry")

    ai_stop = payload.get("ai_stop_policy") or {}
    if ai_stop.get("required") is not True:
        errors.append("ai_stop_required")
    if ai_stop.get("source") != "ai":
        errors.append("ai_stop_source_must_be_ai")
    if ai_stop.get("auditable_required") is not True:
        errors.append("ai_stop_must_be_auditable")
    if ai_stop.get("fallback_allowed") is not False:
        errors.append("ai_stop_fallback_forbidden")

    boundaries = payload.get("boundaries") or {}
    if boundaries.get("broker_calls_allowed") is not False:
        errors.append("broker_calls_must_be_disabled")
    if boundaries.get("paper_orders_allowed") is not False:
        errors.append("paper_orders_must_be_disabled")
    if boundaries.get("live_orders_allowed") is not False:
        errors.append("live_orders_must_be_disabled")
    if boundaries.get("fake_broker_allowed") is not False:
        errors.append("fake_broker_must_be_disabled")
    if boundaries.get("fill_simulation_allowed") is not False:
        errors.append("fill_simulation_must_be_disabled")
    if boundaries.get("balance_simulation_allowed") is not False:
        errors.append("balance_simulation_must_be_disabled")
    if boundaries.get("pnl_simulation_allowed") is not False:
        errors.append("pnl_simulation_must_be_disabled")

    return {
        "ok": not errors,
        "errors": errors,
        "config": payload,
    }


def validateSignalBundle(
    signal_bundle: Optional[Mapping[str, Any]],
    *,
    config: Optional[Mapping[str, Any]] = None,
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = dict(config or loadStrategyRiskConfig())
    errors: List[str] = []
    bundle = deepcopy(dict(signal_bundle or {}))
    signal_policy = cfg["signal_policy"]

    source_path = str(bundle.get("source_path") or "").strip()
    if source_path not in ALLOWED_SIGNAL_PATHS:
        errors.append("signal_bundle_source_path_invalid")

    signal_id = str(bundle.get("signal_id") or "").strip()
    if not signal_id:
        errors.append("signal_bundle_signal_id_required")

    candidate_reason = str(bundle.get("candidate_reason") or "").strip()
    if not candidate_reason:
        errors.append("signal_bundle_candidate_reason_required")

    price_volume_reason = str(bundle.get("price_volume_reason") or "").strip()
    if not price_volume_reason:
        errors.append("signal_bundle_price_volume_reason_required")

    chart_interval = str(bundle.get("chart_interval") or "").strip()
    if chart_interval not in set(signal_policy["allowed_chart_intervals"]):
        errors.append("signal_bundle_chart_interval_invalid")

    generated_at_raw = bundle.get("generated_at_kst")
    chart_timestamp_raw = bundle.get("chart_timestamp_kst")
    generated_at = _parse_kst_timestamp(generated_at_raw, "signal_bundle_generated_at_kst", errors)
    chart_timestamp = _parse_kst_timestamp(
        chart_timestamp_raw,
        "signal_bundle_chart_timestamp_kst",
        errors,
    )

    source_ids = bundle.get("source_ids")
    if source_path in {"event_first", "combined"}:
        if not isinstance(source_ids, list) or not source_ids:
            errors.append("signal_bundle_source_ids_required")

    chart_confirmation = bundle.get("chart_confirmation")
    chart_confirmed = False
    chart_confirmation_reason = ""
    if isinstance(chart_confirmation, Mapping):
        chart_confirmed = bool(chart_confirmation.get("confirmed"))
        chart_confirmation_reason = str(chart_confirmation.get("reason") or "").strip()
    else:
        chart_confirmed = bool(bundle.get("chart_confirmed"))
        chart_confirmation_reason = str(bundle.get("chart_confirmation_reason") or "").strip()

    if source_path == "event_first":
        if not chart_confirmed or not chart_confirmation_reason:
            errors.append("event_first_requires_chart_confirmation")

    if not chart_confirmation_reason and source_path in {"chart_first", "combined"}:
        errors.append("chart_confirmation_reason_required")

    stale_flag = bool(bundle.get("stale_data"))
    if stale_flag:
        errors.append("signal_bundle_stale_data")

    reference_now = _parse_kst_timestamp(now_kst, "now_kst", []) if now_kst else generated_at
    if generated_at and reference_now:
        age = (reference_now - generated_at).total_seconds()
        if age > signal_policy["stale_signal_after_seconds"]:
            errors.append("signal_bundle_stale_data")
    if chart_timestamp and reference_now:
        age = (reference_now - chart_timestamp).total_seconds()
        if age > signal_policy["stale_signal_after_seconds"]:
            errors.append("signal_bundle_stale_chart_data")

    bundle["chart_confirmed"] = chart_confirmed
    bundle["chart_confirmation_reason"] = chart_confirmation_reason
    return {"ok": not errors, "errors": errors, "signal_bundle": bundle}


def validateCandidateOnlyIntent(
    intent: Optional[Mapping[str, Any]],
    *,
    config: Optional[Mapping[str, Any]] = None,
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    payload = deepcopy(dict(intent or {}))
    errors: List[str] = []

    if payload.get("watchlist_only") is not True:
        errors.append("candidate_only_intent_must_be_watchlist_only")

    forbidden_entry_fields = (
        "venue_route",
        "planned_order_cash_krw",
        "entry_price_krw",
        "stop_loss",
        "target_price_krw",
        "target_profit_pct",
        "broker_adapter",
        "execution_mode",
        "order_type",
        "submitted_state",
        "accepted_state",
        "fill_state",
    )
    for field_name in forbidden_entry_fields:
        if payload.get(field_name) not in (None, "", [], {}):
            errors.append(f"candidate_only_intent_forbidden_field:{field_name}")

    signal_result = validateSignalBundle(
        payload.get("signal_bundle"),
        config=config,
        now_kst=now_kst,
    )
    errors.extend(signal_result["errors"])

    return {
        "ok": not errors,
        "errors": errors,
        "intent": payload,
        "signal_bundle": signal_result.get("signal_bundle"),
    }


def validateEntryIntent(
    intent: Optional[Mapping[str, Any]],
    *,
    config: Optional[Mapping[str, Any]] = None,
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = dict(config or loadStrategyRiskConfig())
    payload = deepcopy(dict(intent or {}))
    errors: List[str] = []

    config_result = validateStrategyRiskConfig(cfg)
    errors.extend(config_result["errors"])

    signal_result = validateSignalBundle(
        payload.get("signal_bundle"),
        config=cfg,
        now_kst=now_kst,
    )
    errors.extend(signal_result["errors"])
    signal_bundle = signal_result.get("signal_bundle") or {}

    venue_route = str(payload.get("venue_route") or "").strip()
    if venue_route not in ALLOWED_VENUES:
        errors.append("venue_route_required")

    available_cash = _require_int(payload, "available_cash_krw", errors)
    planned_order_cash = _require_int(payload, "planned_order_cash_krw", errors)
    current_holdings_count = _require_int(payload, "current_holdings_count", errors)
    entry_price = _require_float(payload, "entry_price_krw", errors)

    total_capital = payload.get("total_capital_krw", cfg["starting_capital_krw"])
    if total_capital != cfg["starting_capital_krw"]:
        errors.append("starting_capital_krw_must_match_rulebook")
    total_capital = cfg["starting_capital_krw"]

    execution_mode = str(payload.get("execution_mode") or cfg["execution_mode"]).strip()
    if execution_mode != NO_ORDER_DRY_RUN:
        errors.append("execution_mode_must_be_no_order_dry_run")

    broker_adapter = str(payload.get("broker_adapter") or cfg["broker_adapter"]).strip()
    if broker_adapter != NO_ORDER_DRY_RUN:
        errors.append("broker_adapter_forbidden")
    if _contains_forbidden_execution_token(broker_adapter):
        errors.append("forbidden_broker_route")
    route_hint = str(payload.get("execution_route") or "").strip()
    if route_hint and _contains_forbidden_execution_token(route_hint):
        errors.append("forbidden_broker_route")

    errors.extend(_collect_manual_block_errors(payload))
    errors.extend(_collect_forbidden_simulation_flag_errors(payload))

    if current_holdings_count is not None and current_holdings_count >= cfg["max_simultaneous_holdings"]:
        errors.append("max_simultaneous_holdings_exceeded")

    max_order_cash = None
    projected_cash_after_order = None
    if available_cash is not None and planned_order_cash is not None:
        max_order_cash = computeMaxOrderCashKrw(
            total_capital_krw=total_capital,
            available_cash_krw=available_cash,
            minimum_cash_reserve_ratio=cfg["minimum_cash_reserve_ratio"],
        )
        projected_cash_after_order = available_cash - planned_order_cash
        if planned_order_cash <= 0:
            errors.append("planned_order_cash_must_be_positive")
        if planned_order_cash > max_order_cash:
            errors.append("minimum_cash_reserve_breach")
        if planned_order_cash >= available_cash:
            errors.append("all_in_single_stock_forbidden")

    existing_position_qty = int(payload.get("existing_position_qty") or 0)
    average_entry_price = payload.get("average_entry_price_krw")
    latest_price = payload.get("latest_price_krw")
    add_on_buy = bool(payload.get("add_on_buy"))
    if add_on_buy and existing_position_qty > 0:
        if average_entry_price in (None, "") or latest_price in (None, ""):
            errors.append("averaging_down_forbidden")
        elif float(latest_price) <= float(average_entry_price):
            errors.append("averaging_down_forbidden")

    signal_id = str(signal_bundle.get("signal_id") or "").strip()
    recent_exit_signal_id = str(payload.get("recent_exit_signal_id") or "").strip()
    is_reentry = bool(payload.get("is_reentry")) or bool(recent_exit_signal_id)
    fresh_signal = payload.get("fresh_signal")
    if fresh_signal is None:
        fresh_signal = signal_bundle.get("fresh_signal", True)
    if is_reentry and (
        fresh_signal is not True
        or (recent_exit_signal_id and signal_id and recent_exit_signal_id == signal_id)
    ):
        errors.append("continuous_reentry_without_fresh_signal")

    stop_result = _validate_stop_loss(
        payload.get("stop_loss"),
        entry_price=entry_price,
        cfg=cfg,
        now_kst=now_kst,
    )
    errors.extend(stop_result["errors"])

    target_profit_pct = _resolve_target_profit_pct(payload, entry_price, errors)
    if target_profit_pct is not None:
        target_cfg = cfg["target_band_pct"]
        if not (target_cfg["min"] <= target_profit_pct <= target_cfg["max"]):
            errors.append("target_profit_pct_out_of_band")
        stop_loss_pct = stop_result.get("stop_loss_pct")
        if stop_loss_pct is not None and stop_loss_pct < 0:
            reward_risk = target_profit_pct / abs(stop_loss_pct)
            if reward_risk < cfg["minimum_reward_risk_ratio"]:
                errors.append("reward_risk_ratio_below_minimum")
        else:
            errors.append("stop_loss_required_for_reward_risk")

    return {
        "ok": not errors,
        "errors": errors,
        "intent": payload,
        "signal_bundle": signal_bundle,
        "max_order_cash_krw": max_order_cash,
        "projected_cash_after_order_krw": projected_cash_after_order,
        "stop_loss": stop_result.get("stop_loss"),
        "target_profit_pct": target_profit_pct,
        "config": cfg,
    }


def buildNoOrderDryRunRecord(
    intent: Mapping[str, Any],
    validation_result: Optional[Mapping[str, Any]] = None,
    *,
    config: Optional[Mapping[str, Any]] = None,
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = dict(config or loadStrategyRiskConfig())
    result = (
        deepcopy(dict(validation_result))
        if validation_result is not None
        else validateEntryIntent(intent, config=cfg, now_kst=now_kst)
    )
    payload = deepcopy(dict(intent))
    signal_bundle = deepcopy(dict(result.get("signal_bundle") or payload.get("signal_bundle") or {}))
    stop_loss = deepcopy(dict(result.get("stop_loss") or payload.get("stop_loss") or {}))
    target_profit_pct = result.get("target_profit_pct")

    entry_price = payload.get("entry_price_krw")
    target_price = payload.get("target_price_krw")
    if target_price in (None, "") and entry_price not in (None, "") and target_profit_pct is not None:
        target_price = round(float(entry_price) * (1 + float(target_profit_pct)), 4)

    record = {
        "record_type": "strategy_risk_no_order_dry_run",
        "rulebook_id": cfg["rulebook_id"],
        "execution_mode": NO_ORDER_DRY_RUN,
        "broker_adapter": NO_ORDER_DRY_RUN,
        "decision": "approved" if result.get("ok") else "rejected",
        "symbol": payload.get("symbol"),
        "candidate": {
            "reason": payload.get("candidate_reason") or signal_bundle.get("candidate_reason"),
            "source_path": signal_bundle.get("source_path"),
            "source_ids": signal_bundle.get("source_ids") or [],
            "signal_id": signal_bundle.get("signal_id"),
            "chart_confirmation_reason": signal_bundle.get("chart_confirmation_reason"),
        },
        "entry": {
            "venue_route": payload.get("venue_route"),
            "available_cash_krw": payload.get("available_cash_krw"),
            "planned_order_cash_krw": payload.get("planned_order_cash_krw"),
            "projected_cash_after_order_krw": result.get("projected_cash_after_order_krw"),
            "max_order_cash_krw": result.get("max_order_cash_krw"),
            "entry_price_krw": entry_price,
        },
        "size": {
            "planned_order_cash_krw": payload.get("planned_order_cash_krw"),
            "reserve_ratio_after_order": cfg["minimum_cash_reserve_ratio"],
            "max_simultaneous_holdings": cfg["max_simultaneous_holdings"],
        },
        "stop": {
            "source": stop_loss.get("source"),
            "stop_price_krw": stop_loss.get("stop_price_krw"),
            "validated_max_stop_loss_pct": cfg["max_stop_loss_pct"],
            "auditable": stop_loss.get("auditable"),
        },
        "target": {
            "target_profit_pct": target_profit_pct,
            "target_price_krw": target_price,
            "target_band_label": cfg["target_band_pct"]["label"],
            "minimum_reward_risk_ratio": cfg["minimum_reward_risk_ratio"],
        },
        "hold_window": deepcopy(cfg["holding_window_minutes"]),
        "rejection_reasons": list(result.get("errors") or []),
        "boundary": {
            "broker_call_allowed": False,
            "paper_orders_allowed": False,
            "live_orders_allowed": False,
            "fake_broker_allowed": False,
            "fill_simulation_allowed": False,
            "balance_simulation_allowed": False,
            "pnl_simulation_allowed": False,
        },
    }
    return record


def validateNoOrderDryRunRecord(
    record: Optional[Mapping[str, Any]],
    *,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = dict(config or loadStrategyRiskConfig())
    payload = deepcopy(dict(record or {}))
    errors: List[str] = []

    for required_key in (
        "record_type",
        "execution_mode",
        "broker_adapter",
        "candidate",
        "entry",
        "size",
        "stop",
        "target",
        "hold_window",
        "rejection_reasons",
        "boundary",
    ):
        if required_key not in payload:
            errors.append(f"missing_record_field:{required_key}")

    if payload.get("execution_mode") != NO_ORDER_DRY_RUN:
        errors.append("record_execution_mode_must_be_no_order_dry_run")
    if payload.get("broker_adapter") != NO_ORDER_DRY_RUN:
        errors.append("record_broker_adapter_must_be_no_order_dry_run")

    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), Mapping) else {}
    if not candidate.get("reason"):
        errors.append("record_candidate_reason_required")
    if not candidate.get("source_path"):
        errors.append("record_candidate_source_path_required")

    entry = payload.get("entry") if isinstance(payload.get("entry"), Mapping) else {}
    if not entry.get("venue_route"):
        errors.append("record_entry_venue_route_required")
    if "planned_order_cash_krw" not in entry:
        errors.append("record_entry_size_required")

    stop = payload.get("stop") if isinstance(payload.get("stop"), Mapping) else {}
    if stop.get("source") != "ai":
        errors.append("record_stop_source_must_be_ai")
    if stop.get("stop_price_krw") in (None, ""):
        errors.append("record_stop_price_required")

    target = payload.get("target") if isinstance(payload.get("target"), Mapping) else {}
    if target.get("target_band_label") != cfg["target_band_pct"]["label"]:
        errors.append("record_target_band_label_invalid")

    hold = payload.get("hold_window") if isinstance(payload.get("hold_window"), Mapping) else {}
    if hold.get("hard_max") != cfg["holding_window_minutes"]["hard_max"]:
        errors.append("record_hold_window_hard_max_invalid")

    boundary = payload.get("boundary") if isinstance(payload.get("boundary"), Mapping) else {}
    if boundary.get("broker_call_allowed") is not False:
        errors.append("record_broker_calls_must_be_disabled")
    if boundary.get("paper_orders_allowed") is not False:
        errors.append("record_paper_orders_must_be_disabled")
    if boundary.get("live_orders_allowed") is not False:
        errors.append("record_live_orders_must_be_disabled")
    if boundary.get("fake_broker_allowed") is not False:
        errors.append("record_fake_broker_must_be_disabled")
    if boundary.get("fill_simulation_allowed") is not False:
        errors.append("record_fill_simulation_must_be_disabled")
    if boundary.get("balance_simulation_allowed") is not False:
        errors.append("record_balance_simulation_must_be_disabled")
    if boundary.get("pnl_simulation_allowed") is not False:
        errors.append("record_pnl_simulation_must_be_disabled")

    errors.extend(_collect_forbidden_simulation_flag_errors(payload))

    return {"ok": not errors, "errors": errors, "record": payload}


def computeMaxOrderCashKrw(
    *,
    total_capital_krw: int,
    available_cash_krw: int,
    minimum_cash_reserve_ratio: float,
) -> int:
    reserve = int(total_capital_krw * minimum_cash_reserve_ratio)
    return max(0, int(available_cash_krw) - reserve)


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


def _require_int(payload: Mapping[str, Any], field_name: str, errors: List[str]) -> Optional[int]:
    value = payload.get(field_name)
    if value in (None, ""):
        errors.append(f"{field_name}_required")
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name}_must_be_int")
        return None


def _require_float(payload: Mapping[str, Any], field_name: str, errors: List[str]) -> Optional[float]:
    value = payload.get(field_name)
    if value in (None, ""):
        errors.append(f"{field_name}_required")
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name}_must_be_number")
        return None


def _contains_forbidden_execution_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in FORBIDDEN_EXECUTION_TOKENS)


def _validate_stop_loss(
    stop_loss: Any,
    *,
    entry_price: Optional[float],
    cfg: Mapping[str, Any],
    now_kst: Optional[str],
) -> Dict[str, Any]:
    errors: List[str] = []
    if not isinstance(stop_loss, Mapping):
        return {"errors": ["stop_loss_required"], "stop_loss": {}, "stop_loss_pct": None}

    payload = deepcopy(dict(stop_loss))
    if payload.get("source") != "ai":
        errors.append("ai_stop_required")

    stop_price_raw = payload.get("stop_price_krw")
    if stop_price_raw in (None, ""):
        errors.append("ai_stop_price_required")
        stop_price = None
    else:
        try:
            stop_price = float(stop_price_raw)
        except (TypeError, ValueError):
            errors.append("ai_stop_price_must_be_number")
            stop_price = None

    if payload.get("auditable") is not True:
        errors.append("ai_stop_must_be_auditable")

    proposed_at = _parse_kst_timestamp(payload.get("proposed_at_kst"), "ai_stop_proposed_at_kst", errors)
    reference_now = _parse_kst_timestamp(now_kst, "now_kst", []) if now_kst else proposed_at
    if proposed_at and reference_now:
        age = (reference_now - proposed_at).total_seconds()
        if age > cfg["signal_policy"]["max_stop_age_seconds"]:
            errors.append("ai_stop_stale")

    stop_loss_pct = None
    if stop_price is not None and entry_price not in (None, 0):
        stop_loss_pct = round((stop_price - float(entry_price)) / float(entry_price), 6)
        if stop_loss_pct > 0:
            errors.append("ai_stop_must_be_below_entry")
        if stop_loss_pct < cfg["max_stop_loss_pct"]:
            errors.append("ai_stop_wider_than_minus_5pct")
    elif entry_price in (None, 0):
        errors.append("entry_price_required")

    return {"errors": errors, "stop_loss": payload, "stop_loss_pct": stop_loss_pct}


def _resolve_target_profit_pct(
    payload: Mapping[str, Any],
    entry_price: Optional[float],
    errors: List[str],
) -> Optional[float]:
    target_pct = payload.get("target_profit_pct")
    if target_pct not in (None, ""):
        try:
            return float(target_pct)
        except (TypeError, ValueError):
            errors.append("target_profit_pct_must_be_number")
            return None

    target_price = payload.get("target_price_krw")
    if target_price in (None, ""):
        errors.append("target_profit_pct_or_target_price_required")
        return None
    if entry_price in (None, 0):
        errors.append("entry_price_required_for_target_price")
        return None
    try:
        return (float(target_price) - float(entry_price)) / float(entry_price)
    except (TypeError, ValueError, ZeroDivisionError):
        errors.append("target_price_krw_must_be_number")
        return None


def _collect_forbidden_simulation_flag_errors(payload: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    flattened = _flatten_key_values(payload)
    seen = set()
    for key, value in flattened:
        if key in FORBIDDEN_SIMULATION_FLAGS and value:
            error_code = f"{key}_forbidden"
            if error_code not in seen:
                errors.append(error_code)
                seen.add(error_code)
    return errors


def _collect_manual_block_errors(payload: Mapping[str, Any]) -> List[str]:
    if _manual_block_active(payload):
        return [MANUAL_BLOCK_ERROR]
    return []


def _manual_block_active(payload: Mapping[str, Any]) -> bool:
    for key in MANUAL_BLOCK_FLAGS:
        if payload.get(key) is True:
            return True

    for container_name in MANUAL_BLOCK_CONTAINERS:
        container = payload.get(container_name)
        if isinstance(container, Mapping):
            if container.get("active") is True:
                return True
            for key in MANUAL_BLOCK_FLAGS:
                if container.get(key) is True:
                    return True

    return False


def _flatten_key_values(value: Any, prefix: str = "") -> List[tuple[str, Any]]:
    items: List[tuple[str, Any]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_key = str(key)
            dotted = child_key if not prefix else f"{prefix}.{child_key}"
            items.extend(_flatten_key_values(child, dotted))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            dotted = f"{prefix}[{index}]"
            items.extend(_flatten_key_values(child, dotted))
    else:
        leaf = prefix.rsplit(".", 1)[-1] if prefix else ""
        items.append((leaf, value))
    return items
