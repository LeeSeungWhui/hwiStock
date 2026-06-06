---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-014
type: unit
domain: backend_ops
name: KIS broker order execution and reconciliation
status: go_check_local_passed
implementation_status: go_check_passed_local_no_network_order_smoke_blocked
post_pro_reinforcement_status: corrective_gap_recorded
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-06
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-008
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-007
code_paths:
  include:
    - backend/service/kis_paper_adapter.py
    - backend/lib/kis_paper_continuous_runtime.py
    - backend/service/kis_paper_continuous_runner.py
    - backend/lib/paper_trading_ledger.py
    - backend/lib/trading_engine.py
    - backend/lib/strategy_risk.py
    - backend/tests/test_kis_paper_continuous_runner.py
    - ops/systemd/user/hwistock-kis-paper-runner.service
    - ops/systemd/user/hwistock-kis-paper-runner.timer
  exclude:
    - "**/*.env"
    - backend/config.ini
    - frontend-web/config.ini
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-operational-automated-trading-program.md
  - docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md
  - docs/evidence/RUN-20260605_operational-go-check-units-012-015.md
  - docs/evidence/RUN-20260606_kis-mode-gated-account-truth-go-check.md
  - docs/evidence/RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix.md
---

# KIS Broker Order Execution And Reconciliation

> Post-Pro corrective note (2026-06-05): this unit remains the first broker-order
> side-effect boundary. It cannot run broker order smoke until explicit owner
> approval, KRX regular-session preflight, adapter-only guard, and reconciliation
> evidence scope are all current.
>
> KIS paper/mock hotfix note (2026-06-06): paper/mock cannot rely on provider
> sellable/cancelable/realized-PnL/holiday helper TRs that local references mark
> unsupported. Runtime must skip those helper TRs as
> `skipped_provider_unsupported`, keep unsupported sellable truth as unknown, and
> fail closed where supported provider truth is required.

## 1. Goal

Turn the KIS broker adapter runner foundation into an idempotent broker execution loop
that watches approved trade-document-derived `paper_order_intent/v0` records,
places only KRX broker orders, and reconciles broker-visible adapter-visible state.

This unit is the first place where approved KIS broker orders may be placed
during an explicitly scoped Go/Prove side-effect run. Local no-network
preflight/idempotency/realtime-exit Go-Check passed on 2026-06-05, but KIS broker adapter
order transport and reconciliation smoke remains blocked until approved market
and account conditions are present. Unapproved adapter operation remains forbidden.

## 2. Included Scope

- Consume the UNIT-013 intent queue generated from Flash trade documents and
  fresh KIS/source context.
- On each newly accepted trade document, cancel previous unfilled `WAIT_BUY`
  broker orders unless the new document explicitly renews the same wait and all
  gates still pass.
- Enforce a final risk/order preflight immediately before any broker call.
- Consume only schema-valid, manifest-complete, idempotent intents.
- Re-read current portfolio/order-state immediately before any broker call:
  holdings, available cash, pending orders, active exits, position locks,
  cooldowns, and already-consumed trade-document ids.
- Reject conflicts even if the Flash document looked valid when it was written.
- Acquire the account/symbol lock or equivalent single-writer guard before
  reservation and broker submission.
- Maintain reservation accounting for pending cash, pending quantity, holding
  slots, active exits, and consumed trade docs.
- Monitor held symbols continuously with KIS realtime price/orderbook context
  for stop-loss, take-profit, and trailing-stop execution; do not wait for the
  next Flash document to protect exits.
- Use write-ahead intent logging before broker submission and reconcile KIS
  order/fill inquiry before retry after timeout, crash, or ambiguous result.
- Place broker cash orders only through the configured KIS adapter domain for the
  active investment mode.
- Support cancel/modify only after provider cancelable-order truth is available
  in the active mode and local pending-order state agrees; paper/mock skips the
  provider-unsupported cancelable query and fails closed on ambiguity.
- Run daily order/fill lookup, balance, and buyable reconciliation in paper/mock;
  sellable, cancelable-order, realized-PnL, and holiday/provider-calendar
  cross-checks remain skipped until a supported mode is proven.
- Store masked broker order ids/account aliases only when safe.
- Calculate system cash/position/exposure/PnL from actual broker events, not fake
  broker data.
- Prevent duplicate submissions across service restart/timer replay.
- Emit classified broker errors without turning them into fake success.

## 3. Excluded Scope

- Unapproved domain calls.
- SOR broker-adapter routing.
- NXT broker routing while the runtime is in paper/mock mode.
- Broker account values.
- Fake broker fills, balances, positions, or PnL.
- AI/provider calls.
- Public dashboard exposure.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result |
| --- | --- | --- | --- |
| AC-01 | P0 | Adapter domain only | Unapproved/unknown KIS hosts fail before transport. |
| AC-02 | P0 | Intent consumption is idempotent | The same active intent cannot submit duplicate broker orders. |
| AC-03 | P0 | Final risk preflight blocks unsafe orders | Kill switch, calendar, stale data, holdings cap, reserve floor, and invalid venue block before KIS call. |
| AC-04 | P0 | KRX broker order path works or fails classified | Broker order attempts produce sanitized success/error evidence with no raw secrets. |
| AC-05 | P0 | Reconciliation is broker-evidence-backed | Ledger state derives from KIS broker order/fill/balance/buyable/sellable/cancelable evidence. |
| AC-06 | P0 | Disabled branches do not call broker | Paper/mock NXT and all SOR branches are disabled/fallback-only; provider helper truth is used only through approved query endpoints. |
| AC-07 | P0 | Restart does not duplicate orders | Timer/service restart around pending intents preserves idempotency. |
| AC-08 | P0 | Portfolio conflicts are rechecked at execution | Duplicate held-symbol buys, pending duplicate orders, conflicting exits, and already-consumed trade-doc ids block before KIS submission. |
| AC-09 | P0 | Ambiguous submit is reconciled before retry | Timeout/crash/unknown submit state cannot resubmit until KIS order/fill inquiry proves no matching order exists. |
| AC-10 | P0 | Adapter-only guard aborts before transport | Unknown/unapproved domain, broker account profile, unsupported TR ID, or unsupported venue route fails before network transport. |
| AC-11 | P0 | Pending WAIT_BUY cleanup is deterministic | A superseding trade document cancels old unfilled waits unless explicitly renewed. |
| AC-12 | P0 | Exits are monitored in realtime | Stop-loss, take-profit, and trailing-stop checks run from current KIS realtime/quote state and do not depend on the next Flash tick. |

## 5. Go Notes

Actual broker-network calls are side effects. Go/Prove must record the preflight
time, adapter/unapproved domain guard, secret redaction status, and whether the market
was open. Market-closed broker rejections are valid classified evidence but not
proof that an order can fill.
