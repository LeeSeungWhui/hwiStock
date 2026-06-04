"""
파일명: backend/router/CommonRouter.py
작성자: LSH
갱신일: 2025-11-11
설명: 공통(헬스/레디니스) 라우터. 서비스에는 필요한 데이터만 전달
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from lib.I18n import detectLocale, translate as i18nTranslate
from lib.Response import errorResponse, successResponse
from lib.ServiceError import buildMappedErrorResponse
from service import CommonService

router = APIRouter(tags=["common"])


@router.get("/healthz")
async def healthz(request: Request):
    """
    설명: 프로세스 헬스 체크 응답을 반환. 호출 맥락의 제약을 기준으로 동작 기준 확정
    처리 규칙: service 결과를 표준 successResponse로 감싼 뒤 no-store 헤더를 강제
    반환값: status=200 JSONResponse를 반환
    갱신일: 2026-02-24
    """
    result = await CommonService.healthz({})
    resp = successResponse(result=result)
    r = JSONResponse(content=resp, status_code=200)
    r.headers["Cache-Control"] = "no-store"
    return r


@router.get("/readyz")
async def readyz(request: Request):
    """
    설명: 레디니스 체크 결과를 상태코드와 함께 반환
    처리 규칙: isReady=true면 200 success, false면 로케일 메시지와 code(OBS_503_NOT_READY)로 503 반환
    반환값: Cache-Control=no-store가 적용된 표준 JSONResponse
    갱신일: 2026-02-28
    """
    result, isReady = await CommonService.readyz({})
    if isReady:
        resp = successResponse(result=result)
        status = 200
        r = JSONResponse(content=resp, status_code=status)
        r.headers["Cache-Control"] = "no-store"
        return r

    loc = detectLocale(request)
    mappedResponse = buildMappedErrorResponse(
        "OBS_503_NOT_READY",
        messageByCode={
            "OBS_503_NOT_READY": i18nTranslate("obs.not_ready", "not ready", loc),
        },
        result=result,
        includeNoStore=True,
    )
    if mappedResponse is not None:
        return mappedResponse

    fallbackResponse = JSONResponse(
        content=errorResponse(
            message=i18nTranslate("obs.not_ready", "not ready", loc),
            result=result,
            code="OBS_503_NOT_READY",
        ),
        status_code=503,
    )
    fallbackResponse.headers["Cache-Control"] = "no-store"
    return fallbackResponse
