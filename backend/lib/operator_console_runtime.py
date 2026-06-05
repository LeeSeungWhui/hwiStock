"""
hwiStock read-only operator console runtime.
"""

from __future__ import annotations

import json
import os
import re
from html import unescape
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from service import HwiStockRunnerService as baseRunner
from lib.kis_paper_token_cache import loadKisPaperAccessToken, tokenCacheRevokeSkippedStep
from service.kis_paper_adapter import KisPaperAdapter, UrllibJsonTransport

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
        "compiledWatch": root / "compiled-watch" / day / "compiled-watch-latest.json",
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


def readJsonArtifact(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def readJsonlTail(path: Optional[str], limit: int = 12) -> list[Dict[str, Any]]:
    if not path:
        return []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[Dict[str, Any]] = []
    for line in lines[-max(1, limit * 2):]:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows[-limit:]


def cleanDisplayText(value: Any, fallback: str = "-") -> str:
    text = unescape(str(value or "").strip())
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or fallback


def boolEnv(key: str, default: bool = False) -> bool:
    raw = str(os.getenv(key, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def formatAccountLabel(accountNo: str, productCode: str) -> str:
    account = str(accountNo or "").strip()
    product = str(productCode or "").strip()
    if account and product:
        return f"{account}-{product}"
    return account or "계좌 설정 없음"


def _numericOrNone(value: Any) -> Optional[int]:
    if value is None:
        return None
    raw = str(value).strip().replace(",", "")
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def _writeDashboardAccountSummaryCache(dataRoot: Path, payload: Dict[str, Any]) -> None:
    cachePath = dataRoot / "account" / "dashboard-account-summary-latest.json"
    cachePath.parent.mkdir(parents=True, exist_ok=True)
    safePayload = {
        **payload,
        "rawProviderPayloadDisplayed": False,
        "credentialValuesPrinted": False,
    }
    cachePath.write_text(json.dumps(safePayload, ensure_ascii=False, indent=2), encoding="utf-8")


def _summaryFromPayload(
    payload: Dict[str, Any],
    *,
    accountNo: str,
    productCode: str,
    reserveFloor: int,
    source: str,
) -> Optional[Dict[str, Any]]:
    cash = _numericOrNone(payload.get("cash_balance_krw"))
    if cash is None:
        cash = _numericOrNone(payload.get("buyable_cash_krw"))
    if cash is None:
        cash = _numericOrNone(payload.get("cashBalance"))
    pnl = _numericOrNone(payload.get("today_pnl_krw"))
    if pnl is None:
        pnl = _numericOrNone(payload.get("todayPnl"))
    realizedPnl = _numericOrNone(payload.get("realized_pnl_krw"))
    if realizedPnl is None:
        realizedPnl = _numericOrNone(payload.get("realizedPnl"))
    positions = _numericOrNone(payload.get("positions_count")) or 0
    if positions == 0:
        positions = _numericOrNone(payload.get("openPositions")) or 0
    if cash is None and pnl is None and realizedPnl is None:
        return None
    return {
        "schema_version": "dashboard_account_summary/v0",
        "accountId": formatAccountLabel(accountNo, productCode),
        "cashBalance": cash if cash is not None else "잔고 조회 실패",
        "reserveBalance": reserveFloor,
        "todayPnl": pnl if pnl is not None else "손익 조회 실패",
        "realizedPnl": realizedPnl if realizedPnl is not None else "실현손익 조회 실패",
        "openPositions": positions,
        "status": payload.get("status") or "cached",
        "balanceStatus": payload.get("balance_status") or payload.get("balanceStatus"),
        "buyableStatus": payload.get("buyable_status") or payload.get("buyableStatus"),
        "realizedPnlStatus": payload.get("realized_pnl_status") or payload.get("realizedPnlStatus"),
        "source": source,
        "accountDisplayed": bool(accountNo),
        "rawProviderPayloadDisplayed": False,
        "credentialValuesPrinted": False,
    }


def _accountSummaryHasNumericPnl(summary: Optional[Dict[str, Any]]) -> bool:
    if not summary:
        return False
    return (
        _numericOrNone(summary.get("todayPnl")) is not None
        or _numericOrNone(summary.get("realizedPnl")) is not None
    )


def _readDashboardAccountSummaryFromRunnerEvidence(
    *,
    dataRoot: Path,
    dayKey: str,
    accountNo: str,
    productCode: str,
    reserveFloor: int,
) -> Optional[Dict[str, Any]]:
    evidencePath = dataRoot / "evidence" / dayKey / "kis-paper-continuous-latest.json"
    try:
        evidence = json.loads(evidencePath.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    balanceSummary: Dict[str, Any] = {}
    buyableSummary: Dict[str, Any] = {}
    realizedSummary: Dict[str, Any] = {}
    balanceStatus = None
    buyableStatus = None
    realizedStatus = None
    for step in evidence.get("steps") or []:
        if not isinstance(step, dict):
            continue
        if step.get("step") == "balance_inquire":
            balanceStatus = step.get("status")
            if isinstance(step.get("dashboard_account_summary"), dict):
                balanceSummary = dict(step["dashboard_account_summary"])
        if step.get("step") == "buyable_inquire_psbl_order":
            buyableStatus = step.get("status")
            if isinstance(step.get("dashboard_buyable_summary"), dict):
                buyableSummary = dict(step["dashboard_buyable_summary"])
        if step.get("step") == "realized_pnl_inquire":
            realizedStatus = step.get("status")
            if isinstance(step.get("dashboard_realized_pnl_summary"), dict):
                realizedSummary = dict(step["dashboard_realized_pnl_summary"])
    merged = {
        **balanceSummary,
        **buyableSummary,
        **realizedSummary,
        "status": "cached_pass" if balanceStatus == "pass" or buyableStatus == "pass" else "cached_warn",
        "balance_status": balanceStatus,
        "buyable_status": buyableStatus,
        "realized_pnl_status": realizedStatus,
    }
    return _summaryFromPayload(
        merged,
        accountNo=accountNo,
        productCode=productCode,
        reserveFloor=reserveFloor,
        source="kis-paper-runner-evidence",
    )


def _readDashboardAccountSummaryCache(
    *,
    dataRoot: Path,
    accountNo: str,
    productCode: str,
    reserveFloor: int,
) -> Optional[Dict[str, Any]]:
    cachePath = dataRoot / "account" / "dashboard-account-summary-latest.json"
    try:
        cached = json.loads(cachePath.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return _summaryFromPayload(
        cached,
        accountNo=accountNo,
        productCode=productCode,
        reserveFloor=reserveFloor,
        source="dashboard-account-cache",
    )


def buildDashboardAccountSummary(
    snapshotAt: datetime,
    *,
    dataRoot: Optional[Path] = None,
    dayKey: Optional[str] = None,
) -> Dict[str, Any]:
    accountNo = str(os.getenv("KIS_PAPER_ACCOUNT_NO") or "").strip()
    productCode = str(os.getenv("KIS_PAPER_ACCOUNT_PRODUCT_CODE") or "").strip()
    runtimeRoot = dataRoot or DEFAULT_DATA_ROOT
    evidenceDayKey = dayKey or snapshotAt.astimezone(KST).date().isoformat()
    reserveFloor = int(baseRunner.LIVE_CAPITAL_BASELINE_KRW * 0.25)
    fallback = {
        "schema_version": "dashboard_account_summary/v0",
        "accountId": formatAccountLabel(accountNo, productCode),
        "cashBalance": "잔고 조회 대기",
        "reserveBalance": reserveFloor,
        "todayPnl": "손익 조회 대기",
        "realizedPnl": "실현손익 조회 대기",
        "openPositions": 0,
        "status": "pending",
        "accountDisplayed": bool(accountNo),
        "rawProviderPayloadDisplayed": False,
        "credentialValuesPrinted": False,
    }
    evidenceSummary = _readDashboardAccountSummaryFromRunnerEvidence(
        dataRoot=runtimeRoot,
        dayKey=evidenceDayKey,
        accountNo=accountNo,
        productCode=productCode,
        reserveFloor=reserveFloor,
    )
    if evidenceSummary and _accountSummaryHasNumericPnl(evidenceSummary):
        return evidenceSummary
    cachedSummary = _readDashboardAccountSummaryCache(
        dataRoot=runtimeRoot,
        accountNo=accountNo,
        productCode=productCode,
        reserveFloor=reserveFloor,
    )
    if cachedSummary and _accountSummaryHasNumericPnl(cachedSummary):
        return cachedSummary
    if not boolEnv("HWISTOCK_DASHBOARD_ACCOUNT_READ_ENABLED", True):
        return {
            **fallback,
            "cashBalance": "잔고 조회 비활성",
            "todayPnl": "손익 조회 비활성",
            "realizedPnl": "실현손익 조회 비활성",
            "status": "disabled_by_env",
        }

    sampleSymbol = str(os.getenv("HWISTOCK_KIS_HEALTH_SYMBOL") or "005930").strip() or "005930"
    adapter = KisPaperAdapter(env=os.environ, transport=UrllibJsonTransport())
    missing = adapter.missingEnvKeys()
    if missing:
        return {
            **fallback,
            "cashBalance": "KIS 계좌 설정 필요",
            "todayPnl": "KIS 계좌 설정 필요",
            "realizedPnl": "KIS 계좌 설정 필요",
            "status": "blocked_missing_env",
        }

    try:
        tokenResult, token, tokenCacheManaged = loadKisPaperAccessToken(adapter, env=os.environ, now=snapshotAt)
        if not tokenResult.get("token_present") or not token:
            return {
                **fallback,
                "cashBalance": "KIS 토큰 발급 실패",
                "todayPnl": "KIS 토큰 발급 실패",
                "realizedPnl": "KIS 토큰 발급 실패",
                "status": "blocked_token_missing",
            }
        accountSummary = adapter.inquireAccountSummaryForDashboard(token, sampleSymbol)
        if tokenCacheManaged:
            tokenCacheRevokeSkippedStep()
        else:
            adapter.revokeToken(token)
    except Exception as exc:  # noqa: BLE001 - dashboard must degrade without leaking provider payloads.
        return {
            **fallback,
            "cashBalance": "KIS 잔고 조회 실패",
            "todayPnl": "KIS 잔고 조회 실패",
            "realizedPnl": "KIS 실현손익 조회 실패",
            "status": "warn",
            "errorType": type(exc).__name__,
        }

    summary = _summaryFromPayload(
        {
            **accountSummary,
            "status": accountSummary.get("status") or "unknown",
            "balance_status": accountSummary.get("balance_status"),
            "buyable_status": accountSummary.get("buyable_status"),
            "realized_pnl_status": accountSummary.get("realized_pnl_status"),
        },
        accountNo=accountNo,
        productCode=productCode,
        reserveFloor=reserveFloor,
        source="kis-live-read",
    ) or {
        **fallback,
        "accountId": accountSummary.get("account_label") or fallback["accountId"],
        "cashBalance": accountSummary.get("cash_balance_krw")
        if accountSummary.get("cash_balance_krw") is not None
        else "잔고 조회 실패",
        "reserveBalance": reserveFloor,
        "todayPnl": accountSummary.get("today_pnl_krw")
        if accountSummary.get("today_pnl_krw") is not None
        else "손익 조회 실패",
        "realizedPnl": accountSummary.get("realized_pnl_krw")
        if accountSummary.get("realized_pnl_krw") is not None
        else "실현손익 조회 실패",
        "openPositions": int(accountSummary.get("positions_count") or 0),
        "status": accountSummary.get("status") or "unknown",
        "balanceStatus": accountSummary.get("balance_status"),
        "buyableStatus": accountSummary.get("buyable_status"),
        "realizedPnlStatus": accountSummary.get("realized_pnl_status"),
        "accountDisplayed": bool(accountSummary.get("account_label")),
    }
    _writeDashboardAccountSummaryCache(runtimeRoot, summary)
    return summary


def formatKstMinute(value: Optional[str], fallback: Optional[datetime] = None) -> str:
    try:
        return parseKstTime(value).strftime("%H:%M")
    except Exception:
        if fallback:
            return fallback.astimezone(KST).strftime("%H:%M")
    return "-"


def fileMtimeKst(path: Optional[str]) -> str:
    if not path:
        return "-"
    try:
        return datetime.fromtimestamp(Path(path).stat().st_mtime, KST).strftime("%H:%M:%S")
    except OSError:
        return "-"


def sourceLabelFromEvent(event: Dict[str, Any]) -> str:
    sourceName = event.get("source_name") or event.get("source") or event.get("provider")
    if sourceName:
        return cleanDisplayText(sourceName)
    dedupeKey = str(event.get("dedupe_key") or "")
    if ":" in dedupeKey:
        return dedupeKey.split(":", 1)[0]
    return cleanDisplayText(event.get("event_type") or "market_event")


def buildIntelligenceRows(eventsPath: Optional[str], snapshotAt: datetime, limit: int = 8) -> list[Dict[str, str]]:
    rows: list[Dict[str, str]] = []
    for event in reversed(readJsonlTail(eventsPath, limit=limit)):
        title = (
            event.get("title")
            or event.get("headline")
            or event.get("report_name")
            or event.get("event_summary")
            or event.get("event_id")
        )
        rows.append(
            {
                "at": formatKstMinute(event.get("published_at_kst") or event.get("collected_at_kst"), snapshotAt),
                "source": sourceLabelFromEvent(event),
                "title": cleanDisplayText(title, "제목 없음"),
            }
        )
    return rows


def loadRuntimeArtifacts(latestArtifactPaths: Dict[str, Optional[str]]) -> Dict[str, Dict[str, Any]]:
    return {
        artifactKey: readJsonArtifact(artifactPath)
        for artifactKey, artifactPath in latestArtifactPaths.items()
        if artifactKey != "marketIntelligence"
    }


def buildCandidateRows(artifacts: Dict[str, Dict[str, Any]], limit: int = 5) -> list[Dict[str, Any]]:
    compiledItems = artifacts.get("compiledWatch", {}).get("items") or []
    compiledByName = {
        cleanDisplayText(item.get("name"), "").lower(): item
        for item in compiledItems
        if isinstance(item, dict) and item.get("name")
    }
    compiledBySymbol = {
        str(item.get("symbol") or item.get("ticker") or "").strip(): item
        for item in compiledItems
        if isinstance(item, dict) and (item.get("symbol") or item.get("ticker"))
    }

    actions = artifacts.get("flashTradeDocument", {}).get("actions") or []
    candidateRows: list[Dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        name = cleanDisplayText(action.get("name"), "종목명 없음")
        symbol = str(action.get("symbol") or action.get("ticker") or "").strip()
        compiled = compiledBySymbol.get(symbol) or compiledByName.get(name.lower()) or {}
        symbol = symbol or str(compiled.get("symbol") or compiled.get("ticker") or "-")
        conflict = action.get("portfolio_conflict") if isinstance(action.get("portfolio_conflict"), dict) else {}
        hasConflict = bool(conflict.get("has_conflict"))
        entryZone = action.get("entry_zone") if isinstance(action.get("entry_zone"), list) else []
        entryText = ""
        if len(entryZone) >= 2:
            entryText = f"진입 {entryZone[0]}~{entryZone[1]}"
        reasonParts = [
            cleanDisplayText(action.get("reason"), ""),
            entryText,
        ]
        if hasConflict:
            reasonParts.append("보유/대기 주문 충돌")
        reason = " · ".join([part for part in reasonParts if part])
        actionText = cleanDisplayText(action.get("action"), "WAIT")
        candidateRows.append(
            {
                "symbol": symbol,
                "name": name,
                "signal": actionText,
                "risk": "high" if hasConflict or actionText == "NO_TRADE" else "medium",
                "reason": reason or cleanDisplayText(compiled.get("condition_card_id"), "runtime candidate"),
            }
        )
        if len(candidateRows) >= limit:
            return candidateRows

    for item in compiledItems:
        if not isinstance(item, dict):
            continue
        candidateRows.append(
            {
                "symbol": str(item.get("symbol") or item.get("ticker") or "-"),
                "name": cleanDisplayText(item.get("name"), "종목명 없음"),
                "signal": "WATCH",
                "risk": "medium",
                "reason": cleanDisplayText(item.get("condition_card_id"), "compiled watch candidate"),
            }
        )
        if len(candidateRows) >= limit:
            break
    return candidateRows


def buildAiThreadRows(artifacts: Dict[str, Dict[str, Any]], snapshotAt: datetime) -> list[Dict[str, str]]:
    rows: list[Dict[str, str]] = []
    pro = artifacts.get("ai", {})
    if pro:
        marketRegime = pro.get("market_regime") if isinstance(pro.get("market_regime"), dict) else {}
        marketMode = cleanDisplayText(marketRegime.get("market_mode"), "UNKNOWN")
        strong = ", ".join(cleanDisplayText(item, "") for item in (pro.get("strong_conditions") or [])[:3])
        avoid = ", ".join(cleanDisplayText(item, "") for item in (pro.get("avoid_conditions") or [])[:3])
        bodyParts = [
            cleanDisplayText(pro.get("summary"), "요약 없음"),
            f"강한 조건: {strong}" if strong else "",
            f"피할 조건: {avoid}" if avoid else "",
        ]
        rows.append(
            {
                "at": formatKstMinute(pro.get("produced_at_kst"), snapshotAt),
                "role": "report",
                "subject": f"DeepSeek Pro 정각 분석 · {marketMode}",
                "body": " / ".join([part for part in bodyParts if part]),
            }
        )

    flash = artifacts.get("flashTradeDocument", {})
    if flash:
        actionCount = len(flash.get("actions") or [])
        validationStatus = cleanDisplayText(flash.get("validation_status"), "unknown")
        providerSummary = cleanDisplayText(flash.get("provider_summary"), "")
        body = providerSummary or (
            f"Flash 10분 매매문서 후보 {actionCount}개 · validation={validationStatus} · "
            f"entry_unlocked={bool(flash.get('entry_unlocked'))}"
        )
        rows.append(
            {
                "at": formatKstMinute(flash.get("produced_at_kst"), snapshotAt),
                "role": "assistant",
                "subject": f"DeepSeek Flash 10분 매매문서 · {actionCount}개",
                "body": body,
            }
        )
    return rows


def buildAuditRows(
    *,
    snapshotAt: datetime,
    runnerStatus: Dict[str, Any],
    readinessTruth: Dict[str, Any],
    latestArtifactPaths: Dict[str, Optional[str]],
    artifacts: Dict[str, Dict[str, Any]],
    paperOrderEnabled: bool,
) -> list[Dict[str, Any]]:
    nowText = snapshotAt.strftime("%H:%M")
    rows: list[Dict[str, Any]] = [
        {
            "at": nowText,
            "level": "info",
            "code": "ORDER_GATE",
            "message": str(runnerStatus.get("orderGate") or "unknown"),
            "tags": ["runner", "order_gate"],
        }
    ]

    for artifactKey, artifactPath in latestArtifactPaths.items():
        rows.append(
            {
                "at": fileMtimeKst(artifactPath) if artifactPath else nowText,
                "level": "info" if artifactPath else "warn",
                "code": f"ARTIFACT_{artifactKey}",
                "message": Path(artifactPath).name if artifactPath else "missing_or_safe_blocked",
                "tags": ["artifact", artifactKey],
            }
        )

    kis = artifacts.get("kisMarket", {})
    for result in (kis.get("input_results") or [])[:8]:
        if not isinstance(result, dict):
            continue
        status = cleanDisplayText(result.get("status"), "unknown")
        rows.append(
            {
                "at": formatKstMinute(kis.get("produced_at_kst"), snapshotAt),
                "level": "info" if status == "pass" else "warn",
                "code": f"KIS_{cleanDisplayText(result.get('input_id'), 'input')}",
                "message": (
                    f"{status} · http={result.get('http_status', '-')} · "
                    f"rows={result.get('row_count', '-')}"
                ),
                "tags": ["kis", cleanDisplayText(result.get("transport"), "rest")],
            }
        )

    continuous = artifacts.get("kisPaperRunner", {})
    for step in (continuous.get("steps") or [])[:8]:
        if not isinstance(step, dict):
            continue
        status = cleanDisplayText(step.get("status"), "unknown")
        if status == "pass":
            continue
        rows.append(
            {
                "at": formatKstMinute(continuous.get("timestamp_kst"), snapshotAt),
                "level": "warn",
                "code": f"RUNNER_{cleanDisplayText(step.get('step'), 'step')}",
                "message": (
                    f"{status} · http={step.get('http_status', '-')} · "
                    f"msg={cleanDisplayText(step.get('msg_cd'), '-')}"
                ),
                "tags": ["runner", "kis_paper_continuous"],
            }
        )

    rows.extend(
        [
            {"at": nowText, "level": "info", "code": "READ_ONLY", "message": "dashboard exposes no order controls", "tags": ["dashboard"]},
            {
                "at": nowText,
                "level": "warn" if paperOrderEnabled else "info",
                "code": "SYSTEMD_ORDER_FLAG",
                "message": "enabled" if paperOrderEnabled else "disabled",
                "tags": ["systemd", "order_flag"],
            },
            {
                "at": nowText,
                "level": "warn",
                "code": "NOT_READY",
                "message": ",".join(readinessTruth.get("blockers") or []),
                "tags": ["readiness"],
            },
        ]
    )
    return rows


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
    runtimeArtifacts = loadRuntimeArtifacts(latestArtifactPaths)
    servicePolicy = inspectKisPaperRunnerServicePolicy(serviceUnitPaths)
    accountSummary = buildDashboardAccountSummary(snapshotAt, dataRoot=runtimeRoot, dayKey=dayKey)
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
    candidateRows = buildCandidateRows(runtimeArtifacts)
    intelligenceRows = buildIntelligenceRows(latestArtifactPaths.get("marketIntelligence"), snapshotAt)
    aiThreadRows = buildAiThreadRows(runtimeArtifacts, snapshotAt)
    flashArtifact = runtimeArtifacts.get("flashTradeDocument", {})
    continuousArtifact = runtimeArtifacts.get("kisPaperRunner", {})
    riskRejects = sum(
        1
        for action in (flashArtifact.get("actions") or [])
        if isinstance(action, dict)
        and (
            action.get("action") == "NO_TRADE"
            or bool(
                (action.get("portfolio_conflict") if isinstance(action.get("portfolio_conflict"), dict) else {}).get("has_conflict")
            )
        )
    )
    aiJobStatus = " / ".join(
        [
            f"pro:{pathStatus(latestArtifactPaths.get('ai'))}",
            f"flash:{pathStatus(latestArtifactPaths.get('flashTradeDocument'))}",
        ]
    )
    reportStatus = "continuous_tick:" + cleanDisplayText(continuousArtifact.get("status"), "missing")
    auditRows = buildAuditRows(
        snapshotAt=snapshotAt,
        runnerStatus=runnerStatus,
        readinessTruth=readinessTruth,
        latestArtifactPaths=latestArtifactPaths,
        artifacts=runtimeArtifacts,
        paperOrderEnabled=paperOrderEnabled,
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
            "accountId": accountSummary["accountId"],
            "cashBalance": accountSummary["cashBalance"],
            "reserveBalance": accountSummary["reserveBalance"],
            "todayPnl": accountSummary["todayPnl"],
            "realizedPnl": accountSummary["realizedPnl"],
            "openPositions": accountSummary["openPositions"],
            "riskRejects": riskRejects,
            "aiJobStatus": aiJobStatus,
            "reportStatus": reportStatus,
            "accountReadStatus": accountSummary["status"],
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
            "dashboardAccountSummary": {
                "status": accountSummary["status"],
                "balanceStatus": accountSummary.get("balanceStatus"),
                "buyableStatus": accountSummary.get("buyableStatus"),
                "realizedPnlStatus": accountSummary.get("realizedPnlStatus"),
                "rawProviderPayloadDisplayed": accountSummary["rawProviderPayloadDisplayed"],
                "credentialValuesPrinted": accountSummary["credentialValuesPrinted"],
            },
            "localOnly": True,
            "publicBind": False,
        },
        "holdings": [],
        "candidates": candidateRows,
        "intelligence": intelligenceRows,
        "aiThread": aiThreadRows,
        "auditLog": auditRows,
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
            "rawAccountDisplayed": accountSummary["accountDisplayed"],
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
