"""
파일명: backend/lib/Idempotency.py
작성자: LSH
갱신일: 2026-04-08
설명: 멱등성 키 저장소/검증/중복 재실행 방지 공용 유틸
"""

import hashlib
import json
import re
import time
from typing import Any

from lib import Database as DB
from lib.Casing import convertKeysToCamelCase
from lib.ServiceError import ServiceError

IDEMPOTENCY_STATUS_PENDING = "pending"
IDEMPOTENCY_STATUS_DONE = "done"
IDEMPOTENCY_TTL_MS = 24 * 60 * 60 * 1000
IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,120}$")


def getIdempotencyDbManager():
    """
    설명: 멱등성 저장소에서 사용할 기본 DB 매니저 확보
    실패 동작: 매니저가 없으면 ServiceError("DB_NOT_READY") 발생
    반환값: 초기화된 DB 매니저 인스턴스
    갱신일: 2026-03-06
    """
    db = DB.getManager()
    if not db:
        raise ServiceError("DB_NOT_READY")
    return db


def normalizeIdempotencyKey(rawValue: str | None) -> str | None:
    """
    설명: Idempotency-Key 헤더를 길이/문자셋 기준으로 정규화
    실패 동작: 누락/형식 위반 시 ServiceError("IDEMPOTENCY_422_INVALID_INPUT") 발생
    반환값: trim 처리된 멱등성 키 문자열
    갱신일: 2026-03-06
    """
    if rawValue is None:
        return None
    if not isinstance(rawValue, str):
        raise ServiceError("IDEMPOTENCY_422_INVALID_INPUT")
    key = rawValue.strip()
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(key):
        raise ServiceError("IDEMPOTENCY_422_INVALID_INPUT")
    return key


def isDuplicateIdempotencyConstraintError(error: Exception) -> bool:
    """
    설명: 멱등성 저장 unique 제약 위반 예외 판별
    반환값: duplicate/unique 계열 예외면 True
    갱신일: 2026-03-06
    """
    text = str(error or "").lower()
    if not text:
        return False
    duplicateTokens = (
        "duplicate key",
        "duplicate entry",
        "unique constraint failed",
        "violates unique constraint",
    )
    if any(token in text for token in duplicateTokens):
        return True
    if "integrityerror" in text and ("unique" in text or "duplicate" in text):
        return True
    return False


def buildIdempotencyPayloadDigest(scopeType: str, payload: dict[str, Any]) -> str:
    """
    설명: scope/payload 기준 멱등성 비교용 SHA-256 digest 생성
    처리 규칙: JSON sort_keys + compact separators로 직렬화해 비교 일관성 유지
    반환값: 64자리 hex digest 문자열
    갱신일: 2026-03-06
    """
    normalizedPayload = payload if isinstance(payload, dict) else {}
    payloadJson = json.dumps(normalizedPayload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    raw = f"{scopeType}:{payloadJson}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def ensureIdempotencyStore() -> Any:
    """
    설명: 멱등성 저장소 테이블 준비와 기본 정리 수행
    반환값: 멱등성 저장에 사용할 DB 매니저 인스턴스
    갱신일: 2026-03-06
    """
    manager = getIdempotencyDbManager()
    await manager.executeQuery("idempotency.ensureTable")
    await manager.executeQuery("idempotency.deleteExpired", {"nowMs": int(time.time() * 1000)})
    return manager


async def getIdempotencyEntry(scopeType: str, idempotencyKey: str) -> dict[str, Any] | None:
    """
    설명: scope/key 기준 멱등성 저장 항목 조회
    반환값: camelCase 변환된 저장 항목 dict 또는 None
    갱신일: 2026-03-06
    """
    manager = await ensureIdempotencyStore()
    row = await manager.fetchOneQuery(
        "idempotency.getEntry",
        {"scopeType": scopeType, "idempotencyKey": idempotencyKey},
    )
    if not row:
        return None
    return convertKeysToCamelCase(row)


async def beginIdempotencyRequest(scopeType: str, idempotencyKey: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    """
    설명: 멱등성 요청 시작 시 키 선점 또는 기존 결과 판별
    실패 동작: 동일 키 payload 불일치면 409 mismatch, 처리 중이면 409 in-progress 발생
    반환값: new/replay 상태와 payloadDigest/result를 담은 dict
    갱신일: 2026-03-06
    """
    normalizedKey = normalizeIdempotencyKey(idempotencyKey)
    if normalizedKey is None:
        return {"status": "new", "payloadDigest": None}
    manager = await ensureIdempotencyStore()
    payloadDigest = buildIdempotencyPayloadDigest(scopeType, payload)
    params = {
        "scopeType": scopeType,
        "idempotencyKey": normalizedKey,
        "statusCd": IDEMPOTENCY_STATUS_PENDING,
        "payloadDigest": payloadDigest,
        "responseJson": None,
        "expiresAtMs": int(time.time() * 1000) + IDEMPOTENCY_TTL_MS,
    }
    try:
        await manager.executeQuery("idempotency.insertEntry", params)
        return {"status": "new", "payloadDigest": payloadDigest}
    except Exception as error:
        if not isDuplicateIdempotencyConstraintError(error):
            raise

    existing = await getIdempotencyEntry(scopeType, normalizedKey)
    if not existing:
        raise ServiceError("IDEMPOTENCY_409_IN_PROGRESS")
    if existing.get("payloadDigest") != payloadDigest:
        raise ServiceError("IDEMPOTENCY_409_PAYLOAD_MISMATCH")
    if existing.get("statusCd") == IDEMPOTENCY_STATUS_DONE:
        responseJson = existing.get("responseJson")
        if isinstance(responseJson, str) and responseJson.strip():
            try:
                parsed = json.loads(responseJson)
                if isinstance(parsed, dict):
                    return {"status": "replay", "payloadDigest": payloadDigest, "result": parsed}
            except Exception:
                pass
    raise ServiceError("IDEMPOTENCY_409_IN_PROGRESS")


async def completeIdempotencyRequest(scopeType: str, idempotencyKey: str | None, result: dict[str, Any]) -> None:
    """
    설명: 멱등성 처리 완료 후 replay용 응답 payload 저장
    부작용: 저장 항목 status를 done으로 갱신하고 responseJson을 기록
    갱신일: 2026-03-06
    """
    normalizedKey = normalizeIdempotencyKey(idempotencyKey)
    if normalizedKey is None:
        return
    manager = await ensureIdempotencyStore()
    await manager.executeQuery(
        "idempotency.completeEntry",
        {
            "scopeType": scopeType,
            "idempotencyKey": normalizedKey,
            "statusCd": IDEMPOTENCY_STATUS_DONE,
            "responseJson": json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "expiresAtMs": int(time.time() * 1000) + IDEMPOTENCY_TTL_MS,
        },
    )
