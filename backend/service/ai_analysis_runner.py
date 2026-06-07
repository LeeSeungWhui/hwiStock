"""
hwiStock AI analysis service wrapper.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from lib.ai_analysis_runtime import (
    main,
    publish_morning_watchlist_artifact,
    run_analysis_once,
    run_flash_trade_document_once,
    run_pro_hourly_once,
)

__all__ = (
    "main",
    "publish_morning_watchlist_artifact",
    "run_analysis_once",
    "run_flash_trade_document_once",
    "run_pro_hourly_once",
)


if __name__ == "__main__":
    raise SystemExit(main())
