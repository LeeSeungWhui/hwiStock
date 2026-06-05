"""
hwiStock market intelligence ingestion service wrapper.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from lib.market_intelligence_ingestion_runtime import (
    KST,
    _append_jsonl_unique,
    _public_rss_rows,
    _runtime_registry_for_sources,
    _sanitize_rss_payload,
    collectNaverNewsOnce,
    collectOpenDartOnce,
    collectPublicNewsRssOnce,
    datetime,
    ingestFixtureRows,
    main,
    makeRunCollectedAtKst,
    runCollectorOnce,
)

__all__ = (
    "KST",
    "_append_jsonl_unique",
    "_public_rss_rows",
    "_runtime_registry_for_sources",
    "_sanitize_rss_payload",
    "collectNaverNewsOnce",
    "collectOpenDartOnce",
    "collectPublicNewsRssOnce",
    "datetime",
    "ingestFixtureRows",
    "main",
    "makeRunCollectedAtKst",
    "runCollectorOnce",
)


if __name__ == "__main__":
    raise SystemExit(main())
