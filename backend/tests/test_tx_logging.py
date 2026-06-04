import os
import sys
from fastapi.testclient import TestClient


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testTxLogsIncludeRequestIdAndSqlCount(caplog):
    from server import app

    with TestClient(app) as client:
        loginResponse = client.post(
            "/api/v1/auth/app/login",
            json={"username": "demo@demo.demo", "password": "password123"},
        )
        assert loginResponse.status_code == 200
        loginPayload = loginResponse.json()
        accessToken = loginPayload["result"]["accessToken"]

        caplog.clear()
        requestId = "rid-tx-1234"
        response = client.post(
            "/api/v1/transaction/test/single",
            headers={
                "Authorization": f"Bearer {accessToken}",
                "X-Request-Id": requestId,
            },
        )
        assert response.status_code == 200
        seen = False
        for rec in caplog.records:
            msg = rec.message
            if "tx.commit" in msg and "sql_count=" in msg and ("requestId=" + requestId) in msg:
                seen = True
                break
        assert seen
