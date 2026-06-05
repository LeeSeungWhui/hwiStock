---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-004-go-preflight-rebaseline
stage: go
unit_id: HWISTOCK-UNIT-004
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md
module_refs:
  - docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md
ready_set_completion_ref: docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md
owner_decisions_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
created_at: 2026-06-04
route_class: implementation_worker
route: codex multi-agent
adapter: multi_agent_v1
model: gpt-5.4
reasoning: high
orchestration_gate_id: DG-HWISTOCK-UNIT-004-GO-GPT54-20260604-REBASELINE-001
---

# UNIT-004 Go Preflight Evidence — Rebaseline

## 1. Verdict

PASS. `HWISTOCK-UNIT-004` may enter current-authority rebaseline Go-Check for a
stdlib-only strategy/risk rulebook skeleton in the actual project root.

This preflight authorizes only local config/constants, deterministic validators,
focused unittest coverage, no-order dry-run record shaping, and doc/evidence
updates. It does not authorize broker/KIS calls, AI provider calls, adapter
orders, account-affecting orders, fake broker/fill/balance/PnL behavior, credential reads,
or runtime data artifact commits.

## 2. Delegation Guard Contract

- Stage: go
- Route class: implementation_worker
- Route: `codex multi-agent`
- Adapter: `multi_agent_v1`
- Model: `gpt-5.4`
- Reasoning: `high`
- Gate id: `DG-HWISTOCK-UNIT-004-GO-GPT54-20260604-REBASELINE-001`
- Workspace mode: direct project cwd

Allowed write scope:

- `backend/lib/strategy_risk.py`
- `backend/tests/test_strategy_risk_rulebook.py`
- `docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md`
- `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`
- `docs/index.md`

Denied paths/actions remain:

- `/home/hwi/.config/hwistock/**`, `.env*`, ignored template config files, and
  `apiRefer/**`
- broker/KIS/network/web/browser/SSH/remote use
- Git mutation, server runs, DB/migration/package-manager flows, deploys
- adapter/account-affecting orders, fake fills, fake balances, fake PnL, expected-profit claims

## 3. Selected Row Scope

Included implementation:

- stdlib-only `backend/lib/strategy_risk.py`
- deterministic config/validator surface for current-authority MOD-003 rules
- no-order dry-run record builder/validator
- focused unittest coverage for QA-001..QA-016 where local-only scope applies
- current-authority rebaseline module/unit/QA/index/row-closure/evidence updates

Excluded:

- broker or KIS adapters beyond `no_order_dry_run`
- AI provider runtime calls
- adapter/account-affecting order execution
- fake broker/fill/balance/PnL behavior
- runtime artifact generation under `data/`
- strategy parameter changes beyond already-approved first-pass adapter-backed defaults

## 4. Preflight Checklist

| check_id | result | evidence |
| --- | --- | --- |
| PF-01 | pass | Rebaseline completion report exists. |
| PF-02 | pass | Current scope is `full_queue_skeleton_sandbox_safe`; operational trading readiness remains false. |
| PF-03 | pass | `HWISTOCK-UNIT-004` is in the current Go queue. |
| PF-04 | pass | Row closure listed UNIT-004 as `ready_for_go_check` before this implementation pass. |
| PF-05 | pass | Profile, module, unit, QA, and index refs exist. |
| PF-06 | pass | Scope stays local skeleton-safe and does not cross broker/AI/public-dashboard material-expansion boundaries. |
| PF-07 | pass | No open historical P0/P1 review findings block this local-only scope. |
| PF-08 | pass | First-pass strategy defaults are approved for adapter-backed planning only. |
| PF-09 | pass | Dashboard scope remains out of row selection. |
| PF-10 | pass | Selected work is no-network, no-order, no-credential local validation only. |
| PF-11 | pass | Owner decision receipt and Ready-Set reissue evidence are recorded. |
| PF-12 | not_applicable | Current queue is full, not narrowed foundation-only. |
| PF-13 | pass | Git baseline exists and ignored secrets/data boundaries remain active. |
| PF-14 | pass | Selected backend-lib/test/doc scope adds no MyWebTemplate sample/public/runtime surface. |

## 5. Focused Go Smoke Rows

- P0: QA-001, QA-002, QA-003, QA-004, QA-005, QA-012, QA-014, QA-015
- P1 local-only: QA-006, QA-008, QA-009, QA-011, QA-013, QA-016
- Deferred to later trading-engine execution/logging scope: QA-007, QA-010

## 6. Pre-Go Action

Proceed with the local strategy/risk rulebook reimplementation, focused tests,
and current-authority rebaseline evidence updates only.
