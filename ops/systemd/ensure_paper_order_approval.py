#!/usr/bin/env python3
"""Ensure the KIS paper-order approval file matches the current KST date.

This helper is intentionally narrow:

- It only runs for paper_experiment order loops.
- It requires an existing approval file with the same operator run id.
- It never enables live-money scope.
- It writes a date-stamped paper approval file and emits shell exports for the
  current service process.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DEFAULT_RUNTIME_ENV_FILE = Path("/home/hwi/.config/hwistock/runtime-mode.env")


def _bool_env(env: Mapping[str, str], key: str, default: bool = False) -> bool:
    raw = str(env.get(key, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure daily hwiStock paper-order approval")
    parser.add_argument("--date-kst", help="Override target KST date, YYYY-MM-DD. Defaults to today in KST.")
    parser.add_argument("--emit-env", action="store_true", help="Print shell exports for the selected approval file.")
    parser.add_argument(
        "--update-runtime-env",
        nargs="?",
        const=str(DEFAULT_RUNTIME_ENV_FILE),
        default="",
        help="Update runtime-mode.env with the selected approval file path.",
    )
    return parser.parse_args()


def _target_date(value: str | None) -> str:
    if value:
        return date.fromisoformat(value).isoformat()
    return datetime.now(KST).date().isoformat()


def _load_existing_approval(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"approval file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"approval file is not valid JSON: {path}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"approval file must contain a JSON object: {path}")
    return parsed


def _approval_dir(env: Mapping[str, str], source_path: Path) -> Path:
    configured = str(env.get("HWISTOCK_ORDER_APPROVAL_DIR") or "").strip()
    if configured:
        return Path(configured)
    return source_path.parent


def _coerce_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _build_daily_payload(
    env: Mapping[str, str],
    source_path: Path,
    source_payload: Mapping[str, Any],
    *,
    target_date: str,
) -> dict[str, Any]:
    run_id = str(env.get("HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID") or "").strip()
    approved_run_id = str(source_payload.get("approved_order_run_id") or source_payload.get("run_id") or "").strip()
    if not run_id:
        raise RuntimeError("HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID is required for paper-order approval rollover")
    if approved_run_id != run_id:
        raise RuntimeError("existing approval run id does not match HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID")

    mode = str(source_payload.get("mode") or source_payload.get("operation_mode") or "").strip()
    if mode != "paper_experiment":
        raise RuntimeError("existing approval is not for paper_experiment mode")
    if source_payload.get("allow_paper_orders") is not True:
        raise RuntimeError("existing approval does not allow paper orders")
    live_money_scope = str(source_payload.get("live_money_scope") or "not_applicable").strip().lower()
    if live_money_scope != "not_applicable":
        raise RuntimeError("paper approval rollover cannot carry live-money scope")

    return {
        "schema_version": "paper_order_approval/v0",
        "mode": "paper_experiment",
        "approved_order_run_id": run_id,
        "allow_paper_orders": True,
        "valid_for_date_kst": target_date,
        "valid_until_kst": None,
        "max_daily_orders": _coerce_int(
            env.get("HWISTOCK_MAX_DAILY_PAPER_ORDERS"),
            _coerce_int(source_payload.get("max_daily_orders"), 20),
        ),
        "max_notional_krw": _coerce_int(
            env.get("HWISTOCK_MAX_PAPER_NOTIONAL_KRW"),
            _coerce_int(source_payload.get("max_notional_krw"), 2_000_000),
        ),
        "live_money_scope": "not_applicable",
        "rollover_source_path": str(source_path),
        "generated_by": "hwistock_ensure_paper_order_approval",
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
    }


def _write_json_0600(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)
    path.chmod(0o600)


def _update_runtime_env_file(path: Path, updates: Mapping[str, str]) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    existing_lines: list[str] = []
    if path.exists():
        existing_lines = path.read_text(encoding="utf-8").splitlines()

    pending = dict(updates)
    next_lines: list[str] = []
    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            next_lines.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in pending:
            next_lines.append(f"{key}={pending.pop(key)}")
        else:
            next_lines.append(line)
    for key, value in pending.items():
        next_lines.append(f"{key}={value}")

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)
    path.chmod(0o600)


def _shell_export(key: str, value: str) -> str:
    return f"export {key}={shlex.quote(value)}"


def main() -> int:
    args = _parse_args()
    env = dict(os.environ)
    requested = _bool_env(env, "HWISTOCK_KIS_PAPER_ORDER_ENABLED", False)
    operation_mode = str(env.get("HWISTOCK_OPERATION_MODE") or "").strip()
    if not requested or operation_mode != "paper_experiment":
        return 0

    approval_file = str(env.get("HWISTOCK_ORDER_APPROVAL_FILE") or "").strip()
    if not approval_file:
        raise RuntimeError("HWISTOCK_ORDER_APPROVAL_FILE is required for paper-order approval rollover")
    source_path = Path(approval_file)
    source_payload = _load_existing_approval(source_path)
    target_date = _target_date(args.date_kst)
    daily_path = _approval_dir(env, source_path) / f"paper-{target_date.replace('-', '')}.approval.json"
    payload = _build_daily_payload(env, source_path, source_payload, target_date=target_date)
    _write_json_0600(daily_path, payload)

    updates = {"HWISTOCK_ORDER_APPROVAL_FILE": str(daily_path)}
    if args.update_runtime_env:
        _update_runtime_env_file(Path(args.update_runtime_env), updates)
    if args.emit_env:
        print(_shell_export("HWISTOCK_ORDER_APPROVAL_FILE", str(daily_path)))
    print(
        f"paper order approval ready: date={target_date} path={daily_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"paper order approval rollover failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
