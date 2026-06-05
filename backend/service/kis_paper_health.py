"""
KIS paper/mock REST health runner.

This is an unattended read-health runner for the paper/mock environment only.
It never calls live domains, never stores raw responses, and never submits
orders. Mock order placement remains a separate explicit one-shot smoke.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.getenv("HWISTOCK_DATA_DIR", str(REPO_ROOT / "data")))
DEFAULT_BASE_URL = "https://openapivts.koreainvestment.com:29443"
SAMPLE_SYMBOL = os.getenv("HWISTOCK_KIS_HEALTH_SYMBOL", "005930").strip() or "005930"


def _now_kst() -> datetime:
    return datetime.now(KST).replace(microsecond=0)


def _required_env() -> Dict[str, str]:
    keys = [
        "KIS_PAPER_APP_KEY",
        "KIS_PAPER_APP_SECRET",
        "KIS_PAPER_ACCOUNT_NO",
        "KIS_PAPER_ACCOUNT_PRODUCT_CODE",
    ]
    return {key: os.getenv(key, "").strip() for key in keys}


def _base_url() -> str:
    raw = os.getenv("KIS_PAPER_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    if "openapivts.koreainvestment.com" not in raw:
        raise RuntimeError("kis_paper_base_url_not_paper_domain")
    return raw.rstrip("/")


def _request_json(
    method: str,
    url: str,
    *,
    headers: Optional[Mapping[str, str]] = None,
    body: Optional[Mapping[str, Any]] = None,
    timeout: int = 20,
) -> Dict[str, Any]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8", **dict(headers or {})},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    try:
        payload = json.loads(raw.decode("utf-8", errors="replace")) if raw else {}
    except json.JSONDecodeError:
        payload = {"parse_error": True}
    return {"http_status": status, "payload": payload}


def _step_result(name: str, response: Mapping[str, Any], *, row_count_key: Optional[str] = None) -> Dict[str, Any]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    result = {
        "step": name,
        "http_status": response.get("http_status"),
        "rt_cd": payload.get("rt_cd"),
        "msg_cd": payload.get("msg_cd"),
        "status": "pass" if response.get("http_status") == 200 and str(payload.get("rt_cd", "0")) in {"0", ""} else "warn",
    }
    if row_count_key:
        rows = payload.get(row_count_key)
        result["row_count"] = len(rows) if isinstance(rows, list) else (1 if isinstance(rows, Mapping) else 0)
    return result


def _auth_headers(token: str, app_key: str, app_secret: str, tr_id: str) -> Dict[str, str]:
    return {
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": tr_id,
        "custtype": "P",
    }


def run_kis_paper_health_once(*, data_root: Path = DEFAULT_DATA_ROOT) -> Dict[str, Any]:
    now = _now_kst()
    env = _required_env()
    missing = sorted(key for key, value in env.items() if not value)
    evidence_dir = data_root / "evidence" / now.date().isoformat()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    health_path = evidence_dir / "kis-paper-health.json"
    result: Dict[str, Any] = {
        "event": "kis_paper_health_once",
        "timestamp_kst": now.isoformat(),
        "paper_domain_only": True,
        "live_domain_calls_made": False,
        "orders_enabled": False,
        "order_endpoint_called": False,
        "credential_values_printed": False,
        "raw_responses_stored": False,
        "status": "blocked_missing_env" if missing else "pending",
        "missing_env_keys": missing,
        "steps": [],
    }
    if missing:
        health_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result["artifact_path"] = str(health_path)
        return result

    base = _base_url()
    app_key = env["KIS_PAPER_APP_KEY"]
    app_secret = env["KIS_PAPER_APP_SECRET"]
    account_no = env["KIS_PAPER_ACCOUNT_NO"]
    product_code = env["KIS_PAPER_ACCOUNT_PRODUCT_CODE"]
    token = ""
    try:
        token_response = _request_json(
            "POST",
            f"{base}/oauth2/tokenP",
            body={"grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret},
        )
        token_payload = token_response.get("payload") if isinstance(token_response.get("payload"), Mapping) else {}
        token = str(token_payload.get("access_token") or "")
        result["steps"].append(
            {
                "step": "oauth_token",
                "http_status": token_response.get("http_status"),
                "status": "pass" if token_response.get("http_status") == 200 and bool(token) else "warn",
                "token_present": bool(token),
            }
        )
        if not token:
            result["status"] = "blocked_token_missing"
            health_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result["artifact_path"] = str(health_path)
            return result
        time.sleep(1.35)

        quote_params = urllib.parse.urlencode({"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": SAMPLE_SYMBOL})
        quote = _request_json(
            "GET",
            f"{base}/uapi/domestic-stock/v1/quotations/inquire-price?{quote_params}",
            headers=_auth_headers(token, app_key, app_secret, "FHKST01010100"),
        )
        result["steps"].append(_step_result("quote_inquire_price", quote))
        time.sleep(1.35)

        common_account = {
            "CANO": account_no,
            "ACNT_PRDT_CD": product_code,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        balance = _request_json(
            "GET",
            f"{base}/uapi/domestic-stock/v1/trading/inquire-balance?{urllib.parse.urlencode(common_account)}",
            headers=_auth_headers(token, app_key, app_secret, "VTTC8434R"),
        )
        result["steps"].append(_step_result("balance_inquire", balance, row_count_key="output1"))
        time.sleep(1.35)

        buyable_params = {
            "CANO": account_no,
            "ACNT_PRDT_CD": product_code,
            "PDNO": SAMPLE_SYMBOL,
            "ORD_UNPR": "",
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "Y",
        }
        buyable = _request_json(
            "GET",
            f"{base}/uapi/domestic-stock/v1/trading/inquire-psbl-order?{urllib.parse.urlencode(buyable_params)}",
            headers=_auth_headers(token, app_key, app_secret, "VTTC8908R"),
        )
        result["steps"].append(_step_result("buyable_inquire_psbl_order", buyable))
        time.sleep(1.35)

        today = now.strftime("%Y%m%d")
        daily_params = {
            "CANO": account_no,
            "ACNT_PRDT_CD": product_code,
            "INQR_STRT_DT": today,
            "INQR_END_DT": today,
            "SLL_BUY_DVSN_CD": "00",
            "INQR_DVSN": "00",
            "PDNO": "",
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        daily = _request_json(
            "GET",
            f"{base}/uapi/domestic-stock/v1/trading/inquire-daily-ccld?{urllib.parse.urlencode(daily_params)}",
            headers=_auth_headers(token, app_key, app_secret, "VTTC0081R"),
        )
        result["steps"].append(_step_result("daily_order_fill_inquire", daily, row_count_key="output1"))
    except Exception as exc:  # noqa: BLE001 - health runner records sanitized failure.
        result["steps"].append({"step": "exception", "status": "fail", "error_class": exc.__class__.__name__, "message": str(exc)[:200]})
    finally:
        if token:
            try:
                revoke = _request_json(
                    "POST",
                    f"{base}/oauth2/revokeP",
                    body={"appkey": app_key, "appsecret": app_secret, "token": token},
                )
                result["steps"].append(
                    {
                        "step": "oauth_revoke",
                        "http_status": revoke.get("http_status"),
                        "status": "pass" if revoke.get("http_status") in (200, 403) else "warn",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                result["steps"].append({"step": "oauth_revoke", "status": "warn", "error_class": exc.__class__.__name__})

    failing = [step for step in result["steps"] if step.get("status") == "fail"]
    result["status"] = "fail" if failing else "ok"
    health_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["artifact_path"] = str(health_path)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="KIS paper/mock read-health runner")
    parser.add_argument("--once", action="store_true", help="Run one paper/mock read-health tick")
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT), help="Runtime data root")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.once:
        parser.print_help()
        return 2
    result = run_kis_paper_health_once(data_root=Path(args.data_root))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"ok", "blocked_missing_env", "blocked_token_missing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
