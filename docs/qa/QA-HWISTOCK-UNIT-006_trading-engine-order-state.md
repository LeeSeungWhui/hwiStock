---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-006
type: qa_scenario
name: Trading engine and order state QA
unit_refs:
  - HWISTOCK-UNIT-006
module_refs:
  - HWISTOCK-MOD-005
profile_refs:
  - PROFILE-HWISTOCK
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
owner: hwi
updated_at: 2026-06-04
evidence_refs:
  - docs/evidence/RUN-20260602_unit-006-trading-engine-order-state-set.md
  - docs/evidence/RUN-20260604_unit-006-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md
  - path: docs/evidence/RUN-20260604_unit-006-go-preflight.md
    status: historical_before_rebaseline
  - path: docs/evidence/RUN-20260604_unit-006-go-check.md
    status: superseded_by_code_import
---

# Trading Engine And Order State QA

## Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | schema | Submit AI candidate card | Card is stored as non-executable until compiler accepts it | schema log |
| QA-002 | P0 | compiler | Submit vague condition like "looks good" | Compiler rejects or downgrades to dashboard-only | compiler log |
| QA-003 | P0 | policy | Submit candidate that violates cash-reserve floor, holdings cap, stale data, or missing stop | Buy gate rejects it | policy log |
| QA-004 | P0 | state | Feed recorded or fixture broker-event records for accepted, partial fill, reject, cancel, retry, and fail | Each state is represented and auditable without a broker-fill simulator | state log |
| QA-005 | P0 | adapter | Submit approved intent before KIS paper approval | Intent is recorded as no-order dry-run only; no broker call, simulated fill, or fake balance is produced | adapter/network log |
| QA-006 | P0 | route/capability | Submit KRX, NXT, SOR, and AUTO_SESSION route requests under dry-run and KIS paper-capability modes | Routes share the same state machine; SOR is normalized to KRX for foundation risk gating, AUTO_SESSION requires an explicit resolved underlying venue, and KIS paper-unsupported NXT/SOR broker branches stay disabled or explicit-fallback-only | route/capability log |
| QA-007 | P0 | schema | Submit `condition_card/v0` records with valid fields, unknown condition type, missing source ids, missing risk refs, and expired validity | Valid card is accepted for watch; invalid cards are rejected with explicit reasons | schema/validation log |
| QA-008 | P0 | capability | Inspect adapter capability registry for KIS paper | KRX order/realtime capabilities are true; NXT/SOR/integrated/helper unsupported capabilities are false and produce disabled/fallback records | capability log |
| QA-009 | P0 | reconciliation | Feed KIS KRX paper order/fill/balance/cancel fixture records and unsupported helper cases | Supported KRX paper event shapes are represented without applying broker state changes; unsupported helpers use local state or explicit fallback without live-only API calls | reconciliation log |
| QA-010 | P0 | foundation-scope | Run foundation-only Go smoke for `HWISTOCK-UNIT-006` | Implementation contains condition schema/compiler skeleton and no-order dry-run records only; it cannot submit orders, call KIS, simulate fills, simulate balances, compute fake broker PnL, or transition into submitted/accepted/fill states | smoke/network log |

## PASS / FAIL / BLOCKED Rules

- PASS: all selected foundation P0 rows pass and no AI output can bypass
  compiler/policy/order state. For first foundation Go, KIS adapter,
  reconciliation, and submitted-or-later execution behavior must remain disabled
  unless a later approved broker-network route explicitly expands scope.
- FAIL: vague AI text becomes an order, state transitions are missing, broker
  endpoints are reachable before approval, fake fills/balances are simulated in
  dry-run mode, or NXT/SOR broker calls are enabled in KIS paper/mock mode
  despite unsupported paper references.
- BLOCKED: condition schema, dry-run record shape, adapter capability boundary,
  or KIS paper reconciliation source is not selected.

## Evidence Requirements

- Condition schema validation log.
- Policy gate log with blocked reasons.
- Dry-run record proving `no_broker_call=true` and `no_simulated_fill=true`.
- Adapter capability registry output.
- KIS paper reconciliation event log using supported KRX paper data or explicit
  fallback records.
- Network/config proof that no KIS endpoint is reachable before broker-network
  approval.
- Foundation-only smoke proving no broker/KIS path, paper/live order path, fake
  fill, fake balance, fake PnL, or submitted-or-later state transition is
  reachable.
