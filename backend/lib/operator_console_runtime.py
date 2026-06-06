"""
hwiStock read-only operator console runtime.
"""

from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import time
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
AI_CONVERSATION_RESPONSE_SCHEMA_VERSION = "ai_conversation_response/v0"
AI_CONVERSATION_AUDIT_SCHEMA_VERSION = "ai_conversation_audit/v0"
AI_CONVERSATION_ROUTE = "local_deterministic_dashboard_answer"
AI_CONVERSATION_ACCESS_INVARIANT = "loopback_or_frontend_bff_only"
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|app[_-]?key|appkey|secret|client[_-]?secret|appsecret|password|passwd|token|authorization)\s*[:=]\s*['\"]?[^\s,'\"]+"
)
_LONG_SECRET_LIKE_RE = re.compile(r"\b[A-Za-z0-9_\-]{20,}\b")
_UNSAFE_CONVERSATION_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "order_execution_request",
        re.compile(
            r"(?i)(매수|매도|사줘|팔아줘|주문|체결|진입해|청산해|buy|sell|order|execute|submit|place)"
            r".{0,16}(해|해줘|넣|보내|접수|걸어|등록|취소|cancel|now|바로|실행|submit|place|execute)"
        ),
    ),
    (
        "settings_mutation_request",
        re.compile(
            r"(?i)(설정|리스크|손절|익절|트레일링|비중|킬스위치|kill switch|adapter|broker|모델|프롬프트)"
            r".{0,18}(바꿔|변경|수정|켜|꺼|enable|disable|set|update|edit|patch|적용)"
        ),
    ),
    (
        "credential_disclosure_request",
        re.compile(
            r"(?i)(비번|비밀번호|secret|api\s*key|apikey|client\s*secret|토큰|키|자격증명|credential|authorization|계좌번호)"
            r".{0,18}(보여|알려|출력|print|show|reveal|dump|노출)"
        ),
    ),
    (
        "service_lifecycle_request",
        re.compile(
            r"(?i)(서비스|systemd|timer|daemon|서버|프로세스|runner|worker)"
            r".{0,18}(시작|중지|재시작|켜|꺼|restart|start|stop|enable|disable)"
        ),
    ),
)
_BLOCKER_LABEL_PAIRS: tuple[tuple[str, str], ...] = (
    ("paper_network_disabled", "시장/브로커 네트워크 플래그 미확인"),
    ("paper_order_loop_disabled", "모의투자 주문 루프 비활성"),
    ("artifact_missing_or_safe_blocked", "필수 런타임 산출물 누락"),
    ("blocked_calendar_unconfigured", "거래 캘린더 미설정"),
    ("blocked_calendar_stale", "거래 캘린더 만료"),
    ("blocked_source_unconfigured", "시장 데이터 소스 미설정"),
    ("blocked_kill_switch", "킬스위치 활성"),
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


def buildArtifactFreshness(
    latestArtifactPaths: Dict[str, Optional[str]],
    *,
    snapshotAt: datetime,
) -> Dict[str, Any]:
    ttlByKey = {
        "marketIntelligence": 15 * 60,
        "compiledWatch": 5 * 60,
        "ai": 75 * 60,
        "flashTradeDocument": 15 * 60,
        "kisMarket": 4 * 60,
        "kisPaperRunner": 8 * 60,
        "runner": 8 * 60,
    }
    rows: Dict[str, Any] = {}
    staleKeys: list[str] = []
    missingKeys: list[str] = []
    for artifactKey, artifactPath in latestArtifactPaths.items():
        ttl = ttlByKey.get(artifactKey, 15 * 60)
        if not artifactPath:
            rows[artifactKey] = {
                "path": None,
                "present": False,
                "ageSec": None,
                "ttlSec": ttl,
                "stale": True,
                "state": "missing",
            }
            missingKeys.append(artifactKey)
            continue
        try:
            mtime = datetime.fromtimestamp(Path(artifactPath).stat().st_mtime, KST)
            age = max(0, int((snapshotAt.astimezone(KST) - mtime).total_seconds()))
        except OSError:
            mtime = None
            age = None
        stale = age is None or age > ttl
        if stale:
            staleKeys.append(artifactKey)
        rows[artifactKey] = {
            "path": artifactPath,
            "present": True,
            "mtimeKst": mtime.isoformat() if mtime else None,
            "ageSec": age,
            "ttlSec": ttl,
            "stale": stale,
            "state": "stale" if stale else "fresh",
        }
    return {
        "schema_version": "operator_artifact_freshness/v0",
        "snapshotAtKst": snapshotAt.isoformat(),
        "artifacts": rows,
        "staleKeys": staleKeys,
        "missingKeys": missingKeys,
        "allRequiredFresh": not staleKeys and not missingKeys,
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
    artifactFreshness: Optional[Dict[str, Any]] = None,
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
        freshness = ((artifactFreshness or {}).get("artifacts") or {}).get(artifactKey, {})
        rows.append(
            {
                "at": fileMtimeKst(artifactPath) if artifactPath else nowText,
                "level": "warn" if freshness.get("stale") or not artifactPath else "info",
                "code": f"ARTIFACT_{artifactKey}",
                "message": (
                    f"stale age={freshness.get('ageSec')}s ttl={freshness.get('ttlSec')}s"
                    if freshness.get("stale") and artifactPath
                    else Path(artifactPath).name if artifactPath else "missing_or_safe_blocked"
                ),
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
    livePolicyOverride: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    useLiveSystemd = serviceUnitPaths is None
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
    livePolicy = livePolicyOverride if livePolicyOverride is not None else (
        inspectLiveKisPaperRunnerPolicy()
        if useLiveSystemd
        else {
            "schema_version": "kis_paper_runner_live_policy/v0",
            "available": False,
            "source": "test_or_static_service_unit_paths",
            "paperNetworkEnabledByLiveUnit": False,
            "paperOrderEnabledByLiveUnit": False,
            "activeState": None,
            "subState": None,
            "timerActiveState": None,
            "credentialValuesPrinted": False,
        }
    )
    effectiveNetwork = paperNetworkEnabled or bool(livePolicy.get("paperNetworkEnabledByLiveUnit"))
    effectiveOrder = paperOrderEnabled or bool(livePolicy.get("paperOrderEnabledByLiveUnit"))
    return {
        "schema_version": "kis_paper_runner_service_policy/v0",
        "serviceFiles": inspected,
        "repoPolicy": {
            "paperNetworkEnabledByService": paperNetworkEnabled,
            "paperOrderEnabledByService": paperOrderEnabled,
        },
        "livePolicy": livePolicy,
        "paperNetworkEnabledByService": paperNetworkEnabled,
        "paperOrderEnabledByService": paperOrderEnabled,
        "paperNetworkEnabledEffective": effectiveNetwork,
        "paperOrderEnabledEffective": effectiveOrder,
        "orderFlagContradictsReadiness": False,
    }


def inspectLiveKisPaperRunnerPolicy() -> Dict[str, Any]:
    base = {
        "schema_version": "kis_paper_runner_live_policy/v0",
        "available": False,
        "source": "systemctl_user_show",
        "paperNetworkEnabledByLiveUnit": False,
        "paperOrderEnabledByLiveUnit": False,
        "activeState": None,
        "subState": None,
        "timerActiveState": None,
        "credentialValuesPrinted": False,
    }
    try:
        service = subprocess.run(
            ["systemctl", "--user", "show", "hwistock-kis-paper-runner.service", "--property=ActiveState", "--property=SubState"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        timer = subprocess.run(
            ["systemctl", "--user", "show", "hwistock-kis-paper-runner.timer", "--property=ActiveState", "--property=SubState"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        service_text = subprocess.run(
            ["systemctl", "--user", "cat", "hwistock-kis-paper-runner.service"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {**base, "errorType": type(exc).__name__}
    text = service_text.stdout.lower() if service_text.returncode == 0 else ""
    active_state = _systemctlProperty(service.stdout, "ActiveState")
    sub_state = _systemctlProperty(service.stdout, "SubState")
    timer_active_state = _systemctlProperty(timer.stdout, "ActiveState")
    return {
        **base,
        "available": service.returncode == 0,
        "activeState": active_state,
        "subState": sub_state,
        "timerActiveState": timer_active_state,
        "unitTextInspected": service_text.returncode == 0,
        "paperNetworkEnabledByLiveUnit": "--allow-paper-network" in text or "hwistock_kis_paper_network_enabled=true" in text,
        "paperOrderEnabledByLiveUnit": "--allow-paper-orders" in text or "hwistock_kis_paper_order_enabled=true" in text,
        "paperOrderDisabledByLiveUnit": "hwistock_kis_paper_order_enabled=false" in text,
    }


def _systemctlProperty(text: str, key: str) -> Optional[str]:
    prefix = f"{key}="
    for line in str(text or "").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip() or None
    return None


def buildReadinessTruthPanel(
    *,
    runnerStatus: Dict[str, Any],
    latestArtifactPaths: Dict[str, Optional[str]],
    servicePolicy: Optional[Dict[str, Any]] = None,
    artifactFreshness: Optional[Dict[str, Any]] = None,
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
    if not paperOrderEnabled:
        blockerList.append("paper_order_loop_disabled")
    orderGate = runnerStatus.get("orderGate")
    if orderGate and orderGate != "no_order_dry_run_only":
        blockerList.append(str(orderGate))
    evidenceGapList = []
    if not paperOrdersSubmitted:
        evidenceGapList.append("paper_orders_not_submitted")
    if not paperObservationAccepted:
        evidenceGapList.append("paper_observation_not_accepted")
    if not operationalTradingReadiness:
        evidenceGapList.append("live_production_readiness_not_applicable")
    if fallbackArtifactKeys:
        evidenceGapList.append("artifact_missing_or_safe_blocked")
    for artifactKey in (artifactFreshness or {}).get("staleKeys") or []:
        evidenceGapList.append(f"artifact_stale:{artifactKey}")
    paperExperimentReady = not blockerList
    return {
        "headline": "PAPER_EXPERIMENT_READY" if paperExperimentReady else "PAPER_EXPERIMENT_BLOCKED",
        "severity": "calm" if paperExperimentReady else "danger",
        "operatorMessage": (
            "현재 목표는 최종 운영 ready가 아니라 KIS 모의투자 paper experiment입니다. "
            "live/production readiness는 paper 주문 루프를 차단하지 않으며, session approval·캘린더·중복락·증거 저장을 기준으로 봅니다."
        ),
        "blockers": blockerList,
        "evidenceGaps": evidenceGapList,
        "paperExperimentReady": paperExperimentReady,
        "paperOrderLoopEnabled": paperOrderEnabled,
        "paperNetworkEnabled": paperNetworkEnabled,
        "paperOrderEnabled": paperOrderEnabled,
        "paperOrdersSubmitted": paperOrdersSubmitted,
        "paperObservationAccepted": paperObservationAccepted,
        "operationalTradingReadiness": operationalTradingReadiness,
        "operationalTradingReadinessBlocksPaperOperation": False,
        "liveMoneyTradingReady": "not_applicable",
        "productionQualityReady": "partial_non_blocking",
        "orderGate": orderGate,
        "servicePolicy": policy,
        "artifactFreshness": artifactFreshness or {},
        "fallbackArtifactKeys": fallbackArtifactKeys,
        "serviceVisibilityIsNotReadiness": True,
    }


def sanitizeConversationQuestion(value: Any, limit: int = 500) -> str:
    text = cleanDisplayText(value, "")
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def redactSensitiveConversationText(value: str, limit: int = 180) -> str:
    text = sanitizeConversationQuestion(value, limit=limit)

    def replaceAssignment(match: re.Match[str]) -> str:
        key = match.group(1)
        return f"{key}=[REDACTED]"

    text = _SECRET_ASSIGNMENT_RE.sub(replaceAssignment, text)
    return _LONG_SECRET_LIKE_RE.sub("[REDACTED]", text)


def classifyUnsafeConversationRequest(question: str) -> Optional[str]:
    for reason, pattern in _UNSAFE_CONVERSATION_RULES:
        if pattern.search(question):
            return reason
    return None


def humanizeBlocker(value: Any) -> str:
    raw = str(value or "").strip()
    for blockerKey, label in _BLOCKER_LABEL_PAIRS:
        if blockerKey == raw:
            return label
    return raw or "확인 필요"


def buildAiConversationArtifactContext(
    *,
    snapshotAt: datetime,
    dataRoot: Optional[Path] = None,
    serviceUnitPaths: Optional[list[Path]] = None,
) -> Dict[str, Any]:
    runtimeRoot = dataRoot or DEFAULT_DATA_ROOT
    dayKey = snapshotAt.astimezone(KST).date().isoformat()
    runnerStatus = baseRunner.get_runner_status(snapshotAt.strftime("%Y-%m-%dT%H:%M:%S"))
    latestArtifactPaths = latestRuntimePaths(runtimeRoot, dayKey)
    artifactFreshness = buildArtifactFreshness(latestArtifactPaths, snapshotAt=snapshotAt)
    runtimeArtifacts = loadRuntimeArtifacts(latestArtifactPaths)
    servicePolicy = inspectKisPaperRunnerServicePolicy(serviceUnitPaths)
    readiness = runnerStatus.get("readiness") if isinstance(runnerStatus.get("readiness"), dict) else {}
    paperNetworkEnabled = bool(servicePolicy.get("paperNetworkEnabledEffective", servicePolicy["paperNetworkEnabledByService"]))
    paperOrderEnabled = bool(servicePolicy.get("paperOrderEnabledEffective", servicePolicy["paperOrderEnabledByService"]))
    operationalTradingReadiness = bool(readiness.get("liveRunnerReady"))
    servicePolicy = {
        **servicePolicy,
        "orderFlagContradictsReadiness": False,
        "liveReadinessDoesNotBlockPaperExperiment": True,
    }
    readinessTruth = buildReadinessTruthPanel(
        runnerStatus=runnerStatus,
        latestArtifactPaths=latestArtifactPaths,
        servicePolicy=servicePolicy,
        artifactFreshness=artifactFreshness,
        paperNetworkEnabled=paperNetworkEnabled,
        paperOrderEnabled=paperOrderEnabled,
        paperOrdersSubmitted=False,
        paperObservationAccepted=bool(readiness.get("paperObservationAccepted")),
        operationalTradingReadiness=operationalTradingReadiness,
    )
    contextRefs = [
        {
            "key": artifactKey,
            "status": pathStatus(artifactPath),
            "basename": Path(artifactPath).name if artifactPath else None,
        }
        for artifactKey, artifactPath in latestArtifactPaths.items()
    ]
    return {
        "snapshotAtKst": snapshotAt.isoformat(),
        "dayKey": dayKey,
        "runnerStatus": runnerStatus,
        "latestArtifactPaths": latestArtifactPaths,
        "artifacts": runtimeArtifacts,
        "intelligence": buildIntelligenceRows(latestArtifactPaths.get("marketIntelligence"), snapshotAt, limit=5),
        "candidates": buildCandidateRows(runtimeArtifacts, limit=5),
        "aiThread": buildAiThreadRows(runtimeArtifacts, snapshotAt),
        "readinessTruth": readinessTruth,
        "contextRefs": contextRefs,
        "networkCallMade": False,
        "brokerCallMade": False,
        "orderMutationAttempted": False,
        "serviceMutationAttempted": False,
        "credentialValuesPrinted": False,
        "accessInvariant": AI_CONVERSATION_ACCESS_INVARIANT,
    }


def buildAllowedConversationAnswer(question: str, context: Dict[str, Any]) -> str:
    artifacts = context.get("artifacts") if isinstance(context.get("artifacts"), dict) else {}
    runnerStatus = context.get("runnerStatus") if isinstance(context.get("runnerStatus"), dict) else {}
    readinessTruth = context.get("readinessTruth") if isinstance(context.get("readinessTruth"), dict) else {}
    candidates = context.get("candidates") if isinstance(context.get("candidates"), list) else []
    intelligence = context.get("intelligence") if isinstance(context.get("intelligence"), list) else []
    pro = artifacts.get("ai") if isinstance(artifacts.get("ai"), dict) else {}
    flash = artifacts.get("flashTradeDocument") if isinstance(artifacts.get("flashTradeDocument"), dict) else {}
    lines: list[str] = []

    if pro:
        marketRegime = pro.get("market_regime") if isinstance(pro.get("market_regime"), dict) else {}
        mode = cleanDisplayText(marketRegime.get("market_mode"), "UNKNOWN")
        summary = cleanDisplayText(pro.get("summary"), "요약 없음")
        strong = ", ".join(cleanDisplayText(item, "") for item in (pro.get("strong_conditions") or [])[:3])
        avoid = ", ".join(cleanDisplayText(item, "") for item in (pro.get("avoid_conditions") or [])[:3])
        lines.append(f"Pro 정각 분석 기준 시장 모드는 {mode}이고, 핵심 요약은 “{summary}”입니다.")
        if strong:
            lines.append(f"강한 조건: {strong}.")
        if avoid:
            lines.append(f"피해야 할 조건: {avoid}.")
    else:
        lines.append("현재 저장된 Pro 정각 분석 파일은 아직 확인되지 않습니다.")

    if flash:
        actionCount = len(flash.get("actions") or [])
        validationStatus = cleanDisplayText(flash.get("validation_status"), "unknown")
        lines.append(f"Flash 매매문서는 후보 {actionCount}개를 포함하고 validation={validationStatus} 상태입니다.")
    else:
        lines.append("현재 저장된 Flash 매매문서는 아직 확인되지 않습니다.")

    orderGate = cleanDisplayText(runnerStatus.get("orderGate"), "unknown")
    blockers = [humanizeBlocker(item) for item in (readinessTruth.get("blockers") or [])[:5]]
    if blockers:
        lines.append(f"운영 준비 차단 요인: {', '.join(blockers)}.")
    lines.append(f"현재 주문 게이트는 {orderGate}입니다. 이 대화 API는 설명 전용이며 주문·설정 변경은 수행하지 않습니다.")

    if candidates:
        topCandidates = ", ".join(
            f"{cleanDisplayText(item.get('name'), '종목명 없음')}({cleanDisplayText(item.get('signal'), '-')})"
            for item in candidates[:3]
            if isinstance(item, dict)
        )
        if topCandidates:
            lines.append(f"대시보드 후보 상위 항목은 {topCandidates}입니다.")

    if intelligence:
        titles = ", ".join(cleanDisplayText(item.get("title"), "") for item in intelligence[:3] if isinstance(item, dict))
        if titles:
            lines.append(f"최근 수집 이슈: {titles}.")

    if "왜" in question or "근거" in question:
        lines.append("근거는 저장된 Pro/Flash 리포트, 최신 수집 이벤트, 후보 카드, runner 상태의 sanitized snapshot만 사용했습니다.")

    return " ".join(lines)


def buildConversationRequestId(createdAt: datetime, question: str) -> str:
    digest = hashlib.sha256(f"{createdAt.isoformat()}::{question}".encode("utf-8")).hexdigest()[:10]
    return f"aiq-{createdAt.strftime('%Y%m%d%H%M%S')}-{digest}"


def writeAiConversationAuditRecord(
    *,
    dataRoot: Path,
    createdAt: datetime,
    record: Dict[str, Any],
    auditRoot: Optional[Path] = None,
) -> Dict[str, Any]:
    root = auditRoot
    if root is None:
        configured = str(os.getenv("HWISTOCK_AI_CONVERSATION_AUDIT_DIR") or "").strip()
        root = Path(configured) if configured else dataRoot / "audit" / "ai_conversation"
    auditDir = root / createdAt.astimezone(KST).date().isoformat()
    auditPath = auditDir / "ai-conversation.jsonl"
    try:
        auditDir.mkdir(parents=True, exist_ok=True)
        with auditPath.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return {"written": True, "path": str(auditPath), "errorType": None}
    except OSError as exc:
        return {"written": False, "path": str(auditPath), "errorType": type(exc).__name__}


def answerAiConversation(
    *,
    question: Any,
    atKst: Optional[str] = None,
    dataRoot: Optional[Path] = None,
    auditRoot: Optional[Path] = None,
) -> Dict[str, Any]:
    started = time.perf_counter()
    snapshotAt = parseKstTime(atKst)
    runtimeRoot = dataRoot or DEFAULT_DATA_ROOT
    sanitizedQuestion = sanitizeConversationQuestion(question)
    createdAt = snapshotAt.replace(microsecond=0)
    requestId = buildConversationRequestId(createdAt, sanitizedQuestion)
    unsafeReason = classifyUnsafeConversationRequest(sanitizedQuestion) if sanitizedQuestion else "empty_question"
    context = buildAiConversationArtifactContext(snapshotAt=snapshotAt, dataRoot=runtimeRoot)
    refused = bool(unsafeReason)
    refusal = None
    if unsafeReason:
        refusal = (
            "이 대화는 저장된 리포트와 현재 상태를 설명하는 용도입니다. "
            "주문 실행, 설정 변경, 자격증명 노출, 서비스 제어 요청은 처리하지 않습니다."
        )
        answer = refusal
    else:
        answer = buildAllowedConversationAnswer(sanitizedQuestion, context)

    latencyMs = int((time.perf_counter() - started) * 1000)
    questionHash = hashlib.sha256(sanitizedQuestion.encode("utf-8")).hexdigest() if sanitizedQuestion else None
    contextRefs = context["contextRefs"]
    auditRecord = {
        "schema_version": AI_CONVERSATION_AUDIT_SCHEMA_VERSION,
        "auditCategory": "ai_conversation",
        "requestId": requestId,
        "createdAtKst": createdAt.isoformat(),
        "questionHash": questionHash,
        "questionPreview": redactSensitiveConversationText(sanitizedQuestion),
        "refused": refused,
        "refusalReason": unsafeReason,
        "answerPreview": redactSensitiveConversationText(answer),
        "contextRefs": contextRefs,
        "modelProvider": "local",
        "modelRoute": AI_CONVERSATION_ROUTE,
        "accessInvariant": AI_CONVERSATION_ACCESS_INVARIANT,
        "latencyMs": latencyMs,
        "credentialValuesPrinted": False,
        "networkCallMade": False,
        "brokerCallMade": False,
        "orderMutationAttempted": False,
        "serviceMutationAttempted": False,
    }
    audit = writeAiConversationAuditRecord(
        dataRoot=runtimeRoot,
        createdAt=createdAt,
        record=auditRecord,
        auditRoot=auditRoot,
    )
    return {
        "schema_version": AI_CONVERSATION_RESPONSE_SCHEMA_VERSION,
        "requestId": requestId,
        "createdAtKst": createdAt.isoformat(),
        "answer": None if refused else answer,
        "refusal": refusal,
        "refused": refused,
        "refusalReason": unsafeReason,
        "contextRefs": contextRefs,
        "modelProvider": "local",
        "modelRoute": AI_CONVERSATION_ROUTE,
        "accessInvariant": AI_CONVERSATION_ACCESS_INVARIANT,
        "latencyMs": latencyMs,
        "auditCategory": "ai_conversation",
        "auditWritten": audit["written"],
        "auditPath": audit["path"],
        "auditErrorType": audit["errorType"],
        "credentialValuesPrinted": False,
        "networkCallMade": False,
        "brokerCallMade": False,
        "orderMutationAttempted": False,
        "serviceMutationAttempted": False,
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
    artifactFreshness = buildArtifactFreshness(latestArtifactPaths, snapshotAt=snapshotAt)
    runtimeArtifacts = loadRuntimeArtifacts(latestArtifactPaths)
    servicePolicy = inspectKisPaperRunnerServicePolicy(serviceUnitPaths)
    accountSummary = buildDashboardAccountSummary(snapshotAt, dataRoot=runtimeRoot, dayKey=dayKey)
    readiness = runnerStatus["readiness"]
    paperNetworkEnabled = bool(servicePolicy.get("paperNetworkEnabledEffective", servicePolicy["paperNetworkEnabledByService"]))
    paperOrderEnabled = bool(servicePolicy.get("paperOrderEnabledEffective", servicePolicy["paperOrderEnabledByService"]))
    paperOrdersSubmitted = False
    paperObservationAccepted = readiness["paperObservationAccepted"]
    operationalTradingReadiness = readiness["liveRunnerReady"]
    servicePolicy = {
        **servicePolicy,
        "orderFlagContradictsReadiness": False,
        "liveReadinessDoesNotBlockPaperExperiment": True,
    }
    readinessTruth = buildReadinessTruthPanel(
        runnerStatus=runnerStatus,
        latestArtifactPaths=latestArtifactPaths,
        servicePolicy=servicePolicy,
        artifactFreshness=artifactFreshness,
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
        artifactFreshness=artifactFreshness,
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
            "artifactFreshness": artifactFreshness,
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
            "paperExperimentReady": readinessTruth["paperExperimentReady"],
            "paperOrdersSubmitted": paperOrdersSubmitted,
            "paperObservationAccepted": paperObservationAccepted,
            "operationalTradingReadiness": operationalTradingReadiness,
            "operationalTradingReadinessBlocksPaperOperation": False,
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
