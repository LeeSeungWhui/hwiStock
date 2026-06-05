"""
KIS paper/mock adapter boundary for HWISTOCK-UNIT-010.

Paper-domain only. The adapter sanitizes responses, rejects live/unknown
domains before transport, and never creates fake broker state. Tests inject a
fake transport; the default transport is disabled so importing this module never
touches the network.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

DEFAULT_KIS_PAPER_BASE_URL = "https://openapivts.koreainvestment.com:29443"
PAPER_HOST = "openapivts.koreainvestment.com"
REQUIRED_ENV_KEYS = (
    "KIS_PAPER_APP_KEY",
    "KIS_PAPER_APP_SECRET",
    "KIS_PAPER_ACCOUNT_NO",
    "KIS_PAPER_ACCOUNT_PRODUCT_CODE",
)


class KisPaperAdapterError(RuntimeError):
    """Raised only for local policy/config errors, not raw KIS response bodies."""


class PaperNetworkDisabledError(KisPaperAdapterError):
    pass


def validatePaperBaseUrl(base_url: Optional[str]) -> str:
    raw = (base_url or DEFAULT_KIS_PAPER_BASE_URL).strip().rstrip("/")
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme != "https":
        raise KisPaperAdapterError("kis_paper_base_url_must_be_https")
    if parsed.hostname != PAPER_HOST:
        raise KisPaperAdapterError("kis_paper_base_url_not_paper_domain")
    return raw


def loadKisPaperCapabilityFlags() -> Dict[str, Any]:
    return {
        "supports_paper_krx_order": True,
        "supports_paper_nxt_order": False,
        "supports_paper_sor_order": False,
        "supports_paper_krx_realtime": True,
        "supports_paper_nxt_realtime": False,
        "supports_paper_integrated_realtime": False,
        "supports_paper_cancel_order": True,
        "supports_paper_cancelable_query": False,
        "supports_paper_sellable_quantity_query": False,
        "supports_paper_realized_pnl_query": False,
        "supports_paper_holiday_query": False,
        "unsupported_branch_policy": {
            "nxt_order": "disabled_branch",
            "sor_order": "disabled_branch",
            "integrated_realtime": "disabled_branch",
            "cancelable_query": "local_fallback",
            "sellable_quantity_query": "local_fallback",
            "realized_pnl_query": "local_fallback",
            "holiday_query": "local_fallback",
        },
    }


def describeKisPaperEnv(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    missing = [key for key in REQUIRED_ENV_KEYS if not str(source.get(key, "")).strip()]
    return {
        "envPath": "/home/hwi/.config/hwistock/kis-paper.env",
        "requiredKeys": list(REQUIRED_ENV_KEYS),
        "missingKeys": missing,
        "credentialsPresent": not missing,
        "credentialValuesPrinted": False,
    }


def sanitizeKisResponse(
    response: Mapping[str, Any],
    *,
    step: str,
    row_count_key: Optional[str] = None,
) -> Dict[str, Any]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    out = payload.get("output")
    out1 = payload.get("output1")
    rows: Any = payload.get(row_count_key) if row_count_key else None
    result = {
        "step": step,
        "http_status": response.get("http_status"),
        "rt_cd": payload.get("rt_cd"),
        "msg_cd": payload.get("msg_cd"),
        "status": "pass"
        if response.get("http_status") == 200 and str(payload.get("rt_cd", "0")) in {"0", ""}
        else "warn",
        "raw_response_stored": False,
    }
    if row_count_key:
        result["row_count"] = len(rows) if isinstance(rows, list) else (1 if isinstance(rows, Mapping) else 0)
    elif isinstance(out, list):
        result["row_count"] = len(out)
    elif isinstance(out1, list):
        result["row_count"] = len(out1)
    return result


class NetworkDisabledTransport:
    def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        body: Optional[Mapping[str, Any]] = None,
        timeout: int = 20,
    ) -> Dict[str, Any]:
        raise PaperNetworkDisabledError("kis_paper_network_disabled")


class UrllibJsonTransport:
    def request_json(
        self,
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


@dataclass
class KisPaperAdapter:
    env: Optional[Mapping[str, str]] = None
    base_url: Optional[str] = None
    transport: Optional[Any] = None

    def __post_init__(self) -> None:
        self._env = self.env if self.env is not None else os.environ
        self.base_url = validatePaperBaseUrl(self.base_url or self._env.get("KIS_PAPER_BASE_URL"))
        self.transport = self.transport or NetworkDisabledTransport()

    def configSummary(self) -> Dict[str, Any]:
        return {
            "paperDomainOnly": True,
            "baseHost": urllib.parse.urlparse(str(self.base_url)).hostname,
            "env": describeKisPaperEnv(self._env),
            "capabilities": loadKisPaperCapabilityFlags(),
        }

    def missingEnvKeys(self) -> list[str]:
        return list(describeKisPaperEnv(self._env)["missingKeys"])

    def ready(self) -> bool:
        return not self.missingEnvKeys()

    def issueToken(self) -> Dict[str, Any]:
        result, _token = self.issueTokenWithValue()
        return result

    def issueTokenWithValue(self) -> tuple[Dict[str, Any], str]:
        blocked = self._blockedIfMissingEnv("oauth_token")
        if blocked:
            return blocked, ""
        response = self._request(
            "POST",
            "/oauth2/tokenP",
            body={
                "grant_type": "client_credentials",
                "appkey": self._env_value("KIS_PAPER_APP_KEY"),
                "appsecret": self._env_value("KIS_PAPER_APP_SECRET"),
            },
        )
        payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
        result = sanitizeKisResponse(response, step="oauth_token")
        token = str(payload.get("access_token") or "")
        result["token_present"] = bool(token)
        return result, token

    def revokeToken(self, token: str) -> Dict[str, Any]:
        blocked = self._blockedIfMissingEnv("oauth_revoke")
        if blocked:
            return blocked
        response = self._request(
            "POST",
            "/oauth2/revokeP",
            body={
                "appkey": self._env_value("KIS_PAPER_APP_KEY"),
                "appsecret": self._env_value("KIS_PAPER_APP_SECRET"),
                "token": token,
            },
        )
        return sanitizeKisResponse(response, step="oauth_revoke")

    def inquirePrice(self, token: str, symbol: str) -> Dict[str, Any]:
        params = urllib.parse.urlencode({"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol})
        response = self._request(
            "GET",
            f"/uapi/domestic-stock/v1/quotations/inquire-price?{params}",
            headers=self._authHeaders(token, "FHKST01010100"),
        )
        return sanitizeKisResponse(response, step="quote_inquire_price")

    def inquireBalance(self, token: str) -> Dict[str, Any]:
        response = self._request(
            "GET",
            f"/uapi/domestic-stock/v1/trading/inquire-balance?{urllib.parse.urlencode(self._accountQuery())}",
            headers=self._authHeaders(token, "VTTC8434R"),
        )
        return sanitizeKisResponse(response, step="balance_inquire", row_count_key="output1")

    def inquireBuyable(self, token: str, symbol: str, *, order_price: str = "") -> Dict[str, Any]:
        params = {
            "CANO": self._env_value("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self._env_value("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "PDNO": symbol,
            "ORD_UNPR": order_price,
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "Y",
        }
        response = self._request(
            "GET",
            f"/uapi/domestic-stock/v1/trading/inquire-psbl-order?{urllib.parse.urlencode(params)}",
            headers=self._authHeaders(token, "VTTC8908R"),
        )
        return sanitizeKisResponse(response, step="buyable_inquire_psbl_order")

    def dailyOrderFillLookup(self, token: str, *, date_yyyymmdd: str, symbol: str = "") -> Dict[str, Any]:
        params = {
            "CANO": self._env_value("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self._env_value("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "INQR_STRT_DT": date_yyyymmdd,
            "INQR_END_DT": date_yyyymmdd,
            "SLL_BUY_DVSN_CD": "00",
            "INQR_DVSN": "00",
            "PDNO": symbol,
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        response = self._request(
            "GET",
            f"/uapi/domestic-stock/v1/trading/inquire-daily-ccld?{urllib.parse.urlencode(params)}",
            headers=self._authHeaders(token, "VTTC0081R"),
        )
        return sanitizeKisResponse(response, step="daily_order_fill_inquire", row_count_key="output1")

    def placeCashOrder(self, token: str, intent: Mapping[str, Any]) -> Dict[str, Any]:
        route = str(intent.get("venue_route") or intent.get("venue") or "KRX").upper()
        if route != "KRX":
            return {
                "step": "cash_order",
                "status": "blocked",
                "reason": "kis_paper_only_supports_krx_order",
                "broker_endpoint_called": False,
            }
        side = str(intent.get("side") or "").lower()
        if side not in {"buy", "sell"}:
            return {
                "step": "cash_order",
                "status": "blocked",
                "reason": "order_side_invalid",
                "broker_endpoint_called": False,
            }
        quantity = int(intent.get("quantity") or 0)
        if quantity <= 0:
            return {
                "step": "cash_order",
                "status": "blocked",
                "reason": "order_quantity_invalid",
                "broker_endpoint_called": False,
            }
        body = {
            "CANO": self._env_value("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self._env_value("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "PDNO": str(intent.get("symbol") or "").strip(),
            "ORD_DVSN": str(intent.get("order_division") or "01"),
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(intent.get("order_price") or intent.get("price") or "0"),
        }
        tr_id = "VTTC0802U" if side == "buy" else "VTTC0801U"
        response = self._request(
            "POST",
            "/uapi/domestic-stock/v1/trading/order-cash",
            headers=self._authHeaders(token, tr_id),
            body=body,
        )
        result = sanitizeKisResponse(response, step="cash_order")
        result["broker_endpoint_called"] = True
        result["route"] = "KRX"
        result["side"] = side
        return result

    def cancelOrder(self, token: str, *, original_order_no: str, quantity: int = 0) -> Dict[str, Any]:
        body = {
            "CANO": self._env_value("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self._env_value("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": original_order_no,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": "02",
            "ORD_QTY": str(int(quantity or 0)),
            "ORD_UNPR": "0",
            "QTY_ALL_ORD_YN": "Y" if int(quantity or 0) <= 0 else "N",
        }
        response = self._request(
            "POST",
            "/uapi/domestic-stock/v1/trading/order-rvsecncl",
            headers=self._authHeaders(token, "VTTC0803U"),
            body=body,
        )
        return sanitizeKisResponse(response, step="cancel_order")

    def _blockedIfMissingEnv(self, step: str) -> Optional[Dict[str, Any]]:
        missing = self.missingEnvKeys()
        if not missing:
            return None
        return {
            "step": step,
            "status": "blocked_missing_env",
            "missing_env_keys": missing,
            "credential_values_printed": False,
            "broker_endpoint_called": False,
        }

    def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        body: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self._url(path_or_url)
        validatePaperBaseUrl(url.rsplit("/", 1)[0] if path_or_url.startswith("http") else self.base_url)
        parsed = urllib.parse.urlparse(url)
        if parsed.hostname != PAPER_HOST:
            raise KisPaperAdapterError("kis_paper_request_not_paper_domain")
        return self.transport.request_json(method, url, headers=headers, body=body)

    def _url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            parsed = urllib.parse.urlparse(path_or_url)
            if parsed.hostname != PAPER_HOST:
                raise KisPaperAdapterError("kis_paper_request_not_paper_domain")
            return path_or_url
        path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
        return f"{self.base_url}{path}"

    def _env_value(self, key: str) -> str:
        return str(self._env.get(key, "")).strip()

    def _authHeaders(self, token: str, tr_id: str) -> Dict[str, str]:
        return {
            "authorization": f"Bearer {token}",
            "appkey": self._env_value("KIS_PAPER_APP_KEY"),
            "appsecret": self._env_value("KIS_PAPER_APP_SECRET"),
            "tr_id": tr_id,
            "custtype": "P",
        }

    def _accountQuery(self) -> Dict[str, str]:
        return {
            "CANO": self._env_value("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self._env_value("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
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
