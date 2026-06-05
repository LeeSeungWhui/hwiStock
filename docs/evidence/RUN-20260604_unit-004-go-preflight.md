---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-004-go-preflight
stage: go
unit_id: HWISTOCK-UNIT-004
status: pass
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md
module_refs:
  - docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md
strategy_decision_packet_ref: docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md
ready_set_completion_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
owner_decisions_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
created_at: 2026-06-04
route_class: implementation_worker
adapter: cursor-sdk-local
orchestration_gate_id: DG-HWISTOCK-UNIT-004-GO-20260604-001
---

# UNIT-004 Go Preflight Evidence

## 1. Verdict

PASS. `HWISTOCK-UNIT-004` may enter Go-Check for the local-only strategy/risk
rulebook skeleton scope.

This verdict authorizes only approved config constants, deterministic
entry-intent validators, no-order dry-run record shaping, focused tests, and
evidence updates. It does not authorize broker/KIS calls, AI provider calls,
broker orders, account-affecting orders, fake fills, fake balances, fake PnL, credential
storage, or runtime data artifact commits.

## 2. Delegation Guard

- Stage: go
- Gate size: FULL_GATE
- Route class: implementation_worker
- Adapter: cursor-sdk-local
- Model: composer-2.5
- Orchestration gate: DG-HWISTOCK-UNIT-004-GO-20260604-001
- Allowed writes:
  - `backend/lib/strategy_risk.py`
  - `backend/tests/test_strategy_risk_rulebook.py`
  - `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
  - `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`
  - `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
  - `docs/index.md`
  - `docs/evidence/RUN-20260604_unit-004-*.md`
- Forbidden:
  - broker/KIS/AI network calls
  - adapter or account-affecting order placement
  - fake broker, fake fill, fake balance, fake PnL generation
  - approved strategy parameter changes beyond the already-approved first-pass
    adapter-backed planning defaults
  - runtime `data/` artifact commits

## 3. Selected Row Scope

Included implementation:

- approved UNIT-004 config constants
- deterministic entry-intent validators
- no-order dry-run record shape
- focused unittest coverage for P0/P1 QA rows
- unit/module/QA/index and evidence updates

Excluded:

- broker order routing or adapters beyond `no_order_dry_run`
- AI provider calls
- scheduler/service loop
- fake fill/balance/PnL simulation
- strategy parameter changes beyond approved packet defaults

## 4. Preflight Checklist

| check_id | result | evidence |
| --- | --- | --- |
| PF-01 | pass | Ready-Set completion report exists. |
| PF-02 | pass | Full queue skeleton/adapter-safe scope is active. |
| PF-03 | pass | `HWISTOCK-UNIT-004` appears in the Go queue. |
| PF-04 | pass | Strategy decision packet owner approval is recorded in `RUN-20260604_full-ready-set-owner-decisions-presend.md`. |
| PF-05 | pass | Unit, module, QA scenario, profile, and index refs exist. |
| PF-06 | pass | Current final GPT Pro review is complete for the full queue. |
| PF-07 | pass | No open P0/P1 findings block the selected local-only scope. |
| PF-08 | pass | Dashboard UI is out of scope. |
| PF-09 | pass | Broker/KIS order behavior remains out of scope. |
| PF-10 | pass | Selected action is no-network, no-order, no-credential local config/validation work. |
| PF-11 | pass | Git baseline and Ready-Set owner decisions are recorded. |
| PF-12 | not_applicable | Current queue is the full skeleton/adapter-safe queue. |
| PF-13 | pass | Git baseline exists; secrets and runtime `data/` remain ignored. |

## 5. Pre-Go Action

Proceed with local strategy/risk rulebook skeleton implementation and focused
validation.

## 6. Denied Paths

- `/home/hwi/.config/hwistock/`
- `.env`, `env.sh` contents, broker credentials, tokens, account numbers
- unrelated docs/code outside the contract allowlist
- broker/KIS/AI network endpoints
