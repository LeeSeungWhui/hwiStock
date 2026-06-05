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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    from lib import ai_orchestration as ao
except ImportError:  # pragma: no cover
    from backend.lib import ai_orchestration as ao

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
                "query": str(row.get("query") or ""),
            }
        )
    return rows[-row_limit:]


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


def _build_prompt(events: Sequence[Mapping[str, Any]], *, produced_at_kst: str) -> str:
    titles = [str(event.get("title") or "")[:120] for event in events if event.get("title")]
    return (
        "JSON만 출력. 설명 금지. 아래 한국 증시 뉴스 제목을 아주 짧게 요약해. "
        "매수/매도 추천 금지. 주문 금지. 수익 예측 금지. "
        "형식: {\"summary\":\"한문장\",\"themes\":[\"키워드1\",\"키워드2\"],"
        "\"risk_flags\":[\"위험1\"],\"order_safety\":\"no_order\"}. "
        f"시각={produced_at_kst}. "
        f"제목={json.dumps(titles, ensure_ascii=False)}"
    )


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


def run_pro_hourly_once(
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    at: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    events = _read_recent_events(data_root, at=now)
    kis_snapshots = _read_recent_kis_snapshots(data_root, at=now)
    provider_status = "blocked_missing_deepseek_api_key" if not _deepseek_api_key() else "provider_network_not_called_in_local_go"
    artifact = ao.buildProHourlyMarketAnalysis(
        events=events,
        kis_market_snapshots=kis_snapshots,
        produced_at_kst=now.isoformat(),
        provider_status=provider_status,
    )
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
) -> Dict[str, Any]:
    now = at or _now_kst()
    latest_pro_path = _latest_json_file(data_root, "ai", now.date().isoformat())
    pro_artifact = _read_json_artifact(latest_pro_path) if latest_pro_path else None
    events = _read_recent_events(data_root, limit=20, at=now)
    kis_snapshots = _read_recent_kis_snapshots(data_root, at=now)
    compiled_watch = _read_compiled_watch(data_root, at=now)
    portfolio = _read_json_artifact(_latest_json_file(data_root, "portfolio", now.date().isoformat()) or Path())
    order_state = _read_json_artifact(_latest_json_file(data_root, "orders", now.date().isoformat()) or Path())
    artifact = ao.buildFlashTradeDocument(
        pro_artifact=pro_artifact,
        recent_events=events,
        kis_market_snapshots=kis_snapshots,
        compiled_watch=compiled_watch,
        portfolio_snapshot=portfolio,
        order_state_snapshot=order_state,
        previous_trade_documents=[],
        produced_at_kst=now.isoformat(),
    )
    validation = ao.validateFlashTradeDocument(artifact, compiled_watch=compiled_watch)
    artifact = validation["document"]
    artifact["validation_errors"] = validation["errors"]
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
        choices=("legacy-summary", "pro-hourly", "flash-10m"),
        default=os.getenv("HWISTOCK_AI_JOB", "pro-hourly"),
        help="AI runtime job to execute",
    )
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT), help="Runtime data root")
    parser.add_argument("--model", default=os.getenv("HWISTOCK_DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL), help="DeepSeek model id")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.once:
        parser.print_help(sys.stderr)
        return 2
    if args.job == "pro-hourly":
        result = run_pro_hourly_once(data_root=Path(args.data_root))
    elif args.job == "flash-10m":
        result = run_flash_trade_document_once(data_root=Path(args.data_root))
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
