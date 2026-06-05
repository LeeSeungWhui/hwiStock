---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-004-strategy-risk-rulebook-set
type: evidence
name: Strategy risk rulebook Set pass
stage: set
environment: docs_only
status: pass_with_followups
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
implementation_ready: false
---

# Strategy Risk Rulebook Set Pass

## 1. Scope

This docs-only Set pass closes the first minimal strategy/risk policy for
hwiStock before any trading implementation.

## 2. Decisions

- Starting capital remains 2,000,000 KRW cash.
- Capital mode remains cash-only; credit, margin, 미수, borrowed funds, and
  leveraged capital remain forbidden.
- Maximum simultaneous holdings: 5.
- No fixed per-symbol maximum allocation is used in the first policy.
- Every order must preserve `minimum_cash_reserve_ratio = 0.25` of total
  capital.
  - 2,000,000 KRW capital baseline keeps at least 500,000 KRW unallocated.
  - 10,000,000 KRW KIS adapter target keeps at least 2,500,000 KRW unallocated.
- Stop policy is AI-assisted per entry: AI may propose a concrete stop price
  from the normalized signal bundle.
- Deterministic risk gate caps accepted stop prices at maximum -5% loss from
  average entry, before fees/taxes/slippage.
- Missing, stale, unauditable, or wider-than--5% AI stop output rejects entry.
- There is no first-pass deterministic fallback stop when AI stop output is
  unavailable or invalid.
- Broad account-level loss halt, max trades, and cooldown remain excluded for
  the first minimal policy unless later adapter evidence changes this.

## 3. Evidence

- `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md` is marked `set` and
  records the reserve-floor, holdings, and AI stop policy.
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md` is marked `set` and
  records acceptance criteria and implementation boundaries.
- `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md` is marked `set` and
  adds QA coverage for reserve-floor sizing and AI stop rejection.
- `docs/profiles/PROFILE-HWISTOCK.md`, `docs/index.md`, and
  `docs/evidence/RUN-20260602_ready-set-architecture.md` were updated to reflect
  the closed first-pass risk policy.

## 4. Boundaries

- No broker API, AI API, database, or network call was made.
- No order placement, broker order, simulated fill, fake balance, or PnL claim was
  created.
- This does not approve account-affecting operation or account-affecting operation.
- Exact first-pass alpha/signal formula, chart setup/source, candle intervals,
  liquidity behavior, and market-alert source are packaged for approval in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`. One-week
  operation pass criteria are closed by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`.

## 5. Verdict

UNIT-004 Set: PASS WITH FOLLOW-UPS.

Implementation readiness: BLOCKED until Ready-Set completion gate and remaining
bundle items are closed.
