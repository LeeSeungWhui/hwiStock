"""
파일명: backend/service/SampleService.py
작성자: LSH
갱신일: 2026-04-08
설명: 공개 sample 페이지용 DB 부트스트랩/조회/CRUD 서비스 로직
"""

import asyncio
import json
import re
from datetime import date, timedelta
from types import MappingProxyType
from typing import Any

from lib import Database as DB
from lib.Casing import convertKeysToCamelCase
from lib.Config import getConfig
from lib.Idempotency import beginIdempotencyRequest, completeIdempotencyRequest
from lib.ServiceError import ServiceError
from lib.Transaction import transaction

ALLOWED_TASK_STATUS = frozenset(("ready", "pending", "running", "done", "failed"))
ALLOWED_ADMIN_ROLE = frozenset(("admin", "editor", "user"))
ALLOWED_ADMIN_STATUS = frozenset(("active", "inactive"))
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SAMPLE_CONFIG_KEY = MappingProxyType({
    "BOOTSTRAP_VERSION": "sample.bootstrap.version",
    "ADMIN_SETTING": "sample.admin.setting",
    "ROLE_PERMISSION_MAP": "sample.admin.rolePermissionMap",
    "FORM_CATEGORY_CODE_LIST": "sample.form.categoryCodeList",
    "FORM_FEATURE_CODE_LIST": "sample.form.featureCodeList",
})
DEFAULT_ADMIN_SETTING = MappingProxyType({
    "siteName": "MyWebTemplate",
    "adminEmail": "admin@demo.demo",
    "maintenanceMode": False,
    "sessionTimeout": 60,
    "maxUploadMb": 30,
})
DEFAULT_ROLE_PERMISSION_MAP = MappingProxyType({
    "admin": MappingProxyType({
        "manageUser": True,
        "editContent": True,
        "changeSetting": True,
        "viewLog": True,
        "deleteData": True,
    }),
    "editor": MappingProxyType({
        "manageUser": False,
        "editContent": True,
        "changeSetting": False,
        "viewLog": True,
        "deleteData": False,
    }),
    "user": MappingProxyType({
        "manageUser": False,
        "editContent": False,
        "changeSetting": False,
        "viewLog": False,
        "deleteData": False,
    }),
})
DEFAULT_FORM_CATEGORY_CODE_LIST = ("web", "app", "api", "etc")
DEFAULT_FORM_FEATURE_CODE_LIST = ("login", "board", "payment", "chart", "admin")
BOOTSTRAP_LOCK = asyncio.Lock()


def readDefaultAdminSetting() -> dict[str, Any]:
    """
    설명: immutable 기본 관리자 설정을 JSON/응답용 dict 복사본으로 변환
    반환값: 기본 관리자 설정 dict
    갱신일: 2026-06-04
    """
    return dict(DEFAULT_ADMIN_SETTING)


def readDefaultRolePermissionMap() -> dict[str, dict[str, bool]]:
    """
    설명: immutable 기본 역할 권한 맵을 JSON/응답용 중첩 dict 복사본으로 변환
    반환값: 역할별 권한 dict
    갱신일: 2026-06-04
    """
    return {role: dict(permissionMap) for role, permissionMap in DEFAULT_ROLE_PERMISSION_MAP.items()}


def readTotalCount(row: dict[str, Any] | None) -> int:
    """
    설명: COUNT 행(dict)에서 totalCount 값을 안전하게 읽어 정수로 변환
    반환값: totalCount 정수값, 누락/파싱 실패 시 0
    갱신일: 2026-03-12
    """
    rawMap: Any = row or {}
    if not isinstance(rawMap, dict):
        try:
            rawMap = dict(rawMap)
        except Exception:
            rawMap = {}
    countMap = convertKeysToCamelCase(rawMap)
    try:
        return int(countMap.get("totalCount") or 0)
    except Exception:
        return 0


def ensureDbManager():
    """
    설명: 공개 sample API에서 사용할 기본 DB 매니저 확보
    실패 동작: 매니저가 없으면 ServiceError("DB_NOT_READY") 발생
    반환값: 초기화된 DB 매니저 인스턴스
    갱신일: 2026-03-06
    """
    db = DB.getManager()
    if not db:
        raise ServiceError("DB_NOT_READY")
    return db


def normalizeText(rawValue: Any, *, required: bool = False, maxLength: int = 255) -> str:
    """
    설명: 일반 문자열 입력을 trim/maxLength 기준으로 정규화
    실패 동작: required 위반 또는 최대 길이 초과 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 공백 제거된 문자열
    갱신일: 2026-03-06
    """
    if rawValue is None:
        if required:
            raise ServiceError("SAMPLE_422_INVALID_INPUT")
        return ""
    if not isinstance(rawValue, str):
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    value = rawValue.strip()
    if required and not value:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    if len(value) > maxLength:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return value


def normalizeEmail(rawValue: Any) -> str:
    """
    설명: 이메일 문자열 형식 검증/정규화
    실패 동작: 문자열이 아니거나 이메일 패턴 불일치 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 소문자 이메일 문자열
    갱신일: 2026-03-06
    """
    value = normalizeText(rawValue, required=True, maxLength=120).lower()
    if not EMAIL_PATTERN.fullmatch(value):
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return value


def normalizeDateText(rawValue: Any, *, required: bool = False) -> str:
    """
    설명: YYYY-MM-DD 날짜 문자열 검증/정규화
    실패 동작: required 위반 또는 날짜 패턴 불일치 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 빈 문자열 또는 YYYY-MM-DD 문자열
    갱신일: 2026-03-06
    """
    value = normalizeText(rawValue, required=required, maxLength=10)
    if not value:
        return ""
    if not DATE_PATTERN.fullmatch(value):
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return value


def parseSqlDateBound(value: str) -> date | None:
    """
    설명: 검증된 YYYY-MM-DD 문자열을 SQL 바인딩용 date로 변환
    실패 동작: 빈 값은 None, 파싱 실패는 SAMPLE_422_INVALID_INPUT
    반환값: date 또는 None
    갱신일: 2026-06-04
    """
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except Exception as exc:
        raise ServiceError("SAMPLE_422_INVALID_INPUT") from exc


def normalizeTaskStatus(rawValue: Any) -> str:
    """
    설명: 공개 sample 업무 상태값을 허용 목록으로 정규화
    실패 동작: 허용되지 않은 상태 입력이면 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 허용된 상태 문자열
    갱신일: 2026-03-06
    """
    value = normalizeText(rawValue, required=True, maxLength=20).lower()
    if value not in ALLOWED_TASK_STATUS:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return value


def normalizeAdminRole(rawValue: Any) -> str:
    """
    설명: 공개 sample 관리자 역할값을 허용 목록으로 정규화
    실패 동작: 허용되지 않은 역할 입력이면 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 허용된 역할 문자열
    갱신일: 2026-03-06
    """
    value = normalizeText(rawValue, required=True, maxLength=20).lower()
    if value not in ALLOWED_ADMIN_ROLE:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return value


def normalizeAdminStatus(rawValue: Any) -> str:
    """
    설명: 공개 sample 관리자 상태값을 허용 목록으로 정규화
    실패 동작: 허용되지 않은 상태 입력이면 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 허용된 활성 상태 문자열
    갱신일: 2026-03-06
    """
    value = normalizeText(rawValue, required=True, maxLength=20).lower()
    if value not in ALLOWED_ADMIN_STATUS:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return value


def normalizeAmount(rawValue: Any) -> float:
    """
    설명: 금액 입력을 float으로 보정
    실패 동작: 수치 변환 실패 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: float 금액값
    갱신일: 2026-03-06
    """
    if rawValue in (None, ""):
        return 0.0
    try:
        return float(rawValue)
    except Exception as exc:
        raise ServiceError("SAMPLE_422_INVALID_INPUT") from exc


def normalizeBool(rawValue: Any) -> bool:
    """
    설명: bool/0/1 입력을 불리언으로 정규화
    실패 동작: 해석 불가능한 값은 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: bool 값
    갱신일: 2026-03-06
    """
    if isinstance(rawValue, bool):
        return rawValue
    if rawValue in (0, 1):
        return bool(rawValue)
    if rawValue in (None, ""):
        return False
    raise ServiceError("SAMPLE_422_INVALID_INPUT")


def normalizePage(rawValue: Any, *, defaultValue: int = 1, maxValue: int = 100) -> int:
    """
    설명: 페이지 번호 입력을 최소/최대 범위 기준으로 보정
    실패 동작: 숫자 변환 실패 시 기본값 사용
    반환값: 1 이상 maxValue 이하 정수 페이지 번호
    갱신일: 2026-03-06
    """
    try:
        value = int(rawValue)
    except Exception:
        value = defaultValue
    return max(1, min(value, maxValue))


def normalizeId(rawValue: Any) -> int:
    """
    설명: 공개 sample 엔티티 ID를 양의 정수로 정규화
    실패 동작: 1 미만이거나 숫자 변환 실패 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 1 이상 정수 ID
    갱신일: 2026-03-06
    """
    try:
        value = int(rawValue)
    except Exception as exc:
        raise ServiceError("SAMPLE_422_INVALID_INPUT") from exc
    if value < 1:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return value


def normalizeJsonCodeList(rawValue: Any, *, allowedSet: set[str] | None = None) -> list[str]:
    """
    설명: JSON 배열/리스트 입력을 코드 문자열 목록으로 정규화
    실패 동작: 배열이 아니거나 허용되지 않은 코드 포함 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 공백 제거된 문자열 리스트
    갱신일: 2026-03-06
    """
    if rawValue is None:
        return []
    source = rawValue
    if isinstance(rawValue, str):
        try:
            source = json.loads(rawValue)
        except Exception as exc:
            raise ServiceError("SAMPLE_422_INVALID_INPUT") from exc
    if not isinstance(source, list):
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    out = []
    for item in source:
        value = normalizeText(item, required=True, maxLength=60)
        if allowedSet and value not in allowedSet:
            raise ServiceError("SAMPLE_422_INVALID_INPUT")
        out.append(value)
    return out


def toTaskPayload(payload: dict[str, Any], currentRow: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    설명: 공개 sample 업무 생성/수정 입력을 DB 바인딩 포맷으로 정규화
    실패 동작: 필수값 누락 또는 상태/금액 제약 위반 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: title/description/owner/status/amount/attachmentName 바인딩 dict
    갱신일: 2026-03-06
    """
    current = currentRow or {}
    titleRaw = payload.get("title") if "title" in payload else current.get("title")
    statusRaw = payload.get("status") if "status" in payload else current.get("status")
    descriptionRaw = payload.get("description") if "description" in payload else current.get("description")
    ownerRaw = payload.get("owner") if "owner" in payload else current.get("owner")
    amountRaw = payload.get("amount") if "amount" in payload else current.get("amount")
    attachmentRaw = payload.get("attachmentName") if "attachmentName" in payload else current.get("attachmentName")
    if not current and ("title" not in payload or "status" not in payload):
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    if current and not any(key in payload for key in ("title", "description", "owner", "status", "amount", "attachmentName")):
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return {
        "title": normalizeText(titleRaw, required=True, maxLength=200),
        "description": normalizeText(descriptionRaw, maxLength=1000),
        "owner": normalizeText(ownerRaw, maxLength=80),
        "status": normalizeTaskStatus(statusRaw),
        "amount": normalizeAmount(amountRaw),
        "attachmentName": normalizeText(attachmentRaw, maxLength=255),
    }


def toAdminUserPayload(payload: dict[str, Any], currentRow: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    설명: 공개 sample 관리자 사용자 생성/수정 입력을 DB 바인딩 포맷으로 정규화
    실패 동작: 필수값 누락 또는 이메일/역할/상태 규칙 위반 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: name/email/role/status/notify*/profileImageUrl 바인딩 dict
    갱신일: 2026-03-06
    """
    current = currentRow or {}
    if current:
        if not any(key in payload for key in ("name", "role", "status", "notifyEmail", "notifySms", "notifyPush", "profileImageUrl")):
            raise ServiceError("SAMPLE_422_INVALID_INPUT")
    else:
        if "name" not in payload or "email" not in payload or "role" not in payload or "status" not in payload:
            raise ServiceError("SAMPLE_422_INVALID_INPUT")
    return {
        "name": normalizeText(
            payload.get("name") if "name" in payload else current.get("name"),
            required=True,
            maxLength=80,
        ),
        "email": normalizeEmail(payload.get("email") if "email" in payload else current.get("email")),
        "role": normalizeAdminRole(payload.get("role") if "role" in payload else current.get("role")),
        "status": normalizeAdminStatus(payload.get("status") if "status" in payload else current.get("status")),
        "notifyEmail": 1 if normalizeBool(payload.get("notifyEmail") if "notifyEmail" in payload else current.get("notifyEmail")) else 0,
        "notifySms": 1 if normalizeBool(payload.get("notifySms") if "notifySms" in payload else current.get("notifySms")) else 0,
        "notifyPush": 1 if normalizeBool(payload.get("notifyPush") if "notifyPush" in payload else current.get("notifyPush")) else 0,
        "profileImageUrl": normalizeText(
            payload.get("profileImageUrl") if "profileImageUrl" in payload else current.get("profileImageUrl"),
            maxLength=255,
        ),
    }


def toFormPayload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    설명: 공개 sample 폼 제출 입력을 DB 저장 포맷으로 정규화
    실패 동작: Step1 필수값/날짜 범위/코드 목록 규칙 위반 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 폼 제출 insert 바인딩용 dict
    갱신일: 2026-03-06
    """
    startDate = normalizeDateText(payload.get("startDate"), required=True)
    endDate = normalizeDateText(payload.get("endDate"), required=True)
    if startDate > endDate:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    selectedFeatures = normalizeJsonCodeList(
        payload.get("selectedFeatures"),
        allowedSet=set(DEFAULT_FORM_FEATURE_CODE_LIST),
    )
    return {
        "name": normalizeText(payload.get("name"), required=True, maxLength=80),
        "email": normalizeEmail(payload.get("email")),
        "phone": normalizeText(payload.get("phone"), required=True, maxLength=40),
        "category": normalizeText(payload.get("category"), required=True, maxLength=40),
        "startDate": startDate,
        "endDate": endDate,
        "budgetRange": normalizeText(payload.get("budgetRange"), required=True, maxLength=80),
        "requirement": normalizeText(payload.get("requirement"), maxLength=2000),
        "selectedFeatures": json.dumps(selectedFeatures, ensure_ascii=False),
        "referenceUrl": normalizeText(payload.get("referenceUrl"), maxLength=500),
        "attachmentName": normalizeText(payload.get("attachmentName"), maxLength=255),
    }


def parseConfigRow(row: dict[str, Any] | None, defaultValue: Any) -> Any:
    """
    설명: CONFIG_JSON 행을 JSON 파싱해 기본값 폴백까지 수행
    실패 동작: 파싱 실패 또는 빈 행이면 defaultValue 그대로 반환
    반환값: JSON 파싱 결과 또는 기본값
    갱신일: 2026-03-06
    """
    rawMap: Any = row or {}
    if not isinstance(rawMap, dict):
        try:
            rawMap = dict(rawMap)
        except Exception:
            rawMap = {}
    configMap = convertKeysToCamelCase(rawMap)
    configJson = configMap.get("configJson")
    if not configJson:
        return defaultValue
    try:
        return json.loads(configJson)
    except Exception:
        return defaultValue


def readModelValue(row: dict[str, Any], *keys: str, defaultValue: Any = None) -> Any:
    """
    설명: SQL source-key 모델과 API 응답 모델의 과도기 호환을 위해 후보 키 중 첫 값을 읽는다
    반환값: 첫 번째 non-None 값 또는 defaultValue
    갱신일: 2026-06-04
    """
    for key in keys:
        if key in row and row.get(key) is not None:
            return row.get(key)
    return defaultValue


def toTaskModel(row: dict[str, Any]) -> dict[str, Any]:
    """
    설명: T_SAMPLE_TASK 조회 행을 프론트 응답용 camelCase 모델로 변환
    처리 규칙: amount는 float, createdAt은 문자열 그대로 유지
    반환값: 공개 sample 업무 모델 dict
    갱신일: 2026-03-06
    """
    source = convertKeysToCamelCase(row)
    return {
        "id": readModelValue(source, "id", "taskNo"),
        "title": readModelValue(source, "title", "dataNm", defaultValue=""),
        "description": readModelValue(source, "description", "dataDesc", defaultValue=""),
        "owner": readModelValue(source, "owner", "ownerNm", defaultValue=""),
        "status": readModelValue(source, "status", "statCd", defaultValue=""),
        "amount": normalizeAmount(readModelValue(source, "amount", "amt")),
        "attachmentName": readModelValue(source, "attachmentName", "attachNm", defaultValue=""),
        "createdAt": readModelValue(source, "createdAt", "regDt"),
    }


def toAdminUserModel(row: dict[str, Any]) -> dict[str, Any]:
    """
    설명: T_SAMPLE_ADMIN_USER 조회 행을 프론트 응답용 camelCase 모델로 변환
    처리 규칙: notify 0/1 값을 bool로 치환하고 나머지 필드는 camelCase로 유지
    반환값: 공개 sample 관리자 사용자 모델 dict
    갱신일: 2026-03-06
    """
    source = convertKeysToCamelCase(row)
    return {
        "id": readModelValue(source, "id", "userNo"),
        "name": readModelValue(source, "name", "userNm", defaultValue=""),
        "email": readModelValue(source, "email", "userEml", defaultValue=""),
        "role": readModelValue(source, "role", "roleCd", defaultValue=""),
        "status": readModelValue(source, "status", "statCd", defaultValue=""),
        "notifyEmail": bool(readModelValue(source, "notifyEmail", defaultValue=False)),
        "notifySms": bool(readModelValue(source, "notifySms", defaultValue=False)),
        "notifyPush": bool(readModelValue(source, "notifyPush", defaultValue=False)),
        "profileImageUrl": readModelValue(source, "profileImageUrl", "profileImgUrl", defaultValue=""),
        "createdAt": readModelValue(source, "createdAt", "regDt"),
    }


def toFormSubmissionModel(row: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    설명: 공개 sample 폼 제출 행을 프론트 응답용 camelCase 모델로 변환
    실패 동작: 입력 행이 없으면 None 반환
    반환값: latest submission 응답용 dict 또는 None
    갱신일: 2026-03-06
    """
    if not row:
        return None
    source = convertKeysToCamelCase(row)
    result = {
        "id": readModelValue(source, "id", "formNo"),
        "name": readModelValue(source, "name", "userNm", defaultValue=""),
        "email": readModelValue(source, "email", "userEml", defaultValue=""),
        "phone": readModelValue(source, "phone", "phoneTxt", defaultValue=""),
        "category": readModelValue(source, "category", "categoryCd", defaultValue=""),
        "startDate": readModelValue(source, "startDate", "startDt", defaultValue=""),
        "endDate": readModelValue(source, "endDate", "endDt", defaultValue=""),
        "budgetRange": readModelValue(source, "budgetRange", "budgetRangeTxt", defaultValue=""),
        "requirement": readModelValue(source, "requirement", "requirementTxt", defaultValue=""),
        "selectedFeatures": readModelValue(source, "selectedFeatures", "featureJson"),
        "referenceUrl": readModelValue(source, "referenceUrl", "refUrl", defaultValue=""),
        "attachmentName": readModelValue(source, "attachmentName", "attachNm", defaultValue=""),
        "createdAt": readModelValue(source, "createdAt", "regDt"),
    }
    result["selectedFeatures"] = normalizeJsonCodeList(result.get("selectedFeatures"))
    return result


@transaction("main_db")
async def saveConfigJson(configKey: str, value: Any) -> Any:
    """
    설명: T_SAMPLE_CONFIG에 JSON 값을 upsert 스타일로 저장
    처리 규칙: 기존 행 존재 시 update, 없으면 insert 수행
    반환값: 저장한 원본 value
    갱신일: 2026-03-06
    """
    db = ensureDbManager()
    configJson = json.dumps(value, ensure_ascii=False)
    existingRow = await db.fetchOneQuery("sample.configByKey", {"configKey": configKey})
    if existingRow:
        await db.executeQuery("sample.configUpdate", {"configKey": configKey, "configJson": configJson})
        return value
    await db.executeQuery("sample.configInsert", {"configKey": configKey, "configJson": configJson})
    return value


@transaction("main_db")
async def ensureBootstrapStorage() -> None:
    """
    설명: 공개 sample 전용 테이블/기본 시드/설정 JSON을 DB에 1회 보장
    처리 규칙: create table 후 bootstrap version 키 존재 여부로 시드 실행 결정
    부작용: T_SAMPLE_* 테이블 및 기본 데이터/설정 레코드 생성 가능
    갱신일: 2026-03-06
    """
    db = ensureDbManager()
    await db.executeQuery("sampleBootstrap.createConfigTable")
    await db.executeQuery("sampleBootstrap.createTaskTable")
    await db.executeQuery("sampleBootstrap.createFormTable")
    await db.executeQuery("sampleBootstrap.createAdminUserTable")
    versionRow = await db.fetchOneQuery(
        "sample.configByKey",
        {"configKey": SAMPLE_CONFIG_KEY["BOOTSTRAP_VERSION"]},
    )
    if versionRow:
        return
    await db.executeQuery("sampleBootstrap.seedTasks")
    await db.executeQuery("sampleBootstrap.seedAdminUsers")
    await db.executeQuery(
        "sample.configInsert",
        {
            "configKey": SAMPLE_CONFIG_KEY["ADMIN_SETTING"],
            "configJson": json.dumps(readDefaultAdminSetting(), ensure_ascii=False),
        },
    )
    await db.executeQuery(
        "sample.configInsert",
        {
            "configKey": SAMPLE_CONFIG_KEY["ROLE_PERMISSION_MAP"],
            "configJson": json.dumps(readDefaultRolePermissionMap(), ensure_ascii=False),
        },
    )
    await db.executeQuery(
        "sample.configInsert",
        {
            "configKey": SAMPLE_CONFIG_KEY["FORM_CATEGORY_CODE_LIST"],
            "configJson": json.dumps(list(DEFAULT_FORM_CATEGORY_CODE_LIST), ensure_ascii=False),
        },
    )
    await db.executeQuery(
        "sample.configInsert",
        {
            "configKey": SAMPLE_CONFIG_KEY["FORM_FEATURE_CODE_LIST"],
            "configJson": json.dumps(list(DEFAULT_FORM_FEATURE_CODE_LIST), ensure_ascii=False),
        },
    )
    await db.executeQuery(
        "sample.configInsert",
        {
            "configKey": SAMPLE_CONFIG_KEY["BOOTSTRAP_VERSION"],
            "configJson": json.dumps({"version": 1}, ensure_ascii=False),
        },
    )


async def ensureBootstrap() -> None:
    """
    설명: 공개 sample 전용 테이블/기본 시드/설정 JSON을 DB에 1회 보장
    처리 규칙: create table 후 bootstrap version 키 존재 여부로 시드 실행 결정
    부작용: T_SAMPLE_* 테이블 및 기본 데이터/설정 레코드 생성 가능
    갱신일: 2026-03-06
    """
    async with BOOTSTRAP_LOCK:
        await ensureBootstrapStorage()


async def getSampleOverview() -> dict[str, Any]:
    """
    설명: 공개 sample 허브/포트폴리오용 전체 카운트 요약 조회
    반환값: taskCount/adminUserCount/formSubmissionCount를 포함한 overview dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    row = await db.fetchOneQuery("sample.overview")
    result = convertKeysToCamelCase(row or {})
    result.setdefault("taskCount", 0)
    result.setdefault("adminUserCount", 0)
    result.setdefault("formSubmissionCount", 0)
    return result


async def getSampleDashboard() -> dict[str, Any]:
    """
    설명: 공개 sample 대시보드용 KPI/월별 추이/최근 업무 묶음 조회
    반환값: statusSummaryList/trendList/recentList를 담은 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    summaryRows = await db.fetchAllQuery("sample.dashboardStatusSummary")
    trendRows = await db.fetchAllQuery("sample.dashboardMonthlyTrend")
    recentRows = await db.fetchAllQuery("sample.dashboardRecent")
    summaryMap = {
        str(source.get("status") or source.get("statCd") or "").lower(): source
        for source in [convertKeysToCamelCase(row) for row in (summaryRows or [])]
    }
    statusSummaryList = []
    for statusCode in ("ready", "pending", "running", "done", "failed"):
        row = summaryMap.get(statusCode, {})
        statusSummaryList.append(
            {
                "status": statusCode,
                "count": int(readModelValue(row, "count", defaultValue=0) or 0),
                "amountSum": normalizeAmount(readModelValue(row, "amountSum")),
            }
        )
    trendList = []
    for row in trendRows or []:
        trendRow = convertKeysToCamelCase(row)
        monthKey = str(readModelValue(trendRow, "monthKey", defaultValue="") or "")
        monthParts = monthKey.split("-")
        label = monthKey
        if len(monthParts) == 2 and monthParts[1].isdigit():
            label = f"{int(monthParts[1])}월"
        trendList.append(
            {
                "label": label,
                "count": int(readModelValue(trendRow, "count", defaultValue=0) or 0),
                "amount": normalizeAmount(readModelValue(trendRow, "amountSum")),
            }
        )
    recentList = [toTaskModel(row) for row in (recentRows or [])]
    return {
        "statusSummaryList": statusSummaryList,
        "trendList": trendList,
        "recentList": recentList,
    }


async def listSampleTasks(
    q: str | None = None,
    status: str | None = None,
    fromDate: str | None = None,
    toDate: str | None = None,
    page: int | None = None,
    size: int | None = None,
) -> dict[str, Any]:
    """
    설명: 공개 sample CRUD 목록을 검색/필터/페이지네이션 조건으로 조회
    반환값: sampleTaskList/total/page/size 구조의 목록 결과 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    config = getConfig()
    globalPolicy = config["API_POLICY"] if "API_POLICY" in config else None
    taskListPolicy = config["API_POLICY.sample.taskList"] if "API_POLICY.sample.taskList" in config else None
    absoluteListSizeCap = normalizePage(
        globalPolicy.get("absolute_list_size_cap") if globalPolicy else None,
        defaultValue=200,
        maxValue=500,
    )
    listSizeMax = normalizePage(
        taskListPolicy.get("list_size_max") if taskListPolicy else (globalPolicy.get("list_size_max") if globalPolicy else None),
        defaultValue=50,
        maxValue=absoluteListSizeCap,
    )
    keyword = normalizeText(q, maxLength=120)
    statusValue = normalizeText(status, maxLength=20).lower()
    if statusValue and statusValue not in ALLOWED_TASK_STATUS:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    fromDateValue = normalizeDateText(fromDate)
    toDateValue = normalizeDateText(toDate)
    if fromDateValue and toDateValue and fromDateValue > toDateValue:
        raise ServiceError("SAMPLE_422_INVALID_INPUT")
    fromDateBound = parseSqlDateBound(fromDateValue) or date(1, 1, 1)
    toDateBound = parseSqlDateBound(toDateValue)
    toDateExclusiveBound = toDateBound + timedelta(days=1) if toDateBound else date(9999, 12, 31)
    pageValue = normalizePage(page, defaultValue=1, maxValue=500)
    sizeValue = min(normalizePage(size, defaultValue=10, maxValue=absoluteListSizeCap), listSizeMax)
    bind = {
        "q": keyword,
        "qLike": f"%{keyword}%" if keyword else "",
        "status": statusValue,
        "fromDate": fromDateBound,
        "toDateExclusive": toDateExclusiveBound,
        "limit": sizeValue,
        "offset": (pageValue - 1) * sizeValue,
    }
    rowList = await db.fetchAllQuery("sample.taskList", bind)
    countRow = await db.fetchOneQuery(
        "sample.taskListCount",
        {
            "q": bind["q"],
            "qLike": bind["qLike"],
            "status": bind["status"],
            "fromDate": bind["fromDate"],
            "toDateExclusive": bind["toDateExclusive"],
        },
    )
    return {
        "sampleTaskList": [toTaskModel(row) for row in (rowList or [])],
        "total": readTotalCount(countRow),
        "page": pageValue,
        "size": sizeValue,
        "q": keyword,
        "status": statusValue,
        "fromDate": fromDateValue,
        "toDate": toDateValue,
    }


async def getSampleTaskDetail(taskId: Any) -> dict[str, Any]:
    """
    설명: 공개 sample 업무 단건 상세 조회
    실패 동작: 대상 ID가 없으면 ServiceError("SAMPLE_404_NOT_FOUND") 발생
    반환값: 공개 sample 업무 상세 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    row = await db.fetchOneQuery("sample.taskDetail", {"id": normalizeId(taskId)})
    if not row:
        raise ServiceError("SAMPLE_404_NOT_FOUND")
    return toTaskModel(row)


@transaction("main_db")
async def createSampleTaskInTransaction(payload: dict[str, Any], idempotencyKey: str | None = None) -> dict[str, Any]:
    """
    설명: 공개 sample 업무 신규 생성
    실패 동작: 생성 후 조회 실패 시 ServiceError("SAMPLE_500_CREATE_FAILED") 발생
    반환값: 생성된 공개 sample 업무 dict
    갱신일: 2026-03-06
    """
    createPayload = toTaskPayload(payload)
    scopeType = "sample.taskCreate"

    replay = await beginIdempotencyRequest(scopeType, idempotencyKey, createPayload)
    if replay.get("status") == "replay":
        return replay.get("result") or {}
    db = ensureDbManager()
    await db.executeQuery("sample.taskCreate", createPayload)
    createdRow = await db.fetchOneQuery("sample.taskFindCreatedCandidate", createPayload)
    if not createdRow:
        raise ServiceError("SAMPLE_500_CREATE_FAILED")
    result = toTaskModel(createdRow)
    await completeIdempotencyRequest(scopeType, idempotencyKey, result)
    return result


async def createSampleTask(payload: dict[str, Any], idempotencyKey: str | None = None) -> dict[str, Any]:
    """
    설명: 공개 sample 업무 신규 생성
    실패 동작: 생성 후 조회 실패 시 ServiceError("SAMPLE_500_CREATE_FAILED") 발생
    반환값: 생성된 공개 sample 업무 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    return await createSampleTaskInTransaction(payload, idempotencyKey=idempotencyKey)


async def updateSampleTask(taskId: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """
    설명: 공개 sample 업무 단건 수정
    실패 동작: 대상 ID가 없으면 ServiceError("SAMPLE_404_NOT_FOUND") 발생
    반환값: 수정 후 최신 공개 sample 업무 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    idValue = normalizeId(taskId)
    currentRow = await db.fetchOneQuery("sample.taskDetail", {"id": idValue})
    if not currentRow:
        raise ServiceError("SAMPLE_404_NOT_FOUND")
    taskModel = toTaskModel(currentRow)
    updatePayload = toTaskPayload(payload, taskModel)
    updatePayload["id"] = idValue
    await db.executeQuery("sample.taskUpdate", updatePayload)
    updatedRow = await db.fetchOneQuery("sample.taskDetail", {"id": idValue})
    if not updatedRow:
        raise ServiceError("SAMPLE_404_NOT_FOUND")
    return toTaskModel(updatedRow)


async def deleteSampleTask(taskId: Any) -> dict[str, Any]:
    """
    설명: 공개 sample 업무 단건 삭제
    실패 동작: 대상 ID가 없으면 ServiceError("SAMPLE_404_NOT_FOUND") 발생
    반환값: 삭제 완료된 ID 메타 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    idValue = normalizeId(taskId)
    currentRow = await db.fetchOneQuery("sample.taskDetail", {"id": idValue})
    if not currentRow:
        raise ServiceError("SAMPLE_404_NOT_FOUND")
    await db.executeQuery("sample.taskDelete", {"id": idValue})
    return {"id": idValue}


async def getSampleFormMeta() -> dict[str, Any]:
    """
    설명: 공개 sample 폼의 옵션 코드/제출 현황 메타를 함께 조회
    반환값: categoryCodeList/featureCodeList/submissionCount/latestSubmission dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    categoryRow = await db.fetchOneQuery("sample.configByKey", {"configKey": SAMPLE_CONFIG_KEY["FORM_CATEGORY_CODE_LIST"]})
    featureRow = await db.fetchOneQuery("sample.configByKey", {"configKey": SAMPLE_CONFIG_KEY["FORM_FEATURE_CODE_LIST"]})
    countRow = await db.fetchOneQuery("sample.formSubmitCount")
    latestRow = await db.fetchOneQuery("sample.formSubmitLatest")
    categoryCodeList = normalizeJsonCodeList(parseConfigRow(categoryRow, list(DEFAULT_FORM_CATEGORY_CODE_LIST)))
    featureCodeList = normalizeJsonCodeList(parseConfigRow(featureRow, list(DEFAULT_FORM_FEATURE_CODE_LIST)))
    return {
        "categoryCodeList": categoryCodeList,
        "featureCodeList": featureCodeList,
        "submissionCount": readTotalCount(countRow),
        "latestSubmission": toFormSubmissionModel(latestRow),
    }


@transaction("main_db")
async def submitSampleForm(payload: dict[str, Any], idempotencyKey: str | None = None) -> dict[str, Any]:
    """
    설명: 공개 sample 복합 폼 제출값을 DB에 저장
    반환값: 저장된 최신 제출 행을 camelCase 모델로 반환
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    createPayload = toFormPayload(payload)
    scopeType = "sample.formSubmit"

    replay = await beginIdempotencyRequest(scopeType, idempotencyKey, createPayload)
    if replay.get("status") == "replay":
        return replay.get("result") or {}
    await db.executeQuery("sample.formSubmitCreate", createPayload)
    latestRow = await db.fetchOneQuery("sample.formSubmitLatest")
    result = toFormSubmissionModel(latestRow) or {}
    await completeIdempotencyRequest(scopeType, idempotencyKey, result)
    return result


async def listSampleAdminUsers(
    page: Any = None,
    size: Any = None,
) -> dict[str, Any]:
    """
    설명: 공개 sample 관리자 사용자 목록을 페이지네이션 조건으로 조회
    반환값: sampleAdminUserList/total/page/size 구조의 목록 결과 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    config = getConfig()
    globalPolicy = config["API_POLICY"] if "API_POLICY" in config else None
    adminUserListPolicy = config["API_POLICY.sample.adminUserList"] if "API_POLICY.sample.adminUserList" in config else None
    absoluteListSizeCap = normalizePage(
        globalPolicy.get("absolute_list_size_cap") if globalPolicy else None,
        defaultValue=200,
        maxValue=500,
    )
    listSizeMax = normalizePage(
        adminUserListPolicy.get("list_size_max") if adminUserListPolicy else (globalPolicy.get("list_size_max") if globalPolicy else None),
        defaultValue=50,
        maxValue=absoluteListSizeCap,
    )
    pageValue = normalizePage(page, defaultValue=1, maxValue=500)
    sizeValue = min(normalizePage(size, defaultValue=50, maxValue=absoluteListSizeCap), listSizeMax)
    bind = {
        "limit": sizeValue,
        "offset": (pageValue - 1) * sizeValue,
    }
    rowList = await db.fetchAllQuery("sample.adminUserList", bind)
    countRow = await db.fetchOneQuery("sample.adminUserListCount")
    return {
        "sampleAdminUserList": [toAdminUserModel(row) for row in (rowList or [])],
        "total": readTotalCount(countRow),
        "page": pageValue,
        "size": sizeValue,
    }


@transaction("main_db")
async def createSampleAdminUserInTransaction(payload: dict[str, Any], idempotencyKey: str | None = None) -> dict[str, Any]:
    """
    설명: 공개 sample 관리자 사용자 신규 생성
    실패 동작: 이메일 중복 시 ServiceError("SAMPLE_409_ALREADY_EXISTS") 발생
    반환값: 생성된 사용자 모델 dict
    갱신일: 2026-03-06
    """
    createPayload = toAdminUserPayload(payload)
    scopeType = "sample.adminUserCreate"

    replay = await beginIdempotencyRequest(scopeType, idempotencyKey, createPayload)
    if replay.get("status") == "replay":
        return replay.get("result") or {}
    db = ensureDbManager()
    duplicateRow = await db.fetchOneQuery("sample.adminUserExistsByEmail", {"email": createPayload["email"]})
    if duplicateRow:
        raise ServiceError("SAMPLE_409_ALREADY_EXISTS")
    await db.executeQuery("sample.adminUserCreate", createPayload)
    createdRow = await db.fetchOneQuery("sample.adminUserFindCreatedCandidate", {"email": createPayload["email"]})
    if not createdRow:
        raise ServiceError("SAMPLE_500_CREATE_FAILED")
    result = toAdminUserModel(createdRow)
    await completeIdempotencyRequest(scopeType, idempotencyKey, result)
    return result


async def createSampleAdminUser(payload: dict[str, Any], idempotencyKey: str | None = None) -> dict[str, Any]:
    """
    설명: 공개 sample 관리자 사용자 신규 생성
    실패 동작: 이메일 중복 시 ServiceError("SAMPLE_409_ALREADY_EXISTS") 발생
    반환값: 생성된 사용자 모델 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    return await createSampleAdminUserInTransaction(payload, idempotencyKey=idempotencyKey)


async def updateSampleAdminUser(userId: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """
    설명: 공개 sample 관리자 사용자 단건 수정
    실패 동작: 대상 사용자가 없으면 ServiceError("SAMPLE_404_NOT_FOUND") 발생
    반환값: 수정된 사용자 모델 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    idValue = normalizeId(userId)
    currentRow = await db.fetchOneQuery("sample.adminUserDetail", {"id": idValue})
    if not currentRow:
        raise ServiceError("SAMPLE_404_NOT_FOUND")
    userModel = toAdminUserModel(currentRow)
    updatePayload = toAdminUserPayload(payload, userModel)
    await db.executeQuery(
        "sample.adminUserUpdate",
        {
            "id": idValue,
            "name": updatePayload["name"],
            "role": updatePayload["role"],
            "status": updatePayload["status"],
            "notifyEmail": updatePayload["notifyEmail"],
            "notifySms": updatePayload["notifySms"],
            "notifyPush": updatePayload["notifyPush"],
            "profileImageUrl": updatePayload["profileImageUrl"],
        },
    )
    updatedRow = await db.fetchOneQuery("sample.adminUserDetail", {"id": idValue})
    if not updatedRow:
        raise ServiceError("SAMPLE_404_NOT_FOUND")
    return toAdminUserModel(updatedRow)


async def getSampleAdminSettings() -> dict[str, Any]:
    """
    설명: 공개 sample 관리자 설정/권한 맵 JSON 조회
    반환값: systemSetting/rolePermissionMap를 담은 dict
    갱신일: 2026-03-06
    """
    await ensureBootstrap()
    db = ensureDbManager()
    systemRow = await db.fetchOneQuery("sample.configByKey", {"configKey": SAMPLE_CONFIG_KEY["ADMIN_SETTING"]})
    permissionRow = await db.fetchOneQuery("sample.configByKey", {"configKey": SAMPLE_CONFIG_KEY["ROLE_PERMISSION_MAP"]})
    return {
        "systemSetting": parseConfigRow(systemRow, readDefaultAdminSetting()),
        "rolePermissionMap": parseConfigRow(permissionRow, readDefaultRolePermissionMap()),
    }


async def updateSampleAdminSettings(payload: dict[str, Any]) -> dict[str, Any]:
    """
    설명: 공개 sample 관리자 시스템 설정 JSON 저장
    실패 동작: 필수값/숫자 제약 위반 시 ServiceError("SAMPLE_422_INVALID_INPUT") 발생
    반환값: 저장 후 최신 systemSetting/rolePermissionMap dict
    갱신일: 2026-03-06
    """
    nextSetting = {
        "siteName": normalizeText(payload.get("siteName"), required=True, maxLength=80),
        "adminEmail": normalizeEmail(payload.get("adminEmail")),
        "maintenanceMode": normalizeBool(payload.get("maintenanceMode")),
        "sessionTimeout": normalizePage(payload.get("sessionTimeout"), defaultValue=60, maxValue=1440),
        "maxUploadMb": normalizePage(payload.get("maxUploadMb"), defaultValue=30, maxValue=1000),
    }
    await saveConfigJson(SAMPLE_CONFIG_KEY["ADMIN_SETTING"], nextSetting)
    return await getSampleAdminSettings()
