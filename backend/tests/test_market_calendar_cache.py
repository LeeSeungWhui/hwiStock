from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import market_calendar_cache as calendar_cache  # noqa: E402


def _seed(path: Path, payload: dict | None = None) -> Path:
    path.write_text(
        json.dumps(
            payload or {"schema_version": "test", "validUntil": "2026-06-10T23:59:59+09:00", "days": {}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def test_paper_calendar_autofills_weekday_non_holiday_today(tmp_path: Path):
    repo = _seed(tmp_path / "repo-calendar.json")
    runtime = tmp_path / "runtime-calendar.json"

    result = calendar_cache.ensure_market_calendar(
        investment_mode="paper",
        target_date=date(2026, 6, 11),
        horizon_days=14,
        write=True,
        repo_calendar_path=repo,
        runtime_calendar_path=runtime,
    )
    written = json.loads(runtime.read_text(encoding="utf-8"))

    assert result["status"] == "ok"
    assert "2026-06-11" in result["rows_added"]
    assert "2026-06-19" in written["days"]
    assert written["validUntil"] == "2026-06-25T23:59:59+09:00"
    row = written["days"]["2026-06-11"]
    assert row["isTradingDay"] is True
    assert row["source"] == calendar_cache.AUTOFILL_SOURCE
    assert row["nxtEnabled"] is False
    assert row["krx"]["orderClose"] == "15:00"


def test_paper_calendar_does_not_autofill_weekend_as_trading(tmp_path: Path):
    repo = _seed(tmp_path / "repo-calendar.json")
    result = calendar_cache.ensure_market_calendar(
        investment_mode="paper",
        target_date=date(2026, 6, 13),
        horizon_days=0,
        write=False,
        repo_calendar_path=repo,
        runtime_calendar_path=tmp_path / "runtime-calendar.json",
    )

    assert result["today_row"]["isTradingDay"] is False
    assert result["today_row"]["reason"] == "Saturday"


def test_paper_calendar_marks_known_public_holiday_non_trading(tmp_path: Path):
    repo = _seed(tmp_path / "repo-calendar.json")
    result = calendar_cache.ensure_market_calendar(
        investment_mode="paper",
        target_date=date(2026, 6, 3),
        horizon_days=0,
        write=False,
        repo_calendar_path=repo,
        runtime_calendar_path=tmp_path / "runtime-calendar.json",
    )

    assert result["today_row"]["isTradingDay"] is False
    assert "election" in result["today_row"]["reason"]


def test_live_mode_missing_calendar_fails_closed_no_autofill(tmp_path: Path):
    repo = _seed(tmp_path / "repo-calendar.json")
    runtime = tmp_path / "runtime-calendar.json"
    result = calendar_cache.ensure_market_calendar(
        investment_mode="live",
        target_date=date(2026, 6, 11),
        horizon_days=14,
        write=True,
        repo_calendar_path=repo,
        runtime_calendar_path=runtime,
    )

    assert result["status"] == "fail_closed_no_autofill"
    assert result["rows_added"] == []
    assert not runtime.exists()


def test_calendar_refresh_writes_evidence(tmp_path: Path):
    repo = _seed(tmp_path / "repo-calendar.json")

    result = calendar_cache.ensure_market_calendar(
        investment_mode="paper",
        target_date=date(2026, 6, 11),
        horizon_days=1,
        write=True,
        write_evidence=True,
        repo_calendar_path=repo,
        runtime_calendar_path=tmp_path / "runtime-calendar.json",
        data_root=tmp_path / "data",
    )

    latest = Path(result["evidence_paths"]["latest_path"])
    assert latest.is_file()
    evidence = json.loads(latest.read_text(encoding="utf-8"))
    assert evidence["event"] == "market_calendar_refresh"
    assert evidence["status"] == "ok"
