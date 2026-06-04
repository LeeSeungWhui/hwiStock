---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-006
type: unit
domain: backend
name: Trading engine and order state
status: set
priority: P0
source_of_truth: user_intent
work_class: product_api
owner: hwi
updated_at: 2026-06-03
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-004
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md
evidence_refs:
  - docs/evidence/RUN-20260602_unit-006-trading-engine-order-state-set.md
links:
  - HWISTOCK-MOD-005
---

# Trading Engine And Order State

## 1. Goal

Define the deterministic trading engine contract that turns validated candidate
cards into watched conditions, manages positions, and routes approved intents
through an explicit order state machine.

## 2. Included Scope

Foundation-only first Go may implement only:

- `condition_card/v0` schema and validation.
- Candidate-card to deterministic condition compiler skeleton.
- No-order dry-run decision recorder.
- Order-state enum/transition skeleton up to `dry_run_recorded`.
- Route metadata for KRX/NXT/SOR as no-order dry-run fields only.
- Network-boundary proof that no broker/KIS, paper/live order, fake fill, fake
  balance, fake PnL, or AI provider path is reachable.

The broader Set contract below remains future scope until later explicit owner
approval and broker-network gates close.

- Candidate-card to condition compiler.
- Condition watcher for price, volume, VWAP/indicator, source freshness, and
  risk flags.
- Buy/sell eligibility gate.
- Position manager.
- Order state machine.
- No-order dry-run recorder for pre-KIS-paper approval validation.
- Future adapter boundary for approved KIS KRX paper/mock API.
- Venue/session route parameter handling for KRX, NXT, and SOR on the same
  deterministic order-state semantics.
- Explicit disabled/fallback behavior for KIS paper-unsupported NXT/SOR broker
  branches during KIS paper runs.
- `condition_card/v0` JSON schema.
- `no_order_dry_run` record schema.
- KIS paper adapter capability flags.
- KIS KRX paper order/fill/reconciliation state contract.

## 3. Excluded Scope

- Live orders.
- Direct AI order placement.
- KIS network calls before verification.
- Dashboard UI.
- Final alpha formula.
- Concrete risk parameter values; this unit requires references to configured
  values but does not select them.
- Live NXT/SOR broker verification.
- KIS paper adapter implementation in the foundation-only first Go queue.
- `submitted`, `accepted`, `partial_fill`, `filled`, cancel/retry, or
  reconciliation implementation in the foundation-only first Go queue.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | AI output is non-executable | Candidate cards must be compiled/validated before watching | schema/review | QA-001 |
| AC-02 | P0 | Ambiguous conditions are rejected | Natural-language-only buy conditions do not become orders | compiler test | QA-002 |
| AC-03 | P0 | Buy gate is deterministic | Capital, holdings, stale-data, venue, and stop policy must pass | policy test | QA-003 |
| AC-04 | P0 | Order state is explicit | partial fill, reject, cancel, retry, and fail states are representable | state test | QA-004 |
| AC-05 | P0 | Pre-approval path is dry-run only | Approved intents are recorded without broker calls, simulated fills, or fake balances before KIS paper approval | adapter test | QA-005 |
| AC-06 | P0 | NXT/SOR are parameterized, not separate strategies | KRX/NXT/SOR routes use the same state machine; KIS paper-unsupported NXT/SOR branches are disabled or explicit-fallback-only | route/capability test | QA-006 |
| AC-07 | P0 | Condition schema is deterministic | `condition_card/v0` accepts only known condition types and required source/risk refs | schema test | QA-007 |
| AC-08 | P0 | KIS paper capabilities are explicit | Adapter capability flags expose KRX-only paper support and unsupported NXT/SOR/helper APIs | capability test | QA-008 |
| AC-09 | P0 | KIS paper reconciliation is auditable | Order, fill, balance, cancel, retry, disabled-branch, and fallback events are represented from supported KIS paper data or explicit local fallback | reconciliation test | QA-009 |

## 5. Set Decisions

### 5.1 Condition Card Schema

Use `condition_card/v0` JSON. Required fields:

- `candidate_id`
- `symbol`
- `source_ids`
- `created_at_kst`
- `valid_until_kst`
- `venue_route`: `KRX`, `NXT`, `SOR`, or `AUTO_SESSION`
- `watch_conditions`
- `risk_refs`
- `entry_intent`
- `exit_plan`

Allowed first-pass `watch_conditions.type` values:

- `price_cross`
- `price_between`
- `volume_spike`
- `vwap_relation`
- `moving_average_relation`
- `orderbook_spread`
- `source_freshness`
- `event_context_present`
- `risk_flag_absent`

Reject unknown condition types, missing source ids, missing risk refs, expired
cards, and vague natural-language-only triggers.

### 5.2 State Machine

Minimum states:

- `draft_intent`
- `compiled_watch`
- `eligible`
- `blocked`
- `dry_run_recorded`
- `submitted`
- `accepted`
- `partial_fill`
- `filled`
- `cancel_requested`
- `cancelled`
- `rejected`
- `retrying`
- `failed`

Pre-KIS-paper path must stop at `dry_run_recorded`. `submitted` and later states
are allowed only for an explicitly approved KIS KRX paper adapter or later
approved live adapter.

Foundation-only first Go must not implement executable transitions beyond
`dry_run_recorded`. Later states may be represented as enum constants or
documentation comments only if tests prove no broker/order path can reach them.

### 5.3 No-Order Dry-Run Record

Required fields:

- `mode`: `no_order_dry_run`
- `candidate_id`
- `condition_card_id`
- `decision`: `would_watch`, `would_enter`, `would_exit`, or `blocked`
- `would_venue_route`
- `would_order_side`
- `would_order_price_type`
- `would_cash_amount_krw`
- `risk_gate_result`
- `blocked_reasons`
- `no_broker_call=true`
- `no_simulated_fill=true`
- `created_at_kst`

Dry-run records are decision evidence only. They are not paper-trading evidence,
broker evidence, fill evidence, or PnL evidence.

### 5.4 KIS Paper Capability Flags

The first KIS paper adapter must expose:

- `supports_paper_krx_order=true`
- `supports_paper_nxt_order=false`
- `supports_paper_sor_order=false`
- `supports_paper_krx_realtime=true`
- `supports_paper_nxt_realtime=false`
- `supports_paper_integrated_realtime=false`
- `supports_paper_cancel_order=true`
- `supports_paper_cancelable_query=false`
- `supports_paper_sellable_quantity_query=false`
- `supports_paper_realized_pnl_query=false`
- `supports_paper_holiday_query=false`

Unsupported capabilities produce `disabled_branch` or `local_fallback` records;
they must not call live-only APIs.

### 5.5 KIS Paper Reconciliation

Use supported KIS KRX paper sources for broker-backed evidence:

- cash order
- modify/cancel order
- daily order/fill lookup
- balance
- buyable amount
- KRX realtime trade price
- KRX realtime order book
- realtime fill notice

Use local state or explicit fallback records for paper-unsupported helper APIs:

- modify/cancel eligible-order query
- sellable quantity query
- realized PnL query
- holiday/open-day query from local cached KRX/NXT calendar, with KIS
  `국내휴장일조회` as later-approved broker cross-check only
- NXT realtime
- integrated realtime
- KRX/NXT/integrated market operation status

### 5.6 Go Boundary

This unit is Set-ready for implementation planning but still cannot start Go
until the broader Ready-Set completion gate marks `implementation_ready: true`
and the row appears in an approved `go_check_queue`.

## 6. Remaining Open Questions

- Strategy alpha/signal formula, chart setup/source, candle intervals, liquidity
  behavior, and market-alert source remain outside this unit and are packaged in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.
  First-pass risk values are closed by `HWISTOCK-UNIT-004`: minimum cash reserve
  ratio 0.25, maximum simultaneous holdings 5, and AI-assisted stop price capped
  by deterministic maximum -5% loss. Runtime calendar source hierarchy is closed
  by `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`.
- Exact KIS paper account balance, current rate limits, account/product-code
  shape, and HTS ID must be verified through a future explicitly approved
  broker-network smoke before the KIS paper adapter is enabled.
- Live NXT/SOR behavior remains a later real-account/support-confirmation gate.
