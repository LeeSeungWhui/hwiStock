"""
hwiStock runner read-only API (UNIT-002). No DB or external services.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from lib import operator_console_runtime as operatorConsoleRuntime
from lib.Response import successResponse
from service import HwiStockRunnerService

router = APIRouter(prefix="/api/v1/hwistock/runner", tags=["hwistock-runner"])


class NoOrderIntentBody(BaseModel):
    symbol: Optional[str] = None
    side: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=0)
    venue: Optional[str] = None
    note: Optional[str] = None


class ObservationReportBody(BaseModel):
    startedAtKst: str
    endedAtKst: Optional[str] = None
    operatorNote: Optional[str] = None


def hwiStockJsonResponse(result: Any, statusCode: int = 200) -> JSONResponse:
    return JSONResponse(
        content=successResponse(result=result),
        status_code=statusCode,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/status")
async def runnerStatus(atKst: Optional[str] = None):
    result = HwiStockRunnerService.get_runner_status(at_kst=atKst)
    return hwiStockJsonResponse(result)


@router.get("/kis-paper-continuous-status")
async def kisPaperContinuousStatus(atKst: Optional[str] = None):
    from service import kis_paper_continuous_runner

    result = kis_paper_continuous_runner.evaluateContinuousPaperRunnerStatus(at_kst=atKst)
    return hwiStockJsonResponse(result)


@router.get("/operator-snapshot")
async def operatorSnapshot(atKst: Optional[str] = None):
    result = operatorConsoleRuntime.buildOperatorConsoleSnapshot(atKst=atKst)
    return hwiStockJsonResponse(result)


@router.get("/operatorSnapshot")
async def operatorSnapshotCamel(atKst: Optional[str] = None):
    return await operatorSnapshot(atKst=atKst)


@router.get("/route-preview")
async def routePreview(atKst: str):
    result = HwiStockRunnerService.preview_route(atKst)
    return hwiStockJsonResponse(result)


@router.get("/daily-close-template")
async def dailyCloseTemplate():
    result = HwiStockRunnerService.daily_close_template()
    return hwiStockJsonResponse(result)


@router.post("/observation-report")
async def observationReport(body: ObservationReportBody = Body(...)):
    result = operatorConsoleRuntime.writeObservationReport(
        startedAtKst=body.startedAtKst,
        endedAtKst=body.endedAtKst,
        operatorNote=body.operatorNote,
    )
    return hwiStockJsonResponse(result, statusCode=201)


@router.post("/no-order-intent-record")
async def noOrderIntentRecord(body: NoOrderIntentBody = Body(...)):
    result = HwiStockRunnerService.record_no_order_intent(body.model_dump())
    return hwiStockJsonResponse(result)
