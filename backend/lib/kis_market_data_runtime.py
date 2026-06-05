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
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

KST = timezone(timedelta(hours=9))
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    from lib.kis_paper_token_cache import loadKisPaperAccessToken, tokenCacheRevokeSkippedStep
    from service.kis_paper_adapter import KisPaperAdapter, UrllibJsonTransport
except ImportError:  # pragma: no cover
    from backend.lib.kis_paper_token_cache import loadKisPaperAccessToken, tokenCacheRevokeSkippedStep
    from backend.service.kis_paper_adapter import KisPaperAdapter, UrllibJsonTransport

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
MARKET_READ_PREFIXES = (
    "/uapi/domestic-stock/v1/quotations/",
    "/uapi/domestic-stock/v1/ranking/",
)
SAFE_MARKET_ROW_KEYS = (
    "mksc_shrn_iscd",
    "pdno",
    "stck_shrn_iscd",
    "hts_kor_isnm",
    "prdt_abrv_name",
    "stck_prpr",
    "prdy_vrss",
    "prdy_ctrt",
    "acml_vol",
    "acml_tr_pbmn",
    "data_rank",
    "rank",
    "cntg_vol",
    "cntg_cls_code",
    "tday_rltv",
    "avrg_vol",
    "vol_inrt",
    "stck_cntg_hour",
    "askp1",
    "bidp1",
    "askp_rsqn1",
    "bidp_rsqn1",
    "seln_cnqn",
    "shnu_cnqn",
    "ntby_cnqn",
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


def _float_env(env: Mapping[str, str], key: str, default: float) -> float:
    raw = str(env.get(key, "")).strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int_env(env: Mapping[str, str], key: str, default: int) -> int:
    raw = str(env.get(key, "")).strip().replace(",", "")
    if not raw:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


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
        "sample_symbol": str(source.get("HWISTOCK_KIS_HEALTH_SYMBOL", "005930")).strip() or "005930",
        "min_call_gap_sec": _float_env(source, "HWISTOCK_KIS_MIN_CALL_GAP_SEC", 1.35),
        "default_order_cash_krw": _int_env(source, "HWISTOCK_PAPER_DEFAULT_ORDER_CASH_KRW", 100_000),
        "position_size_pct": _int_env(source, "HWISTOCK_PAPER_DEFAULT_POSITION_SIZE_PCT", 10),
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
    adapter: Optional[KisPaperAdapter] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    source = env if env is not None else os.environ
    config = loadKisSignalCollectorConfig(source)
    audit = buildKisSignalEndpointAudit(config)
    validation = audit["validation"]
    network_enabled = bool(config["paper_read_network_enabled"])
    rows: list[Dict[str, Any]] = []
    steps: list[Dict[str, Any]] = []
    token = ""
    token_cache_managed = False
    approval_result: Dict[str, Any] = {}
    live_domain_calls_made = False

    payload: Dict[str, Any] = {
        "schema_version": "kis_market_snapshot/v0",
        "artifact_id": f"art_kis_signal_scope_{now.strftime('%Y%m%d_%H%M%S')}",
        "artifact_type": "kis_market_snapshot",
        "producer": "kis_intraday_market_collector",
        "produced_at_kst": now.isoformat(),
        "collector_scope": "unit_013_kis_six_input_only",
        "status": "pending",
        "six_input_allowlist": list(ALLOWED_SIGNAL_INPUTS),
        "endpoint_audit": audit,
        "input_results": rows,
        "steps": steps,
        "order_cancel_modify_called": False,
        "live_domain_calls_made": live_domain_calls_made,
        "raw_response_stored": False,
        "credential_values_printed": False,
        "unsupported_nxt_sor_policy": "disabled_or_fallback_only",
    }

    if not validation["ok"]:
        for input_id in validation["requested_inputs"]:
            rows.append(_blocked_input_row(input_id, "safe_blocked_not_in_allowlist"))
        payload["status"] = "blocked_input_scope"
        return payload

    if not network_enabled:
        for input_id in validation["requested_inputs"]:
            rows.append(_blocked_input_row(input_id, "blocked_paper_read_network_disabled"))
        payload["status"] = "safe_block_paper_read_network_disabled"
        return payload

    adapter = adapter or KisPaperAdapter(env=source, transport=UrllibJsonTransport())
    missing = adapter.missingEnvKeys()
    if missing:
        for input_id in validation["requested_inputs"]:
            row = _blocked_input_row(input_id, "blocked_missing_env")
            row["missing_env_keys"] = missing
            rows.append(row)
        payload["status"] = "blocked_missing_env"
        payload["config_summary"] = adapter.configSummary()
        return payload

    try:
        token_result, token, token_cache_managed = loadKisPaperAccessToken(adapter, env=source, now=now)
        steps.append(token_result)
        if not token_result.get("token_present") or not token:
            for input_id in validation["requested_inputs"]:
                rows.append(_blocked_input_row(input_id, "blocked_token_missing"))
            payload["status"] = "blocked_token_missing"
            return payload

        approval_result = _issue_websocket_approval(adapter)
        steps.append(approval_result)
        _sleep_for_kis_gap(config)

        for input_id in validation["requested_inputs"]:
            row = _collect_one_signal_input(
                adapter=adapter,
                token=token,
                input_id=input_id,
                config=config,
                approval_result=approval_result,
            )
            rows.append(row)
            _sleep_for_kis_gap(config)
    except Exception as exc:  # noqa: BLE001 - collector evidence must fail closed.
        rows.append(
            {
                "input_id": "collector_runtime",
                "status": "collector_exception",
                "error_class": exc.__class__.__name__,
                "message": str(exc)[:200],
                "endpoint_called": False,
                "paper_read_only": True,
                "order_cancel_modify_called": False,
            }
        )
    finally:
        if token:
            if token_cache_managed:
                steps.append(tokenCacheRevokeSkippedStep())
            else:
                try:
                    steps.append(adapter.revokeToken(token))
                except Exception as exc:  # noqa: BLE001
                    steps.append({"step": "oauth_revoke", "status": "warn", "error_class": exc.__class__.__name__})

    payload["live_domain_calls_made"] = live_domain_calls_made
    payload["endpoint_audit"] = _mark_audit_calls(audit, rows)
    payload["compiled_watch"] = buildCompiledWatchFromKisSnapshot(payload, config=config, at=now)
    payload["status"] = _overall_status_from_input_rows(rows)
    return payload


def _blocked_input_row(input_id: str, status: str) -> Dict[str, Any]:
    return {
        "input_id": input_id,
        "status": status,
        "endpoint_called": False,
        "paper_read_only": input_id in ALLOWED_SIGNAL_INPUTS,
        "order_cancel_modify_called": False,
    }


def _sleep_for_kis_gap(config: Mapping[str, Any]) -> None:
    gap = float(config.get("min_call_gap_sec") or 0)
    if gap > 0:
        time.sleep(gap)


def _issue_websocket_approval(adapter: KisPaperAdapter) -> Dict[str, Any]:
    fallback = getattr(adapter, "issueWebsocketApproval", None)
    if callable(fallback) and not hasattr(adapter, "_request"):
        return dict(fallback())
    request = getattr(adapter, "_request", None)
    env_value = getattr(adapter, "_env_value", None)
    if not callable(request) or not callable(env_value):
        if callable(fallback):
            return dict(fallback())
        return {"step": "websocket_approval", "status": "blocked_adapter_missing_request_boundary"}
    response = request(
        "POST",
        "/oauth2/Approval",
        body={
            "grant_type": "client_credentials",
            "appkey": env_value("KIS_PAPER_APP_KEY"),
            "secretkey": env_value("KIS_PAPER_APP_SECRET"),
        },
    )
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    result = _sanitize_kis_market_response(response, step="websocket_approval")
    result["approval_key_present"] = bool(payload.get("approval_key"))
    result["credential_values_printed"] = False
    return result


def _kis_market_read(
    adapter: KisPaperAdapter,
    token: str,
    *,
    step: str,
    path: str,
    tr_id: str,
    params: Mapping[str, str],
    fallback_method: str,
    fallback_args: Sequence[Any] = (),
) -> Dict[str, Any]:
    if not any(path.startswith(prefix) for prefix in MARKET_READ_PREFIXES):
        return {
            "step": step,
            "status": "blocked_forbidden_market_read_path",
            "endpoint_called": False,
            "broker_order_surface": False,
            "raw_response_stored": False,
        }
    request = getattr(adapter, "_request", None)
    auth_headers = getattr(adapter, "_authHeaders", None)
    if callable(request) and callable(auth_headers):
        response = request(
            "GET",
            f"{path}?{urllib.parse.urlencode(dict(params))}",
            headers=auth_headers(token, tr_id),
        )
        result = _sanitize_kis_market_response(response, step=step)
    else:
        fallback = getattr(adapter, fallback_method, None)
        result = dict(fallback(token, *fallback_args)) if callable(fallback) else {
            "step": step,
            "status": "blocked_adapter_missing_market_method",
        }
    result["endpoint_called"] = True
    result["broker_order_surface"] = False
    result["tr_id"] = tr_id
    result["raw_response_stored"] = False
    return result


def _program_trade_today(adapter: KisPaperAdapter, token: str, *, market_class: str) -> Dict[str, Any]:
    if not hasattr(adapter, "_request"):
        fallback = getattr(adapter, "programTradeToday", None)
        if callable(fallback):
            return dict(fallback(token, market_class=market_class))
    return _kis_market_read(
        adapter,
        token,
        step=f"rest_program_trading_aggregate_{market_class}",
        path="/uapi/domestic-stock/v1/quotations/comp-program-trade-today",
        tr_id="FHPPG04600101",
        params={
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_MRKT_CLS_CODE": market_class,
            "FID_SCTN_CLS_CODE": "",
            "FID_INPUT_ISCD": "",
            "FID_COND_MRKT_DIV_CODE1": "",
            "FID_INPUT_HOUR_1": "",
        },
        fallback_method="programTradeToday",
        fallback_args=(),
    )


def _sanitize_kis_market_response(response: Mapping[str, Any], *, step: str) -> Dict[str, Any]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    rows = _safe_rows_from_payload(payload)
    out = payload.get("output")
    out1 = payload.get("output1")
    result = {
        "step": step,
        "http_status": response.get("http_status"),
        "rt_cd": payload.get("rt_cd"),
        "msg_cd": payload.get("msg_cd"),
        "status": "pass"
        if response.get("http_status") == 200 and str(payload.get("rt_cd", "0")) in {"0", ""}
        else "warn",
        "raw_response_stored": False,
        "row_count": len(rows),
        "rows_preview": rows,
    }
    if not rows:
        if isinstance(out, list):
            result["row_count"] = len(out)
        elif isinstance(out1, list):
            result["row_count"] = len(out1)
        elif isinstance(out, Mapping):
            result["row_count"] = 1
    return result


def _safe_rows_from_payload(payload: Mapping[str, Any], *, row_limit: int = 10) -> list[Dict[str, Any]]:
    row_sources = [payload.get("output"), payload.get("output1"), payload.get("output2")]
    rows: list[Mapping[str, Any]] = []
    for source in row_sources:
        if isinstance(source, list):
            rows.extend(row for row in source if isinstance(row, Mapping))
        elif isinstance(source, Mapping):
            rows.append(source)
        if rows:
            break
    safe_rows: list[Dict[str, Any]] = []
    for row in rows[: max(0, int(row_limit))]:
        safe = {
            key: row.get(key)
            for key in SAFE_MARKET_ROW_KEYS
            if row.get(key) not in (None, "", [], {})
        }
        if safe:
            safe_rows.append(safe)
    return safe_rows


def _collect_one_signal_input(
    *,
    adapter: KisPaperAdapter,
    token: str,
    input_id: str,
    config: Mapping[str, Any],
    approval_result: Mapping[str, Any],
) -> Dict[str, Any]:
    sample_symbol = str(config.get("sample_symbol") or "005930").strip() or "005930"
    if input_id == "krx_realtime_trade_price_ws":
        result = _kis_market_read(
            adapter,
            token,
            step="quote_inquire_price",
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": sample_symbol},
            fallback_method="inquirePrice",
            fallback_args=(sample_symbol,),
        )
        result.update(
            {
                "input_id": input_id,
                "transport": "websocket_readiness_with_rest_price_snapshot",
                "websocket_approval_status": approval_result.get("status"),
                "websocket_approval_key_present": bool(approval_result.get("approval_key_present")),
                "paper_read_only": True,
                "order_cancel_modify_called": False,
            }
        )
        return result
    if input_id == "krx_realtime_orderbook_ws":
        result = _kis_market_read(
            adapter,
            token,
            step="quote_inquire_orderbook",
            path="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": sample_symbol},
            fallback_method="inquireOrderbook",
            fallback_args=(sample_symbol,),
        )
        result.update(
            {
                "input_id": input_id,
                "transport": "websocket_readiness_with_rest_orderbook_snapshot",
                "websocket_approval_status": approval_result.get("status"),
                "websocket_approval_key_present": bool(approval_result.get("approval_key_present")),
                "paper_read_only": True,
                "order_cancel_modify_called": False,
            }
        )
        return result
    if input_id == "rest_volume_rank":
        result = _kis_market_read(
            adapter,
            token,
            step="rest_volume_rank",
            path="/uapi/domestic-stock/v1/quotations/volume-rank",
            tr_id="FHPST01710000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_DIV_CLS_CODE": "0",
                "FID_BLNG_CLS_CODE": "0",
                "FID_TRGT_CLS_CODE": "0",
                "FID_TRGT_EXLS_CLS_CODE": "0000000000",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": "",
                "FID_INPUT_DATE_1": "",
            },
            fallback_method="volumeRank",
        )
    elif input_id == "rest_volume_power_rank":
        result = _kis_market_read(
            adapter,
            token,
            step="rest_volume_power_rank",
            path="/uapi/domestic-stock/v1/ranking/volume-power",
            tr_id="FHPST01680000",
            params={
                "fid_trgt_exls_cls_code": "0",
                "fid_cond_mrkt_div_code": "J",
                "fid_cond_scr_div_code": "20168",
                "fid_input_iscd": "0000",
                "fid_div_cls_code": "0",
                "fid_input_price_1": "",
                "fid_input_price_2": "",
                "fid_vol_cnt": "",
                "fid_trgt_cls_code": "0",
            },
            fallback_method="volumePowerRank",
        )
    elif input_id == "rest_fluctuation_rank":
        result = _kis_market_read(
            adapter,
            token,
            step="rest_fluctuation_rank",
            path="/uapi/domestic-stock/v1/ranking/fluctuation",
            tr_id="FHPST01700000",
            params={
                "fid_rsfl_rate2": "",
                "fid_cond_mrkt_div_code": "J",
                "fid_cond_scr_div_code": "20170",
                "fid_input_iscd": "0000",
                "fid_rank_sort_cls_code": "0",
                "fid_input_cnt_1": "20",
                "fid_prc_cls_code": "0",
                "fid_input_price_1": "",
                "fid_input_price_2": "",
                "fid_vol_cnt": "",
                "fid_trgt_cls_code": "0",
                "fid_trgt_exls_cls_code": "0",
                "fid_div_cls_code": "0",
                "fid_rsfl_rate1": "",
            },
            fallback_method="fluctuationRank",
        )
    elif input_id == "rest_program_trading_aggregate":
        krx = _program_trade_today(adapter, token, market_class="K")
        _sleep_for_kis_gap(config)
        kosdaq = _program_trade_today(adapter, token, market_class="Q")
        rows_preview = list(krx.get("rows_preview") or []) + list(kosdaq.get("rows_preview") or [])
        result = {
            "step": "rest_program_trading_aggregate",
            "status": "pass" if krx.get("status") == "pass" and kosdaq.get("status") == "pass" else "warn",
            "http_status": krx.get("http_status") or kosdaq.get("http_status"),
            "rt_cd": krx.get("rt_cd") or kosdaq.get("rt_cd"),
            "msg_cd": krx.get("msg_cd") or kosdaq.get("msg_cd"),
            "row_count": len(rows_preview),
            "rows_preview": rows_preview[:10],
            "market_classes": {"K": krx, "Q": kosdaq},
            "endpoint_called": True,
            "broker_order_surface": False,
            "raw_response_stored": False,
        }
    else:
        return _blocked_input_row(input_id, "safe_blocked_not_in_allowlist")

    result.update(
        {
            "input_id": input_id,
            "paper_read_only": True,
            "order_cancel_modify_called": False,
        }
    )
    return result


def _mark_audit_calls(audit: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    payload = dict(audit)
    called_by_input = {
        str(row.get("input_id") or ""): bool(row.get("endpoint_called"))
        for row in rows
    }
    entries = []
    for entry in payload.get("entries") or []:
        next_entry = dict(entry)
        next_entry["endpoint_called"] = called_by_input.get(str(next_entry.get("input_id") or ""), False)
        next_entry["broker_order_surface"] = False
        entries.append(next_entry)
    payload["entries"] = entries
    payload["order_cancel_modify_called"] = False
    payload["live_domain_calls_made"] = False
    return payload


def _overall_status_from_input_rows(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "blocked_no_inputs"
    statuses = [str(row.get("status") or "") for row in rows]
    if any(status in {"collector_exception", "fail"} for status in statuses):
        return "warn_partial_kis_market_read"
    if any(status.startswith("blocked") or status.startswith("safe_blocked") for status in statuses):
        return "warn_partial_kis_market_read"
    if all(status == "pass" for status in statuses):
        return "ok"
    return "warn_partial_kis_market_read"


def buildCompiledWatchFromKisSnapshot(
    snapshot: Mapping[str, Any],
    *,
    config: Optional[Mapping[str, Any]] = None,
    at: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = at or _now_kst()
    source_config = dict(config or {})
    seen: set[str] = set()
    candidates: list[Dict[str, Any]] = []
    valid_until = (now + timedelta(minutes=10)).replace(microsecond=0).isoformat()
    default_cash = int(source_config.get("default_order_cash_krw") or 100_000)
    position_size_pct = int(source_config.get("position_size_pct") or 10)

    for source in _iter_market_rows(snapshot):
        row = dict(source.get("row") or {})
        input_id = str(source.get("input_id") or "kis_market").strip()
        symbol = _first_present(row, "mksc_shrn_iscd", "stck_shrn_iscd", "pdno")
        if not symbol or symbol in seen:
            continue
        price = _parse_krw_price(_first_present(row, "stck_prpr", "askp1", "bidp1"))
        name = _first_present(row, "hts_kor_isnm", "prdt_abrv_name") or symbol
        if not _is_candidate_row(input_id=input_id, symbol=symbol, name=name, price=price):
            continue
        seen.add(symbol)
        lower = max(1, int(price * 0.995))
        upper = max(lower, int(price * 1.005))
        stop_loss = max(1, int(price * 0.97))
        take_profit = max(price + 1, int(price * 1.03))
        rank = _first_present(row, "data_rank", "rank") or str(len(candidates) + 1)
        candidate_id = f"kis_{input_id}_{symbol}_{now.strftime('%H%M%S')}"
        candidates.append(
            {
                "schema_version": "compiled_watch/v0",
                "artifact_id": f"art_watch_{candidate_id}",
                "condition_card_id": f"condition_{candidate_id}",
                "candidate_id": candidate_id,
                "symbol": symbol,
                "ticker": symbol,
                "name": name,
                "source_ids": [str(snapshot.get("artifact_id") or "kis_market_snapshot"), input_id],
                "created_at_kst": now.isoformat(),
                "valid_until_kst": valid_until,
                "compiled_at_kst": now.isoformat(),
                "venue_route": "KRX",
                "watch_state": "compiled_watch",
                "watch_conditions": [
                    {
                        "watch_condition_id": f"{candidate_id}:kis_rank",
                        "type": "source_freshness",
                        "definition": {
                            "source": input_id,
                            "rank": rank,
                            "price_krw": price,
                        },
                    }
                ],
                "risk_refs": ["HWISTOCK-MOD-001", "HWISTOCK-UNIT-013"],
                "entry_intent": {
                    "entry_zone": [lower, upper],
                    "entry_price_krw": price,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "trailing_stop_pct": 1.2,
                    "position_size_pct": position_size_pct,
                    "planned_order_cash_krw": default_cash,
                    "cancel_if_not_filled_until": valid_until,
                },
                "exit_plan": {
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "trailing_stop_pct": 1.2,
                },
                "no_broker_call": True,
                "non_executable": True,
                "approved_adapter_enabled": False,
            }
        )
        if len(candidates) >= 5:
            break

    return {
        "schema_version": "compiled_watch_batch/v0",
        "artifact_id": f"art_compiled_watch_{now.strftime('%Y%m%d_%H%M%S')}",
        "artifact_type": "compiled_watch_batch",
        "producer": "kis_intraday_market_collector",
        "produced_at_kst": now.isoformat(),
        "valid_until_kst": valid_until,
        "items": candidates,
        "candidate_count": len(candidates),
        "source_snapshot_ref": str(snapshot.get("artifact_id") or ""),
        "paper_only": True,
        "no_broker_call": True,
        "no_order_submission": True,
    }


def _iter_market_rows(snapshot: Mapping[str, Any]) -> Sequence[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    for input_result in snapshot.get("input_results") or []:
        if not isinstance(input_result, Mapping):
            continue
        input_id = str(input_result.get("input_id") or input_result.get("step") or "").strip()
        for row in input_result.get("rows_preview") or []:
            if isinstance(row, Mapping):
                rows.append({"input_id": input_id, "row": dict(row)})
        market_classes = input_result.get("market_classes")
        if isinstance(market_classes, Mapping):
            for class_id, nested in market_classes.items():
                if not isinstance(nested, Mapping):
                    continue
                for row in nested.get("rows_preview") or []:
                    if isinstance(row, Mapping):
                        rows.append({"input_id": f"{input_id}:{class_id}", "row": dict(row)})
    return rows


def _first_present(row: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", [], {}):
            return str(value).strip()
    return ""


def _parse_krw_price(value: Any) -> int:
    raw = str(value or "").strip().replace(",", "")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return 0
    try:
        return int(digits)
    except ValueError:
        return 0


def _is_candidate_row(*, input_id: str, symbol: str, name: str, price: int) -> bool:
    if input_id.startswith("krx_realtime_"):
        return False
    if not (symbol.isdigit() and len(symbol) == 6):
        return False
    if price < 1000:
        return False
    lowered_name = str(name or "").lower()
    excluded_fragments = (
        "kodex",
        "tiger",
        "ace ",
        "kbstar",
        "sol ",
        "etn",
        "인버스",
        "레버리지",
        "선물",
        "스팩",
        "채권",
    )
    return not any(fragment in lowered_name for fragment in excluded_fragments)


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
    paths = {"latest_path": str(latest), "stamped_path": str(stamped)}
    compiled_watch = payload.get("compiled_watch")
    if isinstance(compiled_watch, Mapping):
        paths.update(writeCompiledWatchEvidence(compiled_watch, data_root=root, at=now))
    return paths


def writeCompiledWatchEvidence(
    payload: Mapping[str, Any],
    *,
    data_root: Optional[Path] = None,
    at: Optional[datetime] = None,
) -> Dict[str, str]:
    now = at or _now_kst()
    root = data_root or DEFAULT_DATA_ROOT
    output_dir = root / "compiled-watch" / now.date().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    latest = output_dir / "compiled-watch-latest.json"
    stamped = output_dir / f"compiled-watch-{now.strftime('%H%M%S')}.json"
    text = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = latest.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(latest)
    stamped.write_text(text, encoding="utf-8")
    return {"compiled_watch_latest_path": str(latest), "compiled_watch_stamped_path": str(stamped)}


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
