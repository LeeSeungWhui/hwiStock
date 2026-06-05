"""
UNIT-013 KIS paper-read market-data runtime implementation.

The first operational scope is intentionally bounded to six signal inputs:
KRX realtime trade price, KRX realtime orderbook, volume rank, execution
strength/volume-power rank, fluctuation rank, and program-trading aggregate
status. This module never calls KIS order/cancel/modify endpoints.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

KST = timezone(timedelta(hours=9))
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))

ALLOWED_SIGNAL_INPUTS: tuple[str, ...] = (
    "krx_realtime_trade_price_ws",
    "krx_realtime_orderbook_ws",
    "rest_volume_rank",
    "rest_volume_power_rank",
    "rest_fluctuation_rank",
    "rest_program_trading_aggregate",
)

ORDER_ENDPOINT_TOKENS = (
    "order-cash",
    "cash_order",
    "cash-order",
    "cancel",
    "modify",
    "rvsecncl",
    "balance",
    "buyable",
    "inquire-psbl-order",
    "order-cash",
)

INPUT_ENDPOINT_AUDIT: Dict[str, Dict[str, Any]] = {
    "krx_realtime_trade_price_ws": {
        "transport": "websocket",
        "endpoint_alias": "kis_ws_krx_realtime_trade_price_paper",
        "paper_read_only": True,
    },
    "krx_realtime_orderbook_ws": {
        "transport": "websocket",
        "endpoint_alias": "kis_ws_krx_realtime_orderbook_paper",
        "paper_read_only": True,
    },
    "rest_volume_rank": {
        "transport": "rest",
        "endpoint_alias": "kis_rest_volume_rank_paper",
        "paper_read_only": True,
    },
    "rest_volume_power_rank": {
        "transport": "rest",
        "endpoint_alias": "kis_rest_volume_power_rank_paper",
        "paper_read_only": True,
    },
    "rest_fluctuation_rank": {
        "transport": "rest",
        "endpoint_alias": "kis_rest_fluctuation_rank_paper",
        "paper_read_only": True,
    },
    "rest_program_trading_aggregate": {
        "transport": "rest",
        "endpoint_alias": "kis_rest_program_trading_aggregate_paper",
        "paper_read_only": True,
    },
}


def _now_kst() -> datetime:
    return datetime.now(KST).replace(microsecond=0)


def _bool_env(env: Mapping[str, str], key: str, default: bool = False) -> bool:
    raw = str(env.get(key, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def loadKisSignalCollectorConfig(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    raw_inputs = str(source.get("HWISTOCK_KIS_SIGNAL_INPUTS") or "").strip()
    inputs = [
        item.strip()
        for item in raw_inputs.split(",")
        if item.strip()
    ] or list(ALLOWED_SIGNAL_INPUTS)
    return {
        "schema_version": "kis_signal_collector_config/v0",
        "collector_id": "kis_intraday_market_collector",
        "paper_read_network_enabled": _bool_env(source, "HWISTOCK_KIS_MARKET_READ_NETWORK_ENABLED", False),
        "requested_inputs": inputs,
        "allowed_inputs": list(ALLOWED_SIGNAL_INPUTS),
        "forbidden_transport": "order/cancel/modify/balance/buyable",
    }


def validateKisSignalInputScope(config: Mapping[str, Any]) -> Dict[str, Any]:
    requested = [str(item).strip() for item in (config.get("requested_inputs") or []) if str(item).strip()]
    errors: list[str] = []
    for item in requested:
        lowered = item.lower()
        if item not in ALLOWED_SIGNAL_INPUTS:
            errors.append(f"kis_signal_input_not_in_six_input_allowlist:{item}")
        if any(token in lowered for token in ORDER_ENDPOINT_TOKENS):
            errors.append(f"kis_signal_input_forbidden_order_surface:{item}")
    return {
        "ok": not errors,
        "errors": errors,
        "requested_inputs": requested,
        "allowed_inputs": list(ALLOWED_SIGNAL_INPUTS),
        "order_cancel_modify_called": False,
    }


def buildKisSignalEndpointAudit(config: Mapping[str, Any]) -> Dict[str, Any]:
    validation = validateKisSignalInputScope(config)
    entries = []
    for input_id in validation["requested_inputs"]:
        entry = dict(INPUT_ENDPOINT_AUDIT.get(input_id) or {})
        entry["input_id"] = input_id
        entry["allowed"] = input_id in ALLOWED_SIGNAL_INPUTS
        entry["broker_order_surface"] = False
        entry["endpoint_called"] = False
        entries.append(entry)
    return {
        "schema_version": "kis_signal_endpoint_audit/v0",
        "collector_id": config.get("collector_id", "kis_intraday_market_collector"),
        "validation": validation,
        "entries": entries,
        "order_cancel_modify_called": False,
        "live_domain_calls_made": False,
    }


def collectKisMarketDataOnce(
    *,
    env: Optional[Mapping[str, str]] = None,
    at: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    config = loadKisSignalCollectorConfig(env)
    audit = buildKisSignalEndpointAudit(config)
    validation = audit["validation"]
    network_enabled = bool(config["paper_read_network_enabled"])
    rows = []
    for input_id in validation["requested_inputs"]:
        allowed = input_id in ALLOWED_SIGNAL_INPUTS
        status = "safe_blocked_not_in_allowlist" if not allowed else (
            "blocked_paper_read_network_disabled" if not network_enabled else "ready_for_paper_read"
        )
        rows.append(
            {
                "input_id": input_id,
                "status": status,
                "endpoint_called": False,
                "paper_read_only": allowed,
                "order_cancel_modify_called": False,
            }
        )
    overall_status = "blocked_input_scope" if not validation["ok"] else (
        "safe_block_paper_read_network_disabled" if not network_enabled else "ready_paper_read_network_scoped"
    )
    return {
        "schema_version": "kis_market_snapshot/v0",
        "artifact_id": f"art_kis_signal_scope_{now.strftime('%Y%m%d_%H%M%S')}",
        "artifact_type": "kis_market_snapshot",
        "producer": "kis_intraday_market_collector",
        "produced_at_kst": now.isoformat(),
        "collector_scope": "unit_013_kis_six_input_only",
        "status": overall_status,
        "six_input_allowlist": list(ALLOWED_SIGNAL_INPUTS),
        "endpoint_audit": audit,
        "input_results": rows,
        "order_cancel_modify_called": False,
        "live_domain_calls_made": False,
        "raw_response_stored": False,
        "credential_values_printed": False,
        "unsupported_nxt_sor_policy": "disabled_or_fallback_only",
    }


def writeKisMarketDataEvidence(
    payload: Mapping[str, Any],
    *,
    data_root: Optional[Path] = None,
    at: Optional[datetime] = None,
) -> Dict[str, str]:
    now = at or _now_kst()
    root = data_root or DEFAULT_DATA_ROOT
    output_dir = root / "kis-market" / now.date().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    latest = output_dir / "kis-market-snapshot-latest.json"
    stamped = output_dir / f"kis-market-snapshot-{now.strftime('%H%M%S')}.json"
    text = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = latest.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(latest)
    stamped.write_text(text, encoding="utf-8")
    return {"latest_path": str(latest), "stamped_path": str(stamped)}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="hwiStock UNIT-013 KIS six-input market-data collector")
    parser.add_argument("--once", action="store_true", help="Run one collector tick")
    parser.add_argument("--write-evidence", action="store_true", help="Write sanitized collector evidence")
    parser.add_argument("--output-root", default=str(DEFAULT_DATA_ROOT))
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.once:
        parser.print_help(sys.stderr)
        return 2
    payload = collectKisMarketDataOnce()
    if args.write_evidence:
        payload["evidencePaths"] = writeKisMarketDataEvidence(payload, data_root=Path(args.output_root))
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 0 if payload.get("order_cancel_modify_called") is False else 1


if __name__ == "__main__":
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
    raise SystemExit(main())
