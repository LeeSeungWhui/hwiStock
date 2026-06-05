"""
Continuous KIS paper/mock runtime implementation for HWISTOCK-UNIT-010.

The service is duration-agnostic. It writes observation-window metadata and can
run bounded KIS paper actions only when explicitly enabled. No live domain, fake
broker state, AI provider call, or public exposure is performed here.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    from lib.kis_paper_token_cache import loadKisPaperAccessToken, tokenCacheRevokeSkippedStep
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
    from backend.lib.kis_paper_token_cache import loadKisPaperAccessToken, tokenCacheRevokeSkippedStep
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


def loadContinuousPaperRunnerConfig(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    return {
        "runner_id": "hwistock-kis-paper-continuous-runner",
        "schema_version": "kis_paper_continuous_runner_config/v0",
        "duration_policy": "operator_selected",
        "fixed_duration_days": None,
        "auto_stop_on_duration": False,
        "auto_pass_on_duration": False,
        "auto_fail_on_duration": False,
        "paper_network_enabled": _bool_env(source, "HWISTOCK_KIS_PAPER_NETWORK_ENABLED", False),
        "paper_order_enabled": _bool_env(source, "HWISTOCK_KIS_PAPER_ORDER_ENABLED", False),
        "intent_file": str(source.get("HWISTOCK_KIS_PAPER_INTENT_FILE", "")).strip(),
        "data_root": str(source.get("HWISTOCK_DATA_DIR", str(DEFAULT_DATA_ROOT))).strip(),
        "state_file": str(source.get("HWISTOCK_KIS_PAPER_STATE_FILE", "")).strip(),
        "min_call_gap_sec": _float_env(source, "HWISTOCK_KIS_MIN_CALL_GAP_SEC", 1.35),
        "paper_env": describeKisPaperEnv(source),
        "capabilities": loadKisPaperCapabilityFlags(),
    }


def evaluatePaperRiskOverlay(
    intent: Optional[Mapping[str, Any]],
    *,
    status: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    payload = dict(intent or {})
    runner_status = dict(status or base_runner.get_runner_status())
    errors = []
    route = str(payload.get("venue_route") or payload.get("venue") or runner_status.get("routing", {}).get("venue") or "").upper()
    session_venue = str(runner_status.get("routing", {}).get("venue") or "").upper()
    available_cash = int(payload.get("available_cash_krw") or 0)
    planned_cash = int(payload.get("planned_order_cash_krw") or 0)
    current_holdings = int(payload.get("current_holdings_count") or 0)
    reserve_floor = int(base_runner.LIVE_CAPITAL_BASELINE_KRW * 0.25)

    if runner_status.get("killSwitch", {}).get("active"):
        errors.append("kill_switch_active")
    if runner_status.get("calendar", {}).get("tradingAllowed") is not True:
        errors.append("calendar_not_ready")
    if runner_status.get("routing", {}).get("venue") == "idle":
        errors.append("off_session")
    if session_venue != "KRX":
        errors.append("kis_paper_order_requires_krx_regular_session")
    if route != "KRX":
        errors.append("kis_paper_order_route_must_be_krx")
    if current_holdings >= 5:
        errors.append("max_simultaneous_holdings_exceeded")
    if planned_cash <= 0:
        errors.append("planned_order_cash_must_be_positive")
    if available_cash <= 0:
        errors.append("available_cash_required")
    if available_cash and planned_cash and available_cash - planned_cash < reserve_floor:
        errors.append("minimum_cash_reserve_breach")

    return {
        "ok": not errors,
        "errors": errors,
        "risk_overlay": {
            "capital_mode": "cash_only",
            "live_capital_baseline_krw": base_runner.LIVE_CAPITAL_BASELINE_KRW,
            "minimum_cash_reserve_ratio": 0.25,
            "reserve_floor_krw": reserve_floor,
            "max_simultaneous_holdings": 5,
            "route": route,
            "session_venue": session_venue,
        },
    }


def resetContinuousPaperRunnerForTests() -> None:
    _CONSUMED_INTENT_KEYS.clear()


def evaluateIntentExecutionPreflight(
    intent: Optional[Mapping[str, Any]],
    *,
    portfolio_snapshot: Optional[Mapping[str, Any]] = None,
    order_state_snapshot: Optional[Mapping[str, Any]] = None,
    status: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    payload = dict(intent or {})
    portfolio = dict(portfolio_snapshot or {})
    order_state = dict(order_state_snapshot or {})
    errors: list[str] = []
    if payload.get("schema_version") not in (None, "paper_order_intent/v0"):
        errors.append("intent_schema_invalid")
    if payload.get("paper_only") is not True and payload.get("broker_adapter") == "kis_live":
        errors.append("paper_only_guard_failed")
    if str(payload.get("venue_route") or payload.get("venue") or "").upper() != "KRX":
        errors.append("kis_paper_order_route_must_be_krx")
    symbol = str(payload.get("symbol") or payload.get("ticker") or "").strip()
    if not symbol:
        errors.append("symbol_required")
    held = _symbol_set_from_snapshot(portfolio, "holdings")
    pending = _symbol_set_from_snapshot(order_state, "pending_orders")
    exits = _symbol_set_from_snapshot(order_state, "active_exits")
    consumed_docs = {
        str(item or "").strip()
        for item in (order_state.get("consumed_trade_document_ids") or [])
        if str(item or "").strip()
    }
    if symbol and symbol in held and str(payload.get("side") or "buy").lower() == "buy":
        errors.append("already_holding_symbol")
    if symbol and symbol in pending:
        errors.append("pending_order_exists")
    if symbol and symbol in exits:
        errors.append("active_exit_order_exists")
    doc_ref = str(payload.get("flash_trade_document_ref") or "").strip()
    if doc_ref and doc_ref in consumed_docs:
        errors.append("trade_document_already_consumed")
    expiry = _parse_optional_kst_timestamp(payload.get("valid_until_kst") or payload.get("valid_until"))
    reference_now = _status_reference_datetime(status)
    if expiry and expiry <= reference_now:
        errors.append("intent_expired")
    risk = evaluatePaperRiskOverlay(payload, status=status)
    errors.extend(risk.get("errors") or [])
    idempotency_key = str(payload.get("idempotency_key") or payload.get("intent_id") or "").strip()
    if not idempotency_key:
        errors.append("idempotency_key_required")
    if idempotency_key and idempotency_key in _CONSUMED_INTENT_KEYS:
        errors.append("duplicate_intent_idempotency_key")
    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "idempotency_key": idempotency_key,
        "symbol": symbol,
        "riskOverlay": risk,
        "broker_endpoint_called": False,
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


def evaluateContinuousPaperRunnerStatus(
    *,
    at_kst: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    config = loadContinuousPaperRunnerConfig(env)
    status = base_runner.get_runner_status(at_kst)
    return {
        "runnerId": config["runner_id"],
        "mode": "kis_paper_mock",
        "continuousService": True,
        "paperRunReady": False,
        "operationalTradingReadiness": False,
        "durationPolicy": {
            "type": config["duration_policy"],
            "fixedDurationDays": config["fixed_duration_days"],
            "autoStopOnDuration": config["auto_stop_on_duration"],
            "autoPassOnDuration": config["auto_pass_on_duration"],
            "autoFailOnDuration": config["auto_fail_on_duration"],
        },
        "paperNetworkEnabled": config["paper_network_enabled"],
        "paperOrderEnabled": config["paper_order_enabled"],
        "paperEnv": config["paper_env"],
        "capabilities": config["capabilities"],
        "baseRunner": {
            "orderGate": status["orderGate"],
            "routing": status["routing"],
            "calendar": status["calendar"],
            "killSwitch": status["killSwitch"],
        },
    }


def runContinuousPaperTick(
    *,
    intent: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
    adapter: Optional[KisPaperAdapter] = None,
    at_kst: Optional[str] = None,
) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    config = loadContinuousPaperRunnerConfig(source)
    status = _status_with_env_overrides(base_runner.get_runner_status(at_kst), source, at_kst=at_kst)
    now = _now_kst()
    reference_now = _parse_optional_kst_timestamp(at_kst) or now
    data_root = Path(config["data_root"])
    local_state = _load_runner_state(config, data_root=data_root)
    intent_source = "explicit_argument" if intent else "none"
    if intent is None:
        loaded = _load_latest_intent_from_queue(data_root=data_root, at=reference_now, state=local_state)
        intent = loaded.get("intent")
        intent_source = str(loaded.get("source") or "none")
    result: Dict[str, Any] = {
        "event": "kis_paper_continuous_tick",
        "timestamp_kst": now.isoformat(),
        "runner_id": config["runner_id"],
        "continuous_service": True,
        "duration_policy": "operator_selected",
        "fixed_duration_days": None,
        "paper_network_enabled": config["paper_network_enabled"],
        "paper_order_enabled": config["paper_order_enabled"],
        "paper_domain_only": True,
        "live_domain_calls_made": False,
        "ai_provider_calls_made": False,
        "public_dashboard_exposed": False,
        "fake_broker_used": False,
        "credential_values_printed": False,
        "raw_responses_stored": False,
        "status": "pending",
        "intent_source": intent_source,
        "intent_loaded": bool(intent),
        "base_runner_order_gate": status["orderGate"],
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

    sample_symbol = str(source.get("HWISTOCK_KIS_HEALTH_SYMBOL", "005930")).strip() or "005930"
    result["steps"].append(adapter.inquirePrice(token, sample_symbol))
    _sleepForKisCallGap(config)
    result["steps"].append(adapter.inquireBalance(token))
    _sleepForKisCallGap(config)
    result["steps"].append(adapter.inquireBuyable(token, sample_symbol))
    _sleepForKisCallGap(config)
    result["steps"].append(adapter.dailyOrderFillLookup(token, date_yyyymmdd=now.strftime("%Y%m%d")))
    _sleepForKisCallGap(config)

    if intent:
        local_order_state = _order_state_snapshot_from_runner_state(local_state, now=now)
        preflight = evaluateIntentExecutionPreflight(intent, order_state_snapshot=local_order_state, status=status)
        result["executionPreflight"] = preflight
        result["riskOverlay"] = preflight.get("riskOverlay")
        if not preflight["ok"]:
            result["steps"].append({"step": "cash_order", "status": "blocked_risk_overlay", "errors": preflight["errors"]})
        elif not config["paper_order_enabled"]:
            result["steps"].append(
                {
                    "step": "cash_order",
                    "status": "blocked_paper_order_disabled",
                    "broker_endpoint_called": False,
                    "reason": "HWISTOCK_KIS_PAPER_ORDER_ENABLED_false",
                }
            )
        else:
            cash_order = adapter.placeCashOrder(token, intent)
            result["steps"].append(cash_order)
            if _broker_step_passed(cash_order):
                key = str(intent.get("idempotency_key") or intent.get("intent_id") or "")
                markIntentConsumed(key)
                _mark_runner_state_submitted(local_state, intent, cash_order, now=now)
                _write_runner_state(local_state, config, data_root=data_root)
            else:
                result["steps"].append(
                    {
                        "step": "local_state",
                        "status": "not_marked_consumed",
                        "reason": "cash_order_not_passed",
                        "broker_status": cash_order.get("status"),
                    }
                )

    if token_cache_managed:
        result["steps"].append(tokenCacheRevokeSkippedStep())
    else:
        result["steps"].append(adapter.revokeToken(token))
    step_statuses = {str(step.get("status") or "") for step in result["steps"]}
    if "fail" in step_statuses:
        result["status"] = "fail"
    elif "warn" in step_statuses or "not_marked_consumed" in step_statuses:
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


def _load_latest_intent_from_queue(
    *,
    data_root: Path,
    at: datetime,
    state: Mapping[str, Any],
) -> Dict[str, Any]:
    path = data_root / "intents" / at.date().isoformat() / "paper-order-intents-latest.jsonl"
    if not path.is_file():
        return {"intent": None, "source": "latest_intent_queue_missing", "path": str(path)}
    consumed = {
        str(item or "").strip()
        for item in (state.get("consumed_intent_keys") or [])
        if str(item or "").strip()
    }
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
    for row in rows:
        key = str(row.get("idempotency_key") or row.get("intent_id") or "").strip()
        if key and key in consumed:
            continue
        expiry = _parse_optional_kst_timestamp(row.get("valid_until_kst") or row.get("valid_until"))
        if expiry and expiry <= at:
            continue
        return {"intent": row, "source": "latest_intent_queue", "path": str(path)}
    return {"intent": None, "source": "latest_intent_queue_empty_or_expired", "path": str(path)}


def _runner_state_path(config: Mapping[str, Any], *, data_root: Path) -> Path:
    override = str(config.get("state_file") or "").strip()
    if override:
        path = Path(override)
        return path if path.is_absolute() else data_root / override
    return data_root / "state" / "kis-paper-runner-state.json"


def _load_runner_state(config: Mapping[str, Any], *, data_root: Path) -> Dict[str, Any]:
    path = _runner_state_path(config, data_root=data_root)
    if not path.is_file():
        return {
            "schema_version": "kis_paper_runner_state/v0",
            "consumed_intent_keys": [],
            "consumed_trade_document_ids": [],
            "pending_orders": [],
            "last_updated_kst": None,
        }
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        parsed = {}
    state = dict(parsed) if isinstance(parsed, Mapping) else {}
    state.setdefault("schema_version", "kis_paper_runner_state/v0")
    state.setdefault("consumed_intent_keys", [])
    state.setdefault("consumed_trade_document_ids", [])
    state.setdefault("pending_orders", [])
    return state


def _write_runner_state(state: Mapping[str, Any], config: Mapping[str, Any], *, data_root: Path) -> None:
    path = _runner_state_path(config, data_root=data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(state), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


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
        "active_exits": [],
        "cooldowns": [],
        "consumed_trade_document_ids": [
            str(item)
            for item in (state.get("consumed_trade_document_ids") or [])
            if str(item).strip()
        ],
    }


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
    if doc_ref:
        state["consumed_trade_document_ids"] = sorted(set([*(state.get("consumed_trade_document_ids") or []), doc_ref]))
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
            "quantity": intent.get("quantity"),
            "order_price": intent.get("order_price") or intent.get("price"),
            "idempotency_key": key,
            "flash_trade_document_ref": doc_ref,
            "submitted_at_kst": now.isoformat(),
            "broker_status": cash_order.get("status"),
            "broker_endpoint_called": bool(cash_order.get("broker_endpoint_called")),
        }
    )
    state["pending_orders"] = pending
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
            "tradingLoopsActive": market_source in {"kis_paper_mock", "kis_paper_read", "kis_market_six_input"},
            "reason": "runner env market-data source override",
        }

    if _bool_env(env, "HWISTOCK_ALLOW_WEEKDAY_CALENDAR_FALLBACK", False):
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
