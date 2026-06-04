import os
import sys
from fastapi.testclient import TestClient


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testI18nInvalidCredentialsKo():
    from server import app
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "demo@demo.demo", "password": "wrongpassword"},
            headers={"Accept-Language": "ko-KR"},
        )
        assert response.status_code == 401
        j = response.json()
        assert j["code"] == "AUTH_401_INVALID"
        assert "아이디" in j["message"] or "비밀번호" in j["message"]


def testI18nInvalidInputEn():
    from server import app
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "a", "password": "b"},
            headers={"Accept-Language": "en-US"},
        )
        assert response.status_code == 422
        j = response.json()
        assert j["code"] == "AUTH_422_INVALID_INPUT"
        assert j["message"] in ("invalid input", "잘못된 입력")  # 폴백 안전성 확인
