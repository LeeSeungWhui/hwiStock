"""
hwiStock read-only operator console runtime.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from service import HwiStockRunnerService as baseRunner

KST = ZoneInfo("Asia/Seoul")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
DEFAULT_RUNNER_SERVICE_PATHS = (
    Path.home() / ".config" / "systemd" / "user" / "hwistock-kis-paper-runner.service",
    REPO_ROOT / "ops" / "systemd" / "user" / "hwistock-kis-paper-runner.service",
)


def parseKstTime(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now(KST).replace(microsecond=0)
    parsedAt = datetime.fromisoformat(value)
    if parsedAt.tzinfo is None:
        return parsedAt.replace(tzinfo=KST)
    return parsedAt.astimezone(KST)


def latestRuntimePaths(root: Path, day: str) -> Dict[str, Optional[str]]:
    artifactPathByKey = {
        "marketIntelligence": root / "normalized" / day / "events.jsonl",
        "ai": root / "ai" / day / "pro-hourly-latest.json",
        "flashTradeDocument": root / "trade-documents" / day / "flash-trade-document-latest.json",
        "kisMarket": root / "kis-market" / day / "kis-market-snapshot-latest.json",
        "kisPaperRunner": root / "evidence" / day / "kis-paper-continuous-latest.json",
        "runner": root / "evidence" / day / "runner-latest.json",
    }
    return {
        artifactKey: str(artifactPath) if artifactPath.exists() else None
        for artifactKey, artifactPath in artifactPathByKey.items()
    }


def pathStatus(path: Optional[str]) -> str:
    return "present" if path else "missing_or_safe_blocked"


def timelineFromLatest(latestArtifactPaths: Dict[str, Optional[str]]) -> list[Dict[str, str]]:
    timelineRows: list[Dict[str, str]] = []
    for artifactKey, artifactPath in latestArtifactPaths.items():
        timelineRows.append(
            {
                "at": date.today().isoformat(),
                "source": artifactKey,
                "title": "artifact present" if artifactPath else "artifact missing or safe-blocked",
            }
        )
    return timelineRows


def inspectKisPaperRunnerServicePolicy(
    serviceUnitPaths: Optional[list[Path]] = None,
) -> Dict[str, Any]:
    paths = serviceUnitPaths or list(DEFAULT_RUNNER_SERVICE_PATHS)
    inspected: list[Dict[str, Any]] = []
    paperNetworkEnabled = False
    paperOrderEnabled = False
    for unitPath in paths:
        path = Path(unitPath)
        record = {
            "path": str(path),
            "present": path.is_file(),
            "allowPaperNetworkFlag": False,
            "allowPaperOrdersFlag": False,
            "paperOrderEnvTrue": False,
            "paperOrderEnvFalse": False,
        }
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                text = ""
            record["allowPaperNetworkFlag"] = "--allow-paper-network" in text
            record["allowPaperOrdersFlag"] = "--allow-paper-orders" in text
            normalized = text.replace(" ", "").lower()
            record["paperOrderEnvTrue"] = "environment=hwistock_kis_paper_order_enabled=true" in normalized
            record["paperOrderEnvFalse"] = "environment=hwistock_kis_paper_order_enabled=false" in normalized
            if record["allowPaperNetworkFlag"]:
                paperNetworkEnabled = True
            if record["allowPaperOrdersFlag"] or record["paperOrderEnvTrue"]:
                paperOrderEnabled = True
        inspected.append(record)
    return {
        "schema_version": "kis_paper_runner_service_policy/v0",
        "serviceFiles": inspected,
        "paperNetworkEnabledByService": paperNetworkEnabled,
        "paperOrderEnabledByService": paperOrderEnabled,
        "orderFlagContradictsReadiness": False,
    }


def buildReadinessTruthPanel(
    *,
    runnerStatus: Dict[str, Any],
    latestArtifactPaths: Dict[str, Optional[str]],
    servicePolicy: Optional[Dict[str, Any]] = None,
    paperNetworkEnabled: bool = False,
    paperOrderEnabled: bool = False,
    paperOrdersSubmitted: bool = False,
    paperObservationAccepted: bool = False,
    operationalTradingReadiness: bool = False,
) -> Dict[str, Any]:
    policy = servicePolicy or {}
    fallbackArtifactKeys = [
        artifactKey
        for artifactKey, artifactPath in latestArtifactPaths.items()
        if not artifactPath
    ]
    blockerList = []
    if not paperNetworkEnabled:
        blockerList.append("paper_network_disabled")
    if not paperOrdersSubmitted:
        blockerList.append("paper_orders_not_submitted")
    if not paperObservationAccepted:
        blockerList.append("paper_observation_not_accepted")
    if not operationalTradingReadiness:
        blockerList.append("operational_trading_readiness_false")
    orderGate = runnerStatus.get("orderGate")
    if orderGate and orderGate != "no_order_dry_run_only":
        blockerList.append(str(orderGate))
    if fallbackArtifactKeys:
        blockerList.append("artifact_missing_or_safe_blocked")
    if paperOrderEnabled and not operationalTradingReadiness:
        blockerList.append("systemd_order_enabled_contradicts_readiness")
    return {
        "headline": "NOT_READY_FOR_PAPER_TRADING",
        "severity": "danger",
        "operatorMessage": (
            "서비스/타이머/대시보드가 보여도 모의매매 관찰 준비 완료가 아닙니다. "
            "paper network, order submission, observation acceptance, order gate를 모두 확인해야 합니다."
        ),
        "blockers": blockerList,
        "paperNetworkEnabled": paperNetworkEnabled,
        "paperOrderEnabled": paperOrderEnabled,
        "paperOrdersSubmitted": paperOrdersSubmitted,
        "paperObservationAccepted": paperObservationAccepted,
        "operationalTradingReadiness": operationalTradingReadiness,
        "orderGate": orderGate,
        "servicePolicy": policy,
        "fallbackArtifactKeys": fallbackArtifactKeys,
        "serviceVisibilityIsNotReadiness": True,
    }


def buildOperatorConsoleSnapshot(
    atKst: Optional[str] = None,
    *,
    dataRoot: Optional[Path] = None,
    serviceUnitPaths: Optional[list[Path]] = None,
) -> Dict[str, Any]:
    snapshotAt = parseKstTime(atKst)
    runtimeRoot = dataRoot or DEFAULT_DATA_ROOT
    dayKey = snapshotAt.astimezone(KST).date().isoformat()
    runnerStatus = baseRunner.get_runner_status(snapshotAt.strftime("%Y-%m-%dT%H:%M:%S"))
    latestArtifactPaths = latestRuntimePaths(runtimeRoot, dayKey)
    servicePolicy = inspectKisPaperRunnerServicePolicy(serviceUnitPaths)
    readiness = runnerStatus["readiness"]
    paperNetworkEnabled = bool(servicePolicy["paperNetworkEnabledByService"])
    paperOrderEnabled = bool(servicePolicy["paperOrderEnabledByService"])
    paperOrdersSubmitted = False
    paperObservationAccepted = readiness["paperObservationAccepted"]
    operationalTradingReadiness = readiness["liveRunnerReady"]
    servicePolicy = {
        **servicePolicy,
        "orderFlagContradictsReadiness": paperOrderEnabled and not operationalTradingReadiness,
    }
    readinessTruth = buildReadinessTruthPanel(
        runnerStatus=runnerStatus,
        latestArtifactPaths=latestArtifactPaths,
        servicePolicy=servicePolicy,
        paperNetworkEnabled=paperNetworkEnabled,
        paperOrderEnabled=paperOrderEnabled,
        paperOrdersSubmitted=paperOrdersSubmitted,
        paperObservationAccepted=paperObservationAccepted,
        operationalTradingReadiness=operationalTradingReadiness,
    )
    return {
        "schema_version": "operator_console_snapshot/v0",
        "snapshot_at_kst": snapshotAt.isoformat(),
        "status": {
            "mode": runnerStatus["mode"],
            "sessionKst": f"{runnerStatus['routing']['session']} · {snapshotAt.strftime('%H:%M')}",
            "venueRoute": runnerStatus["routing"]["venue"],
            "killSwitch": "on" if runnerStatus["killSwitch"]["active"] else "off",
            "serviceHealth": "observable",
            "dataSourceHealth": "configured" if runnerStatus["marketData"]["state"] == "source_configured" else "blocked",
            "orderGate": runnerStatus["orderGate"],
        },
        "summary": {
            "accountId": "paper_account_alias:masked",
            "cashBalance": "masked",
            "reserveBalance": "masked",
            "todayPnl": "system_report_only",
            "openPositions": 0,
            "riskRejects": 0,
            "aiJobStatus": pathStatus(latestArtifactPaths.get("ai")),
            "reportStatus": "operator_window_required",
            "paperNetworkEnabled": paperNetworkEnabled,
            "paperOrderEnabled": paperOrderEnabled,
            "paperOrdersSubmitted": paperOrdersSubmitted,
            "paperObservationAccepted": paperObservationAccepted,
            "operationalTradingReadiness": operationalTradingReadiness,
        },
        "readinessTruth": readinessTruth,
        "runtime": {
            "serviceTimers": [
                {"name": "hwistock-intel-collector.timer", "scope": "user", "status": "configured_or_external"},
                {"name": "hwistock-ai-analysis.timer", "scope": "user", "status": "configured_or_external"},
                {"name": "hwistock-ai-flash.timer", "scope": "user", "status": "configured_or_external"},
                {"name": "hwistock-kis-market-data.timer", "scope": "user", "status": "configured_or_external"},
                {"name": "hwistock-kis-paper-runner.timer", "scope": "user", "status": "configured_or_external"},
            ],
            "latestEvidencePaths": latestArtifactPaths,
            "kisPaperRunnerServicePolicy": servicePolicy,
            "localOnly": True,
            "publicBind": False,
        },
        "holdings": [],
        "candidates": [],
        "intelligence": timelineFromLatest(latestArtifactPaths),
        "aiThread": [
            {
                "at": snapshotAt.strftime("%H:%M"),
                "role": "report",
                "subject": "read-only runtime status",
                "body": "AI artifacts are analysis/trade-document files only; no AI artifact can submit broker orders.",
            }
        ],
        "auditLog": [
            {"at": snapshotAt.strftime("%H:%M"), "level": "info", "code": "ORDER_GATE", "message": runnerStatus["orderGate"]},
            {"at": snapshotAt.strftime("%H:%M"), "level": "info", "code": "READ_ONLY", "message": "dashboard exposes no buy/sell/live controls"},
            {
                "at": snapshotAt.strftime("%H:%M"),
                "level": "warn" if paperOrderEnabled else "info",
                "code": "SYSTEMD_ORDER_FLAG",
                "message": "enabled" if paperOrderEnabled else "disabled",
            },
            {"at": snapshotAt.strftime("%H:%M"), "level": "warn", "code": "NOT_PAPER_READY", "message": ",".join(readinessTruth["blockers"])},
        ],
        "readiness": {
            "runningServiceVisible": True,
            "paperNetworkEnabled": paperNetworkEnabled,
            "paperOrderEnabled": paperOrderEnabled,
            "paperOrdersSubmitted": paperOrdersSubmitted,
            "paperObservationAccepted": paperObservationAccepted,
            "operationalTradingReadiness": operationalTradingReadiness,
            "liveReadinessRequiresExplicitApproval": True,
        },
        "safety": {
            "readOnlyDashboard": True,
            "buySellControlsExposed": False,
            "liveToggleExposed": False,
            "rawAccountDisplayed": False,
            "rawProviderPayloadDisplayed": False,
        },
    }


def writeObservationReport(
    *,
    startedAtKst: str,
    endedAtKst: Optional[str] = None,
    operatorNote: Optional[str] = None,
    dataRoot: Optional[Path] = None,
    serviceUnitPaths: Optional[list[Path]] = None,
) -> Dict[str, Any]:
    runtimeRoot = dataRoot or DEFAULT_DATA_ROOT
    createdAt = datetime.now(KST).replace(microsecond=0)
    reportDir = runtimeRoot / "reports" / createdAt.date().isoformat()
    reportDir.mkdir(parents=True, exist_ok=True)
    reportPayload = {
        "schema_version": "paper_observation_report/v0",
        "created_at_kst": createdAt.isoformat(),
        "durationPolicy": "operator_selected",
        "fixedDurationDays": None,
        "autoPassOnDuration": False,
        "started_at_kst": startedAtKst,
        "ended_at_kst": endedAtKst,
        "operator_note": operatorNote,
        "readiness": {
            "paperObservationAccepted": False,
            "operationalTradingReadiness": False,
            "requiresExplicitGoNoGo": True,
        },
        "snapshot": buildOperatorConsoleSnapshot(
            createdAt.strftime("%Y-%m-%dT%H:%M:%S"),
            dataRoot=runtimeRoot,
            serviceUnitPaths=serviceUnitPaths,
        ),
    }
    reportPath = reportDir / f"paper-observation-{createdAt.strftime('%H%M%S')}.json"
    reportPath.write_text(
        json.dumps(reportPayload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    reportPayload["reportPath"] = str(reportPath)
    return reportPayload
