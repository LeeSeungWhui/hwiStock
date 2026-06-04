"""
파일명: backend/lib/Casing.py
작성자: LSH
갱신일: 2026-02-22
설명: snake_case → camelCase 변환 유틸(응답/데이터 매핑용)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def toCamelCaseKey(key: str) -> str:
    """
    설명: snake_case 문자열 키를 camelCase로 정규화. 호출 맥락의 제약을 기준으로 동작 기준 확정
    처리 규칙: 구분자 `_`가 없으면 원본을 유지하되 전체 대문자 키는 소문자로 변환
    반환값: 변환된 키 문자열을 반환하며, 문자열이 아닌 입력은 그대로 반환
    갱신일: 2026-02-22
    """
    if not isinstance(key, str):
        return key
    if "_" not in key:
        if key.isupper():
            return key.lower()
        return key
    normalizedParts = [p.lower() for p in key.split("_") if p]
    if not normalizedParts:
        return key
    first = normalizedParts[0]
    rest = [(p[:1].upper() + p[1:]) if p else "" for p in normalizedParts[1:]]
    return first + "".join(rest)


def convertKeysToCamelCase(value: Any) -> Any:
    """
    설명: dict/list 내부의 모든 키를 재귀적으로 camelCase로 변환. 호출 맥락의 제약을 기준으로 동작 기준 확정
    처리 규칙: list는 각 원소를 재귀 처리하고 dict는 문자열 키만 변환한 새 dict를 생성
    반환값: 입력 구조를 유지한 변환 결과를 반환(스칼라는 원본 그대로 반환)
    갱신일: 2026-02-22
    """
    if isinstance(value, list):
        return [convertKeysToCamelCase(v) for v in value]
    if isinstance(value, dict):
        converted: dict[Any, Any] = {}
        for k, v in value.items():
            if isinstance(k, str):
                converted[toCamelCaseKey(k)] = convertKeysToCamelCase(v)
            else:
                converted[k] = convertKeysToCamelCase(v)
        return converted
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
