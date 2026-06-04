import os
import sys
from fastapi.testclient import TestClient


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testReadyzMessageI18nKo(monkeypatch):
    from server import app
    monkeypatch.setenv("MAINTENANCE_MODE", "true")
    with TestClient(app) as client:
        response = client.get("/readyz", headers={"Accept-Language": "ko-KR"})
        assert response.status_code == 503
        j = response.json()
        assert j["code"] == "OBS_503_NOT_READY"
        assert isinstance(j.get("message"), str)
        assert j["message"] in ("준비되지 않았습니다", "not ready")
