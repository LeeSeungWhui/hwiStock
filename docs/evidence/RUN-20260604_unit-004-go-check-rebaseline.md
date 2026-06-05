---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-004-go-check-rebaseline
stage: go-check
unit_id: HWISTOCK-UNIT-004
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md
module_refs:
  - docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md
preflight_ref: docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md
created_at: 2026-06-04
environment: local_only
route_class: implementation_worker
route: codex multi-agent
adapter: multi_agent_v1
model: gpt-5.4
reasoning: high
orchestration_gate_id: DG-HWISTOCK-UNIT-004-GO-GPT54-20260604-REBASELINE-001
---

# UNIT-004 Go-Check Evidence — Rebaseline

## 1. Verdict

PASS. `HWISTOCK-UNIT-004` now has a current-authority rebaseline stdlib-only
strategy/risk rulebook skeleton in the imported MyWebTemplate backend tree.

The implementation is limited to deterministic config/constants, signal and
entry validators, watchlist-only candidate validation, no-order dry-run record
building/validation, and focused unittest coverage. It does not authorize or
implement broker/KIS calls, AI provider calls, adapter/account-affecting orders, fake broker
fills, fake balances, fake PnL, credential access, or runtime data artifacts.

Follow-up remediation on 2026-06-04 closed Darwin's accepted findings:

- P1: UNIT-004 local validator now rejects manual kill-switch/operator block
  activation from top-level or nested control flags.
- P2: no-order dry-run record boundary now mirrors config-level
  `paper_orders_allowed=false`, `live_orders_allowed=false`, and
  `fake_broker_allowed=false` constraints.

## 2. Route

- Stage: Go for `HWISTOCK-UNIT-004`, producing current-authority rebaseline Go evidence
- Route class: implementation_worker
- Route: `codex multi-agent`
- Adapter: `multi_agent_v1`
- Model: `gpt-5.4`
- Reasoning: `high`
- Gate id: `DG-HWISTOCK-UNIT-004-GO-GPT54-20260604-REBASELINE-001`

## 3. Implemented Scope

- `backend/lib/strategy_risk.py`
  - approved config constants: 2,000,000 KRW starting capital, cash-only mode,
    reserve ratio 0.25, max holdings 5, max stop envelope -5%, 10-20 minute
    hold hypothesis, 30-minute hard max, 1-5% target band, minimum reward/risk
    ratio 1.2, day-end flat metadata, stale signal/stop thresholds, and
    `no_order_dry_run` only boundaries
  - deterministic validators: config, signal bundle, candidate-only watchlist
    intent, entry intent, and dry-run record validation
  - explicit manual kill-switch / operator block rejection path for local
    pre-entry validation only
  - rejection coverage for reserve breach, all-in, holdings cap, event-first
    without chart confirmation, stale signal data, averaging down, continuous
    re-entry without fresh signal, missing/stale/unauditable/wider-than--5% AI
    stop, forbidden broker/KIS/operation/adapter/fake routes, and fake
    fill/balance/PnL flags
  - no-order dry-run record builder that records candidate, entry, size, stop,
    target, hold window, rejection reasons, and explicit no-adapter/no-unapproved-adapter/
    no-fake-broker boundary flags without fill/PnL simulation
- `backend/tests/test_strategy_risk_rulebook.py`
  - focused unittest coverage for local-scope QA rows and stdlib-only import boundary
  - follow-up fake-simulation remediation adds rejection coverage for nested
    `fake_*_generated` variants in entry intents and dry-run records

## 4. Boundary Evidence

- No implementation path reads env files, ignored template config files, or
  credential paths.
- No implementation path imports network clients, broker/KIS adapters, or
  runtime execution modules.
- No implementation path creates submitted/accepted/fill states, adapter-mode
  orders, fake broker output, fake balances, or fake PnL.
- No implementation path writes runtime artifacts under `data/`.
- Selected scope touched backend library/test files only; no MyWebTemplate
  sample/public/backend-route surface was introduced.

## 5. QA Row Coverage

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | Config constant `starting_capital_krw = 2000000` plus profile/module/unit alignment. |
| QA-002 | pass | `computeMaxOrderCashKrw()` and entry validation reject reserve breach and all-in sizing. |
| QA-003 | pass | `validateCandidateOnlyIntent()` enforces watchlist-only boundary and rejects entry fields. |
| QA-004 | pass | Missing stop or venue route rejects entry intent. |
| QA-005 | pass | Config validation requires reserve 0.25, holdings 5, -5% stop envelope, and dry-run-only boundaries. |
| QA-006 | pass | Dry-run record includes candidate, entry, size, stop, target, hold window, rejection reasons, and explicit no-adapter/no-unapproved-adapter/no-fake-broker boundary flags without fill/PnL simulation. |
| QA-007 | deferred | 19:30/19:50 flattening requires later trading-engine execution/log evidence. Config metadata remains present. |
| QA-008 | pass | Averaging-down add-on is rejected. |
| QA-009 | pass | Continuous re-entry without a fresh signal is rejected. |
| QA-010 | deferred | Stop-hit exit attempt/fill-retry logging belongs to later trading-engine execution/logging scope. |
| QA-011 | pass | Target band label remains `per_position_price_move`, not a daily account target. |
| QA-012 | pass | Event-first candidate without chart confirmation is rejected. |
| QA-013 | pass | Chart-first path remains valid without event context and still goes through risk checks. |
| QA-014 | pass | Broker/KIS/adapter-mode/fake route attempts, fake simulation flags including nested `fake_*_generated` variants, and dry-run boundary tampering are rejected. |
| QA-015 | pass | Missing, stale, unauditable, or wider-than--5% AI stop output is rejected. |
| QA-016 | pass | Current config exposes first-pass chart interval, stale threshold, chart-confirmation, target, and hold-window defaults. |

## 6. Validation

Compile check:

```text
source ./env.sh && python -m py_compile backend/lib/strategy_risk.py backend/tests/test_strategy_risk_rulebook.py
=> PASS
```

Focused unit test:

```text
source ./env.sh && python -m unittest backend.tests.test_strategy_risk_rulebook
=> Ran 19 tests
=> OK
```

Cross-unit regression check:

```text
source ./env.sh && python -m unittest backend.tests.test_strategy_risk_rulebook backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract
=> Ran 37 tests
=> OK
```

Full backend compile check:

```text
source ./env.sh && python -m py_compile $(find backend -name '*.py' -print)
=> PASS
```

Rule-gate check:

```text
python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --all --preset fastapi-backend-rule-preset --json
=> overall status: fail due broader imported baseline findings
=> total findings: 92
=> UNIT-004 code findings: 0

python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --all --preset db-naming-rule-preset --json
=> overall status: fail due broader imported baseline findings
=> total findings: 25
=> UNIT-004 code findings: 0
```

Formatting / patch hygiene:

```text
git diff --check
=> PASS
```

Secret marker scan:

```text
known KIS adapter credential/account/id markers in UNIT-004 changed code/evidence/docs
=> no matches
```

## 7. Check Review Acceptance

- Reviewer: Darwin (`019e92e1-b192-7543-8af4-4c07437c4884`)
- Route/model/reasoning: `codex multi-agent` / `gpt-5.4` / `high`
- Output acceptance: accepted read-only review result with clean
  `REVIEW_RESULT: DONE` sentinel and no scope drift.
- Findings:
  - P1 manual kill-switch/operator block gap: closed by Hilbert follow-up patch
    and local validation. Entry validation now rejects top-level and nested
    manual/operator/safety block activation.
  - P2 dry-run boundary gap: closed by Hilbert follow-up patch and local
    validation. Dry-run records now expose and validate no-adapter/no-unapproved-adapter/
    no-fake-broker boundary flags.
- Open P0/P1 after remediation: none.
- Closure layer verdict after remediation: sufficient for current UNIT-004
  scope, with QA-007 and QA-010 still explicitly deferred to UNIT-006.

## 8. Changed Files

- `backend/lib/strategy_risk.py`
- `backend/tests/test_strategy_risk_rulebook.py`
- `docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md`
- `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`
- `docs/index.md`

## 9. Remaining Boundaries / Follow-Up

- `HWISTOCK-UNIT-006` remains the later execution/logging owner for actual
  stop-hit exit attempts, 19:30 entry cutoff enforcement, 19:50 flattening, and
  any future dry-run state-machine integration.
- Broker/KIS/adapter/account-affecting routing remains denied outside explicitly approved later
  units.
- AI provider runtime calls remain denied; this rulebook only validates already
  normalized/local data.
