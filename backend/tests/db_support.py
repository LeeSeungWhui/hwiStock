"""
파일명: backend/tests/db_support.py
작성자: LSH
갱신일: 2026-04-08
설명: PostgreSQL 기반 백엔드 테스트용 설정/쿼리 헬퍼
"""

import asyncio
import os
from configparser import ConfigParser
from typing import Any

import asyncpg


def readConfig(path: str) -> ConfigParser:
    """
    설명: INI 파일을 UTF-8 기준으로 읽어 ConfigParser로 반환
    반환값: 로딩된 ConfigParser 인스턴스
    갱신일: 2026-04-08
    """
    config = ConfigParser()
    config.read(path, encoding="utf-8")
    return config


def resolvePgTestSettings(baseDir: str) -> tuple[dict[str, Any] | None, str | None]:
    """
    설명: 백엔드 테스트용 PostgreSQL 접속 설정을 config 파일에서 해석
    실패 동작: 설정 누락/불완전 시 (None, 사유) 반환
    반환값: 접속 설정 dict 또는 오류 사유 tuple
    갱신일: 2026-04-08
    """
    configPath = os.getenv("BACKEND_TEST_CONFIG") or os.path.join(baseDir, "config.test.ini")
    if not os.path.exists(configPath):
        return None, f"postgresql test config missing: {configPath}"

    config = readConfig(configPath)
    if "DATABASE" not in config:
        return None, f"DATABASE section missing: {configPath}"

    dbConfig = config["DATABASE"]
    dbType = str(dbConfig.get("type", "")).strip().lower()
    if dbType != "postgresql":
        return None, f"sqlite backend tests removed: DATABASE.type must be postgresql in {configPath}"

    mainConfigPath = os.path.join(baseDir, "config.ini")
    mainDbConfig = {}
    if os.path.exists(mainConfigPath):
        mainConfig = readConfig(mainConfigPath)
        if "DATABASE" in mainConfig:
            mainDbConfig = dict(mainConfig["DATABASE"])

    host = str(dbConfig.get("host") or mainDbConfig.get("host") or "127.0.0.1").strip()
    portRaw = str(dbConfig.get("port") or mainDbConfig.get("port") or "5432").strip() or "5432"
    database = str(dbConfig.get("database", "")).strip()
    user = str(dbConfig.get("user") or mainDbConfig.get("user") or "").strip()
    password = dbConfig.get("password") or mainDbConfig.get("password") or ""
    if not database or not user:
        return None, f"postgresql test config incomplete: {configPath}"

    try:
        port = int(portRaw)
    except Exception:
        return None, f"invalid postgres port in test config: {configPath}"

    return {
        "configPath": configPath,
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }, None


async def canConnectPg(settings: dict[str, Any]) -> tuple[bool, str | None]:
    """
    설명: 테스트용 PostgreSQL에 실제 접속 가능한지 사전 확인
    실패 동작: 연결 실패 시 (False, 사유) 반환
    반환값: 연결 가능 여부와 사유 tuple
    갱신일: 2026-04-08
    """
    try:
        connection = await asyncpg.connect(
            host=settings["host"],
            port=settings["port"],
            database=settings["database"],
            user=settings["user"],
            password=settings["password"],
            timeout=2,
        )
    except Exception as e:
        return False, f"postgresql test db unavailable: {type(e).__name__}: {e}"

    try:
        await connection.execute("SELECT 1")
        return True, None
    finally:
        await connection.close()


async def executePgAsync(settings: dict[str, Any], sql: str, *args: Any) -> str:
    """
    설명: 단일 SQL 실행 결과 문자열을 비동기로 반환
    부작용: 새 asyncpg 연결을 열고 SQL을 실행한 뒤 즉시 닫는다.
    반환값: asyncpg execute 결과 문자열
    갱신일: 2026-04-08
    """
    connection = await asyncpg.connect(
        host=settings["host"],
        port=settings["port"],
        database=settings["database"],
        user=settings["user"],
        password=settings["password"],
        timeout=5,
    )
    try:
        return await connection.execute(sql, *args)
    finally:
        await connection.close()


async def fetchRowPgAsync(settings: dict[str, Any], sql: str, *args: Any) -> asyncpg.Record | None:
    """
    설명: 단일 행 조회를 비동기로 실행
    반환값: 조회된 첫 행 또는 None
    갱신일: 2026-04-08
    """
    connection = await asyncpg.connect(
        host=settings["host"],
        port=settings["port"],
        database=settings["database"],
        user=settings["user"],
        password=settings["password"],
        timeout=5,
    )
    try:
        return await connection.fetchrow(sql, *args)
    finally:
        await connection.close()


async def fetchValPgAsync(settings: dict[str, Any], sql: str, *args: Any) -> Any:
    """
    설명: 단일 스칼라 값 조회를 비동기로 실행
    반환값: 첫 컬럼 값 또는 None
    갱신일: 2026-04-08
    """
    connection = await asyncpg.connect(
        host=settings["host"],
        port=settings["port"],
        database=settings["database"],
        user=settings["user"],
        password=settings["password"],
        timeout=5,
    )
    try:
        return await connection.fetchval(sql, *args)
    finally:
        await connection.close()


def executePg(settings: dict[str, Any], sql: str, *args: Any) -> str:
    """
    설명: executePgAsync를 동기 테스트 코드에서 바로 호출할 수 있게 래핑
    반환값: asyncpg execute 결과 문자열
    갱신일: 2026-04-08
    """
    return asyncio.run(executePgAsync(settings, sql, *args))


def fetchRowPg(settings: dict[str, Any], sql: str, *args: Any) -> asyncpg.Record | None:
    """
    설명: fetchRowPgAsync를 동기 테스트 코드에서 호출할 수 있게 래핑
    반환값: 조회된 첫 행 또는 None
    갱신일: 2026-04-08
    """
    return asyncio.run(fetchRowPgAsync(settings, sql, *args))


def fetchValPg(settings: dict[str, Any], sql: str, *args: Any) -> Any:
    """
    설명: fetchValPgAsync를 동기 테스트 코드에서 호출할 수 있게 래핑
    반환값: 조회된 첫 컬럼 값 또는 None
    갱신일: 2026-04-08
    """
    return asyncio.run(fetchValPgAsync(settings, sql, *args))
