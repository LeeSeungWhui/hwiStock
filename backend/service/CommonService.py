"""
파일명: backend/service/CommonService.py
작성자: LSH
갱신일: 2026-02-24
설명: 공통(헬스체크 및 레디니스) 서비스 로직
"""

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Dict, Tuple, Any, List

from lib import Database as DB

startedAt = datetime.now(timezone.utc)


def versionInfo() -> Dict[str, str]:
    """
    설명: 버전/시작 시각 메타 정보를 반환. 호출 맥락의 제약을 기준으로 동작 기준 확정
    반환값: version/gitSha/startedAt를 포함한 진단용 메타 dict를 반환
    갱신일: 2026-02-24
    """
    version = os.getenv("APP_VERSION", "dev")
    gitSha = os.getenv("GIT_SHA", "unknown")
    return {
        "version": version,
        "gitSha": gitSha,
        "startedAt": startedAt.isoformat(),
    }


def parseReadyzTimeoutMs(defaultValue: int = 300) -> int:
    """
    설명: READYZ_TIMEOUT_MS 환경변수를 readiness timeout(ms) 정수로 파싱
    처리 규칙: 숫자가 아니거나 0 이하 값이면 defaultValue로 폴백
    반환값: 양수 timeout(ms) 정수
    갱신일: 2026-03-02
    """
    rawValue = os.getenv("READYZ_TIMEOUT_MS", str(defaultValue))
    try:
        timeoutMs = int(str(rawValue).strip())
    except Exception:
        return int(defaultValue)
    if timeoutMs <= 0:
        return int(defaultValue)
    return timeoutMs


async def healthz(_: Dict | None = None) -> Dict[str, str | int | bool]:
    """
    설명: 프로세스 기동 상태와 업타임 정보를 반환. 호출 맥락의 제약을 기준으로 동작 기준 확정
    처리 규칙: 현재 UTC 시각 기준으로 startedAt과의 차이를 계산해 uptimeSeconds를 생성
    반환값: ok/version/gitSha/startedAt/uptimeSeconds를 포함한 헬스 payload dict
    갱신일: 2026-02-28
    """
    now = datetime.now(timezone.utc)
    uptimeSeconds = int((now - startedAt).total_seconds())
    return {
        "ok": True,
        **versionInfo(),
        "uptimeSeconds": uptimeSeconds,
    }


async def readyz(_: Dict | None = None) -> Tuple[Dict[str, Any], bool]:
    """
    설명: 레디니스 체크. DB 핑 및 타임아웃/지표를 포함해 관측성 확장
    처리 규칙: 유지보수 모드 또는 DB ping 실패 시 ok=False로 전환
    반환값: (상태 payload, 준비 완료 여부 bool) 튜플을 반환
    갱신일: 2025-12-03
    """
    maintenance = os.getenv("MAINTENANCE_MODE", "false").lower() in ("1", "true", "yes")
    checks: Dict[str, Any] = {}
    ok = True

    # 유지보수 모드면 즉시 비정상 처리
    if maintenance:
        ok = False
    else:
        dbStatus = "skipped"
        dbLatencies: List[int] = []
        dbTargets: List[str] = []
        timeoutMs = parseReadyzTimeoutMs()

        try:
            try:
                primary = DB.getPrimaryDbName()
            except Exception:
                primary = None

            targets = [primary] if primary in DB.dbManagers else list(DB.dbManagers.keys())

            if not targets:
                dbStatus = "down"
                ok = False
            else:
                dbStatus = "up"
                dbTargets = list(targets)

                async def pingTarget(name: str) -> Tuple[str, int | None, Exception | None]:
                    mgr = DB.dbManagers[name]
                    queryName = "common.ping"
                    try:
                        if hasattr(mgr, "fetchOneQuery"):
                            started = time.perf_counter()
                            await asyncio.wait_for(
                                mgr.fetchOneQuery(queryName),
                                timeout=timeoutMs / 1000.0,
                            )
                        else:
                            query = None
                            if hasattr(mgr, "queryManager"):
                                query = mgr.queryManager.getQuery(queryName)
                            if not query or not hasattr(mgr, "fetchOne"):
                                raise RuntimeError(f"readyz ping query not found: {queryName}")
                            started = time.perf_counter()
                            await asyncio.wait_for(
                                mgr.fetchOne(query),
                                timeout=timeoutMs / 1000.0,
                            )
                        elapsedMs = int((time.perf_counter() - started) * 1000)
                        return name, elapsedMs, None
                    except Exception as exc:
                        return name, None, exc

                pingResults = await asyncio.gather(*(pingTarget(name) for name in targets))
                for _, elapsedMs, error in pingResults:
                    if error is not None:
                        dbStatus = "down"
                        ok = False
                        continue
                    if elapsedMs is not None:
                        dbLatencies.append(elapsedMs)
        except Exception:
            dbStatus = "down"
            ok = False

        checks["db"] = dbStatus
        checks["dbTimeoutMs"] = timeoutMs
        checks["dbTargets"] = dbTargets
        if dbLatencies:
            checks["dbLatencyMs"] = max(dbLatencies)

    payload: Dict[str, Any] = {"ok": ok, **checks}
    return payload, ok
