"""
Shared KIS paper access-token cache for operational ticks.

The token value is sensitive and must stay outside the repository. Runtime
evidence records only cache status and never prints the token.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

KST = timezone(timedelta(hours=9))
DEFAULT_TOKEN_CACHE = Path("/home/hwi/.config/hwistock/runtime/kis-paper-token-cache.json")


def loadKisPaperAccessToken(
    adapter: Any,
    *,
    env: Optional[Mapping[str, str]] = None,
    now: Optional[datetime] = None,
) -> Tuple[Dict[str, Any], str, bool]:
    source = env if env is not None else os.environ
    cacheable = isCacheableKisPaperAdapter(adapter, source)
    if not cacheable:
        result, token = adapter.issueTokenWithValue()
        return result, token, False

    reference = now or datetime.now(KST).replace(microsecond=0)
    cache_path = _cachePath(source)
    cached = _readCache(cache_path)
    token = str(cached.get("access_token") or "").strip()
    expires_at = _parseKst(cached.get("expires_at_kst"))
    if token and expires_at and expires_at - reference > timedelta(minutes=10):
        return {
            "step": "oauth_token_cache",
            "status": "pass",
            "token_present": True,
            "cache_hit": True,
            "cache_path": str(cache_path),
            "credential_values_printed": False,
            "raw_response_stored": False,
        }, token, True

    result, token = adapter.issueTokenWithValue()
    if result.get("token_present") and token:
        _writeCache(cache_path, token=token, now=reference)
        result = dict(result)
        result["cache_hit"] = False
        result["cache_path"] = str(cache_path)
        result["credential_values_printed"] = False
    return result, token, True


def tokenCacheRevokeSkippedStep() -> Dict[str, Any]:
    return {
        "step": "oauth_revoke",
        "status": "skipped_token_cache_enabled",
        "reason": "shared paper token cache prevents tokenP rate-limit churn",
        "raw_response_stored": False,
        "credential_values_printed": False,
    }


def invalidateKisPaperAccessToken(
    env: Optional[Mapping[str, str]] = None,
    *,
    reason: str = "invalid_token_response",
) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    cache_path = _cachePath(source)
    existed = cache_path.is_file()
    try:
        cache_path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        return {
            "step": "oauth_token_cache_invalidate",
            "status": "warn",
            "reason": reason,
            "cache_path": str(cache_path),
            "cache_existed": existed,
            "error_class": exc.__class__.__name__,
            "credential_values_printed": False,
            "raw_response_stored": False,
        }
    return {
        "step": "oauth_token_cache_invalidate",
        "status": "pass",
        "reason": reason,
        "cache_path": str(cache_path),
        "cache_existed": existed,
        "credential_values_printed": False,
        "raw_response_stored": False,
    }


def isCacheableKisPaperAdapter(adapter: Any, env: Mapping[str, str]) -> bool:
    request_method = getattr(adapter, "requestBrokerJson", None)
    if not callable(request_method):
        return False
    if str(env.get("HWISTOCK_KIS_TOKEN_CACHE_FILE") or "").strip():
        return True
    transport = getattr(adapter, "transport", None)
    transport_name = transport.__class__.__name__ if transport is not None else ""
    return transport_name == "UrllibJsonTransport"


def _cachePath(env: Mapping[str, str]) -> Path:
    raw = str(env.get("HWISTOCK_KIS_TOKEN_CACHE_FILE") or "").strip()
    return Path(raw).expanduser() if raw else DEFAULT_TOKEN_CACHE


def _readCache(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _writeCache(path: Path, *, token: str, now: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "kis_paper_token_cache/v0",
        "access_token": token,
        "created_at_kst": now.isoformat(),
        "expires_at_kst": (now + timedelta(hours=20)).isoformat(),
        "credential_values_printed": False,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _parseKst(value: Any) -> Optional[datetime]:
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
