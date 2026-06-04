---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-006-trading-engine-order-state-set
type: evidence
name: UNIT-006 trading engine and order state Set
stage: set
environment: docs_only
status: pass_with_followups
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
unit_refs:
  - HWISTOCK-UNIT-006
module_refs:
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-004
profile_refs:
  - PROFILE-HWISTOCK
source_refs:
  - docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md
---

# UNIT-006 Trading Engine And Order State Set

## 1. Scope

This docs-only Set pass closed the first trading-engine/order-state contract
after the project direction changed away from internal fake broker execution.

No code was written. No broker network call, token request, WebSocket connection,
AI API call, or order placement was attempted.

## 2. Sources Checked

| source | use |
| --- | --- |
| `docs/profiles/PROFILE-HWISTOCK.md` | no internal fake broker, KIS KRX paper-first, no-order dry-run before broker approval |
| `docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md` | durable trading-engine/order-state module contract |
| `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md` | execution contract for the trading engine/order state unit |
| `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md` | QA scenario rows and evidence requirements |
| `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` | KIS paper-supported, constrained, unsupported, fallback, and live-verification API behavior |

## 3. Set Decisions

| decision | result |
| --- | --- |
| Condition schema | `condition_card/v0` JSON with required source ids, venue route, watch conditions, risk refs, entry intent, and exit plan. |
| First condition types | `price_cross`, `price_between`, `volume_spike`, `vwap_relation`, `moving_average_relation`, `orderbook_spread`, `source_freshness`, `event_context_present`, `risk_flag_absent`. |
| Natural language | AI/free text cannot become executable; vague conditions are rejected or downgraded to dashboard-only commentary. |
| State machine | Minimum states include `draft_intent`, `compiled_watch`, `eligible`, `blocked`, `dry_run_recorded`, `submitted`, `accepted`, `partial_fill`, `filled`, `cancel_requested`, `cancelled`, `rejected`, `retrying`, `failed`. |
| Pre-approval behavior | Stop at `dry_run_recorded`; record no-order dry-run only with no broker call, fake fill, fake balance, or simulated PnL. |
| First broker-backed adapter | Approved KIS KRX paper/mock-investment only. |
| NXT/SOR | Venue/session parameters over the same state machine. KIS paper NXT/SOR broker branches are disabled or explicit-fallback-only. |
| KIS paper capabilities | KRX order/realtime supported where references allow; NXT/SOR/integrated realtime and several helper APIs are unsupported and must use disabled/fallback records. |
| Reconciliation | Use supported KIS KRX paper order/fill/balance/realtime fill-notice data; use local state/fallback for paper-unsupported helper queries. |

## 4. Acceptance Closure

| ac_id | result | note |
| --- | --- | --- |
| AC-01 | set | AI output is non-executable and must compile to validated condition cards. |
| AC-02 | set | Ambiguous natural language is rejected or dashboard-only. |
| AC-03 | set | Buy gate requires capital, holdings, stale-data, venue, and stop-policy refs. Concrete values remain in the risk unit. |
| AC-04 | set | Explicit state machine is defined. |
| AC-05 | set | Pre-approval path is no-order dry-run only. |
| AC-06 | set | NXT/SOR are parameterized routes, not separate strategy families. |
| AC-07 | set | `condition_card/v0` schema is selected. |
| AC-08 | set | KIS paper capability flags are selected. |
| AC-09 | set | KIS paper reconciliation and fallback behavior are selected. |

## 5. Follow-Ups

- First-pass risk values are now closed by `HWISTOCK-UNIT-004`: minimum cash
  reserve ratio 0.25, maximum simultaneous holdings 5, and AI-assisted stop
  price capped by deterministic maximum -5% loss.
- Runtime calendar source hierarchy is closed by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`; missing or stale
  cached calendar makes trading/order loops idle.
- KIS paper account/product-code/HTS ID, actual paper balance, and current rate
  limits require a future explicitly approved broker-network smoke.
- Live NXT/SOR behavior requires a future real-account/support-confirmation gate.
- The broader Ready-Set bundle is still not implementation-ready until the
  completion gate and final go-check queue are closed.

## 6. Result

UNIT-006 docs-only Set: PASS WITH FOLLOW-UPS

Implementation remains blocked at the bundle level because
`RUN-20260602_ready-set-architecture.md` still has `implementation_ready: false`.
