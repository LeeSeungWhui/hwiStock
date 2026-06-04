"""
파일명: backend/router/TransactionRouter.py
작성자: LSH
갱신일: 2025-12-18
설명: 트랜잭션/세이브포인트/로깅 검증용 데모 라우터
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from lib.Auth import getCurrentUser
from lib.Response import errorResponse, successResponse
from service import TransactionService

router = APIRouter(prefix="/api/v1/transaction", tags=["transaction"])


def isUniqueConstraintViolation(error: Exception) -> bool:
    """
    설명: DB 예외 메시지에서 UNIQUE 제약 위반 여부 판별
    처리 규칙: sqlite/postgresql/mysql에서 공통으로 쓰이는 duplicate/unique 토큰을 검사
    반환값: UNIQUE 위반으로 판단되면 True, 아니면 False
    갱신일: 2026-03-02
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
    return any(token in text for token in duplicateTokens)


@router.post("/test/single")
async def testSingle(user=Depends(getCurrentUser)):
    """
    설명: 서비스의 단건 insert 시나리오를 호출해 커밋 성공 응답을 반환. 호출 맥락의 제약을 기준으로 동작 기준 확정
    반환값: 삽입 결과를 successResponse로 감싼 status=200 JSONResponse를 반환
    갱신일: 2026-02-22
    """
    result = await TransactionService.testSingle()
    return JSONResponse(status_code=200, content=successResponse(result=result))


@router.post("/test/unique-violation")
async def testUniqueViolation(user=Depends(getCurrentUser)):
    """
    설명: UNIQUE 제약 충돌 시나리오를 실행하고 롤백 결과를 409로 매핑. 호출 맥락의 제약을 기준으로 동작 기준 확정
    처리 규칙: UNIQUE 위반이면 409(TX_409_UNIQUE), 기타 예외는 500(TX_500_INTERNAL)으로 매핑
    갱신일: 2026-03-02
    """
    try:
        await TransactionService.testUniqueViolation()
        return JSONResponse(status_code=200, content=successResponse(result={"ok": True}))
    except Exception as exc:
        if isUniqueConstraintViolation(exc):
            return JSONResponse(
                status_code=409,
                content=errorResponse(
                    message="unique constraint violation",
                    code="TX_409_UNIQUE",
                ),
            )
        return JSONResponse(
            status_code=500,
            content=errorResponse(
                message="transaction test failed",
                code="TX_500_INTERNAL",
            ),
        )
