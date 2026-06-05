---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-006-go-preflight-rebaseline
stage: go
unit_id: HWISTOCK-UNIT-006
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md
module_refs:
  - docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md
  - docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md
  - docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md
superseded_context_refs:
  - docs/evidence/RUN-20260604_unit-006-go-preflight.md
  - docs/evidence/RUN-20260604_unit-006-go-check.md
created_at: 2026-06-04
environment: local_only
route_class: implementation_worker
route: codex multi-agent
adapter: multi_agent_v1
model: gpt-5.4
reasoning: high
orchestration_gate_id: DG-HWISTOCK-UNIT-006-GO-GPT54-20260604-REBASELINE-001
---

# UNIT-006 Go Preflight Evidence — Rebaseline

## 1. Verdict

PASS. `HWISTOCK-UNIT-006` may enter current-authority Go-Check for the imported
MyWebTemplate-derived backend tree, but only for the local foundation skeleton
scope.

Authorized scope is limited to:

- `backend/lib/trading_engine.py`
- `backend/tests/test_trading_engine_order_state.py`
- current-authority evidence/doc status updates for UNIT-006

This preflight does **not** authorize broker/KIS network calls, AI provider
calls, adapter/account-affecting order placement, executable `submitted`/`accepted`/fill
transitions, fake fill/balance/PnL generation, secret/config reads, server run,
DB work, or runtime artifact writes under `data/`.

Historical note:

- `docs/evidence/RUN-20260604_unit-006-go-preflight.md` is pre-rebaseline and
  no longer current authority.
- `docs/evidence/RUN-20260604_unit-006-go-check.md` is already
  `current_authority: false` and remains historical after the import.

## 2. Route

- Stage: Go for `HWISTOCK-UNIT-006`
- Route class: implementation_worker
- Route: `codex multi-agent`
- Adapter: `multi_agent_v1`
- Model: `gpt-5.4`
- Reasoning: `high`
- Gate id: `DG-HWISTOCK-UNIT-006-GO-GPT54-20260604-REBASELINE-001`

## 3. Selected Scope

Included implementation:

- `condition_card/v0` schema validation
- deterministic `compiled_watch/v0` compiler skeleton
- UNIT-004 strategy/risk rulebook delegation for entry-intent validation
- explicit state-machine validation through `dry_run_recorded`
- no-order dry-run decision record build/validation
- KIS adapter capability flags and route metadata
- fixture-only KIS adapter evidence representation without broker-state updates
- focused unittest coverage for QA-001 through QA-010

Excluded:

- broker adapter implementation
- KIS/API/provider/browser/network calls
- adapter/account-affecting order placement
- executable `submitted`/`accepted`/fill state progress in foundation mode
- fake fill/balance/PnL simulation
- dashboard/service/systemd/runtime integration

## 4. Preflight Checklist

| check_id | result | evidence |
| --- | --- | --- |
| PF-01 | pass | Current row-closure authority is `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`. |
| PF-02 | pass | UNIT-006 remains explicitly scoped to foundation-only trading-engine/order-state behavior. |
| PF-03 | pass | Allowed writes are limited to local backend library/test files plus current-authority UNIT-006 docs/evidence. |
| PF-04 | pass | UNIT-004 risk-rulebook helpers already exist and can be imported locally without parameter changes. |
| PF-05 | pass | No broker/KIS/API/browser/server/DB action is required for this Go scope. |
| PF-06 | pass | Residual denials still block adapter/account-affecting orders, fake fill/balance/PnL, and submitted-or-later execution in foundation mode. |
| PF-07 | pass | KIS adapter capability work is metadata/fixture-only; no broker-network approval expansion is implied. |
| PF-08 | pass | Current-go evidence can be produced through local compile/tests/docs updates only. |

## 5. Go Boundary

Proceed only with stdlib-only local helpers and focused tests. Any need for:

- broker/KIS calls
- real/broker order placement
- runtime market/session resolution
- submitted-or-later execution
- secret/config inspection

would exceed the approved first-Go scope and must stop the run.
