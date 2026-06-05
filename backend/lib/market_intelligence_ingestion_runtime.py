"""
HWISTOCK-UNIT-003 market intelligence ingestion runtime implementation.

This module keeps the original in-memory fixture ingestion contract, and also
provides a bounded live collector entrypoint for approved public information
sources. The live collector never imports broker/order routing and never writes
secrets; when source API keys are missing it still emits fail-closed health
evidence so a 24-hour scheduler can prove it is alive.
"""

from __future__ import annotations

import argparse
import email.utils
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from lib.market_intelligence import (
    classifyBlockedSource,
    canIngestSourceInFoundation,
    linkDuplicateEvents,
    loadSourceRegistryConfig,
    normalizeFixtureRow,
)

KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data"
OPENDART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"
NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
DEFAULT_NAVER_QUERIES = ("국장", "코스피", "삼성전자")
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def makeRunCollectedAtKst() -> str:
    return datetime.now(tz=KST).replace(microsecond=0).isoformat()


def _kst_date(value: Optional[datetime] = None) -> date:
    return (value or datetime.now(tz=KST)).astimezone(KST).date()


def _compact_kst_stamp(value: Optional[datetime] = None) -> str:
    return (value or datetime.now(tz=KST)).astimezone(KST).strftime("%H%M%S")


def _iso_kst_from_yyyymmdd(value: str) -> str:
    raw = str(value or "").strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}T00:00:00+09:00"
    return makeRunCollectedAtKst()


def _iso_kst_from_rfc2822(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return makeRunCollectedAtKst()
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return makeRunCollectedAtKst()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(KST).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl_unique(path: Path, rows: Sequence[Mapping[str, Any]], *, id_field: str = "event_id") -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                continue
            value = existing.get(id_field) if isinstance(existing, dict) else None
            if value:
                seen.add(str(value))
    appended = 0
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            value = str(row.get(id_field) or "")
            if value and value in seen:
                continue
            if value:
                seen.add(value)
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            appended += 1
    return appended


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _safe_urlopen_json(
    url: str,
    *,
    headers: Optional[Mapping[str, str]] = None,
    timeout: int = 15,
) -> Dict[str, Any]:
    request = urllib.request.Request(url, headers=dict(headers or {}), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    try:
        parsed = json.loads(raw.decode("utf-8", errors="replace")) if raw else {}
    except json.JSONDecodeError:
        parsed = {"parse_error": True}
    parsed["_http_status"] = status
    return parsed


def _safe_urlopen_text(
    url: str,
    *,
    headers: Optional[Mapping[str, str]] = None,
    timeout: int = 15,
) -> Dict[str, Any]:
    request_headers = {
        "User-Agent": "hwiStock-market-intel/0.1 (+metadata-only RSS collector)",
    }
    request_headers.update(dict(headers or {}))
    request = urllib.request.Request(url, headers=request_headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    return {
        "_http_status": status,
        "text": raw.decode("utf-8", errors="replace"),
    }


def _sanitize_opendart_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "status": payload.get("status"),
        "message": payload.get("message"),
        "http_status": payload.get("_http_status"),
        "list_count": len(payload.get("list") or []),
        "rows": [
            {
                "corp_code": row.get("corp_code"),
                "stock_code": row.get("stock_code"),
                "corp_name": row.get("corp_name"),
                "report_nm": row.get("report_nm"),
                "rcept_no": row.get("rcept_no"),
                "flr_nm": row.get("flr_nm"),
                "rcept_dt": row.get("rcept_dt"),
                "rm": row.get("rm"),
            }
            for row in list(payload.get("list") or [])[:50]
            if isinstance(row, Mapping)
        ],
    }


def _sanitize_naver_payload(payload: Mapping[str, Any], *, query: str) -> Dict[str, Any]:
    return {
        "query": query,
        "http_status": payload.get("_http_status"),
        "total": payload.get("total"),
        "start": payload.get("start"),
        "display": payload.get("display"),
        "item_count": len(payload.get("items") or []),
        "items": [
            {
                "title": item.get("title"),
                "originallink": item.get("originallink"),
                "link": item.get("link"),
                "description": item.get("description"),
                "pubDate": item.get("pubDate"),
            }
            for item in list(payload.get("items") or [])[:50]
            if isinstance(item, Mapping)
        ],
    }


def _strip_markup(value: str) -> str:
    text = html.unescape(str(value or ""))
    # RSS summaries can contain tiny tags. Store text-only snippets, not article bodies.
    return " ".join(text.replace("<b>", "").replace("</b>", "").replace("&nbsp;", " ").split())


def _parse_rss_items(text: str) -> List[Dict[str, str]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    items: List[Dict[str, str]] = []
    for item in root.findall(".//item"):
        def child_text(name: str) -> str:
            child = item.find(name)
            return child.text if child is not None and child.text is not None else ""

        source = item.find("source")
        items.append(
            {
                "title": _strip_markup(child_text("title")),
                "link": child_text("link").strip(),
                "guid": child_text("guid").strip(),
                "pubDate": child_text("pubDate").strip(),
                "description": _strip_markup(child_text("description"))[:500],
                "source": source.text.strip() if source is not None and source.text else "",
            }
        )
    return [item for item in items if item["title"] and item["link"]]


def _sanitize_rss_payload(payload: Mapping[str, Any], *, query: str) -> Dict[str, Any]:
    items = _parse_rss_items(str(payload.get("text") or ""))
    return {
        "query": query,
        "http_status": payload.get("_http_status"),
        "item_count": len(items),
        "items": items[:50],
    }


def _opendart_rows(payload: Mapping[str, Any], collected_at_kst: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("list") or []:
        if not isinstance(item, Mapping):
            continue
        rcept_no = str(item.get("rcept_no") or "").strip()
        if not rcept_no:
            continue
        rows.append(
            {
                "source_id": "dart_openapi_disclosures",
                "source_event_id": rcept_no,
                "rcept_no": rcept_no,
                "symbol": str(item.get("stock_code") or ""),
                "corp_code": item.get("corp_code"),
                "market": "KRX",
                "title": str(item.get("report_nm") or item.get("corp_name") or "OpenDART disclosure"),
                "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={urllib.parse.quote(rcept_no)}",
                "published_at_kst": _iso_kst_from_yyyymmdd(str(item.get("rcept_dt") or "")),
                "collected_at_kst": collected_at_kst,
                "event_type": "disclosure_event",
            }
        )
    return rows


def _naver_rows(payload: Mapping[str, Any], *, query: str, collected_at_kst: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("items") or []:
        if not isinstance(item, Mapping):
            continue
        link = str(item.get("originallink") or item.get("link") or "").strip()
        title = str(item.get("title") or "").strip()
        if not link or not title:
            continue
        rows.append(
            {
                "source_id": "naver_search_news_api",
                "source_event_id": link,
                "symbol": "",
                "corp_code": None,
                "market": "KRX",
                "title": title,
                "source_url": link,
                "original_link": link,
                "published_at_kst": _iso_kst_from_rfc2822(str(item.get("pubDate") or "")),
                "collected_at_kst": collected_at_kst,
                "event_type": "news_event",
            }
        )
    return rows


def _public_rss_rows(items: Sequence[Mapping[str, str]], *, query: str, collected_at_kst: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in items:
        link = str(item.get("link") or "").strip()
        title = str(item.get("title") or "").strip()
        if not link or not title:
            continue
        rows.append(
            {
                "source_id": "public_news_rss_search",
                "source_event_id": str(item.get("guid") or link),
                "symbol": "",
                "corp_code": None,
                "market": "KRX",
                "title": title,
                "source_url": link,
                "original_link": link,
                "published_at_kst": _iso_kst_from_rfc2822(str(item.get("pubDate") or "")),
                "collected_at_kst": collected_at_kst,
                "event_type": "news_event",
                "query": query,
            }
        )
    return rows


def _runtime_registry_for_sources(source_ids: Sequence[str]) -> Dict[str, Any]:
    reg = loadSourceRegistryConfig()
    approved = set(reg["approved_first_go_source_ids"])
    disabled = set(reg["disabled_live_source_ids"])
    for source_id in source_ids:
        source = reg["sources"].get(source_id)
        if not source:
            continue
        source["source_status"] = "approved_first_go"
        source["live_enabled"] = True
        approved.add(source_id)
        disabled.discard(source_id)
    reg["approved_first_go_source_ids"] = sorted(approved)
    reg["disabled_live_source_ids"] = sorted(disabled)
    return reg


def _naver_queries_from_env() -> List[str]:
    raw = os.getenv("HWISTOCK_INTEL_QUERIES", "").strip()
    if not raw:
        return list(DEFAULT_NAVER_QUERIES)
    return [part.strip() for part in raw.split(",") if part.strip()]


def collectOpenDartOnce(
    *,
    api_key: Optional[str] = None,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    collected_at_kst: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    key = api_key if api_key is not None else os.getenv("DART_API_KEY", "").strip()
    collected = collected_at_kst or makeRunCollectedAtKst()
    run_date = _kst_date(now)
    result: Dict[str, Any] = {
        "source_id": "dart_openapi_disclosures",
        "credential_present": bool(key),
        "status": "skipped_missing_key",
        "events": [],
        "raw_artifact_path": None,
        "message_class": None,
    }
    if not key:
        return result

    params = {
        "crtfc_key": key,
        "bgn_de": run_date.strftime("%Y%m%d"),
        "page_no": "1",
        "page_count": os.getenv("HWISTOCK_DART_PAGE_COUNT", "10").strip() or "10",
    }
    url = OPENDART_LIST_URL + "?" + urllib.parse.urlencode(params)
    payload = _safe_urlopen_json(url)
    sanitized = _sanitize_opendart_payload(payload)
    raw_path = output_root / "raw" / run_date.isoformat() / "disclosures" / f"opendart-list-{_compact_kst_stamp(now)}.json"
    _write_json(raw_path, sanitized)

    status_code = str(payload.get("status") or "")
    rows = _opendart_rows(payload, collected)
    result.update(
        {
            "status": "pass" if status_code in ("000", "013") else "fail",
            "message_class": payload.get("message"),
            "http_status": payload.get("_http_status"),
            "source_status": status_code,
            "events": rows,
            "raw_artifact_path": _display_path(raw_path),
        }
    )
    return result


def collectNaverNewsOnce(
    *,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    queries: Optional[Sequence[str]] = None,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    collected_at_kst: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    cid = client_id if client_id is not None else os.getenv("NAVER_CLIENT_ID", "").strip()
    secret = client_secret if client_secret is not None else os.getenv("NAVER_CLIENT_SECRET", "").strip()
    collected = collected_at_kst or makeRunCollectedAtKst()
    run_date = _kst_date(now)
    query_list = list(queries if queries is not None else _naver_queries_from_env())
    result: Dict[str, Any] = {
        "source_id": "naver_search_news_api",
        "credential_present": bool(cid and secret),
        "status": "skipped_missing_key",
        "queries": query_list,
        "events": [],
        "raw_artifact_paths": [],
    }
    if not cid or not secret:
        return result

    headers = {
        "X-Naver-Client-Id": cid,
        "X-Naver-Client-Secret": secret,
    }
    all_rows: List[Dict[str, Any]] = []
    paths: List[str] = []
    failures: List[Dict[str, Any]] = []
    for query in query_list:
        params = {
            "query": query,
            "display": os.getenv("HWISTOCK_NAVER_DISPLAY", "10").strip() or "10",
            "start": "1",
            "sort": "date",
        }
        url = NAVER_NEWS_URL + "?" + urllib.parse.urlencode(params)
        payload = _safe_urlopen_json(url, headers=headers)
        sanitized = _sanitize_naver_payload(payload, query=query)
        safe_query = "".join(ch if ch.isalnum() else "-" for ch in query).strip("-")[:32] or "query"
        raw_path = output_root / "raw" / run_date.isoformat() / "news" / f"naver-{safe_query}-{_compact_kst_stamp(now)}.json"
        _write_json(raw_path, sanitized)
        paths.append(_display_path(raw_path))
        if payload.get("_http_status") == 200:
            all_rows.extend(_naver_rows(payload, query=query, collected_at_kst=collected))
        else:
            failures.append({"query": query, "http_status": payload.get("_http_status")})

    result.update(
        {
            "status": "pass" if not failures else "partial_fail",
            "events": all_rows,
            "raw_artifact_paths": paths,
            "failures": failures,
        }
    )
    return result


def collectPublicNewsRssOnce(
    *,
    queries: Optional[Sequence[str]] = None,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    collected_at_kst: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    collected = collected_at_kst or makeRunCollectedAtKst()
    run_date = _kst_date(now)
    query_list = list(queries if queries is not None else _naver_queries_from_env())
    result: Dict[str, Any] = {
        "source_id": "public_news_rss_search",
        "credential_present": True,
        "status": "pending",
        "queries": query_list,
        "events": [],
        "raw_artifact_paths": [],
    }
    all_rows: List[Dict[str, Any]] = []
    paths: List[str] = []
    failures: List[Dict[str, Any]] = []
    for query in query_list:
        params = {
            "q": f"{query} 주식 OR 증시 OR 공시",
            "hl": "ko",
            "gl": "KR",
            "ceid": "KR:ko",
        }
        url = GOOGLE_NEWS_RSS_URL + "?" + urllib.parse.urlencode(params)
        payload = _safe_urlopen_text(url)
        sanitized = _sanitize_rss_payload(payload, query=query)
        safe_query = "".join(ch if ch.isalnum() else "-" for ch in query).strip("-")[:32] or "query"
        raw_path = output_root / "raw" / run_date.isoformat() / "news" / f"public-rss-{safe_query}-{_compact_kst_stamp(now)}.json"
        _write_json(raw_path, sanitized)
        paths.append(_display_path(raw_path))
        if payload.get("_http_status") == 200 and sanitized["item_count"]:
            all_rows.extend(_public_rss_rows(sanitized["items"], query=query, collected_at_kst=collected))
        else:
            failures.append(
                {
                    "query": query,
                    "http_status": payload.get("_http_status"),
                    "item_count": sanitized["item_count"],
                }
            )
    result.update(
        {
            "status": "pass" if all_rows and not failures else ("partial_fail" if all_rows else "fail"),
            "events": all_rows,
            "raw_artifact_paths": paths,
            "failures": failures,
        }
    )
    return result


def ingestFixtureRows(
    rows: Sequence[Mapping[str, Any]],
    *,
    registry: Optional[Mapping[str, Any]] = None,
    run_collected_at_kst: Optional[str] = None,
) -> Dict[str, Any]:
    reg = registry if registry is not None else loadSourceRegistryConfig()
    collected_at = run_collected_at_kst or makeRunCollectedAtKst()

    accepted_events: List[Dict[str, Any]] = []
    failures: List[Dict[str, str]] = []
    blocked_source_ids: List[str] = []
    per_source_counts: Dict[str, int] = {}
    per_source_last_success: Dict[str, str] = {}

    for index, row in enumerate(rows):
        source_id = str(row.get("source_id") or "")
        if not source_id:
            failures.append({"row_index": str(index), "reason": "missing_source_id"})
            continue

        if source_id not in reg["sources"]:
            blocked_source_ids.append(source_id)
            failures.append({"row_index": str(index), "reason": "unknown_source", "source_id": source_id})
            continue

        if not canIngestSourceInFoundation(source_id, reg):
            blocked = classifyBlockedSource(source_id, reg)
            if source_id not in blocked_source_ids:
                blocked_source_ids.append(source_id)
            failures.append(
                {
                    "row_index": str(index),
                    "reason": blocked,
                    "source_id": source_id,
                }
            )
            continue

        try:
            event = normalizeFixtureRow(row, registry=reg, collected_at_kst=collected_at)
        except (KeyError, TypeError, ValueError) as exc:
            failures.append(
                {
                    "row_index": str(index),
                    "reason": "normalize_error",
                    "source_id": source_id,
                    "detail": str(exc),
                }
            )
            continue

        accepted_events.append(event)
        per_source_counts[source_id] = per_source_counts.get(source_id, 0) + 1
        per_source_last_success[source_id] = collected_at

    events = linkDuplicateEvents(accepted_events)
    duplicate_links = sum(1 for event in events if event.get("duplicate_of_event_id"))
    unique_events = sum(1 for event in events if not event.get("duplicate_of_event_id"))

    summary: Dict[str, Any] = {
        "foundation_mode": True,
        "submitted_rows": len(rows),
        "ingested_events": len(events),
        "unique_events": unique_events,
        "duplicate_links": duplicate_links,
        "per_source_counts": dict(sorted(per_source_counts.items())),
        "failures": failures,
        "blocked_source_ids": sorted(set(blocked_source_ids)),
        "approved_first_go_source_ids": list(reg["approved_first_go_source_ids"]),
        "retention_notes": reg.get("retention_default", "one_week_paper_gate_minimum"),
        "evidence_written": False,
    }

    health: Dict[str, Any] = {
        "status": "ok" if failures == [] or unique_events > 0 else "degraded",
        "foundation_mode": True,
        "last_fetch_at_kst": collected_at,
        "per_source_last_success_at_kst": dict(sorted(per_source_last_success.items())),
        "failure_count": len(failures),
        "backlog_rows": len(failures),
        "duplicate_link_count": duplicate_links,
        "live_sources_enabled": False,
        "disabled_live_source_ids": list(reg["disabled_live_source_ids"]),
        "blocked_source_ids": summary["blocked_source_ids"],
    }

    return {
        "events": events,
        "summary": summary,
        "health": health,
    }


def runCollectorOnce(
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    enable_network: bool = True,
    include_naver: bool = True,
    include_public_rss: bool = False,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    collected_at = makeRunCollectedAtKst()
    run_date = _kst_date(now)
    source_results: List[Dict[str, Any]] = []
    raw_rows: List[Dict[str, Any]] = []
    enabled_source_ids: List[str] = []

    if enable_network:
        dart = collectOpenDartOnce(output_root=output_root, collected_at_kst=collected_at, now=now)
        source_results.append({k: v for k, v in dart.items() if k != "events"})
        raw_rows.extend(dart.get("events") or [])
        if dart.get("status") == "pass":
            enabled_source_ids.append("dart_openapi_disclosures")

        if include_naver:
            naver = collectNaverNewsOnce(output_root=output_root, collected_at_kst=collected_at, now=now)
            source_results.append({k: v for k, v in naver.items() if k != "events"})
            raw_rows.extend(naver.get("events") or [])
            if naver.get("status") in ("pass", "partial_fail"):
                enabled_source_ids.append("naver_search_news_api")
        if include_public_rss:
            rss = collectPublicNewsRssOnce(output_root=output_root, collected_at_kst=collected_at, now=now)
            source_results.append({k: v for k, v in rss.items() if k != "events"})
            raw_rows.extend(rss.get("events") or [])
            if rss.get("status") in ("pass", "partial_fail"):
                enabled_source_ids.append("public_news_rss_search")
    else:
        source_results.extend(
            [
                {"source_id": "dart_openapi_disclosures", "status": "skipped_network_disabled"},
                {"source_id": "naver_search_news_api", "status": "skipped_network_disabled"},
            ]
        )
        if include_public_rss:
            source_results.append({"source_id": "public_news_rss_search", "status": "skipped_network_disabled_fallback_only"})

    registry = _runtime_registry_for_sources(enabled_source_ids)
    normalized = ingestFixtureRows(raw_rows, registry=registry, run_collected_at_kst=collected_at)
    normalized_path = output_root / "normalized" / run_date.isoformat() / "events.jsonl"
    appended_event_count = 0
    if normalized["events"]:
        appended_event_count = _append_jsonl_unique(normalized_path, normalized["events"])

    health = {
        "event": "market_intelligence_collector_once",
        "timestamp_kst": collected_at,
        "network_enabled": enable_network,
        "orders_enabled": False,
        "broker_calls_enabled": False,
        "source_results": source_results,
        "normalized_event_count": len(normalized["events"]),
        "appended_event_count": appended_event_count,
        "unique_event_count": normalized["summary"]["unique_events"],
        "failure_count": normalized["health"]["failure_count"],
        "normalized_artifact_path": _display_path(normalized_path) if normalized["events"] else None,
        "status": "ok" if normalized["events"] else "blocked_no_source_rows",
    }
    health_path = output_root / "evidence" / run_date.isoformat() / "market-intel-collector-health.json"
    _write_json(health_path, health)
    return {
        "health": health,
        "health_artifact_path": _display_path(health_path),
        "ingestion": normalized,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="hwiStock market intelligence collector")
    parser.add_argument("--once", action="store_true", help="Run one collector tick and exit")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Runtime data root")
    parser.add_argument("--no-network", action="store_true", help="Emit health without live source calls")
    parser.add_argument("--no-naver", action="store_true", help="Skip Naver news even when keys exist")
    parser.add_argument("--fallback-public-rss", action="store_true", help="Enable fallback-only public RSS news collection")
    parser.add_argument("--no-public-rss", action="store_true", help="Compatibility no-op: public RSS is disabled by default")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.once:
        parser.print_help(sys.stderr)
        return 2
    result = runCollectorOnce(
        output_root=Path(args.output_root),
        enable_network=not args.no_network,
        include_naver=not args.no_naver,
        include_public_rss=args.fallback_public_rss and not args.no_public_rss,
    )
    sys.stdout.write(json.dumps(result["health"], ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
