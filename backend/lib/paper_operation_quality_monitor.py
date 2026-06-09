"""
hwiStock paper-operation quality monitor.

This monitor is intentionally read-only. It never calls broker, KIS, AI, or
browser providers. It converts the next-session checks from the paper
experiment review into a machine-readable evidence artifact.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, time
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
SCHEMA_VERSION = "paper_operation_quality/v0"
OPEN_CUTOFF = time(9, 10)
ORDER_WINDOW_OPEN = time(9, 0)
ORDER_WINDOW_CLOSE = time(15, 0)
EXIT_TRIGGER_REASONS = frozenset({"target_price_hit", "stop_loss_hit", "hard_max_hold_exceeded"})
EXIT_TRIGGER_STATUSES = frozenset({"target_price_hit", "stop_loss_hit", "hard_max_exceeded"})


def parseKst(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now(KST).replace(microsecond=0)
    parsed = datetime.fromisoformat(str(value).strip())
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _readJson(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _dayPaths(dataRoot: Path, day: str) -> dict[str, str]:
    paths = {
        "kisMarket": dataRoot / "kis-market" / day / "kis-market-snapshot-latest.json",
        "compiledWatch": dataRoot / "compiled-watch" / day / "compiled-watch-latest.json",
        "flashTradeDocument": dataRoot / "trade-documents" / day / "flash-trade-document-latest.json",
        "kisPaperRunner": dataRoot / "evidence" / day / "kis-paper-continuous-latest.json",
    }
    return {key: str(path) for key, path in paths.items() if path.exists()}


def _loadArtifacts(dataRoot: Path, day: str) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    paths = _dayPaths(dataRoot, day)
    artifacts = {key: _readJson(Path(path)) for key, path in paths.items()}
    return paths, artifacts


def _asPositiveInt(value: Any) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _listOfDicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _candidateCount(compiledWatch: Mapping[str, Any], kisMarket: Mapping[str, Any]) -> int:
    for source in (compiledWatch, kisMarket.get("compiled_watch") if isinstance(kisMarket.get("compiled_watch"), Mapping) else None):
        if not isinstance(source, Mapping):
            continue
        count = _asPositiveInt(source.get("candidate_count"))
        if count is not None:
            return count
        items = source.get("items")
        if isinstance(items, list):
            return len(items)
    return 0


def _candidateSource(compiledWatch: Mapping[str, Any], kisMarket: Mapping[str, Any]) -> str:
    if compiledWatch:
        return str(compiledWatch.get("producer") or compiledWatch.get("artifact_type") or "compiled_watch_latest")
    if isinstance(kisMarket.get("compiled_watch"), Mapping):
        return str(kisMarket["compiled_watch"].get("producer") or "kis_market_embedded_compiled_watch")
    return "missing"


def _isOrderWindow(at: datetime) -> bool:
    local = at.astimezone(KST)
    return local.weekday() < 5 and ORDER_WINDOW_OPEN <= local.time() <= ORDER_WINDOW_CLOSE


def _isAfterOpenCutoff(at: datetime) -> bool:
    local = at.astimezone(KST)
    return local.weekday() < 5 and OPEN_CUTOFF <= local.time() <= ORDER_WINDOW_CLOSE


def _containsAnyText(value: Any, needles: Sequence[str]) -> bool:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    return any(needle.lower() in text for needle in needles)


def _pipelineAcceptedIntents(flash: Mapping[str, Any]) -> list[dict[str, Any]]:
    pipeline = flash.get("paper_intent_pipeline")
    if not isinstance(pipeline, Mapping):
        return []
    return _listOfDicts(pipeline.get("accepted_intents"))


def _intentSide(row: Mapping[str, Any]) -> str:
    return str(row.get("side") or row.get("action") or "").strip().lower()


def _intentIsSell(row: Mapping[str, Any]) -> bool:
    return _intentSide(row) in {"sell", "sell_now"} or str(row.get("action") or "").upper() == "SELL_NOW"


def _intentIsBuy(row: Mapping[str, Any]) -> bool:
    return _intentSide(row) in {"buy", "buy_now"} or str(row.get("action") or "").upper() == "BUY_NOW"


def _checkCandidateUniverse(
    *,
    at: datetime,
    compiledWatch: Mapping[str, Any],
    kisMarket: Mapping[str, Any],
) -> dict[str, Any]:
    count = _candidateCount(compiledWatch, kisMarket)
    evaluated = _isAfterOpenCutoff(at)
    status = "pass"
    p0: list[str] = []
    if evaluated and count <= 0:
        status = "p0"
        p0.append("candidate_universe_empty_after_open_cutoff")
    return {
        "status": status if evaluated else "observation_only",
        "evaluated": evaluated,
        "open_cutoff_kst": "09:10",
        "candidate_universe_count": count,
        "candidate_universe_source": _candidateSource(compiledWatch, kisMarket),
        "compiled_watch_produced_at_kst": compiledWatch.get("produced_at_kst"),
        "kis_market_produced_at_kst": kisMarket.get("produced_at_kst"),
        "p0_conditions": p0,
    }


def _checkFlashProvider(*, at: datetime, flash: Mapping[str, Any]) -> dict[str, Any]:
    evaluated = _isAfterOpenCutoff(at)
    p0: list[str] = []
    status = "pass"
    validationStatus = str(flash.get("validation_status") or "missing")
    providerStatus = str(flash.get("provider_status") or "missing")
    documentKind = str(flash.get("document_kind") or "missing")
    noTradeReason = str(flash.get("no_trade_reason") or flash.get("safe_block_reason") or "")
    candidateCount = _asPositiveInt(flash.get("candidate_universe_count")) or 0
    if evaluated and not flash:
        p0.append("flash_trade_document_missing_after_open_cutoff")
    if evaluated and validationStatus == "safe_block" and (
        candidateCount <= 0
        or _containsAnyText(
            [noTradeReason, flash.get("no_trade_reasons"), flash.get("validation_errors"), flash.get("warnings")],
            ["missing_compiled_watch_candidate_universe", "candidate_universe_count", "candidate_universe_empty"],
        )
    ):
        p0.append("flash_safe_block_missing_candidate_universe_after_open_cutoff")
    if evaluated and providerStatus not in {"ok", "accepted", "accepted_with_warnings"} and validationStatus != "safe_block":
        p0.append("flash_provider_not_ok_after_open_cutoff")
    if p0:
        status = "p0"
    return {
        "status": status if evaluated else "observation_only",
        "evaluated": evaluated,
        "produced_at_kst": flash.get("produced_at_kst"),
        "document_kind": documentKind,
        "validation_status": validationStatus,
        "provider_status": providerStatus,
        "no_trade_reason": noTradeReason or None,
        "candidate_universe_source": flash.get("candidate_universe_source"),
        "candidate_universe_count": candidateCount,
        "p0_conditions": p0,
    }


def _checkBuySizing(flash: Mapping[str, Any]) -> dict[str, Any]:
    badActions: list[dict[str, Any]] = []
    buyActions = [row for row in _listOfDicts(flash.get("actions")) if str(row.get("action") or "").upper() == "BUY_NOW"]
    buyIntents = [row for row in _pipelineAcceptedIntents(flash) if _intentIsBuy(row)]
    for row in [*buyActions, *buyIntents]:
        symbol = str(row.get("symbol") or row.get("ticker") or row.get("name") or "").strip()
        positionPct = _asPositiveInt(row.get("position_size_pct"))
        sizingBasis = str(row.get("sizing_basis") or "").strip()
        plannedSource = str(row.get("planned_order_cash_source") or "").strip()
        if positionPct is None or ("position_size_pct" not in sizingBasis and plannedSource != "position_size_pct"):
            badActions.append(
                {
                    "symbol": symbol or None,
                    "action": row.get("action") or row.get("side"),
                    "position_size_pct": row.get("position_size_pct"),
                    "sizing_basis": sizingBasis or None,
                    "planned_order_cash_source": plannedSource or None,
                }
            )
    return {
        "status": "p0" if badActions else "pass",
        "buy_action_count": len(buyActions),
        "buy_intent_count": len(buyIntents),
        "bad_sizing_count": len(badActions),
        "bad_sizing_actions": badActions,
        "p0_conditions": ["buy_order_missing_position_size_pct_basis"] if badActions else [],
    }


def _positionExitTriggered(row: Mapping[str, Any]) -> bool:
    reason = str(row.get("time_exit_reason") or "").strip()
    status = str(row.get("time_exit_status") or "").strip()
    return reason in EXIT_TRIGGER_REASONS or status in EXIT_TRIGGER_STATUSES


def _checkSellPipeline(flash: Mapping[str, Any]) -> dict[str, Any]:
    positionActions = _listOfDicts(flash.get("position_actions"))
    triggered = [row for row in positionActions if bool(row.get("order_window_open")) and _positionExitTriggered(row)]
    blocked = [
        {
            "symbol": row.get("symbol") or row.get("ticker"),
            "action": row.get("action"),
            "time_exit_status": row.get("time_exit_status"),
            "time_exit_reason": row.get("time_exit_reason"),
            "exit_blocked_reason": row.get("exit_blocked_reason"),
            "sellable_truth_status": row.get("sellable_truth_status"),
            "sellable_truth_accepted": row.get("sellable_truth_accepted"),
            "current_price": row.get("current_price"),
        }
        for row in triggered
        if str(row.get("action") or "").upper() != "SELL_NOW"
    ]
    sellNowCount = sum(1 for row in positionActions if str(row.get("action") or "").upper() == "SELL_NOW")
    sellIntents = [row for row in _pipelineAcceptedIntents(flash) if _intentIsSell(row)]
    p0: list[str] = []
    if blocked:
        p0.append("exit_trigger_without_sell_now")
    if sellNowCount > 0 and not sellIntents:
        p0.append("sell_now_without_accepted_sell_intent")
    return {
        "status": "p0" if p0 else "pass",
        "triggered_position_count": len(triggered),
        "sell_now_count": sellNowCount,
        "accepted_sell_intent_count": len(sellIntents),
        "blocked_position_actions": blocked,
        "p0_conditions": p0,
    }


def _stepRows(runner: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _listOfDicts(runner.get("steps"))


def _runnerErrors(runner: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    preflight = runner.get("executionPreflight")
    if isinstance(preflight, Mapping):
        errors.extend(str(item) for item in (preflight.get("errors") or []) if item)
    for step in _stepRows(runner):
        errors.extend(str(item) for item in (step.get("errors") or []) if item)
        reason = step.get("reason")
        if reason:
            errors.append(str(reason))
    return errors


def _checkRunnerSellExecution(*, at: datetime, runner: Mapping[str, Any]) -> dict[str, Any]:
    activeWindow = _isOrderWindow(at)
    loaded = runner.get("loaded_intent") if isinstance(runner.get("loaded_intent"), Mapping) else {}
    loadedIsSell = bool(loaded) and _intentIsSell(loaded)
    cashOrders = [row for row in _stepRows(runner) if row.get("step") == "cash_order"]
    cashBrokerCalled = any(row.get("broker_endpoint_called") is True for row in cashOrders)
    errors = _runnerErrors(runner)
    p0: list[str] = []
    if activeWindow and loadedIsSell:
        if any("sellable_truth_not_accepted" in error for error in errors):
            p0.append("sell_intent_blocked_by_sellable_truth")
        if not cashBrokerCalled:
            p0.append("sell_intent_did_not_reach_cash_order_broker_endpoint")
    if any("trade_document_already_consumed" in error for error in errors):
        p0.append("sibling_intent_blocked_by_trade_document_already_consumed")
    return {
        "status": "p0" if p0 else "pass",
        "evaluated_order_window": activeWindow,
        "intent_loaded": bool(runner.get("intent_loaded")),
        "loaded_intent_side": loaded.get("side") if loaded else None,
        "loaded_intent_symbol": loaded.get("symbol") if loaded else None,
        "base_runner_order_gate": runner.get("base_runner_order_gate"),
        "cash_order_step_count": len(cashOrders),
        "cash_order_broker_endpoint_called": cashBrokerCalled,
        "sellable_truth_accepted": (
            runner.get("account_truth", {}).get("sellable_truth_accepted")
            if isinstance(runner.get("account_truth"), Mapping)
            else None
        ),
        "detected_errors": sorted(set(errors)),
        "p0_conditions": p0,
    }


def evaluatePaperOperationQuality(
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    at: Optional[datetime] = None,
) -> dict[str, Any]:
    now = at or datetime.now(KST).replace(microsecond=0)
    day = now.astimezone(KST).date().isoformat()
    paths, artifacts = _loadArtifacts(data_root, day)
    compiledWatch = artifacts.get("compiledWatch") or {}
    kisMarket = artifacts.get("kisMarket") or {}
    flash = artifacts.get("flashTradeDocument") or {}
    runner = artifacts.get("kisPaperRunner") or {}
    checks = {
        "candidate_universe": _checkCandidateUniverse(at=now, compiledWatch=compiledWatch, kisMarket=kisMarket),
        "flash_provider": _checkFlashProvider(at=now, flash=flash),
        "buy_sizing": _checkBuySizing(flash),
        "sell_pipeline": _checkSellPipeline(flash),
        "runner_sell_execution": _checkRunnerSellExecution(at=now, runner=runner),
    }
    p0Conditions: list[str] = []
    warnings: list[str] = []
    for check in checks.values():
        p0Conditions.extend(str(item) for item in (check.get("p0_conditions") or []))
        if check.get("status") == "observation_only":
            warnings.append("off_session_or_before_open_cutoff_observation_only")
    status = "p0" if p0Conditions else ("warn" if warnings else "pass")
    return {
        "schema_version": SCHEMA_VERSION,
        "event": "paper_operation_quality_check",
        "produced_at_kst": now.astimezone(KST).isoformat(),
        "target_date_kst": day,
        "status": status,
        "p0_conditions": sorted(set(p0Conditions)),
        "warnings": sorted(set(warnings)),
        "broker_calls_enabled": False,
        "orders_enabled": False,
        "no_broker_call": True,
        "checks": checks,
        "artifact_paths": paths,
    }


def writePaperOperationQualityEvidence(
    payload: Mapping[str, Any],
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    at: Optional[datetime] = None,
) -> dict[str, str]:
    now = at or parseKst(str(payload.get("produced_at_kst") or ""))
    day = now.astimezone(KST).date().isoformat()
    evidenceDir = data_root / "evidence" / day
    evidenceDir.mkdir(parents=True, exist_ok=True)
    latest = evidenceDir / "paper-operation-quality-latest.json"
    stamped = evidenceDir / f"paper-operation-quality-{now.strftime('%H%M%S')}.json"
    text = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    latest.write_text(text, encoding="utf-8")
    stamped.write_text(text, encoding="utf-8")
    return {"latest_path": str(latest), "stamped_path": str(stamped)}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only hwiStock paper-operation quality monitor")
    parser.add_argument("--at-kst", help="Evaluation time in KST ISO format")
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT), help="hwiStock runtime data root")
    parser.add_argument("--write-evidence", action="store_true", help="Write latest/stamped evidence JSON")
    parser.add_argument("--fail-on-p0", action="store_true", help="Exit 1 when P0 conditions are detected")
    args = parser.parse_args(list(argv) if argv is not None else None)
    now = parseKst(args.at_kst) if args.at_kst else datetime.now(KST).replace(microsecond=0)
    payload = evaluatePaperOperationQuality(data_root=Path(args.data_root), at=now)
    if args.write_evidence:
        payload["evidence_paths"] = writePaperOperationQualityEvidence(payload, data_root=Path(args.data_root), at=now)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.fail_on_p0 and payload.get("status") == "p0" else 0


if __name__ == "__main__":
    raise SystemExit(main())
