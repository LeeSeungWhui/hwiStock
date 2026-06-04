"""
파일명: backend/lib/Config.py
작성자: LSH
갱신일: 2026-02-24
설명: 구성 로더 + server. config 접근 헬퍼
 - loadConfig: backend 기준 상대 경로로 INI 로드
 - get: server.config 노출 값을 간편히 읽기
"""

from __future__ import annotations

from configparser import ConfigParser
import os
import sys

# 로거 (선택)
try:
    from .Logger import logger  # type: ignore
except Exception:  # pragma: no cover
    logger = None  # type: ignore


configCache: ConfigParser | None = None
configCachePath: str | None = None


def backendDir() -> str:
    """
    설명: 현재 모듈(__file__) 기준으로 계산한 backend 루트 절대 경로
    처리 규칙: 입력값을 검증하고 실패 시 예외/기본값 경로로 수렴
    갱신일: 2026-02-24
    """
    return os.path.dirname(os.path.dirname(__file__))


def resolvePath(filename: str) -> str:
    """설명: 설정 파일 경로를 backend 기준 절대 경로로 해석 반환값: 절대 경로 문자열. 갱신일: 2026-02-24"""
    if os.path.isabs(filename):
        return filename
    return os.path.join(backendDir(), filename)


def get(section: str, key: str, default: str | None = None) -> str:
    """설명: 지정 섹션/키 값 조회 반환값: 존재하는 설정값 또는 기본값. 갱신일: 2025-11-12"""
    conf = getConfig()
    sec = conf[section]
    return sec.get(key, default) if default is not None else sec[key]


def getAuth(key: str, default: str | None = None) -> str:
    """설명: AUTH 섹션 키 조회 반환값: AUTH 섹션의 설정값 또는 기본값. 갱신일: 2025-11-12"""
    return get("AUTH", key, default)


def loadConfig(filename: str) -> ConfigParser:
    """설명: backend 기준 상대경로로 설정 파일을 반환값: 로드 완료된 ConfigParser 인스턴스. 갱신일: 2025-11-12"""
    if logger:
        try:
            logger.info("config load start")
        except Exception:
            pass

    config = ConfigParser()

# backend/lib 경로를 backend 기준으로 보정
    configPath = resolvePath(filename)
    with open(configPath, "r", encoding="utf-8") as f:
        config.read_file(f)

    if logger:
        try:
            logger.info("config load done")
        except Exception:
            pass
    return config


def getConfig(path: str | None = None, forceReload: bool = False) -> ConfigParser:
    """
    설명: 설정 캐시 반환과 forceReload/경로 변경 시 설정 파일 재로딩
    처리 규칙: path 미지정이면 BACKEND_CONFIG 또는 기존 캐시 경로를 우선 사용
    부작용: 재로딩 시 configCache/configCachePath를 갱신하고 파생 캐시를 무효화
    반환값: 현재 유효한 ConfigParser 인스턴스
    갱신일: 2026-02-28
    """
    global configCache, configCachePath

    # 환경변수 우선
    if path is None:
        path = os.getenv("BACKEND_CONFIG", configCachePath or "config.ini")

    resolved = resolvePath(path)
    if forceReload or configCache is None or configCachePath != resolved:
        configCache = loadConfig(path)
        configCachePath = resolved
        clearConfigDependentCaches()
    return configCache


def reloadConfig() -> ConfigParser:
    """설명: 캐시를 무시하고 설정 다시 반환값: 최신 설정 ConfigParser 인스턴스. 갱신일: 2025-11-12"""
    return getConfig(forceReload=True)


def clearConfigDependentCaches() -> None:
    """
    설명: 설정 파생 캐시(AuthRouter CORS rules 등) 무효화
    부작용: AuthRouter.getCorsOriginRules.cache_clear()가 호출되어 CORS 룰 캐시가 비워진
    갱신일: 2026-02-26
    """
    module = sys.modules.get("router.AuthRouter") or sys.modules.get("backend.router.AuthRouter")
    if not module:
        return
    getCorsOriginRules = getattr(module, "getCorsOriginRules", None)
    cacheClear = getattr(getCorsOriginRules, "cache_clear", None)
    if callable(cacheClear):
        cacheClear()
