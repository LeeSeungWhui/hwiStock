"""Local KRX/NXT market-calendar cache refresh helpers.

Paper/mock operation uses a local rolling cache as the calendar source of truth.
Live mode must remain fail-closed when the calendar cannot be verified.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPO_CALENDAR_PATH = REPO_ROOT / "config" / "market-calendar" / "krx-nxt-trading-days.json"
DEFAULT_RUNTIME_CALENDAR_PATH = Path("/home/hwi/.config/hwistock/market-calendar/krx-nxt-trading-days.json")
AUTOFILL_SOURCE = "paper_autofill_weekday_public_holiday_crosscheck"
AUTOFILL_CONFIDENCE = "paper_experiment"
AUTOFILL_WARNING = "calendar_row_autofilled_for_paper_mode"
SCHEMA_VERSION = "krx_nxt_trading_calendar_cache/v0"


KNOWN_PUBLIC_HOLIDAYS: dict[str, str] = {
    "2026-01-01": "New Year's Day",
    "2026-06-03": "KRX/local election day",
    "2026-06-06": "Memorial Day",
    "2026-12-25": "Christmas Day",
}


def now_kst() -> datetime:
    return datetime.now(KST).replace(microsecond=0)


def parse_date(value: Optional[Any], *, today: Optional[date] = None) -> date:
    if value is None or str(value).strip().lower() in {"", "today"}:
        return today or now_kst().date()
    return date.fromisoformat(str(value).strip())


def parse_kst_datetime(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST).replace(microsecond=0)


def resolve_runtime_calendar_path(env: Optional[Mapping[str, str]] = None) -> Path:
    source = env if env is not None else os.environ
    raw = str(source.get("HWISTOCK_RUNTIME_CALENDAR_PATH") or "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else REPO_ROOT / path
    return DEFAULT_RUNTIME_CALENDAR_PATH


def resolve_repo_calendar_path(env: Optional[Mapping[str, str]] = None) -> Path:
    source = env if env is not None else os.environ
    raw = str(source.get("HWISTOCK_CALENDAR_PATH") or "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else REPO_ROOT / path
    return DEFAULT_REPO_CALENDAR_PATH


def resolve_operator_override_path(env: Optional[Mapping[str, str]] = None) -> Optional[Path]:
    source = env if env is not None else os.environ
    raw = str(source.get("HWISTOCK_MARKET_CALENDAR_OVERRIDE_PATH") or "").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def calendar_read_candidates(env: Optional[Mapping[str, str]] = None) -> list[Path]:
    source = env if env is not None else os.environ
    runtime = resolve_runtime_calendar_path(source)
    repo = resolve_repo_calendar_path(source)
    explicit_runtime = bool(str(source.get("HWISTOCK_RUNTIME_CALENDAR_PATH") or "").strip())
    explicit_repo = bool(str(source.get("HWISTOCK_CALENDAR_PATH") or "").strip())
    candidates: list[Path] = []
    if explicit_runtime or (not explicit_repo or repo == DEFAULT_REPO_CALENDAR_PATH):
        candidates.append(runtime)
    candidates.append(repo)
    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def resolve_calendar_read_path(env: Optional[Mapping[str, str]] = None) -> Path:
    candidates = calendar_read_candidates(env)
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


def read_json(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def calendar_day_rows(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for key in ("days", "tradingDays", "calendar"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            for day, row in value.items():
                if isinstance(row, Mapping):
                    rows[str(day)] = dict(row)
                elif isinstance(row, bool):
                    rows[str(day)] = {"dateKst": str(day), "isTradingDay": row}
        elif isinstance(value, list):
            for row in value:
                if isinstance(row, str):
                    rows[row] = {"dateKst": row, "isTradingDay": True}
                elif isinstance(row, Mapping):
                    day = str(row.get("dateKst") or row.get("date") or row.get("day") or "").strip()
                    if day:
                        rows[day] = dict(row)
    return rows


def known_public_holiday_reason(day: date) -> Optional[str]:
    key = day.isoformat()
    if key in KNOWN_PUBLIC_HOLIDAYS:
        return KNOWN_PUBLIC_HOLIDAYS[key]
    return None


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5


def is_paper_autofill_row(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("source") or row.get("sourceAuthority") or "").strip() == AUTOFILL_SOURCE
        or str(row.get("confidence") or "").strip() == AUTOFILL_CONFIDENCE
        or AUTOFILL_WARNING in [str(item) for item in (row.get("warnings") or [])]
    )


def _paper_trading_row(day: date) -> dict[str, Any]:
    return {
        "dateKst": day.isoformat(),
        "isTradingDay": True,
        "venue": "KRX",
        "nxtEnabled": False,
        "krx": {
            "regularOpen": "09:00",
            "regularClose": "15:30",
            "orderOpen": "09:00",
            "orderClose": "15:00",
        },
        "nxt": {"open": "08:00", "close": "20:00", "enabled": False},
        "marketContextOpen": "09:00-15:30",
        "brokerOrderOpen": "09:00-15:00",
        "closeContextOpen": "15:00-15:30",
        "source": AUTOFILL_SOURCE,
        "sourceAuthority": AUTOFILL_SOURCE,
        "confidence": AUTOFILL_CONFIDENCE,
        "warnings": [AUTOFILL_WARNING],
    }


def paper_calendar_row(day: date, *, seed_row: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
    if isinstance(seed_row, Mapping):
        row = deepcopy(dict(seed_row))
        row.setdefault("dateKst", day.isoformat())
        return row
    if is_weekend(day):
        return {
            "dateKst": day.isoformat(),
            "isTradingDay": False,
            "reason": "Saturday" if day.weekday() == 5 else "Sunday",
            "source": "paper_autofill_weekend_rule",
            "confidence": AUTOFILL_CONFIDENCE,
        }
    holiday = known_public_holiday_reason(day)
    if holiday:
        return {
            "dateKst": day.isoformat(),
            "isTradingDay": False,
            "reason": holiday,
            "source": "paper_autofill_public_holiday_table",
            "confidence": AUTOFILL_CONFIDENCE,
        }
    return _paper_trading_row(day)


def _merge_override_rows(rows: dict[str, dict[str, Any]], override_path: Optional[Path]) -> list[str]:
    if not override_path or not override_path.is_file():
        return []
    payload = read_json(override_path)
    override_rows = calendar_day_rows(payload)
    rows.update(override_rows)
    return sorted(override_rows)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _evidence_dir(data_root: Path, day: date) -> Path:
    return data_root / "evidence" / day.isoformat()


def write_refresh_evidence(
    payload: Mapping[str, Any],
    *,
    data_root: Optional[Path] = None,
    at: Optional[datetime] = None,
) -> dict[str, str]:
    ref = at or now_kst()
    root = data_root or Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
    out_dir = _evidence_dir(root, ref.date())
    out_dir.mkdir(parents=True, exist_ok=True)
    latest = out_dir / "market-calendar-refresh-latest.json"
    stamped = out_dir / f"market-calendar-refresh-{ref.strftime('%H%M%S')}.json"
    text = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    latest.write_text(text, encoding="utf-8")
    stamped.write_text(text, encoding="utf-8")
    return {"latest_path": str(latest), "stamped_path": str(stamped)}


def ensure_market_calendar(
    *,
    investment_mode: str = "paper",
    target_date: Optional[date] = None,
    horizon_days: int = 14,
    write: bool = False,
    write_evidence: bool = False,
    repo_calendar_path: Optional[Path] = None,
    runtime_calendar_path: Optional[Path] = None,
    override_path: Optional[Path] = None,
    data_root: Optional[Path] = None,
    at: Optional[datetime] = None,
) -> dict[str, Any]:
    ref = at or now_kst()
    target = target_date or ref.date()
    horizon = max(0, int(horizon_days))
    end_day = target + timedelta(days=horizon)
    mode = str(investment_mode or "paper").strip().lower()
    repo_path = repo_calendar_path or DEFAULT_REPO_CALENDAR_PATH
    runtime_path = runtime_calendar_path or DEFAULT_RUNTIME_CALENDAR_PATH
    override = override_path
    base_path = runtime_path if runtime_path.is_file() else repo_path
    base_payload = read_json(base_path) if base_path.is_file() else {}
    rows = calendar_day_rows(base_payload)
    override_days = _merge_override_rows(rows, override)
    rows_added: list[str] = []
    rows_preserved: list[str] = []
    warnings: list[str] = []
    status = "ok"
    changed = False

    if mode == "live":
        required_days = [(target + timedelta(days=offset)).isoformat() for offset in range(horizon + 1)]
        missing = [day for day in required_days if day not in rows]
        valid_until = parse_kst_datetime(base_payload.get("validUntil") or base_payload.get("valid_until"))
        stale = valid_until is None or valid_until < datetime.combine(end_day, datetime.max.time(), tzinfo=KST)
        if missing or stale:
            status = "fail_closed_no_autofill"
            warnings.append("live_mode_calendar_missing_or_stale_no_autofill")
        result = {
            "schema_version": "market_calendar_refresh/v0",
            "event": "market_calendar_refresh",
            "status": status,
            "investment_mode": mode,
            "target_date_kst": target.isoformat(),
            "horizon_days": horizon,
            "horizon_end_date_kst": end_day.isoformat(),
            "calendar_path": str(base_path),
            "runtime_calendar_path": str(runtime_path),
            "repo_seed_path": str(repo_path),
            "changed": False,
            "rows_added": rows_added,
            "rows_preserved": sorted(rows),
            "override_days": override_days,
            "valid_until_kst": base_payload.get("validUntil") or base_payload.get("valid_until"),
            "warnings": warnings,
            "broker_calls_enabled": False,
            "orders_enabled": False,
        }
        if write_evidence:
            result["evidence_paths"] = write_refresh_evidence(result, data_root=data_root, at=ref)
        return result

    if mode != "paper":
        warnings.append(f"unknown_investment_mode_treated_as_paper:{mode}")
        mode = "paper"

    for offset in range(horizon + 1):
        day = target + timedelta(days=offset)
        key = day.isoformat()
        if key in rows:
            rows_preserved.append(key)
            continue
        rows[key] = paper_calendar_row(day)
        rows_added.append(key)
        changed = True
        if is_paper_autofill_row(rows[key]):
            warnings.append(AUTOFILL_WARNING)

    valid_until = f"{end_day.isoformat()}T23:59:59+09:00"
    existing_valid_until = parse_kst_datetime(base_payload.get("validUntil") or base_payload.get("valid_until"))
    target_valid_until = parse_kst_datetime(valid_until)
    if existing_valid_until is None or (target_valid_until and existing_valid_until < target_valid_until):
        changed = True

    output_payload = dict(base_payload)
    output_payload.update(
        {
            "schema_version": SCHEMA_VERSION,
            "generatedAtKst": ref.isoformat(),
            "validUntil": valid_until,
            "sourceAuthority": AUTOFILL_SOURCE,
            "sourceHierarchy": (
                "runtime calendar cache; repo seed; static public holiday/weekend cross-check; "
                "paper weekday autofill; live mode fail-closed"
            ),
            "autofillPolicy": {
                "paper": "weekday_not_known_public_holiday_autofill_krx_only",
                "live": "no_autofill_fail_closed",
                "nxtEnabledInPaper": False,
            },
            "warnings": sorted(set([*(output_payload.get("warnings") or []), *warnings])),
            "days": {key: rows[key] for key in sorted(rows)},
        }
    )

    if write and changed:
        _atomic_write_json(runtime_path, output_payload)

    today_row = rows.get(target.isoformat())
    result = {
        "schema_version": "market_calendar_refresh/v0",
        "event": "market_calendar_refresh",
        "status": status,
        "investment_mode": mode,
        "target_date_kst": target.isoformat(),
        "horizon_days": horizon,
        "horizon_end_date_kst": end_day.isoformat(),
        "calendar_path": str(runtime_path if write else base_path),
        "runtime_calendar_path": str(runtime_path),
        "repo_seed_path": str(repo_path),
        "changed": changed,
        "rows_added": rows_added,
        "rows_preserved": sorted(set(rows_preserved)),
        "override_days": override_days,
        "valid_until_kst": valid_until,
        "today_row": today_row,
        "warnings": sorted(set(warnings)),
        "broker_calls_enabled": False,
        "orders_enabled": False,
    }
    if write_evidence:
        result["evidence_paths"] = write_refresh_evidence(result, data_root=data_root, at=ref)
    return result
