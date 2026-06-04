"""
파일명: backend/lib/ServiceError.py
작성자: LSH
갱신일: 2026-02-27
설명: 서비스 계층의 코드 기반 예외를 표현하는 공통 타입
"""

from dataclasses import dataclass
from typing import Any

from fastapi.responses import JSONResponse

from .Response import errorResponse


@dataclass(frozen=True)
class ServiceErrorSpec:
    statusCode: int
    responseCode: str
    defaultMessage: str


SERVICE_ERROR_SPECS: dict[str, ServiceErrorSpec] = {
    "DB_NOT_READY": ServiceErrorSpec(
        statusCode=503,
        responseCode="DB_503_NOT_READY",
        defaultMessage="database not ready",
    ),
    "AUTH_422_INVALID_INPUT": ServiceErrorSpec(
        statusCode=422,
        responseCode="AUTH_422_INVALID_INPUT",
        defaultMessage="invalid input",
    ),
    "AUTH_403_FORBIDDEN": ServiceErrorSpec(
        statusCode=403,
        responseCode="AUTH_403_FORBIDDEN",
        defaultMessage="forbidden",
    ),
    "AUTH_404_USER_NOT_FOUND": ServiceErrorSpec(
        statusCode=404,
        responseCode="AUTH_404_USER_NOT_FOUND",
        defaultMessage="user not found",
    ),
    "AUTH_409_USER_EXISTS": ServiceErrorSpec(
        statusCode=409,
        responseCode="AUTH_409_USER_EXISTS",
        defaultMessage="user already exists",
    ),
    "AUTH_503_DB_NOT_READY": ServiceErrorSpec(
        statusCode=503,
        responseCode="AUTH_503_DB_NOT_READY",
        defaultMessage="database not ready",
    ),
    "IDEMPOTENCY_422_INVALID_INPUT": ServiceErrorSpec(
        statusCode=422,
        responseCode="IDEMPOTENCY_422_INVALID_INPUT",
        defaultMessage="invalid idempotency key",
    ),
    "IDEMPOTENCY_409_IN_PROGRESS": ServiceErrorSpec(
        statusCode=409,
        responseCode="IDEMPOTENCY_409_IN_PROGRESS",
        defaultMessage="request already in progress",
    ),
    "IDEMPOTENCY_409_PAYLOAD_MISMATCH": ServiceErrorSpec(
        statusCode=409,
        responseCode="IDEMPOTENCY_409_PAYLOAD_MISMATCH",
        defaultMessage="idempotency key payload mismatch",
    ),
    "DASH_422_INVALID_INPUT": ServiceErrorSpec(
        statusCode=422,
        responseCode="DASH_422_INVALID_INPUT",
        defaultMessage="invalid input",
    ),
    "DASH_401_UNAUTHORIZED": ServiceErrorSpec(
        statusCode=401,
        responseCode="DASH_401_UNAUTHORIZED",
        defaultMessage="unauthorized",
    ),
    "DASH_404_NOT_FOUND": ServiceErrorSpec(
        statusCode=404,
        responseCode="DASH_404_NOT_FOUND",
        defaultMessage="data not found",
    ),
    "DASH_500_CREATE_FAILED": ServiceErrorSpec(
        statusCode=500,
        responseCode="DASH_500_CREATE_FAILED",
        defaultMessage="create failed",
    ),
    "SAMPLE_422_INVALID_INPUT": ServiceErrorSpec(
        statusCode=422,
        responseCode="SAMPLE_422_INVALID_INPUT",
        defaultMessage="invalid input",
    ),
    "SAMPLE_404_NOT_FOUND": ServiceErrorSpec(
        statusCode=404,
        responseCode="SAMPLE_404_NOT_FOUND",
        defaultMessage="data not found",
    ),
    "SAMPLE_409_ALREADY_EXISTS": ServiceErrorSpec(
        statusCode=409,
        responseCode="SAMPLE_409_ALREADY_EXISTS",
        defaultMessage="already exists",
    ),
    "SAMPLE_500_CREATE_FAILED": ServiceErrorSpec(
        statusCode=500,
        responseCode="SAMPLE_500_CREATE_FAILED",
        defaultMessage="create failed",
    ),
    "OBS_503_NOT_READY": ServiceErrorSpec(
        statusCode=503,
        responseCode="OBS_503_NOT_READY",
        defaultMessage="not ready",
    ),
}


class ServiceError(Exception):
    """
    설명: 서비스 계층에서 API 에러 코드를 명시적으로 전달
    갱신일: 2026-02-27
    """

    def __init__(self, code: str):
        """
        설명: 서비스 에러 코드를 정규화해 예외 메시지로 설정
        처리 규칙: code 입력은 문자열로 강제 변환 후 trim 처리
        부작용: self.code 보관 및 부모 Exception 메시지 초기화
        갱신일: 2026-02-28
        """
        self.code = str(code or "").strip()
        super().__init__(self.code)


def resolveServiceErrorCode(error: Exception | str | None) -> str | None:
    """
    설명: 서비스 예외/코드 문자열에서 표준 에러 코드 추출
    처리 규칙: 문자열 입력은 trim 후 사용하고, 예외 입력은 code 속성/args[0] 순서로 해석
    반환값: 공백이 제거된 코드 문자열 또는 None
    갱신일: 2026-03-02
    """
    if isinstance(error, str):
        normalized = error.strip()
        return normalized or None
    if error is None:
        return None
    codeValue = getattr(error, "code", None)
    if isinstance(codeValue, str) and codeValue.strip():
        return codeValue.strip()
    if error.args:
        firstArg = error.args[0]
        if isinstance(firstArg, str) and firstArg.strip():
            return firstArg.strip()
    return None


def buildMappedErrorResponse(
    error: Exception | str | None,
    *,
    messageByCode: dict[str, str] | None = None,
    result: Any = None,
    includeNoStore: bool = False,
    headers: dict[str, str] | None = None,
) -> JSONResponse | None:
    """
    설명: 서비스 에러 코드 매핑 스펙을 사용해 표준 JSONResponse 생성
    처리 규칙: 등록되지 않은 코드면 None을 반환하고, 등록된 코드만 status/code/message를 고정 적용
    반환값: 매핑된 JSONResponse 또는 None
    갱신일: 2026-03-02
    """
    errorCode = resolveServiceErrorCode(error)
    if not errorCode:
        return None
    spec = SERVICE_ERROR_SPECS.get(errorCode)
    if spec is None:
        return None
    message = spec.defaultMessage
    if messageByCode and errorCode in messageByCode:
        message = messageByCode[errorCode]
    response = JSONResponse(
        status_code=spec.statusCode,
        content=errorResponse(
            message=message,
            result=result,
            code=spec.responseCode,
        ),
    )
    if includeNoStore:
        response.headers["Cache-Control"] = "no-store"
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    if spec.statusCode == 401 and "WWW-Authenticate" not in response.headers:
        response.headers["WWW-Authenticate"] = "Bearer"
    return response
