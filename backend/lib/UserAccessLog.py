"""
파일명: backend/lib/UserAccessLog.py
작성자: LSH
갱신일: 2026-02-25
설명: 인증 사용자 접근 로그를 DB 테이블(T_USER_LOG)에 적재
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import time
import uuid
from typing import Optional

import httpx

from lib import Database as DB
from lib.Logger import logger
from .Masking import maskUserIdentifierForLog
from .Config import getConfig


ipGeoCache: dict[str, dict[str, object]] = {}
ipGeoCacheLock = asyncio.Lock()


def parseBool(rawValue: object, defaultValue: bool = False) -> bool:
    """
    설명: 다양한 입력값을 bool로 파싱
    처리 규칙: 문자열은 소문자 정규화 후 truthy 집합(1/true/yes/on)으로 판별
    반환값: 파싱 실패/None 입력 시 defaultValue를 반환
    갱신일: 2026-02-22
    """
    if rawValue is None:
        return defaultValue
    try:
        return str(rawValue).strip().lower() in {"1", "true", "yes", "on"}
    except Exception:
        return defaultValue


def parsePositiveInt(rawValue: object, defaultValue: int) -> int:
    """
    설명: 양의 정수만 허용해 파싱하고, 실패 시 기본값 반환
    갱신일: 2026-02-22
    """
    try:
        value = int(str(rawValue).strip())
        if value <= 0:
            return defaultValue
        return value
    except Exception:
        return defaultValue


def getIpGeoEnabled() -> bool:
    """
    설명: IP 위치 추정 기능 on/off 판단 규칙(환경변수 우선)을 담당하는 설정 조회 유틸
    우선순위: 환경변수(IP_GEO_ENABLED) > config(OBSERVABILITY.ip_geo_enabled)
    갱신일: 2026-02-22
    """
    envValue = os.getenv("IP_GEO_ENABLED")
    if envValue is not None:
        return parseBool(envValue, False)
    try:
        config = getConfig()
        if "OBSERVABILITY" in config:
            return parseBool(config["OBSERVABILITY"].get("ip_geo_enabled"), False)
    except Exception:
        pass
    return False


def getIpGeoTimeoutMs() -> int:
    """
    설명: 외부 IP 위치 조회 타임아웃(ms) 결정 규칙(환경변수 우선) 유틸
    우선순위: 환경변수(IP_GEO_TIMEOUT_MS) > config(API_POLICY.ipGeoLookup.request_timeout_sec) > config(API_POLICY.request_timeout_sec)
    갱신일: 2026-02-22
    """
    envValue = os.getenv("IP_GEO_TIMEOUT_MS")
    if envValue is not None:
        return parsePositiveInt(envValue, 5000)
    try:
        config = getConfig()
        globalPolicy = config["API_POLICY"] if "API_POLICY" in config else None
        ipGeoPolicy = config["API_POLICY.ipGeoLookup"] if "API_POLICY.ipGeoLookup" in config else None
        timeoutSec = None
        if ipGeoPolicy:
            timeoutSec = ipGeoPolicy.get("request_timeout_sec")
        if timeoutSec is None and globalPolicy:
            timeoutSec = globalPolicy.get("request_timeout_sec")
        if timeoutSec is not None:
            return max(100, parsePositiveInt(timeoutSec, 5) * 1000)
    except Exception:
        pass
    return 5000


def getIpGeoCacheTtlSec() -> int:
    """
    설명: IP 위치 조회 캐시 TTL(초) 결정 규칙(환경변수 우선) 유틸
    우선순위: 환경변수(IP_GEO_CACHE_TTL_SEC) > config(OBSERVABILITY.ip_geo_cache_ttl_sec)
    갱신일: 2026-02-22
    """
    envValue = os.getenv("IP_GEO_CACHE_TTL_SEC")
    if envValue is not None:
        return parsePositiveInt(envValue, 3600)
    try:
        config = getConfig()
        if "OBSERVABILITY" in config:
            return parsePositiveInt(config["OBSERVABILITY"].get("ip_geo_cache_ttl_sec"), 3600)
    except Exception:
        pass
    return 3600




def normalizeIp(clientIp: Optional[str]) -> Optional[str]:
    """
    설명: 원본 클라이언트 IP 문자열 표준화(공백/브래킷 제거) 유틸
    처리 규칙: 공백/대괄호([::1])를 제거하고 비어 있으면 None으로 반환
    반환값: 정규화된 IP 문자열 또는 None을 반환
    갱신일: 2026-02-22
    """
    rawIp = (clientIp or "").strip()
    if not rawIp:
        return None

    # IPv6 bracket 제거([::1] 형태 대비)
    if rawIp.startswith("[") and rawIp.endswith("]"):
        rawIp = rawIp[1:-1]
    return rawIp or None


def classifyIpLocal(ipValue: str) -> tuple[str, str]:
    """
    설명: 사설/루프백/예약 IP 여부 분류
    반환: (위치텍스트, 소스)
    갱신일: 2026-02-22
    """
    try:
        addr = ipaddress.ip_address(ipValue)
    except Exception:
        return ("IP_INVALID", "IP_PARSE")
    if addr.is_loopback:
        return ("LOOPBACK", "IP_LOCAL")
    if addr.is_private:
        return ("PRIVATE_NET", "IP_LOCAL")
    if addr.is_link_local:
        return ("LINK_LOCAL", "IP_LOCAL")
    if addr.is_reserved:
        return ("RESERVED", "IP_LOCAL")
    if addr.is_multicast:
        return ("MULTICAST", "IP_LOCAL")
    if addr.is_unspecified:
        return ("UNSPECIFIED", "IP_LOCAL")
    return ("PUBLIC_IP", "IP_LOCAL")


def buildLocationText(geoJson: dict) -> str:
    """
    설명: 외부 IP 위치 조회 결과를 로그 저장용 위치 문자열로 조합하 포매터
    처리 규칙: country/region/city를 순서대로 조합하고 값이 없으면 PUBLIC_IP를 사용
    반환값: 로그 적재용 위치 문자열을 반환
    갱신일: 2026-02-22
    """
    countryCode = str(geoJson.get("country_code") or "").strip()
    countryName = str(geoJson.get("country") or "").strip()
    regionName = str(geoJson.get("region") or "").strip()
    cityName = str(geoJson.get("city") or "").strip()
    parts = []
    if countryCode:
        parts.append(countryCode)
    elif countryName:
        parts.append(countryName)
    if regionName:
        parts.append(regionName)
    if cityName:
        parts.append(cityName)
    if parts:
        return " / ".join(parts)
    return "PUBLIC_IP"


async def getIpGeoFromRemote(ipValue: str, requestId: Optional[str] = None) -> Optional[dict]:
    """
    설명: 외부 API(ipwho.is) 호출로 공인 IP의 대략 위치를 가져오는 원격 조회 함수
    처리 규칙: 200 응답 + success=true dict일 때만 결과를 채택
    실패 동작: 타임아웃/비정상 응답/파싱 실패 시 None을 반환
    갱신일: 2026-02-22
    """
    timeoutMs = getIpGeoTimeoutMs()
    timeoutSec = max(0.1, timeoutMs / 1000.0)
    url = f"https://ipwho.is/{ipValue}"
    try:
        async with httpx.AsyncClient(timeout=timeoutSec) as client:
            response = await client.get(url, headers={"Accept": "application/json"})
            if response.status_code != 200:
                logger.warning(
                    json.dumps(
                        {
                            "event": "ip_geo.lookup.failed",
                            "target": url,
                            "timeoutMs": timeoutMs,
                            "requestId": requestId,
                            "statusCode": response.status_code,
                        },
                        ensure_ascii=False,
                    )
                )
                return None
            data = response.json()
            if not isinstance(data, dict):
                logger.warning(
                    json.dumps(
                        {
                            "event": "ip_geo.lookup.failed",
                            "target": url,
                            "timeoutMs": timeoutMs,
                            "requestId": requestId,
                            "reason": "INVALID_JSON_BODY",
                        },
                        ensure_ascii=False,
                    )
                )
                return None
            if data.get("success") is False:
                logger.warning(
                    json.dumps(
                        {
                            "event": "ip_geo.lookup.failed",
                            "target": url,
                            "timeoutMs": timeoutMs,
                            "requestId": requestId,
                            "reason": "REMOTE_SUCCESS_FALSE",
                        },
                        ensure_ascii=False,
                    )
                )
                return None
            return data
    except Exception as exc:
        logger.warning(
            json.dumps(
                {
                    "event": "ip_geo.lookup.failed",
                    "target": url,
                    "timeoutMs": timeoutMs,
                    "requestId": requestId,
                    "reason": str(exc),
                },
                ensure_ascii=False,
            )
        )
        raise


async def resolveIpLocation(clientIp: Optional[str], requestId: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """
    설명: IP 기반 위치 텍스트/소스 해석 파이프라인 처리
    반환값: (ipLocTxt, ipLocSrc)
    갱신일: 2026-02-22
    """
    ipValue = normalizeIp(clientIp)
    if not ipValue:
        return (None, None)

    localLocTxt, localSource = classifyIpLocal(ipValue)
    if localLocTxt != "PUBLIC_IP":
        return (localLocTxt, localSource)
    if not getIpGeoEnabled():
        return ("PUBLIC_IP", "IP_PUBLIC")

    nowMs = int(time.time() * 1000)
    async with ipGeoCacheLock:
        cached = ipGeoCache.get(ipValue)
        if cached:
            expiresAt = int(cached.get("expiresAtMs", 0) or 0)
            if expiresAt > nowMs:
                return (
                    str(cached.get("ipLocTxt") or "PUBLIC_IP"),
                    str(cached.get("ipLocSrc") or "IP_GEO_CACHE"),
                )
            ipGeoCache.pop(ipValue, None)

    try:
        geoJson = await getIpGeoFromRemote(ipValue, requestId=requestId)
        if not geoJson:
            return ("PUBLIC_IP", "IP_GEO_MISS")
        ipLocTxt = buildLocationText(geoJson)
        ipLocSrc = "IP_GEO_REMOTE"
        ttlSec = getIpGeoCacheTtlSec()
        async with ipGeoCacheLock:
            ipGeoCache[ipValue] = {
                "ipLocTxt": ipLocTxt,
                "ipLocSrc": ipLocSrc,
                "expiresAtMs": nowMs + (ttlSec * 1000),
            }
        return (ipLocTxt, ipLocSrc)
    except Exception:
        return ("PUBLIC_IP", "IP_GEO_FAIL")


async def writeUserAccessLog(
    *,
    username: Optional[str],
    requestId: Optional[str],
    method: Optional[str],
    path: Optional[str],
    statusCode: int,
    latencyMs: int,
    sqlCount: int,
    clientIp: Optional[str],
    dbName: Optional[str] = None,
) -> None:
    """
    설명: 인증 사용자 접근 로그를 T_USER_LOG에 저장
    처리 규칙: username 미존재/DB 미초기화 시 즉시 종료하고, 위치 정보는 비동기 조회 후 bind에 반영
    실패 동작: INSERT 실패는 warning 로그만 남기고 요청 흐름에는 예외를 전파하지 않는
    부작용: T_USER_LOG 테이블에 접근 로그 레코드를 적재
    갱신일: 2026-02-22
    """
    userId = (username or "").strip()
    if not userId:
        return

    targetDbName = (dbName or "").strip() or DB.getPrimaryDbName()
    db = DB.getManager(targetDbName)
    if not db:
        return

    bindValues = {
        "logId": uuid.uuid4().hex,
        "userId": userId,
        "reqId": (requestId or "").strip() or None,
        "reqMthd": (method or "").strip() or "UNKNOWN",
        "reqPath": (path or "").strip() or "/",
        "resCd": int(statusCode),
        "latencyMs": max(0, int(latencyMs)),
        "sqlCnt": max(0, int(sqlCount)),
        "clientIp": (clientIp or "").strip() or None,
        "ipLocTxt": None,
        "ipLocSrc": None,
    }
    ipLocTxt, ipLocSrc = await resolveIpLocation(bindValues["clientIp"], requestId=bindValues["reqId"])
    bindValues["ipLocTxt"] = ipLocTxt
    bindValues["ipLocSrc"] = ipLocSrc
    try:
        await db.executeQuery("common.userAccessLogInsert", bindValues)
    except Exception as e:
        logger.warning(
            json.dumps(
                {
                    "event": "db.user_log.insert.failed",
                    "dbName": targetDbName,
                    "requestId": requestId,
                    "usernameMasked": maskUserIdentifierForLog(userId),
                    "error": str(e),
                },
                ensure_ascii=False,
            )
        )
