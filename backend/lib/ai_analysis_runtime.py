"""
hwiStock AI analysis runtime implementation.

Reads sanitized market-intelligence events, calls the official DeepSeek API
directly, and writes analysis evidence. This runner never imports broker, KIS,
or order-routing code, and its output is report-only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    from lib import ai_orchestration as ao
    from lib import market_session_gate as msg
    from lib import runtime_policy as rp
    from lib import trading_engine
except ImportError:  # pragma: no cover
    from backend.lib import ai_orchestration as ao
    from backend.lib import market_session_gate as msg
    from backend.lib import runtime_policy as rp
    from backend.lib import trading_engine

KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = ao.DEEPSEEK_PRO_MODEL
DEEPSEEK_MAX_TOKENS_OVERRIDE_ENV = "HWISTOCK_DEEPSEEK_MAX_TOKENS_OVERRIDE"
DEEPSEEK_JOB_MAX_TOKENS_OVERRIDE_ENVS = {
    "pro-hourly": "HWISTOCK_DEEPSEEK_PRO_MAX_TOKENS_OVERRIDE",
    "flash-10m": "HWISTOCK_DEEPSEEK_FLASH_MAX_TOKENS_OVERRIDE",
    "legacy-summary": "HWISTOCK_DEEPSEEK_LEGACY_MAX_TOKENS_OVERRIDE",
}
DEPRECATED_DEEPSEEK_MAX_TOKENS_ENVS = {
    "pro-hourly": "HWISTOCK_DEEPSEEK_PRO_MAX_TOKENS",
    "flash-10m": "HWISTOCK_DEEPSEEK_FLASH_MAX_TOKENS",
    "legacy-summary": "HWISTOCK_DEEPSEEK_LEGACY_MAX_TOKENS",
}


def _now_kst() -> datetime:
    return datetime.now(KST).replace(microsecond=0)


def _date_dir(root: Path, subdir: str, at: datetime) -> Path:
    return root / subdir / at.date().isoformat()


def _read_recent_events(data_root: Path, *, limit: Optional[int] = None, at: Optional[datetime] = None) -> List[Dict[str, Any]]:
    row_limit = int(limit or os.getenv("HWISTOCK_AI_EVENT_LIMIT", "12"))
    day = (at or _now_kst()).date().isoformat()
    path = data_root / "normalized" / day / "events.jsonl"
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "event_id": str(row.get("event_id") or ""),
                "source_id": str(row.get("source_id") or ""),
                "event_type": str(row.get("event_type") or ""),
                "title": str(row.get("title") or "")[:160],
                "published_at_kst": str(row.get("published_at_kst") or ""),
                "collected_at_kst": str(row.get("collected_at_kst") or ""),
                "query": str(row.get("query") or ""),
            }
        )
    return rows[-row_limit:]


def _iter_dates(start: date, end: date) -> List[date]:
    days: List[date] = []
    current = start
    while current <= end:
        days.append(current)
        current = current + timedelta(days=1)
    return days


def _parse_optional_kst(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _read_events_for_window(
    data_root: Path,
    *,
    start: datetime,
    end: datetime,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for day in _iter_dates(start.date(), end.date()):
        rows.extend(_read_recent_events(data_root, limit=limit, at=datetime.combine(day, datetime.min.time(), tzinfo=KST)))
    filtered: List[Dict[str, Any]] = []
    for row in rows:
        event_time = _parse_optional_kst(row.get("published_at_kst")) or _parse_optional_kst(row.get("collected_at_kst"))
        if event_time is None or start <= event_time < end:
            filtered.append(row)
    return filtered[-limit:]


def _read_events_for_hour_window(data_root: Path, *, at: datetime, limit: int = 200) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
    window = rp.proHourlyInputWindow(at)
    start = _parse_optional_kst(window["start_kst"])
    end = _parse_optional_kst(window["end_kst"])
    if not start or not end:
        return _read_recent_events(data_root, limit=limit, at=at), window
    return _read_events_for_window(data_root, start=start, end=end, limit=limit), window


def _read_events_for_flash_window(data_root: Path, *, at: datetime, limit: int = 200) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
    start = at - timedelta(minutes=10)
    end = at
    window = {"start_kst": start.isoformat(), "end_kst": end.isoformat()}
    return _read_events_for_window(data_root, start=start, end=end, limit=limit), window


def _read_json_artifact(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _latest_json_file(root: Path, *parts: str) -> Optional[Path]:
    directory = root.joinpath(*parts)
    if not directory.is_dir():
        return None
    files = sorted(p for p in directory.glob("*.json") if p.is_file() and not p.name.startswith("."))
    return files[-1] if files else None


def _read_recent_kis_snapshots(data_root: Path, *, at: datetime, limit: int = 6) -> List[Dict[str, Any]]:
    day = at.date().isoformat()
    paths: List[Path] = []
    for subdir in ("kis-market", "market", "runtime"):
        directory = data_root / subdir / day
        if directory.is_dir():
            paths.extend(p for p in directory.glob("*.json") if p.is_file() and not p.name.startswith("."))
    rows: List[Dict[str, Any]] = []
    for path in sorted(paths)[-limit:]:
        payload = _read_json_artifact(path)
        if payload:
            rows.append(payload)
    return rows


def _artifact_timestamp(payload: Mapping[str, Any]) -> Optional[datetime]:
    for key in (
        "produced_at_kst",
        "timestamp_kst",
        "collected_at_kst",
        "snapshot_at_kst",
        "created_at_kst",
    ):
        parsed = _parse_optional_kst(payload.get(key))
        if parsed:
            return parsed
    return None


def _read_kis_snapshots_for_window(data_root: Path, *, at: datetime, limit: int = 12) -> List[Dict[str, Any]]:
    start = at - timedelta(minutes=10)
    end = at
    paths: List[Path] = []
    for day in _iter_dates(start.date(), end.date()):
        day_text = day.isoformat()
        for subdir in ("kis-market", "market", "runtime"):
            directory = data_root / subdir / day_text
            if directory.is_dir():
                paths.extend(p for p in directory.glob("*.json") if p.is_file() and not p.name.startswith("."))
    rows: List[Dict[str, Any]] = []
    for path in sorted(paths):
        payload = _read_json_artifact(path)
        if not payload:
            continue
        timestamp = _artifact_timestamp(payload)
        if timestamp is None or start <= timestamp < end:
            rows.append(payload)
    return rows[-limit:]


def _read_compiled_watch(data_root: Path, *, at: datetime) -> List[Dict[str, Any]]:
    path = _latest_json_file(data_root, "compiled-watch", at.date().isoformat())
    payload = _read_json_artifact(path) if path else None
    if not payload:
        return []
    if isinstance(payload.get("items"), list):
        return [dict(item) for item in payload["items"] if isinstance(item, Mapping)]
    if isinstance(payload.get("compiled_watch"), list):
        return [dict(item) for item in payload["compiled_watch"] if isinstance(item, Mapping)]
    if payload.get("schema_version") == "compiled_watch/v0":
        return [payload]
    return []


def _read_morning_watchlist(data_root: Path, *, at: datetime) -> Optional[Dict[str, Any]]:
    day = at.date().isoformat()
    candidates = [
        _latest_named_json(data_root, "morning-watchlist", day, "morning-watchlist-latest.json"),
        _latest_named_json(data_root, "ai", day, "morning-watchlist-latest.json"),
    ]
    for path in candidates:
        payload = _read_json_artifact(path) if path else None
        if isinstance(payload, Mapping):
            return dict(payload)
    return None


def _calendar_rows_from_env() -> Dict[str, Dict[str, Any]]:
    path = msg.calendarPathFromEnv(os.environ)
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, Mapping):
        return {}
    rows: Dict[str, Dict[str, Any]] = {}
    for key in ("days", "tradingDays", "calendar"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            for day, row in value.items():
                if isinstance(row, Mapping):
                    rows[str(day)] = dict(row)
                elif isinstance(row, bool):
                    rows[str(day)] = {"isTradingDay": row}
        elif isinstance(value, list):
            for row in value:
                if isinstance(row, str):
                    rows[row] = {"isTradingDay": True}
                elif isinstance(row, Mapping):
                    day = str(row.get("dateKst") or row.get("date") or row.get("day") or "").strip()
                    if day:
                        rows[day] = dict(row)
    return rows


def _calendar_row_is_trading_day(row: Mapping[str, Any]) -> bool:
    return bool(row.get("isTradingDay", row.get("is_trading_day", row.get("tradingAllowed", False))))


def _calendar_regular_close(row: Mapping[str, Any]) -> datetime.time:
    krx = row.get("krx") if isinstance(row.get("krx"), Mapping) else {}
    raw = (
        row.get("orderClose")
        or row.get("order_close")
        or row.get("krxOrderClose")
        or row.get("krx_order_close")
        or krx.get("orderClose")
        or row.get("krxClose")
        or row.get("krx_close")
        or row.get("regularClose")
        or row.get("regular_close")
        or krx.get("regularClose")
        or "15:00"
    )
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(str(raw), fmt).time()
        except ValueError:
            continue
    return datetime.strptime("15:00", "%H:%M").time()


def _morning_prompt_input_window(
    *,
    target_trade_date: str,
    at: datetime,
) -> Dict[str, Any]:
    end = at.astimezone(KST).replace(microsecond=0)
    try:
        target_day = date.fromisoformat(target_trade_date)
    except ValueError:
        target_day = end.date()
    rows = _calendar_rows_from_env()
    previous_day = target_day - timedelta(days=1)
    previous_trading_day: Optional[date] = None
    previous_row: Dict[str, Any] = {}
    for _ in range(45):
        row = rows.get(previous_day.isoformat())
        if isinstance(row, Mapping) and _calendar_row_is_trading_day(row):
            previous_trading_day = previous_day
            previous_row = dict(row)
            break
        previous_day = previous_day - timedelta(days=1)

    if previous_trading_day is None:
        start = end - timedelta(hours=18)
        window_source = "fallback_18h_calendar_previous_trading_day_missing"
    else:
        start = datetime.combine(previous_trading_day, _calendar_regular_close(previous_row), tzinfo=KST)
        window_source = "calendar_previous_trading_close"
        if start >= end:
            start = end - timedelta(hours=18)
            window_source = "fallback_18h_calendar_window_invalid"

    included_dates = [day.isoformat() for day in _iter_dates(start.date(), end.date())]
    non_trading_in_window = False
    for day_text in included_dates:
        row = rows.get(day_text)
        if isinstance(row, Mapping) and not _calendar_row_is_trading_day(row):
            non_trading_in_window = True
            break
    if len(included_dates) > 2 and previous_trading_day is not None:
        non_trading_in_window = True

    return {
        "start": start,
        "end": end,
        "input_window_start_kst": start.isoformat(),
        "input_window_end_kst": end.isoformat(),
        "included_dates": included_dates,
        "non_trading_day_carryover": bool(non_trading_in_window),
        "previous_trading_day": previous_trading_day.isoformat() if previous_trading_day else None,
        "window_source": window_source,
    }


def _read_recent_pro_hourly_artifacts(
    data_root: Path,
    *,
    at: datetime,
    target_trade_date: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 48,
) -> List[Dict[str, Any]]:
    paths: List[Path] = []
    if start and end:
        candidate_days = {day.isoformat() for day in _iter_dates(start.date(), end.date())}
    else:
        candidate_days = {
            at.date().isoformat(),
            target_trade_date,
            (at - timedelta(days=1)).date().isoformat(),
        }
    for day in sorted(candidate_days):
        directory = data_root / "ai" / day
        if not directory.is_dir():
            continue
        paths.extend(
            p
            for p in directory.glob("pro-hourly-*.json")
            if p.is_file() and p.name != "pro-hourly-latest.json"
        )
        latest = directory / "pro-hourly-latest.json"
        if latest.is_file():
            paths.append(latest)

    rows: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in sorted(paths)[-limit * 2 :]:
        payload = _read_json_artifact(path)
        if not payload:
            continue
        timestamp = _artifact_timestamp(payload)
        if start and end and timestamp and not (start <= timestamp <= end):
            continue
        artifact_id = str(payload.get("artifact_id") or path)
        if artifact_id in seen_ids:
            continue
        seen_ids.add(artifact_id)
        rows.append(payload)
    return rows[-limit:]


def _build_morning_watchlist_prompt_text(
    *,
    target_trade_date: str,
    produced_at_kst: str,
    pro_artifacts: Sequence[Mapping[str, Any]],
    recent_events: Sequence[Mapping[str, Any]],
    kis_snapshots: Sequence[Mapping[str, Any]],
    compiled_watch: Sequence[Mapping[str, Any]],
    calendar_context: Mapping[str, Any],
    input_window: Mapping[str, Any],
) -> str:
    required_schema = {
        "schema_version": "morning_watchlist/v1",
        "reviewer": "chatgpt_pro",
        "route": "codex_cli_local_browser_use",
        "target_trade_date_kst": target_trade_date,
        "analysis_language": "ko-KR",
        "forbidden_actions_acknowledged": True,
        "market_open_plan": {
            "opening_bias": "selective_watch|defensive|no_trade_bias",
            "why": "한국어",
            "must_wait_for_market_confirmation": True,
            "first_flash_questions": ["한국어 질문"],
        },
        "items": [
            {
                "ticker": "000000",
                "name": "종목명",
                "stance": "eligible_for_flash_review|watch_only|avoid",
                "thesis": "한국어",
                "opening_trigger_conditions": ["한국어"],
                "invalidation_conditions": ["한국어"],
                "source_refs": [],
                "pro_refs": [],
                "confidence": 0.0,
            }
        ],
        "no_trade_reasons": [],
        "risk_notes": [],
    }
    pro_digest = [
        {
            "artifact_id": row.get("artifact_id"),
            "produced_at_kst": row.get("produced_at_kst") or row.get("generated_at_kst"),
            "validation_status": row.get("validation_status"),
            "document_kind": row.get("document_kind"),
            "summary": row.get("summary"),
            "market_regime": row.get("market_regime"),
            "theme_map": row.get("theme_map"),
            "flash_guidance": row.get("flash_guidance"),
            "questions_for_next_flash": row.get("questions_for_next_flash"),
            "source_refs": row.get("source_refs"),
            "market_data_refs": row.get("market_data_refs"),
        }
        for row in pro_artifacts[-8:]
    ]
    event_digest = [
        {
            "event_id": row.get("event_id") or row.get("source_id"),
            "event_type": row.get("event_type"),
            "title": row.get("title"),
            "published_at_kst": row.get("published_at_kst"),
            "collected_at_kst": row.get("collected_at_kst"),
            "query": row.get("query"),
        }
        for row in recent_events[-80:]
    ]
    watch_digest = [
        {
            "symbol": row.get("symbol") or row.get("ticker"),
            "name": row.get("name") or row.get("symbol_name"),
            "entry_intent": row.get("entry_intent"),
            "source_ids": row.get("source_ids") or row.get("source_refs"),
        }
        for row in compiled_watch[:20]
    ]
    return (
        "너는 hwiStock의 ChatGPT Pro 장전 감시목록 외부 분석자다. "
        "아래 입력만 근거로 삼아 morning_watchlist/v1 strict JSON object 하나만 반환해. "
        "Markdown, 설명문, 코드블록 금지. JSON 외 텍스트 금지. "
        "사람이 읽는 자연어 문자열 값은 모두 한국어로 작성하고, schema key/enum/ticker/route/source_ref/pro_ref 같은 기계값은 지정 형식 그대로 유지해. "
        "이 산출물은 주문이 아니라 09:00 첫 Flash가 검토할 감시목록이다. broker API 호출, 주문 제출, 수량/주문가/주문유형/직접 매수 지시 금지. "
        "후보는 입력된 Pro 분석, 뉴스/공시, compiled watch 근거 밖에서 만들지 마. 근거가 부족하면 top-level items를 빈 리스트([])로 두고 no_trade_reasons를 채워라. "
        "반드시 top-level `items` 키를 리스트로 사용하고, top-level `eligible_for_flash_review` 키는 만들지 마. "
        "`eligible_for_flash_review`는 오직 items[].stance 값으로만 사용해라. "
        "각 items 원소 중 stance=eligible_for_flash_review인 항목은 ticker, thesis, opening_trigger_conditions, invalidation_conditions, source_refs 또는 pro_refs, confidence를 반드시 포함해. "
        "market_open_plan.opening_bias, why, must_wait_for_market_confirmation, first_flash_questions를 반드시 포함해. "
        f"필수 JSON 스키마 예시={json.dumps(required_schema, ensure_ascii=False)} "
        f"target_trade_date_kst={target_trade_date}. produced_at_kst={produced_at_kst}. "
        f"input_window={json.dumps(dict(input_window), ensure_ascii=False)} "
        f"calendar_context={json.dumps(dict(calendar_context), ensure_ascii=False)} "
        f"pro_hourly_artifacts={json.dumps(_compact_json_for_prompt(pro_digest, 9000), ensure_ascii=False)} "
        f"recent_events={json.dumps(_compact_json_for_prompt(event_digest, 9000), ensure_ascii=False)} "
        f"kis_market_snapshots={json.dumps(_compact_json_for_prompt(list(kis_snapshots)[-6:], 6000), ensure_ascii=False)} "
        f"compiled_watch={json.dumps(_compact_json_for_prompt(watch_digest, 5000), ensure_ascii=False)}"
    )


def build_morning_watchlist_prompt(
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    target_trade_date: Optional[str] = None,
    at: Optional[datetime] = None,
    purpose: Optional[str] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    requested_target = str(target_trade_date or now.date().isoformat()).strip()
    gate = msg.evaluateKisCallGate(now_kst=now, call_family="gpt_morning", env=os.environ)
    input_window = _morning_prompt_input_window(target_trade_date=requested_target, at=now)
    start = input_window["start"]
    end = input_window["end"]
    events = _read_events_for_window(data_root, start=start, end=end, limit=240)
    kis_snapshots = _read_recent_kis_snapshots(data_root, at=now, limit=8)
    compiled_watch = _read_compiled_watch(data_root, at=now)
    pro_artifacts = _read_recent_pro_hourly_artifacts(
        data_root,
        at=now,
        target_trade_date=requested_target,
        start=start,
        end=end,
    )
    prompt_text = _build_morning_watchlist_prompt_text(
        target_trade_date=requested_target,
        produced_at_kst=now.isoformat(),
        pro_artifacts=pro_artifacts,
        recent_events=events,
        kis_snapshots=kis_snapshots,
        compiled_watch=compiled_watch,
        calendar_context=gate["calendar_context"],
        input_window={
            "start_kst": input_window["input_window_start_kst"],
            "end_kst": input_window["input_window_end_kst"],
            "included_dates": input_window["included_dates"],
            "non_trading_day_carryover": input_window["non_trading_day_carryover"],
        },
    )
    stamp = now.strftime("%H%M%S")
    prompt_paths: Dict[str, str] = {}
    for family, latest_name, stamped_name in (
        ("ai", "gpt-morning-prompt-latest.txt", f"gpt-morning-prompt-{stamp}.txt"),
        ("prompts", "gpt-morning-watchlist-latest.txt", f"gpt-morning-watchlist-{stamp}.txt"),
    ):
        output_dir = data_root / family / requested_target
        output_dir.mkdir(parents=True, exist_ok=True)
        latest_path = output_dir / latest_name
        stamped_path = output_dir / stamped_name
        tmp_path = latest_path.with_suffix(".tmp")
        tmp_path.write_text(prompt_text, encoding="utf-8")
        tmp_path.replace(latest_path)
        stamped_path.write_text(prompt_text, encoding="utf-8")
        prompt_paths[f"{family}_latest"] = str(latest_path)
        prompt_paths[f"{family}_stamped"] = str(stamped_path)

    evidence_dir = data_root / "evidence" / now.date().isoformat()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    health_path = evidence_dir / "gpt-morning-prompt-health.json"
    health = {
        "event": "gpt_morning_prompt_health",
        "timestamp_kst": now.isoformat(),
        "target_trade_date_kst": requested_target,
        "status": "ok",
        "schema_version": "gpt_morning_prompt/v0",
        "purpose": str(purpose or "morning_watchlist_0715_local_browser_use"),
        "input_window_start_kst": input_window["input_window_start_kst"],
        "input_window_end_kst": input_window["input_window_end_kst"],
        "included_dates": input_window["included_dates"],
        "non_trading_day_carryover": input_window["non_trading_day_carryover"],
        "previous_trading_day": input_window["previous_trading_day"],
        "input_window_source": input_window["window_source"],
        "prompt_paths": prompt_paths,
        "input_counts": {
            "pro_hourly_artifacts": len(pro_artifacts),
            "recent_events": len(events),
            "kis_market_snapshots": len(kis_snapshots),
            "compiled_watch_items": len(compiled_watch),
        },
        "orders_enabled": False,
        "broker_calls_enabled": False,
    }
    health_path.write_text(json.dumps(health, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "schema_version": "gpt_morning_prompt/v0",
        "status": "ok",
        "target_trade_date_kst": requested_target,
        "generated_at_kst": now.isoformat(),
        "purpose": health["purpose"],
        "input_window_start_kst": health["input_window_start_kst"],
        "input_window_end_kst": health["input_window_end_kst"],
        "included_dates": health["included_dates"],
        "non_trading_day_carryover": health["non_trading_day_carryover"],
        "previous_trading_day": health["previous_trading_day"],
        "input_window_source": health["input_window_source"],
        "prompt_paths": prompt_paths,
        "health_path": str(health_path),
        "input_counts": health["input_counts"],
        "orders_enabled": False,
        "broker_calls_enabled": False,
    }


def _morning_artifact_id(target_trade_date: str, now: datetime, suffix: str) -> str:
    return f"art_morning_watchlist_{target_trade_date.replace('-', '')}_{now.strftime('%H%M%S')}_{suffix}"


def _write_morning_watchlist_latest(
    payload: Mapping[str, Any],
    *,
    data_root: Path,
    target_trade_date: str,
    at: datetime,
) -> Dict[str, str]:
    text = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    stamp = at.strftime("%H%M%S")
    paths: Dict[str, str] = {}
    for family in ("morning-watchlist", "ai"):
        output_dir = data_root / family / target_trade_date
        output_dir.mkdir(parents=True, exist_ok=True)
        latest_path = output_dir / "morning-watchlist-latest.json"
        stamped_path = output_dir / f"morning-watchlist-{stamp}.json"
        tmp_path = latest_path.with_suffix(".tmp")
        tmp_path.write_text(text, encoding="utf-8")
        tmp_path.replace(latest_path)
        stamped_path.write_text(text, encoding="utf-8")
        paths[f"{family}_latest"] = str(latest_path)
        paths[f"{family}_stamped"] = str(stamped_path)
    evidence_dir = data_root / "evidence" / at.date().isoformat()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    health_path = evidence_dir / "morning-watchlist-publish-health.json"
    health_path.write_text(
        json.dumps(
            {
                "event": "morning_watchlist_publish_health",
                "timestamp_kst": at.isoformat(),
                "target_trade_date_kst": target_trade_date,
                "status": payload.get("validation_status") or payload.get("status"),
                "artifact_id": payload.get("artifact_id") or payload.get("safe_block_id"),
                "orders_enabled": False,
                "broker_calls_enabled": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["health"] = str(health_path)
    return paths


FORBIDDEN_MORNING_ORDER_FIELDS = {
    "entry_price_limit",
    "quantity",
    "order_type",
    "order_price",
    "broker_order_request",
    "order_request",
    "submit_order",
    "execution_route",
}


def _find_forbidden_morning_order_fields(value: Any, *, prefix: str = "") -> List[str]:
    hits: List[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in FORBIDDEN_MORNING_ORDER_FIELDS:
                hits.append(path)
            hits.extend(_find_forbidden_morning_order_fields(item, prefix=path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_find_forbidden_morning_order_fields(item, prefix=f"{prefix}[{index}]"))
    return hits


def _validate_morning_watchlist_payload(
    payload: Mapping[str, Any],
    *,
    requested_target: str,
) -> List[str]:
    errors: List[str] = []
    schema = str(payload.get("schema_version") or payload.get("schema") or "").strip()
    route = str(payload.get("route") or "").strip()
    payload_target = str(
        payload.get("target_trade_date_kst")
        or payload.get("trading_date_kst")
        or payload.get("trading_date")
        or requested_target
    ).strip()

    if schema != "morning_watchlist/v1":
        errors.append("schema_version_must_be_morning_watchlist_v1")
    if route != "codex_cli_local_browser_use":
        errors.append("route_must_be_codex_cli_local_browser_use")
    if payload_target != requested_target:
        errors.append("target_trade_date_mismatch")
    if payload.get("forbidden_actions_acknowledged") is not True:
        errors.append("forbidden_actions_acknowledged_required")
    if not str(payload.get("target_trade_date_kst") or "").strip():
        errors.append("target_trade_date_kst_required")
    if not isinstance(payload.get("market_open_plan"), Mapping):
        errors.append("market_open_plan_required")
    forbidden_fields = _find_forbidden_morning_order_fields(payload)
    if forbidden_fields:
        errors.append("executable_order_fields_forbidden:" + ",".join(sorted(forbidden_fields)[:8]))

    if "eligible_for_flash_review" in payload:
        errors.append("top_level_eligible_for_flash_review_forbidden")

    items = payload.get("items")
    if not isinstance(items, list):
        errors.append("items_must_be_list")
        items = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"items_{index}_must_be_object")
            continue
        stance = str(item.get("stance") or "").strip()
        if stance != "eligible_for_flash_review":
            continue
        if not str(item.get("ticker") or "").strip():
            errors.append(f"items_{index}_ticker_required")
        if not str(item.get("thesis") or "").strip():
            errors.append(f"items_{index}_thesis_required")
        if not item.get("opening_trigger_conditions"):
            errors.append(f"items_{index}_opening_trigger_conditions_required")
        if not item.get("invalidation_conditions"):
            errors.append(f"items_{index}_invalidation_conditions_required")
        if not item.get("source_refs") and not item.get("pro_refs"):
            errors.append(f"items_{index}_source_or_pro_refs_required")
        try:
            confidence = float(item.get("confidence"))
        except (TypeError, ValueError):
            errors.append(f"items_{index}_confidence_required")
        else:
            if confidence < 0 or confidence > 1:
                errors.append(f"items_{index}_confidence_invalid")
    return errors


def publish_morning_watchlist_artifact(
    *,
    payload: Optional[Mapping[str, Any]] = None,
    source_path: Optional[Path] = None,
    data_root: Path = DEFAULT_DATA_ROOT,
    target_trade_date: Optional[str] = None,
    at: Optional[datetime] = None,
    purpose: Optional[str] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    source_payload = dict(payload or {})
    if source_path is not None:
        source_payload = _read_json_artifact(source_path) or {}

    requested_target = str(
        target_trade_date
        or source_payload.get("target_trade_date_kst")
        or source_payload.get("trading_date_kst")
        or source_payload.get("trading_date")
        or now.date().isoformat()
    ).strip()
    artifact: Dict[str, Any]
    errors: List[str] = []

    if not source_payload:
        errors.append("missing_morning_watchlist_payload")
    else:
        errors.extend(
            _validate_morning_watchlist_payload(
                source_payload,
                requested_target=requested_target,
            )
        )

    if errors:
        artifact = {
            "schema_version": "morning_watchlist/v1",
            "artifact_type": "morning_watchlist_safe_block",
            "safe_block_id": _morning_artifact_id(requested_target, now, "safe_block"),
            "target_trade_date_kst": requested_target,
            "generated_at_kst": now.isoformat(),
            "route": "codex_cli_local_browser_use",
            "document_kind": "NO_TRADE",
            "no_trade_reason": "morning_watchlist_publish_validation_failed",
            "validation_errors": errors,
            "items": [],
            "forbidden_actions_acknowledged": True,
            "validation_status": "safe_block",
            "broker_calls_enabled": False,
            "orders_enabled": False,
        }
    else:
        artifact = dict(source_payload)
        artifact["schema_version"] = "morning_watchlist/v1"
        artifact["artifact_type"] = "morning_watchlist"
        artifact["artifact_id"] = str(
            artifact.get("artifact_id")
            or artifact.get("watchlist_id")
            or _morning_artifact_id(requested_target, now, "imported")
        )
        artifact["target_trade_date_kst"] = requested_target
        artifact["trading_date"] = requested_target
        artifact["generated_at_kst"] = str(artifact.get("generated_at_kst") or artifact.get("produced_at_kst") or now.isoformat())
        artifact["purpose"] = str(purpose or artifact.get("purpose") or "monday_preopen_import")
        artifact["route"] = "codex_cli_local_browser_use"
        artifact["forbidden_actions_acknowledged"] = artifact.get("forbidden_actions_acknowledged") is not False
        artifact["validation_status"] = "accepted"
        artifact["broker_calls_enabled"] = False
        artifact["orders_enabled"] = False

    artifact["artifact_paths"] = _write_morning_watchlist_latest(
        artifact,
        data_root=data_root,
        target_trade_date=requested_target,
        at=now,
    )
    return artifact


def _build_prompt(events: Sequence[Mapping[str, Any]], *, produced_at_kst: str) -> str:
    titles = [str(event.get("title") or "")[:120] for event in events if event.get("title")]
    return (
        "JSON만 출력. 설명 금지. 아래 한국 증시 뉴스 제목을 아주 짧게 요약해. "
        "summary, themes, risk_flags 같은 사람이 읽는 모든 문자열 값은 한국어로 작성해. "
        "schema key와 order_safety 같은 기계용 키/고정값은 지정 형식 그대로 유지해. "
        "매수/매도 추천 금지. 주문 금지. 수익 예측 금지. "
        "형식: {\"summary\":\"한문장\",\"themes\":[\"키워드1\",\"키워드2\"],"
        "\"risk_flags\":[\"위험1\"],\"order_safety\":\"no_order\"}. "
        f"시각={produced_at_kst}. "
        f"제목={json.dumps(titles, ensure_ascii=False)}"
    )


def _cluster_events_for_prompt(events: Sequence[Mapping[str, Any]], *, max_clusters: int = 10) -> List[Dict[str, Any]]:
    clusters: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for event in events:
        title = str(event.get("title") or "").strip()
        query = str(event.get("query") or "").strip()
        event_type = str(event.get("event_type") or "news").strip() or "news"
        key_seed = query or " ".join(title.split()[:2]) or event_type
        cluster_key = f"{event_type}:{key_seed}"[:80]
        if cluster_key not in clusters:
            clusters[cluster_key] = {
                "cluster_id": f"cluster_{len(order) + 1:02d}",
                "theme_hint": key_seed[:80],
                "representative_titles": [],
                "source_refs": [],
                "event_count": 0,
                "freshness": "last_1h",
            }
            order.append(cluster_key)
        cluster = clusters[cluster_key]
        cluster["event_count"] += 1
        if title and len(cluster["representative_titles"]) < 3:
            cluster["representative_titles"].append(title[:160])
        source_ref = str(event.get("event_id") or event.get("source_id") or event.get("source_event_id") or "").strip()
        if source_ref and source_ref not in cluster["source_refs"] and len(cluster["source_refs"]) < 5:
            cluster["source_refs"].append(source_ref[:100])
    ranked = sorted((clusters[key] for key in order), key=lambda row: int(row.get("event_count") or 0), reverse=True)
    return [dict(row) for row in ranked[:max_clusters]]


def _build_pro_hourly_prompt(
    events: Sequence[Mapping[str, Any]],
    kis_snapshots: Sequence[Mapping[str, Any]],
    *,
    produced_at_kst: str,
    calendar_context: Optional[Mapping[str, Any]] = None,
) -> str:
    top_news_clusters = _cluster_events_for_prompt(events, max_clusters=10)
    market_rows = []
    for snapshot in kis_snapshots[-6:]:
        market_rows.append(
            {
                "artifact_id": str(snapshot.get("artifact_id") or "")[:80],
                "status": str(snapshot.get("status") or ""),
                "inputs": [
                    {
                        "input_id": str(row.get("input_id") or row.get("step") or ""),
                        "status": str(row.get("status") or ""),
                        "row_count": row.get("row_count"),
                        "rows_preview": (row.get("rows_preview") or [])[:3],
                    }
                    for row in (snapshot.get("input_results") or [])[:6]
                    if isinstance(row, Mapping)
                ],
            }
        )
    required_schema = {
        "schema_version": "pro_hourly_market_analysis/v1",
        "document_kind": "MARKET_STRATEGY_CONTEXT",
        "analysis_language": "ko-KR",
        "order_safety": "no_order",
        "ai_direct_order_allowed": False,
        "input_window_kst": {"start_kst": "string", "end_kst": "string", "window_seconds": 3600},
        "data_quality": {
            "news_event_count": 0,
            "kis_market_snapshot_count": 0,
            "kis_artifact_count": 0,
            "kis_realtime_snapshot_count": 0,
            "kis_safe_skip_count": 0,
            "valid_market_confirmation_count": 0,
            "kis_data_status": "ok|partial|expected_off_session_no_realtime|off_session_context_only|missing|degraded",
            "market_confirmation_status": "confirmed|not_confirmed|awaiting_next_open|not_available",
            "runtime_kis_failure_evidence_present": False,
            "missing_inputs": [],
            "warnings": [],
        },
        "market_regime": {"mode": "RISK_ON|NEUTRAL|RISK_OFF|NO_TRADE", "confidence": 0.0, "why": []},
        "theme_map": [],
        "flash_guidance": {
            "preferred_bias": "aggressive|selective_watch|defensive|no_trade_bias",
            "max_aggression": "none|low|medium|high",
            "candidate_focus": [],
            "avoid_focus": [],
            "must_check_before_buy": [],
            "position_management_notes": [],
        },
        "no_trade_conditions": [],
        "contradiction_notes": [],
        "source_ref_map": [],
        "questions_for_next_flash": [],
        "investment_utility_status": "actionable_context|limited_context|news_only_low_utility|safe_block",
    }
    return (
        "JSON만 출력. 설명/Markdown 금지. "
        "너는 한국 주식 단기 paper 운용을 위한 1시간 시장 전략 분석가다. "
        "너는 주문하지 않고, 종목 매수/매도 지시를 직접 내리지 않는다. "
        "단순 뉴스 요약 금지. 뉴스/공시 클러스터와 통합 KIS 시장 데이터를 연결해 Flash 10분 매매문서가 사용할 전략 컨텍스트를 만들어라. "
        "사람이 읽는 자연어 문자열은 한국어로 쓰고, schema key/enum/source_ref/ticker 같은 기계값은 지정 형식 그대로 유지해. "
        "theme_map, flash_guidance, no_trade_conditions, contradiction_notes, source_ref_map, questions_for_next_flash를 반드시 채워라. "
        "calendar_context.kis_realtime_expected=false이면 KIS 실시간 부재는 정상 오프세션/휴장 상태로 취급하고 KIS 장애/수신 장애라고 쓰지 마. "
        "calendar_context.kis_realtime_expected=false 또는 market_context_open=false이면 data_quality.kis_data_status='ok' 금지; expected_off_session_no_realtime 또는 off_session_context_only를 써라. "
        "data_quality에는 kis_artifact_count, kis_realtime_snapshot_count, kis_safe_skip_count, valid_market_confirmation_count, market_confirmation_status를 반드시 분리해서 넣어라. "
        "runtime evidence에 실제 token/transport/provider failure가 있을 때만 KIS 실패라고 써라. "
        "summary/themes/risk_flags만 내면 news_only_low_utility로 간주된다. "
        "출력 hard cap: theme_map 최대 5개, source_ref_map 최대 5개, no_trade_conditions 최대 5개, questions_for_next_flash 최대 5개. "
        "각 theme/source_ref/no_trade item의 source_refs는 최대 3개, market_data_refs는 최대 3개. market_regime.why claim은 최대 2개. "
        "긴 설명 금지. 대표 ref만 넣고 provider JSON을 compact하게 유지해라. "
        "top_news_clusters는 압축된 입력이다. source_ref_map claim은 '최근 1시간 입력 묶음' 같은 비분석 문장을 쓰지 말고, 테마/종목군/확인조건을 연결한 판단 문장으로 써라. "
        "오프세션/휴장으로 calendar_context.kis_realtime_expected=false이면 market_confirmation_status=confirmed 금지; not_available, awaiting_next_open, carryover_only 중 하나를 써라. "
        "오프세션/휴장에서는 no_trade_conditions에 '개장 후 KRX 거래대금/체결강도 확인 전 BUY_NOW 금지'를 반드시 포함해라. "
        f"필수 JSON 스키마 예시={json.dumps(required_schema, ensure_ascii=False)} "
        f"시각={produced_at_kst}. "
        f"calendar_context={json.dumps(dict(calendar_context or {}), ensure_ascii=False)} "
        f"top_news_clusters={json.dumps(top_news_clusters, ensure_ascii=False)} "
        f"KIS요약={json.dumps(market_rows, ensure_ascii=False)}"
    )


def _build_flash_prompt(
    *,
    pro_artifact: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    kis_snapshots: Sequence[Mapping[str, Any]],
    compiled_watch: Sequence[Mapping[str, Any]],
    portfolio: Mapping[str, Any],
    order_state: Mapping[str, Any],
    produced_at_kst: str,
    morning_watchlist: Optional[Mapping[str, Any]] = None,
    calendar_context: Optional[Mapping[str, Any]] = None,
) -> str:
    watch_summary = [
        {
            "symbol": row.get("symbol") or row.get("ticker"),
            "name": row.get("name") or row.get("symbol_name"),
            "entry_intent": row.get("entry_intent"),
            "valid_until_kst": row.get("valid_until_kst"),
        }
        for row in compiled_watch[:5]
    ]
    required_schema = {
        "schema_version": "flash_trade_document/v1",
        "document_kind": "TRADE_ACTIONS|TRADE_ACTIONS_WITH_NO_NEW_ENTRY|POSITION_MANAGEMENT|NO_TRADE",
        "analysis_language": "ko-KR",
        "investment_mode": "paper|live",
        "market_analysis_feed_mode": "integrated",
        "execution_venue_mode": "krx_only",
        "order_safety": "no_direct_order",
        "ai_direct_broker_call_allowed": False,
        "actions": [
            {
                "symbol": "000000",
                "name": "string",
                "side": "BUY|SELL|HOLD|NO_TRADE",
                "action": "BUY_NOW|WAIT_BUY|SELL_NOW|WAIT_SELL|HOLD|NO_TRADE|NO_NEW_ENTRY|HOLD_EXISTING_POSITION|WAIT_ORDER_RECONCILIATION|EXIT_REVIEW",
                "quantity": 0,
                "planned_order_cash_krw": 0,
                "entry_price_limit": 0,
                "target_price": 0,
                "stop_loss_price": 0,
                "valid_from_kst": "string",
                "valid_until_kst": "string",
                "confidence": 0.0,
                "urgency": "low|medium|high",
                "thesis": "한국어",
                "why_now": "한국어",
                "required_confirmations": [],
                "cancel_if": [],
                "source_refs": [],
                "symbol_source_refs": [],
                "market_context_refs": [],
                "pro_refs": [],
                "pro_context_refs": [],
                "morning_watchlist_refs": [],
                "market_data_refs": [],
                "kis_market_refs": [],
                "rationale_type": "kis_market_data_momentum|symbol_news_and_market_data|deterministic_market_data_fallback",
                "news_backed": False,
                "source_quality_warnings": [],
            }
        ],
        "position_actions": [],
        "no_trade_reasons": [],
        "global_risk_flags": [],
        "operator_notes": [],
    }
    return (
        "JSON만 출력. 설명/Markdown 금지. "
        "너는 hwiStock의 10분 단위 매매문서 작성자다. broker API를 호출하지 않고 주문을 제출하지 않는다. "
        "latest Pro 전략 컨텍스트, GPT Pro morning watchlist, 지난 10분 뉴스/공시/KIS 통합시장데이터, 현재 보유/대기주문 상태를 보고 다음 10분 매매문서를 작성해라. "
        "compiled_watch 또는 morning_watchlist universe 밖 종목 생성 금지. paper mode는 KRX-only이며 09:00~15:00 KST 신규 주문/진입만 허용. "
        "15:00 이후 신규 BUY/SELL 금지. 보유/대기주문과 충돌하는 신규 BUY 금지. 이때 NO_TRADE로 뭉개지 말고 NO_NEW_ENTRY, HOLD_EXISTING_POSITION, WAIT_ORDER_RECONCILIATION, EXIT_REVIEW로 표현해라. "
        "NO_TRADE는 후보 없음/시장 위험/입력 부족/장외 같은 진짜 거래 없음에만 사용해라. 최대 보유 5개와 총예수금 75% exposure cap을 고려. "
        "불확실하면 WAIT_BUY 또는 NO_NEW_ENTRY/HOLD_EXISTING_POSITION. source_refs/pro_refs/market_data_refs 없는 BUY_NOW 금지. target_price/stop_loss_price 없는 BUY_NOW 금지. quantity:0 BUY_NOW 금지. "
        "BUY 근거는 symbol_source_refs(해당 종목 직접 뉴스/공시), market_context_refs(일반 뉴스/정책/매크로), kis_market_refs(KIS rank/현재가/거래량), pro_context_refs, morning_watchlist_refs로 분리해라. "
        "종목 직접 뉴스가 없고 KIS 시장데이터만 있으면 rationale_type=kis_market_data_momentum, news_backed=false, source_quality_warnings에 no_symbol_specific_news_refs를 넣어라. "
        "각 action은 thesis, why_now, required_confirmations, cancel_if, confidence, urgency, refs를 반드시 포함해야 한다. "
        "사람이 읽는 자연어 문자열은 한국어로 쓰고, schema key/enum/symbol 숫자 필드는 지정 형식 그대로 유지해. "
        "calendar_context.kis_realtime_expected=false이면 KIS 실시간 부재를 장애/제공자 실패로 쓰지 말고 오프세션 정상 상태로 처리해. "
        f"필수 JSON 스키마 예시={json.dumps(required_schema, ensure_ascii=False)} "
        f"시각={produced_at_kst}. "
        f"calendar_context={json.dumps(dict(calendar_context or {}), ensure_ascii=False)} "
        f"Pro분석={json.dumps(_compact_json_for_prompt(pro_artifact, 3500), ensure_ascii=False)} "
        f"MorningWatchlist={json.dumps(_compact_json_for_prompt(dict(morning_watchlist or {}), 2500), ensure_ascii=False)} "
        f"최근뉴스={json.dumps(list(events)[-20:], ensure_ascii=False)} "
        f"KIS스냅샷={json.dumps(_compact_json_for_prompt(list(kis_snapshots)[-4:], 3500), ensure_ascii=False)} "
        f"후보={json.dumps(watch_summary, ensure_ascii=False)} "
        f"포트폴리오={json.dumps(_compact_json_for_prompt(portfolio, 1600), ensure_ascii=False)} "
        f"주문상태={json.dumps(_compact_json_for_prompt(order_state, 1600), ensure_ascii=False)}"
    )


def _compact_json_for_prompt(value: Any, max_chars: int) -> Any:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(text) <= max_chars:
        return value
    return {"truncated_json": text[:max_chars], "truncated": True}


def _parse_provider_json(text: str) -> Dict[str, Any]:
    raw = str(text or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _provider_action_rows(provider_json: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows = provider_json.get("actions")
    if not isinstance(rows, list):
        rows = provider_json.get("trade_actions")
    if not isinstance(rows, list):
        rows = provider_json.get("candidate_actions")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows[:5] if isinstance(row, Mapping)]


def _provider_meta(provider: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if not provider:
        return None
    return {
        "http_status": provider.get("http_status"),
        "finish_reason": provider.get("finish_reason"),
        "model": provider.get("model"),
        "usage": provider.get("usage"),
        "error": provider.get("error"),
        "request": provider.get("request"),
        "warnings": provider.get("warnings"),
        "text_present": bool(str(provider.get("text") or "").strip()),
    }


def _apply_provider_runtime_warnings(artifact: Dict[str, Any], provider: Optional[Mapping[str, Any]]) -> None:
    if not provider or not isinstance(provider.get("warnings"), list):
        return
    warnings = artifact.setdefault("warnings", [])
    if not isinstance(warnings, list):
        return
    for warning in provider["warnings"]:
        text = str(warning or "").strip()
        if text and text not in warnings:
            warnings.append(text)


def _provider_claims_kis_failure(provider_json: Mapping[str, Any]) -> bool:
    if not provider_json:
        return False
    rendered = json.dumps(provider_json, ensure_ascii=False).lower()
    kis_tokens = ("kis", "한국투자", "실시간", "realtime")
    failure_tokens = (
        "장애",
        "실패",
        "오류",
        "에러",
        "미수신",
        "불능",
        "failure",
        "failed",
        "error",
        "unavailable",
    )
    return any(token in rendered for token in kis_tokens) and any(token in rendered for token in failure_tokens)


def _drop_kis_failure_claims(values: Any) -> Any:
    if not isinstance(values, list):
        return values
    kept = []
    for item in values:
        text = json.dumps(item, ensure_ascii=False).lower()
        if _provider_claims_kis_failure({"value": text}):
            continue
        kept.append(item)
    return kept


def _apply_off_session_provider_guard(
    artifact: Dict[str, Any],
    *,
    provider_json: Mapping[str, Any],
    calendar_context: Mapping[str, Any],
) -> None:
    if bool(calendar_context.get("kis_realtime_expected")) or not _provider_claims_kis_failure(provider_json):
        return
    warning = "provider_misclassified_expected_off_session_as_kis_failure"
    warnings = artifact.setdefault("warnings", [])
    if isinstance(warnings, list) and warning not in warnings:
        warnings.append(warning)
    for key in ("risk_flags", "avoid_conditions"):
        if key in artifact:
            artifact[key] = _drop_kis_failure_claims(artifact.get(key))
    for key in ("summary", "provider_summary"):
        if key in artifact and _provider_claims_kis_failure({key: artifact.get(key)}):
            artifact[key] = "장 운영시간 밖이라 KIS 실시간 부재는 정상 상태로 처리했습니다."
    artifact["provider_guard"] = {
        "status": "downgraded_expected_off_session",
        "warning": warning,
        "kis_realtime_expected": False,
        "calendar_reason": calendar_context.get("reason"),
    }
    data_quality = artifact.get("data_quality")
    if isinstance(data_quality, dict):
        data_quality["kis_data_status"] = "expected_off_session_no_realtime"
        data_quality["runtime_kis_failure_evidence_present"] = False
        dq_warnings = data_quality.setdefault("warnings", [])
        if isinstance(dq_warnings, list) and warning not in dq_warnings:
            dq_warnings.append(warning)


def _provider_status(provider: Mapping[str, Any]) -> str:
    error = provider.get("error")
    if isinstance(error, Mapping) and error.get("code") == "missing_deepseek_api_key":
        return "blocked_missing_deepseek_api_key"
    if error:
        return "provider_failed"
    if provider.get("finish_reason") == "length":
        return "provider_output_truncated"
    if provider.get("finish_reason") == "stop" and str(provider.get("text") or "").strip():
        return "ok"
    if provider.get("http_status") == 200 and str(provider.get("text") or "").strip():
        return "ok"
    return "provider_failed"


def _apply_pro_provider_json(artifact: Dict[str, Any], provider_json: Mapping[str, Any]) -> None:
    if not provider_json:
        return
    normalized_provider = ao.normalizeProHourlyOutputCaps(provider_json)
    artifact["provider_json"] = dict(normalized_provider)
    if str(normalized_provider.get("summary") or "").strip():
        artifact["summary"] = str(normalized_provider["summary"])[:1000]
    if normalized_provider.get("schema_version") == "pro_hourly_market_analysis/v1":
        for key in (
            "document_kind",
            "input_window_kst",
            "data_quality",
            "market_regime",
            "theme_map",
            "flash_guidance",
            "no_trade_conditions",
            "contradiction_notes",
            "source_ref_map",
            "questions_for_next_flash",
            "investment_utility_status",
        ):
            value = normalized_provider.get(key)
            if isinstance(value, (dict, list)) or (isinstance(value, str) and value.strip()):
                artifact[key] = value
        artifact["schema_version"] = "pro_hourly_market_analysis/v1"
        artifact["analysis_language"] = "ko-KR"
        artifact["order_safety"] = "no_order"
        artifact["ai_direct_order_allowed"] = False
        return

    themes = normalized_provider.get("themes")
    if isinstance(themes, list):
        artifact["themes"] = [str(item)[:80] for item in themes[:12]]
    risk_flags = normalized_provider.get("risk_flags")
    if isinstance(risk_flags, list):
        artifact["risk_flags"] = [str(item)[:120] for item in risk_flags[:12]]
    strong = normalized_provider.get("strong_conditions")
    if isinstance(strong, list):
        artifact["strong_conditions"] = [str(item)[:120] for item in strong[:12]]
    avoid = normalized_provider.get("avoid_conditions")
    if isinstance(avoid, list):
        artifact["avoid_conditions"] = [str(item)[:120] for item in avoid[:12]]
    market_mode = str(normalized_provider.get("market_mode") or "").strip()
    if market_mode:
        regime = artifact.setdefault("market_regime", {})
        if isinstance(regime, dict):
            regime["mode"] = market_mode[:40]
            regime["market_mode"] = market_mode[:40]
    artifact["investment_utility_status"] = "news_only_low_utility"
    warnings = artifact.setdefault("warnings", [])
    if isinstance(warnings, list) and "pro_hourly_low_utility_news_only" not in warnings:
        warnings.append("pro_hourly_low_utility_news_only")


def _is_pro_hourly_off_session(calendar_context: Mapping[str, Any]) -> bool:
    return (
        calendar_context.get("kis_realtime_expected") is False
        or calendar_context.get("market_context_open") is False
        or calendar_context.get("is_trading_day") is False
    )


def _pro_hourly_calendar_context(calendar_context: Mapping[str, Any], at: datetime) -> Dict[str, Any]:
    result = dict(calendar_context or {})
    at_kst = at.astimezone(KST)
    if at_kst.weekday() >= 5 and _is_pro_hourly_off_session(result):
        if "raw_calendar_status" not in result and result.get("calendar_status"):
            result["raw_calendar_status"] = result.get("calendar_status")
        raw_reason = result.get("calendar_reason") or result.get("reason")
        if "raw_calendar_reason" not in result and raw_reason:
            result["raw_calendar_reason"] = raw_reason
        result["calendar_status"] = "derived_weekend_non_trading"
        result["calendar_reason"] = "weekend_non_trading_day"
        result["reason"] = "weekend_non_trading_day"
        result["non_trading_reason"] = "weekend_non_trading_day"
        result["is_trading_day"] = False
        result["market_context_open"] = False
        result["broker_order_open"] = False
        result["kis_realtime_expected"] = False
        result["route_venue"] = result.get("route_venue") or "idle"
    return result


def _merge_pro_kis_data_quality_counts(
    artifact: Dict[str, Any],
    *,
    kis_snapshots: Sequence[Mapping[str, Any]],
    calendar_context: Mapping[str, Any],
) -> None:
    data_quality = artifact.setdefault("data_quality", {})
    if not isinstance(data_quality, dict):
        data_quality = {}
        artifact["data_quality"] = data_quality
    counts = ao._kis_snapshot_counts([dict(row) for row in kis_snapshots])  # noqa: SLF001
    data_quality["kis_market_snapshot_count"] = len(kis_snapshots)
    for key, value in counts.items():
        data_quality[key] = value
    if _is_pro_hourly_off_session(calendar_context):
        if str(data_quality.get("kis_data_status") or "").strip() in {
            "",
            "ok",
            "partial",
            "missing",
            "degraded",
            "expected_off_session",
        }:
            data_quality["kis_data_status"] = "expected_off_session_no_realtime"
        if data_quality.get("valid_market_confirmation_count", 0) <= 0:
            data_quality["market_confirmation_status"] = "not_confirmed"
        dq_warnings = data_quality.setdefault("warnings", [])
        if isinstance(dq_warnings, list) and "off_session_no_realtime_expected" not in dq_warnings:
            dq_warnings.append("off_session_no_realtime_expected")


def _deepseek_api_key() -> str:
    return (
        os.getenv("HWISTOCK_DEEPSEEK_API_KEY", "").strip()
        or os.getenv("DEEPSEEK_API_KEY", "").strip()
    )


def _deepseek_chat_url() -> str:
    base_url = os.getenv("HWISTOCK_DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).strip()
    base_url = (base_url or DEFAULT_DEEPSEEK_BASE_URL).rstrip("/")
    return f"{base_url}/chat/completions"


def _deepseek_system_prompt(job: str) -> str:
    if job == "pro-hourly":
        return (
            "You produce Korean JSON strategy context for a Korean stock paper-trading analysis pipeline. "
            "Do not submit or recommend broker orders. Do not summarize only. "
            "Map evidence to market regime, themes, confirmations, risks, and Flash guidance."
        )
    if job == "flash-10m":
        return (
            "You produce Korean JSON trade documents for a deterministic paper-trading runner. "
            "You do not call broker APIs. The runner will validate all actions. "
            "Every action must be source-grounded, time-bounded, and risk-bounded."
        )
    return "You write compact Korean JSON market-intelligence summaries. Never recommend or place orders."


def _parse_max_tokens_env(name: str) -> Optional[int]:
    raw = str(os.getenv(name) or "").strip()
    if not raw:
        return None
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _deepseek_max_tokens_override(job: str) -> tuple[Optional[int], Optional[str], List[str]]:
    normalized_job = str(job or "legacy-summary").strip() or "legacy-summary"
    warnings: List[str] = []
    for name in (
        DEEPSEEK_JOB_MAX_TOKENS_OVERRIDE_ENVS.get(normalized_job),
        DEEPSEEK_MAX_TOKENS_OVERRIDE_ENV,
    ):
        if not name:
            continue
        value = _parse_max_tokens_env(name)
        if value is not None:
            return value, name, warnings

    legacy_candidates = [
        "HWISTOCK_AI_MAX_OUTPUT_TOKENS",
        DEPRECATED_DEEPSEEK_MAX_TOKENS_ENVS.get(normalized_job),
    ]
    for name in legacy_candidates:
        if not name:
            continue
        value = _parse_max_tokens_env(name)
        if value is not None:
            warnings.append(f"deprecated_max_tokens_env:{name}")
            return value, name, warnings
    return None, None, warnings


def _call_deepseek(
    prompt: str,
    *,
    model: str,
    timeout: int = 90,
    job: str = "legacy-summary",
) -> Dict[str, Any]:
    max_tokens, max_tokens_source, max_token_warnings = _deepseek_max_tokens_override(job)
    request_meta = {
        "max_tokens_sent": max_tokens is not None,
        "max_tokens_source_env": max_tokens_source,
        "deprecated_warnings": list(max_token_warnings),
    }
    api_key = _deepseek_api_key()
    if not api_key:
        return {
            "http_status": None,
            "finish_reason": None,
            "model": model,
            "text": "",
            "usage": None,
            "error": {"code": "missing_deepseek_api_key"},
            "request": request_meta,
            "warnings": list(max_token_warnings),
        }

    thinking_mode = os.getenv("HWISTOCK_DEEPSEEK_THINKING", "disabled").strip().lower()
    request_body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": _deepseek_system_prompt(job),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    if max_tokens is not None:
        request_body["max_tokens"] = max_tokens
    if thinking_mode in {"enabled", "disabled"}:
        request_body["thinking"] = {"type": thinking_mode}
    data = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        _deepseek_chat_url(),
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    parsed: Dict[str, Any]
    try:
        parsed = json.loads(raw.decode("utf-8", errors="replace")) if raw else {}
    except json.JSONDecodeError:
        parsed = {"parse_error": True}
    choices = parsed.get("choices") if isinstance(parsed, Mapping) else None
    choice = choices[0] if isinstance(choices, list) and choices else {}
    message = choice.get("message") if isinstance(choice, Mapping) else {}
    return {
        "http_status": status,
        "finish_reason": choice.get("finish_reason") if isinstance(choice, Mapping) else None,
        "model": parsed.get("model"),
        "text": str(message.get("content") or "") if isinstance(message, Mapping) else "",
        "usage": parsed.get("usage"),
        "error": parsed.get("error"),
        "request": request_meta,
        "warnings": list(max_token_warnings),
    }


def _write_artifact_bundle(
    payload: Mapping[str, Any],
    *,
    data_root: Path,
    at: datetime,
    family: str,
    latest_name: str,
) -> Dict[str, str]:
    output_dir = _date_dir(data_root, family, at)
    evidence_dir = _date_dir(data_root, "evidence", at)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stamp = at.strftime("%H%M%S")
    stamped_path = output_dir / f"{latest_name.replace('-latest', '')}-{stamp}.json"
    latest_path = output_dir / f"{latest_name}.json"
    health_path = evidence_dir / f"{latest_name}-health.json"
    payload_to_write = _with_quality_metadata(payload)
    text = json.dumps(payload_to_write, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp_path = latest_path.with_suffix(".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(latest_path)
    stamped_path.write_text(text, encoding="utf-8")
    health_path.write_text(
        json.dumps(
            {
                "event": f"{latest_name}_health",
                "timestamp_kst": at.isoformat(),
                "status": payload_to_write.get("validation_status") or payload_to_write.get("status"),
                "artifact_path": str(latest_path),
                "schema_version": payload_to_write.get("schema_version"),
                "model_name": payload_to_write.get("model_name"),
                "quality_degraded": payload_to_write.get("quality_degraded") is True,
                "flash_usable": payload_to_write.get("flash_usable"),
                "warnings": payload_to_write.get("validation_warnings") or payload_to_write.get("warnings") or [],
                "orders_enabled": False,
                "broker_calls_enabled": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"latest": str(latest_path), "stamped": str(stamped_path), "health": str(health_path)}


def _dedupe_texts(values: Sequence[Any]) -> List[str]:
    seen: set[str] = set()
    rows: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        rows.append(text)
    return rows


def _artifact_warnings(payload: Mapping[str, Any]) -> List[str]:
    warnings: List[Any] = []
    for key in ("validation_warnings", "warnings"):
        value = payload.get(key)
        if isinstance(value, list):
            warnings.extend(value)
    return _dedupe_texts(warnings)


def _quality_degraded(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("validation_status") == "accepted_with_warnings"
        or payload.get("flash_usable") is False
        or str(payload.get("investment_utility_status") or "") in {"news_only_low_utility", "truncated_low_utility"}
    )


def _with_quality_metadata(payload: Mapping[str, Any]) -> Dict[str, Any]:
    result = dict(payload)
    warnings = _artifact_warnings(result)
    degraded = _quality_degraded(result)
    result["quality_degraded"] = bool(degraded)
    if degraded:
        result["flash_usable"] = False
        result["warnings"] = warnings
        result["validation_warnings"] = warnings
    return result


def _latest_named_json(data_root: Path, family: str, day: str, name: str) -> Optional[Path]:
    path = data_root / family / day / name
    return path if path.is_file() else None


def _read_previous_trade_documents(data_root: Path, *, at: datetime, limit: int = 3) -> List[Dict[str, Any]]:
    directory = data_root / "trade-documents" / at.date().isoformat()
    if not directory.is_dir():
        return []
    rows: List[Dict[str, Any]] = []
    for path in sorted(directory.glob("flash-trade-document-*.json"))[-limit:]:
        if path.name.endswith("-latest.json"):
            continue
        payload = _read_json_artifact(path)
        if payload:
            rows.append(payload)
    return rows[-limit:]


def _default_portfolio_snapshot(now: datetime) -> Dict[str, Any]:
    return {
        "schema_version": "portfolio_snapshot/v0",
        "artifact_id": f"art_portfolio_policy_snapshot_{now.strftime('%Y%m%d_%H%M%S')}",
        "snapshot_id": f"portfolio_policy_snapshot_{now.strftime('%Y%m%d_%H%M%S')}",
        "produced_at_kst": now.isoformat(),
        "source": "policy_budget_snapshot_for_paper_sizing",
        "available_cash_krw": 2_000_000,
        "total_capital_krw": 2_000_000,
        "holdings": [],
        "credential_values_printed": False,
        "raw_account_displayed": False,
        "fake_broker_used": False,
    }


def _default_order_state_snapshot(now: datetime, *, data_root: Path = DEFAULT_DATA_ROOT) -> Dict[str, Any]:
    state_path = data_root / "state" / "kis-paper-runner-state.json"
    pending_orders: list[Dict[str, Any]] = []
    holdings: list[Dict[str, Any]] = []
    active_exits: list[Dict[str, Any]] = []
    consumed_ids: list[str] = []
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
        if isinstance(state, Mapping):
            pending_orders = [
                dict(row)
                for row in (state.get("pending_orders") or [])
                if isinstance(row, Mapping)
            ]
            holdings = [
                dict(row)
                for row in (state.get("holdings") or [])
                if isinstance(row, Mapping)
            ]
            active_exits = [
                dict(row)
                for row in (state.get("active_exits") or [])
                if isinstance(row, Mapping)
            ]
            consumed_ids = [
                str(item)
                for item in (state.get("consumed_trade_document_ids") or state.get("consumed_intent_keys") or [])
                if str(item).strip()
            ]
    return {
        "schema_version": "order_state_snapshot/v0",
        "artifact_id": f"art_order_state_local_snapshot_{now.strftime('%Y%m%d_%H%M%S')}",
        "snapshot_id": f"order_state_local_snapshot_{now.strftime('%Y%m%d_%H%M%S')}",
        "produced_at_kst": now.isoformat(),
        "source": "local_kis_paper_runner_state",
        "pending_orders": pending_orders,
        "holdings": holdings,
        "active_exits": active_exits,
        "cooldowns": [],
        "consumed_trade_document_ids": consumed_ids,
        "credential_values_printed": False,
        "fake_broker_used": False,
    }


def _read_existing_intents(data_root: Path, *, at: datetime) -> List[Dict[str, Any]]:
    path = data_root / "intents" / at.date().isoformat() / "paper-order-intents-latest.jsonl"
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, Mapping):
            rows.append(dict(parsed))
    return rows


def _write_paper_intents(
    pipeline: Mapping[str, Any],
    *,
    data_root: Path,
    at: datetime,
) -> Dict[str, str]:
    output_dir = _date_dir(data_root, "intents", at)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = at.strftime("%H%M%S")
    latest_jsonl = output_dir / "paper-order-intents-latest.jsonl"
    stamped_jsonl = output_dir / f"paper-order-intents-{stamp}.jsonl"
    latest_pipeline = output_dir / "paper-order-intent-pipeline-latest.json"
    stamped_pipeline = output_dir / f"paper-order-intent-pipeline-{stamp}.json"
    intents = [
        dict(row)
        for row in (pipeline.get("accepted_intents") or [])
        if isinstance(row, Mapping)
    ]
    jsonl = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in intents)
    latest_jsonl.write_text(jsonl, encoding="utf-8")
    stamped_jsonl.write_text(jsonl, encoding="utf-8")
    text = json.dumps(dict(pipeline), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    latest_pipeline.write_text(text, encoding="utf-8")
    stamped_pipeline.write_text(text, encoding="utf-8")
    return {
        "latest_jsonl": str(latest_jsonl),
        "stamped_jsonl": str(stamped_jsonl),
        "latest_pipeline": str(latest_pipeline),
        "stamped_pipeline": str(stamped_pipeline),
    }


def run_pro_hourly_once(
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    at: Optional[datetime] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    gate = msg.evaluateKisCallGate(now_kst=now, call_family="pro_hourly", env=os.environ)
    raw_calendar_context = gate["calendar_context"]
    calendar_context = _pro_hourly_calendar_context(raw_calendar_context, now)
    events, input_window = _read_events_for_hour_window(data_root, at=now)
    kis_snapshots = _read_recent_kis_snapshots(data_root, at=now)
    selected_model = model or os.getenv("HWISTOCK_DEEPSEEK_MODEL", ao.DEEPSEEK_PRO_MODEL)
    provider: Optional[Dict[str, Any]] = None
    provider_json: Dict[str, Any] = {}
    if events or kis_snapshots:
        try:
            provider = _call_deepseek(
                _build_pro_hourly_prompt(
                    events,
                    kis_snapshots,
                    produced_at_kst=now.isoformat(),
                    calendar_context=calendar_context,
                ),
                model=selected_model,
                job="pro-hourly",
            )
            provider_json = _parse_provider_json(str(provider.get("text") or ""))
            provider_status = _provider_status(provider)
        except Exception as exc:  # noqa: BLE001 - fail closed and keep evidence.
            provider = {"error": {"code": "provider_exception", "class": exc.__class__.__name__, "message": str(exc)[:200]}}
            provider_status = "provider_error"
    else:
        provider_status = "blocked_no_source_inputs"
    artifact = ao.buildProHourlyMarketAnalysis(
        events=events,
        kis_market_snapshots=kis_snapshots,
        produced_at_kst=now.isoformat(),
        provider_status=provider_status,
        input_window_kst=input_window,
    )
    artifact["calendar_context"] = calendar_context
    artifact["kis_call_gate"] = gate["evidence_payload"]
    artifact["model_name"] = selected_model
    artifact["provider"] = _provider_meta(provider)
    _apply_provider_runtime_warnings(artifact, provider)
    if provider_json:
        _apply_pro_provider_json(artifact, provider_json)
        _apply_off_session_provider_guard(
            artifact,
            provider_json=provider_json,
            calendar_context=calendar_context,
        )
    _merge_pro_kis_data_quality_counts(
        artifact,
        kis_snapshots=kis_snapshots,
        calendar_context=calendar_context,
    )
    if provider_status not in {"ok", "blocked_no_source_inputs", "provider_output_truncated"}:
        artifact["validation_status"] = "safe_block"
        artifact["document_kind"] = "NO_TRADE"
        artifact["market_regime"]["mode"] = "NO_TRADE"
        artifact["market_regime"]["market_mode"] = "NO_TRADE"
        artifact["safe_block_reason"] = provider_status
        artifact["investment_utility_status"] = "safe_block"
        artifact["no_trade_conditions"] = [
            {
                "condition": "Pro hourly provider unavailable",
                "reason": provider_status,
                "source_refs": artifact.get("source_refs") or [],
                "market_data_refs": artifact.get("market_data_refs") or [],
            }
        ]
    pro_validation = ao.validateProHourlyMarketAnalysis(artifact)
    artifact = pro_validation["document"]
    artifact["validation_errors"] = pro_validation["errors"]
    artifact["validation_warnings"] = pro_validation["warnings"]
    artifact = _with_quality_metadata(artifact)
    artifact["artifact_paths"] = _write_artifact_bundle(
        artifact,
        data_root=data_root,
        at=now,
        family="ai",
        latest_name="pro-hourly-latest",
    )
    return artifact


def run_flash_trade_document_once(
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    at: Optional[datetime] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    gate = msg.evaluateKisCallGate(now_kst=now, call_family="pro_hourly", env=os.environ)
    calendar_context = gate["calendar_context"]
    day = now.date().isoformat()
    latest_pro_path = (
        _latest_named_json(data_root, "ai", day, "pro-hourly-latest.json")
        or _latest_json_file(data_root, "ai", day)
    )
    pro_artifact = _read_json_artifact(latest_pro_path) if latest_pro_path else None
    events, flash_input_window = _read_events_for_flash_window(data_root, at=now)
    kis_snapshots = _read_kis_snapshots_for_window(data_root, at=now)
    compiled_watch = _read_compiled_watch(data_root, at=now)
    portfolio = _read_json_artifact(_latest_json_file(data_root, "portfolio", day) or Path()) or _default_portfolio_snapshot(now)
    order_state = _read_json_artifact(_latest_json_file(data_root, "orders", day) or Path()) or _default_order_state_snapshot(now, data_root=data_root)
    previous_docs = _read_previous_trade_documents(data_root, at=now)
    morning_watchlist = _read_morning_watchlist(data_root, at=now)
    selected_model = model or os.getenv("HWISTOCK_DEEPSEEK_MODEL", ao.DEEPSEEK_FLASH_MODEL)
    provider: Optional[Dict[str, Any]] = None
    provider_json: Dict[str, Any] = {}
    flash_candidate_universe = compiled_watch or ao.buildProvisionalCompiledWatchFromMorningWatchlist(
        morning_watchlist,
        produced_at_kst=now.isoformat(),
    )
    if pro_artifact and flash_candidate_universe and (events or kis_snapshots or morning_watchlist):
        try:
            provider = _call_deepseek(
                _build_flash_prompt(
                    pro_artifact=pro_artifact,
                    events=events,
                    kis_snapshots=kis_snapshots,
                    compiled_watch=flash_candidate_universe,
                    portfolio=portfolio,
                    order_state=order_state,
                    produced_at_kst=now.isoformat(),
                    morning_watchlist=morning_watchlist,
                    calendar_context=calendar_context,
                ),
                model=selected_model,
                timeout=60,
                job="flash-10m",
            )
            provider_json = _parse_provider_json(str(provider.get("text") or ""))
        except Exception as exc:  # noqa: BLE001
            provider = {"error": {"code": "provider_exception", "class": exc.__class__.__name__, "message": str(exc)[:200]}}
    artifact = ao.buildFlashTradeDocument(
        pro_artifact=pro_artifact,
        recent_events=events,
        kis_market_snapshots=kis_snapshots,
        compiled_watch=compiled_watch,
        portfolio_snapshot=portfolio,
        order_state_snapshot=order_state,
        previous_trade_documents=previous_docs,
        morning_watchlist=morning_watchlist,
        provider_actions=_provider_action_rows(provider_json),
        investment_mode=rp.runtimePolicyFromEnv(os.environ)["investment_mode"],
        market_analysis_feed_mode=rp.runtimePolicyFromEnv(os.environ)["market_analysis_feed_mode"],
        execution_venue_mode=rp.runtimePolicyFromEnv(os.environ)["execution_venue_mode"],
        input_window_kst=flash_input_window,
        produced_at_kst=now.isoformat(),
    )
    artifact["calendar_context"] = calendar_context
    artifact["kis_call_gate"] = gate["evidence_payload"]
    artifact["model_name"] = selected_model
    artifact["provider_status"] = _provider_status(provider or {}) if provider else "blocked_no_flash_provider_inputs"
    artifact["provider"] = _provider_meta(provider)
    _apply_provider_runtime_warnings(artifact, provider)
    market_context = artifact.get("market_context")
    if isinstance(market_context, dict):
        market_context["market_context_open"] = bool(calendar_context.get("market_context_open"))
        market_context["broker_order_open"] = bool(calendar_context.get("broker_order_open"))
        market_context["kis_realtime_expected"] = bool(calendar_context.get("kis_realtime_expected"))
    if provider_json:
        artifact["provider_json"] = provider_json
        notes = provider_json.get("candidate_notes")
        if isinstance(notes, list):
            artifact["provider_candidate_notes"] = notes[:5]
        if str(provider_json.get("summary") or "").strip():
            artifact["provider_summary"] = str(provider_json["summary"])[:1000]
        _apply_off_session_provider_guard(
            artifact,
            provider_json=provider_json,
            calendar_context=calendar_context,
        )
    validation = ao.validateFlashTradeDocument(artifact, compiled_watch=flash_candidate_universe)
    artifact = validation["document"]
    artifact["validation_errors"] = validation["errors"]
    artifact = _with_quality_metadata(artifact)
    if artifact.get("validation_status") == "accepted":
        pipeline = trading_engine.generatePaperOrderIntentsFromFlashDocument(
            artifact,
            compiled_watch=flash_candidate_universe,
            portfolio_snapshot=portfolio,
            order_state_snapshot=order_state,
            existing_intents=_read_existing_intents(data_root, at=now),
            now_kst=now.isoformat(),
        )
    else:
        pipeline = {
            "schema_version": "paper_intent_pipeline_result/v0",
            "ok": artifact.get("validation_status") in {"safe_block", "accepted", "accepted_with_warnings"},
            "accepted_intents": [],
            "rejected_actions": [{"reason": artifact.get("no_trade_reason") or "flash_document_not_accepted"}],
            "accepted_count": 0,
            "rejected_count": 1,
            "order_cancel_modify_called": False,
        }
    artifact["paper_intent_pipeline"] = pipeline
    artifact["paper_intent_paths"] = _write_paper_intents(pipeline, data_root=data_root, at=now)
    artifact["artifact_paths"] = _write_artifact_bundle(
        artifact,
        data_root=data_root,
        at=now,
        family="trade-documents",
        latest_name="flash-trade-document-latest",
    )
    return artifact


def run_analysis_once(
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    model: Optional[str] = None,
    at: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    produced_at = now.isoformat()
    events = _read_recent_events(data_root, at=now)
    selected_model = model or os.getenv("HWISTOCK_DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL)
    analysis_dir = _date_dir(data_root, "ai", now)
    evidence_dir = _date_dir(data_root, "evidence", now)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, Any] = {
        "event": "ai_analysis_once",
        "timestamp_kst": produced_at,
        "provider_route": "deepseek_direct",
        "requested_model": selected_model,
        "source_event_count": len(events),
        "broker_calls_enabled": False,
        "orders_enabled": False,
        "ai_direct_order_allowed": False,
        "status": "blocked_no_source_events" if not events else "pending",
        "analysis_text": "",
        "provider": None,
    }

    if events:
        try:
            provider = _call_deepseek(_build_prompt(events, produced_at_kst=produced_at), model=selected_model, job="legacy-summary")
            result["provider"] = _provider_meta(provider)
            if isinstance(provider.get("warnings"), list):
                result["warnings"] = [str(item) for item in provider["warnings"] if str(item or "").strip()]
            result["analysis_text"] = str(provider.get("text") or "")
            if (provider.get("error") or {}).get("code") == "missing_deepseek_api_key":
                result["status"] = "blocked_missing_deepseek_api_key"
            else:
                result["status"] = "ok" if provider.get("finish_reason") == "stop" and result["analysis_text"] else "provider_failed"
        except Exception as exc:  # noqa: BLE001 - evidence runner must fail closed.
            result["provider"] = {"error_class": exc.__class__.__name__, "message": str(exc)[:200]}
            result["status"] = "provider_error"

    stamp = now.strftime("%H%M%S")
    stamped_path = analysis_dir / f"deepseek-analysis-{stamp}.json"
    latest_path = analysis_dir / "deepseek-analysis-latest.json"
    health_path = evidence_dir / "ai-analysis-health.json"
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    stamped_path.write_text(text, encoding="utf-8")
    latest_path.write_text(text, encoding="utf-8")
    health_path.write_text(
        json.dumps(
            {
                "event": "ai_analysis_health",
                "timestamp_kst": produced_at,
                "status": result["status"],
                "requested_model": selected_model,
                "actual_model": (result.get("provider") or {}).get("model"),
                "provider_route": "deepseek_direct",
                "source_event_count": len(events),
                "analysis_artifact_path": str(latest_path),
                "orders_enabled": False,
                "broker_calls_enabled": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    result["artifact_paths"] = {
        "latest": str(latest_path),
        "stamped": str(stamped_path),
        "health": str(health_path),
    }
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="hwiStock direct AI analysis runner")
    parser.add_argument("--once", action="store_true", help="Run one analysis tick")
    parser.add_argument(
        "--job",
        choices=("legacy-summary", "pro-hourly", "flash-10m", "build-morning-prompt", "publish-morning-watchlist"),
        default=os.getenv("HWISTOCK_AI_JOB", "pro-hourly"),
        help="AI runtime job to execute",
    )
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT), help="Runtime data root")
    parser.add_argument("--model", default=os.getenv("HWISTOCK_DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL), help="DeepSeek model id")
    parser.add_argument("--source-json", help="Sanitized local GPT Pro morning_watchlist/v1 JSON file to publish")
    parser.add_argument("--target-trade-date", help="Target trade date for morning watchlist latest paths")
    parser.add_argument("--purpose", help="Override morning watchlist purpose metadata")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.once:
        parser.print_help(sys.stderr)
        return 2
    if args.job == "pro-hourly":
        result = run_pro_hourly_once(data_root=Path(args.data_root), model=args.model)
    elif args.job == "flash-10m":
        result = run_flash_trade_document_once(data_root=Path(args.data_root), model=args.model)
    elif args.job == "build-morning-prompt":
        result = build_morning_watchlist_prompt(
            data_root=Path(args.data_root),
            target_trade_date=args.target_trade_date,
            purpose=args.purpose,
        )
    elif args.job == "publish-morning-watchlist":
        result = publish_morning_watchlist_artifact(
            source_path=Path(args.source_json) if args.source_json else None,
            data_root=Path(args.data_root),
            target_trade_date=args.target_trade_date,
            purpose=args.purpose,
        )
    else:
        result = run_analysis_once(data_root=Path(args.data_root), model=args.model)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if result.get("status") == "provider_error" or result.get("provider_status") == "provider_error":
        return 1
    if result.get("validation_status") == "rejected":
        return 1
    accepted_statuses = {"ok", "blocked_no_source_events", "blocked_missing_deepseek_api_key"}
    if result.get("status") in accepted_statuses:
        return 0
    if result.get("validation_status") in {"accepted", "accepted_with_warnings", "safe_block"}:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
