import os
import sys
from fastapi.testclient import TestClient


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def authHeaderFromCookie(client):
    token = client.cookies.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def loginAsDemo(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "demo@demo.demo", "password": "password123", "rememberMe": True},
    )
    assert response.status_code == 200


def testProfileMeGetAndUpdateFlow():
    from server import app

    with TestClient(app) as client:
        loginAsDemo(client)
        headers = authHeaderFromCookie(client)

        getResponse = client.get("/api/v1/profile/me", headers=headers)
        assert getResponse.status_code == 200
        getBody = getResponse.json()
        assert getBody["status"] is True
        assert getBody["result"]["userId"] == "demo@demo.demo"

        updateResponse = client.put(
            "/api/v1/profile/me",
            json={
                "userNm": "Demo Profile",
                "notifyEmail": True,
                "notifySms": False,
                "notifyPush": True,
            },
            headers=headers,
        )
        assert updateResponse.status_code == 200
        updateBody = updateResponse.json()
        assert updateBody["status"] is True
        assert updateBody["result"]["userNm"] == "Demo Profile"
        assert updateBody["result"]["notifyEmail"] is True
        assert updateBody["result"]["notifyPush"] is True

        refetchResponse = client.get("/api/v1/profile/me", headers=headers)
        assert refetchResponse.status_code == 200
        refetchResult = refetchResponse.json()["result"]
        assert refetchResult["userNm"] == "Demo Profile"
        assert refetchResult["notifyEmail"] is True
        assert refetchResult["notifyPush"] is True


def testProfileUpdateInvalidInputReturns422():
    from server import app

    with TestClient(app) as client:
        loginAsDemo(client)
        headers = authHeaderFromCookie(client)

        response = client.put("/api/v1/profile/me", json={"userNm": "A"}, headers=headers)
        assert response.status_code == 422
        body = response.json()
        assert body["status"] is False
        assert body["code"] == "AUTH_422_INVALID_INPUT"


def testProfileRequiresAuth():
    from server import app

    with TestClient(app) as client:
        response = client.get("/api/v1/profile/me")
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"
