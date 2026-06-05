---
schema_version: hwi.evidence/v0
id: RUN-20260602-calendar-alert-operation-gate-set
type: evidence
name: Market calendar, alert channel, and one-week operation gate Set pass
stage: set
environment: docs_only
status: set
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
unit_refs:
  - HWISTOCK-UNIT-002
  - HWISTOCK-UNIT-004
  - HWISTOCK-UNIT-006
source_refs:
  - docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md
go_allowed: false
---

# Market Calendar, Alert Channel, And One-Week Adapter Gate Set Pass

## 1. Scope

This docs-only Set pass closes three Ready-Set blockers:

- official/broker market-calendar source
- first-pass alert channel
- one-week adapter-backed pass criteria

No code, broker network call, AI network call, external alert delivery, order
placement, or credential storage was performed.

## 2. Source Checks

Public source checks performed on 2026-06-02:

- KRX official trading-days/holidays page:
  `https://global.krx.co.kr/contents/GLB/06/0606/0606030101/GLB0606030101T3.jsp`
- NXT official site:
  `https://www.nextrade.co.kr/`

Local KIS reference:

- `apiRefer/국내휴장일조회[국내주식-040].xlsx`

The local KIS capability matrix marks `국내휴장일조회` adapter-unsupported, so it is
not a first-pass operationtime dependency.

## 3. Closed Decisions

- Calendar source hierarchy: KRX official trading-days/holidays and notices, NXT
  official session references, local cached calendar for runtime, and later KIS
  holiday lookup only after approved broker-network integration.
- Runtime calendar cache: planned path
  `config/market-calendar/krx-nxt-trading-days.json`.
- Missing/stale calendar behavior: active trading/order loops idle with
  `calendar_unconfigured` or `calendar_stale`.
- Alert channel: local-only first pass through systemd journal,
  `data/alerts/YYYY-MM-DD/alerts.jsonl`, dashboard audit/error panel when
  implemented, and daily close report.
- External alert delivery: deferred; requires later Set approval.
- One-week adapter-backed gate: minimum 7 consecutive calendar days and at least
  5 valid Korean market open days. If holidays reduce open days below 5, extend
  the run.
- Operation pass criteria: P0 safety/evidence/reconciliation criteria; no profit
  threshold and no expected-profit claim.

## 4. Updated Documents

- `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`
- `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/modules/HWISTOCK-MOD-001_trading-safety-core.md`
- `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`
- `docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md`
- `docs/units/HWISTOCK-UNIT-002_home-server-adapter-runner.md`
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md`
- `docs/qa/QA-HWISTOCK-UNIT-002_home-server-adapter-runner.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`
- `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`
- `docs/evidence/RUN-20260602_ready-set-architecture.md`
- `docs/index.md`

## 5. Verdict

Calendar/alert/operation-gate Set status: PASS

Implementation readiness for whole bundle: BLOCKED

Remaining blockers: current final external review, dashboard `agy` design
review, and trading-strategy inputs packaged in
`docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`, such as
alpha/signal formula, chart/realtime source, candle intervals, liquidity threshold, and market-alert
source.
