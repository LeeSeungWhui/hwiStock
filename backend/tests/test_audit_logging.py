import os
import sys
from fastapi.testclient import TestClient


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testAuditLoginAndLogoutLogs(caplog):
    from server import app

    with TestClient(app) as client:
        caplog.clear()
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "demo@demo.demo", "password": "password123"},
        )
        assert response.status_code == 200

        seenLogin = any(
            ('"event": "auth.login"' in rec.message and '"success": true' in rec.message)
            for rec in caplog.records
        )
        assert seenLogin

        logoutResponse = client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://localhost:5000"},
        )
        assert logoutResponse.status_code == 204

        seenLogout = any("auth.logout" in rec.message for rec in caplog.records)
        assert seenLogout
