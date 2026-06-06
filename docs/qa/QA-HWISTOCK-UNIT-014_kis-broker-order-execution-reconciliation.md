---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-014
type: qa_scenario
name: KIS broker order execution and reconciliation QA
unit_refs:
  - HWISTOCK-UNIT-014
  - HWISTOCK-UNIT-016
module_refs:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-008
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-007
profile_refs:
  - PROFILE-HWISTOCK
status: go_check_local_passed_order_smoke_blocked
owner: hwi
updated_at: 2026-06-05
evidence_refs:
  - docs/evidence/RUN-20260605_operational-go-check-units-012-015.md
  - docs/set/READY-SET-CORRECTION-20260606_mode-schedule-ai-loop-followup.md
---

# KIS Adapter Order Execution And Reconciliation QA

## 1. Purpose

Prove that approved order intents can flow through KIS KRX adapter execution and
reconciliation without unapproved endpoints, duplicate orders, or fake broker state.

## 2. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | domain | Configure unapproved/unknown KIS host | Adapter fails before transport | adapter test |
| QA-002 | P0 | no-network | Run runner without adapter network enable | Status is `idle_paper_network_disabled`; no broker call occurs | CLI output |
| QA-003 | P0 | final-risk | Feed unsafe approved-intent fixtures | Kill/calendar/stale/reserve/holdings/venue blocks before KIS call | risk log |
| QA-004 | P0 | adapter-order | Run bounded KRX broker order when market/env allow | Order succeeds or returns classified adapter error; no raw secret/response stored | sanitized smoke |
| QA-005 | P0 | reconcile | Run daily order/fill/balance/buyable/sellable/cancelable reconciliation | Ledger fields derive from KIS adapter evidence and masked account aliases | reconciliation report |
| QA-006 | P0 | restart | Restart timer around pending intent | Duplicate broker submission is prevented | idempotency smoke |
| QA-007 | P0 | mode-gate | Request NXT/SOR/integrated/helper branches under paper/mock and real investment modes | Paper/mock NXT and all SOR branches write fallback/disabled records; integrated market-data and provider helper truth use only approved query/read endpoints | capability log |
| QA-008 | P0 | conflict | Change portfolio/order state after intent creation but before execution | Executor rechecks holdings/pending/exits/consumed trade-doc ids and blocks conflicting KIS submission | execution log |
| QA-009 | P0 | ambiguous-submit | Simulate timeout/crash after broker submit may have succeeded | Executor records `SUBMIT_UNKNOWN`, reconciles KIS order/fill inquiry, and does not retry until no matching broker order is proven | reconciliation log |
| QA-010 | P0 | reservation | Feed intent where pending orders would breach cash reserve or holding-slot cap | Reservation gate blocks before KIS transport | risk log |
| QA-011 | P0 | adapter-bound | Configure broker account profile, unknown domain, unsupported TR ID, or unsupported venue route | Runtime aborts before network transport with sanitized adapter-bound guard error | startup log |
| QA-012 | P0 | state-machine | Force illegal order-state transitions | Illegal transition is rejected and valid transition path remains auditable | state log |
| QA-013 | P0 | supersede-wait | Accept a new trade document while a previous WAIT_BUY remains unfilled | Previous unfilled wait is canceled unless the new document explicitly renews it and final gates still pass | execution log |
| QA-014 | P0 | realtime-exit | Move realtime/quote fixture through stop-loss, take-profit, and trailing-stop thresholds for a held symbol | Executor emits the appropriate adapter exit decision from realtime state without waiting for the next Flash tick | execution log |
| QA-015 | P0 | paper-window | Attempt paper/mock KRX broker submit at 14:59, 15:00, 15:10, and 15:30 KST | 14:59 may proceed only if every other gate passes; 15:00 and later reject before broker transport as outside the paper/mock investment/order window | execution log |
| QA-016 | P0 | dynamic-exposure | Feed an otherwise valid broker request that would exceed authoritative 75% total-deposit exposure after pending buys | Executor rejects before KIS transport with a dynamic exposure cap reason | risk log |

## 3. PASS / FAIL / BLOCKED Rules

- PASS: adapter KRX order/reconciliation is proven or safely classified, all hard
  safety gates hold, superseded waits are canceled, realtime exits are monitored,
  and restart does not duplicate orders.
- FAIL: unapproved domain reachable, fake broker state created, disabled branch
  calls KIS, raw secrets leak, duplicate orders are submitted, or execution
  submits an order that conflicts with current holdings, pending orders, active
  exits, cooldowns, or already-consumed trade documents, or ambiguous submit
  paths can retry before broker reconciliation, or exits wait for the next Flash
  document instead of realtime risk thresholds, or paper/mock broker submit is
  attempted at or after `15:00 KST`.
- BLOCKED: KIS broker-adapter env unavailable, market closed for order-specific smoke, or
  current KIS adapter limits/rate state prevent safe bounded execution.
