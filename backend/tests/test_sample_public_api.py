import os
import sys

from fastapi.testclient import TestClient

from db_support import executePg
from conftest import pgTestSettings


baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)


def resetSampleTables():
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_SAMPLE_TASK")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_SAMPLE_FORM_SUBMIT")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_SAMPLE_ADMIN_USER")
    executePg(pgTestSettings, "DROP TABLE IF EXISTS T_SAMPLE_CONFIG")


def testSampleOverviewAndDashboardArePublic():
    from server import app

    resetSampleTables()
    with TestClient(app) as client:
        overviewResponse = client.get("/api/v1/sample/overview")
        assert overviewResponse.status_code == 200
        overviewResult = overviewResponse.json()["result"]
        assert overviewResult["taskCount"] >= 1
        assert overviewResult["adminUserCount"] >= 1
        assert overviewResult["formSubmissionCount"] == 0

        dashboardResponse = client.get("/api/v1/sample/dashboard")
        assert dashboardResponse.status_code == 200
        dashboardResult = dashboardResponse.json()["result"]
        assert isinstance(dashboardResult["statusSummaryList"], list)
        assert isinstance(dashboardResult["recentList"], list)
        assert len(dashboardResult["recentList"]) >= 1


def testSampleTaskCrudFlow():
    from server import app

    resetSampleTables()
    with TestClient(app) as client:
        listResponse = client.get("/api/v1/sample/tasks?page=1&size=20")
        assert listResponse.status_code == 200
        initialCount = listResponse.json()["count"]
        assert initialCount >= 1

        createResponse = client.post(
            "/api/v1/sample/tasks",
            json={
                "title": "공개 샘플 신규 업무",
                "description": "DB 연동 CRUD 검증",
                "owner": "테스트",
                "status": "running",
                "amount": 210000,
                "attachmentName": "sample.md",
            },
        )
        assert createResponse.status_code == 201
        createResult = createResponse.json()["result"]
        taskId = int(createResult["id"])

        detailResponse = client.get(f"/api/v1/sample/tasks/{taskId}")
        assert detailResponse.status_code == 200
        assert detailResponse.json()["result"]["title"] == "공개 샘플 신규 업무"

        updateResponse = client.put(
            f"/api/v1/sample/tasks/{taskId}",
            json={
                "status": "done",
                "amount": 333000,
                "owner": "수정자",
            },
        )
        assert updateResponse.status_code == 200
        updateResult = updateResponse.json()["result"]
        assert updateResult["status"] == "done"
        assert float(updateResult["amount"]) == 333000

        deleteResponse = client.delete(f"/api/v1/sample/tasks/{taskId}")
        assert deleteResponse.status_code == 200
        assert deleteResponse.json()["result"]["id"] == taskId

        missingResponse = client.get(f"/api/v1/sample/tasks/{taskId}")
        assert missingResponse.status_code == 404
        assert missingResponse.json()["code"] == "SAMPLE_404_NOT_FOUND"


def testSampleFormMetaAndSubmit():
    from server import app

    resetSampleTables()
    with TestClient(app) as client:
        metaResponse = client.get("/api/v1/sample/forms/meta")
        assert metaResponse.status_code == 200
        metaResult = metaResponse.json()["result"]
        assert metaResult["submissionCount"] == 0
        assert "web" in metaResult["categoryCodeList"]
        assert "login" in metaResult["featureCodeList"]

        submitResponse = client.post(
            "/api/v1/sample/forms",
            json={
                "name": "홍길동",
                "email": "hong@example.com",
                "phone": "010-1234-5678",
                "category": "web",
                "startDate": "2026-03-01",
                "endDate": "2026-03-10",
                "budgetRange": "300만 ~ 500만",
                "requirement": "대시보드 고도화",
                "selectedFeatures": ["login", "chart"],
                "referenceUrl": "https://example.com/spec",
                "attachmentName": "brief.pdf",
            },
        )
        assert submitResponse.status_code == 201
        submitResult = submitResponse.json()["result"]
        assert submitResult["name"] == "홍길동"
        assert submitResult["selectedFeatures"] == ["login", "chart"]

        metaReloadResponse = client.get("/api/v1/sample/forms/meta")
        assert metaReloadResponse.status_code == 200
        metaReloadResult = metaReloadResponse.json()["result"]
        assert metaReloadResult["submissionCount"] == 1
        assert metaReloadResult["latestSubmission"]["email"] == "hong@example.com"


def testSampleAdminUserAndSettingFlow():
    from server import app

    resetSampleTables()
    with TestClient(app) as client:
        userListResponse = client.get("/api/v1/sample/admin/users")
        assert userListResponse.status_code == 200
        userResult = userListResponse.json()["result"]
        userList = userResult["sampleAdminUserList"]
        assert len(userList) >= 3
        assert userResult["listMetaObj"]["page"] == 1
        assert userResult["listMetaObj"]["size"] == 50
        assert userResult["listMetaObj"]["totalCount"] >= len(userList)

        createUserResponse = client.post(
            "/api/v1/sample/admin/users",
            json={
                "name": "신규 운영자",
                "email": "new-admin@example.com",
                "role": "editor",
                "status": "active",
                "notifyEmail": True,
                "notifySms": False,
                "notifyPush": True,
            },
        )
        assert createUserResponse.status_code == 201
        createdUser = createUserResponse.json()["result"]
        userId = int(createdUser["id"])

        updateUserResponse = client.put(
            f"/api/v1/sample/admin/users/{userId}",
            json={
                "name": "수정 운영자",
                "role": "admin",
                "status": "inactive",
                "notifySms": True,
            },
        )
        assert updateUserResponse.status_code == 200
        updatedUser = updateUserResponse.json()["result"]
        assert updatedUser["name"] == "수정 운영자"
        assert updatedUser["role"] == "admin"
        assert updatedUser["notifySms"] is True

        settingsResponse = client.get("/api/v1/sample/admin/settings")
        assert settingsResponse.status_code == 200
        settingsResult = settingsResponse.json()["result"]
        assert settingsResult["systemSetting"]["siteName"] == "MyWebTemplate"
        assert settingsResult["rolePermissionMap"]["admin"]["manageUser"] is True

        saveSettingsResponse = client.put(
            "/api/v1/sample/admin/settings",
            json={
                "siteName": "MyWebTemplate Sample",
                "adminEmail": "sample-admin@example.com",
                "maintenanceMode": True,
                "sessionTimeout": 90,
                "maxUploadMb": 50,
            },
        )
        assert saveSettingsResponse.status_code == 200
        savedSetting = saveSettingsResponse.json()["result"]["systemSetting"]
        assert savedSetting["siteName"] == "MyWebTemplate Sample"
        assert savedSetting["maintenanceMode"] is True
