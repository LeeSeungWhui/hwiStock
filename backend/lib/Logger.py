"""
파일명: backend/lib/Logger.py
작성자: LSH
갱신일: 2025-09-07
설명: 콘솔/파일 로거 설정. 포맷은 JSON 라인(ts/level/requestId/msg 등)
"""

import json
import logging
import os
from typing import Any
from datetime import datetime

# requestId는 Middleware에서 ContextVar로 주입된다.
from .RequestContext import getRequestId

# 로그 디렉토리 생성
logDir = "logs"
if not os.path.exists(logDir):
    os.makedirs(logDir)

# 로그 파일명 생성 (현재 날짜/시간 기준)
logFilename = os.path.join(logDir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 로거 설정
logger: logging.Logger = logging.getLogger()


def resolveLogLevel() -> int:
    """
    설명: 환경변수 LOG_LEVEL 값을 logging 레벨 상수로 변환. 호출 맥락의 제약을 기준으로 동작 기준 확정
    처리 규칙: 미지원 문자열이면 기본 INFO 레벨을 사용
    반환값: logging 모듈의 정수 레벨 상수를 반환
    갱신일: 2026-02-24
    """
    raw = str(os.getenv("LOG_LEVEL", "INFO")).strip().upper()
    return getattr(logging, raw, logging.INFO)


logLevel = resolveLogLevel()
logger.setLevel(logLevel)

# ---------------------------------------------------------------------------
# JSON 라인 포맷터
# ---------------------------------------------------------------------------


class JsonLineFormatter(logging.Formatter):
    """
    설명: 로그를 JSON 한 줄로 출력
    - msg가 이미 JSON(dict) 문자열이면 병합해 구조 로그를 유지한다.
    - requestId는 ContextVar(getRequestId)에서 보강한다.
    갱신일: 2026-01-15
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        설명: logging 레코드를 JSON 한 줄 문자열로 직렬화
        처리 규칙: msg가 JSON 문자열이면 병합하고, 아니면 문자열 msg로 기록
        반환값: requestId/예외 정보가 보강된 JSON 라인 문자열을 반환
        갱신일: 2026-02-24
        """
        payload: dict[str, Any] = {}
        msg = record.getMessage()

        if isinstance(msg, str):
            raw = msg.strip()
            if raw.startswith("{") and raw.endswith("}"):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        payload.update(parsed)
                    else:
                        payload["msg"] = msg
                except Exception:
                    payload["msg"] = msg
            else:
                payload["msg"] = msg
        else:
            payload["msg"] = str(msg)

        payload.setdefault("ts", int(record.created * 1000))
        payload.setdefault("level", record.levelname)
        payload.setdefault("logger", record.name)

        rid = None
        try:
            rid = getRequestId()
        except Exception:
            rid = None
        if rid and "requestId" not in payload:
            payload["requestId"] = rid

        if record.exc_info:
            try:
                payload["exc"] = self.formatException(record.exc_info)
            except Exception:
                payload["exc"] = "exception"

        return json.dumps(payload, ensure_ascii=False)


jsonFormatter = JsonLineFormatter()

# 파일 핸들러 설정 (UTF-8 인코딩)
fileHandler = logging.FileHandler(logFilename, encoding="utf-8")
fileHandler.setLevel(logLevel)
fileHandler.setFormatter(jsonFormatter)

# 콘솔 핸들러 설정
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logLevel)
consoleHandler.setFormatter(jsonFormatter)

# 핸들러 추가
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)
