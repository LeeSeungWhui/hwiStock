"""
HWISTOCK-UNIT-003 foundation ingestion: in-memory fixture rows only.
Returns events, summary, and health dictionaries. No network or file writes.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence

from lib.market_intelligence import (
    classifyBlockedSource,
    canIngestSourceInFoundation,
    linkDuplicateEvents,
    loadSourceRegistryConfig,
    normalizeFixtureRow,
)

KST = timezone(timedelta(hours=9))


def makeRunCollectedAtKst() -> str:
    return datetime.now(tz=KST).replace(microsecond=0).isoformat()


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
