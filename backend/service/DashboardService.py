"""
파일명: backend/service/DashboardService.py
작성자: LSH
갱신일: 2026-02-22
설명: 대시보드 업무(T_DATA) 목록/상세/CRUD/집계 서비스 로직
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional

from lib import Database as DB
from lib.Casing import convertKeysToCamelCase
from lib.Config import getConfig
from lib.Idempotency import beginIdempotencyRequest, completeIdempotencyRequest
from lib.ServiceError import ServiceError
from lib.Transaction import transaction

ALLOWED_STATUS = frozenset(("ready", "pending", "running", "done", "failed"))
SQLITE_LOCK_RETRY_COUNT = 8
ALLOWED_SORT = frozenset((
    "reg_dt_desc",
    "reg_dt_asc",
    "amt_desc",
    "amt_asc",
    "title_desc",
    "title_asc",
))


def toIntOrDefault(rawValue: Optional[Any], defaultValue: int) -> int:
    """
    설명: 정수값 파싱 실패 시 기본값으로 대체
    반환값: 파싱 성공 시 정수값, 실패 시 defaultValue
    갱신일: 2026-02-22
    """
    if rawValue is None:
        return defaultValue
    try:
        return int(rawValue)
    except Exception:
        return defaultValue


def clampValue(rawValue: Optional[Any], defaultValue: int, minValue: int, maxValue: int) -> int:
    """
    설명: 정수값을 범위로 보정
    반환값: minValue~maxValue 범위로 제한된 정수값
    갱신일: 2026-02-22
    """
    value = toIntOrDefault(rawValue, defaultValue)
    return max(minValue, min(value, maxValue))


def normalizeSort(sortValue: Optional[str]) -> str:
    """
    설명: 허용된 정렬값만 통과시키고 나머지는 기본 정렬로 보정
    반환값: 허용 목록(ALLOWED_SORT) 내 정렬키 또는 기본값 reg_dt_desc
    갱신일: 2026-02-22
    """
    candidate = str(sortValue or "").strip().lower()
    return candidate if candidate in ALLOWED_SORT else "reg_dt_desc"


def normalizeStatus(statusValue: Optional[str]) -> str:
    """
    설명: 상태 필터 문자열을 허용 상태 집합(ALLOWED_STATUS) 기준으로 정규화하 유틸
    반환값: 빈 문자열 또는 허용 상태값, 허용 외 입력은 ServiceError를 발생시킨
    갱신일: 2026-02-22
    """
    candidate = str(statusValue or "").strip().lower()
    if not candidate:
        return ""
    if candidate not in ALLOWED_STATUS:
        raise ServiceError("DASH_422_INVALID_INPUT")
    return candidate


def normalizeKeyword(keyword: Optional[str]) -> str:
    """
    설명: 검색 키워드 문자열의 공백 정리를 담당하는 정규화 유틸
    반환값: 좌우 공백이 제거된 검색어 문자열
    갱신일: 2026-02-22
    """
    return str(keyword or "").strip()


def parseTagList(rawTags: Any) -> List[str]:
    """
    설명: tags 입력(raw list/json/comma text)을 문자열 리스트로 통일하 파서
    반환값: 공백/빈값이 제거된 태그 문자열 리스트
    갱신일: 2026-02-22
    """
    if rawTags is None:
        return []
    if isinstance(rawTags, list):
        tagList = [str(tag).strip() for tag in rawTags if str(tag).strip()]
        return tagList
    if isinstance(rawTags, str):
        text = rawTags.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(tag).strip() for tag in parsed if str(tag).strip()]
        except Exception:
            pass
        return [tag.strip() for tag in text.split(",") if tag.strip()]
    raise ServiceError("DASH_422_INVALID_INPUT")


def normalizeTitle(rawTitle: Any) -> str:
    """
    설명: 제목 필드 길이/타입 제약을 검증하는 정규화 단계
    반환값: 공백 제거된 제목 문자열, 형식 위반 시 ServiceError를 발생시킨
    갱신일: 2026-02-22
    """
    if not isinstance(rawTitle, str):
        raise ServiceError("DASH_422_INVALID_INPUT")
    title = rawTitle.strip()
    if not title or len(title) > 200:
        raise ServiceError("DASH_422_INVALID_INPUT")
    return title


def normalizeDescription(rawDescription: Any) -> str:
    """
    설명: 설명 필드의 타입/널 입력을 처리하는 정규화 단계
    반환값: 공백 제거된 설명 문자열(null 입력 시 빈 문자열)
    갱신일: 2026-02-22
    """
    if rawDescription is None:
        return ""
    if not isinstance(rawDescription, str):
        raise ServiceError("DASH_422_INVALID_INPUT")
    return rawDescription.strip()


def normalizeAmount(rawAmount: Any) -> float:
    """
    설명: 금액 필드를 수치형으로 보정
    반환값: float 금액값(공백/None은 0.0), 변환 실패 시 ServiceError를 발생시킨
    갱신일: 2026-02-22
    """
    if rawAmount in (None, ""):
        return 0.0
    try:
        amount = float(rawAmount)
    except Exception:
        raise ServiceError("DASH_422_INVALID_INPUT")
    return amount


def parseInsertedId(rawResult: Any) -> Optional[int]:
    """
    설명: DB execute 결과값에서 생성된 PK 후보 ID 추출
    반환값: 1 이상 정수 ID 또는 None
    갱신일: 2026-02-23
    """
    if isinstance(rawResult, bool):
        return None
    if isinstance(rawResult, (int, float)):
        value = int(rawResult)
        return value if value > 0 else None
    if isinstance(rawResult, str):
        text = rawResult.strip()
        if text.isdigit():
            value = int(text)
            return value if value > 0 else None
    return None


def buildCreatePayload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    설명: 신규 등록 payload를 DB insert 바인딩 형태로 구성하 매퍼
    반환값: DB insert 바인딩에 바로 사용할 정규화 payload dict
    갱신일: 2026-02-22
    """
    title = normalizeTitle(payload.get("title"))
    status = normalizeStatus(payload.get("status"))
    if not status:
        raise ServiceError("DASH_422_INVALID_INPUT")
    description = normalizeDescription(payload.get("description"))
    amount = normalizeAmount(payload.get("amount"))
    tags = parseTagList(payload.get("tags"))
    return {
        "title": title,
        "description": description,
        "status": status,
        "amount": amount,
        "tags": json.dumps(tags, ensure_ascii=False),
    }


def buildUpdatePayload(payload: Dict[str, Any], currentRow: Dict[str, Any]) -> Dict[str, Any]:
    """
    설명: 부분 수정 payload와 기존 값 병합 기반 DB 입력 포맷 생성
    반환값: 기존값과 병합된 DB update 바인딩용 payload dict
    갱신일: 2026-02-22
    """
    if not payload:
        raise ServiceError("DASH_422_INVALID_INPUT")

    knownFields = {"title", "description", "status", "amount", "tags"}
    if not any(fieldName in payload for fieldName in knownFields):
        raise ServiceError("DASH_422_INVALID_INPUT")

    titleRaw = payload.get("title") if "title" in payload else currentRow.get("title")
    descriptionRaw = payload.get("description") if "description" in payload else currentRow.get("description")
    statusRaw = payload.get("status") if "status" in payload else currentRow.get("status")
    amountRaw = payload.get("amount") if "amount" in payload else currentRow.get("amount")
    tagsRaw = payload.get("tags") if "tags" in payload else currentRow.get("tags")

    title = normalizeTitle(titleRaw)
    description = normalizeDescription(descriptionRaw)
    status = normalizeStatus(statusRaw)
    if not status:
        raise ServiceError("DASH_422_INVALID_INPUT")
    amount = normalizeAmount(amountRaw)
    tags = parseTagList(tagsRaw)

    return {
        "title": title,
        "description": description,
        "status": status,
        "amount": amount,
        "tags": json.dumps(tags, ensure_ascii=False),
    }


def ensureDbManager():
    """
    설명: 기본 DB 매니저를 확보하고 미준비 상태 차단
    반환값: 초기화된 DB 매니저 인스턴스, 미준비 시 ServiceError를 발생시킨
    갱신일: 2026-02-22
    """
    db = DB.getManager()
    if not db:
        raise ServiceError("DB_NOT_READY")
    return db


def normalizeUserId(rawUserId: Any) -> str:
    """
    설명: 인증 사용자 식별자를 서비스 공통 바인딩 키로 정규화
    실패 동작: 빈 문자열/비문자 입력은 ServiceError를 발생시킨
    반환값: 공백 제거된 사용자 식별자 문자열
    갱신일: 2026-03-03
    """
    if not isinstance(rawUserId, str):
        raise ServiceError("DASH_401_UNAUTHORIZED")
    userId = rawUserId.strip()
    if not userId:
        raise ServiceError("DASH_401_UNAUTHORIZED")
    return userId


async def listDataTemplates(
    userId: str,
    q: Optional[str] = None,
    status: Optional[str] = None,
    page: Optional[int] = None,
    size: Optional[int] = None,
    sort: Optional[str] = None,
) -> Dict[str, Any]:
    """
    설명: 검색/필터/페이지네이션 파라미터를 안전값으로 보정해 업무 목록을 조회하 서비스
    반환값: dataTemplateList/total/page/size/sort를 포함한 목록 조회 결과 dict
    갱신일: 2026-02-22
    """
    db = ensureDbManager()
    ownerUserId = normalizeUserId(userId)
    sortValue = normalizeSort(sort)
    keywordValue = normalizeKeyword(q)
    statusValue = normalizeStatus(status)
    listPolicy = getConfig()
    globalPolicy = listPolicy["API_POLICY"] if "API_POLICY" in listPolicy else None
    dashboardListPolicy = listPolicy["API_POLICY.dashboard.list"] if "API_POLICY.dashboard.list" in listPolicy else None
    absoluteListSizeCap = clampValue(
        globalPolicy.get("absolute_list_size_cap") if globalPolicy else None,
        500,
        1,
        500,
    )
    listSizeMax = clampValue(
        dashboardListPolicy.get("list_size_max") if dashboardListPolicy else (globalPolicy.get("list_size_max") if globalPolicy else None),
        50,
        1,
        absoluteListSizeCap,
    )

    pageValue = clampValue(page, 1, 1, 100000)
    sizeValue = min(clampValue(size, 20, 1, absoluteListSizeCap), listSizeMax)
    offsetValue = (pageValue - 1) * sizeValue

    binds = {
        "userId": ownerUserId,
        "q": keywordValue,
        "qLike": f"%{keywordValue}%" if keywordValue else "",
        "status": statusValue,
        "sort": sortValue,
        "limit": sizeValue,
        "offset": offsetValue,
    }
    countBinds = {
        "userId": ownerUserId,
        "q": keywordValue,
        "qLike": f"%{keywordValue}%" if keywordValue else "",
        "status": statusValue,
    }
    rows = await db.fetchAllQuery("dashboard.list", binds) or []
    countRow = await db.fetchOneQuery("dashboard.listCount", countBinds) or {}
    dataTemplateList = [convertKeysToCamelCase(row) for row in rows]
    countResult = convertKeysToCamelCase(countRow)
    totalCount = int(countResult.get("totalCount", 0) or 0)

    return {
        "dataTemplateList": dataTemplateList,
        "count": len(dataTemplateList),
        "total": totalCount,
        "page": pageValue,
        "size": sizeValue,
        "sort": sortValue,
        "q": keywordValue,
        "status": statusValue,
    }


async def getDataTemplateDetail(dataId: int, userId: str) -> Dict[str, Any]:
    """
    설명: dataId 기준 업무 단건 상세를 조회하고 camelCase 결과로 반환하 서비스
    반환값: camelCase 변환된 단건 상세 dict, 미존재 시 ServiceError를 발생시킨
    갱신일: 2026-02-22
    """
    db = ensureDbManager()
    ownerUserId = normalizeUserId(userId)
    row = await db.fetchOneQuery("dashboard.detail", {"id": int(dataId), "userId": ownerUserId})
    if not row:
        raise ServiceError("DASH_404_NOT_FOUND")
    return convertKeysToCamelCase(row)


@transaction("main_db", retries=SQLITE_LOCK_RETRY_COUNT, retryOn=(sqlite3.OperationalError,))
async def createDataTemplate(payload: Dict[str, Any], userId: str, idempotencyKey: str | None = None) -> Dict[str, Any]:
    """
    설명: 업무를 신규 등록
    반환값: 신규 생성된 업무 상세 dict, 생성 후보 확인 실패 시 ServiceError를 발생시킨
    갱신일: 2026-02-22
    """
    if not isinstance(payload, dict):
        raise ServiceError("DASH_422_INVALID_INPUT")
    ownerUserId = normalizeUserId(userId)
    insertPayload = buildCreatePayload(payload)
    insertPayload["userId"] = ownerUserId
    scopeType = f"dashboard.create.{ownerUserId}"

    replay = await beginIdempotencyRequest(scopeType, idempotencyKey, insertPayload)
    if replay.get("status") == "replay":
        return replay.get("result") or {}
    db = ensureDbManager()
    inserted = await db.executeQuery("dashboard.create", insertPayload)
    createdId = parseInsertedId(inserted)
    if createdId:
        row = await db.fetchOneQuery("dashboard.detail", {"id": createdId, "userId": ownerUserId})
        if row:
            result = convertKeysToCamelCase(row)
            await completeIdempotencyRequest(scopeType, idempotencyKey, result)
            return result
    candidate = await db.fetchOneQuery("dashboard.findCreatedCandidate", insertPayload)
    if candidate:
        result = convertKeysToCamelCase(candidate)
        await completeIdempotencyRequest(scopeType, idempotencyKey, result)
        return result
    raise ServiceError("DASH_500_CREATE_FAILED")


async def updateDataTemplate(dataId: int, payload: Dict[str, Any], userId: str) -> Dict[str, Any]:
    """
    설명: 업무를 수정(부분 수정 지원)
    반환값: 수정 완료 후 재조회한 업무 상세 dict
    갱신일: 2026-02-22
    """
    if not isinstance(payload, dict):
        raise ServiceError("DASH_422_INVALID_INPUT")
    db = ensureDbManager()
    ownerUserId = normalizeUserId(userId)
    current = await db.fetchOneQuery("dashboard.detail", {"id": int(dataId), "userId": ownerUserId})
    if not current:
        raise ServiceError("DASH_404_NOT_FOUND")
    currentCamel = convertKeysToCamelCase(current)
    nextPayload = buildUpdatePayload(payload, currentCamel)
    nextPayload["id"] = int(dataId)
    nextPayload["userId"] = ownerUserId
    await db.executeQuery("dashboard.update", nextPayload)
    row = await db.fetchOneQuery("dashboard.detail", {"id": int(dataId), "userId": ownerUserId})
    if not row:
        raise ServiceError("DASH_404_NOT_FOUND")
    return convertKeysToCamelCase(row)


async def deleteDataTemplate(dataId: int, userId: str) -> Dict[str, Any]:
    """
    설명: 업무 삭제
    반환값: 삭제된 업무 ID dict, 대상 미존재 시 ServiceError를 발생시킨
    갱신일: 2026-02-22
    """
    db = ensureDbManager()
    ownerUserId = normalizeUserId(userId)
    row = await db.fetchOneQuery("dashboard.detail", {"id": int(dataId), "userId": ownerUserId})
    if not row:
        raise ServiceError("DASH_404_NOT_FOUND")
    await db.executeQuery("dashboard.delete", {"id": int(dataId), "userId": ownerUserId})
    return {"id": int(dataId)}


async def dataTemplateStats(userId: str) -> Dict[str, Any]:
    """
    설명: 상태별 count/amount 집계를 합산해 대시보드 통계 payload를 구성하 서비스
    반환값: totalCount/totalAmount/statusSummaryList를 포함한 통계 결과 dict
    갱신일: 2026-02-22
    """
    db = ensureDbManager()
    ownerUserId = normalizeUserId(userId)
    rows: List[Dict[str, Any]] = await db.fetchAllQuery("dashboard.statusSummary", {"userId": ownerUserId}) or []
    statusSummaryList = [convertKeysToCamelCase(row) for row in rows]
    totalCount = sum(int(row.get("count", 0) or 0) for row in statusSummaryList)
    totalAmount = float(sum(row.get("amountSum", 0) or 0 for row in statusSummaryList))
    return {
        "totalCount": totalCount,
        "totalAmount": totalAmount,
        "statusSummaryList": statusSummaryList,
    }
