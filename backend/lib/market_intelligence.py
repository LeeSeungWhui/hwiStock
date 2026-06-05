"""
HWISTOCK-UNIT-003 foundation: deterministic source registry, fixture normalization,
and normalized event validation. Stdlib-only; no network or env secret reads.
"""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

KST = timezone(timedelta(hours=9))

SOURCE_STATUS_APPROVED_FIRST_GO = "approved_first_go"
SOURCE_STATUS_CONDITIONAL_AFTER_KEY = "conditional_after_key"
SOURCE_STATUS_CONDITIONAL_AFTER_TERMS = "conditional_after_terms_check"
SOURCE_STATUS_DEFERRED = "deferred"
SOURCE_STATUS_FORBIDDEN_DEFAULT = "forbidden_default"

FOUNDATION_INGESTIBLE_STATUSES = frozenset({SOURCE_STATUS_APPROVED_FIRST_GO})

REQUIRED_EVENT_FIELDS = (
    "event_id",
    "source_id",
    "source_event_id",
    "symbol",
    "corp_code",
    "market",
    "title",
    "source_url",
    "published_at_kst",
    "collected_at_kst",
    "event_type",
    "dedupe_key",
    "body_storage_policy",
    "source_hash",
    "candidate_eligible",
)

_EVENT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
_KST_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+09:00$"
)


def _source_entry(
    source_id: str,
    source_status: str,
    *,
    collection_method: str,
    credential_policy: str,
    storage_policy: str,
    rate_limit_policy: str,
    terms_notes: str,
    retention_notes: str,
    body_storage_policy: str = "metadata_only",
    live_enabled: bool = False,
    venue: Optional[str] = None,
    interval: Optional[str] = None,
    ohlcv_schema: Optional[Dict[str, str]] = None,
    latency_budget_ms: Optional[int] = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "source_id": source_id,
        "source_status": source_status,
        "collection_method": collection_method,
        "credential_policy": credential_policy,
        "storage_policy": storage_policy,
        "rate_limit_policy": rate_limit_policy,
        "terms_notes": terms_notes,
        "retention_notes": retention_notes,
        "body_storage_policy": body_storage_policy,
        "live_enabled": live_enabled,
        "terms_checked_at": None,
        "last_success_at": None,
        "last_failure_at": None,
    }
    if venue is not None:
        entry["venue"] = venue
    if interval is not None:
        entry["interval"] = interval
    if ohlcv_schema is not None:
        entry["ohlcv_schema"] = ohlcv_schema
    if latency_budget_ms is not None:
        entry["latency_budget_ms"] = latency_budget_ms
    return entry


def _build_registry_sources() -> Dict[str, Dict[str, Any]]:
    ohlcv_fields = {
        "open": "number",
        "high": "number",
        "low": "number",
        "close": "number",
        "volume": "number",
        "timestamp_kst": "string",
    }
    return {
        "dart_openapi_disclosures": _source_entry(
            "dart_openapi_disclosures",
            SOURCE_STATUS_APPROVED_FIRST_GO,
            collection_method="official_api_fixture",
            credential_policy="DART_API_KEY deferred until live source approval",
            storage_policy="metadata, filing ids, timestamps, summaries",
            rate_limit_policy="official API limits with local conservative cap when live",
            terms_notes="OPENDART official API terms; foundation uses fixtures only",
            retention_notes="normalized events retained per paper gate policy",
            body_storage_policy="metadata_only",
            live_enabled=False,
        ),
        "krx_nxt_market_calendar_cache": _source_entry(
            "krx_nxt_market_calendar_cache",
            SOURCE_STATUS_APPROVED_FIRST_GO,
            collection_method="local_cached_calendar_fixture",
            credential_policy="none",
            storage_policy="trading-day/session metadata only",
            rate_limit_policy="local cache refresh only after explicit approval",
            terms_notes="generated from official KRX/NXT references; fixture-only in foundation",
            retention_notes="calendar metadata retained for scheduler decisions",
            body_storage_policy="metadata_only",
            live_enabled=False,
            venue="KRX+NXT",
            interval="session_calendar",
            ohlcv_schema=ohlcv_fields,
            latency_budget_ms=0,
        ),
        "naver_search_news_api": _source_entry(
            "naver_search_news_api",
            SOURCE_STATUS_CONDITIONAL_AFTER_KEY,
            collection_method="official_api",
            credential_policy="NAVER_CLIENT_ID and NAVER_CLIENT_SECRET required after approval",
            storage_policy="title, links, excerpt, timestamps, query metadata",
            rate_limit_policy="daily cap and query list required after approval",
            terms_notes="NAVER Developers Search API terms",
            retention_notes="metadata and permitted excerpts only",
            body_storage_policy="excerpt_allowed",
            live_enabled=False,
        ),
        "public_news_rss_search": _source_entry(
            "public_news_rss_search",
            SOURCE_STATUS_APPROVED_FIRST_GO,
            collection_method="public_rss",
            credential_policy="none",
            storage_policy="title, link, source, published timestamp, and RSS summary only",
            rate_limit_policy="local conservative polling; no article-body crawling",
            terms_notes="public RSS/search feed metadata only; no paywall/login/HTML article scraping",
            retention_notes="metadata and permitted RSS summaries only",
            body_storage_policy="excerpt_allowed",
            live_enabled=True,
        ),
        "kind_krx_disclosure_portal": _source_entry(
            "kind_krx_disclosure_portal",
            SOURCE_STATUS_CONDITIONAL_AFTER_TERMS,
            collection_method="official_web_portal",
            credential_policy="none until approved method recorded",
            storage_policy="metadata only until method approved",
            rate_limit_policy="no automated collection until terms/access recorded",
            terms_notes="KRX KIND portal terms/access check required",
            retention_notes="metadata only in foundation",
            body_storage_policy="metadata_only",
            live_enabled=False,
        ),
        "krx_data_marketplace_delayed": _source_entry(
            "krx_data_marketplace_delayed",
            SOURCE_STATUS_CONDITIONAL_AFTER_TERMS,
            collection_method="official_data_portal",
            credential_policy="none until approved",
            storage_policy="delayed OHLCV/metadata after terms confirmation",
            rate_limit_policy="deferred until access policy recorded",
            terms_notes="KRX Data Marketplace terms required",
            retention_notes="delayed context data only; no realtime trading feed",
            body_storage_policy="metadata_only",
            live_enabled=False,
            venue="KRX",
            interval="1d",
            ohlcv_schema=ohlcv_fields,
            latency_budget_ms=300000,
        ),
        "kis_market_or_realtime_data": _source_entry(
            "kis_market_or_realtime_data",
            SOURCE_STATUS_DEFERRED,
            collection_method="broker_api",
            credential_policy="not configured; deferred to UNIT-009 broker-network approval",
            storage_policy="none",
            rate_limit_policy="broker throttles deferred",
            terms_notes="KIS API verification documents endpoint families only",
            retention_notes="no collection in UNIT-003 foundation",
            body_storage_policy="metadata_only",
            live_enabled=False,
            venue="KRX",
            interval="realtime_deferred",
            ohlcv_schema=ohlcv_fields,
            latency_budget_ms=None,
        ),
        "general_media_html_scrape": _source_entry(
            "general_media_html_scrape",
            SOURCE_STATUS_FORBIDDEN_DEFAULT,
            collection_method="html_scraping",
            credential_policy="none",
            storage_policy="none",
            rate_limit_policy="blocked",
            terms_notes="copyright/terms/anti-bot risk; forbidden by default",
            retention_notes="none",
            body_storage_policy="metadata_only",
            live_enabled=False,
        ),
        "unofficial_finance_apis": _source_entry(
            "unofficial_finance_apis",
            SOURCE_STATUS_FORBIDDEN_DEFAULT,
            collection_method="unofficial_api_scraping",
            credential_policy="none",
            storage_policy="none",
            rate_limit_policy="blocked",
            terms_notes="unofficial APIs blocked unless later explicit review",
            retention_notes="none",
            body_storage_policy="metadata_only",
            live_enabled=False,
        ),
    }


def loadSourceRegistryConfig() -> Dict[str, Any]:
    sources = _build_registry_sources()
    approved_first_go = sorted(
        sid
        for sid, cfg in sources.items()
        if cfg["source_status"] == SOURCE_STATUS_APPROVED_FIRST_GO
    )
    return {
        "registry_id": "HWISTOCK-SOURCE-REGISTRY",
        "foundation_mode": True,
        "ingestible_statuses": sorted(FOUNDATION_INGESTIBLE_STATUSES),
        "approved_first_go_source_ids": approved_first_go,
        "disabled_live_source_ids": sorted(sources.keys()),
        "sources": sources,
        "market_data_context": {
            "chart_signals_enabled": False,
            "live_chart_sources_enabled": False,
            "declared_venues": ["KRX", "KRX+NXT"],
            "declared_intervals": ["session_calendar", "1d", "realtime_deferred"],
            "ohlcv_schema": {
                "open": "number",
                "high": "number",
                "low": "number",
                "close": "number",
                "volume": "number",
                "timestamp_kst": "string",
            },
            "latency_budget_ms_by_source": {
                "krx_nxt_market_calendar_cache": 0,
                "krx_data_marketplace_delayed": 300000,
                "kis_market_or_realtime_data": None,
            },
        },
        "dedupe_policy": {
            "disclosure": "source_id + rcept_no",
            "news": "canonical_url + title_hash",
            "market_data": "source_id + symbol + venue + interval + timestamp",
            "duplicate_handling": "link_not_discard",
        },
        "retention_default": "one_week_paper_gate_minimum",
    }


def canIngestSourceInFoundation(source_id: str, registry: Optional[Mapping[str, Any]] = None) -> bool:
    reg = registry if registry is not None else loadSourceRegistryConfig()
    source = reg["sources"].get(source_id)
    if source is None:
        return False
    return source["source_status"] in FOUNDATION_INGESTIBLE_STATUSES


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def _title_hash(title: str) -> str:
    normalized = re.sub(r"\s+", " ", title.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def buildDedupeKey(row: Mapping[str, Any], source_cfg: Mapping[str, Any]) -> str:
    source_id = str(row.get("source_id") or source_cfg["source_id"])
    event_type = str(row.get("event_type") or "disclosure_event")
    if event_type == "disclosure_event":
        rcept_no = row.get("rcept_no") or row.get("source_event_id") or ""
        return f"{source_id}:{rcept_no}"
    if event_type == "news_event":
        link = _normalize_url(
            str(row.get("original_link") or row.get("source_url") or row.get("canonical_url") or "")
        )
        title = str(row.get("title") or "")
        return f"{source_id}:{link}:{_title_hash(title)}"
    venue = str(row.get("venue") or source_cfg.get("venue") or "")
    interval = str(row.get("interval") or source_cfg.get("interval") or "")
    symbol = str(row.get("symbol") or "")
    ts = str(row.get("published_at_kst") or row.get("collected_at_kst") or "")
    return f"{source_id}:{symbol}:{venue}:{interval}:{ts}"


def _source_hash(row: Mapping[str, Any], dedupe_key: str) -> str:
    payload = "|".join(
        [
            str(row.get("source_id") or ""),
            str(row.get("source_event_id") or ""),
            str(row.get("title") or ""),
            dedupe_key,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _make_event_id(source_id: str, source_event_id: str) -> str:
    digest = hashlib.sha256(f"{source_id}:{source_event_id}".encode("utf-8")).hexdigest()[:24]
    return f"evt.{source_id}.{digest}"


def normalizeFixtureRow(
    row: Mapping[str, Any],
    *,
    registry: Optional[Mapping[str, Any]] = None,
    collected_at_kst: Optional[str] = None,
) -> Dict[str, Any]:
    reg = registry if registry is not None else loadSourceRegistryConfig()
    source_id = str(row["source_id"])
    source_cfg = reg["sources"][source_id]
    source_event_id = str(row.get("source_event_id") or row.get("rcept_no") or "")
    if not source_event_id:
        raise ValueError("fixture row requires source_event_id or rcept_no")

    dedupe_key = str(row.get("dedupe_key") or buildDedupeKey(row, source_cfg))
    published = str(row.get("published_at_kst") or row.get("collected_at_kst") or "")
    collected = str(collected_at_kst or row.get("collected_at_kst") or published)
    body_storage_policy = str(source_cfg.get("body_storage_policy") or "metadata_only")
    supplied_body_storage_policy = row.get("body_storage_policy")
    if supplied_body_storage_policy is not None and str(supplied_body_storage_policy) != body_storage_policy:
        raise ValueError("body_storage_policy must match source registry policy")
    event = {
        "event_id": str(row.get("event_id") or _make_event_id(source_id, source_event_id)),
        "source_id": source_id,
        "source_event_id": source_event_id,
        "symbol": str(row.get("symbol") or ""),
        "corp_code": row.get("corp_code"),
        "market": str(row.get("market") or "KRX"),
        "title": str(row.get("title") or ""),
        "source_url": str(row.get("source_url") or ""),
        "published_at_kst": published,
        "collected_at_kst": collected,
        "event_type": str(row.get("event_type") or "disclosure_event"),
        "dedupe_key": dedupe_key,
        "body_storage_policy": body_storage_policy,
        "source_hash": str(row.get("source_hash") or _source_hash(row, dedupe_key)),
        "candidate_eligible": bool(row.get("candidate_eligible", True)),
        "duplicate_of_event_id": None,
        "linked_duplicate_event_ids": [],
        "ingestion_mode": "foundation_fixture",
    }
    validateNormalizedEvent(event, registry=reg)
    return event


def validateNormalizedEvent(
    event: Mapping[str, Any],
    *,
    registry: Optional[Mapping[str, Any]] = None,
) -> None:
    reg = registry if registry is not None else loadSourceRegistryConfig()
    missing = [field for field in REQUIRED_EVENT_FIELDS if field not in event]
    if missing:
        raise ValueError(f"normalized event missing fields: {', '.join(missing)}")

    if not _EVENT_ID_PATTERN.match(str(event["event_id"])):
        raise ValueError("event_id must be a stable lowercase identifier")

    source_id = str(event["source_id"])
    if source_id not in reg["sources"]:
        raise ValueError(f"unknown source_id: {source_id}")

    for ts_field in ("published_at_kst", "collected_at_kst"):
        ts_value = str(event[ts_field])
        if not ts_value or not _KST_TIMESTAMP_PATTERN.match(ts_value):
            raise ValueError(f"{ts_field} must be an ISO-8601 KST timestamp string ending with +09:00")

    if str(event["dedupe_key"]).strip() == "":
        raise ValueError("dedupe_key must be non-empty")

    if str(event["source_hash"]).strip() == "":
        raise ValueError("source_hash must be non-empty")

    if not isinstance(event["candidate_eligible"], bool):
        raise ValueError("candidate_eligible must be boolean")


def linkDuplicateEvents(events: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    linked: List[Dict[str, Any]] = []
    primary_by_dedupe: Dict[str, str] = {}
    for raw in events:
        event = deepcopy(dict(raw))
        dedupe_key = str(event["dedupe_key"])
        primary_id = primary_by_dedupe.get(dedupe_key)
        if primary_id is None:
            primary_by_dedupe[dedupe_key] = str(event["event_id"])
            event["duplicate_of_event_id"] = None
            event["linked_duplicate_event_ids"] = list(event.get("linked_duplicate_event_ids") or [])
            linked.append(event)
            continue
        event["duplicate_of_event_id"] = primary_id
        event["linked_duplicate_event_ids"] = []
        event["candidate_eligible"] = False
        for prior in linked:
            if str(prior["event_id"]) == primary_id:
                prior.setdefault("linked_duplicate_event_ids", [])
                if str(event["event_id"]) not in prior["linked_duplicate_event_ids"]:
                    prior["linked_duplicate_event_ids"].append(str(event["event_id"]))
                break
        linked.append(event)
    return linked


def classifyBlockedSource(source_id: str, registry: Optional[Mapping[str, Any]] = None) -> str:
    reg = registry if registry is not None else loadSourceRegistryConfig()
    source = reg["sources"].get(source_id)
    if source is None:
        return "unknown_source"
    status = source["source_status"]
    if status in FOUNDATION_INGESTIBLE_STATUSES:
        return "allowed"
    if status == SOURCE_STATUS_FORBIDDEN_DEFAULT:
        return "forbidden"
    if status == SOURCE_STATUS_DEFERRED:
        return "deferred"
    return "blocked_conditional"
