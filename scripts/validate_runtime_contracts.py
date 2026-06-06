#!/usr/bin/env python3
"""
Validate HWISTOCK-UNIT-016 runtime contract catalog and fixtures.

This validator is intentionally stdlib-only because the current repo toolchain
does not include the external jsonschema package. It validates the subset of
the contract catalog required for the Set gate: required fields, primitive
types, const/enum/pattern/min/max, KST timestamps, nested array item specs,
Flash action caps, paper-only broker guards, cancel-target refs, legal executor
state transitions, freshness gates, deterministic sizing bounds, duplicate
ids, and obvious secret-like key/value leaks.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs/contracts/hwistock-runtime-contracts.schema.json"
VALID_FIXTURE_PATH = ROOT / "docs/contracts/fixtures/runtime-contract-valid.json"
INVALID_FIXTURE_PATH = ROOT / "docs/contracts/fixtures/runtime-contract-invalid.json"

KST_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+09:00$")
ALLOWED_FLASH_ACTIONS = {"WAIT_BUY", "BUY_NOW", "HOLD", "SELL", "NO_TRADE"}

SECRET_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|app[_-]?key|secret|password|passwd|token|credential|"
    r"account[_-]?(no|number|id)|acct[_-]?(no|number|id)|appsecret)"
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(appsecret|appkey|access_token|authorization:|bearer\s+[a-z0-9._-]+|"
    r"kis_live_prod_url|real_account)"
)
SECRET_KEY_ALLOWLIST = {
    "account_alias",
    "paper_account_alias",
    "client_order_key",
    "matched_client_order_key",
    "raw_secret_redacted",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_kst(value: Any) -> datetime | None:
    if not isinstance(value, str) or not KST_TS.match(value):
        return None
    return datetime.fromisoformat(value)


def type_ok(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return True


def validate_field(name: str, value: Any, spec: Mapping[str, Any], errors: list[str]) -> None:
    expected_type = spec.get("type")
    if expected_type and not type_ok(value, expected_type):
        errors.append(f"{name}_type_{expected_type}")
        return

    if "const" in spec and value != spec["const"]:
        const_text = str(spec["const"]).lower()
        errors.append(f"{name}_const_{const_text}")

    enum = spec.get("enum")
    if enum is not None and value not in enum:
        errors.append(f"{name}_enum_invalid")

    pattern = spec.get("pattern")
    if pattern and isinstance(value, str) and not re.match(pattern, value):
        errors.append(f"{name}_pattern_invalid")

    if spec.get("format") == "kst_datetime" and parse_kst(value) is None:
        errors.append(f"{name}_kst_datetime_invalid")

    if isinstance(value, (int, float)) and "minimum" in spec and value < spec["minimum"]:
        errors.append(f"{name}_minimum_{spec['minimum']}")
    if isinstance(value, (int, float)) and "maximum" in spec and value > spec["maximum"]:
        errors.append(f"{name}_maximum_{spec['maximum']}")

    if isinstance(value, list):
        min_items = spec.get("min_items")
        if min_items is not None and len(value) < min_items:
            errors.append(f"{name}_min_items_{min_items}")
        max_items = spec.get("max_items")
        if max_items is not None and len(value) > max_items:
            errors.append(f"{name}_max_items_{max_items}")
        item_required = spec.get("item_required_fields") or []
        item_fields = spec.get("item_fields") or {}
        if item_required:
            for index, item in enumerate(value):
                if not isinstance(item, Mapping):
                    errors.append(f"{name}_item_{index}_not_object")
                    continue
                for field in item_required:
                    if field not in item:
                        errors.append(f"{name}_item_{index}_{field}_required")
        if item_fields:
            for index, item in enumerate(value):
                if not isinstance(item, Mapping):
                    errors.append(f"{name}_item_{index}_not_object")
                    continue
                for child_name, child_spec in item_fields.items():
                    if child_name in item:
                        validate_field(f"{name}_item_{index}.{child_name}", item[child_name], child_spec, errors)

    if isinstance(value, Mapping):
        for field in spec.get("required_fields") or []:
            if field not in value:
                errors.append(f"{name}.{field}_required")
        for child_name, child_spec in (spec.get("fields") or {}).items():
            if child_name in value:
                validate_field(f"{name}.{child_name}", value[child_name], child_spec, errors)


def find_secretish_values(value: Any, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            if key not in SECRET_KEY_ALLOWLIST and SECRET_KEY_RE.search(str(key)):
                errors.append(f"secret_key_like:{key_path}")
            errors.extend(find_secretish_values(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(find_secretish_values(child, f"{path}[{index}]"))
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        errors.append(f"secret_value_like:{path}")
    return errors


def unavailable_ref(value: Any) -> bool:
    return not isinstance(value, str) or value == "" or value.startswith("unavailable:")


def has_unavailable_refs(values: Any) -> bool:
    if not isinstance(values, list):
        return True
    return any(unavailable_ref(value) for value in values)


def ref_has_prefix(value: Any, prefixes: tuple[str, ...]) -> bool:
    return isinstance(value, str) and any(value.startswith(prefix) for prefix in prefixes)


def refs_have_allowed_prefixes(values: Any, prefixes: tuple[str, ...]) -> bool:
    if has_unavailable_refs(values):
        return False
    return all(ref_has_prefix(value, prefixes) for value in values)


def validate_paper_order_intent_refs(artifact: Mapping[str, Any], errors: list[str]) -> None:
    source_refs = artifact.get("source_refs")
    market_data_refs = artifact.get("market_data_refs")
    flash_ref = artifact.get("flash_trade_document_ref")
    portfolio_ref = artifact.get("portfolio_snapshot_ref")
    order_state_ref = artifact.get("order_state_snapshot_ref")
    input_refs = artifact.get("input_refs")

    missing_or_weak = (
        not ref_has_prefix(flash_ref, ("art_flash_",))
        or not refs_have_allowed_prefixes(
            source_refs,
            ("art_news_", "art_disclosure_", "art_market_notice_", "art_source_"),
        )
        or not refs_have_allowed_prefixes(market_data_refs, ("art_kis_snapshot_", "art_market_"))
        or not ref_has_prefix(portfolio_ref, ("art_portfolio_",))
        or not ref_has_prefix(order_state_ref, ("art_order_state_",))
        or parse_kst(artifact.get("authoritative_refs_verified_at_kst")) is None
        or has_unavailable_refs(input_refs)
    )
    if not missing_or_weak and isinstance(input_refs, list):
        required_input_refs = [flash_ref, portfolio_ref, order_state_ref]
        required_input_refs.extend(source_refs)
        required_input_refs.extend(market_data_refs)
        if any(ref not in input_refs for ref in required_input_refs):
            missing_or_weak = True

    if missing_or_weak:
        errors.append("paper_order_intent_authoritative_refs_missing")


def require_fields(prefix: str, value: Mapping[str, Any], fields: list[str], errors: list[str]) -> None:
    for field in fields:
        if field not in value:
            errors.append(f"{prefix}{field}_required")


def validate_paper_guard(artifact: Mapping[str, Any], errors: list[str]) -> None:
    guard = artifact.get("paper_only_guard") or {}
    required_values = {
        "environment_label": "PAPER_ONLY",
        "paper_account_alias": None,
        "account_alias_redacted": True,
        "krx_only": True,
        "tr_id_allowed": True,
        "tr_id_allowlist_version": None,
        "startup_self_test_passed": True,
        "broker_adapter_alias": "kis_paper",
        "base_url_alias": "kis_paper_vts",
        "resolved_rest_base_url_alias": "kis_paper_vts",
        "resolved_rest_host_class": "kis_paper",
        "resolved_websocket_host_class": "kis_paper",
        "live_domain_detected": False,
        "unknown_domain_detected": False,
    }
    for field, expected in required_values.items():
        if field not in guard:
            errors.append(f"paper_only_guard.{field}_required")
            continue
        if expected is not None and guard.get(field) != expected:
            errors.append("paper_only_guard_failed")
    if not isinstance(guard.get("paper_account_alias"), str) or not guard["paper_account_alias"].startswith("paper_account_alias:"):
        errors.append("paper_only_guard_failed")


def validate_quantity_rule(artifact: Mapping[str, Any], errors: list[str]) -> None:
    rule = artifact.get("quantity_rule")
    if not isinstance(rule, Mapping):
        return
    required_numbers = [
        "risk_overlay_capital_krw",
        "minimum_cash_reserve_ratio",
        "available_cash_before_order",
        "reserved_cash_before_order",
        "max_order_cash_krw",
        "limit_price_krw",
    ]
    if any(not isinstance(rule.get(field), (int, float)) or isinstance(rule.get(field), bool) for field in required_numbers):
        return
    computed_quantity = rule.get("computed_quantity")
    lot_size = rule.get("lot_size", 1)
    if not isinstance(computed_quantity, int) or isinstance(computed_quantity, bool) or computed_quantity < 1:
        errors.append("quantity_rule_computed_quantity_invalid")
        return
    if not isinstance(lot_size, int) or isinstance(lot_size, bool) or lot_size < 1:
        errors.append("quantity_rule_lot_size_invalid")
        return
    if computed_quantity % lot_size != 0:
        errors.append("quantity_rule_lot_rounding_invalid")
    dynamic_fields = [
        "current_position_value_krw",
        "pending_buy_notional_krw",
        "new_order_notional_krw",
        "effective_total_deposit_krw",
        "max_cash_deployment_ratio",
        "max_deployable_notional_krw",
        "projected_deployed_notional_krw",
    ]
    if any(field in rule for field in dynamic_fields):
        if any(
            not isinstance(rule.get(field), (int, float)) or isinstance(rule.get(field), bool)
            for field in dynamic_fields
        ):
            errors.append("quantity_rule_dynamic_exposure_fields_required")
            return
        current_position = float(rule["current_position_value_krw"])
        pending_buy = float(rule["pending_buy_notional_krw"])
        new_order = float(rule["new_order_notional_krw"])
        effective_total = float(rule["effective_total_deposit_krw"])
        deployment_ratio = float(rule["max_cash_deployment_ratio"])
        expected_cap = min(float(rule["risk_overlay_capital_krw"]), effective_total) * deployment_ratio
        projected = current_position + pending_buy + new_order
        if abs(float(rule["max_deployable_notional_krw"]) - expected_cap) > 1:
            errors.append("quantity_rule_dynamic_exposure_cap_mismatch")
        if abs(float(rule["projected_deployed_notional_krw"]) - projected) > 1:
            errors.append("quantity_rule_dynamic_exposure_projection_mismatch")
        if projected > expected_cap:
            errors.append("quantity_rule_dynamic_exposure_breach")
    risk_capital = float(rule["risk_overlay_capital_krw"])
    reserve_ratio = float(rule["minimum_cash_reserve_ratio"])
    already_reserved = float(rule["reserved_cash_before_order"])
    max_order_cash = float(rule["max_order_cash_krw"])
    order_cash = computed_quantity * float(rule["limit_price_krw"])
    allowed_cash = max(0.0, risk_capital * (1.0 - reserve_ratio) - already_reserved)
    if max_order_cash > allowed_cash or order_cash > max_order_cash:
        errors.append("quantity_rule_reserve_breach")
    if artifact.get("max_cash_krw") != rule.get("max_order_cash_krw"):
        errors.append("quantity_rule_max_cash_mismatch")


def validate_collection(artifacts: list[Mapping[str, Any]], catalog: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    seen_artifacts: set[str] = set()
    seen_trade_docs: set[str] = set()
    seen_intents: set[str] = set()
    seen_client_keys: set[str] = set()
    seen_snapshots: set[tuple[Any, Any, Any]] = set()
    for index, artifact in enumerate(artifacts):
        errors.extend(f"item_{index}:{error}" for error in validate_artifact(artifact, catalog))
        artifact_id = artifact.get("artifact_id")
        if artifact_id in seen_artifacts:
            errors.append("duplicate_artifact_id")
        seen_artifacts.add(str(artifact_id))
        trade_doc_id = artifact.get("trade_doc_id")
        if trade_doc_id:
            if trade_doc_id in seen_trade_docs:
                errors.append("duplicate_trade_doc_id")
            seen_trade_docs.add(str(trade_doc_id))
        intent_id = artifact.get("intent_id")
        if intent_id:
            if intent_id in seen_intents:
                errors.append("duplicate_intent_id")
            seen_intents.add(str(intent_id))
        client_key = artifact.get("client_order_key")
        if client_key:
            if client_key in seen_client_keys:
                errors.append("duplicate_client_order_key")
            seen_client_keys.add(str(client_key))
        if artifact.get("schema_version") == "kis_market_snapshot/v0":
            seq_key = (artifact.get("endpoint_family"), artifact.get("snapshot_kind"), artifact.get("sequence_no"))
            if seq_key in seen_snapshots:
                errors.append("duplicate_kis_snapshot_sequence")
            seen_snapshots.add(seq_key)
    return errors


def validate_artifact(artifact: Mapping[str, Any], catalog: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    schema_version = artifact.get("schema_version")
    schema = (catalog.get("schemas") or {}).get(schema_version)
    if schema is None:
        return [f"schema_unknown:{schema_version}"]

    required = list(catalog.get("common_required_fields") or []) + list(schema.get("required_fields") or [])
    for field in required:
        if field not in artifact:
            errors.append(f"{field}_required")

    expected_artifact_type = schema.get("artifact_type")
    if artifact.get("artifact_type") != expected_artifact_type:
        errors.append(f"artifact_type_must_be_{expected_artifact_type}")

    field_specs = dict(catalog.get("common_field_specs") or {})
    field_specs.update(schema.get("fields") or {})
    for field, spec in field_specs.items():
        if field in artifact:
            validate_field(field, artifact[field], spec, errors)

    created_at = parse_kst(artifact.get("created_at_kst"))
    valid_until = parse_kst(artifact.get("valid_until"))
    collected_at = parse_kst(artifact.get("collected_at_kst"))
    if created_at and valid_until and valid_until <= created_at:
        errors.append("valid_until_must_be_after_created_at_kst")
    if collected_at and valid_until and collected_at > valid_until:
        errors.append("collected_at_after_valid_until")

    if schema_version == "flash_trade_document/v0":
        actions = artifact.get("actions")
        if isinstance(actions, list):
            for index, action in enumerate(actions):
                if not isinstance(action, Mapping):
                    continue
                if action.get("executable_intent_allowed") is not False:
                    errors.append(f"actions_item_{index}_executable_intent_allowed_const_false")
                if action.get("action") not in ALLOWED_FLASH_ACTIONS:
                    errors.append(f"actions_item_{index}_action_invalid")
                if action.get("action") in {"WAIT_BUY", "BUY_NOW"}:
                    if has_unavailable_refs(action.get("source_refs")) or has_unavailable_refs(action.get("market_data_refs")):
                        errors.append(f"actions_item_{index}_source_or_market_refs_missing")
                    state_refs = action.get("portfolio_state_refs")
                    if (
                        has_unavailable_refs(state_refs)
                        or not any(str(ref).startswith("art_portfolio_") for ref in state_refs)
                        or not any(str(ref).startswith("art_order_state_") for ref in state_refs)
                    ):
                        errors.append(f"actions_item_{index}_portfolio_state_refs_missing_authoritative_context")
        if artifact.get("document_kind") == "NO_TRADE" and actions:
            errors.append("no_trade_must_not_have_actions")
        if artifact.get("document_kind") == "NO_TRADE" and not artifact.get("no_trade_reason"):
            errors.append("no_trade_reason_required")
        if artifact.get("document_kind") == "TRADE_ACTIONS":
            if artifact.get("pro_manifest_status") != "latest_complete":
                errors.append("pro_manifest_not_latest_complete")
            if unavailable_ref(artifact.get("portfolio_snapshot_ref")) or unavailable_ref(artifact.get("order_state_snapshot_ref")):
                errors.append("trade_actions_require_authoritative_portfolio_and_order_refs")
            if not actions:
                errors.append("trade_actions_require_actions")

    if schema_version == "kis_market_snapshot/v0":
        freshness = artifact.get("freshness") or {}
        if freshness.get("is_fresh") is not True:
            errors.append("snapshot_freshness_failed")

    if schema_version == "portfolio_snapshot/v0":
        freshness = artifact.get("freshness") or {}
        if artifact.get("authoritative_for_executor") is not True or freshness.get("is_fresh") is not True:
            errors.append("portfolio_freshness_failed")

    if schema_version == "order_state_snapshot/v0":
        freshness = artifact.get("freshness") or {}
        if artifact.get("authoritative_for_executor") is not True or freshness.get("is_fresh") is not True:
            errors.append("order_state_freshness_failed")

    if schema_version == "paper_order_intent/v0":
        validate_paper_order_intent_refs(artifact, errors)
        validate_quantity_rule(artifact, errors)

    if schema_version == "executor_decision/v0":
        from_state = artifact.get("from_state")
        to_state = artifact.get("to_state")
        allowed = (catalog.get("order_state_machine") or {}).get(from_state)
        if allowed is None or to_state not in allowed:
            errors.append(f"illegal_state_transition:{from_state}->{to_state}")

    if schema_version == "broker_order_request/v0":
        validate_paper_guard(artifact, errors)
        if (
            artifact.get("broker_adapter") != "kis_paper"
            or artifact.get("base_url_alias") != "kis_paper_vts"
            or artifact.get("route") != "KRX"
        ):
            errors.append("paper_only_guard_failed")
        if artifact.get("side") == "cancel":
            require_fields(
                "",
                artifact,
                [
                    "cancel_target_request_id",
                    "cancel_target_client_order_key",
                    "cancel_target_broker_order_id_alias",
                    "cancel_reason",
                    "superseding_trade_doc_id",
                    "cancel_deadline_kst",
                ],
                errors,
            )

    if schema_version == "broker_order_result/v0":
        if artifact.get("broker_status") in {"timeout", "unknown"} and artifact.get("reconciliation_required") is not True:
            errors.append("submit_unknown_requires_reconciliation")

    errors.extend(find_secretish_values(artifact))
    return errors


def main() -> int:
    catalog = load_json(CATALOG_PATH)
    valid_fixture = load_json(VALID_FIXTURE_PATH)
    invalid_fixture = load_json(INVALID_FIXTURE_PATH)

    failures: list[str] = []
    seen_artifact_ids: set[str] = set()
    valid_count = 0

    for artifact in valid_fixture.get("valid_artifacts", []):
        valid_count += 1
        artifact_id = artifact.get("artifact_id")
        if artifact_id in seen_artifact_ids:
            failures.append(f"valid:{artifact_id}:duplicate_artifact_id")
        seen_artifact_ids.add(artifact_id)

        errors = validate_artifact(artifact, catalog)
        if errors:
            failures.append(f"valid:{artifact_id}:{','.join(errors)}")

    invalid_count = 0
    for case in invalid_fixture.get("invalid_cases", []):
        invalid_count += 1
        name = case.get("name", "<unnamed>")
        expected = str(case.get("expected_error_contains") or "")
        if "artifacts" in case:
            errors = validate_collection(case.get("artifacts") or [], catalog)
        else:
            errors = validate_artifact(case.get("artifact") or {}, catalog)
        joined = ",".join(errors)
        if not errors:
            failures.append(f"invalid:{name}:unexpected_pass")
        elif expected and expected not in joined:
            failures.append(f"invalid:{name}:expected_{expected}:got_{joined}")

    if failures:
        print("runtime_contract_validation=FAIL")
        for failure in failures:
            print(failure)
        return 1

    print("runtime_contract_validation=PASS")
    print(f"valid_artifacts={valid_count}")
    print(f"invalid_cases={invalid_count}")
    print(f"schema_count={len(catalog.get('schemas') or {})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
