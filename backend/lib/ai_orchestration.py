"""
HWISTOCK-UNIT-005 foundation: deterministic local AI orchestration helpers.

Stdlib-only; no network, broker, KIS, or AI provider calls. AI outputs are
recommendation-only and must pass schema validation and deterministic policy gates
before any no-order dry-run record is produced.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

try:
    from lib import runtime_policy as rp
    from lib import strategy_risk as sr
except ImportError:  # pragma: no cover - package-style imports
    from backend.lib import runtime_policy as rp
    from backend.lib import strategy_risk as sr

KST = timezone(timedelta(hours=9))

AI_RECOMMENDATION_SCHEMA = "ai_recommendation/v0"
PRO_HOURLY_SCHEMA = "pro_hourly_market_analysis/v1"
FLASH_TRADE_DOCUMENT_SCHEMA = "flash_trade_document/v1"
MORNING_WATCHLIST_SCHEMA = "morning_watchlist/v1"
COMPILED_WATCH_SCHEMA = "compiled_watch/v0"
NO_ORDER_DRY_RUN = "no_order_dry_run"
DEEPSEEK_PRO_MODEL = "deepseek-v4-pro"
DEEPSEEK_FLASH_MODEL = "deepseek-v4-flash"

FLASH_BUY_ACTIONS = frozenset({"WAIT_BUY", "BUY_NOW"})
FLASH_SELL_ACTIONS = frozenset({"SELL", "SELL_NOW", "WAIT_SELL"})
FLASH_MANAGEMENT_ACTIONS = frozenset(
    {"HOLD", "NO_TRADE", "NO_NEW_ENTRY", "HOLD_EXISTING_POSITION", "WAIT_ORDER_RECONCILIATION", "EXIT_REVIEW"}
)
FLASH_ACTION_TYPES = FLASH_BUY_ACTIONS | FLASH_SELL_ACTIONS | FLASH_MANAGEMENT_ACTIONS

ALLOWED_ACTIONS = frozenset(
    {"watch", "reject", "consider_entry", "hold_review", "exit_review"}
)
ALLOWED_CONFIDENCE = frozenset({"low", "medium", "high"})
ALLOWED_SOURCE_PATHS = frozenset({"event_first", "chart_first", "combined"})
ALLOWED_CHART_INTERVALS = frozenset({"1m", "3m", "5m"})
ALLOWED_ORDER_SIDES = frozenset({"buy", "sell"})
ALLOWED_PRICE_TYPES = frozenset({"limit", "market"})

JOB_REGISTRY: Dict[str, Dict[str, Any]] = {
    "deepseek_pro_hourly": {
        "schedule": "top-of-hour, 24h",
        "model_role": "deepseek_pro",
        "model_name": DEEPSEEK_PRO_MODEL,
        "input_schema": "pro_hourly_input_bundle/v0",
        "output_schema": PRO_HOURLY_SCHEMA,
        "market_analysis_feed_mode": rp.MARKET_ANALYSIS_FEED_INTEGRATED,
        "includes_market_regime": True,
        "soft_latency_seconds": 600,
        "hard_latency_seconds": 1200,
        "tool_use_enabled": False,
    },
    "deepseek_flash_trade_document_10m": {
        "schedule": "every 10 minutes during active investment-mode decision window",
        "model_role": "deepseek_flash",
        "model_name": DEEPSEEK_FLASH_MODEL,
        "input_schema": "flash_10m_input_bundle/v0",
        "output_schema": FLASH_TRADE_DOCUMENT_SCHEMA,
        "market_analysis_feed_mode": rp.MARKET_ANALYSIS_FEED_INTEGRATED,
        "execution_venue_mode": rp.EXECUTION_VENUE_KRX_ONLY,
        "max_action_symbols": 5,
        "requires_compiled_watch": True,
        "requires_morning_watchlist_before_first_bucket": True,
        "requires_portfolio_or_order_state": True,
        "soft_latency_seconds": 120,
        "hard_latency_seconds": 600,
        "tool_use_enabled": False,
    },
    "gpt_morning_watchlist_0715": {
        "schedule": "07:15 KST",
        "model_role": "local_codex_cli_browser_use_chatgpt_pro",
        "input_schema": "morning_watchlist_input_bundle/v0",
        "output_schema": MORNING_WATCHLIST_SCHEMA,
        "approved_route": "codex_cli_local_browser_use",
        "ssh_browser_use_allowed": False,
        "artifact_or_safe_block_required_before_first_flash": True,
        "tool_use_enabled": False,
    },
    "daily_close_mode_aware": {
        "schedule": "paper after 15:30 KST; live at 20:00 KST",
        "model_role": "deepseek_pro",
        "input_schema": "daily_close_bundle/v0",
        "output_schema": "daily_close_report/v0",
        "soft_latency_seconds": 1200,
        "hard_latency_seconds": 3600,
        "tool_use_enabled": False,
    },
}

TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+09:00$"
)

FORBIDDEN_BROKER_TOKENS = (
    "broker",
    "kis",
    "live",
    "paper",
    "mock",
    "demo",
    "testbed",
    "sandbox",
    "orderno",
    "order_no",
    "submit_order",
    "place_order",
    "fake_broker",
    "mock_broker",
)
FORBIDDEN_POLICY_TOKENS = (
    "all_in",
    "all-in",
    "credit",
    "margin",
    "미수",
    "leverage",
    "overnight",
    "ignore_stop",
    "bypass_risk",
    "bypass_stop",
)
FORBIDDEN_TOOL_REQUEST_TOKENS = (
    "browse",
    "web_search",
    "call_tool",
    "invoke_tool",
    "use_tool",
    "retrieval_tool",
    "function_call",
)
SENSITIVE_PAYLOAD_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "password",
        "token",
        "credential",
        "credentials",
        "account_id",
        "account_no",
        "account_number",
        "balance_krw",
        "private_account",
        "broker_credential",
        "kis_app_key",
        "kis_app_secret",
    }
)
SENSITIVE_PAYLOAD_FRAGMENTS = (
    "api_key",
    "api_secret",
    "password",
    "credential",
    "account_id",
    "account_no",
    "full_article_body",
    "unapproved_full_article",
)


def loadAiOrchestrationConfig() -> Dict[str, Any]:
    return {
        "module_id": "HWISTOCK-MOD-004",
        "version": "2026-06-04-rebaseline",
        "AI_NETWORK_ENABLED": False,
        "AI_DAILY_COST_CAP_KRW": 0,
        "DEEPSEEK_PRO_ENABLED": False,
        "DEEPSEEK_FLASH_ENABLED": False,
        "CHATGPT_PRO_BROWSER_REVIEW_ENABLED": False,
        "GPT_PRO_MORNING_REVIEW_START_KST": "07:15",
        "GPT_PRO_APPROVED_ROUTE": "codex_cli_local_browser_use",
        "MORNING_WATCHLIST_REQUIRED_BEFORE_FIRST_FLASH": True,
        "DEEPSEEK_PRO_MODEL": DEEPSEEK_PRO_MODEL,
        "DEEPSEEK_FLASH_MODEL": DEEPSEEK_FLASH_MODEL,
        "AI_TOOL_USE_ENABLED": False,
        "execution_mode": NO_ORDER_DRY_RUN,
        "broker_adapter": NO_ORDER_DRY_RUN,
        "kis_paper_approved": False,
        "job_registry": deepcopy(JOB_REGISTRY),
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "boundaries": {
            "broker_calls_allowed": False,
            "order_placement_allowed": False,
            "ai_direct_order_allowed": False,
            "provider_network_allowed": False,
            "tool_use_allowed": False,
            "fill_simulation_allowed": False,
            "balance_simulation_allowed": False,
        },
    }


def validateAiOrchestrationConfig(
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    payload = deepcopy(dict(config or loadAiOrchestrationConfig()))
    errors: List[str] = []

    if payload.get("AI_NETWORK_ENABLED") is not False:
        errors.append("ai_network_must_be_disabled_by_default")
    if payload.get("AI_DAILY_COST_CAP_KRW") != 0:
        errors.append("ai_daily_cost_cap_must_be_zero_by_default")
    if payload.get("DEEPSEEK_PRO_ENABLED") is not False:
        errors.append("deepseek_pro_must_be_disabled_by_default")
    if payload.get("DEEPSEEK_FLASH_ENABLED") is not False:
        errors.append("deepseek_flash_must_be_disabled_by_default")
    if payload.get("CHATGPT_PRO_BROWSER_REVIEW_ENABLED") is not False:
        errors.append("chatgpt_pro_browser_review_must_be_disabled_by_default")
    if payload.get("GPT_PRO_MORNING_REVIEW_START_KST") != "07:15":
        errors.append("gpt_pro_morning_review_start_must_be_0715")
    if payload.get("GPT_PRO_APPROVED_ROUTE") != "codex_cli_local_browser_use":
        errors.append("gpt_pro_route_must_be_codex_cli_local_browser_use")
    if payload.get("MORNING_WATCHLIST_REQUIRED_BEFORE_FIRST_FLASH") is not True:
        errors.append("morning_watchlist_or_safe_block_required_before_first_flash")
    if payload.get("DEEPSEEK_PRO_MODEL") != DEEPSEEK_PRO_MODEL:
        errors.append("deepseek_pro_model_must_be_deepseek_v4_pro")
    if payload.get("DEEPSEEK_FLASH_MODEL") != DEEPSEEK_FLASH_MODEL:
        errors.append("deepseek_flash_model_must_be_deepseek_v4_flash")
    serialized_models = _serialize_for_policy_scan(
        {
            "DEEPSEEK_PRO_MODEL": payload.get("DEEPSEEK_PRO_MODEL"),
            "DEEPSEEK_FLASH_MODEL": payload.get("DEEPSEEK_FLASH_MODEL"),
        }
    )
    if "moonbridge" in serialized_models or "deepseek-chat" in serialized_models:
        errors.append("deprecated_or_router_model_alias_forbidden")
    if payload.get("AI_TOOL_USE_ENABLED") is not False:
        errors.append("ai_tool_use_must_be_disabled_by_default")
    if payload.get("execution_mode") != NO_ORDER_DRY_RUN:
        errors.append("execution_mode_must_be_no_order_dry_run")
    if payload.get("broker_adapter") != NO_ORDER_DRY_RUN:
        errors.append("broker_adapter_must_be_no_order_dry_run")

    registry = payload.get("job_registry")
    if not isinstance(registry, Mapping) or set(registry.keys()) != set(JOB_REGISTRY.keys()):
        errors.append("job_registry_must_match_unit_contract")

    boundaries = payload.get("boundaries") or {}
    if boundaries.get("broker_calls_allowed") is not False:
        errors.append("broker_calls_must_be_disabled")
    if boundaries.get("order_placement_allowed") is not False:
        errors.append("order_placement_must_be_disabled")
    if boundaries.get("ai_direct_order_allowed") is not False:
        errors.append("ai_direct_order_must_be_disabled")
    if boundaries.get("provider_network_allowed") is not False:
        errors.append("provider_network_must_be_disabled")
    if boundaries.get("tool_use_allowed") is not False:
        errors.append("tool_use_must_be_disabled")

    return {"ok": not errors, "errors": errors, "config": payload}


def getAiJobRegistry() -> Dict[str, Dict[str, Any]]:
    return deepcopy(JOB_REGISTRY)


def getOfficialDeepSeekModels() -> Dict[str, str]:
    return {
        "deepseek_pro": DEEPSEEK_PRO_MODEL,
        "deepseek_flash": DEEPSEEK_FLASH_MODEL,
    }


def _dedupe_strings(values: Sequence[Any]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _window_seconds(window: Optional[Mapping[str, Any]]) -> Optional[int]:
    if not isinstance(window, Mapping):
        return None
    start = _parse_kst_timestamp(window.get("start_kst"), "start_kst", [])
    end = _parse_kst_timestamp(window.get("end_kst"), "end_kst", [])
    if not start or not end:
        return None
    return max(0, int((end - start).total_seconds()))


LOW_UTILITY_PRO_STATUSES = {"news_only_low_utility", "truncated_low_utility"}

GENERIC_PRO_SUMMARY_FRAGMENTS = (
    "근거 입력을 바탕으로",
    "시간별 시장 분석입니다",
    "생성한 deepseek pro",
)

GENERIC_PRO_THEME_FRAGMENTS = (
    "최근 1시간 입력 기반 감시",
    "입력 기반 감시",
    "시장 반응 확인 필요",
)

GENERIC_PRO_CLAIM_FRAGMENTS = (
    "최근 1시간 입력 묶음",
    "입력 묶음",
)

GENERIC_NEXT_FLASH_QUESTIONS = (
    "실제 거래대금과 체결강도가 붙는가",
    "보유/대기주문과 신규 진입 후보가 충돌하지 않는가",
)

PRO_OUTPUT_LIMITS = {
    "theme_map": 5,
    "source_ref_map": 5,
    "no_trade_conditions": 5,
    "questions_for_next_flash": 5,
    "refs_per_item": 3,
    "why_claims": 2,
}


def _contains_any_fragment(value: Any, fragments: Sequence[str]) -> bool:
    text = str(value or "").strip().lower()
    return bool(text) and any(fragment.lower() in text for fragment in fragments)


def _is_off_session_pro_context(payload: Mapping[str, Any]) -> bool:
    calendar = payload.get("calendar_context") if isinstance(payload.get("calendar_context"), Mapping) else {}
    market_context = payload.get("market_context") if isinstance(payload.get("market_context"), Mapping) else {}
    return (
        calendar.get("kis_realtime_expected") is False
        or calendar.get("market_context_open") is False
        or market_context.get("market_context_open") is False
        or market_context.get("kis_realtime_expected") is False
    )


def _append_default_off_session_no_trade_condition(payload: Dict[str, Any]) -> None:
    conditions = payload.setdefault("no_trade_conditions", [])
    if not isinstance(conditions, list):
        payload["no_trade_conditions"] = conditions = []
    if conditions:
        return
    conditions.append(
        {
            "condition": "개장 후 KRX 거래대금/체결강도 확인 전 BUY_NOW 금지",
            "reason": "오프세션/휴장일 carryover 분석만으로는 장중 수급 확인이 불가능합니다",
            "source_refs": [],
            "market_data_refs": [],
        }
    )


def _limited_list(value: Any, limit: int) -> List[Any]:
    return list(value[:limit]) if isinstance(value, list) else []


def _limited_deduped_strings(value: Any, limit: int) -> List[str]:
    return _dedupe_strings(value if isinstance(value, list) else [])[:limit]


def _limit_ref_fields(row: Dict[str, Any], *, limit: int) -> None:
    for key in ("source_refs", "market_data_refs"):
        if key in row:
            row[key] = _limited_deduped_strings(row.get(key), limit)


def normalizeProHourlyOutputCaps(document: Mapping[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(dict(document or {}))
    refs_limit = int(PRO_OUTPUT_LIMITS["refs_per_item"])
    theme_map = _limited_list(payload.get("theme_map"), int(PRO_OUTPUT_LIMITS["theme_map"]))
    normalized_themes: List[Any] = []
    for theme in theme_map:
        if isinstance(theme, Mapping):
            row = dict(theme)
            _limit_ref_fields(row, limit=refs_limit)
            normalized_themes.append(row)
        else:
            normalized_themes.append(theme)
    if isinstance(payload.get("theme_map"), list):
        payload["theme_map"] = normalized_themes

    source_ref_map = _limited_list(payload.get("source_ref_map"), int(PRO_OUTPUT_LIMITS["source_ref_map"]))
    normalized_source_refs: List[Any] = []
    for item in source_ref_map:
        if isinstance(item, Mapping):
            row = dict(item)
            _limit_ref_fields(row, limit=refs_limit)
            normalized_source_refs.append(row)
        else:
            normalized_source_refs.append(item)
    if isinstance(payload.get("source_ref_map"), list):
        payload["source_ref_map"] = normalized_source_refs

    no_trade_conditions = _limited_list(
        payload.get("no_trade_conditions"),
        int(PRO_OUTPUT_LIMITS["no_trade_conditions"]),
    )
    normalized_no_trade: List[Any] = []
    for item in no_trade_conditions:
        if isinstance(item, Mapping):
            row = dict(item)
            _limit_ref_fields(row, limit=refs_limit)
            normalized_no_trade.append(row)
        else:
            normalized_no_trade.append(item)
    if isinstance(payload.get("no_trade_conditions"), list):
        payload["no_trade_conditions"] = normalized_no_trade

    if isinstance(payload.get("questions_for_next_flash"), list):
        payload["questions_for_next_flash"] = _limited_deduped_strings(
            payload.get("questions_for_next_flash"),
            int(PRO_OUTPUT_LIMITS["questions_for_next_flash"]),
        )

    regime = payload.get("market_regime")
    if isinstance(regime, Mapping):
        regime_row = dict(regime)
        why = _limited_list(regime_row.get("why"), int(PRO_OUTPUT_LIMITS["why_claims"]))
        normalized_why: List[Any] = []
        for item in why:
            if isinstance(item, Mapping):
                row = dict(item)
                _limit_ref_fields(row, limit=refs_limit)
                normalized_why.append(row)
            else:
                normalized_why.append(item)
        if isinstance(regime_row.get("why"), list):
            regime_row["why"] = normalized_why
        payload["market_regime"] = regime_row

    guidance = payload.get("flash_guidance")
    if isinstance(guidance, Mapping):
        guidance_row = dict(guidance)
        for key in ("candidate_focus", "avoid_focus", "must_check_before_buy", "position_management_notes"):
            if isinstance(guidance_row.get(key), list):
                guidance_row[key] = _limited_deduped_strings(guidance_row.get(key), 8)
        payload["flash_guidance"] = guidance_row
    return payload


def _normalize_off_session_data_quality(payload: Dict[str, Any]) -> None:
    if not _is_off_session_pro_context(payload):
        return
    data_quality = payload.get("data_quality")
    if not isinstance(data_quality, dict):
        data_quality = {}
        payload["data_quality"] = data_quality
    if data_quality.get("kis_data_status") == "ok" or data_quality.get("kis_data_status") in {
        None,
        "",
        "partial",
        "missing",
        "degraded",
        "expected_off_session",
    }:
        data_quality["kis_data_status"] = "expected_off_session_no_realtime"
    data_quality.setdefault("kis_artifact_count", int(data_quality.get("kis_market_snapshot_count") or 0))
    data_quality.setdefault("kis_realtime_snapshot_count", 0)
    data_quality.setdefault("kis_safe_skip_count", 0)
    data_quality.setdefault("valid_market_confirmation_count", 0)
    if data_quality.get("market_confirmation_status") == "confirmed" or not data_quality.get("market_confirmation_status"):
        data_quality["market_confirmation_status"] = "not_confirmed"
    dq_warnings = data_quality.setdefault("warnings", [])
    if isinstance(dq_warnings, list) and "off_session_no_realtime_expected" not in dq_warnings:
        dq_warnings.append("off_session_no_realtime_expected")


def _apply_low_utility_pro_status(
    payload: Dict[str, Any],
    warnings: List[str],
    *,
    status: str,
    warning: str,
    aggression_cap: str = "no_buy_now",
) -> None:
    if status == "truncated_low_utility" or payload.get("investment_utility_status") not in {"safe_block"}:
        payload["investment_utility_status"] = status
    payload["flash_usable"] = False
    payload["flash_aggression_cap"] = aggression_cap
    warnings.append(warning)


def _semantic_pro_quality_warnings(payload: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    summary = str(payload.get("summary") or "")
    if _contains_any_fragment(summary, GENERIC_PRO_SUMMARY_FRAGMENTS):
        warnings.append("generic_pro_summary")

    theme_map = payload.get("theme_map") if isinstance(payload.get("theme_map"), list) else []
    if theme_map:
        generic_theme_only = True
        all_groups_empty = True
        off_session_confirmed = False
        for theme in theme_map:
            if not isinstance(theme, Mapping):
                continue
            if not (
                _contains_any_fragment(theme.get("theme"), GENERIC_PRO_THEME_FRAGMENTS)
                or _contains_any_fragment(theme.get("why_it_matters"), GENERIC_PRO_THEME_FRAGMENTS)
            ):
                generic_theme_only = False
            if theme.get("affected_groups") or theme.get("avoid_groups"):
                all_groups_empty = False
            if str(theme.get("market_confirmation_status") or "").strip() == "confirmed":
                off_session_confirmed = True
        if generic_theme_only:
            warnings.append("generic_theme_map")
        if all_groups_empty:
            warnings.append("theme_map_empty_groups")
        if off_session_confirmed and _is_off_session_pro_context(payload):
            warnings.append("off_session_market_confirmation_confirmed")
            for theme in theme_map:
                if isinstance(theme, dict) and str(theme.get("market_confirmation_status") or "").strip() == "confirmed":
                    theme["market_confirmation_status"] = "awaiting_next_open"

    source_ref_map = payload.get("source_ref_map") if isinstance(payload.get("source_ref_map"), list) else []
    if source_ref_map:
        generic_claims = 0
        weak_confidence = 0
        for item in source_ref_map:
            if not isinstance(item, Mapping):
                continue
            if _contains_any_fragment(item.get("claim"), GENERIC_PRO_CLAIM_FRAGMENTS):
                generic_claims += 1
            try:
                confidence = float(item.get("confidence"))
            except (TypeError, ValueError):
                confidence = 0.0
            if confidence <= 0.3:
                weak_confidence += 1
        if generic_claims == len(source_ref_map):
            warnings.append("generic_source_ref_claim")
        if weak_confidence == len(source_ref_map):
            warnings.append("weak_source_ref_confidence")

    questions = [str(item or "") for item in payload.get("questions_for_next_flash") or []]
    if questions and all(any(fragment in question for fragment in GENERIC_NEXT_FLASH_QUESTIONS) for question in questions):
        warnings.append("generic_questions_for_next_flash")

    if _is_off_session_pro_context(payload):
        guidance = payload.get("flash_guidance") if isinstance(payload.get("flash_guidance"), dict) else {}
        if guidance:
            if guidance.get("preferred_bias") not in {"defensive", "selective_watch", "no_trade_bias"}:
                warnings.append("off_session_flash_bias_too_aggressive")
                guidance["preferred_bias"] = "selective_watch"
            if guidance.get("max_aggression") not in {None, "none", "low"}:
                warnings.append("off_session_flash_aggression_too_high")
                guidance["max_aggression"] = "low"
            must_check = guidance.setdefault("must_check_before_buy", [])
            if isinstance(must_check, list):
                must_check.extend(
                    item
                    for item in (
                        "KRX execution quote",
                        "거래대금/체결강도 확인",
                        "morning watchlist consistency",
                        "75% exposure cap",
                        "보유/대기주문 충돌 확인",
                    )
                    if item not in must_check
                )
        if not payload.get("no_trade_conditions"):
            warnings.append("off_session_no_trade_conditions_required")
            _append_default_off_session_no_trade_condition(payload)
        _normalize_off_session_data_quality(payload)

    return _dedupe_strings(warnings)


def _kis_snapshot_counts(kis_rows: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    safe_skip_count = 0
    realtime_snapshot_count = 0
    valid_market_confirmation_count = 0
    success_statuses = {"ok", "accepted", "success", "completed"}
    for snapshot in kis_rows:
        snapshot_status = str(snapshot.get("status") or "")
        input_results = snapshot.get("input_results") if isinstance(snapshot.get("input_results"), list) else []
        if not input_results and snapshot_status.startswith("safe_skip"):
            safe_skip_count += 1
        for item in input_results:
            if not isinstance(item, Mapping):
                continue
            status = str(item.get("status") or "")
            input_id = str(item.get("input_id") or item.get("step") or "")
            try:
                row_count = int(item.get("row_count") or 0)
            except (TypeError, ValueError):
                row_count = 0
            if status.startswith("safe_skip") or status.startswith("skipped"):
                safe_skip_count += 1
            valid = bool(item.get("endpoint_called") is True and row_count > 0 and status in success_statuses)
            if valid:
                valid_market_confirmation_count += 1
                if "realtime" in input_id or "_ws" in input_id or "market_operation" in input_id:
                    realtime_snapshot_count += 1
    return {
        "kis_artifact_count": len(kis_rows),
        "kis_realtime_snapshot_count": realtime_snapshot_count,
        "kis_safe_skip_count": safe_skip_count,
        "valid_market_confirmation_count": valid_market_confirmation_count,
    }


def buildProHourlyMarketAnalysis(
    *,
    events: Optional[Sequence[Mapping[str, Any]]] = None,
    kis_market_snapshots: Optional[Sequence[Mapping[str, Any]]] = None,
    produced_at_kst: Optional[str] = None,
    provider_status: str = "safe_block_no_provider_network",
    input_window_kst: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    produced_at = produced_at_kst or _default_now_kst()
    event_rows = [deepcopy(dict(event)) for event in (events or [])]
    kis_rows = [deepcopy(dict(row)) for row in (kis_market_snapshots or [])]
    source_refs = _dedupe_strings([
        str(event.get("source_event_id") or event.get("event_id") or event.get("source_id") or "").strip()
        for event in event_rows
        if str(event.get("source_event_id") or event.get("event_id") or event.get("source_id") or "").strip()
    ])
    market_refs = _dedupe_strings([
        str(row.get("artifact_id") or row.get("snapshot_id") or row.get("source_id") or "").strip()
        for row in kis_rows
        if str(row.get("artifact_id") or row.get("snapshot_id") or row.get("source_id") or "").strip()
    ])
    safe_block = not event_rows and not kis_rows
    window = dict(input_window_kst or {})
    if "window_seconds" not in window:
        seconds = _window_seconds(window)
        if seconds is not None:
            window["window_seconds"] = seconds
    kis_data_status = "ok" if kis_rows else ("missing" if event_rows else "missing")
    kis_counts = _kis_snapshot_counts(kis_rows)
    regime_mode = "NO_TRADE" if safe_block else "NEUTRAL"
    return {
        "schema_version": PRO_HOURLY_SCHEMA,
        "artifact_id": f"art_pro_hourly_{_compact_timestamp(produced_at)}",
        "artifact_type": "pro_hourly_market_analysis",
        "job_id": "deepseek_pro_hourly",
        "model_role": "deepseek_pro",
        "model_name": DEEPSEEK_PRO_MODEL,
        "prompt_schema_version": "pro_hourly_prompt/v1",
        "produced_at_kst": produced_at,
        "input_window_kst": window,
        "market_analysis_feed_mode": rp.MARKET_ANALYSIS_FEED_INTEGRATED,
        "provider_status": provider_status,
        "validation_status": "safe_block" if safe_block else "accepted",
        "document_kind": "NO_TRADE" if safe_block else "MARKET_STRATEGY_CONTEXT",
        "source_refs": source_refs,
        "market_data_refs": market_refs,
        "source_event_count": len(event_rows),
        "kis_market_snapshot_count": len(kis_rows),
        "source_counts": {
            "news_disclosure_events": len(event_rows),
            "kis_market_snapshots": len(kis_rows),
        },
        "data_quality": {
            "news_event_count": len(event_rows),
            "kis_market_snapshot_count": len(kis_rows),
            **kis_counts,
            "kis_data_status": "safe_block" if safe_block else kis_data_status,
            "market_confirmation_status": "confirmed" if kis_counts["valid_market_confirmation_count"] else "not_confirmed",
            "runtime_kis_failure_evidence_present": False,
            "missing_inputs": []
            if event_rows and kis_rows
            else [
                label
                for label, missing in (
                    ("news_disclosure_events", not event_rows),
                    ("kis_market_snapshots", not kis_rows),
                )
                if missing
            ],
            "warnings": [],
        },
        "missing_source_warnings": []
        if event_rows or kis_rows
        else ["no_news_disclosure_or_market_events_in_hour_window"],
        "market_regime": {
            "included_in_pro_artifact": True,
            "session_analysis": "insufficient_inputs" if safe_block else "source_and_kis_context_available",
            "mode": regime_mode,
            "market_mode": regime_mode,
            "confidence": 0.0 if safe_block else 0.35,
            "why": [
                {
                    "claim": "입력 부족으로 거래 판단을 보류합니다" if safe_block else "최근 뉴스/공시와 KIS 시장 스냅샷을 함께 확인해야 합니다",
                    "source_refs": source_refs[:5],
                    "market_data_refs": market_refs[:5],
                }
            ],
        },
        "theme_map": []
        if safe_block
        else [
            {
                "theme": "최근 1시간 입력 기반 감시",
                "direction": "neutral",
                "strength": 0.3,
                "freshness": "last_1h",
                "affected_groups": [],
                "avoid_groups": [],
                "why_it_matters": "Flash가 개별 후보를 보기 전에 시장 반응과 거래대금 확인이 필요합니다",
                "source_refs": source_refs[:5],
                "market_data_refs": market_refs[:5],
                "market_confirmation_status": "not_confirmed" if not market_refs else "confirmed",
                "confirmation_signals_for_flash": [
                    "개장 후 거래대금 상위 진입",
                    "체결강도 개선",
                    "KRX 호가 스프레드 과도하지 않음",
                ],
            }
        ],
        "flash_guidance": {
            "preferred_bias": "no_trade_bias" if safe_block else "selective_watch",
            "max_aggression": "none" if safe_block else "low",
            "candidate_focus": [],
            "avoid_focus": [],
            "must_check_before_buy": [
                "KRX execution quote",
                "거래대금/체결강도 확인",
                "보유/대기주문 충돌 확인",
                "75% exposure cap 확인",
            ],
            "position_management_notes": [],
        },
        "no_trade_conditions": [
            {
                "condition": "근거 입력 부족",
                "reason": "뉴스/공시와 시장 데이터가 부족하면 신규 진입을 보류합니다",
                "source_refs": source_refs[:5],
                "market_data_refs": market_refs[:5],
            }
        ]
        if safe_block
        else [],
        "contradiction_notes": [],
        "source_ref_map": [
            {
                "claim": "최근 1시간 입력 묶음",
                "source_refs": source_refs[:5],
                "market_data_refs": market_refs[:5],
                "confidence": 0.3 if source_refs or market_refs else 0.0,
            }
        ],
        "questions_for_next_flash": [
            "다음 10분에 실제 거래대금과 체결강도가 붙는가?",
            "보유/대기주문과 신규 진입 후보가 충돌하지 않는가?",
        ],
        "investment_utility_status": "safe_block" if safe_block else "limited_context",
        "analysis_language": "ko-KR",
        "summary": "NO_TRADE: 뉴스/공시와 KIS 시장 데이터 입력이 없어 분석을 보류합니다" if safe_block else "근거 입력을 바탕으로 생성한 DeepSeek Pro 시간별 시장 분석입니다",
        "order_safety": "no_order",
        "no_broker_call": True,
        "no_order_submission": True,
        "ai_direct_order_allowed": False,
        "redaction_status": "sanitized",
    }


def buildNoTradeSentinel(
    *,
    job_id: str,
    reason: str,
    schema_version: str = FLASH_TRADE_DOCUMENT_SCHEMA,
    produced_at_kst: Optional[str] = None,
    bucket_id: Optional[str] = None,
) -> Dict[str, Any]:
    produced_at = produced_at_kst or _default_now_kst()
    return {
        "schema_version": schema_version,
        "artifact_id": f"art_no_trade_{_compact_timestamp(produced_at)}",
        "artifact_type": "flash_trade_document" if schema_version == FLASH_TRADE_DOCUMENT_SCHEMA else "safe_block",
        "job_id": job_id,
        "model_role": "deepseek_flash" if "flash" in job_id else "deepseek_pro",
        "model_name": DEEPSEEK_FLASH_MODEL if "flash" in job_id else DEEPSEEK_PRO_MODEL,
        "prompt_schema_version": "safe_block/v0",
        "produced_at_kst": produced_at,
        "bucket_id": bucket_id or _ten_minute_bucket_id(produced_at),
        "document_kind": "NO_TRADE",
        "no_trade_reason": str(reason or "safe_block"),
        "no_trade_reasons": [str(reason or "safe_block")],
        "actions": [],
        "order_safety": "no_direct_order",
        "ai_direct_broker_call_allowed": False,
        "validation_status": "safe_block",
        "entry_unlocked": False,
        "no_broker_call": True,
        "no_order_submission": True,
        "ai_direct_order_allowed": False,
        "redaction_status": "sanitized",
    }


def buildProvisionalCompiledWatchFromMorningWatchlist(
    morning_watchlist: Optional[Mapping[str, Any]],
    *,
    produced_at_kst: Optional[str] = None,
    default_order_cash_krw: int = 100_000,
) -> List[Dict[str, Any]]:
    produced_at = produced_at_kst or _default_now_kst()
    produced_dt = _parse_kst_timestamp(produced_at, "produced_at_kst", [])
    valid_until = (produced_dt + timedelta(minutes=10)).isoformat() if produced_dt else produced_at
    morning = deepcopy(dict(morning_watchlist or {}))
    morning_ref = str(
        morning.get("artifact_id")
        or morning.get("watchlist_id")
        or morning.get("safe_block_id")
        or ""
    ).strip()
    candidates: List[Dict[str, Any]] = []
    for item in morning.get("items") or []:
        if not isinstance(item, Mapping):
            continue
        if str(item.get("stance") or "").strip() != "eligible_for_flash_review":
            continue
        symbol = str(item.get("ticker") or item.get("symbol") or "").strip()
        if not (symbol.isdigit() and len(symbol) == 6):
            continue
        price = _safe_positive_int(
            _first_non_empty(
                item.get("entry_price_limit"),
                item.get("entry_price_krw"),
                item.get("price"),
            )
        )
        entry_zone = _normalize_price_list(item.get("entry_zone") or item.get("entryZone"))
        if not entry_zone and price > 0:
            entry_zone = [price]
        source_ids = _dedupe_strings(
            [morning_ref]
            + _string_list(item.get("source_refs"))
            + _string_list(item.get("pro_refs"))
        )
        candidate_id = f"gpt_morning_{symbol}_{_compact_timestamp(produced_at)}_{len(candidates)+1}"
        candidates.append(
            {
                "schema_version": COMPILED_WATCH_SCHEMA,
                "artifact_id": f"art_watch_{candidate_id}",
                "condition_card_id": f"condition_{candidate_id}",
                "candidate_id": candidate_id,
                "symbol": symbol,
                "ticker": symbol,
                "name": str(item.get("name") or item.get("symbol_name") or symbol),
                "source_type": "gpt_morning_watchlist_provisional",
                "source_ids": source_ids,
                "created_at_kst": produced_at,
                "valid_until_kst": valid_until,
                "compiled_at_kst": produced_at,
                "venue_route": "KRX",
                "watch_state": "morning_watchlist_provisional",
                "entry_intent": {
                    "entry_zone": entry_zone,
                    "entry_price_krw": price,
                    "take_profit": _safe_positive_int(item.get("target_price") or item.get("take_profit")),
                    "stop_loss": _safe_positive_int(item.get("stop_loss_price") or item.get("stop_loss")),
                    "planned_order_cash_krw": _safe_positive_int(item.get("planned_order_cash_krw")) or default_order_cash_krw,
                    "cancel_if_not_filled_until": valid_until,
                },
                "exit_plan": {
                    "take_profit": _safe_positive_int(item.get("target_price") or item.get("take_profit")),
                    "stop_loss": _safe_positive_int(item.get("stop_loss_price") or item.get("stop_loss")),
                },
                "watch_conditions": [
                    {
                        "watch_condition_id": f"{candidate_id}:gpt_morning",
                        "type": "morning_watchlist_flash_review",
                        "definition": {
                            "thesis": str(item.get("thesis") or ""),
                            "opening_trigger_conditions": _string_list(item.get("opening_trigger_conditions")),
                            "invalidation_conditions": _string_list(item.get("invalidation_conditions")),
                            "confidence": item.get("confidence"),
                        },
                    }
                ],
                "no_broker_call": True,
                "non_executable": True,
                "approved_adapter_enabled": False,
                "requires_kis_confirmation_before_order": True,
                "non_executable_until_kis_quote_confirmed": True,
                "kis_quote_confirmed": False,
                "krx_execution_quote_confirmed": False,
                "paper_only": True,
            }
        )
        if len(candidates) >= 5:
            break
    return candidates


def buildFlashTradeDocument(
    *,
    pro_artifact: Optional[Mapping[str, Any]],
    recent_events: Optional[Sequence[Mapping[str, Any]]],
    kis_market_snapshots: Optional[Sequence[Mapping[str, Any]]],
    compiled_watch: Optional[Sequence[Mapping[str, Any]]],
    portfolio_snapshot: Optional[Mapping[str, Any]] = None,
    order_state_snapshot: Optional[Mapping[str, Any]] = None,
    previous_trade_documents: Optional[Sequence[Mapping[str, Any]]] = None,
    morning_watchlist: Optional[Mapping[str, Any]] = None,
    provider_actions: Optional[Sequence[Mapping[str, Any]]] = None,
    investment_mode: str = rp.PAPER_INVESTMENT_MODE,
    market_analysis_feed_mode: str = rp.MARKET_ANALYSIS_FEED_INTEGRATED,
    execution_venue_mode: str = rp.EXECUTION_VENUE_KRX_ONLY,
    input_window_kst: Optional[Mapping[str, Any]] = None,
    produced_at_kst: Optional[str] = None,
) -> Dict[str, Any]:
    produced_at = produced_at_kst or _default_now_kst()
    produced_dt = _parse_kst_timestamp(produced_at, "produced_at_kst", [])
    mode = rp.normalizeInvestmentMode(investment_mode)
    market_feed = rp.normalizeMarketAnalysisFeedMode(market_analysis_feed_mode)
    execution_mode = rp.normalizeExecutionVenueMode(execution_venue_mode)
    morning = deepcopy(dict(morning_watchlist or {}))
    morning_ref = str(
        morning.get("artifact_id")
        or morning.get("watchlist_id")
        or morning.get("safe_block_id")
        or ""
    ).strip()
    morning_warnings: List[str] = []
    if produced_dt and rp.isFirstFlashBucket(produced_dt, investment_mode=mode):
        if not morning_ref:
            sentinel = buildNoTradeSentinel(
                job_id="deepseek_flash_trade_document_10m",
                reason="missing_morning_watchlist_for_first_flash_bucket",
                produced_at_kst=produced_at,
            )
            sentinel.update(
                {
                    "investment_mode": mode,
                    "market_analysis_feed_mode": market_feed,
                    "execution_venue_mode": execution_mode,
                    "morning_watchlist_ref": "",
                    "morning_watchlist_required": True,
                    "max_cash_deployment_ratio": rp.MAX_CASH_DEPLOYMENT_RATIO,
                }
            )
            return sentinel
        morning_warnings = _first_flash_morning_watchlist_warnings(morning, produced_dt)
    watch_rows = [deepcopy(dict(row)) for row in (compiled_watch or [])]
    event_rows = [deepcopy(dict(event)) for event in (recent_events or [])]
    market_rows = [deepcopy(dict(row)) for row in (kis_market_snapshots or [])]
    portfolio = deepcopy(dict(portfolio_snapshot or {}))
    order_state = deepcopy(dict(order_state_snapshot or {}))
    previous_docs = [deepcopy(dict(doc)) for doc in (previous_trade_documents or [])]
    candidate_universe_source = "kis_compiled_watch" if watch_rows else "none"
    candidate_universe_warnings: List[str] = []
    if not watch_rows:
        watch_rows = buildProvisionalCompiledWatchFromMorningWatchlist(
            morning,
            produced_at_kst=produced_at,
        )
        if watch_rows:
            candidate_universe_source = "gpt_morning_watchlist_provisional"
            candidate_universe_warnings.append("kis_compiled_watch_empty_using_morning_watchlist_fallback")

    if not pro_artifact:
        return buildNoTradeSentinel(
            job_id="deepseek_flash_trade_document_10m",
            reason="missing_pro_hourly_artifact",
            produced_at_kst=produced_at,
        )
    if not watch_rows:
        sentinel = buildNoTradeSentinel(
            job_id="deepseek_flash_trade_document_10m",
            reason="missing_compiled_watch_candidate_universe",
            produced_at_kst=produced_at,
        )
        sentinel.update(
            {
                "candidate_universe_source": "none",
                "candidate_universe_count": 0,
                "morning_watchlist_ref": morning_ref,
            }
        )
        return sentinel
    if not portfolio and not order_state and not previous_docs:
        return buildNoTradeSentinel(
            job_id="deepseek_flash_trade_document_10m",
            reason="missing_portfolio_or_order_state_context",
            produced_at_kst=produced_at,
        )

    held_symbols = _symbol_set_from_snapshot(portfolio, "holdings")
    pending_symbols = _symbol_set_from_snapshot(order_state, "pending_orders")
    active_prior_symbols = _active_symbols_from_trade_documents(previous_docs, now_kst=produced_at)
    market_refs = [
        str(row.get("artifact_id") or row.get("snapshot_id") or "").strip()
        for row in market_rows
        if str(row.get("artifact_id") or row.get("snapshot_id") or "").strip()
    ]
    source_refs = [
        str(event.get("source_event_id") or event.get("event_id") or event.get("source_id") or "").strip()
        for event in event_rows
        if str(event.get("source_event_id") or event.get("event_id") or event.get("source_id") or "").strip()
    ]
    source_ref_context = _split_flash_source_context(event_rows)
    portfolio_ref = str(portfolio.get("artifact_id") or portfolio.get("snapshot_id") or "art_portfolio_fixture").strip()
    order_state_ref = str(order_state.get("artifact_id") or order_state.get("snapshot_id") or "art_order_state_fixture").strip()
    order_open, order_close = rp.orderWindowForMode(mode)
    watch_by_symbol = {
        str(row.get("symbol") or row.get("ticker") or "").strip(): row
        for row in watch_rows
        if str(row.get("symbol") or row.get("ticker") or "").strip()
    }
    provider_rows = _normalize_flash_provider_action_sources(provider_actions, watch_by_symbol)
    action_sources = provider_rows or [
        {"row": row, "provider": {}, "action_source": "compiled_watch_deterministic_fallback"}
        for row in watch_rows[:5]
    ]
    pro_map = dict(pro_artifact or {})
    pro_regime = pro_map.get("market_regime") if isinstance(pro_map.get("market_regime"), Mapping) else {}
    pro_guidance = pro_map.get("flash_guidance") if isinstance(pro_map.get("flash_guidance"), Mapping) else {}
    pro_low_utility = (
        str(pro_map.get("investment_utility_status") or "").strip() in LOW_UTILITY_PRO_STATUSES
        or str(pro_map.get("validation_status") or "").strip() == "accepted_with_warnings"
        or pro_map.get("flash_usable") is False
    )
    market_context_open = bool(produced_dt and rp.isMarketContextOpen(produced_dt, investment_mode=mode))
    broker_order_open = bool(produced_dt and rp.isOrderWindowOpen(produced_dt, investment_mode=mode))
    bucket_end = produced_dt + timedelta(minutes=10) if produced_dt else None
    current_holdings_count = len(held_symbols)

    actions: List[Dict[str, Any]] = []
    for index, action_source in enumerate(action_sources[:5], start=1):
        row = action_source["row"]
        provider_action = action_source["provider"]
        action_source_name = action_source["action_source"]
        symbol = str(row.get("symbol") or row.get("ticker") or "").strip()
        if not symbol:
            continue
        conflict_reasons: List[str] = []
        if symbol in held_symbols:
            conflict_reasons.append("already_holding_symbol")
        if symbol in pending_symbols:
            conflict_reasons.append("pending_order_exists")
        if symbol in active_prior_symbols:
            conflict_reasons.append("prior_trade_document_still_valid")
        entry_intent = row.get("entry_intent") if isinstance(row.get("entry_intent"), Mapping) else {}
        exit_plan = row.get("exit_plan") if isinstance(row.get("exit_plan"), Mapping) else {}
        provider_action_type = _normalize_flash_action_type(provider_action.get("action") or provider_action.get("stance"))
        action = provider_action_type or "WAIT_BUY"
        if conflict_reasons and action in (FLASH_BUY_ACTIONS | {"NO_TRADE"}):
            if "pending_order_exists" in conflict_reasons:
                action = "NO_NEW_ENTRY"
            elif "already_holding_symbol" in conflict_reasons or "prior_trade_document_still_valid" in conflict_reasons:
                action = "HOLD_EXISTING_POSITION"
        quote_confirmation = _candidate_kis_confirmation(row, provider_action, market_rows, symbol=symbol)
        requires_kis_confirmation = bool(
            row.get("requires_kis_confirmation_before_order") is True
            or row.get("non_executable_until_kis_quote_confirmed") is True
            or candidate_universe_source == "gpt_morning_watchlist_provisional"
        )
        downgraded_for_kis_confirmation = False
        if action == "BUY_NOW" and requires_kis_confirmation and not quote_confirmation["quote_confirmed"]:
            action = "WAIT_BUY"
            downgraded_for_kis_confirmation = True
        if pro_low_utility and action == "BUY_NOW":
            action = "WAIT_BUY"
        entry_zone = _normalize_price_list(
            provider_action.get("entry_zone")
            or provider_action.get("entryZone")
            or entry_intent.get("entry_zone")
            or entry_intent.get("entryZone")
        )
        entry_price_limit = _first_non_empty(
            provider_action.get("entry_price_limit"),
            provider_action.get("entry_price_krw"),
            provider_action.get("price"),
            entry_zone[0] if entry_zone else None,
            entry_intent.get("entry_price_limit"),
        )
        if not entry_zone and _safe_positive_int(entry_price_limit) > 0:
            entry_zone = [_safe_positive_int(entry_price_limit)]
        stop_loss = _first_non_empty(
            provider_action.get("stop_loss_price"),
            provider_action.get("stop_loss"),
            entry_intent.get("stop_loss"),
            exit_plan.get("stop_loss"),
        )
        take_profit = _first_non_empty(
            provider_action.get("target_price"),
            provider_action.get("take_profit"),
            entry_intent.get("take_profit"),
            exit_plan.get("take_profit"),
        )
        valid_until_kst = (
            provider_action.get("valid_until_kst")
            or provider_action.get("cancel_if_not_filled_until")
            or entry_intent.get("valid_until_kst")
            or entry_intent.get("cancel_if_not_filled_until")
            or row.get("valid_until_kst")
        )
        if not valid_until_kst:
            valid_until_kst = (produced_dt + timedelta(minutes=10)).isoformat() if produced_dt else produced_at
        elif produced_dt:
            parsed_valid_until = _parse_kst_timestamp(valid_until_kst, "valid_until_kst", [])
            bucket_end_kst = produced_dt + timedelta(minutes=10)
            if parsed_valid_until and parsed_valid_until > bucket_end_kst:
                valid_until_kst = bucket_end_kst.isoformat()
        valid_from_kst = str(provider_action.get("valid_from_kst") or produced_at)
        confidence_raw = provider_action.get("confidence")
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.35 if action_source_name == "deepseek_flash_provider" else 0.25
        confidence = min(1.0, max(0.0, confidence))
        if action_source_name == "compiled_watch_deterministic_fallback":
            confidence = min(confidence, 0.35)
        urgency = str(provider_action.get("urgency") or ("medium" if action == "BUY_NOW" else "low")).strip().lower()
        if urgency not in {"low", "medium", "high"}:
            urgency = "low"
        thesis = str(
            provider_action.get("thesis")
            or provider_action.get("reason")
            or ("포트폴리오/주문 상태와 충돌해 신규 진입을 보류합니다" if conflict_reasons else "소스와 KIS 시장 데이터가 붙은 compiled_watch 후보입니다")
        )
        why_now = str(
            provider_action.get("why_now")
            or provider_action.get("whyNow")
            or ("다음 10분 동안 확인 조건이 충족되는지 관찰합니다" if action in {"WAIT_BUY", "BUY_NOW"} else "현재 조건에서는 즉시 신규 진입하지 않습니다")
        )
        required_confirmations = [
            str(item)
            for item in (
                provider_action.get("required_confirmations")
                or provider_action.get("confirmations")
                or [
                    "KRX 현재가/호가 확인",
                    "거래대금/체결강도 확인",
                    "스프레드 과도 여부 확인",
                ]
            )
            if str(item).strip()
        ]
        if requires_kis_confirmation and not quote_confirmation["quote_confirmed"]:
            required_confirmations = _dedupe_strings(
                required_confirmations + ["KIS KRX 현재가/호가 확인 후 BUY_NOW 재검토"]
            )
        cancel_if = [
            str(item)
            for item in (
                provider_action.get("cancel_if")
                or provider_action.get("cancel_conditions")
                or ["유효시간 내 거래대금/체결강도 확인 조건이 깨지면 취소"]
            )
            if str(item).strip()
        ]
        market_ref_values = _dedupe_strings(
            market_refs
            + _string_list(provider_action.get("market_data_refs"))
            + _string_list(provider_action.get("kis_market_refs"))
        )
        pro_ref_values = _dedupe_strings([str(dict(pro_artifact).get("artifact_id") or "")])
        split_refs = _flash_refs_for_symbol(
            symbol,
            row=row,
            source_ref_context=source_ref_context,
            legacy_source_refs=source_refs,
        )
        symbol_source_ref_values = _dedupe_strings(
            split_refs["symbol_source_refs"] + _string_list(provider_action.get("symbol_source_refs"))
        )
        market_context_ref_values = _dedupe_strings(
            split_refs["market_context_refs"]
            + _string_list(provider_action.get("market_context_refs"))
            + _string_list(provider_action.get("source_refs"))
        )
        source_ref_values = _dedupe_strings(symbol_source_ref_values + market_context_ref_values)
        kis_market_ref_values = market_ref_values
        source_quality_warnings: List[str] = []
        rationale_type = str(provider_action.get("rationale_type") or "").strip()
        if action_source_name == "compiled_watch_deterministic_fallback":
            rationale_type = "deterministic_market_data_fallback"
        elif not symbol_source_ref_values and kis_market_ref_values:
            rationale_type = "kis_market_data_momentum"
        elif not rationale_type:
            rationale_type = "symbol_news_and_market_data" if symbol_source_ref_values else "market_context_only"
        news_backed = bool(symbol_source_ref_values)
        if action in FLASH_BUY_ACTIONS and not symbol_source_ref_values:
            source_quality_warnings.append("no_symbol_specific_news_refs")
        if _boolish(provider_action.get("news_backed")) and not symbol_source_ref_values:
            source_quality_warnings.append("news_claim_without_symbol_specific_refs")
        would_exceed_max_holdings = action in FLASH_BUY_ACTIONS and symbol not in held_symbols and current_holdings_count + 1 > rp.MAX_SIMULTANEOUS_HOLDINGS
        bucket_hhmm = produced_dt.astimezone(KST).strftime("%H%M") if produced_dt else "0000"
        actions.append(
            {
                "action_id": f"act_{symbol}_{bucket_hhmm}_{index:02d}",
                "symbol": symbol,
                "ticker": symbol,
                "name": str(row.get("name") or row.get("symbol_name") or symbol),
                "action": action,
                "side": "BUY" if action in FLASH_BUY_ACTIONS else ("SELL" if action in FLASH_SELL_ACTIONS else "HOLD"),
                "quantity": _safe_positive_int(provider_action.get("quantity") or entry_intent.get("quantity") or row.get("quantity")),
                "entry_zone": entry_zone,
                "entry_price_limit": _safe_positive_int(entry_price_limit),
                "target_price": _safe_positive_int(take_profit),
                "take_profit": take_profit,
                "stop_loss_price": _safe_positive_int(stop_loss),
                "stop_loss": stop_loss,
                "trailing_stop_pct": _first_non_empty(
                    provider_action.get("trailing_stop_pct"),
                    entry_intent.get("trailing_stop_pct"),
                    exit_plan.get("trailing_stop_pct"),
                ),
                "cancel_if_not_filled_until": valid_until_kst,
                "valid_until": valid_until_kst,
                "valid_until_kst": valid_until_kst,
                "valid_from_kst": valid_from_kst,
                "confidence": confidence,
                "urgency": urgency,
                "position_size_pct": _first_non_empty(provider_action.get("position_size_pct"), entry_intent.get("position_size_pct")),
                "planned_order_cash_krw": _safe_positive_int(
                    provider_action.get("planned_order_cash_krw")
                    or provider_action.get("max_cash_krw")
                    or entry_intent.get("planned_order_cash_krw")
                    or row.get("planned_order_cash_krw")
                ),
                "max_cash_deployment_ratio": rp.MAX_CASH_DEPLOYMENT_RATIO,
                "source_refs": source_ref_values,
                "symbol_source_refs": symbol_source_ref_values,
                "market_context_refs": market_context_ref_values,
                "pro_refs": pro_ref_values,
                "pro_context_refs": pro_ref_values,
                "morning_watchlist_ref": morning_ref,
                "morning_watchlist_refs": _dedupe_strings([morning_ref]),
                "market_data_refs": market_ref_values,
                "kis_market_refs": kis_market_ref_values,
                "portfolio_state_refs": [portfolio_ref, order_state_ref],
                "rationale_type": rationale_type,
                "news_backed": news_backed,
                "source_quality_warnings": source_quality_warnings,
                "portfolio_conflict": {
                    "already_holding": "already_holding_symbol" in conflict_reasons,
                    "pending_order_exists": "pending_order_exists" in conflict_reasons,
                    "active_exit_exists": False,
                    "cooldown_active": False,
                    "position_locked": False,
                    "has_conflict": bool(conflict_reasons),
                    "reasons": conflict_reasons,
                },
                "portfolio_conflict_check": {
                    "already_holding": "already_holding_symbol" in conflict_reasons,
                    "pending_order_conflict": "pending_order_exists" in conflict_reasons,
                    "would_exceed_max_holdings": would_exceed_max_holdings,
                    "would_exceed_75pct_exposure": False,
                },
                "reason": thesis,
                "thesis": thesis,
                "why_now": why_now,
                "required_confirmations": required_confirmations,
                "cancel_if": cancel_if,
                "risk_notes": [str(item) for item in provider_action.get("risk_notes") or [] if str(item).strip()],
                "risk_flags": _dedupe_strings(
                    conflict_reasons
                    + (
                        ["gpt_morning_fallback_buy_now_downgraded_until_kis_quote_confirmed"]
                        if downgraded_for_kis_confirmation
                        else []
                    )
                ),
                "action_source": action_source_name,
                "candidate_universe_source": candidate_universe_source,
                "source_type": str(row.get("source_type") or candidate_universe_source),
                "requires_kis_confirmation_before_order": requires_kis_confirmation,
                "non_executable_until_kis_quote_confirmed": bool(
                    requires_kis_confirmation and not quote_confirmation["quote_confirmed"]
                ),
                "kis_quote_confirmed": bool(quote_confirmation["quote_confirmed"]),
                "krx_execution_quote_confirmed": bool(quote_confirmation["quote_confirmed"]),
                "kis_orderbook_confirmed": bool(quote_confirmation["orderbook_confirmed"]),
                "executable_intent_allowed": False,
                "paper_only": True,
                "no_live_order": True,
            }
        )

    if not actions:
        return buildNoTradeSentinel(
            job_id="deepseek_flash_trade_document_10m",
            reason="no_valid_compiled_watch_symbols",
            produced_at_kst=produced_at,
        )

    position_actions = _build_flash_position_actions(
        portfolio_snapshot=portfolio,
        order_state_snapshot=order_state,
        market_rows=market_rows,
        produced_at_kst=produced_at,
        portfolio_ref=portfolio_ref,
        order_state_ref=order_state_ref,
        market_refs=market_refs,
    )
    entry_actions_present = any(action.get("action") in (FLASH_BUY_ACTIONS | FLASH_SELL_ACTIONS) for action in actions)
    management_actions_present = any(action.get("action") in FLASH_MANAGEMENT_ACTIONS for action in actions) or bool(position_actions)
    document_kind = (
        "TRADE_ACTIONS_WITH_NO_NEW_ENTRY"
        if entry_actions_present and management_actions_present
        else ("TRADE_ACTIONS" if entry_actions_present else "POSITION_MANAGEMENT")
    )
    new_entry_policy = (
        "ENTRY_CANDIDATES_PRESENT"
        if entry_actions_present
        else ("NO_NEW_ENTRY_EXISTING_ORDER_OR_POSITION" if management_actions_present else "NO_NEW_ENTRY")
    )

    return {
        "schema_version": FLASH_TRADE_DOCUMENT_SCHEMA,
        "artifact_id": f"art_flash_tdoc_{_compact_timestamp(produced_at)}",
        "artifact_type": "flash_trade_document",
        "job_id": "deepseek_flash_trade_document_10m",
        "model_role": "deepseek_flash",
        "model_name": DEEPSEEK_FLASH_MODEL,
        "prompt_schema_version": "flash_trade_document_prompt/v1",
        "produced_at_kst": produced_at,
        "investment_mode": mode,
        "market_analysis_feed_mode": market_feed,
        "execution_venue_mode": execution_mode,
        "order_safety": "no_direct_order",
        "ai_direct_broker_call_allowed": False,
        "trade_window_kst": {
            "start_kst": produced_at,
            "end_kst": bucket_end.isoformat() if bucket_end else produced_at,
            "bucket_seconds": 600,
            "order_session": f"{order_open.strftime('%H:%M')}-{order_close.strftime('%H:%M')}",
        },
        "input_window_kst": dict(input_window_kst or {}),
        "bucket_id": _ten_minute_bucket_id(produced_at),
        "document_kind": document_kind,
        "new_entry_policy": new_entry_policy,
        "pro_hourly_report_ref": str(dict(pro_artifact).get("artifact_id") or ""),
        "pro_hourly_ref": str(dict(pro_artifact).get("artifact_id") or ""),
        "morning_watchlist_ref": morning_ref,
        "morning_watchlist_required": bool(produced_dt and rp.isFirstFlashBucket(produced_dt, investment_mode=mode)),
        "morning_watchlist_status": "provisional" if morning_warnings else ("accepted" if morning_ref else "missing"),
        "morning_watchlist_warnings": morning_warnings,
        "morning_watchlist_refresh_required": bool(
            morning.get("requires_monday_refresh") is True
            or any("refresh" in warning for warning in morning_warnings)
        ),
        "source_refs": source_refs,
        "symbol_source_refs": _dedupe_strings(
            ref for action in actions for ref in action.get("symbol_source_refs", [])
        ),
        "market_context_refs": _dedupe_strings(
            ref for action in actions for ref in action.get("market_context_refs", [])
        ),
        "market_data_refs": market_refs,
        "kis_market_refs": market_refs,
        "compiled_watch_refs": [
            str(row.get("artifact_id") or row.get("condition_card_id") or row.get("candidate_id") or "")
            for row in watch_rows
        ],
        "candidate_universe_source": candidate_universe_source,
        "candidate_universe_count": len(watch_rows),
        "candidate_universe_symbols": [str(row.get("symbol") or row.get("ticker") or "").strip() for row in watch_rows],
        "portfolio_snapshot_ref": portfolio_ref,
        "order_state_snapshot_ref": order_state_ref,
        "refs": {
            "pro_hourly_report_ref": str(dict(pro_artifact).get("artifact_id") or ""),
            "morning_watchlist_ref": morning_ref,
            "portfolio_ref": portfolio_ref,
            "order_state_ref": order_state_ref,
            "market_context_refs": _dedupe_strings(
                ref for action in actions for ref in action.get("market_context_refs", [])
            ),
            "kis_market_refs": market_refs,
        },
        "market_context": {
            "regime_mode": str(pro_regime.get("mode") or pro_regime.get("market_mode") or "NEUTRAL"),
            "flash_bias": str(pro_guidance.get("preferred_bias") or "selective_watch"),
            "market_context_open": market_context_open,
            "broker_order_open": broker_order_open,
            "kis_realtime_expected": market_context_open,
        },
        "portfolio_constraints": {
            "max_holdings": rp.MAX_SIMULTANEOUS_HOLDINGS,
            "current_holdings_count": current_holdings_count,
            "max_cash_deployment_ratio": rp.MAX_CASH_DEPLOYMENT_RATIO,
            "new_entries_allowed": broker_order_open and current_holdings_count < rp.MAX_SIMULTANEOUS_HOLDINGS,
        },
        "previous_trade_document_refs": [
            str(doc.get("artifact_id") or doc.get("document_id") or "") for doc in previous_docs
        ],
        "actions": actions,
        "position_actions": position_actions,
        "no_trade_reasons": [],
        "global_risk_flags": ["pro_hourly_low_utility", "pro_context_low_utility"] if pro_low_utility else [],
        "warnings": candidate_universe_warnings,
        "operator_notes": candidate_universe_warnings,
        "analysis_language": "ko-KR",
        "max_holdings_after_trade": rp.MAX_SIMULTANEOUS_HOLDINGS,
        "max_cash_deployment_ratio": rp.MAX_CASH_DEPLOYMENT_RATIO,
        "validation_status": "pending",
        "entry_unlocked": False,
        "no_broker_call": True,
        "no_order_submission": True,
        "ai_direct_order_allowed": False,
        "redaction_status": "sanitized",
    }


def _candidate_kis_confirmation(
    row: Mapping[str, Any],
    provider_action: Mapping[str, Any],
    market_rows: Sequence[Mapping[str, Any]],
    *,
    symbol: str,
) -> Dict[str, bool]:
    if row.get("kis_quote_confirmed") is True or row.get("krx_execution_quote_confirmed") is True:
        return {
            "quote_confirmed": True,
            "orderbook_confirmed": bool(row.get("kis_orderbook_confirmed") or row.get("orderbook_confirmed")),
        }
    del provider_action
    quote_confirmed = False
    orderbook_confirmed = False
    for market in market_rows:
        for candidate in _iter_nested_market_rows(market):
            row_symbol = _first_non_empty(
                candidate.get("mksc_shrn_iscd"),
                candidate.get("stck_shrn_iscd"),
                candidate.get("pdno"),
                candidate.get("stck_code"),
                candidate.get("iscd"),
                candidate.get("isu_cd"),
                candidate.get("code"),
            )
            if str(row_symbol or "").strip() != symbol:
                continue
            price = _safe_positive_int(
                _first_non_empty(
                    candidate.get("stck_prpr"),
                    candidate.get("prpr"),
                    candidate.get("price"),
                    candidate.get("last"),
                    candidate.get("askp1"),
                    candidate.get("bidp1"),
                )
            )
            if price > 0:
                quote_confirmed = True
            if _safe_positive_int(candidate.get("askp1")) > 0 and _safe_positive_int(candidate.get("bidp1")) > 0:
                orderbook_confirmed = True
    return {"quote_confirmed": quote_confirmed, "orderbook_confirmed": orderbook_confirmed}


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _row_symbol(value: Mapping[str, Any]) -> str:
    return str(
        _first_non_empty(
            value.get("symbol"),
            value.get("ticker"),
            value.get("mksc_shrn_iscd"),
            value.get("stck_shrn_iscd"),
            value.get("pdno"),
            value.get("stck_code"),
            value.get("iscd"),
            value.get("isu_cd"),
            value.get("code"),
        )
        or ""
    ).strip()


def _source_ref_id(value: Mapping[str, Any]) -> str:
    return str(value.get("source_event_id") or value.get("event_id") or value.get("source_id") or "").strip()


def _split_flash_source_context(event_rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    symbol_refs: Dict[str, List[str]] = {}
    refs_by_id: Dict[str, Mapping[str, Any]] = {}
    market_context_refs: List[str] = []
    for event in event_rows:
        if not isinstance(event, Mapping):
            continue
        ref = _source_ref_id(event)
        if not ref:
            continue
        refs_by_id[ref] = event
        symbol = _row_symbol(event)
        if symbol:
            symbol_refs.setdefault(symbol, []).append(ref)
        else:
            market_context_refs.append(ref)
    return {
        "symbol_refs": {symbol: _dedupe_strings(refs) for symbol, refs in symbol_refs.items()},
        "market_context_refs": _dedupe_strings(market_context_refs),
        "refs_by_id": refs_by_id,
    }


def _flash_refs_for_symbol(
    symbol: str,
    *,
    row: Mapping[str, Any],
    source_ref_context: Mapping[str, Any],
    legacy_source_refs: Sequence[Any],
) -> Dict[str, List[str]]:
    symbol_ref_map = (
        source_ref_context.get("symbol_refs")
        if isinstance(source_ref_context.get("symbol_refs"), Mapping)
        else {}
    )
    refs_by_id = (
        source_ref_context.get("refs_by_id")
        if isinstance(source_ref_context.get("refs_by_id"), Mapping)
        else {}
    )
    symbol_refs = _dedupe_strings(symbol_ref_map.get(symbol, []))
    market_context_refs = _dedupe_strings(source_ref_context.get("market_context_refs") or [])
    for ref in _string_list(row.get("source_ids")) + _string_list(row.get("source_refs")):
        event = refs_by_id.get(ref) if isinstance(refs_by_id, Mapping) else None
        if isinstance(event, Mapping) and _row_symbol(event) == symbol:
            symbol_refs.append(ref)
        else:
            market_context_refs.append(ref)
    known_refs = set(symbol_refs) | set(market_context_refs)
    for ref in legacy_source_refs:
        text = str(ref or "").strip()
        if text and text not in known_refs:
            market_context_refs.append(text)
    return {
        "symbol_source_refs": _dedupe_strings(symbol_refs),
        "market_context_refs": _dedupe_strings(market_context_refs),
    }


def _snapshot_rows(snapshot: Mapping[str, Any], key: str) -> List[Mapping[str, Any]]:
    rows = snapshot.get(key)
    if isinstance(rows, Mapping):
        iterable = rows.values()
    elif isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
        iterable = rows
    else:
        iterable = []
    return [row for row in iterable if isinstance(row, Mapping)]


def _kis_current_price_for_symbol(market_rows: Sequence[Mapping[str, Any]], *, symbol: str) -> int:
    for market in market_rows:
        for candidate in _iter_nested_market_rows(market):
            if _row_symbol(candidate) != symbol:
                continue
            price = _safe_positive_int(
                _first_non_empty(
                    candidate.get("stck_prpr"),
                    candidate.get("prpr"),
                    candidate.get("price"),
                    candidate.get("last"),
                    candidate.get("askp1"),
                    candidate.get("bidp1"),
                )
            )
            if price > 0:
                return price
    return 0


def _position_state_from_order_row(row: Mapping[str, Any]) -> str:
    explicit = str(row.get("position_state") or row.get("order_state") or row.get("state") or row.get("status") or "").strip().lower()
    if explicit in {"submitted_unreconciled", "order_submitted_fill_status_unknown"}:
        return "submitted_unreconciled"
    if explicit in {"filled", "filled_holding_confirmed", "holding_confirmed", "holding"}:
        return "holding_confirmed"
    if row.get("submitted_at_kst") or str(row.get("action") or "").strip() in FLASH_BUY_ACTIONS:
        return "submitted_unreconciled"
    return "pending_order"


def _build_position_action(
    row: Mapping[str, Any],
    *,
    position_state: str,
    market_rows: Sequence[Mapping[str, Any]],
    produced_at_kst: str,
    portfolio_ref: str,
    order_state_ref: str,
    market_refs: Sequence[Any],
) -> Optional[Dict[str, Any]]:
    symbol = _row_symbol(row)
    if not symbol:
        return None
    current_price = _kis_current_price_for_symbol(market_rows, symbol=symbol)
    target_price = _safe_positive_int(row.get("target_price") or row.get("take_profit"))
    stop_loss_price = _safe_positive_int(row.get("stop_loss_price") or row.get("stop_loss"))
    action = "WAIT_ORDER_RECONCILIATION" if position_state == "submitted_unreconciled" else "HOLD_EXISTING_POSITION"
    reason = "주문 접수됨, 체결/보유 반영 확인 대기" if position_state == "submitted_unreconciled" else "기존 보유/주문 상태 관리"
    if current_price > 0 and (
        (target_price > 0 and current_price >= target_price)
        or (stop_loss_price > 0 and current_price <= stop_loss_price)
    ):
        action = "EXIT_REVIEW"
        reason = "KIS 현재가가 익절/손절 기준에 닿아 청산 검토 필요"
    elif current_price <= 0:
        reason = f"{reason}; KIS 현재가 부재로 SELL_NOW 금지"
    return {
        "symbol": symbol,
        "ticker": symbol,
        "name": str(row.get("name") or row.get("symbol_name") or symbol),
        "position_state": position_state,
        "action": action,
        "target_price": target_price,
        "stop_loss_price": stop_loss_price,
        "current_price": current_price,
        "quantity": _safe_positive_int(row.get("quantity")),
        "entry_price_limit": _safe_positive_int(row.get("entry_price_limit") or row.get("order_price") or row.get("price")),
        "take_profit": row.get("take_profit") or target_price,
        "stop_loss": row.get("stop_loss") or stop_loss_price,
        "trailing_stop_pct": row.get("trailing_stop_pct"),
        "reason": reason,
        "next_check": "다음 Flash에서 체결/보유 reconciliation과 KIS 현재가를 다시 확인",
        "portfolio_state_refs": [portfolio_ref, order_state_ref],
        "market_data_refs": _dedupe_strings(market_refs),
        "kis_market_refs": _dedupe_strings(market_refs),
        "produced_at_kst": produced_at_kst,
        "paper_only": True,
        "no_live_order": True,
    }


def _build_flash_position_actions(
    *,
    portfolio_snapshot: Mapping[str, Any],
    order_state_snapshot: Mapping[str, Any],
    market_rows: Sequence[Mapping[str, Any]],
    produced_at_kst: str,
    portfolio_ref: str,
    order_state_ref: str,
    market_refs: Sequence[Any],
) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for row in _snapshot_rows(order_state_snapshot, "pending_orders"):
        symbol = _row_symbol(row)
        if not symbol or symbol in seen:
            continue
        action = _build_position_action(
            row,
            position_state=_position_state_from_order_row(row),
            market_rows=market_rows,
            produced_at_kst=produced_at_kst,
            portfolio_ref=portfolio_ref,
            order_state_ref=order_state_ref,
            market_refs=market_refs,
        )
        if action:
            actions.append(action)
            seen.add(symbol)
    for row in _snapshot_rows(portfolio_snapshot, "holdings"):
        symbol = _row_symbol(row)
        if not symbol or symbol in seen:
            continue
        action = _build_position_action(
            row,
            position_state="holding_confirmed",
            market_rows=market_rows,
            produced_at_kst=produced_at_kst,
            portfolio_ref=portfolio_ref,
            order_state_ref=order_state_ref,
            market_refs=market_refs,
        )
        if action:
            actions.append(action)
            seen.add(symbol)
    return actions[:5]


def _iter_nested_market_rows(value: Any) -> List[Mapping[str, Any]]:
    rows: List[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        if any(key in value for key in ("mksc_shrn_iscd", "stck_shrn_iscd", "pdno", "stck_code", "iscd", "isu_cd", "code")):
            rows.append(value)
        for key in ("rows_preview", "output", "output1", "output2", "items", "input_results"):
            child = value.get(key)
            if isinstance(child, list):
                for item in child:
                    rows.extend(_iter_nested_market_rows(item))
            elif isinstance(child, Mapping):
                rows.extend(_iter_nested_market_rows(child))
        market_classes = value.get("market_classes")
        if isinstance(market_classes, Mapping):
            for child in market_classes.values():
                rows.extend(_iter_nested_market_rows(child))
    elif isinstance(value, list):
        for item in value:
            rows.extend(_iter_nested_market_rows(item))
    return rows


def validateProHourlyMarketAnalysis(
    document: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    payload = normalizeProHourlyOutputCaps(document)
    errors: List[str] = []
    warnings: List[str] = list(payload.get("warnings") or []) if isinstance(payload.get("warnings"), list) else []

    has_v1_strategy_fields = any(
        key in payload
        for key in (
            "data_quality",
            "market_regime",
            "theme_map",
            "flash_guidance",
            "no_trade_conditions",
            "source_ref_map",
            "investment_utility_status",
        )
    )
    legacy_summary_only = (
        payload.get("schema_version") not in {PRO_HOURLY_SCHEMA}
        or not has_v1_strategy_fields
    ) and any(key in payload for key in ("summary", "themes", "risk_flags"))

    if legacy_summary_only:
        warnings.append("pro_hourly_low_utility_news_only")
        payload["schema_version"] = PRO_HOURLY_SCHEMA
        payload["document_kind"] = "MARKET_STRATEGY_CONTEXT"
        payload["analysis_language"] = "ko-KR"
        payload["order_safety"] = "no_order"
        payload["ai_direct_order_allowed"] = False
        payload.setdefault("data_quality", {
            "news_event_count": payload.get("source_event_count", 0),
            "kis_market_snapshot_count": payload.get("kis_market_snapshot_count", 0),
            "kis_data_status": "missing",
            "runtime_kis_failure_evidence_present": False,
            "missing_inputs": ["kis_market_strategy_context"],
            "warnings": [],
        })
        payload.setdefault("market_regime", {
            "mode": str(payload.get("market_mode") or "NO_TRADE"),
            "market_mode": str(payload.get("market_mode") or "NO_TRADE"),
            "confidence": 0.0,
            "why": [],
        })
        payload.setdefault("theme_map", [])
        payload.setdefault("flash_guidance", {})
        payload.setdefault("no_trade_conditions", [])
        payload.setdefault("contradiction_notes", [])
        payload.setdefault("source_ref_map", [])
        payload.setdefault("questions_for_next_flash", [])
        payload["investment_utility_status"] = "news_only_low_utility"
        payload["validation_status"] = "accepted_with_warnings"
        payload["warnings"] = _dedupe_strings(warnings)
        return {
            "ok": True,
            "errors": [],
            "warnings": payload["warnings"],
            "document": payload,
            "validation_status": payload["validation_status"],
        }

    if payload.get("schema_version") != PRO_HOURLY_SCHEMA:
        errors.append("schema_version_must_be_pro_hourly_market_analysis_v1")
    if payload.get("order_safety") != "no_order":
        errors.append("order_safety_must_be_no_order")
    if payload.get("ai_direct_order_allowed") is not False:
        errors.append("ai_direct_order_allowed_must_be_false")
    if not isinstance(payload.get("data_quality"), Mapping):
        errors.append("data_quality_required")

    regime = payload.get("market_regime") if isinstance(payload.get("market_regime"), Mapping) else {}
    mode = str(regime.get("mode") or regime.get("market_mode") or "").strip()
    if not mode:
        errors.append("market_regime_mode_required")
    try:
        confidence = float(regime.get("confidence"))
    except (TypeError, ValueError):
        errors.append("market_regime_confidence_required")
    else:
        if confidence < 0 or confidence > 1:
            errors.append("market_regime_confidence_invalid")

    theme_map = payload.get("theme_map")
    no_trade_conditions = payload.get("no_trade_conditions")
    if not isinstance(theme_map, list):
        errors.append("theme_map_must_be_list")
        theme_map = []
    if not isinstance(no_trade_conditions, list):
        errors.append("no_trade_conditions_must_be_list")
        no_trade_conditions = []
    if not theme_map and not no_trade_conditions:
        errors.append("theme_map_or_no_trade_conditions_required")
    if not isinstance(payload.get("flash_guidance"), Mapping):
        errors.append("flash_guidance_required")
    if not isinstance(payload.get("source_ref_map"), list):
        errors.append("source_ref_map_required")
    if not str(payload.get("investment_utility_status") or "").strip():
        errors.append("investment_utility_status_required")

    _normalize_off_session_data_quality(payload)

    provider = payload.get("provider") if isinstance(payload.get("provider"), Mapping) else {}
    if provider.get("finish_reason") == "length":
        _apply_low_utility_pro_status(
            payload,
            warnings,
            status="truncated_low_utility",
            warning="provider_output_truncated",
        )

    semantic_warnings = _semantic_pro_quality_warnings(payload)
    if semantic_warnings:
        warnings.extend(semantic_warnings)
        if "provider_output_truncated" not in warnings and payload.get("investment_utility_status") not in {"truncated_low_utility"}:
            _apply_low_utility_pro_status(
                payload,
                warnings,
                status="news_only_low_utility",
                warning="low_investment_utility",
            )

    payload["warnings"] = _dedupe_strings(warnings)
    if errors:
        payload["validation_status"] = "rejected"
    elif payload.get("document_kind") == "NO_TRADE":
        payload["validation_status"] = "safe_block"
    elif payload.get("investment_utility_status") in LOW_UTILITY_PRO_STATUSES or payload.get("flash_usable") is False:
        payload["validation_status"] = "accepted_with_warnings"
    else:
        payload["validation_status"] = "accepted"
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": payload["warnings"],
        "document": payload,
        "validation_status": payload["validation_status"],
    }


def validateFlashTradeDocument(
    document: Optional[Mapping[str, Any]],
    *,
    compiled_watch: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    payload = deepcopy(dict(document or {}))
    errors: List[str] = []
    warnings: List[str] = list(payload.get("warnings") or []) if isinstance(payload.get("warnings"), list) else []

    if payload.get("schema_version") != FLASH_TRADE_DOCUMENT_SCHEMA:
        errors.append("schema_version_must_be_flash_trade_document_v0")
    if payload.get("investment_mode") not in {None, rp.PAPER_INVESTMENT_MODE, rp.LIVE_INVESTMENT_MODE}:
        errors.append("investment_mode_invalid")
    if payload.get("market_analysis_feed_mode") not in {None, rp.MARKET_ANALYSIS_FEED_INTEGRATED}:
        errors.append("market_analysis_feed_mode_must_be_integrated")
    if payload.get("execution_venue_mode") not in {None, rp.EXECUTION_VENUE_KRX_ONLY}:
        errors.append("execution_venue_mode_must_be_krx_only")
    if payload.get("order_safety") != "no_direct_order":
        errors.append("order_safety_must_be_no_direct_order")
    if payload.get("ai_direct_broker_call_allowed") is not False:
        errors.append("ai_direct_broker_call_allowed_must_be_false")
    if payload.get("document_kind") != "NO_TRADE" and not payload.get("pro_hourly_report_ref"):
        errors.append("pro_hourly_report_ref_required")
    if payload.get("morning_watchlist_required") is True and not payload.get("morning_watchlist_ref"):
        errors.append("morning_watchlist_ref_required_for_first_flash_bucket")
    if payload.get("model_name") != DEEPSEEK_FLASH_MODEL:
        errors.append("flash_model_must_be_deepseek_v4_flash")
    if payload.get("no_broker_call") is not True or payload.get("no_order_submission") is not True:
        errors.append("flash_document_must_be_non_executable")
    if payload.get("ai_direct_order_allowed") is not False:
        errors.append("ai_direct_order_must_be_false")

    actions = payload.get("actions")
    if not isinstance(actions, list):
        errors.append("actions_must_be_list")
        actions = []
    if len(actions) > 5:
        errors.append("actions_max_five_symbols")

    universe = {
        str(row.get("symbol") or row.get("ticker") or "").strip()
        for row in (compiled_watch or [])
        if str(row.get("symbol") or row.get("ticker") or "").strip()
    }
    if not universe:
        universe = {
            str(item or "").strip()
            for item in (payload.get("candidate_universe_symbols") or [])
            if str(item or "").strip()
        }
    produced_dt = _parse_kst_timestamp(payload.get("produced_at_kst"), "produced_at_kst", [])
    bucket_end = produced_dt + timedelta(minutes=10) if produced_dt else None
    mode = rp.normalizeInvestmentMode(payload.get("investment_mode"))
    market_context = payload.get("market_context") if isinstance(payload.get("market_context"), Mapping) else {}
    market_context_open = market_context.get("market_context_open")
    broker_order_open = market_context.get("broker_order_open")
    if market_context_open is None and produced_dt:
        market_context_open = rp.isMarketContextOpen(produced_dt, investment_mode=mode)
    if broker_order_open is None and produced_dt:
        broker_order_open = rp.isOrderWindowOpen(produced_dt, investment_mode=mode)
    global_risk_flags = {
        str(item or "").strip()
        for item in (payload.get("global_risk_flags") or [])
        if str(item or "").strip()
    }
    pro_context_low_utility = bool(global_risk_flags & {"pro_hourly_low_utility", "pro_context_low_utility"})
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            errors.append(f"actions_item_{index}_must_be_object")
            continue
        symbol = str(action.get("ticker") or action.get("symbol") or "").strip()
        if not symbol:
            errors.append(f"actions_item_{index}_ticker_required")
        elif universe and symbol not in universe:
            errors.append(f"actions_item_{index}_off_universe_ticker")
        action_type = str(action.get("action") or "").strip()
        if action_type not in FLASH_ACTION_TYPES:
            errors.append(f"actions_item_{index}_action_invalid")
        side = str(action.get("side") or "").strip().upper()
        is_buy = action_type in FLASH_BUY_ACTIONS
        is_sell = action_type in FLASH_SELL_ACTIONS or side == "SELL"
        valid_until = _parse_kst_timestamp(action.get("valid_until_kst"), f"actions_item_{index}_valid_until_kst", [])
        if valid_until and bucket_end and valid_until > bucket_end:
            errors.append(f"actions_item_{index}_valid_until_kst_must_be_within_bucket")
        if mode == rp.PAPER_INVESTMENT_MODE and produced_dt and not rp.isOrderWindowOpen(produced_dt, investment_mode=mode):
            if is_buy or is_sell:
                errors.append(f"actions_item_{index}_paper_buy_sell_after_1500_forbidden")
        if (market_context_open is False or broker_order_open is False) and action_type not in FLASH_MANAGEMENT_ACTIONS:
            errors.append(f"actions_item_{index}_market_or_order_closed_must_hold_or_no_trade")
        confidence = action.get("confidence")
        if confidence is None:
            errors.append(f"actions_item_{index}_confidence_required")
        else:
            try:
                confidence_float = float(confidence)
            except (TypeError, ValueError):
                errors.append(f"actions_item_{index}_confidence_invalid")
            else:
                if confidence_float < 0 or confidence_float > 1:
                    errors.append(f"actions_item_{index}_confidence_invalid")
        if action_type in FLASH_BUY_ACTIONS:
            provisional_without_kis_quote = (
                action.get("requires_kis_confirmation_before_order") is True
                and action.get("kis_quote_confirmed") is not True
                and str(action.get("candidate_universe_source") or payload.get("candidate_universe_source") or "")
                == "gpt_morning_watchlist_provisional"
            )
            symbol_refs = action.get("symbol_source_refs") if isinstance(action.get("symbol_source_refs"), list) else []
            kis_refs = (
                action.get("kis_market_refs")
                if isinstance(action.get("kis_market_refs"), list)
                else action.get("market_data_refs")
            )
            has_kis_refs = bool(kis_refs)
            action_warnings = (
                list(action.get("source_quality_warnings") or [])
                if isinstance(action.get("source_quality_warnings"), list)
                else []
            )
            for warning in action_warnings:
                warnings.append(f"actions_item_{index}_{warning}")
            if not symbol_refs and has_kis_refs:
                if isinstance(action, dict):
                    action.setdefault("rationale_type", "kis_market_data_momentum")
                    action["news_backed"] = False
                if "no_symbol_specific_news_refs" not in action_warnings:
                    action_warnings.append("no_symbol_specific_news_refs")
                if isinstance(action, dict):
                    action["source_quality_warnings"] = action_warnings
                warnings.append(f"actions_item_{index}_no_symbol_specific_news_refs")
            claimed_news = str(action.get("rationale_type") or "").strip().lower() in {
                "news",
                "news_catalyst",
                "symbol_news",
                "symbol_news_and_market_data",
            } or action.get("news_backed") is True
            if claimed_news and not symbol_refs:
                if "news_claim_without_symbol_specific_refs" not in action_warnings:
                    action_warnings.append("news_claim_without_symbol_specific_refs")
                if isinstance(action, dict):
                    action["source_quality_warnings"] = action_warnings
                    action["news_backed"] = False
                warnings.append(f"actions_item_{index}_news_claim_without_symbol_specific_refs")
            if side not in {"BUY"}:
                errors.append(f"actions_item_{index}_side_buy_required")
            if action.get("valid_until_kst") in (None, ""):
                errors.append(f"actions_item_{index}_valid_until_kst_required")
            if _safe_positive_int(action.get("entry_price_limit")) <= 0:
                errors.append(f"actions_item_{index}_entry_price_limit_required")
            if _safe_positive_int(action.get("target_price")) <= 0:
                errors.append(f"actions_item_{index}_target_price_required")
            if _safe_positive_int(action.get("stop_loss_price")) <= 0:
                errors.append(f"actions_item_{index}_stop_loss_price_required")
            if not action.get("source_refs") and not symbol_refs and not has_kis_refs:
                errors.append(f"actions_item_{index}_source_refs_required")
            if not action.get("pro_refs"):
                errors.append(f"actions_item_{index}_pro_refs_required")
            if not action.get("market_data_refs") and not provisional_without_kis_quote:
                errors.append(f"actions_item_{index}_market_data_refs_required")
            ref_kind_count = sum(
                1
                for key in ("symbol_source_refs", "source_refs", "pro_refs", "kis_market_refs", "market_data_refs")
                if action.get(key)
            )
            if action_type == "BUY_NOW" and ref_kind_count < 2:
                errors.append(f"actions_item_{index}_buy_now_requires_two_ref_kinds")
            if action_type == "BUY_NOW" and pro_context_low_utility:
                errors.append(f"actions_item_{index}_buy_now_forbidden_when_pro_context_low_utility")
            if action_type == "BUY_NOW" and (
                _safe_positive_int(action.get("quantity")) <= 0
                and _safe_positive_int(action.get("planned_order_cash_krw")) <= 0
            ):
                errors.append(f"actions_item_{index}_buy_now_size_required")
            if not action.get("portfolio_state_refs"):
                errors.append(f"actions_item_{index}_portfolio_state_refs_required")
            if action.get("paper_only") is not True or action.get("no_live_order") is not True:
                errors.append(f"actions_item_{index}_paper_only_required")
            for text_key in ("thesis", "why_now"):
                if not str(action.get(text_key) or "").strip():
                    errors.append(f"actions_item_{index}_{text_key}_required")
            if not action.get("required_confirmations"):
                errors.append(f"actions_item_{index}_required_confirmations_required")
            if not action.get("cancel_if"):
                errors.append(f"actions_item_{index}_cancel_if_required")
    if payload.get("document_kind") == "NO_TRADE" and actions:
        errors.append("no_trade_document_must_have_empty_actions")
    if payload.get("document_kind") == "NO_TRADE" and not payload.get("no_trade_reason"):
        errors.append("no_trade_reason_required")

    payload["warnings"] = _dedupe_strings(warnings)
    payload["validation_status"] = "rejected" if errors else (
        "safe_block" if payload.get("document_kind") == "NO_TRADE" else "accepted"
    )
    return {"ok": not errors, "errors": errors, "document": payload}


def reviewAiRequestPayload(payload: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    body = deepcopy(dict(payload or {}))
    violations: List[str] = []
    redacted_fields: List[str] = []

    for key, value in _flatten_key_values(body):
        if _is_sensitive_payload_key(key):
            violations.append(f"sensitive_field_forbidden:{key}")
            redacted_fields.append(key)
            continue
        if isinstance(value, str):
            lowered_value = value.lower()
            if any(fragment in lowered_value for fragment in SENSITIVE_PAYLOAD_FRAGMENTS):
                violations.append(f"sensitive_value_forbidden:{key}")
                redacted_fields.append(key)
            if _contains_forbidden_token(lowered_value, FORBIDDEN_BROKER_TOKENS):
                violations.append(f"broker_reference_forbidden:{key}")

    return {
        "ok": not violations,
        "violations": violations,
        "redacted_fields": sorted(set(redacted_fields)),
        "redaction_status": "full" if violations else "none",
        "payload_reviewed": True,
    }


def validateAiRecommendation(
    output: Optional[Mapping[str, Any]],
    *,
    known_source_ids: Optional[Sequence[str]] = None,
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    payload = deepcopy(dict(output or {}))
    errors: List[str] = []
    policy_violations: List[str] = []

    _validate_common_output_envelope(payload, errors, now_kst=now_kst)

    if payload.get("schema_version") != AI_RECOMMENDATION_SCHEMA:
        errors.append("schema_version_must_be_ai_recommendation_v0")

    recommendation_id = str(payload.get("recommendation_id") or "").strip()
    if not recommendation_id:
        errors.append("recommendation_id_required")

    action = str(payload.get("action") or "").strip()
    if action not in ALLOWED_ACTIONS:
        errors.append("action_unknown_or_missing")

    candidate_id = str(payload.get("candidate_id") or "").strip()
    if not candidate_id:
        errors.append("candidate_id_required")

    symbol = str(payload.get("symbol") or "").strip()
    if not symbol:
        errors.append("symbol_required")

    source_path = str(payload.get("source_path") or "").strip()
    if source_path not in ALLOWED_SOURCE_PATHS:
        errors.append("source_path_invalid")

    chart_interval = str(payload.get("chart_interval") or "").strip()
    if chart_interval and chart_interval not in ALLOWED_CHART_INTERVALS:
        errors.append("chart_interval_invalid")

    confidence = str(payload.get("confidence") or "").strip()
    if confidence not in ALLOWED_CONFIDENCE:
        errors.append("confidence_invalid")

    thesis = str(payload.get("thesis") or "").strip()
    if not thesis:
        errors.append("thesis_required")

    source_ids = payload.get("source_ids")
    known = {str(item).strip() for item in (known_source_ids or []) if str(item).strip()}
    if not isinstance(source_ids, list) or not source_ids:
        errors.append("source_ids_required")
    else:
        normalized_ids = [str(item).strip() for item in source_ids if str(item).strip()]
        if not normalized_ids:
            errors.append("source_ids_required")
        elif known and any(source_id not in known for source_id in normalized_ids):
            errors.append("source_ids_not_grounded")
        payload["source_ids"] = normalized_ids

    if bool(payload.get("stale_data")):
        errors.append("stale_data_forbidden")

    serialized = _serialize_for_policy_scan(payload)
    if _contains_forbidden_token(serialized, FORBIDDEN_BROKER_TOKENS):
        policy_violations.append("broker_endpoint_reference_forbidden")
    if _contains_forbidden_token(serialized, FORBIDDEN_POLICY_TOKENS):
        policy_violations.append("risk_policy_violation_detected")
    if _contains_forbidden_token(serialized, FORBIDDEN_TOOL_REQUEST_TOKENS):
        policy_violations.append("tool_use_request_forbidden")

    tool_request = payload.get("tool_request") or payload.get("requested_tools")
    if tool_request not in (None, "", [], {}):
        policy_violations.append("tool_use_request_forbidden")

    draft_intent = payload.get("draft_order_intent")
    if draft_intent is not None:
        draft_result = validateDraftOrderIntent(draft_intent, now_kst=now_kst)
        errors.extend(draft_result["errors"])
        policy_violations.extend(draft_result.get("policy_violations") or [])

    if policy_violations:
        errors.extend(policy_violations)

    validation_status = "rejected" if errors else "accepted"
    payload["validation_status"] = validation_status
    if policy_violations:
        payload["policy_violation"] = True

    return {
        "ok": not errors,
        "errors": errors,
        "policy_violations": policy_violations,
        "output": payload,
        "validation_status": validation_status,
        "entry_unlocked": False,
    }


def validateDraftOrderIntent(
    intent: Optional[Mapping[str, Any]],
    *,
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    payload = deepcopy(dict(intent or {}))
    errors: List[str] = []
    policy_violations: List[str] = []

    symbol = str(payload.get("symbol") or "").strip()
    if not symbol:
        errors.append("draft_intent_symbol_required")

    side = str(payload.get("side") or "").strip()
    if side not in ALLOWED_ORDER_SIDES:
        errors.append("draft_intent_side_invalid")

    risk_ref = str(payload.get("risk_reference_id") or payload.get("risk_ref") or "").strip()
    if not risk_ref:
        errors.append("draft_intent_risk_reference_required")

    price_type = str(payload.get("price_type") or payload.get("order_type") or "").strip()
    if price_type not in ALLOWED_PRICE_TYPES:
        errors.append("draft_intent_price_type_invalid")

    expires_at = _parse_kst_timestamp(
        payload.get("expires_at_kst"),
        "draft_intent_expires_at_kst",
        errors,
    )
    reference_now = _parse_kst_timestamp(now_kst, "now_kst", []) if now_kst else expires_at
    if expires_at and reference_now and expires_at < reference_now:
        errors.append("draft_intent_expired")

    if bool(payload.get("stale_data")) or bool(payload.get("stale_source_data")):
        errors.append("draft_intent_stale_source_forbidden")

    max_cash = payload.get("max_cash_krw")
    max_shares = payload.get("max_shares")
    if max_cash in (None, "") and max_shares in (None, ""):
        errors.append("draft_intent_size_required")

    all_in_flag = payload.get("all_in") or payload.get("all_in_sizing")
    if all_in_flag is True:
        policy_violations.append("all_in_sizing_forbidden")

    if payload.get("use_credit") is True or payload.get("use_margin") is True:
        policy_violations.append("credit_or_margin_forbidden")

    serialized = _serialize_for_policy_scan(payload)
    if _contains_forbidden_token(serialized, FORBIDDEN_BROKER_TOKENS):
        policy_violations.append("broker_endpoint_reference_forbidden")
    if _contains_forbidden_token(serialized, FORBIDDEN_POLICY_TOKENS):
        policy_violations.append("risk_policy_violation_detected")

    execution_route = str(payload.get("execution_route") or payload.get("broker_adapter") or "").strip()
    if execution_route and execution_route != NO_ORDER_DRY_RUN:
        if _contains_forbidden_token(execution_route, FORBIDDEN_BROKER_TOKENS):
            policy_violations.append("broker_endpoint_reference_forbidden")
        else:
            errors.append("draft_intent_execution_route_forbidden")

    if policy_violations:
        errors.extend(policy_violations)

    return {
        "ok": not errors,
        "errors": errors,
        "policy_violations": policy_violations,
        "intent": payload,
        "executable": False,
    }


def buildAiAuditRecord(
    job_id: str,
    output: Mapping[str, Any],
    validation_result: Mapping[str, Any],
    *,
    latency_ms: int = 0,
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    produced_at = now_kst or str(output.get("produced_at_kst") or "")
    if not produced_at:
        produced_at = _default_now_kst()

    return {
        "record_type": "ai_orchestration_audit/v0",
        "job_id": job_id,
        "model_role": output.get("model_role"),
        "model_name": output.get("model_name"),
        "prompt_schema_version": output.get("prompt_schema_version"),
        "input_bundle_ids": list(output.get("input_bundle_ids") or []),
        "source_ids": list(output.get("source_ids") or []),
        "action": output.get("action"),
        "validation_status": validation_result.get("validation_status")
        or ("accepted" if validation_result.get("ok") else "rejected"),
        "validation_errors": list(validation_result.get("errors") or []),
        "policy_violations": list(validation_result.get("policy_violations") or []),
        "latency_ms": int(latency_ms),
        "produced_at_kst": produced_at,
        "redaction_status": output.get("redaction_status", "none"),
        "entry_unlocked": False,
        "broker_call_allowed": False,
        "order_placement_allowed": False,
    }


def routeAiRecommendationThroughPolicyGate(
    output: Mapping[str, Any],
    *,
    entry_intent: Optional[Mapping[str, Any]] = None,
    known_source_ids: Optional[Sequence[str]] = None,
    now_kst: Optional[str] = None,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = dict(config or loadAiOrchestrationConfig())
    validation = validateAiRecommendation(
        output,
        known_source_ids=known_source_ids,
        now_kst=now_kst,
    )
    action = str(output.get("action") or "").strip()

    result: Dict[str, Any] = {
        "ok": False,
        "validation": validation,
        "policy_gate_result": "rejected",
        "entry_unlocked": False,
        "execution_mode": NO_ORDER_DRY_RUN,
        "broker_adapter": NO_ORDER_DRY_RUN,
        "dry_run_record": None,
        "blocked_reasons": list(validation.get("errors") or []),
    }

    if not validation.get("ok"):
        return result

    if action != "consider_entry":
        result.update(
            {
                "ok": True,
                "policy_gate_result": "recommendation_only",
                "blocked_reasons": [],
            }
        )
        return result

    intent_payload = deepcopy(dict(entry_intent or output.get("draft_order_intent") or {}))
    if not intent_payload:
        result["blocked_reasons"] = ["consider_entry_requires_entry_intent"]
        return result

    risk_validation = sr.validateEntryIntent(intent_payload, now_kst=now_kst)
    result["risk_validation"] = risk_validation
    if not risk_validation.get("ok"):
        result["blocked_reasons"] = list(risk_validation.get("errors") or [])
        return result

    dry_run_record = buildAiNoOrderDryRunDecisionRecord(
        output,
        intent_payload,
        risk_validation,
        now_kst=now_kst,
        config=cfg,
    )
    record_validation = validateAiNoOrderDryRunDecisionRecord(dry_run_record, config=cfg)
    result["dry_run_record"] = dry_run_record
    result["dry_run_validation"] = record_validation

    if not record_validation.get("ok"):
        result["blocked_reasons"] = list(record_validation.get("errors") or [])
        return result

    result.update(
        {
            "ok": True,
            "policy_gate_result": "approved_no_order_dry_run",
            "entry_unlocked": False,
            "blocked_reasons": [],
        }
    )
    return result


def buildAiNoOrderDryRunDecisionRecord(
    output: Mapping[str, Any],
    entry_intent: Mapping[str, Any],
    risk_validation: Mapping[str, Any],
    *,
    now_kst: Optional[str] = None,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = dict(config or loadAiOrchestrationConfig())
    produced_at = now_kst or _default_now_kst()
    rulebook_record = sr.buildNoOrderDryRunRecord(entry_intent, risk_validation, now_kst=produced_at)

    return {
        "record_type": "ai_orchestration_no_order_dry_run/v0",
        "module_id": cfg["module_id"],
        "job_id": output.get("job_id"),
        "recommendation_id": output.get("recommendation_id"),
        "candidate_id": output.get("candidate_id"),
        "symbol": output.get("symbol"),
        "action": output.get("action"),
        "decision": "approved_no_order_dry_run",
        "execution_mode": NO_ORDER_DRY_RUN,
        "broker_adapter": NO_ORDER_DRY_RUN,
        "kis_paper_approved": cfg.get("kis_paper_approved", False),
        "produced_at_kst": produced_at,
        "no_broker_call": True,
        "no_order_submission": True,
        "no_simulated_fill": True,
        "no_simulated_balance": True,
        "no_simulated_pnl": True,
        "no_paper_order": True,
        "no_live_order": True,
        "entry_unlocked": False,
        "rulebook_record": rulebook_record,
        "source_ids": list(output.get("source_ids") or []),
        "input_bundle_ids": list(output.get("input_bundle_ids") or []),
    }


def validateAiNoOrderDryRunDecisionRecord(
    record: Optional[Mapping[str, Any]],
    *,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = dict(config or loadAiOrchestrationConfig())
    payload = deepcopy(dict(record or {}))
    errors: List[str] = []

    required = (
        "record_type",
        "execution_mode",
        "broker_adapter",
        "no_broker_call",
        "no_order_submission",
        "no_simulated_fill",
        "no_simulated_balance",
        "entry_unlocked",
        "rulebook_record",
    )
    for key in required:
        if key not in payload:
            errors.append(f"missing_record_field:{key}")

    if payload.get("execution_mode") != NO_ORDER_DRY_RUN:
        errors.append("record_execution_mode_must_be_no_order_dry_run")
    if payload.get("broker_adapter") != NO_ORDER_DRY_RUN:
        errors.append("record_broker_adapter_must_be_no_order_dry_run")
    if payload.get("no_broker_call") is not True:
        errors.append("no_broker_call_must_be_true")
    if payload.get("no_order_submission") is not True:
        errors.append("no_order_submission_must_be_true")
    if payload.get("no_simulated_fill") is not True:
        errors.append("no_simulated_fill_must_be_true")
    if payload.get("no_simulated_balance") is not True:
        errors.append("no_simulated_balance_must_be_true")
    if payload.get("entry_unlocked") is not False:
        errors.append("entry_unlocked_must_remain_false")

    if cfg.get("kis_paper_approved") is not True:
        if payload.get("kis_paper_route_allowed") is True:
            errors.append("kis_paper_route_forbidden_before_approval")
        for field_name in (
            "broker_endpoint",
            "execution_route",
            "kis_endpoint",
            "order_router",
            "broker_adapter_hint",
        ):
            value = str(payload.get(field_name) or "").strip()
            if value and value != NO_ORDER_DRY_RUN:
                if _contains_forbidden_token(value, FORBIDDEN_BROKER_TOKENS):
                    errors.append("broker_endpoint_reference_forbidden")

    rulebook_record = payload.get("rulebook_record")
    if isinstance(rulebook_record, Mapping):
        rulebook_validation = sr.validateNoOrderDryRunRecord(rulebook_record)
        if not rulebook_validation.get("ok"):
            errors.extend(
                f"rulebook_record:{error}" for error in rulebook_validation.get("errors") or []
            )
    else:
        errors.append("rulebook_record_required")

    return {"ok": not errors, "errors": errors, "record": payload}


def buildAiFallbackReport(
    job_id: str,
    reason: str,
    *,
    now_kst: Optional[str] = None,
) -> Dict[str, Any]:
    produced_at = now_kst or _default_now_kst()
    fallback_reason = str(reason or "").strip() or "ai_unavailable"
    alternate_job_id = None
    if job_id == "gpt_morning_watchlist_0715":
        alternate_job_id = "deepseek_pro_hourly"

    return {
        "schema_version": "ai_fallback_report/v0",
        "job_id": job_id,
        "fallback_reason": fallback_reason,
        "produced_at_kst": produced_at,
        "entry_unlocked": False,
        "alternate_job_id": alternate_job_id,
        "morning_review_mode": "deepseek_only" if alternate_job_id else None,
        "validation_status": "fallback",
        "redaction_status": "none",
    }


def validateDailyCloseReport(
    report: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    payload = deepcopy(dict(report or {}))
    errors: List[str] = []

    if payload.get("schema_version") != "daily_close_report/v0":
        errors.append("schema_version_must_be_daily_close_report_v0")

    pnl = payload.get("pnl") if isinstance(payload.get("pnl"), Mapping) else {}
    for field_name in ("net_pnl_krw", "gross_pnl_krw", "fees_krw", "taxes_krw"):
        source = pnl.get(f"{field_name}_source") or pnl.get("calculation_source")
        if source != "system":
            errors.append(f"pnl_{field_name}_must_be_system_calculated")

    interpretation = str(payload.get("ai_interpretation") or "").strip()
    if not interpretation:
        errors.append("ai_interpretation_required")

    if payload.get("ai_calculated_pnl") is True:
        errors.append("ai_must_not_calculate_pnl")

    return {"ok": not errors, "errors": errors, "report": payload}


def simulateAiFailure(
    failure_type: str,
    *,
    job_id: str = "deepseek_pro_news_hourly",
) -> Dict[str, Any]:
    normalized = str(failure_type or "").strip().lower() or "unavailable"
    return {
        "job_id": job_id,
        "failure_type": normalized,
        "entry_unlocked": False,
        "validation_status": "rejected",
        "fallback_report": buildAiFallbackReport(job_id, normalized),
    }


def _validate_common_output_envelope(
    payload: Mapping[str, Any],
    errors: List[str],
    *,
    now_kst: Optional[str],
) -> None:
    required_fields = (
        "schema_version",
        "job_id",
        "model_role",
        "model_name",
        "prompt_schema_version",
        "input_bundle_ids",
        "produced_at_kst",
        "source_ids",
        "validation_status",
        "redaction_status",
    )
    for field_name in required_fields:
        if field_name not in payload:
            errors.append(f"missing_field:{field_name}")

    job_id = str(payload.get("job_id") or "").strip()
    if job_id and job_id not in JOB_REGISTRY:
        errors.append("job_id_unknown")

    input_bundle_ids = payload.get("input_bundle_ids")
    if not isinstance(input_bundle_ids, list) or not input_bundle_ids:
        errors.append("input_bundle_ids_required")

    _parse_kst_timestamp(payload.get("produced_at_kst"), "produced_at_kst", errors)
    if now_kst:
        _parse_kst_timestamp(now_kst, "now_kst", [])


def _compact_timestamp(value: str) -> str:
    raw = str(value or _default_now_kst()).strip()
    return (
        raw.replace("-", "")
        .replace(":", "")
        .replace("+0900", "")
        .replace("+09:00", "")
        .replace("T", "_")
    )


def _ten_minute_bucket_id(value: str) -> str:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    local = parsed.astimezone(KST)
    bucket_minute = (local.minute // 10) * 10
    bucket = local.replace(minute=bucket_minute, second=0, microsecond=0)
    return f"flash_10m_{bucket.strftime('%Y%m%d_%H%M')}"


def _symbol_set_from_snapshot(snapshot: Mapping[str, Any], key: str) -> Set[str]:
    rows = snapshot.get(key)
    symbols: Set[str] = set()
    if isinstance(rows, Mapping):
        iterable = rows.values()
    elif isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        iterable = rows
    else:
        iterable = []
    for row in iterable:
        if isinstance(row, Mapping):
            symbol = str(row.get("symbol") or row.get("ticker") or "").strip()
        else:
            symbol = str(row or "").strip()
        if symbol:
            symbols.add(symbol)
    return symbols


def _active_symbols_from_trade_documents(documents: Sequence[Mapping[str, Any]], *, now_kst: Optional[str] = None) -> Set[str]:
    symbols: Set[str] = set()
    errors: List[str] = []
    reference_now = _parse_kst_timestamp(now_kst, "now_kst", errors) if now_kst else None
    for document in documents:
        valid_state = str(document.get("document_state") or document.get("status") or "active").lower()
        if valid_state in {"expired", "cancelled", "closed"}:
            continue
        valid_until_raw = document.get("valid_until") or document.get("valid_until_kst")
        if reference_now and valid_until_raw:
            expiry_errors: List[str] = []
            expiry = _parse_kst_timestamp(valid_until_raw, "valid_until_kst", expiry_errors)
            if expiry and expiry <= reference_now:
                continue
        for action in document.get("actions") or []:
            if not isinstance(action, Mapping):
                continue
            if str(action.get("action") or "").strip() in {
                "WAIT_BUY",
                "BUY_NOW",
                "HOLD",
                "NO_NEW_ENTRY",
                "HOLD_EXISTING_POSITION",
                "WAIT_ORDER_RECONCILIATION",
            }:
                symbol = str(action.get("ticker") or action.get("symbol") or "").strip()
                if symbol:
                    symbols.add(symbol)
    return symbols


def _normalize_flash_provider_action_sources(
    provider_actions: Optional[Sequence[Mapping[str, Any]]],
    watch_by_symbol: Mapping[str, Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for provider_action in provider_actions or []:
        if not isinstance(provider_action, Mapping):
            continue
        symbol = str(provider_action.get("symbol") or provider_action.get("ticker") or "").strip()
        if not symbol or symbol in seen:
            continue
        watch_row = watch_by_symbol.get(symbol)
        if not watch_row:
            continue
        action_type = _normalize_flash_action_type(provider_action.get("action") or provider_action.get("stance"))
        if not action_type:
            continue
        rows.append(
            {
                "row": deepcopy(dict(watch_row)),
                "provider": deepcopy(dict(provider_action)),
                "action_source": "deepseek_flash_provider",
            }
        )
        seen.add(symbol)
        if len(rows) >= 5:
            break
    return rows


def _normalize_flash_action_type(value: Any) -> str:
    raw = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "BUY": "BUY_NOW",
        "ENTRY": "WAIT_BUY",
        "WAIT": "WAIT_BUY",
        "WATCH": "HOLD",
        "WATCH_ONLY": "HOLD",
        "SELL": "SELL_NOW",
        "EXIT": "SELL_NOW",
        "WAIT_SELL": "WAIT_SELL",
        "AVOID": "NO_TRADE",
        "REJECT": "NO_TRADE",
        "NO_NEW_ENTRY": "NO_NEW_ENTRY",
        "HOLD_EXISTING": "HOLD_EXISTING_POSITION",
        "HOLD_EXISTING_POSITION": "HOLD_EXISTING_POSITION",
        "WAIT_RECONCILIATION": "WAIT_ORDER_RECONCILIATION",
        "WAIT_ORDER_RECONCILIATION": "WAIT_ORDER_RECONCILIATION",
        "EXIT_REVIEW": "EXIT_REVIEW",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in FLASH_ACTION_TYPES else ""


def _normalize_price_list(value: Any) -> List[int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    prices: List[int] = []
    for item in value:
        parsed = _safe_positive_int(item)
        if parsed > 0:
            prices.append(parsed)
    return prices[:2]


def _safe_positive_int(value: Any) -> int:
    if value is None or isinstance(value, bool):
        return 0
    raw = (
        str(value)
        .strip()
        .replace(",", "")
        .replace("₩", "")
        .replace("원", "")
        .strip()
    )
    if not raw:
        return 0
    try:
        number = Decimal(raw)
    except (InvalidOperation, ValueError):
        return 0
    if not number.is_finite() or number <= 0:
        return 0
    return int(number)


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _first_flash_morning_watchlist_warnings(
    morning_watchlist: Mapping[str, Any],
    produced_dt: datetime,
) -> List[str]:
    warnings: List[str] = []
    if morning_watchlist.get("requires_monday_refresh") is True:
        warnings.append("monday_final_morning_watchlist_refresh_recommended")

    purpose = str(morning_watchlist.get("purpose") or "").strip().lower()
    if purpose in {
        "monday_preopen_rehearsal",
        "monday_preopen_rehearsal_late",
        "monday_preopen_candidate_watchlist",
    } or "rehearsal" in purpose:
        warnings.append("morning_watchlist_is_rehearsal_or_candidate")

    produced_day = produced_dt.astimezone(KST).date().isoformat()
    target_day = str(
        morning_watchlist.get("target_trade_date_kst")
        or morning_watchlist.get("trading_date_kst")
        or morning_watchlist.get("trading_date")
        or ""
    ).strip()
    if target_day and target_day != produced_day:
        warnings.append("morning_watchlist_target_trade_date_mismatch")

    generated_raw = (
        morning_watchlist.get("generated_at_kst")
        or morning_watchlist.get("produced_at_kst")
        or morning_watchlist.get("created_at_kst")
    )
    if generated_raw:
        generated_errors: List[str] = []
        generated_dt = _parse_kst_timestamp(
            generated_raw,
            "morning_watchlist_generated_at_kst",
            generated_errors,
        )
        if generated_dt and generated_dt.astimezone(KST).date() < produced_dt.astimezone(KST).date():
            warnings.append("morning_watchlist_generated_before_trade_date")

    return sorted(set(warnings))


def _parse_kst_timestamp(value: Any, label: str, errors: List[str]) -> Optional[datetime]:
    if value in (None, ""):
        if label.endswith("_required") or "required" in label:
            errors.append(f"{label}_required")
        else:
            errors.append(f"{label}_required")
        return None
    raw = str(value).strip()
    if not TIMESTAMP_PATTERN.match(raw):
        errors.append(f"{label}_must_be_kst_iso")
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        errors.append(f"{label}_must_be_kst_iso")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != KST.utcoffset(None):
        errors.append(f"{label}_must_be_kst_iso")
        return None
    return parsed


def _default_now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def _serialize_for_policy_scan(value: Any) -> str:
    if isinstance(value, Mapping):
        parts = [f"{key}={child}" for key, child in value.items()]
        return " ".join(parts).lower()
    if isinstance(value, list):
        return " ".join(str(item) for item in value).lower()
    return str(value).lower()


def _contains_forbidden_token(value: str, tokens: Sequence[str]) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in tokens)


def _flatten_key_values(value: Any, prefix: str = "") -> List[tuple[str, Any]]:
    items: List[tuple[str, Any]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_key = str(key)
            dotted = child_key if not prefix else f"{prefix}.{child_key}"
            items.extend(_flatten_key_values(child, dotted))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            dotted = f"{prefix}[{index}]"
            items.extend(_flatten_key_values(child, dotted))
    else:
        items.append((prefix, value))
    return items


def _is_sensitive_payload_key(key: str) -> bool:
    lowered_key = str(key or "").lower()
    if not lowered_key:
        return False
    if lowered_key in SENSITIVE_PAYLOAD_KEYS or any(
        fragment in lowered_key for fragment in SENSITIVE_PAYLOAD_FRAGMENTS
    ):
        return True
    segments = lowered_key.split(".")
    if "account" in segments and any(
        segment in ("id", "no", "number", "account_no", "account_id") for segment in segments
    ):
        return True
    if any(segment in ("credentials", "credential") for segment in segments):
        if any(
            fragment in lowered_key
            for fragment in ("api_key", "api_secret", "app_key", "app_secret", "password", "token", "secret")
        ):
            return True
    return False
