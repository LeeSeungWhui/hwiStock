"""
hwiStock overnight AI analysis runner.

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

KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"


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
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT), help="Runtime data root")
    parser.add_argument("--model", default=os.getenv("HWISTOCK_DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL), help="DeepSeek model id")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.once:
        parser.print_help(sys.stderr)
        return 2
    result = run_analysis_once(data_root=Path(args.data_root), model=args.model)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"ok", "blocked_no_source_events", "blocked_missing_deepseek_api_key"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
