"""
파일명: backend/lib/RateLimit.py
작성자: LSH
갱신일: 2026-02-24
설명: 간단한 인메모리 속도 제한기와 FastAPI용 체크 헬퍼
"""

from __future__ import annotations

import os
import time
from collections import deque
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from lib.Response import errorResponse


class RateLimiter:
    """설명: 간단한 인메모리 속도 제한기 갱신일: 2025-11-12"""
    """
    초간단 인메모리 속도 제한기(프로세스 단위).
    - limit: 윈도우 내 허용 횟수
    - windowSec: 윈도우 길이(초)
    """

    def __init__(self, limit: int = 5, windowSec: int = 60, sweepEvery: int = 256):
        """
        설명: 제한 횟수/윈도우/청소 주기 초기화
        처리 규칙: sweepEvery는 최소 1로 보정하고 내부 store/hitCount를 초기화
        부작용: 인메모리 카운터 상태를 새로 생성
        갱신일: 2026-02-27
        """
        self.limit = int(limit)
        self.window = int(windowSec)
        self.store = {}
        self.sweepEvery = max(1, int(sweepEvery))
        self.hitCount = 0

    def now(self):
        """
        설명: 시스템 시계 변경 영향 없이 윈도우 계산에 쓰는 monotonic 타임스탬프 제공
        반환값: rate-limit 윈도우 계산에 사용하는 monotonic float 초 값
        갱신일: 2025-11-12
        """
        return time.monotonic()

    def sweepExpired(self, nowSec: float) -> None:
        """
        설명: 윈도우를 벗어난 키를 일괄 정리해 메모리 증 완화
        처리 규칙: 각 키의 오래된 타임스탬프를 제거하고 비어 있는 키는 store에서 제거
        부작용: self.store 내부 상태를 직접 변경
        갱신일: 2026-02-24
        """
        expiredKeys = []
        for key, timestamps in list(self.store.items()):
            while timestamps and nowSec - timestamps[0] > self.window:
                timestamps.popleft()
            if not timestamps:
                expiredKeys.append(key)
        for key in expiredKeys:
            self.store.pop(key, None)

    def hit(self, key: str, *, commit: bool = True):
        """
        설명: 주어진 키로 속도 제한 검사
        - commit=True: 검사 + 히트 기록(윈도우 내 카운트 증가)
        - commit=False: 검사만 수행(카운트 증가 없음)
        갱신일: 2026-01-15
        """
        now = self.now()
        self.hitCount += 1
        if self.hitCount % self.sweepEvery == 0:
            self.sweepExpired(now)
        timestamps = self.store.get(key)
        if timestamps is None:
            if not commit:
                return True, 0
            timestamps = deque()
            self.store[key] = timestamps
        while timestamps and now - timestamps[0] > self.window:
            timestamps.popleft()
        if not timestamps and not commit:
            self.store.pop(key, None)
            return True, 0
        if len(timestamps) >= self.limit:
            retryAfter = max(1, int(self.window - (now - timestamps[0])))
            return False, retryAfter
        if commit:
            timestamps.append(now)
        return True, 0


def parseRateLimitLimit(defaultValue: int = 5) -> int:
    """
    설명: AUTH_RATE_LIMIT 환경변수를 rate-limit limit 정수로 파싱
    처리 규칙: 숫자가 아니거나 1 미만이면 defaultValue로 폴백
    반환값: 1 이상 정수 limit 값
    갱신일: 2026-03-02
    """
    rawValue = os.getenv("AUTH_RATE_LIMIT", str(defaultValue))
    try:
        parsedValue = int(str(rawValue).strip())
    except Exception:
        return int(defaultValue)
    if parsedValue < 1:
        return int(defaultValue)
    return parsedValue


globalRateLimiter = RateLimiter(limit=parseRateLimitLimit(), windowSec=60)

def resolveClientIp(request: Request) -> str:
    """
    설명: 요청의 클라이언트 IP를 최대한 정확히 추정
    - 기본: request.client.host
    - 프록시 뒤: TRUST_PROXY_HEADERS=true 일 때 X-Forwarded-For 첫 IP를 사용
    갱신일: 2026-01-15
    """
    trustProxy = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in ("1", "true", "yes")
    if trustProxy:
        xff = request.headers.get("X-Forwarded-For")
        if isinstance(xff, str) and xff.strip():
            first = xff.split(",")[0].strip()
            if first:
                return first
    return getattr(request.client, "host", None) or "unknown"


def checkRateLimit(request: Request, username: Optional[str] = None, *, commit: bool = True) -> Optional[JSONResponse]:
    """
    설명: IP/사용자별 속도 제한 검사
    처리 규칙: 키(ip:{ip}, user:{username})를 순회해 하나라도 초과면 즉시 429를 반환
    반환값: 제한 초과 시 Retry-After/no-store 헤더가 포함된 JSONResponse, 통과 시 None을 반환
    갱신일: 2026-01-15
    """
    ip = resolveClientIp(request)
    keys = [f"ip:{ip}"]
    if username:
        keys.append(f"user:{username}")
    for key in keys:
        ok, retryAfter = globalRateLimiter.hit(key, commit=commit)
        if not ok:
            return JSONResponse(
                status_code=429,
                content=errorResponse(message="too many requests", code="AUTH_429_RATE_LIMIT"),
                headers={"Retry-After": str(retryAfter), "Cache-Control": "no-store"},
            )
    return None
