#!/usr/bin/env python3
"""
Validate HWISTOCK-UNIT-016 runtime contract catalog and fixtures.

This validator is intentionally stdlib-only because the current repo toolchain
does not include the external jsonschema package. It validates the subset of
the contract catalog required for the Set gate: required fields, primitive
    types, const/enum/pattern/min/max, KST timestamps, Flash action caps,
paper-only broker guards, legal executor state transitions, duplicate artifact
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
        if item_required:
            for index, item in enumerate(value):
                if not isinstance(item, Mapping):
                    errors.append(f"{name}_item_{index}_not_object")
                    continue
                for field in item_required:
                    if field not in item:
                        errors.append(f"{name}_item_{index}_{field}_required")

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
        if artifact.get("document_kind") == "NO_TRADE" and actions:
            errors.append("no_trade_must_not_have_actions")

    if schema_version == "executor_decision/v0":
        from_state = artifact.get("from_state")
        to_state = artifact.get("to_state")
        allowed = (catalog.get("order_state_machine") or {}).get(from_state)
        if allowed is None or to_state not in allowed:
            errors.append(f"illegal_state_transition:{from_state}->{to_state}")

    if schema_version == "broker_order_request/v0":
        guard = artifact.get("paper_only_guard") or {}
        if (
            artifact.get("broker_adapter") != "kis_paper"
            or artifact.get("base_url_alias") != "kis_paper_vts"
            or artifact.get("route") != "KRX"
            or guard.get("environment_label") != "PAPER_ONLY"
            or guard.get("krx_only") is not True
            or guard.get("tr_id_allowed") is not True
            or guard.get("startup_self_test_passed") is not True
        ):
            errors.append("paper_only_guard_failed")

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
