"""
hwiStock AI conversation API.

The route is read-only: it answers from stored runtime artifacts and sanitized
state only. It must not call broker APIs, AI providers, or service controls.
Operational exposure invariant: loopback backend plus frontend BFF/auth boundary
only; LAN/public exposure requires a future approved access contract.
"""

from typing import Optional

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from lib import operator_console_runtime as operatorConsoleRuntime
from lib.Response import successResponse

router = APIRouter(prefix="/api/v1/hwistock/ai", tags=["hwistock-ai"])


class AiConversationBody(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    atKst: Optional[str] = None


def hwiStockJsonResponse(result, statusCode: int = 200) -> JSONResponse:
    return JSONResponse(
        content=successResponse(result=result),
        status_code=statusCode,
        headers={"Cache-Control": "no-store"},
    )


@router.post("/conversation")
async def aiConversation(body: AiConversationBody = Body(...)):
    result = operatorConsoleRuntime.answerAiConversation(
        question=body.question,
        atKst=body.atKst,
    )
    return hwiStockJsonResponse(result)
