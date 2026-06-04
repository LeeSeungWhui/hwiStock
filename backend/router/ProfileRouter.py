"""
파일명: backend/router/ProfileRouter.py
작성자: LSH
갱신일: 2026-03-12
설명: /api/v1/profile/me 조회/수정 API 라우터
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from lib.Auth import getCurrentUser
from lib.RequestPayloadValidator import readJsonPayloadDict, validatePayloadTypes
from lib.Response import successResponse
from lib.ServiceError import buildMappedErrorResponse
from service import ProfileService

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def handleProfileError(exc: Exception) -> JSONResponse:
    """
    설명: 프로필 서비스 예외를 표준 에러 응답(JSONResponse)으로 매핑. 호출 맥락의 제약을 기준으로 동작 기준 확정
    처리 규칙: DB/권한/입력/사용자없음 코드만 상태코드와 code를 고정 매핑
    실패 동작: 매핑되지 않은 예외 코드는 라우터 상위에서 처리되도록 원본 예외를 다시 발생시킨
    반환값: 매핑된 JSONResponse
    갱신일: 2026-02-28
    """
    mappedResponse = buildMappedErrorResponse(exc, includeNoStore=True)
    if mappedResponse is not None:
        return mappedResponse
    raise exc


@router.get("/me")
async def getMyProfile(user=Depends(getCurrentUser)):
    """
    설명: 인증 사용자 프로필을 조회. 호출 맥락의 제약을 기준으로 동작 기준 확정
    실패 동작: 서비스 예외는 handleProfileError에서 표준 코드/상태로 변환
    반환값: successResponse(result=profile) 형태의 JSON 본문을 반환
    갱신일: 2026-02-22
    """
    try:
        result = await ProfileService.getMyProfile(user)
        response = JSONResponse(status_code=200, content=successResponse(result=result))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleProfileError(exc)


@router.put("/me")
async def updateMyProfile(request: Request, user=Depends(getCurrentUser)):
    """
    설명: 인증 사용자 프로필 수정
    처리 규칙: None 필드는 제외한 payload만 서비스로 전달
    실패 동작: 서비스 예외는 handleProfileError에서 공통 에러 응답으로 변환
    갱신일: 2026-02-22
    """
    try:
        payload = validatePayloadTypes(
            await readJsonPayloadDict(request),
            optionalFieldTypeMap={
                "userNm": "str",
                "notifyEmail": "bool",
                "notifySms": "bool",
                "notifyPush": "bool",
            },
            excludeNone=True,
            errorCode="AUTH_422_INVALID_INPUT",
        )
        result = await ProfileService.updateMyProfile(user, payload)
        response = JSONResponse(
            status_code=200,
            content=successResponse(result=result, message="updated"),
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleProfileError(exc)
