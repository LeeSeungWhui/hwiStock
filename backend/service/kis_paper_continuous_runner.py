"""
Continuous KIS paper/mock runner for HWISTOCK-UNIT-010.

The service is duration-agnostic. It writes observation-window metadata and can
run bounded KIS paper actions only when explicitly enabled. No live domain, fake
broker state, AI provider call, or public exposure is performed here.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
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


def _now_kst() -> datetime:
    return datetime.now(KST).replace(microsecond=0)


def _bool_env(env: Mapping[str, str], key: str, default: bool = False) -> bool:
    raw = str(env.get(key, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


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
        },
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
    status = base_runner.get_runner_status(at_kst)
    now = _now_kst()
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

    token_result, token = adapter.issueTokenWithValue()
    result["steps"].append(token_result)
    if not token_result.get("token_present") or not token:
        result["status"] = "blocked_token_missing"
        return result

    sample_symbol = str(source.get("HWISTOCK_KIS_HEALTH_SYMBOL", "005930")).strip() or "005930"
    result["steps"].append(adapter.inquirePrice(token, sample_symbol))
    result["steps"].append(adapter.inquireBalance(token))
    result["steps"].append(adapter.inquireBuyable(token, sample_symbol))
    result["steps"].append(adapter.dailyOrderFillLookup(token, date_yyyymmdd=now.strftime("%Y%m%d")))

    if intent:
        risk = evaluatePaperRiskOverlay(intent, status=status)
        result["riskOverlay"] = risk
        if not risk["ok"]:
            result["steps"].append({"step": "cash_order", "status": "blocked_risk_overlay", "errors": risk["errors"]})
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
            result["steps"].append(adapter.placeCashOrder(token, intent))

    result["steps"].append(adapter.revokeToken(token))
    result["status"] = "ok" if not any(step.get("status") in {"fail"} for step in result["steps"]) else "fail"
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
    if "\n" in text:
        text = text.splitlines()[0]
    return dict(json.loads(text))


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
    intent = _load_intent_file(args.intent_file)
    payload = runContinuousPaperTick(intent=intent, env=env)
    if args.write_evidence:
        payload["evidencePaths"] = writeContinuousPaperEvidence(payload, data_root=Path(args.output_root))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
