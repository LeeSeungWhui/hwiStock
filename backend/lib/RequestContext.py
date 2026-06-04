"""
파일명: backend/lib/RequestContext.py
작성자: LSH
갱신일: 2025-09-07
설명: 요청 스코프 값(ContextVar) 저장/조회 유틸
"""

import contextvars

# 요청ID 등 요청 스코프 값을 저장하는 컨텍스트 변수
requestIdVar: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def setRequestId(requestId: str) -> contextvars.Token:
    """
    설명: 요청ID를 컨텍스트에 저장하고 reset 토큰 반환
    갱신일: 2025-11-12
    처리 규칙: 입력값을 검증하고 실패 시 예외/기본값 경로로 수렴
    """
    return requestIdVar.set(requestId)


def getRequestId() -> str | None:
    """
    설명: 현재 컨텍스트의 요청ID를 조회. 호출 맥락의 제약을 기준으로 동작 기준 확정
    반환값: 미들웨어에서 설정한 requestId 문자열 또는 None을 반환
    갱신일: 2025-11-12
    """
    return requestIdVar.get()


def resetRequestId(token: contextvars.Token) -> None:
    """
    설명: 저장된 요청ID를 초기 상태로 복구
    처리 규칙: 유효하지 않은 토큰이 전달돼도 예외를 삼켜 요청 종료 경로를 방해하지 않는
    갱신일: 2025-11-12
    """
    try:
        requestIdVar.reset(token)
    except Exception:
        pass
