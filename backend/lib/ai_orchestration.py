"""
HWISTOCK-UNIT-005 foundation: deterministic local AI orchestration helpers.

Stdlib-only; no network, broker, KIS, or AI provider calls. AI outputs are
recommendation-only and must pass schema validation and deterministic policy gates
before any no-order dry-run record is produced.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

try:
    from lib import strategy_risk as sr
except ImportError:  # pragma: no cover - package-style imports
    from backend.lib import strategy_risk as sr

KST = timezone(timedelta(hours=9))

AI_RECOMMENDATION_SCHEMA = "ai_recommendation/v0"
NO_ORDER_DRY_RUN = "no_order_dry_run"

ALLOWED_ACTIONS = frozenset(
    {"watch", "reject", "consider_entry", "hold_review", "exit_review"}
)
ALLOWED_CONFIDENCE = frozenset({"low", "medium", "high"})
ALLOWED_SOURCE_PATHS = frozenset({"event_first", "chart_first", "combined"})
ALLOWED_CHART_INTERVALS = frozenset({"1m", "3m", "5m"})
ALLOWED_ORDER_SIDES = frozenset({"buy", "sell"})
ALLOWED_PRICE_TYPES = frozenset({"limit", "market"})

JOB_REGISTRY: Dict[str, Dict[str, Any]] = {
    "deepseek_pro_news_hourly": {
        "schedule": "hourly, 24h",
        "model_role": "deepseek_pro",
        "input_schema": "intel_delta_bundle/v0",
        "output_schema": "hourly_intel_analysis/v0",
        "soft_latency_seconds": 600,
        "hard_latency_seconds": 1200,
        "tool_use_enabled": False,
    },
    "deepseek_pro_market_regime": {
        "schedule": "hourly, 08:00-19:00 KST",
        "model_role": "deepseek_pro",
        "input_schema": "market_regime_bundle/v0",
        "output_schema": "market_regime_report/v0",
        "soft_latency_seconds": 600,
        "hard_latency_seconds": 1200,
        "tool_use_enabled": False,
    },
    "deepseek_flash_intraday_label": {
        "schedule": "event-triggered, 08:00-20:00 KST",
        "model_role": "deepseek_flash",
        "input_schema": "candidate_context_bundle/v0",
        "output_schema": "intraday_candidate_label/v0",
        "soft_latency_seconds": 15,
        "hard_latency_seconds": 30,
        "tool_use_enabled": False,
    },
    "gpt_prompt_0650": {
        "schedule": "06:50 KST",
        "model_role": "local_orchestrator",
        "input_schema": "overnight_analysis_bundle/v0",
        "output_schema": "gpt_morning_prompt/v0",
        "hard_cutoff_kst": "07:00",
        "tool_use_enabled": False,
    },
    "chatgpt_pro_morning_review": {
        "schedule": "07:00 KST",
        "model_role": "chatgpt_pro_browser",
        "input_schema": "gpt_morning_prompt/v0",
        "output_schema": "morning_review_report/v0",
        "hard_cutoff_kst": "07:20",
        "tool_use_enabled": False,
    },
    "daily_close_2000": {
        "schedule": "20:00 KST",
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
        "GPT_PRO_MORNING_REVIEW_CUTOFF_KST": "07:20",
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
    if payload.get("GPT_PRO_MORNING_REVIEW_CUTOFF_KST") != "07:20":
        errors.append("gpt_pro_morning_review_cutoff_must_be_0720")
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
    if job_id == "chatgpt_pro_morning_review":
        alternate_job_id = "gpt_prompt_0650"

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
