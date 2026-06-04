import base64
import hashlib
import os
import sys
import secrets

import pytest

from db_support import canConnectPg, executePg, resolvePgTestSettings

"""
파일명: backend/tests/conftest.py
작성자: LSH
갱신일: 2026-03-12
설명: PostgreSQL 전용 pytest 준비(테스트 DB 설정 확인, 기본 스키마/데이터 시드, 통합테스트 skip 제어)
"""

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

pgTestSettings, pgTestConfigError = resolvePgTestSettings(baseDir)
pgTestReady = False
pgTestSkipReason = pgTestConfigError or "postgresql test db unavailable"

if pgTestSettings:
    os.environ["BACKEND_CONFIG"] = pgTestSettings["configPath"]
    pgTestReady, connectReason = __import__("asyncio").run(canConnectPg(pgTestSettings))
    if not pgTestReady and connectReason:
        pgTestSkipReason = connectReason

INTEGRATION_TEST_FILES = {
    "test_audit_logging.py",
    "test_auth.py",
    "test_dashboard_api.py",
    "test_i18n.py",
    "test_i18n_observability.py",
    "test_observability.py",
    "test_profile_api.py",
    "test_sample_public_api.py",
    "test_transaction.py",
    "test_transaction_savepoint.py",
    "test_tx_logging.py",
}


def hashPasswordPbkdf2(plain: str, iterations: int = 260000) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
    return f"pbkdf2${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def ensureBaseTablesAndDemo() -> None:
    if not pgTestReady or not pgTestSettings:
        return

    executePg(
        pgTestSettings,
        """
        CREATE TABLE IF NOT EXISTS T_USER (
            USER_NO BIGSERIAL PRIMARY KEY,
            USER_ID TEXT UNIQUE NOT NULL,
            USER_PW TEXT NOT NULL,
            USER_NM TEXT,
            USER_EML TEXT,
            ROLE_CD TEXT
        )
        """,
    )
    executePg(
        pgTestSettings,
        """
        CREATE TABLE IF NOT EXISTS T_USER_LOG (
            LOG_ID TEXT PRIMARY KEY,
            USER_ID TEXT NOT NULL,
            REQ_ID TEXT,
            REQ_MTHD TEXT NOT NULL,
            REQ_PATH TEXT NOT NULL,
            RES_CD INTEGER NOT NULL,
            LATENCY_MS INTEGER NOT NULL,
            SQL_CNT INTEGER NOT NULL DEFAULT 0,
            CLIENT_IP TEXT,
            IP_LOC_TXT TEXT,
            IP_LOC_SRC TEXT,
            REG_DT TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    executePg(
        pgTestSettings,
        """
        CREATE TABLE IF NOT EXISTS T_TEST_TRANSACTION (
            ID BIGSERIAL PRIMARY KEY,
            VALUE TEXT UNIQUE
        )
        """,
    )

    passwordHash = hashPasswordPbkdf2("password123")
    executePg(
        pgTestSettings,
        """
        INSERT INTO T_USER (USER_ID, USER_PW, USER_NM, USER_EML, ROLE_CD)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (USER_ID) DO UPDATE
            SET USER_PW = EXCLUDED.USER_PW,
                USER_NM = EXCLUDED.USER_NM,
                USER_EML = EXCLUDED.USER_EML,
                ROLE_CD = EXCLUDED.ROLE_CD
        """,
        "demo@demo.demo",
        passwordHash,
        "Demo User",
        "demo@demo.demo",
        "user",
    )


def markPgTestUnavailable(reason: str) -> None:
    global pgTestReady, pgTestSkipReason
    pgTestReady = False
    pgTestSkipReason = reason


def resetIntegrationDbState() -> None:
    if not pgTestReady or not pgTestSettings:
        return

    try:
        from lib import Database as DB

        DB.dbManagers.clear()
        DB.setPrimaryDbName("main_db")
    except Exception:
        pass

    ensureBaseTablesAndDemo()
    executePg(pgTestSettings, "DELETE FROM T_USER WHERE USER_ID <> $1", "demo@demo.demo")
    executePg(pgTestSettings, "DELETE FROM T_USER_LOG")
    executePg(pgTestSettings, "DELETE FROM T_TEST_TRANSACTION")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_TOKEN")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_REQUEST_IDEMPOTENCY")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_DATA")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_SAMPLE_FORM_SUBMIT")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_SAMPLE_ADMIN_USER")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_SAMPLE_CONFIG")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_SAMPLE_TASK")

    try:
        from service import AuthService

        AuthService.tokenStateStoreReady = False
    except Exception:
        pass

    try:
        from service import SampleService

        SampleService.sampleTaskStoreReady = False
        SampleService.sampleFormStoreReady = False
        SampleService.sampleAdminStoreReady = False
    except Exception:
        pass


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "backend_integration: PostgreSQL test DB가 준비된 경우에만 실행되는 백엔드 통합테스트",
    )


def pytest_collection_modifyitems(config, items):
    for item in items:
        if os.path.basename(str(item.fspath)) in INTEGRATION_TEST_FILES:
            item.add_marker(pytest.mark.backend_integration)
            if not pgTestReady:
                item.add_marker(pytest.mark.skip(reason=pgTestSkipReason))


def pytest_sessionstart(session):
    if not pgTestReady:
        return
    try:
        try:
            from lib import Database as DB

            DB.dbManagers.clear()
            DB.setPrimaryDbName("main_db")
        except Exception:
            pass
        ensureBaseTablesAndDemo()
    except Exception as e:
        markPgTestUnavailable(
            f"postgresql test db bootstrap failed: {type(e).__name__}: {e}"
        )


@pytest.fixture(autouse=True)
def resetRateLimiter():
    try:
        from lib.RateLimit import globalRateLimiter

        globalRateLimiter.store.clear()
    except Exception:
        pass
    yield


@pytest.fixture(autouse=True)
def resetBackendIntegrationState(request):
    if os.path.basename(str(request.fspath)) in INTEGRATION_TEST_FILES and pgTestReady:
        resetIntegrationDbState()
    yield
