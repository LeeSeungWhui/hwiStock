"""
파일명: backend/server.py
작성자: LSH
갱신일: 2025-11-12
설명: FastAPI 서버 기동, DB/CORS/라우터 전체 초기화 담당
"""

import importlib
import ipaddress
import json
import os
import pkgutil
import re
from urllib.parse import quote_plus
from urllib.parse import urlsplit

import router

from fastapi import FastAPI, Request
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lib.Auth import AuthConfig, isStrongAuthSecret
from lib.Database import (
    DatabaseManager,
    loadQueries,
    sqlObserver,
    startWatchingQueryFolder,
    setQueryConfig,
)
from lib import Database as DB
from lib.Logger import logger
from lib.Response import errorResponse
from lib.Middleware import RequestLogMiddleware
from lib.OpenAPI import attachOpenAPI
from lib.Config import getConfig

app = FastAPI()

# ---------------------------------------------------------------------------
# 설정 관련 헬퍼
# ---------------------------------------------------------------------------


def encodeDsnUserInfo(value: object) -> str:
    """
    설명: DB DSN user/password 구간을 URL-safe 문자열로 인코딩
    처리 규칙: None 입력은 빈 문자열로 처리해 DSN 조합 시 예외를 방지
    반환값: urllib.quote_plus 규칙으로 인코딩된 문자열을 반환
    갱신일: 2026-02-24
    """
    if value is None:
        return ""
    return quote_plus(str(value))


def buildNetworkDbUrl(
    scheme: str,
    host: str,
    port: str,
    database: str,
    user: str,
    password: str,
) -> str:
    """
    설명: mysql/postgresql 접속에 사용하는 DSN 문자열 조합 유틸(계정 정보 URL 인코딩 포함)
    처리 규칙: 사용자명/비밀번호는 encodeDsnUserInfo로 선인코딩해 특수문자 충돌을 방지
    반환값: databases 라이브러리가 사용하는 접속 URL 문자열을 반환
    갱신일: 2026-02-24
    """
    safeUser = encodeDsnUserInfo(user)
    safePassword = encodeDsnUserInfo(password)
    safeHost = normalizeNetworkDbHost(host)
    return f"{scheme}://{safeUser}:{safePassword}@{safeHost}:{port}/{database}"


def normalizeNetworkDbHost(host: object) -> str:
    """
    설명: 네트워크 DB host 문자열을 DSN 규격에 맞게 정규화
    처리 규칙: IPv6 literal 입력은 RFC 3986 규칙에 맞춰 대괄호([])를 감싸서 반환
    반환값: DSN host 구간에 안전하게 삽입 가능한 host 문자열
    갱신일: 2026-03-02
    """
    rawHost = str(host or "").strip()
    if not rawHost:
        return "localhost"
    if rawHost.startswith("[") and rawHost.endswith("]"):
        return rawHost
    try:
        ip = ipaddress.ip_address(rawHost)
        if ip.version == 6:
            return f"[{rawHost}]"
    except ValueError:
        pass
    return rawHost


FALSE_ENV_VALUES = frozenset(("0", "false", "no", "off"))
TRUE_ENV_VALUES = frozenset(("1", "true", "yes", "on"))
SAFE_POSTGRES_SCHEMA_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def envText(name: str) -> str:
    return str(os.getenv(name, "") or "").strip()


def hwiStockDbIsolationEnabled() -> bool:
    """
    설명: hwiStock 런타임 DB 격리 강제 여부 반환
    처리 규칙: 기본값은 활성화. pytest 통합 테스트는 명시 opt-in 없으면 기존 테스트 DB를 존중.
    반환값: 격리 강제 활성화 여부
    갱신일: 2026-06-05
    """
    raw = envText("HWISTOCK_DB_ISOLATION_ENABLED").lower()
    if raw in FALSE_ENV_VALUES:
        return False
    if os.getenv("PYTEST_CURRENT_TEST") and raw not in TRUE_ENV_VALUES:
        return False
    return True


def validatePostgresqlSchemaName(schema: str) -> str:
    """
    설명: PostgreSQL search_path에 넣을 hwiStock schema 이름 검증
    처리 규칙: identifier 한 개만 허용해 옵션 주입/다중 명령을 방지
    반환값: 검증된 schema 이름
    갱신일: 2026-06-05
    """
    schemaText = str(schema or "").strip()
    if not schemaText:
        return ""
    if not SAFE_POSTGRES_SCHEMA_PATTERN.fullmatch(schemaText):
        raise RuntimeError("HWISTOCK_POSTGRES_SCHEMA contains an unsafe identifier.")
    return schemaText


def buildPostgresqlConnectOptions(schema: str) -> dict[str, dict[str, str]]:
    """
    설명: asyncpg pool 생성 시 모든 연결에 적용할 PostgreSQL 서버 설정 구성
    처리 규칙: hwiStock schema가 있으면 search_path를 schema,public으로 고정
    반환값: databases.Database에 전달할 connect option dict
    갱신일: 2026-06-05
    """
    schemaText = validatePostgresqlSchemaName(schema)
    if not schemaText:
        return {}
    return {"server_settings": {"search_path": f"{schemaText},public"}}


def databaseNameFromUrl(databaseUrl: str) -> str:
    """
    설명: 로그/검증용으로 DSN path의 database 이름만 추출
    반환값: database 이름 또는 빈 문자열
    갱신일: 2026-06-05
    """
    try:
        parsed = urlsplit(databaseUrl)
        return (parsed.path or "").lstrip("/")
    except Exception:
        return ""


def resolveHwiStockPostgresqlRuntimeConnection(dbConfig) -> tuple[str | None, dict[str, dict[str, str]], dict[str, str]]:
    """
    설명: MyWebTemplate-derived config.ini 대신 hwiStock 전용 런타임 DB 경계를 적용
    처리 규칙:
      1. HWISTOCK_DATABASE_URL이 있으면 전체 DSN을 우선한다.
      2. 없으면 기존 host/user/password는 유지하되 database는 HWISTOCK_POSTGRES_DB로 강제한다.
      3. HWISTOCK_POSTGRES_SCHEMA는 asyncpg server_settings.search_path로 고정한다.
    반환값: (override DSN 또는 None, connect options, 감사용 공개 메타)
    갱신일: 2026-06-05
    """
    if not hwiStockDbIsolationEnabled():
        return None, {}, {"isolation": "disabled"}

    schema = validatePostgresqlSchemaName(envText("HWISTOCK_POSTGRES_SCHEMA") or "hwistock_core")
    connectOptions = buildPostgresqlConnectOptions(schema)
    explicitUrl = envText("HWISTOCK_DATABASE_URL")
    if explicitUrl:
        return (
            explicitUrl,
            connectOptions,
            {
                "isolation": "enabled",
                "source": "HWISTOCK_DATABASE_URL",
                "database": databaseNameFromUrl(explicitUrl),
                "schema": schema,
            },
        )

    database = envText("HWISTOCK_POSTGRES_DB")
    if not database:
        return None, connectOptions, {"isolation": "enabled", "schema": schema}

    dbUrl = buildNetworkDbUrl(
        scheme="postgresql",
        host=envText("HWISTOCK_POSTGRES_HOST") or dbConfig.get("host", "localhost"),
        port=envText("HWISTOCK_POSTGRES_PORT") or dbConfig.get("port", "5432"),
        database=database,
        user=envText("HWISTOCK_POSTGRES_USER") or dbConfig.get("user"),
        password=envText("HWISTOCK_POSTGRES_PASSWORD") or dbConfig.get("password"),
    )
    return (
        dbUrl,
        connectOptions,
        {
            "isolation": "enabled",
            "source": "HWISTOCK_POSTGRES_DB",
            "database": database,
            "schema": schema,
        },
    )


async def onShutdown():
    """
    설명: 애플리케이션 종료 시 DB 연결과 쿼리 워처 리소스 정리
    처리 규칙: 등록된 DB 매니저마다 disconnect를 호출하고, 워처 스레드는 stop/join으로 종료
    부작용: 전역 DB 커넥션과 파일 감시 스레드를 해제
    갱신일: 2026-02-24
    """
    for manager in DB.dbManagers.values():
        if hasattr(manager, "disconnect"):
            await manager.disconnect()
    if sqlObserver:
        sqlObserver.stop()
        sqlObserver.join()

# ---------------------------------------------------------------------------
# 스타트업 작업
# ---------------------------------------------------------------------------


async def onStartup():
    """
    설명: 서버 시작 시 DB 연결, 쿼리 로더, 인증 설정 초기화
    처리 규칙: DB 섹션을 순회해 매니저를 생성/연결하고, query watcher 및 AuthConfig를 초기화
    실패 동작: 개별 DB 연결 실패는 로그로 남기고 나머지 초기화는 계속 진행
    갱신일: 2026-02-24
    """
    logger.info("database connect start")
    global sqlObserver

    config = getConfig()
    dbSections = [s for s in config.sections() if s.startswith("DATABASE")]

    for section in dbSections:
        dbConfig = config[section]
        dbName = dbConfig.get("name", section.lower())
        dbType = dbConfig.get("type")
        dbConnectOptions = {}

        if dbType == "sqlite":

            # 데이터베이스 파일 경로 안전 처리(None/빈문자열 대비)
            rawPath = dbConfig.get("database")
            baseDir = os.path.dirname(__file__)
            if not rawPath:
                dbPath = os.path.join(baseDir, "data", "main.db")
            else:
                dbPath = rawPath
                if not os.path.isabs(dbPath):
                    dbPath = os.path.join(baseDir, dbPath)
            os.makedirs(os.path.dirname(dbPath), exist_ok=True)
            dbUrl = f"sqlite:///{dbPath}"
        elif dbType in ["mysql", "mariadb"]:
            host = dbConfig.get("host", "localhost")
            port = dbConfig.get("port", "3306")
            database = dbConfig.get("database")
            user = dbConfig.get("user")
            password = dbConfig.get("password")

            # databases 패키지와의 호환을 위해 async 드라이버를 사용
            dbUrl = buildNetworkDbUrl(
                scheme="mysql+aiomysql",
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            )
        elif dbType == "postgresql":
            host = dbConfig.get("host", "localhost")
            port = dbConfig.get("port", "5432")
            database = dbConfig.get("database")
            user = dbConfig.get("user")
            password = dbConfig.get("password")
            dbUrl = buildNetworkDbUrl(
                scheme="postgresql",
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            )
            dbConnectOptions = {}
            overrideUrl, overrideOptions, overrideMeta = resolveHwiStockPostgresqlRuntimeConnection(dbConfig)
            if overrideUrl:
                dbUrl = overrideUrl
                dbConnectOptions = overrideOptions
                logger.info(
                    json.dumps(
                        {
                            "event": "hwistock.db.isolation",
                            "dbName": dbName,
                            "source": overrideMeta.get("source"),
                            "database": overrideMeta.get("database"),
                            "schema": overrideMeta.get("schema"),
                        },
                        ensure_ascii=False,
                    )
                )
            elif hwiStockDbIsolationEnabled() and str(database or "").strip().lower() == "mywebtemplate":
                raise RuntimeError(
                    "HWISTOCK_DATABASE_ISOLATION_REQUIRED: refusing to connect hwiStock runtime to mywebtemplate database."
                )
        else:
            logger.warning(f"unsupported database type: {dbType}")
            continue

        try:
            existingManager = DB.dbManagers.get(dbName)
            if (
                existingManager is None
                or not getattr(existingManager, "databaseUrl", None)
                or getattr(existingManager, "databaseUrl", None) != dbUrl
                or getattr(existingManager, "connectOptions", {}) != dbConnectOptions
            ):
                DB.dbManagers[dbName] = DatabaseManager(dbUrl, connectOptions=dbConnectOptions)
            if hasattr(DB.dbManagers[dbName], "connect"):
                await DB.dbManagers[dbName].connect()
            logger.info(f"database connected: {dbName}")
        except Exception as e:
            logger.error(f"database connect failed ({dbName}): {str(e)}")

    logger.info("database connect done")
    logger.info("query load start")

    # 쿼리 로더 설정
    try:
        dbGlobal = config["DATABASE"]
    except Exception:
        dbGlobal = None

    baseDir = os.path.dirname(__file__)
    repoRoot = os.path.dirname(baseDir)
    queryDirRaw = (dbGlobal.get("query_dir") if dbGlobal else None) or "query"
    if not os.path.isabs(queryDirRaw):
        norm = queryDirRaw.replace("\\", "/")
        if norm.startswith("backend/"):
            queryDirAbs = os.path.join(repoRoot, queryDirRaw)
        else:
            queryDirAbs = os.path.join(baseDir, queryDirRaw)
    else:
        queryDirAbs = queryDirRaw

    queryWatch = True
    try:
        queryWatch = dbGlobal.getboolean("query_watch", True) if dbGlobal else True
    except Exception:
        pass

    try:
        queryWatchDebounceMs = dbGlobal.getint("query_watch_debounce_ms", 150) if dbGlobal else 150
    except Exception:
        queryWatchDebounceMs = 150

    setQueryConfig(queryDirAbs, queryWatch, queryWatchDebounceMs)

    loadQueries()
    logger.info("query load done")
    sqlObserver = startWatchingQueryFolder()
    if sqlObserver:
        logger.info("query watcher started")

    # 인증 설정 로딩
    config = getConfig()
    authConfig = config["AUTH"]
    serverConfig = config["SERVER"] if "SERVER" in config else {}

    # Refresh 토큰 회전 직후 경합(동시 탭/네트워크 재시도)을 완화하기 위한 유예 시간(ms)
    try:
        refreshGraceMs = authConfig.getint("refresh_grace_ms", 10_000)
    except Exception:
        refreshGraceMs = 10_000
    secretKey = authConfig.get("secret_key", "")
    tokenEnable = authConfig.getboolean("token_enable", True)
    runtimeRaw = serverConfig.get("runtime", "DEV") if serverConfig else "DEV"
    runtime = str(runtimeRaw or "").strip().upper()
    allowWeakAuthSecret = runtime in {"TEST", "CI"} or str(os.getenv("ALLOW_WEAK_AUTH_SECRET", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    strictSecretValidation = tokenEnable and not allowWeakAuthSecret

    if strictSecretValidation and not isStrongAuthSecret(secretKey):
        raise RuntimeError(
            "AUTH secret_key is too weak. Use 32+ chars strong random secret and restart."
        )
    if tokenEnable and not strictSecretValidation and not isStrongAuthSecret(secretKey):
        logger.warning(
            "weak AUTH secret_key allowed in non-strict runtime. set ALLOW_WEAK_AUTH_SECRET=false in runtime."
        )
    AuthConfig.initConfig(
        secretKey=secretKey,
        accessExpireMinutes=authConfig.getint("token_expire", 3600) // 60,
        refreshExpireMinutes=authConfig.getint("refresh_expire", 3600 * 24 * 7)
        // 60,
        refreshGraceMs=refreshGraceMs,
        tokenEnable=tokenEnable,
        accessCookie=authConfig.get("access_cookie", "access_token"),
        refreshCookie=authConfig.get("refresh_cookie", "refresh_token"),
        strictSecretValidation=strictSecretValidation,
    )

    # 사용자 테이블 생성/시드는 스크립트나 AuthService가 담당하므로 여기서는 건드리지 않는다.
    # 외부 DB를 존중하기 위해 스타트업 단계에서 묵시적 DDL/DML을 수행하지 않는다.

    try:
        attachOpenAPI(app, getConfig())
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 애플리케이션 설정
# ---------------------------------------------------------------------------

# 설정은 한 번만 로드해 재사용
config = getConfig()

# DB 헬퍼가 기본 DB 이름을 알 수 있도록 전달(실패 시 무시)
try:
    DB.setPrimaryDbName(config["DATABASE"].get("name", "main_db"))
except Exception:
    pass

# CORS 설정
corsConfig = config["CORS"]
originsRaw = corsConfig.get("allow_origins", "").strip()
originRegexRaw = corsConfig.get("allow_origin_regex", "").strip()
try:
    allowCredentials = corsConfig.getboolean("allow_credentials", True)
except Exception:
    allowCredentials = True

# 공통 규칙: CORS는 와일드카드('*')를 허용하지 않는다(환경별 allowlist 강제).
if originsRaw == "*":
    raise ValueError(
        "CORS misconfig: allow_origins='*' is forbidden. "
        "Use explicit allowlist origins instead."
    )
else:
    origins = [o.strip() for o in originsRaw.split(",") if o.strip()]

if "*" in origins:
    raise ValueError(
        "CORS misconfig: wildcard '*' token is forbidden in allow_origins list. "
        "Use explicit allowlist origins instead."
    )

allowOriginRegex = originRegexRaw or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allowOriginRegex,
    allow_credentials=allowCredentials,
    allow_methods=["*"],
    allow_headers=["*"]
)

# FastAPI 이벤트 핸들러 연결
app.add_event_handler("startup", onStartup)
app.add_event_handler("shutdown", onShutdown)

# 요청 로그 및 request id 전파 미들웨어
app.add_middleware(RequestLogMiddleware)

# 라우터 로딩
logger.info("router load start")

# 설정값에 따라 데모 라우터를 비활성화할 수 있음
disableDemoRoutes = True
try:
    disableDemoRoutes = config["SERVER"].getboolean("disable_demo_routes", True)
except Exception:
    disableDemoRoutes = True

for _, moduleName, _ in pkgutil.iter_modules(router.__path__, router.__name__ + "."):

    # 데모/샘플 라우터는 비활성화 시 제외
    if disableDemoRoutes and moduleName.endswith((".TransactionRouter", ".SampleRouter")):
        continue
    module = importlib.import_module(moduleName)
    if hasattr(module, "router"):
        app.include_router(module.router)
logger.info("router load done")


@app.exception_handler(Exception)
async def globalExceptionHandler(request: Request, exc: Exception):
    """
    설명: 처리되지 않은 예외를 표준 에러 응답(JSON)으로 변환
    처리 규칙: 내부 예외 상세는 응답에서 숨기고 path/code만 포함한 500 응답을 반환
    실패 동작: 로거 기록 실패는 무시하고 예외 핸들링 흐름을 유지
    반환값: status=500 표준 JSONResponse
    갱신일: 2026-02-28
    """
    try:

        # 내부 예외 메시지는 응답에 노출하지 않고, 로그로만 남긴다.
        logger.exception(f"unhandled_exception path={request.url.path}")
    except Exception:
        pass
    return JSONResponse(
        status_code=500,
        content=errorResponse(
            message="internal server error",
            result={"path": request.url.path},
            code="HTTP_500_INTERNAL",
        ),
        headers={"Cache-Control": "no-store"},
    )


def sanitizeValidationErrors(errors: object) -> list[dict]:
    """
    설명: RequestValidationError의 errors()를 노출 가능한 형태로 정리
    주의: 입력값(input) 등 민감정보가 포함될 수 있어 최소 필드만 반환
    갱신일: 2026-01-15
    """
    if not isinstance(errors, list):
        return []
    safe: list[dict] = []
    for item in errors:
        if not isinstance(item, dict):
            continue
        safe.append(
            {
                "loc": item.get("loc"),
                "msg": item.get("msg"),
                "type": item.get("type"),
            }
        )
    return safe


@app.exception_handler(RequestValidationError)
async def requestValidationExceptionHandler(request: Request, exc: RequestValidationError):
    """
    설명: 요청 바디/파라미터 검증 실패를 표준 422 응답으로 변환
    처리 규칙: 검증 오류 detail에서 loc/msg/type 최소 필드만 노출
    반환값: status=422 표준 JSONResponse
    갱신일: 2026-02-28
    """
    return JSONResponse(
        status_code=422,
        content=errorResponse(
            message="invalid request",
            result={
                "path": request.url.path,
                "detail": sanitizeValidationErrors(exc.errors()),
            },
            code="VALID_422_REQUEST",
        ),
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(HTTPException)
async def httpExceptionHandler(request: Request, exc: HTTPException):
    """
    설명: HTTPException을 표준 에러 응답으로 변환하고 401 헤더 보강
    처리 규칙: detail dict의 message/code를 우선 사용하고 없으면 status 기반 기본 코드를 부여
    반환값: code/path/detail을 포함한 표준 JSONResponse를 반환
    갱신일: 2026-02-24
    """
    headers = dict(getattr(exc, "headers", None) or {})

    # 401은 인증 방식에 맞춰 WWW-Authenticate 헤더를 유지/보강한다.
    if int(getattr(exc, "status_code", 500) or 500) == 401:
        headers.setdefault("WWW-Authenticate", "Bearer")

    statusCode = int(getattr(exc, "status_code", 500) or 500)
    if statusCode == 401:
        headers.setdefault("Cache-Control", "no-store")

    detail = getattr(exc, "detail", None)
    message = str(detail) if detail is not None else "error"

    # detail이 dict일 경우(확장) message/code 힌트를 지원한다.
    code = None
    if isinstance(detail, dict):
        message = (
            detail.get("message")
            or detail.get("detail")
            or message
        )
        code = detail.get("code") or None

    if not code:
        if statusCode == 401:
            code = "AUTH_401_UNAUTHORIZED"
        elif statusCode == 403:
            code = "AUTH_403_FORBIDDEN"
        elif statusCode == 404:
            code = "HTTP_404_NOT_FOUND"
        else:
            code = f"HTTP_{statusCode}"

    return JSONResponse(
        status_code=statusCode,
        content=errorResponse(
            message=message,
            result={"path": request.url.path, "detail": detail},
            code=code,
        ),
        headers=headers,
    )
