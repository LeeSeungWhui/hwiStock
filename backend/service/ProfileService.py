"""
파일명: backend/service/ProfileService.py
작성자: LSH
갱신일: 2026-02-22
설명: 프로필 조회/수정 서비스 로직
"""

from typing import Any, Dict

from lib import Database as DB
from lib.Casing import convertKeysToCamelCase
from lib.ServiceError import ServiceError
from lib.Transaction import transaction

profileNotifyStore: Dict[str, Dict[str, bool]] = {}


def ensureDbManager():
    """
    설명: 기본 DB 매니저를 조회하고 준비 상태 확인
    실패 동작: 매니저가 없으면 ServiceError("DB_NOT_READY")를 발생시킨
    갱신일: 2026-02-22
    """
    db = DB.getManager()
    if not db:
        raise ServiceError("DB_NOT_READY")
    return db


def normalizeUserNm(rawValue: Any) -> str:
    """
    설명: userNm 입력값을 검증/정규화. 호출 맥락의 제약을 기준으로 동작 기준 확정
    반환값: 좌우 공백이 제거된 사용자 이름 문자열(길이 2~80)
    갱신일: 2026-02-22
    """
    if not isinstance(rawValue, str):
        raise ServiceError("AUTH_422_INVALID_INPUT")
    value = rawValue.strip()
    if len(value) < 2 or len(value) > 80:
        raise ServiceError("AUTH_422_INVALID_INPUT")
    return value


def normalizeNotifyValue(rawValue: Any) -> bool:
    """
    설명: 알림 설정값을 bool로 정규화. 호출 맥락의 제약을 기준으로 동작 기준 확정
    처리 규칙: bool은 그대로 사용하고 None/빈문자열은 False로 간주
    갱신일: 2026-02-22
    """
    if isinstance(rawValue, bool):
        return rawValue
    if rawValue in (None, ""):
        return False
    raise ServiceError("AUTH_422_INVALID_INPUT")


def ensureUserId(user: Any) -> str:
    """
    설명: 인증 주체에서 USER_ID(sub) 추출
    실패 동작: username이 비어 있거나 문자열이 아니면 ServiceError("AUTH_403_FORBIDDEN")를 발생시킨
    갱신일: 2026-02-22
    """
    userId = getattr(user, "username", None)
    if not isinstance(userId, str) or not userId.strip():
        raise ServiceError("AUTH_403_FORBIDDEN")
    return userId.strip()


def loadNotifyState(userId: str) -> Dict[str, bool]:
    """
    설명: 알림설정(비영속 메모리)을 조회. 호출 맥락의 제약을 기준으로 동작 기준 확정
    반환값: notifyEmail/notifySms/notifyPush 기본값이 보장된 dict
    갱신일: 2026-02-22
    """
    return profileNotifyStore.get(
        userId,
        {"notifyEmail": False, "notifySms": False, "notifyPush": False},
    )


def saveNotifyState(userId: str, payload: Dict[str, Any]) -> Dict[str, bool]:
    """
    설명: 알림설정(비영속 메모리) 저장
    부작용: profileNotifyStore[userId] 항목이 payload 기반으로 갱신
    갱신일: 2026-02-22
    """
    current = loadNotifyState(userId)
    if "notifyEmail" in payload:
        current["notifyEmail"] = normalizeNotifyValue(payload.get("notifyEmail"))
    if "notifySms" in payload:
        current["notifySms"] = normalizeNotifyValue(payload.get("notifySms"))
    if "notifyPush" in payload:
        current["notifyPush"] = normalizeNotifyValue(payload.get("notifyPush"))
    profileNotifyStore[userId] = current
    return current


async def getMyProfile(user: Any) -> Dict[str, Any]:
    """
    설명: 현재 인증 사용자 프로필을 조회. 호출 맥락의 제약을 기준으로 동작 기준 확정
    반환값: DB 프로필(camelCase) + notify 상태가 병합된 dict
    갱신일: 2026-02-22
    """
    userId = ensureUserId(user)
    db = ensureDbManager()
    row = await db.fetchOneQuery("profile.me", {"userId": userId})
    if not row:
        raise ServiceError("AUTH_404_USER_NOT_FOUND")
    result = convertKeysToCamelCase(row)
    notifyState = loadNotifyState(userId)
    result.update(notifyState)
    return result


@transaction("main_db")
async def updateMyProfile(user: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    설명: 현재 인증 사용자 프로필 수정
    처리 규칙: userNm 또는 notify 필드 중 최소 1개가 있어야 하며, 저장 후 최신 프로필을 재조회해 반환
    갱신일: 2026-02-22
    """
    if not isinstance(payload, dict):
        raise ServiceError("AUTH_422_INVALID_INPUT")
    userId = ensureUserId(user)
    db = ensureDbManager()
    row = await db.fetchOneQuery("profile.me", {"userId": userId})
    if not row:
        raise ServiceError("AUTH_404_USER_NOT_FOUND")

    hasUserNm = "userNm" in payload
    hasNotify = any(key in payload for key in ("notifyEmail", "notifySms", "notifyPush"))
    if not hasUserNm and not hasNotify:
        raise ServiceError("AUTH_422_INVALID_INPUT")

    if hasUserNm:
        userNm = normalizeUserNm(payload.get("userNm"))
        await db.executeQuery("profile.updateMe", {"userNm": userNm, "userId": userId})

    notifyState = saveNotifyState(userId, payload)
    updated = await db.fetchOneQuery("profile.me", {"userId": userId})
    if not updated:
        raise ServiceError("AUTH_404_USER_NOT_FOUND")
    result = convertKeysToCamelCase(updated)
    result.update(notifyState)
    return result
