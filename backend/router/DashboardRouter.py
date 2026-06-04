"""
파일명: backend/router/DashboardRouter.py
작성자: LSH
갱신일: 2026-03-12
설명: 대시보드용 T_DATA 목록/상세/CRUD/집계 API. 토큰 인증 후 서비스 계층을 통해 처리
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from lib.Auth import getCurrentUser
from lib.Config import getConfig
from lib.RequestPayloadValidator import readJsonPayloadDict, validatePayloadTypes
from lib.Response import successResponse, toJsonSafe
from lib.ServiceError import buildMappedErrorResponse
from service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def dashboardJsonResponse(statusCode: int, content: dict) -> JSONResponse:
    """
    설명: 대시보드 API 응답 본문을 JSON 직렬화 가능한 형태로 변환해 반환
    처리 규칙: Decimal 등 비-JSON 타입은 toJsonSafe로 원시값으로 축소한다
    반환값: Cache-Control=no-store가 적용된 JSONResponse
    갱신일: 2026-06-05
    """
    response = JSONResponse(status_code=statusCode, content=toJsonSafe(content))
    response.headers["Cache-Control"] = "no-store"
    return response


def handleDashboardError(exc: Exception) -> JSONResponse:
    """
    설명: 대시보드 서비스 코드(DB_NOT_READY/422/404/500)를 HTTP 에러 응답으로 매핑하 변환기
    처리 규칙: 정의된 코드만 고정 매핑하고, 미정의 예외는 상위 핸들러로 재전파
    반환값: 매핑된 JSONResponse
    갱신일: 2026-02-22
    """
    mappedResponse = buildMappedErrorResponse(exc, includeNoStore=True)
    if mappedResponse is not None:
        return mappedResponse
    raise exc


@router.get("")
async def listDataTemplates(
    q: str | None = None,
    status: str | None = None,
    page: int | None = None,
    size: int | None = None,
    sort: str | None = None,
    user=Depends(getCurrentUser),
):
    """
    설명: 목록 쿼리 파라미터를 서비스로 위임하고 응답 본문(meta 포함)으로 직렬화하 라우터
    실패 동작: 서비스 예외는 handleDashboardError에서 코드별 HTTP 응답으로 변환
    갱신일: 2026-02-22
    """
    try:
        effectiveSize = size
        if size is not None:
            config = getConfig()
            globalPolicy = config["API_POLICY"] if "API_POLICY" in config else None
            dashboardListPolicy = config["API_POLICY.dashboard.list"] if "API_POLICY.dashboard.list" in config else None
            absoluteListSizeCap = min(int(globalPolicy.get("absolute_list_size_cap", 500)) if globalPolicy else 500, 500)
            listSizeMax = int(
                dashboardListPolicy.get("list_size_max")
                if dashboardListPolicy and dashboardListPolicy.get("list_size_max") is not None
                else (globalPolicy.get("list_size_max", 50) if globalPolicy else 50)
            )
            effectiveSize = max(1, min(int(size), max(1, min(listSizeMax, absoluteListSizeCap))))
        result = await DashboardService.listDataTemplates(
            userId=user.username,
            q=q,
            status=status,
            page=page,
            size=effectiveSize,
            sort=sort,
        )
        return dashboardJsonResponse(
            200,
            {
                **successResponse(
                    result={
                        "dataTemplateList": [*result["dataTemplateList"]],
                        "listMetaObj": {
                            "page": result["page"],
                            "size": result["size"],
                            "sort": result["sort"],
                            "q": result["q"],
                            "status": result["status"],
                            "totalCount": result["total"],
                        },
                    }
                ),
                "count": result["total"],
            },
        )
    except Exception as exc:
        return handleDashboardError(exc)


@router.get("/stats")
async def dataTemplateStats(user=Depends(getCurrentUser)):
    """
    설명: 상태별 집계 서비스 결과를 successResponse로 노출하는 통계 조회 엔드포인트
    반환값: 상태별 count/amount 집계 리스트를 담은 successResponse
    갱신일: 2026-02-22
    """
    try:
        result = await DashboardService.dataTemplateStats(userId=user.username)
        return dashboardJsonResponse(200, successResponse(result=result))
    except Exception as exc:
        return handleDashboardError(exc)


@router.get("/{dataId}")
async def getDataTemplateDetail(dataId: int, user=Depends(getCurrentUser)):
    """
    설명: 단건 상세 서비스 결과를 successResponse로 감싸 반환하는 조회 엔드포인트
    반환값: dataId에 해당하는 단건 상세를 담은 successResponse
    갱신일: 2026-02-22
    """
    try:
        result = await DashboardService.getDataTemplateDetail(dataId, userId=user.username)
        return dashboardJsonResponse(200, successResponse(result=result))
    except Exception as exc:
        return handleDashboardError(exc)


@router.post("")
async def createDataTemplate(request: Request, user=Depends(getCurrentUser)):
    """
    설명: 생성 payload를 서비스 입력으로 변환해 신규 등록 결과를 반환하는 생성 엔드포인트
    반환값: 생성된 엔티티를 포함한 201(successResponse, message=created)
    갱신일: 2026-02-22
    """
    try:
        payload = validatePayloadTypes(
            await readJsonPayloadDict(request),
            requiredFieldTypeMap={
                "title": "str",
                "status": "str",
            },
            optionalFieldTypeMap={
                "description": "str",
                "amount": "number",
                "tags": "str_or_str_list",
            },
            errorCode="DASH_422_INVALID_INPUT",
        )
        idempotencyKey = request.headers.get("Idempotency-Key")
        result = await DashboardService.createDataTemplate(
            payload,
            userId=user.username,
            idempotencyKey=idempotencyKey,
        )
        return dashboardJsonResponse(201, successResponse(result=result, message="created"))
    except Exception as exc:
        return handleDashboardError(exc)


@router.put("/{dataId}")
async def updateDataTemplate(dataId: int, request: Request, user=Depends(getCurrentUser)):
    """
    설명: 부분 수정 payload(excludeNone)를 서비스에 위임해 수정 결과를 반환하 엔드포인트
    반환값: 수정 완료 엔티티를 포함한 successResponse(message=updated)
    갱신일: 2026-02-22
    """
    try:
        payload = validatePayloadTypes(
            await readJsonPayloadDict(request),
            optionalFieldTypeMap={
                "title": "str",
                "description": "str",
                "status": "str",
                "amount": "number",
                "tags": "str_or_str_list",
            },
            excludeNone=True,
            errorCode="DASH_422_INVALID_INPUT",
        )
        result = await DashboardService.updateDataTemplate(
            dataId,
            payload,
            userId=user.username,
        )
        return dashboardJsonResponse(200, successResponse(result=result, message="updated"))
    except Exception as exc:
        return handleDashboardError(exc)


@router.delete("/{dataId}")
async def deleteDataTemplate(dataId: int, user=Depends(getCurrentUser)):
    """
    설명: 삭제 서비스 호출 결과를 successResponse(message=deleted)로 직렬화하 엔드포인트
    반환값: 삭제 결과 정보를 담은 successResponse(message=deleted)
    갱신일: 2026-02-22
    """
    try:
        result = await DashboardService.deleteDataTemplate(dataId, userId=user.username)
        return dashboardJsonResponse(200, successResponse(result=result, message="deleted"))
    except Exception as exc:
        return handleDashboardError(exc)
