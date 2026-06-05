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


def buildOperatorConsoleSnapshot(
    atKst: Optional[str] = None,
    *,
    dataRoot: Optional[Path] = None,
) -> Dict[str, Any]:
    snapshotAt = parseKstTime(atKst)
    runtimeRoot = dataRoot or DEFAULT_DATA_ROOT
    dayKey = snapshotAt.astimezone(KST).date().isoformat()
    runnerStatus = baseRunner.get_runner_status(snapshotAt.strftime("%Y-%m-%dT%H:%M:%S"))
    latestArtifactPaths = latestRuntimePaths(runtimeRoot, dayKey)
    readiness = runnerStatus["readiness"]
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
            "paperNetworkEnabled": False,
            "paperOrdersSubmitted": False,
            "paperObservationAccepted": readiness["paperObservationAccepted"],
            "operationalTradingReadiness": readiness["liveRunnerReady"],
        },
        "runtime": {
            "serviceTimers": [
                {"name": "hwistock-intel-collector.timer", "scope": "user", "status": "configured_or_external"},
                {"name": "hwistock-ai-analysis.timer", "scope": "user", "status": "configured_or_external"},
                {"name": "hwistock-ai-flash.timer", "scope": "user", "status": "configured_or_external"},
                {"name": "hwistock-kis-market-data.timer", "scope": "user", "status": "configured_or_external"},
                {"name": "hwistock-kis-paper-runner.timer", "scope": "user", "status": "configured_or_external"},
            ],
            "latestEvidencePaths": latestArtifactPaths,
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
        ],
        "readiness": {
            "runningServiceVisible": True,
            "paperNetworkEnabled": False,
            "paperOrdersSubmitted": False,
            "paperObservationAccepted": False,
            "operationalTradingReadiness": False,
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
        ),
    }
    reportPath = reportDir / f"paper-observation-{createdAt.strftime('%H%M%S')}.json"
    reportPath.write_text(
        json.dumps(reportPayload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    reportPayload["reportPath"] = str(reportPath)
    return reportPayload
