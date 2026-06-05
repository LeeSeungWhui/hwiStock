---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-006-go-check
stage: go-check
unit_id: HWISTOCK-UNIT-006
status: superseded_by_mywebtemplate_code_import
current_authority: false
superseded_by_rebaseline_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
superseded_reason: MyWebTemplate backend/frontend-web import removed the validated UNIT-006 implementation files from the current tree.
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md
module_refs:
  - docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md
  - docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md
  - docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md
preflight_ref: docs/evidence/RUN-20260604_unit-006-go-preflight.md
created_at: 2026-06-04
route_class: implementation_worker
adapter: cursor-sdk-local
model: composer-2.5
reasoning: cursor-sdk-default-reasoning
orchestration_gate_id: DG-HWISTOCK-UNIT-006-GO-20260604-001
worker_output_acceptance: local_takeover_after_quarantined_worker_output
check_review_gate_id: DG-HWISTOCK-UNIT-006-CHECK-REVIEW-20260604-001
check_review_status: pending_orchestrator_check
final_fastapi_rule_gate_status: pass
final_db_rule_gate_status: pass
---

# UNIT-006 Go-Check Evidence

> Superseded notice: this evidence is historical after the 2026-06-04
> MyWebTemplate backend/frontend-web code import. It no longer proves the
> current tree because the referenced UNIT-006 implementation files are missing.

## 1. Verdict

PASS for the foundation-only Go implementation/check scope.

`HWISTOCK-UNIT-006` now has a stdlib-only trading engine/order-state skeleton with
`condition_card/v0` validation, deterministic condition compilation, pre-approval
order-state transitions through `dry_run_recorded`, UNIT-006 no-order dry-run
decision records, venue-route metadata, and KIS adapter capability flags. This is
not Prove evidence and does not authorize broker, KIS network calls, AI provider
calls, broker orders, account-affecting orders, executable submitted/accepted/fill transitions,
fake fills, fake balances, fake PnL, or broker-backed adapter reconciliation.

## 2. Route

- Stage: Go for HWISTOCK-UNIT-006, producing Go evidence for orchestrator Check.
- Route class: implementation_worker
- Adapter: cursor-sdk-local
- Model: composer-2.5
- Reasoning: cursor-sdk-default-reasoning
- Gate id: DG-HWISTOCK-UNIT-006-GO-20260604-001

## 3. Implemented Scope

- `backend/lib/trading_engine.py`
  - `condition_card/v0` validator for known watch types, source ids, risk refs,
    expiry, and vague natural-language-only rejection;
  - deterministic `compileConditionCard` skeleton producing `compiled_watch/v0`
    without broker requests or executable orders;
  - pre-approval order-state transition validator and chain ending at
    `dry_run_recorded` with post-approval states blocked in foundation scope;
  - UNIT-006 `no_order_dry_run` decision recorder/validator with
    `no_broker_call=true` and `no_simulated_fill=true`;
  - venue-route metadata and KIS adapter capability flags with NXT/SOR/helper
    branches disabled or `local_fallback` only;
  - fixture-only KIS adapter evidence-shape representation and unsupported-helper
    records without network calls or broker state application.
- `backend/tests/test_trading_engine_order_state.py`
  - focused unittest coverage for QA-001 through QA-010 in local scope.
- Updated UNIT-006, MOD-005, QA-006, and index docs with Go-Check status.

## 4. Boundary Evidence

- No implementation path reads environment variables or credential files.
- No implementation path imports network client modules.
- No implementation path places adapter/account-affecting orders or transitions into
  `submitted`, `accepted`, `partial_fill`, `filled`, cancel/retry, or
  reconciliation execution.
- No fake fill, fake balance, or fake PnL generation in dry-run mode.
- Approved UNIT-004 strategy/risk parameters were referenced, not changed.
- No runtime artifacts were written under `data/`.

## 5. QA Row Coverage

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | `isAiCandidateNonExecutable` remains true until `compileConditionCard` output exists. |
| QA-002 | pass | Vague natural-language-only watch conditions are rejected. |
| QA-003 | pass | `evaluateEntryRiskGate` delegates to UNIT-004 reserve/holdings/stale-data validators. |
| QA-004 | pass | `representBrokerEventState` represents accepted/partial_fill/reject/cancel/retry/fail without simulation. |
| QA-005 | pass | `buildNoOrderDryRunDecisionRecord` enforces `no_broker_call` and `no_simulated_fill`. |
| QA-006 | pass | KRX/NXT/SOR share transition semantics; NXT/SOR KIS adapter branches are `disabled_branch`. |
| QA-007 | pass | Valid/invalid `condition_card/v0` cases covered by validator tests. |
| QA-008 | pass | `loadKisPaperCapabilityFlags` exposes KRX-only adapter support and false NXT/SOR/helper flags. |
| QA-009 | pass | Supported KRX order/fill/balance/cancel fixture event shapes are represented without applying broker state changes; order/fill/cancel require explicit mapped order states, balance cannot be mislabeled as an order state, and unsupported helpers use `local_fallback`. |
| QA-010 | pass | Module has no network imports; executable post-approval transitions are blocked. |

## 6. Validation

Required validation:

```text
source ./env.sh && python -m unittest backend.tests.test_trading_engine_order_state backend.tests.test_strategy_risk_rulebook backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract
```

Result:

```text
Ran 49 tests in 0.021s
OK
```

Required compile validation:

```text
source ./env.sh && python -m py_compile $(find backend -name '*.py' -print)
```

Result:

```text
PASS
```

Required rule-gate validation:

```text
source ./env.sh && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile /data/workspace/My/hwiStock/docs/profiles/PROFILE-HWISTOCK.md --preset fastapi-backend-rule-preset --all --fail-on-warn
```

Result:

```text
Status: pass
Scanned files: 13
Findings: error=0 warning=0 info=0
```

```text
source ./env.sh && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile /data/workspace/My/hwiStock/docs/profiles/PROFILE-HWISTOCK.md --preset db-naming-rule-preset --all --fail-on-warn
```

Result:

```text
Status: pass
Findings: error=0 warning=0 info=0
```

## 7. Changed Files

- `backend/lib/trading_engine.py`
- `backend/tests/test_trading_engine_order_state.py`
- `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md`
- `docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md`
- `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md`
- `docs/index.md`
- `docs/evidence/RUN-20260604_unit-006-go-check.md`

## 8. Denied Paths

- `/home/hwi/.config/hwistock/`
- `.env`, `env.sh` contents, broker credentials, tokens, account numbers
- runtime `data/` artifacts
- broker/KIS/AI network endpoints
- adapter/account-affecting order placement and executable post-approval transitions
- fake broker, fake fill, fake balance, fake PnL generation

## 9. Worker Output Acceptance

Implementation worker:

- Gate id: `DG-HWISTOCK-UNIT-006-GO-20260604-001`.
- Route/model: `cursor-sdk-local` / `composer-2.5`.
- Wrapper acceptance state: `incomplete_worker_result`, because the streamed
  assistant output contained prose before the required `WORKER_RESULT` sentinel.
- Additional audit note: the worker-reported read set included prior Go evidence
  and unrelated module files outside the original `ALLOWED_READS`, so the raw
  worker result is quarantined for formal acceptance.
- Local takeover: the orchestrator reviewed the diff, found a foundation-boundary
  issue where KRX adapter fixture handling looked like broker state application,
  and corrected it to representation-only output with `no_broker_call=true` and
  `state_update_executed=false`.
- Current closure basis before Check review: local diff review, focused tests,
  compile check, profile-aware rule-gates, and evidence consistency checks.
- Worker audit artifacts for this run:
  - contract: `/tmp/hwistock-unit006-worker/contract.md`
  - contract sha256:
    `6ec6f3a306d88c2333986694f5bf1182a2a5dd1e93ad51db6e1b32862dda47c9`
  - transcript: `/tmp/hwistock-unit006-worker/transcript.jsonl`
  - transcript sha256:
    `843ca614da682c6a08e542978350cb5294130743050bc302ac70a8dc9d217f53`
  - out-of-allowlist worker reads observed in the sentinel/transcript:
    `docs/evidence/RUN-20260604_unit-004-go-check.md`,
    `docs/evidence/RUN-20260604_unit-008-go-check.md`,
    `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`,
    `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`, and
    `docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md`.

Check handoff:

- A focused read-only Check review is still required because this unit touches
  trading engine/order-state boundaries.

## 10. Initial Check Review Follow-Up

Initial Check review under `DG-HWISTOCK-UNIT-006-CHECK-REVIEW-20260604-001`
reported:

- P1: QA-009 overclaimed order/fill/balance/cancel fixture coverage and the
  implementation could default missing `mapped_order_state` to `accepted`.
- P2: worker-output quarantine/local-takeover evidence lacked an auditable
  transcript/contract reference in the evidence chain.

Follow-up applied:

- `representKisPaperEvidenceEvent()` now requires explicit allowed mapped order
  states for order/fill/cancel fixture events.
- Balance fixture evidence is represented without any order state and rejects
  attempts to label balance as an order state.
- `backend/tests/test_trading_engine_order_state.py` now covers KRX order, fill,
  balance, and cancel fixture event shapes plus missing mapped-state rejection.
- Worker contract/transcript paths and sha256 values are recorded above.

Check review rerun is required before final Check closure.
