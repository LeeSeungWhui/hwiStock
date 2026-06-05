"""
hwiStock runner read-only API (UNIT-002). No DB or external services.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from lib.Response import successResponse
from service import HwiStockRunnerService

router = APIRouter(prefix="/api/v1/hwistock/runner", tags=["hwistock-runner"])


class NoOrderIntentBody(BaseModel):
    symbol: Optional[str] = None
    side: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=0)
    venue: Optional[str] = None
    note: Optional[str] = None


def _json_ok(result: Any, status_code: int = 200) -> JSONResponse:
    resp = successResponse(result=result)
    r = JSONResponse(content=resp, status_code=status_code)
    r.headers["Cache-Control"] = "no-store"
    return r


@router.get("/status")
async def runner_status(atKst: Optional[str] = None):
    result = HwiStockRunnerService.get_runner_status(at_kst=atKst)
    return _json_ok(result)


@router.get("/kis-paper-continuous-status")
async def kis_paper_continuous_status(atKst: Optional[str] = None):
    from service import kis_paper_continuous_runner

    result = kis_paper_continuous_runner.evaluateContinuousPaperRunnerStatus(at_kst=atKst)
    return _json_ok(result)


@router.get("/route-preview")
async def route_preview(atKst: str):
    result = HwiStockRunnerService.preview_route(atKst)
    return _json_ok(result)


@router.get("/daily-close-template")
async def daily_close_template():
    result = HwiStockRunnerService.daily_close_template()
    return _json_ok(result)


@router.post("/no-order-intent-record")
async def no_order_intent_record(body: NoOrderIntentBody = Body(...)):
    result = HwiStockRunnerService.record_no_order_intent(body.model_dump())
    return _json_ok(result)
