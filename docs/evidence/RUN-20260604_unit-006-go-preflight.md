---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-006-go-preflight
stage: go
unit_id: HWISTOCK-UNIT-006
status: pass
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md
module_refs:
  - docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md
  - docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md
  - docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md
ready_set_completion_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
created_at: 2026-06-04
route_class: implementation_worker
adapter: cursor-sdk-local
model: composer-2.5
reasoning: cursor-sdk-default-reasoning
orchestration_gate_id: DG-HWISTOCK-UNIT-006-GO-20260604-001
---

# UNIT-006 Go Preflight Evidence

## 1. Verdict

PASS. `HWISTOCK-UNIT-006` may enter Go-Check for the foundation-only trading
engine/order-state skeleton scope.

This verdict authorizes only local schema/compiler/state-machine/dry-run/capability
code, focused tests, and docs/evidence updates. It does not authorize broker or
KIS network calls, AI provider calls, paper orders, live orders, executable
`submitted`/`accepted`/fill transitions, fake fills, fake balances, fake PnL,
credential reads, or runtime data artifact creation.

## 2. Delegation Guard

- Stage: go
- Gate size: FULL_GATE
- Route class: implementation_worker
- Adapter: cursor-sdk-local
- Model: composer-2.5
- Reasoning: cursor-sdk-default-reasoning
- Orchestration gate: DG-HWISTOCK-UNIT-006-GO-20260604-001
- Allowed writes:
  - `backend/lib/trading_engine.py`
  - `backend/tests/test_trading_engine_order_state.py`
  - `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md`
  - `docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md`
  - `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md`
  - `docs/index.md`
  - `docs/evidence/RUN-20260604_unit-006-go-check.md`
- Forbidden:
  - broker/KIS/AI network calls
  - paper or live order placement
  - executable `submitted`, `accepted`, `partial_fill`, `filled`, cancel/retry,
    reconciliation, or broker-backed transitions
  - fake broker, fake fill, fake balance, fake PnL generation
  - credential/env secret reads and runtime `data/` artifact writes
  - git/svn mutation

## 3. Selected Row Scope

Included implementation:

- `condition_card/v0` schema validator.
- Candidate-card to deterministic condition compiler skeleton.
- Order-state enum/transition skeleton that can stop at `dry_run_recorded`.
- No-order dry-run decision recorder.
- KRX/NXT/SOR route metadata and KIS paper capability flags with unsupported
  NXT/SOR/helper branches disabled or local-fallback-only.
- Focused unittest coverage for the foundation P0 QA rows.
- Unit/module/QA/index and evidence updates.

Excluded:

- Broker/KIS network adapters and endpoint calls.
- AI provider calls or browser/model automation.
- Paper/live order placement.
- Simulated fills, fake balances, fake PnL, or broker order ids.
- Executable transitions into `submitted`, `accepted`, `partial_fill`, `filled`,
  cancel/retry, or reconciliation states.
- Dashboard UI and runner/systemd wiring.

## 4. Preflight Checklist

| check_id | result | evidence |
| --- | --- | --- |
| PF-01 | pass | Ready-Set completion report exists with `implementation_ready: true`. |
| PF-02 | pass | `HWISTOCK-UNIT-006` appears in the full Go queue. |
| PF-03 | pass | Row closure marks `HWISTOCK-UNIT-006` as `ready_for_go_check`. |
| PF-04 | pass | Unit, module, QA scenario, profile, and index refs exist. |
| PF-05 | pass | Selected row explicitly limits Go to condition/order-state skeleton and no-order dry-run. |
| PF-06 | pass | Residual denials forbid submitted/accepted/fill transitions, broker calls, fake fills, fake balances, and fake PnL. |
| PF-07 | pass | KIS paper smoke evidence does not authorize additional unscoped broker/KIS calls for this unit. |
| PF-08 | pass | UNIT-004 strategy/risk validator foundation is already available for risk-boundary references. |
| PF-09 | pass | No dashboard, service runner, broker adapter, AI provider, or runtime data path is required for this Go scope. |

## 5. Pre-Go Action

Proceed with a bounded Cursor SDK local implementation worker under
`DG-HWISTOCK-UNIT-006-GO-20260604-001`.

## 6. Denied Paths

- `/home/hwi/.config/hwistock/`
- `.env`, `env.sh` contents, broker credentials, tokens, account numbers
- runtime `data/` artifacts
- unrelated docs/code outside the contract allowlist
- broker/KIS/AI network endpoints
