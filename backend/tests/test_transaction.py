import os
import sys
import time
from fastapi.testclient import TestClient

from conftest import pgTestSettings
from db_support import fetchValPg

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testTransactionSingleAndUniqueRollback():
    from server import app

    with TestClient(app) as client:
        loginResponse = client.post(
            "/api/v1/auth/app/login",
            json={"username": "demo@demo.demo", "password": "password123"},
        )
        assert loginResponse.status_code == 200
        loginPayload = loginResponse.json()
        accessToken = loginPayload["result"]["accessToken"]
        authHeaders = {"Authorization": f"Bearer {accessToken}"}

        response = client.post("/api/v1/transaction/test/single", headers=authHeaders)
        assert response.status_code == 200
        assert response.json()["status"] is True

        # access-log DB 쓰기(비동기)가 잠금을 해제할 시간을 준다.
        time.sleep(0.35)

        response = None
        for _ in range(5):
            response = client.post("/api/v1/transaction/test/unique-violation", headers=authHeaders)
            if response.status_code == 409:
                break

            # 테스트 DB 런타임에서 일시적 잠금/경합이 날 수 있어 짧게 재시도한다.
            time.sleep(0.05)
        assert response is not None
        assert response.status_code == 409
        j = response.json()
        assert j["status"] is False
        assert j["code"] == "TX_409_UNIQUE"

        cnt = fetchValPg(
            pgTestSettings,
            "SELECT COUNT(*) FROM T_TEST_TRANSACTION WHERE VALUE = $1",
            "tx-dup",
        )
        assert cnt == 0


def testTransactionUniqueViolationUnknownErrorReturns500(monkeypatch):
    from server import app
    from service import TransactionService

    async def raiseUnexpectedError():
        raise RuntimeError("db disconnected")

    monkeypatch.setattr(TransactionService, "testUniqueViolation", raiseUnexpectedError)

    with TestClient(app) as client:
        loginResponse = client.post(
            "/api/v1/auth/app/login",
            json={"username": "demo@demo.demo", "password": "password123"},
        )
        assert loginResponse.status_code == 200
        loginPayload = loginResponse.json()
        accessToken = loginPayload["result"]["accessToken"]
        authHeaders = {"Authorization": f"Bearer {accessToken}"}

        response = client.post("/api/v1/transaction/test/unique-violation", headers=authHeaders)
        assert response.status_code == 500
        body = response.json()
        assert body["status"] is False
        assert body["code"] == "TX_500_INTERNAL"
