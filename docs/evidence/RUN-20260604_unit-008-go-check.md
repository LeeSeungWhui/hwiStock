---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-008-go-check
stage: check
unit_id: HWISTOCK-UNIT-008
status: superseded_by_mywebtemplate_code_import
current_authority: false
superseded_by_rebaseline_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
superseded_reason: MyWebTemplate backend/frontend-web import removed the validated UNIT-008 implementation files from the current tree.
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md
module_refs:
  - docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md
preflight_ref: docs/evidence/RUN-20260604_unit-008-go-preflight.md
created_at: 2026-06-04
---

# UNIT-008 Go-Check Evidence

> Superseded notice: this evidence is historical after the 2026-06-04
> MyWebTemplate backend/frontend-web code import. It no longer proves the
> current tree because the referenced UNIT-008 implementation files are missing.

## 1. Verdict

PASS. `HWISTOCK-UNIT-008` completed Go-Check for the local storage skeleton
scope.

This result does not authorize live DB migration execution, broker/KIS network
calls, AI provider calls, paper orders, live orders, credential storage,
dashboard UI, runtime `data/` artifact commits, or operational trading
readiness.

## 2. Go Changes

- Added backend package skeleton:
  - `backend/__init__.py`
  - `backend/router/__init__.py`
  - `backend/service/__init__.py`
  - `backend/query/__init__.py`
  - `backend/lib/__init__.py`
- Added storage contract helpers:
  - `backend/lib/storage_schemas.py`
  - `backend/lib/request_payload.py`
- Added Alembic migration skeleton:
  - `backend/migrations/README.md`
  - `backend/migrations/env.py`
  - `backend/migrations/script.py.mako`
  - `backend/migrations/versions/20260604_0001_create_hwistock_core_storage.py`
- Added focused tests:
  - `backend/tests/__init__.py`
  - `backend/tests/test_storage_contract.py`
- Updated UNIT-008, MOD-007, QA-008, profile, and index docs with Go-Check state
  and evidence references.

## 3. Check Review

| finding_id | priority | status | note |
| --- | --- | --- | --- |
| none | none | pass | No open P0/P1/P2 findings remain for UNIT-008 bounded storage skeleton scope. |

## 4. QA Row Results

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | Unit/module and `backend/migrations/` select PostgreSQL plus date-partitioned artifacts; SQLite is not in scope. |
| QA-002 | pass | Migration/env/profile use database `hwistock`, schema `hwistock_core`, and env var `HWISTOCK_DATABASE_URL`; no MyWebTemplate names are used. |
| QA-003 | pass | Unit/module and `buildArtifactPath` keep raw, normalized, AI, candidate, reports, trading, and evidence paths separated under ignored `data/`. |
| QA-004 | pass | `backend/lib/storage_schemas.py` defines common artifact fields and validation for ids, KST timestamps, environment, source/related links, redaction, and hashes. |
| QA-005 | pass | `DailyPnL` contract and tests require `calculation_source: system`; AI-calculated PnL is rejected. |
| QA-006 | pass | `PaperDayEvidenceManifest` validation requires links across source, AI, candidate, trading, PnL, morning report, and daily close artifacts. |
| QA-007 | pass | Sensitive-key validation exists; exact known KIS secret marker scan over docs/AGENTS/.gitignore/backend found no leak. |
| QA-008 | pass | Migration tables include artifact id/path/hash, KST creation time, trading date, and environment fields for derived rows. |
| QA-009 | pass | `SourceArtifact` requires body storage policy and blocks `body` unless `full_body_allowed`. |

## 5. Validation Commands

Executed locally from `/data/workspace/My/hwiStock` on 2026-06-04:

1. `source ./env.sh >/tmp/hwistock-env-unit008-test3.log 2>&1 && python -m unittest backend.tests.test_storage_contract`
   - Result: PASS
   - Output: 7 tests passed.

2. `source ./env.sh >/tmp/hwistock-env-unit008-compile3.log 2>&1 && python -m py_compile $(find backend -name '*.py' -print)`
   - Result: PASS

3. `source ./env.sh >/tmp/hwistock-env-unit008-rule-fastapi-all.log 2>&1 && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile /data/workspace/My/hwiStock/docs/profiles/PROFILE-HWISTOCK.md --preset fastapi-backend-rule-preset --all --fail-on-warn`
   - Result: PASS
   - Scanned files: 9
   - Findings: error=0, warning=0, info=0
   - Manual coverage remains for transaction/query contract checks not yet
     applicable to this storage-only skeleton.

4. `source ./env.sh >/tmp/hwistock-env-unit008-rule-db-all.log 2>&1 && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile /data/workspace/My/hwiStock/docs/profiles/PROFILE-HWISTOCK.md --preset db-naming-rule-preset --all --fail-on-warn`
   - Result: PASS
   - Findings: error=0, warning=0, info=0
   - Manual coverage remains for semantic DB ownership checks; migration text
     was additionally checked by `backend.tests.test_storage_contract`.

5. Local contract and secret validation:
   - required docs/code/evidence presence: PASS
   - UNIT-008 queue/preflight state: PASS
   - known KIS secret marker absence in docs/AGENTS/.gitignore/backend: PASS
   - tracked env-like file check: PASS
