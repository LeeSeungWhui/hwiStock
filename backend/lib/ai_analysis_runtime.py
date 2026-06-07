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
    from lib import runtime_policy as rp
    from lib import trading_engine
except ImportError:  # pragma: no cover
    from backend.lib import ai_orchestration as ao
    from backend.lib import runtime_policy as rp
    from backend.lib import trading_engine

KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = ao.DEEPSEEK_PRO_MODEL


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
    schema = str(source_payload.get("schema_version") or source_payload.get("schema") or "").strip()
    route = str(source_payload.get("route") or "").strip()
    payload_target = str(
        source_payload.get("target_trade_date_kst")
        or source_payload.get("trading_date_kst")
        or source_payload.get("trading_date")
        or requested_target
    ).strip()

    if not source_payload:
        errors.append("missing_morning_watchlist_payload")
    elif schema != "morning_watchlist/v0":
        errors.append("schema_version_must_be_morning_watchlist_v0")
    elif route and route != "codex_cli_local_browser_use":
        errors.append("route_must_be_codex_cli_local_browser_use")
    elif payload_target != requested_target:
        errors.append("target_trade_date_mismatch")

    if errors:
        artifact = {
            "schema_version": "morning_watchlist/v0",
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
        artifact["schema_version"] = "morning_watchlist/v0"
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


def _build_pro_hourly_prompt(
    events: Sequence[Mapping[str, Any]],
    kis_snapshots: Sequence[Mapping[str, Any]],
    *,
    produced_at_kst: str,
) -> str:
    titles = [
        {
            "event_id": str(event.get("event_id") or event.get("source_id") or "")[:80],
            "title": str(event.get("title") or "")[:160],
            "type": str(event.get("event_type") or "")[:40],
        }
        for event in events[:20]
    ]
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
    return (
        "JSON만 출력. 직접 주문, 수익 보장, 계좌/비밀값 언급 금지. "
        "역할은 한국 장중 시장국면/테마/피해야 할 조건 정리다. "
        "summary, themes, strong_conditions, avoid_conditions, risk_flags 등 사람이 읽는 모든 문자열 값은 한국어로 작성해. "
        "schema key와 market_mode enum, order_safety 같은 기계용 키/고정값은 지정 형식 그대로 유지해. "
        "형식: {\"summary\":\"한문장\", \"market_mode\":\"RISK_ON|NEUTRAL|RISK_OFF|NO_TRADE\", "
        "\"themes\":[\"테마\"], \"strong_conditions\":[\"조건\"], "
        "\"avoid_conditions\":[\"조건\"], \"risk_flags\":[\"리스크\"], \"order_safety\":\"no_order\"}. "
        f"시각={produced_at_kst}. "
        f"뉴스/공시={json.dumps(titles, ensure_ascii=False)} "
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
    return (
        "JSON만 출력. 직접 주문 실행 금지. 후보는 compiled_watch 안에서 최대 5개만 평가. "
        "보유/대기 주문과 충돌하는 신규매수 금지. "
        "summary, reason, candidate_notes.reason, risk_flags 등 사람이 읽는 모든 문자열 값은 한국어로 작성해. "
        "schema key, symbol, action enum, 숫자 필드는 지정 형식 그대로 유지해. "
        "actions는 다음 10분 매매문서 초안이며 허용 action은 WAIT_BUY, BUY_NOW, HOLD, SELL, NO_TRADE뿐이다. "
        "형식: {\"summary\":\"한문장\", "
        "\"actions\":[{\"symbol\":\"000000\",\"action\":\"WAIT_BUY|BUY_NOW|HOLD|SELL|NO_TRADE\","
        "\"entry_price_limit\":10000,\"target_price\":10500,\"stop_loss_price\":9800,"
        "\"planned_order_cash_krw\":100000,\"quantity\":0,\"reason\":\"짧게\"}], "
        "\"candidate_notes\":[{\"symbol\":\"000000\",\"stance\":\"watch|avoid\",\"reason\":\"짧게\"}], "
        "\"risk_flags\":[\"리스크\"], \"order_safety\":\"no_direct_order\"}. "
        f"시각={produced_at_kst}. "
        f"Pro분석={json.dumps(_compact_json_for_prompt(pro_artifact, 2000), ensure_ascii=False)} "
        f"최근뉴스={json.dumps(list(events)[-20:], ensure_ascii=False)} "
        f"KIS스냅샷={json.dumps(_compact_json_for_prompt(list(kis_snapshots)[-3:], 2500), ensure_ascii=False)} "
        f"후보={json.dumps(watch_summary, ensure_ascii=False)} "
        f"포트폴리오={json.dumps(_compact_json_for_prompt(portfolio, 1200), ensure_ascii=False)} "
        f"주문상태={json.dumps(_compact_json_for_prompt(order_state, 1200), ensure_ascii=False)}"
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
        "text_present": bool(str(provider.get("text") or "").strip()),
    }


def _provider_status(provider: Mapping[str, Any]) -> str:
    error = provider.get("error")
    if isinstance(error, Mapping) and error.get("code") == "missing_deepseek_api_key":
        return "blocked_missing_deepseek_api_key"
    if error:
        return "provider_failed"
    if provider.get("finish_reason") == "stop" and str(provider.get("text") or "").strip():
        return "ok"
    if provider.get("http_status") == 200 and str(provider.get("text") or "").strip():
        return "ok"
    return "provider_failed"


def _deepseek_api_key() -> str:
    return (
        os.getenv("HWISTOCK_DEEPSEEK_API_KEY", "").strip()
        or os.getenv("DEEPSEEK_API_KEY", "").strip()
    )


def _deepseek_chat_url() -> str:
    base_url = os.getenv("HWISTOCK_DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).strip()
    base_url = (base_url or DEFAULT_DEEPSEEK_BASE_URL).rstrip("/")
    return f"{base_url}/chat/completions"


def _call_deepseek(prompt: str, *, model: str, timeout: int = 90) -> Dict[str, Any]:
    api_key = _deepseek_api_key()
    if not api_key:
        return {
            "http_status": None,
            "finish_reason": None,
            "model": model,
            "text": "",
            "usage": None,
            "error": {"code": "missing_deepseek_api_key"},
        }

    thinking_mode = os.getenv("HWISTOCK_DEEPSEEK_THINKING", "disabled").strip().lower()
    request_body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You write compact JSON market-intelligence summaries. Never recommend or place orders.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": int(os.getenv("HWISTOCK_AI_MAX_OUTPUT_TOKENS", "1000")),
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
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
    text = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp_path = latest_path.with_suffix(".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(latest_path)
    stamped_path.write_text(text, encoding="utf-8")
    health_path.write_text(
        json.dumps(
            {
                "event": f"{latest_name}_health",
                "timestamp_kst": at.isoformat(),
                "status": payload.get("validation_status") or payload.get("status"),
                "artifact_path": str(latest_path),
                "schema_version": payload.get("schema_version"),
                "model_name": payload.get("model_name"),
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
        "active_exits": [],
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
    events, input_window = _read_events_for_hour_window(data_root, at=now)
    kis_snapshots = _read_recent_kis_snapshots(data_root, at=now)
    selected_model = model or os.getenv("HWISTOCK_DEEPSEEK_MODEL", ao.DEEPSEEK_PRO_MODEL)
    provider: Optional[Dict[str, Any]] = None
    provider_json: Dict[str, Any] = {}
    if events or kis_snapshots:
        try:
            provider = _call_deepseek(
                _build_pro_hourly_prompt(events, kis_snapshots, produced_at_kst=now.isoformat()),
                model=selected_model,
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
    artifact["model_name"] = selected_model
    artifact["provider"] = _provider_meta(provider)
    if provider_json:
        artifact["provider_json"] = provider_json
        if str(provider_json.get("summary") or "").strip():
            artifact["summary"] = str(provider_json["summary"])[:1000]
        themes = provider_json.get("themes")
        if isinstance(themes, list):
            artifact["themes"] = [str(item)[:80] for item in themes[:12]]
        risk_flags = provider_json.get("risk_flags")
        if isinstance(risk_flags, list):
            artifact["risk_flags"] = [str(item)[:120] for item in risk_flags[:12]]
        strong = provider_json.get("strong_conditions")
        if isinstance(strong, list):
            artifact["strong_conditions"] = [str(item)[:120] for item in strong[:12]]
        avoid = provider_json.get("avoid_conditions")
        if isinstance(avoid, list):
            artifact["avoid_conditions"] = [str(item)[:120] for item in avoid[:12]]
        market_mode = str(provider_json.get("market_mode") or "").strip()
        if market_mode:
            artifact["market_regime"]["market_mode"] = market_mode[:40]
    if provider_status not in {"ok", "blocked_no_source_inputs"}:
        artifact["validation_status"] = "safe_block"
        artifact["document_kind"] = "NO_TRADE"
        artifact["market_regime"]["market_mode"] = "NO_TRADE"
        artifact["safe_block_reason"] = provider_status
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
    if pro_artifact and compiled_watch and (events or kis_snapshots):
        try:
            provider = _call_deepseek(
                _build_flash_prompt(
                    pro_artifact=pro_artifact,
                    events=events,
                    kis_snapshots=kis_snapshots,
                    compiled_watch=compiled_watch,
                    portfolio=portfolio,
                    order_state=order_state,
                    produced_at_kst=now.isoformat(),
                ),
                model=selected_model,
                timeout=60,
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
    artifact["model_name"] = selected_model
    artifact["provider_status"] = _provider_status(provider or {}) if provider else "blocked_no_flash_provider_inputs"
    artifact["provider"] = _provider_meta(provider)
    if provider_json:
        artifact["provider_json"] = provider_json
        notes = provider_json.get("candidate_notes")
        if isinstance(notes, list):
            artifact["provider_candidate_notes"] = notes[:5]
        if str(provider_json.get("summary") or "").strip():
            artifact["provider_summary"] = str(provider_json["summary"])[:1000]
    validation = ao.validateFlashTradeDocument(artifact, compiled_watch=compiled_watch)
    artifact = validation["document"]
    artifact["validation_errors"] = validation["errors"]
    if artifact.get("validation_status") == "accepted":
        pipeline = trading_engine.generatePaperOrderIntentsFromFlashDocument(
            artifact,
            compiled_watch=compiled_watch,
            portfolio_snapshot=portfolio,
            order_state_snapshot=order_state,
            existing_intents=_read_existing_intents(data_root, at=now),
            now_kst=now.isoformat(),
        )
    else:
        pipeline = {
            "schema_version": "paper_intent_pipeline_result/v0",
            "ok": artifact.get("validation_status") in {"safe_block", "accepted"},
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
            provider = _call_deepseek(_build_prompt(events, produced_at_kst=produced_at), model=selected_model)
            result["provider"] = {
                "http_status": provider.get("http_status"),
                "finish_reason": provider.get("finish_reason"),
                "model": provider.get("model"),
                "usage": provider.get("usage"),
                "error": provider.get("error"),
            }
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
    parser = argparse.ArgumentParser(description="hwiStock direct DeepSeek analysis runner")
    parser.add_argument("--once", action="store_true", help="Run one analysis tick")
    parser.add_argument(
        "--job",
        choices=("legacy-summary", "pro-hourly", "flash-10m", "publish-morning-watchlist"),
        default=os.getenv("HWISTOCK_AI_JOB", "pro-hourly"),
        help="AI runtime job to execute",
    )
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT), help="Runtime data root")
    parser.add_argument("--model", default=os.getenv("HWISTOCK_DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL), help="DeepSeek model id")
    parser.add_argument("--source-json", help="Sanitized local GPT Pro morning_watchlist/v0 JSON file to publish")
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
    accepted_statuses = {"ok", "blocked_no_source_events", "blocked_missing_deepseek_api_key"}
    if result.get("status") in accepted_statuses:
        return 0
    if result.get("validation_status") in {"accepted", "safe_block"}:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
