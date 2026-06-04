"""
파일명: backend/lib/storage_schemas.py
작성자: hwi (via Codex)
갱신일: 2026-06-04
설명: HWISTOCK-UNIT-008 typed artifact contracts, SHA-256 content hashing,
       KST date-scoped artifact path builder, redaction/sensitive-key validation,
       DailyPnL system-calculation enforcement, and paper-day evidence linkage.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, field_validator, model_validator

KST = timezone(offset=timedelta(hours=9))

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Environment(str, Enum):
    docs_only = "docs_only"
    backtest = "backtest"
    paper = "paper"
    sandbox = "sandbox"
    live_readonly = "live_readonly"
    live_order = "live_order"


class BodyStoragePolicy(str, Enum):
    metadata_only = "metadata_only"
    excerpt_allowed = "excerpt_allowed"
    summary_only = "summary_only"
    full_body_allowed = "full_body_allowed"


class RedactionStatus(str, Enum):
    none = "none"
    partial = "partial"
    full = "full"


class BrokerAdapter(str, Enum):
    no_order_dry_run = "no_order_dry_run"
    kis_paper = "kis_paper"
    kis_live_readonly = "kis_live_readonly"
    kis_live_order = "kis_live_order"


class CalculationSource(str, Enum):
    system = "system"


class ArtifactType(str, Enum):
    source = "source"
    normalized_event = "normalized_event"
    ai_analysis = "ai_analysis"
    candidate_card = "candidate_card"
    order_event = "order_event"
    fill_event = "fill_event"
    position_snapshot = "position_snapshot"
    daily_pnl = "daily_pnl"
    morning_report = "morning_report"
    daily_close_report = "daily_close_report"
    evidence_manifest = "evidence_manifest"


class ArtifactPathClass(str, Enum):
    source_news = "source_news"
    source_disclosures = "source_disclosures"
    source_market_data = "source_market_data"
    normalized = "normalized"
    ai_hourly = "ai_hourly"
    ai_market_regime = "ai_market_regime"
    ai_intraday = "ai_intraday"
    candidate = "candidate"
    order = "order"
    fill = "fill"
    position = "position"
    pnl = "pnl"
    morning_report = "morning_report"
    daily_close_report = "daily_close_report"
    evidence = "evidence"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(api[_\s]?key|apikey|secret|token|password|passwd"
    r"|credential|private[_\s]?key|access[_\s]?key"
    r"|account[_\s]?(no|number|id)|acct[_\s]?(no|number|id)"
    r"|appkey|appsecret|cert[_\s]?(key|password)|private[-_\s]?id"
    r"|canonical[_\s]?account)",
)


def _now_kst_iso() -> str:
    return datetime.now(tz=KST).isoformat()


def _today_kst() -> date:
    return datetime.now(tz=KST).date()


def compute_sha256_hex(content: Union[str, bytes, Dict[str, Any], List[Any]]) -> str:
    """Deterministic SHA-256 content hash.

    Strings and bytes are hashed directly.  dict/list values are serialised
    with ``sort_keys=True`` before hashing.
    """
    if isinstance(content, str):
        raw = content.encode("utf-8")
    elif isinstance(content, bytes):
        raw = content
    else:
        raw = json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Date-scoped artifact path builder
# ---------------------------------------------------------------------------

_ARTIFACT_PATH_TEMPLATES: Dict[str, str] = {
    "source_news": "data/raw/{date}/news",
    "source_disclosures": "data/raw/{date}/disclosures",
    "source_market_data": "data/raw/{date}/market-data",
    "normalized": "data/normalized/{date}",
    "ai_hourly": "data/ai/{date}/deepseek-pro/hourly",
    "ai_market_regime": "data/ai/{date}/deepseek-pro/market-regime",
    "ai_intraday": "data/ai/{date}/deepseek-flash/intraday",
    "candidate": "data/candidates/{date}",
    "order": "data/trading/{date}",
    "fill": "data/trading/{date}",
    "position": "data/trading/{date}",
    "pnl": "data/trading/{date}",
    "morning_report": "data/reports/{date}",
    "daily_close_report": "data/reports/{date}",
    "evidence": "data/evidence/{date}",
}

_DEFAULT_ARTIFACT_FILENAMES: Dict[str, str] = {
    "normalized": "events.jsonl",
    "order": "orders.jsonl",
    "fill": "fills.jsonl",
    "position": "positions.jsonl",
    "pnl": "pnl.json",
    "morning_report": "morning-0700.json",
    "daily_close_report": "daily-close-2000.json",
    "evidence": "paper-day.json",
}


def build_artifact_path(
    *,
    category: Union[str, ArtifactPathClass],
    trading_date: date,
    sub_path: str = "",
) -> str:
    """Build a date-scoped artifact path.

    ``category`` must be one of the recognised keys (e.g. ``"candidate"``,
    ``"evidence"``).  ``trading_date`` is the KST trading date.
    ``sub_path``, when provided, is appended after the category/date folder.
    """
    category_name = category.value if isinstance(category, ArtifactPathClass) else category
    root = _ARTIFACT_PATH_TEMPLATES.get(category_name, "data/{date}")
    date_str = trading_date.isoformat()
    path = root.format(date=date_str)
    file_or_sub_path = sub_path or _DEFAULT_ARTIFACT_FILENAMES.get(category_name, "")
    if not file_or_sub_path:
        return path

    clean_sub_path = file_or_sub_path.strip("/")
    if any(part == ".." for part in clean_sub_path.split("/")):
        raise ValueError("sub_path must not contain path traversal segments")
    return f"{path}/{clean_sub_path}"


# ---------------------------------------------------------------------------
# Base model with shared artifact fields
# ---------------------------------------------------------------------------

class BaseArtifact(BaseModel):
    schema_version: str = Field(default="hwistock.artifact/v1")
    artifact_id: str
    artifact_type: ArtifactType
    created_at_kst: str = Field(default_factory=_now_kst_iso)
    trading_date: str = Field(default_factory=lambda: _today_kst().isoformat())
    environment: Environment = Environment.paper
    source_ids: List[str] = Field(default_factory=list)
    related_artifact_ids: List[str] = Field(default_factory=list)
    symbols: List[str] = Field(default_factory=list)
    redaction_status: RedactionStatus = RedactionStatus.none
    content_hash: Optional[str] = None
    supersedes_artifact_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Source / event models
# ---------------------------------------------------------------------------

class SourceArtifact(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.source
    source_type: str = ""
    source_name: str = ""
    source_url: str = ""
    collected_at_kst: str = Field(default_factory=_now_kst_iso)
    published_at_kst: Optional[str] = None

    body_storage_policy: BodyStoragePolicy = BodyStoragePolicy.metadata_only
    license_or_terms_note: str = ""

    title: Optional[str] = None
    excerpt: Optional[str] = None
    summary: Optional[str] = None
    body: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _enforce_body_storage_policy(self) -> "SourceArtifact":
        if self.body is not None and self.body_storage_policy != BodyStoragePolicy.full_body_allowed:
            raise ValueError(
                f"body field is only allowed when body_storage_policy is"
                f" 'full_body_allowed', got '{self.body_storage_policy.value}'"
            )
        return self


class NormalizedEvent(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.normalized_event
    event_kind: str = ""
    event_summary: str = ""
    event_payload: Dict[str, Any] = Field(default_factory=dict)
    source_artifact_ids: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# AI analysis artifacts
# ---------------------------------------------------------------------------

class AIAnalysisArtifact(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.ai_analysis
    model_id: str = ""
    model_provider: str = ""
    prompt_id: Optional[str] = None
    analysis_kind: str = ""
    confidence: Optional[float] = None
    input_source_ids: List[str] = Field(default_factory=list)
    output_candidate_ids: List[str] = Field(default_factory=list)
    output_payload: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Candidate card
# ---------------------------------------------------------------------------

class CandidateCard(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.candidate_card
    symbol: str = ""
    reason: str = ""
    status: str = "proposed"
    source_artifact_ids: List[str] = Field(default_factory=list)
    ai_output_ids: List[str] = Field(default_factory=list)
    entry_price_range: Optional[Dict[str, float]] = None
    target_price_range: Optional[Dict[str, float]] = None
    stop_loss_price: Optional[float] = None
    risk_label: Optional[str] = None
    decision_rationale: str = ""


# ---------------------------------------------------------------------------
# Order / fill / position models
# ---------------------------------------------------------------------------

class OrderEvent(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.order_event
    order_id: str = ""
    broker_adapter: BrokerAdapter = BrokerAdapter.no_order_dry_run
    symbol: str = ""
    order_side: str = ""
    order_type: str = ""
    quantity: int = 0
    price_krw: float = 0.0
    cash_amount_krw: float = 0.0
    fees_krw: float = 0.0
    taxes_krw: float = 0.0
    order_state: str = ""
    candidate_id: Optional[str] = None


class FillEvent(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.fill_event
    fill_id: str = ""
    order_id: str = ""
    broker_adapter: BrokerAdapter = BrokerAdapter.no_order_dry_run
    symbol: str = ""
    fill_side: str = ""
    quantity: int = 0
    price_krw: float = 0.0
    cash_amount_krw: float = 0.0
    fees_krw: float = 0.0
    taxes_krw: float = 0.0
    fill_timestamp_kst: Optional[str] = None


class PositionSnapshot(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.position_snapshot
    position_id: str = ""
    broker_adapter: BrokerAdapter = BrokerAdapter.no_order_dry_run
    symbol: str = ""
    quantity: int = 0
    avg_price_krw: float = 0.0
    current_price_krw: float = 0.0
    market_value_krw: float = 0.0
    unrealized_pnl_krw: float = 0.0
    snapshot_timestamp_kst: Optional[str] = None


# ---------------------------------------------------------------------------
# DailyPnL — system-calculated only
# ---------------------------------------------------------------------------

class DailyPnL(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.daily_pnl
    calculation_source: CalculationSource = CalculationSource.system
    gross_profit_krw: float = 0.0
    gross_loss_krw: float = 0.0
    gross_pnl_krw: float = 0.0
    fees_krw: float = 0.0
    taxes_krw: float = 0.0
    net_pnl_krw: float = 0.0
    cash_start_krw: float = 0.0
    cash_end_krw: float = 0.0
    open_position_value_krw: float = 0.0
    realized_trade_ids: List[str] = Field(default_factory=list)

    @field_validator("calculation_source")
    @classmethod
    def _must_be_system(cls, v: CalculationSource) -> CalculationSource:
        if v != CalculationSource.system:
            raise ValueError(
                f"calculation_source must be 'system', got '{v.value}'"
            )
        return v


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class MorningReport(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.morning_report
    report_time_kst: str = ""
    overnight_summary: str = ""
    ai_analysis_ids: List[str] = Field(default_factory=list)
    market_regime_id: Optional[str] = None
    candidate_ids: List[str] = Field(default_factory=list)
    key_headlines: List[str] = Field(default_factory=list)
    risk_notes: str = ""


class DailyCloseReport(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.daily_close_report
    report_time_kst: str = ""
    daily_summary: str = ""
    pnl_artifact_id: str = ""
    order_event_ids: List[str] = Field(default_factory=list)
    fill_event_ids: List[str] = Field(default_factory=list)
    position_snapshot_ids: List[str] = Field(default_factory=list)
    candidate_outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    ai_interpretation_ids: List[str] = Field(default_factory=list)
    morning_report_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Paper-day evidence manifest
# ---------------------------------------------------------------------------

class PaperDayEvidenceManifest(BaseArtifact):
    artifact_type: ArtifactType = ArtifactType.evidence_manifest
    paper_day_date: str = ""
    source_artifact_ids: List[str] = Field(default_factory=list)
    normalized_event_ids: List[str] = Field(default_factory=list)
    ai_analysis_ids: List[str] = Field(default_factory=list)
    candidate_card_ids: List[str] = Field(default_factory=list)
    order_event_ids: List[str] = Field(default_factory=list)
    fill_event_ids: List[str] = Field(default_factory=list)
    position_snapshot_ids: List[str] = Field(default_factory=list)
    pnl_artifact_id: Optional[str] = None
    morning_report_id: Optional[str] = None
    daily_close_report_id: Optional[str] = None
    notes: str = ""

    @model_validator(mode="after")
    def _require_linkability(self) -> "PaperDayEvidenceManifest":
        missing: List[str] = []
        if not self.source_artifact_ids:
            missing.append("source_artifact_ids")
        if not self.normalized_event_ids:
            missing.append("normalized_event_ids")
        if not self.ai_analysis_ids:
            missing.append("ai_analysis_ids")
        if not self.candidate_card_ids:
            missing.append("candidate_card_ids")
        if not self.order_event_ids:
            missing.append("order_event_ids")
        if not self.fill_event_ids:
            missing.append("fill_event_ids")
        if not self.position_snapshot_ids:
            missing.append("position_snapshot_ids")
        if not self.pnl_artifact_id:
            missing.append("pnl_artifact_id")
        if not self.morning_report_id:
            missing.append("morning_report_id")
        if not self.daily_close_report_id:
            missing.append("daily_close_report_id")
        if missing:
            raise ValueError(
                f"PaperDayEvidenceManifest is missing required linkage fields: "
                + ", ".join(missing)
            )
        return self


# ---------------------------------------------------------------------------
# Sensitive-key validation
# ---------------------------------------------------------------------------

SENSITIVE_KEY_NAMES: Set[str] = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "passwd",
    "credential",
    "private_key",
    "access_key",
    "account_no",
    "account_number",
    "account_id",
    "acct_no",
    "acct_number",
    "acct_id",
    "appkey",
    "appsecret",
    "cert_key",
    "cert_password",
    "private_id",
    "private-id",
    "canonical_account",
}


def _collect_dict_keys(d: Dict[str, Any], prefix: str = "") -> List[str]:
    keys: List[str] = []
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        keys.append(full)
        if isinstance(v, dict):
            keys.extend(_collect_dict_keys(v, full))
    return keys


def validate_no_sensitive_keys(payload: Dict[str, Any], *, location: str = "") -> List[str]:
    """Return a list of sensitive key paths found in *payload*.

    An empty list means no sensitive keys were detected.  The check is
    case-insensitive and covers known credential / account / secret field-name
    patterns.  It does not inspect values — only field names.
    """
    all_keys = _collect_dict_keys(payload)
    violations: List[str] = []
    for key_path in all_keys:
        leaf = key_path.rsplit(".", 1)[-1] if "." in key_path else key_path
        if leaf.lower() in SENSITIVE_KEY_NAMES:
            violations.append(key_path)
        elif SENSITIVE_KEY_PATTERN.search(leaf):
            violations.append(key_path)
    if violations:
        violations.sort()
    return violations


def validate_payload_no_sensitive_keys(
    payload: Dict[str, Any], *, location: str = ""
) -> None:
    """Raise ``ValueError`` when *payload* contains sensitive keys."""
    violations = validate_no_sensitive_keys(payload, location=location)
    if violations:
        raise ValueError(
            f"Sensitive key names detected in payload: {', '.join(violations)}"
        )
