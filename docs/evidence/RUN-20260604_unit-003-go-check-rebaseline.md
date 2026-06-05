---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-003-go-check-rebaseline
stage: go-check
unit_id: HWISTOCK-UNIT-003
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md
module_refs:
  - docs/modules/HWISTOCK-MOD-002_market-intelligence-ingestion.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md
source_registry_ref: docs/sources/HWISTOCK-SOURCE-REGISTRY.md
preflight_ref: docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md
created_at: 2026-06-04
supersedes:
  - docs/evidence/RUN-20260604_unit-003-go-check.md
---

# UNIT-003 Go-Check Evidence — Rebaseline 2026-06-04

## 1. Verdict

PASS for the bounded current-tree market-intelligence ingestion skeleton scope.

`HWISTOCK-UNIT-003` now has a stdlib-only, fixture/config-first source registry
and ingestion skeleton. It defines approved/conditional/deferred/forbidden
source states, normalizes in-memory fixture rows into required event fields,
links duplicates by dedupe key, exposes summary/health dictionaries, enforces
KST `+09:00` timestamps, and blocks caller overrides of per-source
`body_storage_policy`.

This result does not authorize network source collection, broker/KIS calls, AI
provider calls, order placement, credential storage, runtime scheduler
execution, runtime artifact writes under `data/`, browser QA, deploy, server
operations, or operational trading readiness.

## 2. Current Go Changes

| path | change |
| --- | --- |
| `backend/lib/market_intelligence.py` | deterministic source registry, foundation source-status model, normalized event validation, KST timestamp enforcement, registry-controlled body storage policy, dedupe keys, source hashes, duplicate linking, and blocked-source classification |
| `backend/service/market_intelligence_ingestion.py` | in-memory fixture-row ingestion orchestration returning events, summary, and health dictionaries without file writes or network calls |
| `backend/tests/test_market_intelligence_ingestion.py` | focused unittest coverage for QA-001 through QA-011, including no network/order imports, blocked/deferred source behavior, duplicate linking, KST timestamp rejection, and body policy enforcement |
| `docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md` | current preflight evidence |
| `docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md` | current Go-Check evidence |

## 3. Worker Output Acceptance

### Attempt 1 — quarantined implementation worker

- Gate id: `DG-HWISTOCK-UNIT-003-GO-CURSOR-20260604-001`.
- Route/model: `cursor-sdk-local` through `hwi-cursor-worker run` /
  `composer-2.5`.
- Workspace: `/data/workspace/My/hwiStock` direct project cwd.
- Contract: `/tmp/hwistock-unit003-cursor-20260604/contract.md`.
- Transcript: `/tmp/hwistock-unit003-cursor-20260604/transcript.jsonl`.
- Observed result: the worker wrote the initial UNIT-003 library/service/test
  files and its final text contained `WORKER_RESULT: DONE`.
- Failure: wrapper classified the run as `incomplete_worker_result` because the
  assistant stream contained prose before the final sentinel.
- Acceptance state: quarantined. Its file changes were not treated as accepted
  worker output until orchestrator inspection, local validation, remediation,
  and review-worker Check were completed.

### Attempt 2 — accepted read-only Check review

- Gate id: `DG-HWISTOCK-UNIT-003-CHECK-GPT54-20260604-001`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Worker id/nickname: `019e9242-7415-72b1-85eb-23cca938cbf5` / Nash.
- Result: `REVIEW_RESULT: DONE`.
- Findings:
  - P1 stale current-authority evidence and status docs still said UNIT-003 was
    superseded/pending.
  - P1 timestamp validation allowed `Z` or missing timezone for KST-labeled
    fields.
  - P2 fixture normalization allowed caller override of source
    `body_storage_policy`.
- Acceptance state: accepted as a blocker review. The P1/P2 findings were
  remediated locally in the exact named files and revalidated.

### Attempt 3 — blocked final GPT re-review

- Gate id: `DG-HWISTOCK-UNIT-003-CHECK-GPT54-20260604-002`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Worker id/nickname: `019e924b-9802-7661-a1c8-6e01893d77c9` / Erdos.
- Result: `REVIEW_RESULT: BLOCKED`.
- Failure: the worker contract forbade shell commands, and the worker had no
  non-shell file-read tool in-session. It therefore could not inspect the
  allowed files or produce path:line evidence.
- Acceptance state: blocked/no evidence. This attempt is preserved as a route
  contract failure, not used for Go-Check closure.

### Attempt 4 — accepted final GPT re-review

- Gate id: `DG-HWISTOCK-UNIT-003-CHECK-GPT54-20260604-003`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Worker id/nickname: `019e924c-d5b5-7e72-8fc6-2ea6a764842f` / Huygens.
- Result: `REVIEW_RESULT: DONE`.
- Prior findings status:
  - stale docs/status: resolved.
  - timestamp KST validation: resolved.
  - `body_storage_policy` override: resolved.
- Go-Check closure verdict: `no_open_P0_P1`.
- Acceptance state: accepted final Check review for the bounded UNIT-003
  fixture/config-first ingestion skeleton scope.

### Remediation disposition

- Timestamp validation now accepts only ISO-8601 timestamps ending in `+09:00`
  for `published_at_kst` and `collected_at_kst`.
- `normalizeFixtureRow` now uses the source registry's `body_storage_policy`;
  mismatched caller-supplied policy values raise `ValueError`.
- Focused regression tests cover both fixes.
- This rebaseline evidence and matching unit/module/QA/index/row-closure
  updates resolve the stale documentation blocker.

## 4. QA Row Results

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | PASS | Source registry config entries expose status, method, credential policy, storage policy, rate, terms, retention, and body policy fields. |
| QA-002 | PASS | Import inspection confirms no broker/order/trading routing imports in UNIT-003 implementation modules. |
| QA-003 | PASS | Source policy notes and rate/terms text are present in the implementation config. |
| QA-004 | PASS | Duplicate disclosure fixtures link deterministically by dedupe key. |
| QA-005 | PASS | Health output exposes source counts, failures, backlog, disabled network sources, blocked source ids, duplicate links, and last fetch timestamps. |
| QA-006 | PASS | Summary dictionary exposes source counts, duplicate count, failures, disabled network sources, and retention notes without writing runtime evidence files. |
| QA-007 | PASS | Market-data context fields include venue, interval, OHLCV schema, and latency budget while network chart sources remain disabled/deferred. |
| QA-008 | PASS | General HTML scraping and unofficial finance APIs are blocked in foundation mode. |
| QA-009 | PASS | KIS/broker market/realtime/news source remains deferred and cannot ingest. |
| QA-010 | PASS | Normalized event schema includes all required UNIT-003 fields; validation rejects non-KST/ambiguous timestamps and caller body-policy overrides. |
| QA-011 | PASS | Foundation fixture smoke succeeds without credentials, network imports, network source calls, broker/KIS imports, or order-routing imports. |

## 5. Validation Commands

Executed locally from `/data/workspace/My/hwiStock` on 2026-06-04:

1. `source ./env.sh >/tmp/hwistock-unit003-env-compile3.log 2>&1 && python -m py_compile backend/lib/market_intelligence.py backend/service/market_intelligence_ingestion.py backend/tests/test_market_intelligence_ingestion.py`
   - Result: PASS.

2. `source ./env.sh >/tmp/hwistock-unit003-env-test4.log 2>&1 && python -m unittest backend.tests.test_market_intelligence_ingestion`
   - Result: PASS.
   - Output: `Ran 10 tests in 0.010s` / `OK`.

3. `source ./env.sh >/tmp/hwistock-unit003-env-combined4.log 2>&1 && python -m unittest backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract`
   - Result: PASS.
   - Output: `Ran 18 tests in 0.008s` / `OK`.

4. `source ./env.sh >/tmp/hwistock-unit003-env-rule-fastapi4.log 2>&1 && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --preset fastapi-backend-rule-preset --all --fail-on-warn --json >/tmp/hwistock-unit003-rule-fastapi4.json`
   - Overall result: FAIL due pre-existing broader backend/import baseline.
   - Total findings: 92.
   - UNIT-003 changed-path findings: 0.

5. `source ./env.sh >/tmp/hwistock-unit003-env-rule-db4.log 2>&1 && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --preset db-naming-rule-preset --all --fail-on-warn --json >/tmp/hwistock-unit003-rule-db4.json`
   - Overall result: FAIL due pre-existing broader SQL/import baseline.
   - Total findings: 25.
   - UNIT-003 changed-path findings: 0.

6. `git diff --check -- backend/lib/market_intelligence.py backend/service/market_intelligence_ingestion.py backend/tests/test_market_intelligence_ingestion.py`
   - Result: PASS.

Known KIS app-key, secret, adapter account, and HTS id markers were not found in
UNIT-003 implementation/test/doc evidence files during the local marker check.

## 6. Residual Boundaries

- Network OpenDART, Naver, KRX/KIND, KIS/broker, general HTML scraping, and
  unofficial API paths remain disabled in this row.
- This row does not create API routes, runtime scheduler loops, persistent event
  stores, or runtime `data/` artifacts.
- The broader MyWebTemplate sample/public route quarantine is tracked by other
  rows. This evidence proves that UNIT-003 library/service/test files do not
  introduce a market-intelligence sample/public backend surface.
- Full-repo FastAPI/DB rule-gates still fail on broader imported/backend
  baseline findings outside UNIT-003. UNIT-003 changed paths have zero
  rule-gate findings.

## 7. Check Disposition

The accepted GPT review found P1/P2 issues and the code/documentation
remediation above resolved them. The accepted final GPT re-review confirmed no
open P0/P1 findings remain for the bounded UNIT-003 current-tree
fixture/config-first ingestion skeleton scope.
