"""
파일명: backend/router/AuthRouter.py
작성자: LSH
갱신일: 2026-04-08
설명: 인증 API 라우터. Access/Refresh 쿠키 기반 토큰 흐름 담당
"""

import os
import re
from functools import lru_cache
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response

from lib.Auth import AuthConfig, getCurrentUser
from lib.Config import getConfig
from lib.I18n import detectLocale, translate as i18nTranslate
from lib.RateLimit import checkRateLimit
from lib.RequestPayloadValidator import readJsonPayloadDict, readOptionalJsonPayloadDict
from lib.Response import errorResponse, successResponse
from lib.ServiceError import buildMappedErrorResponse
from service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def normalizeOrigin(value: str | None) -> str | None:
    """
    설명: Origin/Referer 값을 scheme://host[:port] 형태로 정규화
    반환값: 유효하지 않은 입력은 None, 유효 입력은 정규화된 오리진 문자열
    갱신일: 2026-02-25
    """
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    scheme = str(parsed.scheme or "").strip().lower()
    host = str(parsed.hostname or "").strip().lower()
    if not scheme or not host:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    isDefaultPort = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    if port and not isDefaultPort:
        return f"{scheme}://{host}:{port}"
    return f"{scheme}://{host}"


@lru_cache(maxsize=1)
def getCorsOriginRules() -> tuple[tuple[str, ...], str | None]:
    """
    설명: CORS allowlist/regex와 frontendHost를 합쳐 Origin 검증 룰셋을 구성하는 캐시 함수
    처리 규칙: 설정 오리진 문자열을 정규화하고 localhost/127.0.0.1 alias를 함께 확장
    반환값: (허용 오리진 튜플, 허용 정규식) 튜플
    갱신일: 2026-02-25
    """
    allowOrigins: list[str] = []
    allowOriginRegex: str | None = None

    def addOriginCandidate(candidate: str | None) -> None:
        """
        설명: 오리진 후보를 정규화해 allowlist에 추가 처리(localhost/127 alias 포함)
        부작용: allowOrigins 리스트에 정규화 결과와 localhost/127 alias를 누적
        갱신일: 2026-02-25
        """
        originValue = normalizeOrigin(candidate)
        if not originValue:
            return
        if originValue not in allowOrigins:
            allowOrigins.append(originValue)

        parsed = urlparse(originValue)
        scheme = str(parsed.scheme or "").strip().lower()
        host = str(parsed.hostname or "").strip().lower()
        if not scheme or not host:
            return
        try:
            port = parsed.port
        except ValueError:
            return
        if port:
            portPart = f":{port}"
        else:
            portPart = ""
        if host == "localhost":
            alias = normalizeOrigin(f"{scheme}://127.0.0.1{portPart}")
            if alias and alias not in allowOrigins:
                allowOrigins.append(alias)
        elif host == "127.0.0.1":
            alias = normalizeOrigin(f"{scheme}://localhost{portPart}")
            if alias and alias not in allowOrigins:
                allowOrigins.append(alias)

    try:
        config = getConfig()
        corsSection = config["CORS"] if "CORS" in config else None
        serverSection = config["SERVER"] if "SERVER" in config else None
        originsRaw = (corsSection.get("allow_origins", "") if corsSection else "").strip()
        allowOriginRegex = (corsSection.get("allow_origin_regex", "") if corsSection else "").strip() or None
        for candidate in [item.strip() for item in originsRaw.split(",") if item.strip()]:
            addOriginCandidate(candidate)

        frontendHostRaw = (serverSection.get("frontendHost", "") if serverSection else "").strip()
        for frontendCandidate in [item.strip() for item in frontendHostRaw.split(",") if item.strip()]:
            addOriginCandidate(frontendCandidate)
    except Exception:
        pass
    return tuple(allowOrigins), allowOriginRegex


def isAllowedWebOrigin(origin: str) -> bool:
    """
    설명: 요청 Origin이 CORS allowlist/regex 정책을 만족하는지 확인
    반환값: allowlist 또는 regex 매칭 시 True, 그 외는 False
    갱신일: 2026-02-25
    """
    allowOrigins, allowOriginRegex = getCorsOriginRules()
    if origin in allowOrigins:
        return True
    if not allowOriginRegex:
        return False
    try:
        return re.match(allowOriginRegex, origin) is not None
    except re.error:
        return False


def ensureWebCookieOrigin(request: Request, loc: str) -> JSONResponse | None:
    """
    설명: Web 쿠키 권한 경로(refresh/logout)의 Origin/Referer allowlist 강제
    갱신일: 2026-02-25
    """
    origin = normalizeOrigin(request.headers.get("origin"))
    referer = normalizeOrigin(request.headers.get("referer"))
    requestOrigin = origin or referer
    if not requestOrigin:
        response = JSONResponse(
            status_code=403,
            content=errorResponse(
                message=i18nTranslate("error.csrf_required", "CSRF required", loc),
                code="AUTH_403_ORIGIN_REQUIRED",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    if isAllowedWebOrigin(requestOrigin):
        return None
    response = JSONResponse(
        status_code=403,
        content=errorResponse(
            message=i18nTranslate("error.csrf_required", "CSRF required", loc),
            code="AUTH_403_ORIGIN_DENIED",
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def isSecureRequest(request: Request) -> bool:
    """
    설명: 프록시 환경을 포함해 HTTPS 요청 여부 판정
    처리 규칙: URL scheme, 프록시 헤더, 운영 ENV 값을 순서대로 확인
    갱신일: 2026-02-24
    """
    scheme = str(getattr(request.url, "scheme", "") or "").strip().lower()
    if scheme == "https":
        return True

    forwardedProto = request.headers.get("X-Forwarded-Proto", "")
    forwardedFirst = str(forwardedProto).split(",")[0].strip().lower()
    if forwardedFirst == "https":
        return True
    if str(request.headers.get("X-Forwarded-Ssl", "")).strip().lower() == "on":
        return True
    if str(request.headers.get("Front-End-Https", "")).strip().lower() == "on":
        return True
    if os.getenv("ENV", "").strip().lower() == "prod":
        return True
    return False


def cookieOptions(request: Request, name: str, value: str, maxAge: int | None = None) -> dict:
    """
    설명: 인증 쿠키(HttpOnly/SameSite/Secure) 기본 옵션을 만드 빌더
    반환값: set_cookie 호출에 바로 전달 가능한 옵션 dict
    갱신일: 2026-02-24
    """
    opts = {
        "key": name,
        "value": value,
        "httponly": True,
        "samesite": "lax",
        "secure": isSecureRequest(request),
        "path": "/",
    }
    if maxAge:
        opts["max_age"] = maxAge
    return opts


def clearAuthCookies(response: JSONResponse | Response, request: Request) -> None:
    """
    설명: 인증 쿠키(access/refresh)를 현재 보안 옵션으로 제거
    부작용: response.delete_cookie를 통해 access/refresh 쿠키를 모두 만료시킨
    갱신일: 2026-02-24
    """
    secure = isSecureRequest(request)
    response.delete_cookie(AuthConfig.accessCookieName, path="/", httponly=True, samesite="lax", secure=secure)
    response.delete_cookie(AuthConfig.refreshCookieName, path="/", httponly=True, samesite="lax", secure=secure)


def invalidInputResponse(loc: str, includeAuthHeader: bool = False) -> JSONResponse:
    """
    설명: 잘못된 JSON/입력 형식에 공통 적용하는 422 에러 응답 빌더
    반환값: includeAuthHeader 여부에 따라 WWW-Authenticate 포함 정책이 반영된 JSONResponse
    갱신일: 2026-02-23
    """
    if includeAuthHeader:
        return JSONResponse(
            status_code=422,
            content=errorResponse(
                message=i18nTranslate("error.invalid_input", "invalid input", loc),
                code="AUTH_422_INVALID_INPUT",
            ),
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        )
    return JSONResponse(
        status_code=422,
        content=errorResponse(
            message=i18nTranslate("error.invalid_input", "invalid input", loc),
            code="AUTH_422_INVALID_INPUT",
        ),
        headers={"Cache-Control": "no-store"},
    )


async def parseJsonBody(request: Request) -> dict | None:
    """
    설명: 요청 본문을 JSON dict로 안전하게 파싱하 유틸
    실패 동작: 파싱 실패 또는 dict 타입 불일치 시 None을 반환
    갱신일: 2026-02-23
    """
    return await readJsonPayloadDict(request)


def webSessionResult(tokenPayload: dict) -> dict:
    """
    설명: 웹(cookie) 계약에서 노출할 최소 토큰 메타 result 매퍼
    반환값: tokenType/expiresIn/refreshExpiresIn 필드만 포함한 요약 결과
    갱신일: 2026-02-25
    """
    return {
        "tokenType": "cookie",
        "expiresIn": tokenPayload["expiresIn"],
        "refreshExpiresIn": tokenPayload["refreshExpiresIn"],
    }


def appTokenResult(tokenPayload: dict) -> dict:
    """
    설명: 앱(JSON token) 계약에서 사용하는 토큰 페어 응답 매퍼
    반환값: access/refresh 토큰과 만료 정보를 포함한 앱 전용 결과
    갱신일: 2026-02-25
    """
    return {
        "accessToken": tokenPayload["accessToken"],
        "refreshToken": tokenPayload["refreshToken"],
        "tokenType": tokenPayload["tokenType"],
        "expiresIn": tokenPayload["expiresIn"],
        "refreshExpiresIn": tokenPayload["refreshExpiresIn"],
    }


@router.post("/login")
async def login(request: Request):
    """
    설명: 로그인 요청을 처리하고 Access/Refresh 쿠키 발급
    실패 동작: 입력 검증/인증 실패/레이트리밋/상태저장소 오류를 각각 4xx/5xx로 매핑해 반환
    갱신일: 2026-02-22
    """
    loc = detectLocale(request)
    body = await parseJsonBody(request)
    if body is None:
        return invalidInputResponse(loc, includeAuthHeader=True)
    payload = {
        "username": body.get("username"),
        "password": body.get("password"),
    }
    remember = bool(body.get("rememberMe", False))

    # 간단 입력 검증
    username = payload.get("username")
    password = payload.get("password")
    isShortUsername = not isinstance(username, str) or len(username) < 3
    isShortPassword = not isinstance(password, str) or len(password) < 8
    if isShortUsername or isShortPassword:
        return JSONResponse(
            status_code=422,
            content=errorResponse(message=i18nTranslate("error.invalid_input", "invalid input", loc), code="AUTH_422_INVALID_INPUT"),
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        )

    # 레이트리밋(선체크): 이미 초과된 상태면 인증 로직(쿼리/해시)을 타기 전에 차단한다.
    limited = checkRateLimit(request, username=username, commit=False)
    if limited is not None:
        return limited

    authResult = await AuthService.login(payload, remember)
    if not authResult:

        # 레이트리밋(실패 기록): 로그인 실패 시에만 카운트를 증가시킨다.
        limited = checkRateLimit(request, username=username, commit=True)
        if limited is not None:
            return limited
        return JSONResponse(
            status_code=401,
            content=errorResponse(message=i18nTranslate("error.invalid_credentials", "invalid credentials", loc), code="AUTH_401_INVALID"),
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        )

    tokenPayload = authResult["token"]
    accessMaxAge = AuthConfig.accessTokenExpireMinutes * 60
    refreshMaxAge = (
        AuthConfig.refreshTokenExpireMinutes * 60
        if tokenPayload.get("remember")
        else None
    )

    response = JSONResponse(status_code=200, content=successResponse(result=webSessionResult(tokenPayload)))
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(**cookieOptions(request, AuthConfig.accessCookieName, tokenPayload["accessToken"], maxAge=accessMaxAge))
    response.set_cookie(**cookieOptions(request, AuthConfig.refreshCookieName, tokenPayload["refreshToken"], maxAge=refreshMaxAge))
    return response


@router.post("/signup")
async def signup(request: Request):
    """
    설명: 회원가입 입력 검증과 서비스 에러코드→HTTP 상태코드 매핑을 담당하 핸들러
    실패 동작: 서비스 오류 코드를 상태코드(422/409/503/500)와 메시지로 변환해 반환
    갱신일: 2026-02-22
    """
    loc = detectLocale(request)
    body = await parseJsonBody(request)
    if body is None:
        return invalidInputResponse(loc)
    payload = {
        "name": body.get("name"),
        "email": body.get("email"),
        "password": body.get("password"),
    }
    idempotencyKey = request.headers.get("Idempotency-Key")
    result, errorCode = await AuthService.signup(payload, idempotencyKey=idempotencyKey)
    if errorCode:
        mappedResponse = buildMappedErrorResponse(
            errorCode,
            messageByCode={
                "AUTH_422_INVALID_INPUT": i18nTranslate("error.invalid_input", "invalid input", loc),
                "AUTH_409_USER_EXISTS": i18nTranslate("auth.user_exists", "user already exists", loc),
                "AUTH_503_DB_NOT_READY": i18nTranslate("error.db_not_ready", "database not ready", loc),
            },
            includeNoStore=True,
        )
        if mappedResponse is not None:
            return mappedResponse
        return JSONResponse(
            status_code=500,
            content=errorResponse(
                message=i18nTranslate("error.server_error", "server error", loc),
                code=errorCode,
            ),
            headers={"Cache-Control": "no-store"},
        )

    response = JSONResponse(status_code=201, content=successResponse(result=result))
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/password-reset/request")
async def requestPasswordReset(request: Request):
    """
    설명: 비밀번호 재설정 요청을 접수하고 계정 존재 여부를 숨긴 채 동일 성공 응답 반환
    실패 동작: 입력 형식 오류는 422, 그 외 예외는 500으로 표준 응답화
    갱신일: 2026-04-08
    """
    loc = detectLocale(request)
    body = await parseJsonBody(request)
    if body is None:
        return invalidInputResponse(loc)
    payload = {
        "email": body.get("email"),
    }
    result, errorCode = await AuthService.requestPasswordReset(payload)
    if errorCode == "AUTH_422_INVALID_INPUT":
        return invalidInputResponse(loc)
    if errorCode:
        return JSONResponse(
            status_code=500,
            content=errorResponse(
                message=i18nTranslate("error.server_error", "server error", loc),
                code=errorCode,
            ),
            headers={"Cache-Control": "no-store"},
        )
    response = JSONResponse(status_code=200, content=successResponse(result=result))
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/refresh")
async def refresh(request: Request):
    """
    설명: refresh_token 쿠키로 Access/Refresh 토큰 재발급
    실패 동작: Origin 검증 실패/토큰 누락·무효 시 401·403을 반환하고 필요 시 쿠키를 정리
    갱신일: 2026-02-22
    """
    refreshToken = request.cookies.get(AuthConfig.refreshCookieName)
    loc = detectLocale(request)
    originError = ensureWebCookieOrigin(request, loc)
    if originError is not None:
        return originError
    if not refreshToken:
        response = JSONResponse(
            status_code=401,
            content=errorResponse(
                message=i18nTranslate("auth.refresh_missing", "refresh token missing", loc),
                code="AUTH_401_INVALID",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

        # 브라우저 쿠키가 꼬인 상태(스테일 refresh 등)에서 무한 루프를 방지하기 위해 쿠키를 정리한다.
        clearAuthCookies(response, request)
        response.headers["Cache-Control"] = "no-store"
        return response
    try:
        tokenPayload = await AuthService.refresh(refreshToken)
    except RuntimeError:
        response = JSONResponse(
            status_code=503,
            content=errorResponse(
                message=i18nTranslate(
                    "auth.state_store_unavailable",
                    "temporary auth state storage unavailable",
                    loc,
                ),
                code="AUTH_503_STATE_STORE",
            ),
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    if not tokenPayload:
        response = JSONResponse(
            status_code=401,
            content=errorResponse(
                message=i18nTranslate("auth.refresh_invalid", "invalid refresh token", loc),
                code="AUTH_401_INVALID",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
        clearAuthCookies(response, request)
        response.headers["Cache-Control"] = "no-store"
        return response
    accessMaxAge = AuthConfig.accessTokenExpireMinutes * 60
    refreshMaxAge = (
        AuthConfig.refreshTokenExpireMinutes * 60
        if tokenPayload.get("remember")
        else None
    )
    response = JSONResponse(
        status_code=200,
        content=successResponse(result=webSessionResult(tokenPayload)),
    )
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(**cookieOptions(request, AuthConfig.accessCookieName, tokenPayload["accessToken"], maxAge=accessMaxAge))
    response.set_cookie(**cookieOptions(request, AuthConfig.refreshCookieName, tokenPayload["refreshToken"], maxAge=refreshMaxAge))
    return response


@router.post("/app/login")
async def appLogin(request: Request):
    """
    설명: 앱 로그인(JSON) 계약 전용 인증 핸들러(쿠키 미사용)
    실패 동작: 입력 오류/인증 실패/레이트리밋 시 422/401/429 응답을 반환
    반환값: successResponse(result=appTokenResult(tokenPayload)) 형태 JSONResponse
    갱신일: 2026-02-25
    """
    loc = detectLocale(request)
    body = await parseJsonBody(request)
    if body is None:
        return invalidInputResponse(loc, includeAuthHeader=True)
    payload = {
        "username": body.get("username"),
        "password": body.get("password"),
    }
    remember = bool(body.get("rememberMe", False))

    username = payload.get("username")
    password = payload.get("password")
    isShortUsername = not isinstance(username, str) or len(username) < 3
    isShortPassword = not isinstance(password, str) or len(password) < 8
    if isShortUsername or isShortPassword:
        return JSONResponse(
            status_code=422,
            content=errorResponse(message=i18nTranslate("error.invalid_input", "invalid input", loc), code="AUTH_422_INVALID_INPUT"),
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        )

    limited = checkRateLimit(request, username=username, commit=False)
    if limited is not None:
        return limited

    authResult = await AuthService.login(payload, remember)
    if not authResult:
        limited = checkRateLimit(request, username=username, commit=True)
        if limited is not None:
            return limited
        return JSONResponse(
            status_code=401,
            content=errorResponse(message=i18nTranslate("error.invalid_credentials", "invalid credentials", loc), code="AUTH_401_INVALID"),
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        )

    tokenPayload = authResult["token"]
    response = JSONResponse(status_code=200, content=successResponse(result=appTokenResult(tokenPayload)))
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/app/refresh")
async def appRefresh(request: Request):
    """
    설명: 앱 refresh_token(JSON body)으로 Access/Refresh 토큰 재발급
    실패 동작: refreshToken 누락/무효 또는 상태저장소 오류 시 401/503을 반환
    갱신일: 2026-02-25
    """
    loc = detectLocale(request)
    body = await parseJsonBody(request)
    if body is None:
        return invalidInputResponse(loc, includeAuthHeader=True)
    refreshToken = body.get("refreshToken")
    if not isinstance(refreshToken, str) or not refreshToken.strip():
        return JSONResponse(
            status_code=401,
            content=errorResponse(
                message=i18nTranslate("auth.refresh_missing", "refresh token missing", loc),
                code="AUTH_401_INVALID",
            ),
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        )
    try:
        tokenPayload = await AuthService.refresh(refreshToken)
    except RuntimeError:
        response = JSONResponse(
            status_code=503,
            content=errorResponse(
                message=i18nTranslate(
                    "auth.state_store_unavailable",
                    "temporary auth state storage unavailable",
                    loc,
                ),
                code="AUTH_503_STATE_STORE",
            ),
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    if not tokenPayload:
        return JSONResponse(
            status_code=401,
            content=errorResponse(
                message=i18nTranslate("auth.refresh_invalid", "invalid refresh token", loc),
                code="AUTH_401_INVALID",
            ),
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        )
    response = JSONResponse(status_code=200, content=successResponse(result=appTokenResult(tokenPayload)))
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/app/logout", status_code=204)
async def appLogout(request: Request):
    """
    설명: 앱 로그아웃 처리. body의 refreshToken(옵션) 폐기
    처리 규칙: body가 있으면 JSON dict만 허용하고, 토큰이 없어도 revoke 경로를 안전하게 호출
    갱신일: 2026-02-25
    """
    loc = detectLocale(request)
    body, isBodyValid = await readOptionalJsonPayloadDict(request)
    if not isBodyValid:
        return invalidInputResponse(loc)
    refreshToken = body.get("refreshToken")
    if not isinstance(refreshToken, str):
        refreshToken = None
    try:
        await AuthService.revokeRefreshToken(refreshToken)
    except RuntimeError:
        response = JSONResponse(
            status_code=503,
            content=errorResponse(
                message=i18nTranslate(
                    "auth.state_store_unavailable",
                    "temporary auth state storage unavailable",
                    loc,
                ),
                code="AUTH_503_STATE_STORE",
            ),
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    return Response(status_code=204)


@router.post("/logout", status_code=204)
async def logout(request: Request):
    """
    설명: 로그아웃 처리 후 인증 쿠키 제거
    부작용: 서버 측 refresh revoke 이후 access/refresh 쿠키를 삭제
    갱신일: 2026-02-22
    """
    loc = detectLocale(request)
    originError = ensureWebCookieOrigin(request, loc)
    if originError is not None:
        return originError
    refreshToken = request.cookies.get(AuthConfig.refreshCookieName)
    try:
        await AuthService.revokeRefreshToken(refreshToken)
    except RuntimeError:
        response = JSONResponse(
            status_code=503,
            content=errorResponse(
                message=i18nTranslate(
                    "auth.state_store_unavailable",
                    "temporary auth state storage unavailable",
                    loc,
                ),
                code="AUTH_503_STATE_STORE",
            ),
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    response = Response(status_code=204)
    clearAuthCookies(response, request)
    return response


@router.get("/me")
async def me(request: Request, user=Depends(getCurrentUser)):
    """
    설명: 인증 컨텍스트 사용자 정보를 표준 successResponse로 감싸 반환하는 조회 엔드포인트
    반환값: successResponse(result=userProfile) 형태의 no-store JSONResponse
    갱신일: 2026-02-22
    """
    result = await AuthService.me(user)
    response = JSONResponse(content=successResponse(result=result), status_code=200)
    response.headers["Cache-Control"] = "no-store"
    return response
