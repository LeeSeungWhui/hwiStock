---
schema_version: hwi.evidence/v0
id: RUN-20260602-strategy-risk-rulebook
type: evidence
name: Strategy risk rulebook evidence
unit_refs:
  - HWISTOCK-UNIT-004
module_refs:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
profile_refs:
  - PROFILE-HWISTOCK
status: draft
created_at: 2026-06-02
environment: docs_only
---

# Strategy Risk Rulebook Evidence

## Summary

Created the initial docs-only strategy/risk rulebook for `hwiStock` using the
owner-confirmed starting capital of 2,000,000 KRW cash.

## Superseded Draft Risk Defaults

This section records an earlier planning snapshot. The fixed deployed-cash,
per-symbol cash, pilot entry size, daily loss, losing-streak, and daily trade
count values below are superseded by the later Set contracts in
`docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`,
`docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`, and
`docs/evidence/RUN-20260602_unit-004-strategy-risk-rulebook-set.md`.

Current authoritative first-pass allocation policy:

- No fixed per-symbol maximum allocation.
- Every order must preserve `minimum_cash_reserve_ratio = 0.25` of total
  capital.
- Maximum simultaneous holdings: 5.
- All-in single-stock deployment remains forbidden by default.

Historical snapshot values:

- Starting capital: 2,000,000 KRW cash.
- All-in single-stock deployment: forbidden by default.
- Maximum simultaneous deployed cash: 1,000,000 KRW.
- Maximum cash per symbol: 400,000 KRW.
- Default pilot entry size: 200,000 KRW.
- Maximum risk per trade: 10,000 KRW.
- Maximum daily realized loss: 40,000 KRW.
- Maximum consecutive losing trades: 3.
- Maximum completed trades per day: 5.
- Strategy tempo hypothesis: 10-20 minute fast intraday scalping/momentum.
- Candidate target band: per-position 1-5% price movement/take-profit candidate,
  subject to reward/risk validation.
- The 1-5% band is not a daily account return target.
- Signal model: combine news/disclosure context and chart/market-data
  confirmation. Event-first candidates require chart confirmation by default;
  chart-first candidates should search for related official/news context and
  must still pass all risk checks.
- Continuous re-entry is forbidden: every entry still needs a fresh signal,
  cooldown pass, daily cap pass, and risk check pass.
- No overnight positions by default; new entries stop by 19:30 KST and positions
  are flat by 19:50 KST unless a future approved unit changes this.

## Source Notes

- KRX and NXT official pages remain the current source basis for the initial
  KRX/NXT session envelope used by the scheduler docs.
- DART/OpenDART and KRX KIND-style official disclosure sources should be
  preferred for future disclosure registries, but the exact allowlist is still
  open.
- Chart signals should use approved raw market data such as broker feeds, KRX
  data products, or another licensed market-data provider. Rendered chart image
  scraping is not a source of truth.
- This evidence does not verify profitability. It only records the current
  software risk-control contract.

## Follow-Up

- Approve or reject
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md` before full
  strategy Go.
- After adapter/backtest evidence, refine liquidity, take-profit, trailing, and
  latency parameters if the first-pass defaults are too strict or too loose.
- Backtest the rulebook before operation runs.
- Run at least one full week of adapter-backed testing before any operation approval.
- Validate whether the 1-5% target band is realistic after fees, slippage,
  spread, failed entries, and missed exits are modeled.
