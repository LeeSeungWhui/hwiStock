"""
파일명: backend/lib/Response.py
작성자: LSH
갱신일: 2026-06-05
설명: 공통 응답 스키마/헬퍼. { status, message, result, count. , code. , requestId }
"""

from decimal import Decimal
from typing import Any, Optional, Dict

from pydantic import BaseModel

from .RequestContext import getRequestId


class StandardResponse(BaseModel):
    status: bool = True
    message: str = "success"
    result: Optional[Any] = None
    count: Optional[int] = None  # 리스트 응답일 때만 포함
    code: Optional[str] = None
    requestId: Optional[str] = None


def toJsonSafe(value: Any) -> Any:
    """
    설명: JSONResponse 직렬화 전 Decimal 등 비-JSON 타입을 원시값으로 변환
    처리 규칙: dict/list/tuple은 재귀 변환하고 Decimal은 int/float로 축소
    반환값: json.dumps 가능한 구조
    갱신일: 2026-06-05
    """
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, dict):
        return {key: toJsonSafe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [toJsonSafe(item) for item in value]
    if isinstance(value, tuple):
        return [toJsonSafe(item) for item in value]
    return value


def dumpModel(model: BaseModel) -> Dict[str, Any]:
    """
    설명: Pydantic 모델을 dict로 직렬화
    처리 규칙: model_dump(exclude_none=True)로 표준 응답 형태를 유지
    반환값: exclude_none이 적용된 표준 dict 응답
    갱신일: 2026-02-28
    """
    return model.model_dump(exclude_none=True)


def successResponse(result: Any = None, message: str = "success") -> Dict[str, Any]:
    """
    설명: 성공 응답 본문 생성. 리스트일 경우 count 자동 포함
    갱신일: 2026-06-05
    """
    safeResult = toJsonSafe(result) if result is not None else None
    count = len(safeResult) if isinstance(safeResult, list) else None
    return dumpModel(
        StandardResponse(
            status=True,
            message=message,
            result=safeResult,
            count=count,
            requestId=getRequestId(),
        )
    )


def errorResponse(message: str = "error", result: Any = None, code: Optional[str] = None) -> Dict[str, Any]:
    """
    설명: 표준 에러 응답 본문 생성. 오류 코드를 포함할 수 있음
    처리 규칙: status=false 고정이며 현재 requestId를 함께 포함
    반환값: API 에러 응답 규격(dict) 객체를 반환
    갱신일: 2025-11-12
    """
    return dumpModel(
        StandardResponse(
            status=False,
            message=message,
            result=result,
            code=code,
            requestId=getRequestId(),
        )
    )
