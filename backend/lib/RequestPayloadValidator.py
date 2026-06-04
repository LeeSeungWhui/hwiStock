"""
파일명: backend/lib/RequestPayloadValidator.py
작성자: LSH
갱신일: 2026-04-08
설명: 라우터 JSON payload 읽기/기본 타입검증 공통 유틸
"""

import json
from typing import Any

from fastapi import Request

from lib.ServiceError import ServiceError


def matchesPayloadType(value: Any, expectedType: str) -> bool:
    """
    설명: request payload 값이 기대 타입 라벨과 일치하는지 판별
    처리 규칙: bool/int 경계는 엄격히 분리하고 number는 int/float 둘 다 허용
    반환값: 타입 일치 여부 bool
    갱신일: 2026-03-12
    """
    if expectedType == "str":
        return isinstance(value, str)
    if expectedType == "bool":
        return isinstance(value, bool)
    if expectedType == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expectedType == "number":
        return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)
    if expectedType == "str_list":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if expectedType == "str_or_str_list":
        return isinstance(value, str) or (isinstance(value, list) and all(isinstance(item, str) for item in value))
    return False


async def readJsonPayloadDict(request: Request) -> dict[str, Any] | None:
    """
    설명: 요청 본문을 JSON dict로 안전하게 파싱
    실패 동작: 파싱 실패 또는 dict 타입 불일치 시 None 반환
    반환값: JSON object 본문 dict 또는 None
    갱신일: 2026-03-12
    """
    try:
        payload = await request.json()
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


async def readOptionalJsonPayloadDict(request: Request) -> tuple[dict[str, Any], bool]:
    """
    설명: 빈 본문을 허용하는 JSON dict payload를 shared boundary에서 파싱
    실패 동작: 빈 본문은 ({}, True), 파싱 실패 또는 dict 타입 불일치는 ({}, False)
    반환값: (payload dict, 유효 여부)
    갱신일: 2026-06-04
    """
    rawBody = await request.body()
    if not rawBody:
        return {}, True
    try:
        payload = json.loads(rawBody.decode("utf-8"))
    except Exception:
        return {}, False
    if not isinstance(payload, dict):
        return {}, False
    return payload, True


def validatePayloadTypes(
    payload: dict[str, Any] | None,
    *,
    requiredFieldTypeMap: dict[str, str] | None = None,
    optionalFieldTypeMap: dict[str, str] | None = None,
    excludeNone: bool = False,
    errorCode: str = "SAMPLE_422_INVALID_INPUT",
) -> dict[str, Any]:
    """
    설명: JSON payload dict의 필수/선택 필드 타입을 1차 검증
    실패 동작: payload가 dict가 아니거나 타입이 어긋나면 ServiceError(errorCode) 발생
    반환값: 허용 필드만 남긴 plain dict
    갱신일: 2026-03-12
    """
    requiredMap = requiredFieldTypeMap or {}
    optionalMap = optionalFieldTypeMap or {}
    if not isinstance(payload, dict):
        raise ServiceError(errorCode)

    normalizedPayload: dict[str, Any] = {}
    for fieldName, expectedType in requiredMap.items():
        if fieldName not in payload:
            raise ServiceError(errorCode)
        fieldValue = payload.get(fieldName)
        if fieldValue is None or not matchesPayloadType(fieldValue, expectedType):
            raise ServiceError(errorCode)
        normalizedPayload[fieldName] = fieldValue

    for fieldName, expectedType in optionalMap.items():
        if fieldName not in payload:
            if not excludeNone:
                normalizedPayload[fieldName] = None
            continue
        fieldValue = payload.get(fieldName)
        if fieldValue is None:
            if not excludeNone:
                normalizedPayload[fieldName] = None
            continue
        if not matchesPayloadType(fieldValue, expectedType):
            raise ServiceError(errorCode)
        normalizedPayload[fieldName] = fieldValue

    return normalizedPayload
