"""
파일명: backend/router/SampleRouter.py
작성자: LSH
갱신일: 2026-04-08
설명: 공개 sample 페이지용 DB 연동 API 라우터
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from lib.Config import getConfig
from lib.RequestPayloadValidator import readJsonPayloadDict, validatePayloadTypes
from lib.Response import successResponse
from lib.ServiceError import buildMappedErrorResponse
from service import SampleService

router = APIRouter(prefix="/api/v1/sample", tags=["sample"])


def handleSampleError(exc: Exception) -> JSONResponse:
    """
    설명: 공개 sample 서비스 예외를 표준 에러 응답으로 매핑
    처리 규칙: 등록된 sample 코드만 상태코드/code/message로 고정 변환
    반환값: 매핑된 JSONResponse
    갱신일: 2026-03-06
    """
    mappedResponse = buildMappedErrorResponse(exc, includeNoStore=True)
    if mappedResponse is not None:
        return mappedResponse
    raise exc


@router.get("/overview")
async def getSampleOverview():
    """
    설명: 공개 sample 허브/포트폴리오용 전체 요약 카운트 조회
    반환값: taskCount/adminUserCount/formSubmissionCount를 담은 successResponse
    갱신일: 2026-03-06
    """
    try:
        result = await SampleService.getSampleOverview()
        response = JSONResponse(status_code=200, content=successResponse(result=result))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.get("/dashboard")
async def getSampleDashboard():
    """
    설명: 공개 sample 대시보드용 KPI/차트/최근 업무 묶음 조회
    반환값: dashboard result dict를 담은 successResponse
    갱신일: 2026-03-06
    """
    try:
        result = await SampleService.getSampleDashboard()
        response = JSONResponse(status_code=200, content=successResponse(result=result))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.get("/tasks")
async def listSampleTasks(
    q: str | None = None,
    status: str | None = None,
    fromDate: str | None = None,
    toDate: str | None = None,
    page: int | None = None,
    size: int | None = None,
):
    """
    설명: 공개 sample CRUD 목록을 검색/필터 조건으로 조회
    반환값: sampleTaskList/total/page/size meta를 담은 successResponse
    갱신일: 2026-03-06
    """
    try:
        effectiveSize = size
        if size is not None:
            config = getConfig()
            globalPolicy = config["API_POLICY"] if "API_POLICY" in config else None
            taskListPolicy = config["API_POLICY.sample.taskList"] if "API_POLICY.sample.taskList" in config else None
            absoluteListSizeCap = min(int(globalPolicy.get("absolute_list_size_cap", 200)) if globalPolicy else 200, 500)
            listSizeMax = int(
                taskListPolicy.get("list_size_max")
                if taskListPolicy and taskListPolicy.get("list_size_max") is not None
                else (globalPolicy.get("list_size_max", 50) if globalPolicy else 50)
            )
            effectiveSize = max(1, min(int(size), max(1, min(listSizeMax, absoluteListSizeCap))))
        result = await SampleService.listSampleTasks(
            q=q,
            status=status,
            fromDate=fromDate,
            toDate=toDate,
            page=page,
            size=effectiveSize,
        )
        response = JSONResponse(
            status_code=200,
            content={
                **successResponse(
                    result={
                        "sampleTaskList": [*result["sampleTaskList"]],
                        "listMetaObj": {
                            "page": result["page"],
                            "size": result["size"],
                            "q": result["q"],
                            "status": result["status"],
                            "fromDate": result["fromDate"],
                            "toDate": result["toDate"],
                            "totalCount": result["total"],
                        },
                    }
                ),
                "count": result["total"],
            },
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.get("/tasks/{taskId}")
async def getSampleTaskDetail(taskId: int):
    """
    설명: 공개 sample 업무 단건 상세 조회
    반환값: 업무 상세 dict를 담은 successResponse
    갱신일: 2026-03-06
    """
    try:
        result = await SampleService.getSampleTaskDetail(taskId)
        response = JSONResponse(status_code=200, content=successResponse(result=result))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.post("/tasks")
async def createSampleTask(request: Request):
    """
    설명: 공개 sample 업무 신규 생성
    반환값: 생성된 업무 dict를 담은 201 successResponse
    갱신일: 2026-03-06
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
                "owner": "str",
                "amount": "number",
                "attachmentName": "str",
            },
            errorCode="SAMPLE_422_INVALID_INPUT",
        )
        idempotencyKey = request.headers.get("Idempotency-Key")
        result = await SampleService.createSampleTask(payload, idempotencyKey=idempotencyKey)
        response = JSONResponse(status_code=201, content=successResponse(result=result, message="created"))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.put("/tasks/{taskId}")
async def updateSampleTask(taskId: int, request: Request):
    """
    설명: 공개 sample 업무 단건 수정
    반환값: 수정된 업무 dict를 담은 successResponse(message=updated)
    갱신일: 2026-03-06
    """
    try:
        payload = validatePayloadTypes(
            await readJsonPayloadDict(request),
            optionalFieldTypeMap={
                "title": "str",
                "description": "str",
                "owner": "str",
                "status": "str",
                "amount": "number",
                "attachmentName": "str",
            },
            excludeNone=True,
            errorCode="SAMPLE_422_INVALID_INPUT",
        )
        result = await SampleService.updateSampleTask(taskId, payload)
        response = JSONResponse(status_code=200, content=successResponse(result=result, message="updated"))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.delete("/tasks/{taskId}")
async def deleteSampleTask(taskId: int):
    """
    설명: 공개 sample 업무 단건 삭제
    반환값: 삭제된 ID 메타를 담은 successResponse(message=deleted)
    갱신일: 2026-03-06
    """
    try:
        result = await SampleService.deleteSampleTask(taskId)
        response = JSONResponse(status_code=200, content=successResponse(result=result, message="deleted"))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.get("/forms/meta")
async def getSampleFormMeta():
    """
    설명: 공개 sample 복합 폼의 옵션/제출 현황 메타 조회
    반환값: categoryCodeList/featureCodeList/submissionCount/latestSubmission dict
    갱신일: 2026-03-06
    """
    try:
        result = await SampleService.getSampleFormMeta()
        response = JSONResponse(status_code=200, content=successResponse(result=result))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.post("/forms")
async def submitSampleForm(request: Request):
    """
    설명: 공개 sample 복합 폼 제출 저장
    반환값: 최신 제출 결과 dict를 담은 201 successResponse
    갱신일: 2026-03-06
    """
    try:
        payload = validatePayloadTypes(
            await readJsonPayloadDict(request),
            requiredFieldTypeMap={
                "name": "str",
                "email": "str",
                "phone": "str",
                "category": "str",
                "startDate": "str",
                "endDate": "str",
                "budgetRange": "str",
            },
            optionalFieldTypeMap={
                "requirement": "str",
                "selectedFeatures": "str_list",
                "referenceUrl": "str",
                "attachmentName": "str",
            },
            errorCode="SAMPLE_422_INVALID_INPUT",
        )
        idempotencyKey = request.headers.get("Idempotency-Key")
        result = await SampleService.submitSampleForm(
            payload,
            idempotencyKey=idempotencyKey,
        )
        response = JSONResponse(status_code=201, content=successResponse(result=result, message="created"))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.get("/admin/users")
async def listSampleAdminUsers(
    page: int | None = None,
    size: int | None = None,
):
    """
    설명: 공개 sample 관리자 사용자 목록 조회
    반환값: 사용자 리스트를 담은 successResponse
    갱신일: 2026-03-06
    """
    try:
        effectiveSize = size
        if size is not None:
            config = getConfig()
            globalPolicy = config["API_POLICY"] if "API_POLICY" in config else None
            adminUserListPolicy = (
                config["API_POLICY.sample.adminUserList"]
                if "API_POLICY.sample.adminUserList" in config
                else None
            )
            absoluteListSizeCap = min(int(globalPolicy.get("absolute_list_size_cap", 200)) if globalPolicy else 200, 500)
            listSizeMax = int(
                adminUserListPolicy.get("list_size_max")
                if adminUserListPolicy and adminUserListPolicy.get("list_size_max") is not None
                else (globalPolicy.get("list_size_max", 50) if globalPolicy else 50)
            )
            effectiveSize = max(1, min(int(size), max(1, min(listSizeMax, absoluteListSizeCap))))
        result = await SampleService.listSampleAdminUsers(page=page, size=effectiveSize)
        response = JSONResponse(
            status_code=200,
            content={
                **successResponse(
                    result={
                        "sampleAdminUserList": [*result["sampleAdminUserList"]],
                        "listMetaObj": {
                            "page": result["page"],
                            "size": result["size"],
                            "totalCount": result["total"],
                        },
                    }
                ),
                "count": result["total"],
            },
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.post("/admin/users")
async def createSampleAdminUser(request: Request):
    """
    설명: 공개 sample 관리자 사용자 신규 생성
    반환값: 생성된 사용자 dict를 담은 201 successResponse
    갱신일: 2026-03-06
    """
    try:
        payload = validatePayloadTypes(
            await readJsonPayloadDict(request),
            requiredFieldTypeMap={
                "name": "str",
                "email": "str",
                "role": "str",
                "status": "str",
            },
            optionalFieldTypeMap={
                "notifyEmail": "bool",
                "notifySms": "bool",
                "notifyPush": "bool",
                "profileImageUrl": "str",
            },
            excludeNone=True,
            errorCode="SAMPLE_422_INVALID_INPUT",
        )
        idempotencyKey = request.headers.get("Idempotency-Key")
        result = await SampleService.createSampleAdminUser(
            payload,
            idempotencyKey=idempotencyKey,
        )
        response = JSONResponse(status_code=201, content=successResponse(result=result, message="created"))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.put("/admin/users/{userId}")
async def updateSampleAdminUser(userId: int, request: Request):
    """
    설명: 공개 sample 관리자 사용자 단건 수정
    반환값: 수정된 사용자 dict를 담은 successResponse(message=updated)
    갱신일: 2026-03-06
    """
    try:
        payload = validatePayloadTypes(
            await readJsonPayloadDict(request),
            optionalFieldTypeMap={
                "name": "str",
                "role": "str",
                "status": "str",
                "notifyEmail": "bool",
                "notifySms": "bool",
                "notifyPush": "bool",
                "profileImageUrl": "str",
            },
            excludeNone=True,
            errorCode="SAMPLE_422_INVALID_INPUT",
        )
        result = await SampleService.updateSampleAdminUser(userId, payload)
        response = JSONResponse(status_code=200, content=successResponse(result=result, message="updated"))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.get("/admin/settings")
async def getSampleAdminSettings():
    """
    설명: 공개 sample 관리자 시스템 설정/권한 맵 조회
    반환값: systemSetting/rolePermissionMap dict를 담은 successResponse
    갱신일: 2026-03-06
    """
    try:
        result = await SampleService.getSampleAdminSettings()
        response = JSONResponse(status_code=200, content=successResponse(result=result))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)


@router.put("/admin/settings")
async def updateSampleAdminSettings(request: Request):
    """
    설명: 공개 sample 관리자 시스템 설정 저장
    반환값: 저장된 설정 dict를 담은 successResponse(message=updated)
    갱신일: 2026-03-06
    """
    try:
        payload = validatePayloadTypes(
            await readJsonPayloadDict(request),
            requiredFieldTypeMap={
                "siteName": "str",
                "adminEmail": "str",
                "sessionTimeout": "int",
                "maxUploadMb": "int",
            },
            optionalFieldTypeMap={
                "maintenanceMode": "bool",
            },
            excludeNone=True,
            errorCode="SAMPLE_422_INVALID_INPUT",
        )
        result = await SampleService.updateSampleAdminSettings(payload)
        response = JSONResponse(status_code=200, content=successResponse(result=result, message="updated"))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return handleSampleError(exc)
