"""
파일명: backend/run.py
작성자: LSH
갱신일: 2026-02-24
설명: 로컬 실행 엔트리. config.ini를 읽어 uvicorn 기동
"""

import os
import sys

import uvicorn

baseDir = os.path.dirname(__file__)
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib.Config import getConfig
from service.HwiStockRunnerService import resolveBindHost as resolveRunnerBindHost

DEFAULT_BIND_HOST = "127.0.0.1"


def _isTruthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def resolveBindHost(config) -> str:
    server = config["SERVER"] if config.has_section("SERVER") else {}
    config_host = server.get("bind_host", "").strip() or None
    return resolveRunnerBindHost(config_host)


def resolveReloadEnabled(config) -> bool:
    server = config["SERVER"] if config.has_section("SERVER") else {}
    envReload = os.getenv("HWISTOCK_BACKEND_RELOAD")
    if envReload is not None:
        return _isTruthy(envReload)
    return _isTruthy(server.get("reload", "false"))


def loadConfig():
    """
    설명: 실행 시점 설정(config.ini) 로딩
    반환값: ConfigParser 인스턴스를 반환하며, 이후 uvicorn 포트/옵션 계산에 사용
    갱신일: 2026-02-24
    """
    return getConfig()


if __name__ == "__main__":
    config = loadConfig()
    serverConfig = config["SERVER"]
    bind_host = resolveBindHost(config)

    uvicorn.run(
        "server:app",
        host=bind_host,
        port=serverConfig.getint("port", 5001),
        reload=resolveReloadEnabled(config),
    )
