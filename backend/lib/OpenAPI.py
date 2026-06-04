"""
파일명: backend/lib/OpenAPI.py
작성자: LSH
갱신일: 2025-09-07
설명: FastAPI OpenAPI 스키마 커스터마이저 부착(보안 스키마/표준 응답/CSRF/servers/codeSamples 등)
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from lib.Logger import logger


def attachOpenAPI(app: FastAPI, config) -> None:
    """
    이름: attachOpenAPI
    설명: 주어진 app에 custom openapi 함수 부착. config는 [AUTH]/기타 값 제공
    갱신일: 2026-02-24
    """

    def readConfigValue(section: Optional[object], key: str, fallback: Optional[str] = None) -> Optional[str]:
        """
        설명: configparser 섹션에서 설정 값을 안전 조회
        처리 규칙: 섹션/키 조회 실패 시 fallback을 반환
        반환값: 설정 문자열 또는 fallback 값을 반환
        갱신일: 2026-02-26
        """
        if section is None:
            return fallback
        getter = getattr(section, "get", None)
        if not callable(getter):
            return fallback
        try:
            return getter(key, fallback=fallback)  # type: ignore[misc]
        except Exception:
            return fallback

    def patchOpenapi(schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        설명: OpenAPI 스키마에 보안/응답/파라미터/코드샘플 정책 패치
        처리 규칙: components/paths를 보강하되 예외 발생 시 로그만 남기고 원본 schema를 반환
        반환값: 패치가 적용된 OpenAPI schema dict를 반환
        갱신일: 2026-02-26
        """
        try:
            authSection = None
            try:
                authSection = config["AUTH"]
            except Exception:
                authSection = None

            accessCookie = (
                readConfigValue(authSection, "access_cookie")
                or "access_token"
            )
            refreshCookie = readConfigValue(authSection, "refresh_cookie") or "refresh_token"

            components = schema.setdefault("components", {})
            securitySchemes = components.setdefault("securitySchemes", {})
            securitySchemes.update(
                {
                    "cookieAuth": {
                        "type": "apiKey",
                        "in": "cookie",
                        "name": accessCookie,
                        "description": (
                            "Browser clients may send this HttpOnly cookie to the Web BFF, "
                            "which forwards it as `Authorization: Bearer <token>` to the backend."
                        ),
                    },
                    "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
                }
            )

            schemas = components.setdefault("schemas", {})
            if "StandardResponse" not in schemas:
                schemas["StandardResponse"] = {
                    "type": "object",
                    "properties": {
                        "status": {"type": "boolean"},
                        "message": {"type": "string"},
                        "result": {},
                        "count": {"type": "integer"},
                        "code": {"type": "string"},
                        "requestId": {"type": "string"},
                    },
                    "required": ["status", "message", "result", "requestId"],
                }
            if "ErrorResponse" not in schemas:
                schemas["ErrorResponse"] = dict(schemas["StandardResponse"])

            if "AuthWebSessionResult" not in schemas:
                schemas["AuthWebSessionResult"] = {
                    "type": "object",
                    "properties": {
                        "tokenType": {"type": "string", "example": "cookie"},
                        "expiresIn": {"type": "integer", "example": 3600},
                        "refreshExpiresIn": {"type": "integer", "example": 604800},
                    },
                    "required": ["tokenType", "expiresIn", "refreshExpiresIn"],
                }
            if "AuthWebSessionResponse" not in schemas:
                schemas["AuthWebSessionResponse"] = {
                    "allOf": [
                        {"$ref": "#/components/schemas/StandardResponse"},
                        {
                            "type": "object",
                            "properties": {"result": {"$ref": "#/components/schemas/AuthWebSessionResult"}},
                        },
                    ]
                }

            if "AuthAppTokenResult" not in schemas:
                schemas["AuthAppTokenResult"] = {
                    "type": "object",
                    "properties": {
                        "accessToken": {"type": "string"},
                        "refreshToken": {"type": "string"},
                        "tokenType": {"type": "string", "example": "bearer"},
                        "expiresIn": {"type": "integer", "example": 3600},
                        "refreshExpiresIn": {"type": "integer", "example": 604800},
                    },
                    "required": ["accessToken", "refreshToken", "tokenType", "expiresIn", "refreshExpiresIn"],
                }
            if "AuthAppTokenResponse" not in schemas:
                schemas["AuthAppTokenResponse"] = {
                    "allOf": [
                        {"$ref": "#/components/schemas/StandardResponse"},
                        {
                            "type": "object",
                            "properties": {"result": {"$ref": "#/components/schemas/AuthAppTokenResult"}},
                        },
                    ]
                }

            if "AuthMeResult" not in schemas:
                schemas["AuthMeResult"] = {
                    "type": "object",
                    "properties": {"username": {"type": "string"}},
                    "required": ["username"],
                }
            if "AuthMeResponse" not in schemas:
                schemas["AuthMeResponse"] = {
                    "allOf": [
                        {"$ref": "#/components/schemas/StandardResponse"},
                        {
                            "type": "object",
                            "properties": {"result": {"$ref": "#/components/schemas/AuthMeResult"}},
                        },
                    ]
                }

            params = components.setdefault("parameters", {})
            csrfHeaderName = readConfigValue(authSection, "csrf_header", "X-CSRF-Token")
            params["CSRFToken"] = {
                "name": csrfHeaderName,
                "in": "header",
                "required": False,
                "schema": {"type": "string"},
                "description": "CSRF token header for cookie-mode unsafe requests.",
            }
            params["OriginHeader"] = {
                "name": "Origin",
                "in": "header",
                "required": False,
                "schema": {"type": "string"},
                "description": "Allowed origin for Web cookie-authorized endpoints (/api/v1/auth/refresh|logout).",
            }
            params["RefererHeader"] = {
                "name": "Referer",
                "in": "header",
                "required": False,
                "schema": {"type": "string"},
                "description": "Fallback header for Web cookie-authorized endpoint origin checks.",
            }

            # 설정값에서 서버 URL 목록을 구성
            def resolveServers():
                """
                설명: 설정 기반 서버 URL 목록을 OpenAPI servers 형식으로 변환
                갱신일: 2026-02-26
                """
                urls = []
                try:
                    serverSection = config["SERVER"]
                except Exception:
                    serverSection = None

                # [SERVER].servers 콤마 리스트가 있으면 우선 사용
                if serverSection is not None:
                    raw = (serverSection.get("servers") or "").strip()
                    if raw:
                        for u in [x.strip() for x in raw.split(",") if x.strip()]:
                            if u not in urls:
                                urls.append(u)

                    # backendHost/base_url/host 값이 있으면 보조로 삽입
                    bh = (
                        serverSection.get("backendHost")
                        or serverSection.get("base_url")
                        or serverSection.get("host")
                    )
                    if bh and bh not in urls:
                        urls.insert(0, bh)
                if not urls:
                    urls = ["http://127.0.0.1:5001"]
                return [{"url": u} for u in urls]

            schema["servers"] = resolveServers()

            tags = sorted({tag for tag in (t.get("name") for t in schema.get("tags", [])) if tag})
            if tags:
                schema["x-tagGroups"] = [{"name": "default", "tags": tags}]

            paths = schema.get("paths", {})

            def ensureJavaScriptCodeSample(operation: Dict[str, Any], source: str) -> None:
                """
                설명: operation에 openapi-client-axios JavaScript 예제 보장
                갱신일: 2026-02-26
                """
                samples = operation.setdefault("x-codeSamples", [])
                hasSample = any(
                    isinstance(sample, dict)
                    and sample.get("lang") == "JavaScript"
                    and sample.get("label") == "openapi-client-axios"
                    for sample in samples
                )
                if hasSample:
                    return
                samples.append(
                    {
                        "lang": "JavaScript",
                        "label": "openapi-client-axios",
                        "source": source,
                    }
                )

            def ensureHeaderRef(operation: Dict[str, Any], refName: str) -> None:
                """
                설명: operation 파라미터에 공통 헤더 ref를 중복 없 추가
                갱신일: 2026-02-26
                """
                parameters = operation.setdefault("parameters", [])
                refPath = f"#/components/parameters/{refName}"
                hasRef = any(isinstance(param, dict) and param.get("$ref") == refPath for param in parameters)
                if not hasRef:
                    parameters.append({"$ref": refPath})

            # 실제 구현은 /api/v1/auth/me 를 사용한다.
            me = paths.get("/api/v1/auth/me", {}).get("get")
            if isinstance(me, dict):

                # backend는 Bearer 토큰을 신뢰한다(Auth.getCurrentUser).
                me["security"] = [{"bearerAuth": []}, {"OAuth2PasswordBearer": []}]
                responses = me.setdefault("responses", {})
                res200 = responses.setdefault("200", {"description": "OK"})
                res200["description"] = res200.get("description") or "OK"
                res200.setdefault("content", {}).setdefault("application/json", {})["schema"] = {
                    "$ref": "#/components/schemas/AuthMeResponse"
                }

            login = paths.get("/api/v1/auth/login", {}).get("post")
            if isinstance(login, dict):
                responses = login.setdefault("responses", {})

                # 참고: 실제 구현은 200 JSON(successResponse) + Set-Cookie 이다(AuthRouter.login).
                responses.pop("204", None)

                res200 = responses.setdefault("200", {"description": "OK"})
                res200["description"] = "OK (sets access/refresh cookies; token strings are hidden in JSON body)"
                res200.setdefault("headers", {})["Set-Cookie"] = {
                    "description": f"Sets `{accessCookie}` and `{refreshCookie}` cookies on success.",
                    "schema": {"type": "string"},
                }
                res200.setdefault("content", {}).setdefault("application/json", {})["schema"] = {
                    "$ref": "#/components/schemas/AuthWebSessionResponse"
                }
                ensureJavaScriptCodeSample(
                    login,
                    (
                        "// Example using openapi-client-axios\n"
                        "// const client = ...;\n"
                        "// await client.POST('/api/v1/auth/login', {\n"
                        "//   body: { username: 'demo@demo.demo', password: 'password123', rememberMe: false },\n"
                        "// });\n"
                        "// The backend responds 200 JSON(tokenType/expiresIn only) and sets HttpOnly cookies."
                    ),
                )

            refresh = paths.get("/api/v1/auth/refresh", {}).get("post")
            if isinstance(refresh, dict):

                # Refresh는 refresh cookie로 새 토큰 발급 + Set-Cookie 를 반환한다.
                responses = refresh.setdefault("responses", {})
                res200 = responses.setdefault("200", {"description": "OK"})
                res200["description"] = "OK (rotates access/refresh cookies; token strings are hidden in JSON body)"
                res200.setdefault("headers", {})["Set-Cookie"] = {
                    "description": f"Rotates `{accessCookie}` and `{refreshCookie}` cookies on success.",
                    "schema": {"type": "string"},
                }
                res200.setdefault("content", {}).setdefault("application/json", {})["schema"] = {
                    "$ref": "#/components/schemas/AuthWebSessionResponse"
                }
                ensureHeaderRef(refresh, "OriginHeader")
                ensureHeaderRef(refresh, "RefererHeader")
                ensureJavaScriptCodeSample(
                    refresh,
                    (
                        "// Example using openapi-client-axios\n"
                        "// const client = ...;\n"
                        "// await client.POST('/api/v1/auth/refresh', {\n"
                        "//   headers: { Origin: 'http://127.0.0.1:5000' },\n"
                        "// });\n"
                        "// Web refresh uses HttpOnly refresh cookie + Origin/Referer allowlist."
                    ),
                )

            logout = paths.get("/api/v1/auth/logout", {}).get("post")
            if isinstance(logout, dict):

                # 실제 구현은 204(No Content).
                responses = logout.setdefault("responses", {})
                responses.setdefault("204", {"description": "No Content"})
                responses.pop("200", None)
                ensureHeaderRef(logout, "OriginHeader")
                ensureHeaderRef(logout, "RefererHeader")
                ensureJavaScriptCodeSample(
                    logout,
                    (
                        "// Example using openapi-client-axios\n"
                        "// const client = ...;\n"
                        "// await client.POST('/api/v1/auth/logout', {\n"
                        "//   headers: { Origin: 'http://127.0.0.1:5000' },\n"
                        "// });"
                    ),
                )

            appLogin = paths.get("/api/v1/auth/app/login", {}).get("post")
            if isinstance(appLogin, dict):
                responses = appLogin.setdefault("responses", {})
                responses.pop("204", None)
                res200 = responses.setdefault("200", {"description": "OK"})
                res200["description"] = "OK (returns access/refresh tokens in JSON; no cookies)"
                res200.setdefault("content", {}).setdefault("application/json", {})["schema"] = {
                    "$ref": "#/components/schemas/AuthAppTokenResponse"
                }
                ensureJavaScriptCodeSample(
                    appLogin,
                    (
                        "// Example using openapi-client-axios\n"
                        "// const client = ...;\n"
                        "// const res = await client.POST('/api/v1/auth/app/login', {\n"
                        "//   body: { username: 'demo@demo.demo', password: 'password123', rememberMe: false },\n"
                        "// });\n"
                        "// console.log(res.data.result.accessToken);"
                    ),
                )

            appRefresh = paths.get("/api/v1/auth/app/refresh", {}).get("post")
            if isinstance(appRefresh, dict):
                responses = appRefresh.setdefault("responses", {})
                responses.pop("204", None)
                res200 = responses.setdefault("200", {"description": "OK"})
                res200["description"] = "OK (returns rotated access/refresh tokens in JSON; no cookies)"
                res200.setdefault("content", {}).setdefault("application/json", {})["schema"] = {
                    "$ref": "#/components/schemas/AuthAppTokenResponse"
                }
                ensureJavaScriptCodeSample(
                    appRefresh,
                    (
                        "// Example using openapi-client-axios\n"
                        "// const client = ...;\n"
                        "// const res = await client.POST('/api/v1/auth/app/refresh', {\n"
                        "//   body: { refreshToken: '<refresh-token>' },\n"
                        "// });\n"
                        "// console.log(res.data.result.accessToken);"
                    ),
                )

            appLogout = paths.get("/api/v1/auth/app/logout", {}).get("post")
            if isinstance(appLogout, dict):
                responses = appLogout.setdefault("responses", {})
                responses.setdefault("204", {"description": "No Content"})
                responses.pop("200", None)
                ensureJavaScriptCodeSample(
                    appLogout,
                    (
                        "// Example using openapi-client-axios\n"
                        "// const client = ...;\n"
                        "// await client.POST('/api/v1/auth/app/logout', {\n"
                        "//   body: { refreshToken: '<refresh-token>' },\n"
                        "// });"
                    ),
                )

            # 참고: 템플릿 기본(토큰 모드)에서는 CSRF 헤더를 강제하지 않는다.
            # 쿠키가 직접 권한을 갖는 엔드포인트를 추가하는 경우에만,
            # 해당 라우트에 CSRFToken 파라미터를 수동으로 붙여 문서화한다.
        except Exception as e:
            logger.error(f"OpenAPI schema patching failed: {e}")
        return schema

    def customOpenapi():
        """
        설명: FastAPI 기본 스키마 생성 후 patchOpenapi를 적용해 캐시
        처리 규칙: 이미 캐시(app.openapi_schema)가 있으면 재생성하지 않고 그대로 반환
        반환값: FastAPI에서 사용하는 최종 OpenAPI schema 객체를 반환
        갱신일: 2026-02-26
        """
        if app.openapi_schema:
            return app.openapi_schema
        openapiSchema = get_openapi(
            title="MyWebTemplate API",
            version=os.getenv("APP_VERSION", "dev"),
            description="API for Web/App backend.",
            routes=app.routes,
        )
        app.openapi_schema = patchOpenapi(openapiSchema)
        return app.openapi_schema

    app.openapi = customOpenapi  # type: ignore
