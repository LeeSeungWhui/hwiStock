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
from typing import Any, Dict, Mapping, Optional, Sequence

DEFAULT_KIS_PAPER_BASE_URL = "https://openapivts.koreainvestment.com:29443"
DEFAULT_KIS_WEBSOCKET_URL = "ws://ops.koreainvestment.com:31000"
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
        "supports_paper_integrated_realtime": True,
        "supports_paper_cancel_order": True,
        "supports_paper_cancelable_query": False,
        "supports_paper_sellable_quantity_query": False,
        "supports_paper_realized_pnl_query": False,
        "supports_paper_holiday_query": False,
        "supports_real_krx_realtime": True,
        "supports_real_integrated_realtime": True,
        "supports_real_nxt_realtime": True,
        "unsupported_branch_policy": {
            "nxt_order": "disabled_branch",
            "sor_order": "disabled_branch",
            "nxt_realtime": "real_mode_only",
            "integrated_realtime": "enabled_in_paper_and_real_modes",
            "cancelable_query": "paper_mock_unsupported",
            "sellable_quantity_query": "paper_mock_unsupported",
            "realized_pnl_query": "paper_mock_unsupported",
            "holiday_query": "paper_mock_unsupported",
        },
    }


def describeKisPaperEnv(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    missing = [key for key in REQUIRED_ENV_KEYS if not str(source.get(key, "")).strip()]
    return {
        "envPath": "/home/hwi/.config/hwistock/hwistockApi.env",
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


def toIntOrNone(value: Any) -> Optional[int]:
    if value is None:
        return None
    raw = str(value).strip().replace(",", "")
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def firstStringByKeys(container: Mapping[str, Any], keys: Sequence[str]) -> str:
    for key in keys:
        value = container.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def firstMapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, list):
        for item in value:
            if isinstance(item, Mapping):
                return dict(item)
    return {}


def firstIntByKeys(container: Any, keys: tuple[str, ...]) -> Optional[int]:
    if isinstance(container, Mapping):
        for key in keys:
            parsed = toIntOrNone(container.get(key))
            if parsed is not None:
                return parsed
        for value in container.values():
            nested = firstIntByKeys(value, keys)
            if nested is not None:
                return nested
    elif isinstance(container, list):
        for item in container:
            nested = firstIntByKeys(item, keys)
            if nested is not None:
                return nested
    return None


def _payloadRows(response: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    rows = payload.get(key)
    if isinstance(rows, Mapping):
        return [rows]
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, Mapping)]
    return []


def _normalizeKisSide(row: Mapping[str, Any]) -> str:
    raw = firstStringByKeys(
        row,
        (
            "sll_buy_dvsn_cd",
            "SLL_BUY_DVSN_CD",
            "sll_buy_dvsn_name",
            "ord_dvsn_name",
            "side",
        ),
    ).lower()
    if raw in {"02", "2", "buy", "b"} or "매수" in raw:
        return "buy"
    if raw in {"01", "1", "sell", "s"} or "매도" in raw:
        return "sell"
    return raw


def extractKisBalancePositionsPayload(response: Mapping[str, Any]) -> list[Dict[str, Any]]:
    positions: list[Dict[str, Any]] = []
    for row in _payloadRows(response, "output1"):
        symbol = firstStringByKeys(
            row,
            (
                "pdno",
                "PDNO",
                "stck_shrn_iscd",
                "mksc_shrn_iscd",
                "isu_cd",
                "code",
                "symbol",
            ),
        )
        if not symbol:
            continue
        quantity = firstIntByKeys(row, ("hldg_qty", "hold_qty", "evlu_qty", "qty", "quantity"))
        average_price = firstIntByKeys(row, ("pchs_avg_pric", "pchs_avg_price", "avg_price", "average_price"))
        current_price = firstIntByKeys(row, ("prpr", "stck_prpr", "now_pric", "cur_price", "current_price"))
        sellable_quantity = firstIntByKeys(
            row,
            ("ord_psbl_qty", "sll_psbl_qty", "sell_psbl_qty", "ord_psbl_qty1", "sellable_quantity"),
        )
        eval_amount = firstIntByKeys(row, ("evlu_amt", "evlu_pfls_amt_smtl", "stock_eval_krw", "eval_amount_krw"))
        pnl = firstIntByKeys(row, ("evlu_pfls_amt", "rlzt_pfls", "pnl_krw"))
        positions.append(
            {
                "symbol": symbol,
                "ticker": symbol,
                "name": firstStringByKeys(row, ("prdt_name", "prdt_abrv_name", "hts_kor_isnm", "name")),
                "quantity": quantity,
                "sellable_quantity": sellable_quantity,
                "average_price": average_price,
                "current_price": current_price,
                "eval_amount_krw": eval_amount,
                "pnl_krw": pnl,
                "source": "kis_balance_output1",
            }
        )
    return positions[:50]


def extractKisDailyFillRowsPayload(response: Mapping[str, Any]) -> list[Dict[str, Any]]:
    fills: list[Dict[str, Any]] = []
    for row in _payloadRows(response, "output1"):
        symbol = firstStringByKeys(
            row,
            (
                "pdno",
                "PDNO",
                "stck_shrn_iscd",
                "mksc_shrn_iscd",
                "isu_cd",
                "code",
                "symbol",
            ),
        )
        order_no = firstStringByKeys(row, ("odno", "ODNO", "ord_no", "order_no"))
        if not symbol and not order_no:
            continue
        filled_quantity = firstIntByKeys(row, ("tot_ccld_qty", "ccld_qty", "filled_qty", "filled_quantity"))
        order_quantity = firstIntByKeys(row, ("ord_qty", "order_qty", "quantity"))
        remaining_quantity = firstIntByKeys(row, ("rmn_qty", "unfilled_qty", "remaining_quantity"))
        filled_price = firstIntByKeys(row, ("avg_prvs", "ccld_unpr", "avg_price", "filled_price"))
        order_price = firstIntByKeys(row, ("ord_unpr", "order_price", "price"))
        status = firstStringByKeys(row, ("ccld_dvsn_name", "ord_dvsn_name", "fill_status", "status"))
        if not status:
            if filled_quantity is not None and filled_quantity > 0 and (remaining_quantity in (None, 0)):
                status = "filled"
            elif remaining_quantity and remaining_quantity > 0:
                status = "partially_filled_or_open"
        fills.append(
            {
                "symbol": symbol,
                "ticker": symbol,
                "side": _normalizeKisSide(row),
                "order_no": order_no,
                "filled_quantity": filled_quantity,
                "order_quantity": order_quantity,
                "remaining_quantity": remaining_quantity,
                "filled_price": filled_price,
                "order_price": order_price,
                "fill_status": status,
                "source": "kis_daily_ccld_output1",
            }
        )
    return fills[:100]


def summarizeKisBalancePayload(response: Mapping[str, Any]) -> Dict[str, Any]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    output1 = payload.get("output1")
    output2 = firstMapping(payload.get("output2"))
    positions = output1 if isinstance(output1, list) else []
    return {
        "cash_balance_krw": firstIntByKeys(
            output2,
            (
                "dnca_tot_amt",
                "prvs_rcdl_excc_amt",
                "nxdy_excc_amt",
                "d2_auto_rdpt_amt",
                "tot_evlu_amt",
            ),
        ),
        "total_eval_krw": firstIntByKeys(
            output2,
            (
                "tot_evlu_amt",
                "tot_asst_amt",
                "nass_amt",
                "evlu_amt_smtl_amt",
            ),
        ),
        "stock_eval_krw": firstIntByKeys(
            output2,
            (
                "scts_evlu_amt",
                "evlu_amt_smtl_amt",
            ),
        ),
        "today_pnl_krw": firstIntByKeys(
            output2,
            (
                "evlu_pfls_smtl_amt",
                "asst_icdc_amt",
            ),
        ),
        "positions_count": len(positions),
    }


def summarizeKisBuyablePayload(response: Mapping[str, Any]) -> Dict[str, Any]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    output = payload.get("output")
    return {
        "buyable_cash_krw": firstIntByKeys(
            output,
            (
                "ord_psbl_cash",
                "ord_psbl_sbst",
                "ruse_psbl_amt",
                "max_buy_amt",
                "nrcvb_buy_amt",
            ),
        )
    }


def summarizeKisSellablePayload(response: Mapping[str, Any]) -> Dict[str, Any]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    output = payload.get("output")
    return {
        "sellable_quantity": firstIntByKeys(
            output,
            (
                "ord_psbl_qty",
                "sll_psbl_qty",
                "sell_psbl_qty",
                "ord_psbl_qty1",
            ),
        )
    }


def summarizeKisRealizedPnlPayload(response: Mapping[str, Any]) -> Dict[str, Any]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    output2 = payload.get("output2")
    output1 = payload.get("output1")
    realized_pnl = firstIntByKeys(output2, ("rlzt_pfls",))
    if realized_pnl is None:
        realized_pnl = firstIntByKeys(output1, ("rlzt_pfls", "real_evlu_pfls"))
    real_eval_pnl = firstIntByKeys(output2, ("real_evlu_pfls",))
    if real_eval_pnl is None:
        real_eval_pnl = firstIntByKeys(output1, ("real_evlu_pfls",))
    eval_pnl_sum = firstIntByKeys(output2, ("evlu_pfls_smtl_amt",))
    if eval_pnl_sum is None:
        eval_pnl_sum = firstIntByKeys(output1, ("evlu_pfls_smtl_amt",))
    return {
        "realized_pnl_krw": realized_pnl,
        "real_eval_pnl_krw": real_eval_pnl,
        "eval_pnl_sum_krw": eval_pnl_sum,
    }


def summarizeKisCancelableOrdersPayload(response: Mapping[str, Any]) -> Dict[str, Any]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    output = payload.get("output")
    rows = output if isinstance(output, list) else []
    return {
        "cancelable_order_count": len(rows),
        "cancelable_order_numbers": [
            str(row.get("odno") or row.get("ODNO") or "").strip()
            for row in rows
            if isinstance(row, Mapping) and str(row.get("odno") or row.get("ODNO") or "").strip()
        ][:20],
    }


def unsupportedPaperMockStep(
    step: str,
    *,
    summaryKey: Optional[str] = None,
    summary: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "step": step,
        "status": "skipped_provider_unsupported",
        "reason": "kis_paper_mock_tr_unsupported_by_local_reference",
        "broker_endpoint_called": False,
        "raw_response_stored": False,
        "credential_values_printed": False,
    }
    if summaryKey:
        result[summaryKey] = dict(summary or {})
    return result


def extractKisOrderIdentifiers(response: Mapping[str, Any]) -> Dict[str, str]:
    payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
    output = firstMapping(payload.get("output"))
    order_no = str(output.get("ODNO") or output.get("odno") or "").strip()
    orgno = str(output.get("KRX_FWDG_ORD_ORGNO") or output.get("krx_fwdg_ord_orgno") or "").strip()
    return {
        "broker_order_no": order_no,
        "krx_forwarding_order_orgno": orgno,
    }


class NetworkDisabledTransport:
    def requestJson(
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
    def requestJson(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        body: Optional[Mapping[str, Any]] = None,
        timeout: int = 20,
    ) -> Dict[str, Any]:
        jsonTransportContent = body
        requestBodyBytes = (
            json.dumps(jsonTransportContent, ensure_ascii=False).encode("utf-8")
            if jsonTransportContent is not None
            else None
        )
        req = urllib.request.Request(
            url,
            data=requestBodyBytes,
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


class WebSocketClientTransport:
    def subscribeOnce(
        self,
        url: str,
        frame: Mapping[str, Any],
        *,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        try:
            import websocket  # type: ignore[import-not-found]
        except ImportError:
            return {
                "status": "blocked_websocket_dependency_missing",
                "dependency": "websocket-client",
                "ack_received": False,
                "raw_response_stored": False,
            }

        ws = websocket.create_connection(url, timeout=timeout)
        try:
            ws.send(json.dumps(dict(frame), ensure_ascii=False))
            raw = ws.recv()
        finally:
            ws.close()
        parsed: Any
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else {"binary_ack": True}
        except json.JSONDecodeError:
            parsed = {"text_ack": str(raw)[:200]}
        return {
            "status": "pass",
            "ack_received": True,
            "payload": parsed,
            "raw_response_stored": False,
        }


@dataclass
class KisPaperAdapter:
    env: Optional[Mapping[str, str]] = None
    base_url: Optional[str] = None
    transport: Optional[Any] = None
    websocket_transport: Optional[Any] = None

    def __post_init__(self) -> None:
        self._env = self.env if self.env is not None else os.environ
        self.base_url = validatePaperBaseUrl(self.base_url or self._env.get("KIS_PAPER_BASE_URL"))
        self.transport = self.transport or NetworkDisabledTransport()
        self.websocket_transport = self.websocket_transport or WebSocketClientTransport()

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
        blocked = self.blockedIfMissingEnv("oauth_token")
        if blocked:
            return blocked, ""
        response = self.requestBrokerJson(
            "POST",
            "/oauth2/tokenP",
            body={
                "grant_type": "client_credentials",
                "appkey": self.envValue("KIS_PAPER_APP_KEY"),
                "appsecret": self.envValue("KIS_PAPER_APP_SECRET"),
            },
        )
        payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
        result = sanitizeKisResponse(response, step="oauth_token")
        token = str(payload.get("access_token") or "")
        result["token_present"] = bool(token)
        return result, token

    def revokeToken(self, token: str) -> Dict[str, Any]:
        blocked = self.blockedIfMissingEnv("oauth_revoke")
        if blocked:
            return blocked
        response = self.requestBrokerJson(
            "POST",
            "/oauth2/revokeP",
            body={
                "appkey": self.envValue("KIS_PAPER_APP_KEY"),
                "appsecret": self.envValue("KIS_PAPER_APP_SECRET"),
                "token": token,
            },
        )
        return sanitizeKisResponse(response, step="oauth_revoke")

    def issueWebsocketApproval(self) -> Dict[str, Any]:
        result, _approval_key = self.issueWebsocketApprovalWithValue()
        return result

    def issueWebsocketApprovalWithValue(self) -> tuple[Dict[str, Any], str]:
        blocked = self.blockedIfMissingEnv("websocket_approval")
        if blocked:
            return blocked, ""
        response = self.requestBrokerJson(
            "POST",
            "/oauth2/Approval",
            body={
                "grant_type": "client_credentials",
                "appkey": self.envValue("KIS_PAPER_APP_KEY"),
                "secretkey": self.envValue("KIS_PAPER_APP_SECRET"),
            },
        )
        payload = response.get("payload") if isinstance(response.get("payload"), Mapping) else {}
        approval_key = str(payload.get("approval_key") or "")
        result = sanitizeKisResponse(response, step="websocket_approval")
        result["approval_key_present"] = bool(approval_key)
        result["credential_values_printed"] = False
        return result, approval_key

    def inquirePrice(self, token: str, symbol: str) -> Dict[str, Any]:
        params = urllib.parse.urlencode({"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol})
        response = self.requestBrokerJson(
            "GET",
            f"/uapi/domestic-stock/v1/quotations/inquire-price?{params}",
            headers=self.authHeaders(token, "FHKST01010100"),
        )
        return sanitizeKisResponse(response, step="quote_inquire_price")

    def inquireOrderbook(self, token: str, symbol: str) -> Dict[str, Any]:
        params = urllib.parse.urlencode({"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol})
        response = self.requestBrokerJson(
            "GET",
            f"/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn?{params}",
            headers=self.authHeaders(token, "FHKST01010200"),
        )
        return sanitizeKisResponse(response, step="quote_inquire_orderbook")

    def inquireBalance(self, token: str) -> Dict[str, Any]:
        response = self.requestBrokerJson(
            "GET",
            f"/uapi/domestic-stock/v1/trading/inquire-balance?{urllib.parse.urlencode(self.accountQuery())}",
            headers=self.authHeaders(token, "VTTC8434R"),
        )
        result = sanitizeKisResponse(response, step="balance_inquire", row_count_key="output1")
        result["dashboard_account_summary"] = summarizeKisBalancePayload(response)
        result["dashboard_positions"] = extractKisBalancePositionsPayload(response)
        return result

    def inquireBuyable(self, token: str, symbol: str, *, order_price: str = "") -> Dict[str, Any]:
        params = {
            "CANO": self.envValue("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self.envValue("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "PDNO": symbol,
            "ORD_UNPR": order_price,
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "Y",
        }
        response = self.requestBrokerJson(
            "GET",
            f"/uapi/domestic-stock/v1/trading/inquire-psbl-order?{urllib.parse.urlencode(params)}",
            headers=self.authHeaders(token, "VTTC8908R"),
        )
        result = sanitizeKisResponse(response, step="buyable_inquire_psbl_order")
        result["dashboard_buyable_summary"] = summarizeKisBuyablePayload(response)
        return result

    def inquireSellable(self, token: str, symbol: str) -> Dict[str, Any]:
        del token, symbol
        return unsupportedPaperMockStep(
            "sellable_inquire_psbl_sell",
            summaryKey="dashboard_sellable_summary",
            summary={"sellable_quantity": None},
        )

    def inquireRealizedPnl(self, token: str) -> Dict[str, Any]:
        del token
        return unsupportedPaperMockStep(
            "realized_pnl_inquire",
            summaryKey="dashboard_realized_pnl_summary",
            summary={"realized_pnl_krw": None, "real_eval_pnl_krw": None, "eval_pnl_sum_krw": None},
        )

    def dailyOrderFillLookup(self, token: str, *, date_yyyymmdd: str, symbol: str = "") -> Dict[str, Any]:
        params = {
            "CANO": self.envValue("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self.envValue("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
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
        response = self.requestBrokerJson(
            "GET",
            f"/uapi/domestic-stock/v1/trading/inquire-daily-ccld?{urllib.parse.urlencode(params)}",
            headers=self.authHeaders(token, "VTTC0081R"),
        )
        result = sanitizeKisResponse(response, step="daily_order_fill_inquire", row_count_key="output1")
        result["dashboard_daily_fills"] = extractKisDailyFillRowsPayload(response)
        return result

    def inquireCancelableOrders(self, token: str, *, side: str = "all") -> Dict[str, Any]:
        del token, side
        return unsupportedPaperMockStep(
            "cancelable_order_inquire",
            summaryKey="dashboard_cancelable_summary",
            summary={"cancelable_order_count": 0, "cancelable_order_numbers": []},
        )

    def inquireHoliday(self, token: str, *, date_yyyymmdd: str) -> Dict[str, Any]:
        del token, date_yyyymmdd
        return unsupportedPaperMockStep("holiday_inquire")

    def subscribeRealtime(
        self,
        approval_key: str,
        *,
        tr_id: str,
        tr_key: str,
        step: str,
        tr_type: str = "1",
        timeout: int = 10,
    ) -> Dict[str, Any]:
        if not str(approval_key or "").strip():
            return {
                "step": step,
                "status": "blocked_websocket_approval_key_missing",
                "subscription_frame_ready": False,
                "ack_received": False,
                "raw_response_stored": False,
            }
        frame = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": tr_type,
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": tr_key,
                }
            },
        }
        transport = self.websocket_transport
        if not transport or not hasattr(transport, "subscribeOnce"):
            return {
                "step": step,
                "status": "blocked_websocket_transport_missing",
                "subscription_frame_ready": True,
                "tr_id": tr_id,
                "tr_key": tr_key,
                "ack_received": False,
                "raw_response_stored": False,
                "credential_values_printed": False,
            }
        response = transport.subscribeOnce(
            str(self.envValue("KIS_WEBSOCKET_URL") or DEFAULT_KIS_WEBSOCKET_URL),
            frame,
            timeout=timeout,
        )
        payload = response.get("payload") if isinstance(response, Mapping) else {}
        return {
            "step": step,
            "status": response.get("status", "warn") if isinstance(response, Mapping) else "warn",
            "tr_id": tr_id,
            "tr_key": tr_key,
            "subscription_frame_ready": True,
            "ack_received": bool(response.get("ack_received")) if isinstance(response, Mapping) else False,
            "rt_cd": payload.get("rt_cd") if isinstance(payload, Mapping) else None,
            "msg_cd": payload.get("msg_cd") if isinstance(payload, Mapping) else None,
            "raw_response_stored": False,
            "credential_values_printed": False,
        }

    def subscribeFillNotice(self, approval_key: str) -> Dict[str, Any]:
        hts_id = self.envValue("KIS_PAPER_HTS_ID")
        if not hts_id:
            return {
                "step": "ws_fill_notice",
                "status": "blocked_hts_id_missing",
                "tr_id": "H0STCNI9",
                "ack_received": False,
                "raw_response_stored": False,
                "credential_values_printed": False,
            }
        return self.subscribeRealtime(
            approval_key,
            tr_id="H0STCNI9",
            tr_key=hts_id,
            step="ws_fill_notice",
        )

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
            "CANO": self.envValue("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self.envValue("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "PDNO": str(intent.get("symbol") or "").strip(),
            "ORD_DVSN": str(intent.get("order_division") or "01"),
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(intent.get("order_price") or intent.get("price") or "0"),
        }
        tr_id = "VTTC0802U" if side == "buy" else "VTTC0801U"
        response = self.requestBrokerJson(
            "POST",
            "/uapi/domestic-stock/v1/trading/order-cash",
            headers=self.authHeaders(token, tr_id),
            body=body,
        )
        result = sanitizeKisResponse(response, step="cash_order")
        order_ids = extractKisOrderIdentifiers(response)
        result["broker_order_no"] = order_ids["broker_order_no"]
        result["broker_order_no_present"] = bool(order_ids["broker_order_no"])
        result["krx_forwarding_order_orgno"] = order_ids["krx_forwarding_order_orgno"]
        result["broker_endpoint_called"] = True
        result["route"] = "KRX"
        result["side"] = side
        return result

    def inquireAccountSummaryForDashboard(self, token: str, symbol: str) -> Dict[str, Any]:
        blocked = self.blockedIfMissingEnv("dashboard_account_summary")
        if blocked:
            return {
                **blocked,
                "account_no": "",
                "account_product_code": "",
                "account_label": "",
                "credential_values_printed": False,
                "raw_response_stored": False,
            }

        balance_response = self.requestBrokerJson(
            "GET",
            f"/uapi/domestic-stock/v1/trading/inquire-balance?{urllib.parse.urlencode(self.accountQuery())}",
            headers=self.authHeaders(token, "VTTC8434R"),
        )
        buyable_params = {
            "CANO": self.envValue("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self.envValue("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "PDNO": symbol,
            "ORD_UNPR": "",
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "Y",
        }
        buyable_response = self.requestBrokerJson(
            "GET",
            f"/uapi/domestic-stock/v1/trading/inquire-psbl-order?{urllib.parse.urlencode(buyable_params)}",
            headers=self.authHeaders(token, "VTTC8908R"),
        )
        balance = sanitizeKisResponse(balance_response, step="dashboard_balance_inquire", row_count_key="output1")
        buyable = sanitizeKisResponse(buyable_response, step="dashboard_buyable_inquire")
        balance_summary = summarizeKisBalancePayload(balance_response)
        buyable_summary = summarizeKisBuyablePayload(buyable_response)
        realized = {
            "status": "skipped",
            "reason": "dashboard_account_summary_uses_runner_realized_pnl_when_available",
        }
        realized_summary: Dict[str, Any] = {}
        cash_balance = buyable_summary.get("buyable_cash_krw")
        if cash_balance is None:
            cash_balance = balance_summary.get("cash_balance_krw")
        return {
            "step": "dashboard_account_summary",
            "status": "pass" if balance.get("status") == "pass" and buyable.get("status") == "pass" else "warn",
            "account_no": self.envValue("KIS_PAPER_ACCOUNT_NO"),
            "account_product_code": self.envValue("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "account_label": f"{self.envValue('KIS_PAPER_ACCOUNT_NO')}-{self.envValue('KIS_PAPER_ACCOUNT_PRODUCT_CODE')}",
            "cash_balance_krw": cash_balance,
            "total_eval_krw": balance_summary.get("total_eval_krw"),
            "stock_eval_krw": balance_summary.get("stock_eval_krw"),
            "today_pnl_krw": balance_summary.get("today_pnl_krw"),
            "realized_pnl_krw": realized_summary.get("realized_pnl_krw"),
            "positions_count": balance_summary.get("positions_count", 0),
            "balance_status": balance.get("status"),
            "buyable_status": buyable.get("status"),
            "realized_pnl_status": realized.get("status"),
            "credential_values_printed": False,
            "raw_response_stored": False,
        }

    def cancelOrder(
        self,
        token: str,
        *,
        original_order_no: str,
        quantity: int = 0,
        original_order_orgno: str = "",
    ) -> Dict[str, Any]:
        body = {
            "CANO": self.envValue("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self.envValue("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
            "KRX_FWDG_ORD_ORGNO": original_order_orgno,
            "ORGN_ODNO": original_order_no,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": "02",
            "ORD_QTY": str(int(quantity or 0)),
            "ORD_UNPR": "0",
            "QTY_ALL_ORD_YN": "Y" if int(quantity or 0) <= 0 else "N",
        }
        response = self.requestBrokerJson(
            "POST",
            "/uapi/domestic-stock/v1/trading/order-rvsecncl",
            headers=self.authHeaders(token, "VTTC0803U"),
            body=body,
        )
        result = sanitizeKisResponse(response, step="cancel_order")
        result.update(
            {
                "broker_endpoint_called": True,
                "order_cancel_modify_called": True,
                "original_order_no": original_order_no,
                "original_order_orgno": original_order_orgno,
                "cancel_quantity": int(quantity or 0),
                "cancel_all_quantity": int(quantity or 0) <= 0,
            }
        )
        return result

    def blockedIfMissingEnv(self, step: str) -> Optional[Dict[str, Any]]:
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

    def requestBrokerJson(
        self,
        method: str,
        path_or_url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        body: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self.buildUrl(path_or_url)
        validatePaperBaseUrl(url.rsplit("/", 1)[0] if path_or_url.startswith("http") else self.base_url)
        parsed = urllib.parse.urlparse(url)
        if parsed.hostname != PAPER_HOST:
            raise KisPaperAdapterError("kis_paper_request_not_paper_domain")
        return self.transport.requestJson(method, url, headers=headers, body=body)

    def buildUrl(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            parsed = urllib.parse.urlparse(path_or_url)
            if parsed.hostname != PAPER_HOST:
                raise KisPaperAdapterError("kis_paper_request_not_paper_domain")
            return path_or_url
        path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
        return f"{self.base_url}{path}"

    def envValue(self, key: str) -> str:
        return str(self._env.get(key, "")).strip()

    def authHeaders(self, token: str, tr_id: str) -> Dict[str, str]:
        return {
            "authorization": f"Bearer {token}",
            "appkey": self.envValue("KIS_PAPER_APP_KEY"),
            "appsecret": self.envValue("KIS_PAPER_APP_SECRET"),
            "tr_id": tr_id,
            "custtype": "P",
        }

    def accountQuery(self) -> Dict[str, str]:
        return {
            "CANO": self.envValue("KIS_PAPER_ACCOUNT_NO"),
            "ACNT_PRDT_CD": self.envValue("KIS_PAPER_ACCOUNT_PRODUCT_CODE"),
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
