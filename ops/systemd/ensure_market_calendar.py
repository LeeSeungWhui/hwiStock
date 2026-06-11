#!/usr/bin/env python3
"""Ensure hwiStock local market-calendar cache is usable for paper runtime."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from lib import market_calendar_cache as calendar_cache  # noqa: E402


def _path_arg(value: Optional[str]) -> Optional[Path]:
    if not value:
        return None
    path = Path(str(value).strip())
    return path if path.is_absolute() else REPO_ROOT / path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh/repair local hwiStock market calendar")
    parser.add_argument("--investment-mode", default=os.getenv("HWISTOCK_INVESTMENT_MODE", "paper"))
    parser.add_argument("--date", default="today", help="Target KST date, YYYY-MM-DD or today")
    parser.add_argument("--horizon-days", type=int, default=14)
    parser.add_argument("--write", action="store_true", help="Write runtime calendar atomically")
    parser.add_argument("--write-evidence", action="store_true", help="Write refresh evidence JSON")
    parser.add_argument("--print-row", action="store_true", help="Print only target date row")
    parser.add_argument("--data-root", default=os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
    parser.add_argument("--repo-calendar-path", default=os.getenv("HWISTOCK_CALENDAR_PATH", ""))
    parser.add_argument("--runtime-calendar-path", default=os.getenv("HWISTOCK_RUNTIME_CALENDAR_PATH", ""))
    parser.add_argument(
        "--override-path",
        default=os.getenv("HWISTOCK_MARKET_CALENDAR_OVERRIDE_PATH", ""),
        help="Optional operator override calendar JSON",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    target = calendar_cache.parse_date(args.date)
    repo_path = _path_arg(args.repo_calendar_path) or calendar_cache.DEFAULT_REPO_CALENDAR_PATH
    runtime_path = _path_arg(args.runtime_calendar_path) or calendar_cache.DEFAULT_RUNTIME_CALENDAR_PATH
    override_path = _path_arg(args.override_path)
    result = calendar_cache.ensure_market_calendar(
        investment_mode=args.investment_mode,
        target_date=target,
        horizon_days=args.horizon_days,
        write=args.write,
        write_evidence=args.write_evidence,
        repo_calendar_path=repo_path,
        runtime_calendar_path=runtime_path,
        override_path=override_path,
        data_root=Path(args.data_root),
    )
    payload = result.get("today_row") if args.print_row else result
    print(json.dumps(payload or {}, ensure_ascii=False, indent=2, sort_keys=True))

    status = str(result.get("status") or "")
    if status.startswith("fail"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
