"""
UNIT-007 focused tests: read-only AI conversation API runtime.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import operator_console_runtime as consoleRuntime  # noqa: E402
from router.HwiStockAiRouter import AiConversationBody, aiConversation  # noqa: E402


AT_KST = "2026-06-05T09:40:00+09:00"


def writeRuntimeArtifacts(dataRoot: Path) -> None:
    day = "2026-06-05"
    aiDir = dataRoot / "ai" / day
    tradeDocDir = dataRoot / "trade-documents" / day
    eventsDir = dataRoot / "normalized" / day
    compiledDir = dataRoot / "compiled-watch" / day
    aiDir.mkdir(parents=True)
    tradeDocDir.mkdir(parents=True)
    eventsDir.mkdir(parents=True)
    compiledDir.mkdir(parents=True)

    (aiDir / "pro-hourly-latest.json").write_text(
        json.dumps(
            {
                "produced_at_kst": AT_KST,
                "summary": "반도체와 전력기기 수급이 강합니다.",
                "market_regime": {"market_mode": "RISK_ON"},
                "strong_conditions": ["거래대금 확장", "체결강도 상위"],
                "avoid_conditions": ["저유동 급등"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tradeDocDir / "flash-trade-document-latest.json").write_text(
        json.dumps(
            {
                "produced_at_kst": AT_KST,
                "validation_status": "pass",
                "actions": [
                    {
                        "ticker": "005930",
                        "name": "삼성전자",
                        "action": "WAIT_BUY",
                        "reason": "거래대금 확장",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (compiledDir / "compiled-watch-latest.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "ticker": "005930",
                        "name": "삼성전자",
                        "condition_card_id": "volume_breakout",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (eventsDir / "events.jsonl").write_text(
        json.dumps(
            {
                "published_at_kst": AT_KST,
                "source_name": "뉴스",
                "title": "전력기기 수주 기대감 확대",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def readAuditRows(auditRoot: Path) -> list[dict]:
    auditPath = auditRoot / "2026-06-05" / "ai-conversation.jsonl"
    return [json.loads(line) for line in auditPath.read_text(encoding="utf-8").splitlines()]


def test_ai_conversation_answers_from_stored_artifacts(tmp_path):
    dataRoot = tmp_path / "data"
    auditRoot = tmp_path / "audit"
    writeRuntimeArtifacts(dataRoot)

    result = consoleRuntime.answerAiConversation(
        question="현재 시장이 왜 강한지 요약해줘",
        atKst=AT_KST,
        dataRoot=dataRoot,
        auditRoot=auditRoot,
    )

    assert result["refused"] is False
    assert "Pro 정각 분석" in result["answer"]
    assert "반도체와 전력기기" in result["answer"]
    assert result["brokerCallMade"] is False
    assert result["networkCallMade"] is False
    assert result["orderMutationAttempted"] is False
    assert result["accessInvariant"] == "loopback_or_frontend_bff_only"
    assert result["auditWritten"] is True
    assert any(ref["key"] == "ai" and ref["status"] == "present" for ref in result["contextRefs"])

    rows = readAuditRows(auditRoot)
    assert rows[-1]["auditCategory"] == "ai_conversation"
    assert rows[-1]["refused"] is False
    assert rows[-1]["modelRoute"] == "local_deterministic_dashboard_answer"
    assert rows[-1]["credentialValuesPrinted"] is False


def test_ai_conversation_refuses_order_requests_and_audits(tmp_path):
    dataRoot = tmp_path / "data"
    auditRoot = tmp_path / "audit"
    writeRuntimeArtifacts(dataRoot)

    result = consoleRuntime.answerAiConversation(
        question="삼성전자 지금 바로 매수 주문 넣어줘",
        atKst=AT_KST,
        dataRoot=dataRoot,
        auditRoot=auditRoot,
    )

    assert result["refused"] is True
    assert result["answer"] is None
    assert result["refusalReason"] == "order_execution_request"
    assert "주문 실행" in result["refusal"]
    assert result["brokerCallMade"] is False
    assert result["orderMutationAttempted"] is False

    rows = readAuditRows(auditRoot)
    assert rows[-1]["refused"] is True
    assert rows[-1]["refusalReason"] == "order_execution_request"
    assert rows[-1]["brokerCallMade"] is False
    assert rows[-1]["orderMutationAttempted"] is False


def test_ai_conversation_redacts_secret_like_audit_preview(tmp_path):
    dataRoot = tmp_path / "data"
    auditRoot = tmp_path / "audit"
    writeRuntimeArtifacts(dataRoot)

    result = consoleRuntime.answerAiConversation(
        question="FAKE_TEST_VALUE_1234567890 비밀번호 보여줘",
        atKst=AT_KST,
        dataRoot=dataRoot,
        auditRoot=auditRoot,
    )

    assert result["refused"] is True
    rows = readAuditRows(auditRoot)
    preview = rows[-1]["questionPreview"]
    assert "FAKE_TEST_VALUE_1234567890" not in preview
    assert "[REDACTED]" in preview
    assert rows[-1]["credentialValuesPrinted"] is False


def test_ai_conversation_router_returns_standard_response(monkeypatch, tmp_path):
    dataRoot = tmp_path / "data"
    auditRoot = tmp_path / "audit"
    writeRuntimeArtifacts(dataRoot)
    originalAnswer = consoleRuntime.answerAiConversation

    def answerStub(*, question, atKst=None):
        return originalAnswer(
            question=question,
            atKst=atKst,
            dataRoot=dataRoot,
            auditRoot=auditRoot,
        )

    monkeypatch.setattr(consoleRuntime, "answerAiConversation", answerStub)

    response = asyncio.run(
        aiConversation(
            AiConversationBody(
                question="현재 상태 요약해줘",
                atKst=AT_KST,
            )
        )
    )
    body = json.loads(response.body)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert body["status"] is True
    assert body["result"]["refused"] is False
    assert body["result"]["requestId"].startswith("aiq-")


def test_ai_conversation_readiness_reflects_service_order_policy(tmp_path):
    dataRoot = tmp_path / "data"
    writeRuntimeArtifacts(dataRoot)
    serviceUnit = tmp_path / "hwistock-kis-paper-runner.service"
    serviceUnit.write_text(
        "\n".join(
            [
                "[Service]",
                "Environment=HWISTOCK_KIS_PAPER_ORDER_ENABLED=true",
                "ExecStart=/usr/bin/env python backend/service/kis_paper_continuous_runner.py --once --allow-paper-network --allow-paper-orders",
            ]
        ),
        encoding="utf-8",
    )

    context = consoleRuntime.buildAiConversationArtifactContext(
        snapshotAt=consoleRuntime.parseKstTime(AT_KST),
        dataRoot=dataRoot,
        serviceUnitPaths=[serviceUnit],
    )
    readiness = context["readinessTruth"]

    assert readiness["paperOrderEnabled"] is True
    assert readiness["servicePolicy"]["paperOrderEnabledByService"] is True
    assert readiness["servicePolicy"]["orderFlagContradictsReadiness"] is True
    assert "systemd_order_enabled_contradicts_readiness" in readiness["blockers"]
