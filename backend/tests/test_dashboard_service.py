import asyncio
import json
import os
import sys
from decimal import Decimal


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def testSuccessResponseSerializesDecimalFields():
    from lib.Response import successResponse

    payload = successResponse(
        result={
            "dataTemplateList": [{"amount": Decimal("1000.50")}],
            "statusSummaryList": [{"amountSum": Decimal("3000")}],
        }
    )
    json.dumps(payload)
    assert payload["result"]["dataTemplateList"][0]["amount"] == 1000.5
    assert payload["result"]["statusSummaryList"][0]["amountSum"] == 3000


def testCreateDataTemplateUsesCandidateQueryWhenInsertIdMissing(monkeypatch):
    from service import DashboardService
    from lib import Database as DB

    class FakeManager:
        class _FakeTxContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        class _FakeDatabase:
            def transaction(self, **kwargs):
                return FakeManager._FakeTxContext()

        def __init__(self):
            self.fetchQueryCalls = []
            self.database = self._FakeDatabase()

        async def executeQuery(self, queryName, binds):
            assert queryName == "dashboard.create"
            return None

        async def fetchOneQuery(self, queryName, binds):
            self.fetchQueryCalls.append((queryName, dict(binds)))
            if queryName == "dashboard.findCreatedCandidate":
                return {
                    "id": 901,
                    "title": binds.get("title"),
                    "description": binds.get("description"),
                    "status": binds.get("status"),
                    "amount": binds.get("amount"),
                    "tags": binds.get("tags"),
                    "created_at": "2026-02-23 00:00:00",
                }
            return None

    fakeDb = FakeManager()
    monkeypatch.setattr(DB, "getManager", lambda _name=None: fakeDb)
    monkeypatch.setitem(DB.dbManagers, "main_db", fakeDb)

    created = asyncio.run(
        DashboardService.createDataTemplate(
            {
                "title": "후보 조회 테스트",
                "description": "insert id 없음 fallback",
                "status": "ready",
                "amount": 1000,
                "tags": ["qa", "fallback"],
            },
            userId="demo@demo.demo",
        )
    )

    assert int(created["id"]) == 901
    assert created["title"] == "후보 조회 테스트"
    queryNameList = [call[0] for call in fakeDb.fetchQueryCalls]
    assert "dashboard.findCreatedCandidate" in queryNameList
