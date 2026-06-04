---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-004-go-check
stage: go-check
unit_id: HWISTOCK-UNIT-004
status: superseded_by_mywebtemplate_code_import
current_authority: false
superseded_by_rebaseline_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
superseded_reason: MyWebTemplate backend/frontend-web import removed the validated UNIT-004 implementation files from the current tree.
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md
module_refs:
  - docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md
strategy_decision_packet_ref: docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md
preflight_ref: docs/evidence/RUN-20260604_unit-004-go-preflight.md
created_at: 2026-06-04
environment: docs_only
route_class: implementation_worker
adapter: cursor-sdk-local
model: composer-2.5
reasoning: cursor-sdk-default-reasoning
orchestration_gate_id: DG-HWISTOCK-UNIT-004-GO-20260604-001
worker_output_acceptance: local_takeover_after_quarantined_worker_output
check_review_gate_id: DG-HWISTOCK-UNIT-004-CHECK-REVIEW-20260604-001
check_review_status: accepted_pass_after_p2_followup
final_fastapi_rule_gate_status: pass
final_db_rule_gate_status: pass
---

# UNIT-004 Go-Check Evidence

> Superseded notice: this evidence is historical after the 2026-06-04
> MyWebTemplate backend/frontend-web code import. It no longer proves the
> current tree because the referenced UNIT-004 implementation files are missing.

## 1. Verdict

PASS for the local-only Go implementation/check scope.

`HWISTOCK-UNIT-004` now has a stdlib-only strategy/risk rulebook skeleton with
approved config constants, deterministic entry-intent validators, and no-order
dry-run records only. This is not Prove evidence and does not authorize broker,
KIS, AI provider, paper order, live order, fake fill, fake balance, or fake PnL
behavior.

## 2. Route

- Stage: Go for HWISTOCK-UNIT-004, producing Go evidence for orchestrator Check.
- Route class: implementation_worker
- Adapter: cursor-sdk-local
- Model: composer-2.5
- Reasoning: cursor-sdk-default-reasoning
- Gate id: DG-HWISTOCK-UNIT-004-GO-20260604-001

## 3. Implemented Scope

- `backend/lib/strategy_risk.py`
  - approved UNIT-004 config constants: 2,000,000 KRW cash, reserve ratio 0.25,
    max holdings 5, -5% stop envelope, 10-20 minute hypothesis, hard 30 minute
    max, 1-5% per-position target band, first-pass candle/liquidity/chart gate
    constants, and no-order dry-run execution mode;
  - deterministic entry-intent validators for reserve breach, all-in, holdings
    cap, event-first chart confirmation, stale data, averaging-down add-ons,
    AI stop audit/stale/wide-stop rejection, and forbidden broker routing;
  - no-order dry-run record builder/validator without submitted/accepted/fill
    states or fake balance/PnL flags.
- `backend/tests/test_strategy_risk_rulebook.py`
  - focused unittest coverage for QA-001 through QA-016 where practical in local
    scope.

## 4. Boundary Evidence

- No implementation path reads environment variables or credential files.
- No implementation path imports network client modules.
- No implementation path imports broker, KIS, trading-engine, or order-routing
  modules beyond the explicit `no_order_dry_run` contract.
- Approved strategy parameters were not changed beyond the already-approved
  first-pass paper/sandbox planning defaults.
- No runtime artifacts were written under `data/`.

## 5. QA Row Coverage

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | Config constant `starting_capital_krw = 2000000`. |
| QA-002 | pass | All-in and reserve-floor breach rejections covered by validator tests. |
| QA-003 | pass | Candidate-only payload cannot include entry fields. |
| QA-004 | pass | Missing stop or venue route rejects entry. |
| QA-005 | pass | Config validation requires reserve, holdings cap, stop envelope, dry-run mode. |
| QA-006 | pass | Dry-run record captures candidate, entry, size, stop, target, hold, and rejection-reason fields without fill/PnL simulation. |
| QA-007 | deferred | Session 19:30/19:50 flattening remains future trading-engine scope. |
| QA-008 | pass | Averaging-down add-on rejection covered by validator test. |
| QA-009 | pass | Continuous re-entry without fresh signal id is rejected. |
| QA-010 | deferred | Stop-hit fill/retry logging remains future trading-engine scope. |
| QA-011 | pass | Target band label is `per_position_price_move`. |
| QA-012 | pass | Event-first without chart confirmation is rejected. |
| QA-013 | pass | Chart-first still requires reserve/holdings/risk checks. |
| QA-014 | pass | Forbidden broker adapters and dry-run boundary enforced. |
| QA-015 | pass | Missing/stale/unauditable/wide AI stop rejections covered. |
| QA-016 | pass | Config constants match approved first-pass packet defaults. |

## 6. Validation

Required validation:

```text
source ./env.sh && python -m unittest backend.tests.test_strategy_risk_rulebook backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract
```

Result:

```text
Ran 33 tests in 0.015s
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

- `backend/lib/strategy_risk.py`
- `backend/tests/test_strategy_risk_rulebook.py`
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`
- `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/index.md`
- `docs/evidence/RUN-20260604_unit-004-go-preflight.md`
- `docs/evidence/RUN-20260604_unit-004-go-check.md`

## 8. Denied Paths

- `/home/hwi/.config/hwistock/`
- `.env`, `env.sh` contents, broker credentials, tokens, account numbers
- unrelated docs/code outside the contract allowlist
- broker/KIS/AI network endpoints

## 9. Check Handoff

Orchestrator Check may verify:

- approved config constants remain unchanged;
- entry-intent validators reject reserve/holdings/stop/signal/broker violations;
- dry-run records remain no-order only;
- QA P0 rows pass in focused tests;
- no broker/AI/order authorization was introduced.

## 10. Worker Output Acceptance

Implementation worker:

- Gate id: `DG-HWISTOCK-UNIT-004-GO-20260604-001`.
- Route/model: `cursor-sdk-local` / `composer-2.5`.
- Wrapper acceptance state: `incomplete_worker_result`, because the streamed
  assistant output contained prose before the required `WORKER_RESULT` sentinel.
- Additional audit note: the worker-reported read set included prior Go evidence
  files outside the original `ALLOWED_READS`, so the raw worker result is
  quarantined for formal acceptance.
- Final acceptance path before Check review: documented orchestrator local
  takeover using local diff review, focused tests, compile check, profile-aware
  rule-gates, and evidence consistency checks as authoritative closure proof.

Check review:

- A focused read-only `codex-multi-agent` review completed under
  `DG-HWISTOCK-UNIT-004-CHECK-REVIEW-20260604-001` because this unit changes
  trading-risk controls.
- Route/model/reasoning: `codex-multi-agent` / `gpt-5.4` / `high`.
- Output acceptance: accepted. The reviewer returned only the required sentinel
  block, reported no scope drift, no redelegation, no runtime anomaly, and no
  P0/P1 findings.
- Reviewer P2 follow-up completed locally:
  - `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md` no longer frames
    the approved `minimum_reward_risk_ratio = 1.2` guard as deferred.
  - `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md` and
    `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md` now describe
    QA-006/AC-06 as no-order dry-run decision evidence, not fill/PnL evidence.
  - `backend/tests/test_strategy_risk_rulebook.py` directly asserts rejection
    when `fake_balance_generated` or `fake_pnl_generated` is set true.
- Check verdict after P2 follow-up: PASS for UNIT-004 local Go-Check scope.

## 11. Remaining Risks / Handoff Notes

- This is a skeleton foundation pass only. Trading-engine stop-hit logging,
  session flattening, scheduler loops, broker adapters, and Prove evidence remain
  future work.
- QA-007 and QA-010 are intentionally deferred to later trading-engine units.
- No approved strategy parameter was changed beyond implementing the approved
  first-pass paper/sandbox planning defaults.
