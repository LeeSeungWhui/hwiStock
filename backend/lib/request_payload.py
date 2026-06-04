"""
파일명: backend/lib/request_payload.py
작성자: hwi (via Codex)
갱신일: 2026-06-04
설명: HWISTOCK-UNIT-008 FastAPI-profile request-payload helper names
       introduced before route implementation.  Each function returns an
       optional ``BaseModel`` subclass or ``None`` when the corresponding
       endpoint does not yet accept typed bodies.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Named payload helpers — stubs until route contracts are finalised
# ---------------------------------------------------------------------------

class _EmptyPayload(BaseModel):
    pass


def artifact_list_payload_model() -> type[BaseModel]:
    """Return the expected request-body model for artifact list endpoints."""
    return _EmptyPayload


def artifact_detail_payload_model() -> type[BaseModel]:
    """Return the expected request-body model for single-artifact lookups."""
    return _EmptyPayload


def paper_day_manifest_payload_model() -> type[BaseModel]:
    """Return the expected request-body model for paper-day evidence queries."""
    return _EmptyPayload


def pnl_query_payload_model() -> type[BaseModel]:
    """Return the expected request-body model for daily PnL queries."""
    return _EmptyPayload


def report_payload_model() -> type[BaseModel]:
    """Return the expected request-body model for report endpoints."""
    return _EmptyPayload
