---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-006-go-check-rebaseline
stage: go-check
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
preflight_ref: docs/evidence/RUN-20260604_unit-006-go-preflight-rebaseline.md
historical_evidence_refs:
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

# UNIT-006 Go-Check Evidence — Rebaseline

## 1. Verdict

PASS. `HWISTOCK-UNIT-006` now has a current-authority rebaseline trading
engine/order-state foundation skeleton in the imported backend tree.

Validated scope is limited to deterministic local helpers for
`condition_card/v0`, `compiled_watch/v0`, UNIT-004 risk-gate delegation,
dry-run-only state validation through `dry_run_recorded`, no-order dry-run
decision records, KIS paper capability flags, route metadata, SOR/AUTO_SESSION
risk-gate normalization-or-blocking, and fixture-only broker-evidence
representation. This closure does **not** authorize broker/KIS network calls,
paper/live orders, executable submitted-or-later state progress, fake fills,
fake balances, fake PnL, secret reads, server start, DB work, or runtime
artifact writes.

Historical note:

- `docs/evidence/RUN-20260604_unit-006-go-check.md` remains historical and
  `current_authority: false`.
- `docs/evidence/RUN-20260604_unit-006-go-preflight.md` is pre-rebaseline
  context only and not current authority.

## 2. Route

- Stage: Go for `HWISTOCK-UNIT-006`, producing current-authority rebaseline Go evidence
- Route class: implementation_worker
- Route: `codex multi-agent`
- Adapter: `multi_agent_v1`
- Model: `gpt-5.4`
- Reasoning: `high`
- Gate id: `DG-HWISTOCK-UNIT-006-GO-GPT54-20260604-REBASELINE-001`

## 3. Implemented Scope

- `backend/lib/trading_engine.py`
  - `loadTradingEngineConfig()` for deterministic local engine defaults and
    explicit boundaries
  - `validateConditionCard()` for required-field, route, source/risk-ref,
    expiry, and vague natural-language-only rejection
  - `compileConditionCard()` producing non-executable `compiled_watch/v0`
  - `isAiCandidateNonExecutable()` to preserve the AI/output boundary
  - `evaluateEntryRiskGate()` delegating to UNIT-004
    `validateEntryIntent()` after explicit route handling:
    - `KRX` / `NXT` direct
    - `SOR` normalized to underlying `KRX` for current foundation risk gating
    - `AUTO_SESSION` blocked unless an explicit `session_venue_hint` resolves
      to `KRX` or `NXT`
  - `validateOrderStateTransition()` enforcing foundation-only progress through
    `dry_run_recorded`
  - `buildNoOrderDryRunDecisionRecord()` /
    `validateNoOrderDryRunDecisionRecord()` with explicit no-broker/
    no-simulated-fill/no-simulated-balance/no-simulated-pnl/
    no-paper-order/no-live-order flags
  - `loadKisPaperCapabilityFlags()` and `resolveVenueRoute()` for KRX/NXT/SOR/
    AUTO_SESSION shared-state-machine metadata with unsupported KIS paper
    branches returning `disabled_branch` or `local_fallback`
  - `representBrokerEventState()` / `representKisPaperEvidenceEvent()` for
    fixture-only order/fill/balance/cancel/helper evidence representation
    without state updates, with event-kind-specific mapped-state compatibility
- `backend/tests/test_trading_engine_order_state.py`
  - focused unittest coverage for QA-001 through QA-010
  - stdlib/no-network import-boundary assertions
  - dry-run/non-executable/fake-simulation rejection coverage
  - Carson P1/P2 follow-up coverage for route normalization and semantic
    event-kind/state compatibility

## 4. Boundary Evidence

- No implementation path imports network clients, broker adapters, FastAPI,
  SQLAlchemy, or AI SDK modules.
- No implementation path performs broker/KIS/API/browser/server/DB actions.
- SOR is preserved as requested route metadata but is risk-gated against
  underlying `KRX` in current foundation mode.
- AUTO_SESSION is preserved as requested route metadata but is blocked unless a
  resolved underlying venue hint is supplied.
- No implementation path can advance foundation mode into `submitted`,
  `accepted`, `partial_fill`, `filled`, `cancel_requested`, `cancelled`,
  `rejected`, `retrying`, or `failed` unless `approved_adapter_enabled=True`;
  even then the helper returns representation-only metadata and
  `state_update_executed=False`.
- No dry-run record can carry broker order ids, submitted/accepted/fill fields,
  or fake fill/balance/PnL markers.
- Balance evidence cannot be mislabeled as an order state.
- Unsupported KIS paper helper branches are explicit `local_fallback` or
  `disabled_branch` records only.

## 5. QA Row Coverage

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | Valid candidate cards compile to non-executable `compiled_watch/v0`; AI output remains non-executable. |
| QA-002 | pass | `natural_language` / `looks good` style watch conditions are rejected. |
| QA-003 | pass | `evaluateEntryRiskGate()` delegates to UNIT-004 `validateEntryIntent()` with explicit requested-route preservation plus risk-gate venue normalization/blocking metadata. |
| QA-004 | pass | Order-state skeleton explicitly represents submitted, accepted, partial fill, rejected, cancel requested/cancelled, retrying, and failed late states while still blocking executable progress in foundation mode. |
| QA-005 | pass | Dry-run decision records enforce no broker call, no simulated fill, no simulated balance, no simulated PnL, no paper order, and no live order. |
| QA-006 | pass | KRX/NXT/SOR/AUTO_SESSION share one state machine; SOR normalizes to KRX for foundation risk gating, unresolved AUTO_SESSION blocks clearly, and KIS paper NXT/SOR branches remain `disabled_branch`. |
| QA-007 | pass | `condition_card/v0` validator accepts required valid shape and rejects missing/expired/unknown/vague inputs. |
| QA-008 | pass | KIS paper capability flags expose KRX-only order/realtime support with unsupported helper flags set false. |
| QA-009 | pass | Order/fill/cancel fixture evidence requires explicit semantically compatible mapped states; balance/helper/disabled/local fallback cannot impersonate order state. |
| QA-010 | pass | Foundation smoke confirms stdlib/local-only import boundary and no executable submitted-or-later path without explicit adapter approval metadata. |

## 6. Validation

Compile check:

```text
source ./env.sh >/tmp/hwistock-env-source.log && python -m py_compile backend/lib/trading_engine.py backend/tests/test_trading_engine_order_state.py
=> PASS
```

Focused unit test:

```text
source ./env.sh >/tmp/hwistock-env-source.log && python -m unittest backend.tests.test_trading_engine_order_state
=> Ran 9 tests
=> OK
```

Cross-unit regression check:

```text
source ./env.sh >/tmp/hwistock-env-source.log && python -m unittest backend.tests.test_trading_engine_order_state backend.tests.test_strategy_risk_rulebook backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract
=> Ran 46 tests
=> OK
```

Full backend compile check:

```text
source ./env.sh >/tmp/hwistock-env-source.log && python -m py_compile $(find backend -name '*.py' -print)
=> PASS
```

Additional orchestrator probes:

```text
SOR risk gate => ok, requested_venue_route=SOR, risk_gate_venue_route=KRX,
  venue_resolution_status=normalized_sor_to_krx_for_foundation
AUTO_SESSION without hint => blocked with auto_session_requires_resolved_underlying_venue
AUTO_SESSION with session_venue_hint=NXT => ok, risk_gate_venue_route=NXT
cancel->accepted / fill->submitted / order->filled => rejected
helper->retrying / disabled_branch->failed => rejected
```

Rule-gate check:

```text
python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --all --preset fastapi-backend-rule-preset --json
=> overall status: fail due broader imported baseline findings
=> total findings: 92
=> UNIT-006 code findings: 0

python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --all --preset db-naming-rule-preset --json
=> overall status: fail due broader imported baseline findings
=> total findings: 25
=> UNIT-006 code findings: 0
```

Formatting / patch hygiene:

```text
git diff --check
=> PASS
```

Secret marker scan:

```text
known KIS paper credential/account/id markers in UNIT-006 changed code/evidence/docs
=> no matches
```

## 7. Carson Check Review Follow-Up

Accepted Carson follow-up findings remediated in this patch:

- P1 route-contract behavior gap:
  - `evaluateEntryRiskGate()` no longer forwards `SOR` / `AUTO_SESSION`
    directly into UNIT-004.
  - `SOR` is normalized to `KRX` for current foundation risk gating while
    preserving requested route metadata in UNIT-006 output.
  - `AUTO_SESSION` requires explicit `session_venue_hint=KRX|NXT`; otherwise
    the risk gate blocks with
    `auto_session_requires_resolved_underlying_venue`.
- P1 QA-004 / QA-009 proof gap:
  - focused tests now cover the claimed representable late states and explicit
    semantic mismatches (`order->filled`, `fill->submitted`,
    `cancel->accepted`) as rejection cases.
  - `representKisPaperEvidenceEvent()` now enforces event-kind-specific mapped
    state compatibility and forbids helper/fallback/balance order-state labels.
- P2 historical evidence classification:
  - MOD-005 and QA-006 frontmatter now mark old UNIT-006 evidence refs as
    `historical_before_rebaseline` or `superseded_by_code_import` instead of
    listing them as peer-current refs.

## 8. Check Review Acceptance

- Reviewer: Carson (`019e92fa-e099-72e0-898b-7ef259b3839e`)
- Route/model/reasoning: `codex multi-agent` / `gpt-5.4` / `high`
- Initial review output acceptance: accepted read-only review result with clean
  `REVIEW_RESULT: DONE` sentinel and no scope drift.
- Initial findings: P1 route-contract behavior gap, P1 QA-004/QA-009 proof gap,
  and P2 historical evidence metadata gap.
- Remediation worker: Heisenberg (`019e92ee-5691-7601-bf89-bb88df790f67`) under
  `DG-HWISTOCK-UNIT-006-GO-GPT54-20260604-REBASELINE-001-FOLLOWUP-CARSON-P1`.
- Rerun review output acceptance: accepted read-only rerun with clean
  `REVIEW_RESULT: DONE`, `FINDINGS: none`, `OPEN_P0_P1: no`, and
  `CLOSURE_LAYERS_VERDICT: sufficient`.
- Open P0/P1 after remediation: none.

## 9. Changed Files

- `backend/lib/trading_engine.py`
- `backend/tests/test_trading_engine_order_state.py`
- `docs/evidence/RUN-20260604_unit-006-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md`
- `docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md`
- `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md`
- `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`
- `docs/index.md`

## 10. Remaining Boundaries / Follow-Up

- Broker/KIS paper/live runtime integration remains out of scope until a later
  explicitly approved unit expands the adapter boundary.
- Submitted-or-later states are still representation metadata only for current
  foundation scope.
- Actual session-aware route execution, condition watching, position
  management, and reconciliation application remain future work.
