---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-008-go-preflight-rebaseline
stage: go
unit_id: HWISTOCK-UNIT-008
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md
module_refs:
  - docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md
ready_set_completion_ref: docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md
rebaseline_evidence_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
created_at: 2026-06-04
supersedes:
  - docs/evidence/RUN-20260604_unit-008-go-preflight.md
---

# UNIT-008 Go Preflight Evidence — Rebaseline 2026-06-04

## 1. Verdict

PASS. `HWISTOCK-UNIT-008` may enter Go-Check for the current MyWebTemplate
import baseline under the bounded local storage skeleton scope.

This preflight authorizes only local backend storage contract files, Alembic
schema skeleton files, focused tests, and docs/evidence synchronization. It
does not authorize live database migration execution, broker/KIS network calls,
AI provider calls, paper orders, live orders, credential storage, runtime
`data/` artifact commits, dashboard UI, deploy, server operations, browser QA,
or operational trading readiness.

## 2. Current Baseline

The historical `RUN-20260604-unit-008-go-preflight` evidence is superseded
because the 2026-06-04 MyWebTemplate import changed the backend/frontend code
baseline. This rebaseline preflight uses:

- `docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md`
- `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`
- `docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md`

## 3. Delegation Guard

- Stage: go
- Gate size: FULL_GATE
- Route class: implementation_worker
- Workspace: `/data/workspace/My/hwiStock`
- Workspace mode: direct project cwd
- Primary non-GPT preference: Cursor SDK / MoonBridge routes where available
  and launch-verified.
- Forbidden:
  - `.env*`, `/home/hwi/.config/hwistock/**`, `backend/config.ini`,
    `backend/config.test.ini`, `frontend-web/config.ini`, and `apiRefer/**`
  - broker/KIS/API/AI network calls
  - token/account/balance/quote/realtime/order/WebSocket calls
  - database connections and migration execution
  - server/deploy/browser/systemd/git mutation
  - runtime `data/` artifact commits
  - fake fills, fake balances, fake PnL, paper orders, live orders

## 4. Selected Row Scope

Included implementation/check surface:

- `backend/lib/storage_schemas.py`
- `backend/lib/request_payload.py`
- `backend/migrations/README.md`
- `backend/migrations/env.py`
- `backend/migrations/script.py.mako`
- `backend/migrations/versions/20260604_0001_create_hwistock_core_storage.py`
- `backend/tests/test_storage_contract.py`
- UNIT-008 module/unit/QA/index/evidence documentation

Excluded surface:

- live PostgreSQL connection or `alembic upgrade`
- external source ingestion
- AI API execution
- broker API execution
- dashboard implementation
- runtime artifact generation under `data/`

## 5. Pre-Go Checklist

| check_id | result | evidence |
| --- | --- | --- |
| PF-01 | PASS | Current rebaseline Ready-Set completion report exists. |
| PF-02 | PASS | Rebaseline completion report has `implementation_ready: true` for `skeleton_sandbox_safe_rebaseline_queue`. |
| PF-03 | PASS | `HWISTOCK-UNIT-008` appears in the rebaseline Go-Check queue. |
| PF-04 | PASS | At preflight time `HWISTOCK-UNIT-008` queue row was `ready_for_go_check`; after Go-Check this row is updated to `go_check_passed` in the row-closure matrix. |
| PF-05 | PASS | Unit, module, QA scenario, profile, and index refs exist. |
| PF-06 | PASS | Current scope is local storage skeleton only; no broker/API/order action is authorized. |
| PF-07 | PASS | PostgreSQL isolation decision remains `hwistock` / `hwistock_core` / `HWISTOCK_DATABASE_URL`. |
| PF-08 | PASS | MyWebTemplate import invalidated old UNIT-008 evidence, so a new current Go-Check evidence file is required. |

## 6. Pre-Go Action

Proceed with UNIT-008 current-tree storage skeleton implementation, validation,
review-worker Check, and rebaseline evidence synchronization.
