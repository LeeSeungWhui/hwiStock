"""
파일명: backend/lib/Middleware.py
작성자: LSH
갱신일: 2026-02-25
설명: 요청ID 전파 및 구조적 접근 로그 미들웨어
"""

import asyncio
import json
import ipaddress
import os
import time
import uuid
from typing import Callable, Awaitable

from fastapi import Request
from starlette.responses import Response as StarletteResponse
from starlette.middleware.base import BaseHTTPMiddleware

from lib.Logger import logger
from .Masking import maskUserIdentifierForLog
from .Database import getSqlCount, resetSqlCount
from .Config import getConfig
from .RequestContext import resetRequestId, setRequestId
from .UserAccessLog import writeUserAccessLog


async def writeUserAccessLogSafely(
    *,
    username: str,
    requestId: str,
    method: str,
    path: str,
    statusCode: int,
    latencyMs: int,
    sqlCount: int,
    clientIp: str | None,
) -> None:
    """
    설명: 요청 종료 후 사용자 접근 로그를 비차단 방식으로 적재하는 보호 래퍼
    처리 규칙: writeUserAccessLog 호출 인자를 그대로 전달하고, 본 요청 응답 흐름을 우선
    실패 동작: 로그 적재 예외는 삼키고 API 응답/이벤트 루프를 중단시키지 않는
    부작용: user_access_log 저장 시도가 발생할 수
    갱신일: 2026-02-27
    """
    try:
        await writeUserAccessLog(
            username=username,
            requestId=requestId,
            method=method,
            path=path,
            statusCode=statusCode,
            latencyMs=latencyMs,
            sqlCount=sqlCount,
            clientIp=clientIp,
        )
    except Exception:

        # 사용자 로그 적재 실패가 API 응답/백그라운드 루프를 깨지 않도록 방어
        pass


def parsePositiveInt(rawValue: object) -> int | None:
    """
    설명: 양의 정수 값만 파싱해서 반환. 호출 맥락의 제약을 기준으로 동작 기준 확정
    반환값: 1 이상 정수면 해당 값, 그 외 입력은 None
    갱신일: 2026-02-22
    """
    if rawValue is None:
        return None
    try:
        value = int(str(rawValue).strip())
        if value <= 0:
            return None
        return value
    except Exception:
        return None


def getSqlWarnThresholdFromConfig() -> int | None:
    """
    설명: config. ini 기반 SQL 경고 임계치(sql_warn_threshold) 조회
    우선순위 섹션: OBSERVABILITY > SERVER > DATABASE > DATABASE_*
    갱신일: 2026-02-22
    """
    try:
        config = getConfig()
    except Exception:
        return None

    sectionNames = ["OBSERVABILITY", "SERVER", "DATABASE"]
    try:
        sectionNames.extend([name for name in config.sections() if name.startswith("DATABASE_")])
    except Exception:
        pass

    for sectionName in sectionNames:
        try:
            if sectionName not in config:
                continue
            rawValue = config[sectionName].get("sql_warn_threshold")
            parsed = parsePositiveInt(rawValue)
            if parsed is not None:
                return parsed
        except Exception:
            continue
    return None


def getSqlWarnThreshold() -> int:
    """
    설명: 요청당 SQL 경고 임계치(환경변수 SQL_WARN_THRESHOLD) 조회
    처리 규칙: env 우선, 없으면 config, 둘 다 없으면 기본값 30을 사용
    갱신일: 2026-02-22
    """
    envThreshold = parsePositiveInt(os.getenv("SQL_WARN_THRESHOLD"))
    if envThreshold is not None:
        return envThreshold
    configThreshold = getSqlWarnThresholdFromConfig()
    if configThreshold is not None:
        return configThreshold
    return 30


def resolveClientIp(request: Request) -> str | None:
    """
    설명: 요청 헤더/소켓 정보를 기반으로 클라이언트 IP 추정
    우선순위: X-Forwarded-For(첫 IP) > X-Real-IP > request.client.host
    갱신일: 2026-02-22
    """
    try:
        forwardedFor = request.headers.get("X-Forwarded-For")
        if isinstance(forwardedFor, str) and forwardedFor.strip():
            first = forwardedFor.split(",")[0].strip()
            if first:
                return first
    except Exception:
        pass

    try:
        realIp = request.headers.get("X-Real-IP")
        if isinstance(realIp, str) and realIp.strip():
            return realIp.strip()
    except Exception:
        pass

    try:
        clientHost = request.client.host if request.client else None
        if isinstance(clientHost, str) and clientHost.strip():
            return clientHost
    except Exception:
        pass
    return None


def resolveAuthUsername(request: Request) -> str | None:
    """
    설명: 인증 의존성에서 주입한 request. state. authUsername 값을 조회. 호출 맥락의 제약을 기준으로 동작 기준 확정
    반환값: 공백 제거 후 유효 문자열 username 또는 None
    갱신일: 2026-02-22
    """
    try:
        raw = getattr(request.state, "authUsername", None)
    except Exception:
        raw = None
    if isinstance(raw, str) and raw.strip():
        return raw
    return None


def maskClientIpForLog(clientIp: str | None) -> str | None:
    """
    설명: 로그 출력용 클라이언트 IP 마스킹
    처리 규칙: IPv4는 마지막 octet을 `*`, IPv6는 앞 4블록만 남기고 나머지는 `*`로 마스킹
    갱신일: 2026-02-22
    """
    value = (clientIp or "").strip()
    if not value:
        return None
    try:
        parsedIp = ipaddress.ip_address(value)
    except Exception:
        return "***"
    if isinstance(parsedIp, ipaddress.IPv4Address):
        octets = value.split(".")
        if len(octets) == 4:
            return f"{octets[0]}.{octets[1]}.{octets[2]}.*"
        return "***"
    hextets = parsedIp.exploded.split(":")
    return ":".join(hextets[:4] + ["*"])


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    설명: Request-Id 생성/전파 및 구조적 JSON 접근 로그 기록
    갱신일: 2025-11-12
    """

    async def dispatch(self, request: Request, callNext: Callable[[Request], Awaitable[StarletteResponse]]) -> StarletteResponse:
        """
        설명: 요청 처리 시간/상태/경로 등을 수집하여 INFO 레벨로 로그 출력
        부작용: X-Request-Id 헤더 주입, 구조적 access 로그 기록, 인증 사용자 접근로그 백그라운드 적재를 수행
        갱신일: 2025-11-12
        """
        started = time.perf_counter()
        reqId = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        token = setRequestId(reqId)
        resetSqlCount()
        try:

            # 실제 비즈니스 핸들러 호출
            response = await callNext(request)

            # 응답 헤더에 요청 ID를 추가
            try:
                response.headers["X-Request-Id"] = reqId
            except Exception:
                pass

            elapsedMs = int((time.perf_counter() - started) * 1000)
            sqlCount = getSqlCount()
            level = "INFO"
            username = resolveAuthUsername(request)
            clientIp = resolveClientIp(request)
            maskedUsername = maskUserIdentifierForLog(username)
            maskedClientIp = maskClientIpForLog(clientIp)
            logObj = {
                "ts": int(time.time() * 1000),
                "level": level,
                "requestId": reqId,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": elapsedMs,
                "sql_count": sqlCount,
                "is_authenticated": bool(username),
                "msg": "access",
            }
            if maskedUsername:
                logObj["usernameMasked"] = maskedUsername
            if maskedClientIp:
                logObj["clientIpMasked"] = maskedClientIp

            # 구조적 로그를 위해 JSON 문자열로 기록
            msg = json.dumps(logObj, ensure_ascii=False)
            logger.info(msg)
            threshold = getSqlWarnThreshold()
            if sqlCount >= threshold:
                warnObj = {
                    "ts": int(time.time() * 1000),
                    "level": "WARNING",
                    "requestId": reqId,
                    "path": request.url.path,
                    "method": request.method,
                    "status": response.status_code,
                    "sql_count": sqlCount,
                    "sql_warn_threshold": threshold,
                    "msg": "sql_count_high",
                }
                logger.warning(json.dumps(warnObj, ensure_ascii=False))
            if username:
                try:
                    asyncio.create_task(
                        writeUserAccessLogSafely(
                            username=username,
                            requestId=reqId,
                            method=request.method,
                            path=request.url.path,
                            statusCode=int(response.status_code),
                            latencyMs=elapsedMs,
                            sqlCount=sqlCount,
                            clientIp=clientIp,
                        )
                    )
                except Exception:

                    # 태스크 생성 실패가 API 응답을 깨지 않도록 방어
                    pass
            return response
        finally:
            resetRequestId(token)
            resetSqlCount()
