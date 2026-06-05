---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-008-go-check-rebaseline
stage: go-check
unit_id: HWISTOCK-UNIT-008
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md
module_refs:
  - docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md
preflight_ref: docs/evidence/RUN-20260604_unit-008-go-preflight-rebaseline.md
created_at: 2026-06-04
supersedes:
  - docs/evidence/RUN-20260604_unit-008-go-check.md
---

# UNIT-008 Go-Check Evidence — Rebaseline 2026-06-04

## 1. Verdict

PASS for the bounded current-tree storage skeleton scope.

`HWISTOCK-UNIT-008` now has typed artifact contracts, deterministic hashing,
canonical date-scoped artifact paths, adapter-day evidence link validation,
system-only PnL validation, an Alembic PostgreSQL schema skeleton for
`hwistock_core`, and focused contract tests.

This result does not authorize operational database migration execution, broker/KIS
network calls, AI provider calls, broker orders, account-affecting orders, credential
storage, runtime `data/` artifact commits, dashboard UI, deploy, server
operations, browser QA, or operational trading readiness.

## 2. Current Go Changes

| path | change |
| --- | --- |
| `backend/lib/storage_schemas.py` | typed artifact models, SHA-256 hashing, KST artifact path builder, sensitive-key name validation, system-only PnL validation, adapter-day evidence link validation |
| `backend/lib/request_payload.py` | storage/report query payload helper stubs compatible with the backend profile |
| `backend/migrations/README.md` | hwiStock Alembic isolation notes using `HWISTOCK_DATABASE_URL` and schema `hwistock_core` |
| `backend/migrations/env.py` | Alembic env skeleton with `HWISTOCK_DATABASE_URL`, `hwistock_core`, and controlled search path |
| `backend/migrations/script.py.mako` | Alembic revision template |
| `backend/migrations/versions/20260604_0001_create_hwistock_core_storage.py` | schema-qualified storage tables under `hwistock_core`, artifact links, and DB CHECK for system-only daily PnL |
| `backend/tests/test_storage_contract.py` | focused storage contract tests for hash, paths, source body policy, system PnL, manifest links, sensitive keys, payload helpers, and migration isolation |
| `docs/evidence/RUN-20260604_unit-008-go-preflight-rebaseline.md` | current preflight evidence |
| `docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md` | current Go-Check evidence |

## 3. Worker Output Acceptance

### Attempt 1 — quarantined implementation worker

- Gate id: `gate-20260604-go-unit008-rebaseline-001`.
- Route/model: `codex-cli-moonbridge` / `deepseek-v4-pro`.
- Launcher: `/home/hwi/.codex/skills/hwi-codex-moonbridge-worker/scripts/run_codex_moonbridge_worker.sh`.
- Workspace: `/data/workspace/My/hwiStock` direct project cwd.
- Contract: `/tmp/hwistock-unit008-worker-20260604/contract.md`.
- Transcript: `/tmp/hwistock-unit008-worker-20260604/transcript.log`.
- Observed wrapper header: `HWI_CODEX_MOONBRIDGE_WORKER_LAUNCH`,
  `MODEL=deepseek-v4-pro`, `CWD=/data/workspace/My/hwiStock`,
  `SANDBOX=danger-full-access`.
- Failure: `EXIT_CODE=124`, no last-message file, no final sentinel, timeout at
  240 seconds, and an intermediate incompatible `apply_patch` payload.
- Acceptance state: quarantined incomplete. Partial files were not accepted
  until a later worker and local validation repaired and verified them.

### Attempt 2 — accepted implementation worker

- Gate id: `gate-20260604-go-unit008-rebaseline-002`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Worker id/nickname: `019e91df-ea6a-7391-b81b-f567e074d42d` / Mendel.
- Reason for GPT fallback: Cursor route was not exposed through tool discovery
  at the time, MoonBridge DeepSeek timed out without sentinel, prior Kimi route
  was no-sentinel/no-last-message, and the remaining scope was persistence
  correctness cleanup requiring precise patch review.
- Sentinel: `WORKER_RESULT: DONE`.
- Changed files: UNIT-008 backend storage, migration, and focused test files.
- Worker validation: py_compile PASS and `python -m unittest
  backend.tests.test_storage_contract` PASS (`8 tests, OK`).
- Acceptance state: accepted after local diff review and re-validation.

### Attempt 3 — accepted read-only Check review

- Gate id: `DG-HWISTOCK-UNIT-008-CHECK-CURSOR-20260604-001`.
- Route/model: `cursor-sdk-local` through `hwi-cursor-worker run` /
  `composer-2.5`.
- Contract: `/tmp/hwistock-unit008-cursor-review-20260604/contract.md`.
- Transcript: `/tmp/hwistock-unit008-cursor-review-20260604/transcript.jsonl`.
- Wrapper status: accepted.
- Worker result: `DONE`.
- Review result: no P0 findings. The review identified stale superseded
  UNIT-008 evidence/unit wording as P1; this rebaseline evidence and matching
  unit/module/QA/index updates resolve that documentation blocker. The review
  also identified P2 hardening items for canonical artifact filenames, broader
  path tests, and DB-level system-only PnL enforcement; those were patched and
  revalidated locally.

### Attempt 4 — quarantined final Cursor review

- Gate id: `DG-HWISTOCK-UNIT-008-CHECK-CURSOR-20260604-002`.
- Route/model: `cursor-sdk-local` through `hwi-cursor-worker run` /
  `composer-2.5`.
- Contract: `/tmp/hwistock-unit008-cursor-review-20260604/contract-final.md`.
- Transcript:
  `/tmp/hwistock-unit008-cursor-review-20260604/transcript-final.jsonl`.
- Observed result: final text contained `REVIEW_RESULT: DONE` and no P0/P1
  findings.
- Failure: wrapper classified the run as `incomplete_worker_result` because the
  assistant stream contained prose before the final sentinel.
- Acceptance state: quarantined; useful only as advisory input. Its advisory P2
  notes about profile migration wording and QA historical evidence refs were
  patched locally before the accepted final review.

### Attempt 5 — failed GPT final review

- Gate id: `DG-HWISTOCK-UNIT-008-CHECK-GPT54-20260604-001`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Worker id/nickname: `019e91f5-dc67-7162-b02e-64a31da3d0f2` /
  Kierkegaard.
- Result: `REVIEW_RESULT: FAILED`.
- Finding: P1 row-closure sync gap. The queue table marked `HWISTOCK-UNIT-008`
  as `go_check_passed`, but the current row-closure file's Go-Check Progress
  table omitted UNIT-008.
- Acceptance state: accepted as a failing review; the P1 was patched by adding
  the UNIT-008 pass row to the progress table.

### Attempt 6 — accepted GPT re-review

- Gate id: `DG-HWISTOCK-UNIT-008-CHECK-GPT54-20260604-002`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Worker id/nickname: `019e91f5-dc67-7162-b02e-64a31da3d0f2` /
  Kierkegaard.
- Result: `REVIEW_RESULT: DONE`.
- Findings: no P0/P1 findings. Prior P1 resolved.
- Validation: read-only review confirmed
  `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md` Go-Check
  Progress includes `HWISTOCK-UNIT-008 | pass |
  docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md`.
- Acceptance state: accepted final Check review for the bounded UNIT-008
  storage skeleton scope.

## 4. QA Row Results

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | PASS | Unit/module/migration README select PostgreSQL plus date-partitioned artifacts; SQLite is not part of the first implementation. |
| QA-002 | PASS | `backend/migrations/env.py` uses `HWISTOCK_DATABASE_URL`; migration tables are schema-qualified under `hwistock_core`; docs preserve database `hwistock`; no MyWebTemplate database/schema/migration names are used in UNIT-008 files. |
| QA-003 | PASS | `build_artifact_path` separates raw news/disclosures/market-data, normalized events, AI deepseek-pro/deepseek-flash outputs, candidates, trading logs, reports, and evidence manifests. |
| QA-004 | PASS | `BaseArtifact` and typed subclasses include required ids, type, KST timestamp/date, environment, source/related links, symbols, redaction, and hash fields. |
| QA-005 | PASS | `DailyPnL` requires `calculation_source: system`; migration adds a DB CHECK for the same system-only value. |
| QA-006 | PASS | `PaperDayEvidenceManifest` requires source, normalized, AI, candidate, order, fill, position, PnL, morning report, and daily-close links. |
| QA-007 | PASS | Sensitive key-name validation exists; local grep over UNIT-008 files found no actual pasted KIS app key, secret, HTS id, or account number. |
| QA-008 | PASS | Migration stores artifact id/path/hash/date/environment and child tables link through schema-qualified artifact foreign keys. Runtime DB execution remains future scope. |
| QA-009 | PASS | `SourceArtifact` records body storage policy and rejects full `body` unless `full_body_allowed`. |

## 5. Validation Commands

Executed locally from `/data/workspace/My/hwiStock` on 2026-06-04:

1. `source ./env.sh >/tmp/hwistock-unit008-local-compile4.log 2>&1 && python -m py_compile backend/lib/storage_schemas.py backend/lib/request_payload.py backend/migrations/env.py backend/migrations/versions/20260604_0001_create_hwistock_core_storage.py backend/tests/test_storage_contract.py`
   - Result: PASS.

2. `source ./env.sh >/tmp/hwistock-unit008-local-test4.log 2>&1 && python -m unittest backend.tests.test_storage_contract`
   - Result: PASS.
   - Output: `Ran 8 tests in 0.001s` / `OK`.

3. `source ./env.sh >/tmp/hwistock-unit008-sensitive-grep2-env.log 2>&1 && rg -n "<known-secret-markers-and-sensitive-key-names>" backend/lib/storage_schemas.py backend/lib/request_payload.py backend/migrations backend/tests/test_storage_contract.py || true`
   - Result: PASS for actual secret absence.
   - Findings were limited to validator/test strings such as `api_key`,
     `secret`, `token`, `password`, `account_no`, and the test fixture string
     `token`.

4. `source ./env.sh >/tmp/hwistock-unit008-rule-fastapi4-env.log 2>&1 && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile /data/workspace/My/hwiStock/docs/profiles/PROFILE-HWISTOCK.md --preset fastapi-backend-rule-preset --all --fail-on-warn --json >/tmp/hwistock-unit008-rule-fastapi4.json`
   - Overall result: FAIL due pre-existing broader backend/import baseline.
   - Total findings: 92.
   - UNIT-008 changed-path findings: 0.

5. `source ./env.sh >/tmp/hwistock-unit008-rule-db4-env.log 2>&1 && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile /data/workspace/My/hwiStock/docs/profiles/PROFILE-HWISTOCK.md --preset db-naming-rule-preset --all --fail-on-warn --json >/tmp/hwistock-unit008-rule-db4.json`
   - Overall result: FAIL due pre-existing broader SQL/import baseline.
   - Total findings: 25.
   - UNIT-008 changed-path findings: 0.

6. `git diff --check`
   - Result: PASS.

## 6. Residual Boundaries

- No operational PostgreSQL database connection or `alembic upgrade` was run.
- `HWISTOCK_DATABASE_URL` values were not read because env/config values may
  contain secrets.
- Sensitive validation checks field names and known marker absence; it does not
  perform arbitrary secret-value classification.
- File-to-DB runtime write integration is future work; this row proves the
  storage contract skeleton and migration shape.
- The full-repo FastAPI/DB rule-gates still fail on broader imported/backend
  baseline findings outside UNIT-008. UNIT-008 changed paths have zero
  rule-gate findings.

## 7. Check Disposition

No open P0/P1 findings remain for the bounded UNIT-008 current-tree storage
skeleton scope after this rebaseline evidence and doc synchronization. The
final accepted GPT re-review confirmed the prior row-closure P1 is resolved.
P2 hardening items for canonical artifact filenames, path test coverage,
profile migration wording, QA evidence refs, and system-only daily PnL DB
enforcement were patched and revalidated.
