---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-004
type: qa_scenario
name: Strategy risk rulebook QA
unit_refs:
  - HWISTOCK-UNIT-004
module_refs:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
profile_refs:
  - PROFILE-HWISTOCK
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
owner: hwi
updated_at: 2026-06-04
evidence_refs:
  - docs/evidence/RUN-20260602_unit-004-strategy-risk-rulebook-set.md
  - docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md
  - docs/evidence/RUN-20260604_unit-004-go-preflight.md
  - docs/evidence/RUN-20260604_unit-004-go-check.md
---

# Strategy Risk Rulebook QA

## 1. Purpose

Prove that strategy/risk rules are explicit enough to prevent all-in behavior,
missing stop policy, missing reserve/holdings caps, and unexplainable entries before any
trading code is implemented.

## 2. Scope

In scope:

- 2,000,000 KRW cash starting capital
- all-in prohibition
- candidate filters
- news/disclosure plus chart signal bundle
- fast 10-20 minute scalping/momentum hypothesis
- per-trade 1-5% price-move target band
- reserve-floor position sizing behavior
- maximum simultaneous holdings 5
- minimum cash reserve ratio 0.25
- entry risk preconditions
- exit rules
- AI-assisted per-entry stop price with deterministic -5% maximum loss envelope
- manual kill switch / operational blocks
- adapter/backtest evidence shape

Out of scope:

- account-affecting operation
- broker order routing
- KIS/external broker endpoint routing
- broker-provided broker-adapter/demo/testbed endpoint routing before approval
- specific stock recommendations
- final alpha formula optimization

## 3. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | docs/config | Inspect profile, module, and unit capital lines | Starting capital is consistently 2,000,000 KRW cash | doc review |
| QA-002 | P0 | risk | Attempt to size an order that would leave less than 25% cash reserve or consume 100% capital | Order is rejected or config is invalid | rule/config test |
| QA-003 | P0 | architecture | Submit a candidate event without entry signal/risk fields | Candidate is watchlist-only and cannot place an order | code/log review |
| QA-004 | P0 | risk | Submit entry request without configured stop-loss trigger or route | Entry is rejected before order routing | rule/config test |
| QA-005 | P0 | risk | Submit config without minimum cash reserve ratio 0.25, max simultaneous holdings 5, max stop envelope, or AI stop-validation policy | Config is invalid | schema/config test |
| QA-006 | P1 | evidence | Generate no-order dry-run decision summary | Candidate, entry, size, stop, target, hold window, and rejection reason are recorded without fill/PnL simulation | evidence file |
| QA-007 | P1 | session | Open position before 19:30 and inspect 19:50 rule | Position is flattened by 19:50 KST by default | adapter log |
| QA-008 | P1 | safety | Submit averaging-down add-on after price moves against position | Add-on is rejected by default | test/log |
| QA-009 | P1 | tempo | Attempt continuous 10-20 minute re-entry after each exit without a fresh signal | Re-entry is blocked unless fresh signal, reserve, holdings, and data checks pass | test/log |
| QA-010 | P1 | stop | Simulate price falling below accepted AI-proposed stop price | Immediate full-exit attempt is logged with fill/retry result | rule/log test |
| QA-011 | P1 | docs/config | Inspect target-band configuration | 1-5% is labeled as per-position price-move/take-profit target, not daily account return | doc/config review |
| QA-012 | P0 | signal | Submit event-first candidate without chart confirmation | Entry is rejected and remains watchlist-only | rule/config test |
| QA-013 | P1 | signal | Submit chart-first candidate without related news/disclosure context | Candidate is labeled chart-first and still requires risk, stale-data, reserve, and holdings checks | test/log |
| QA-014 | P0 | adapter | Submit risk-approved order intent before KIS adapter approval | Intent is recorded as no-order dry-run only; KIS/external broker, internal fake broker, simulated fill, fake balance, broker adapter/demo, and account-affecting routing are rejected until approved | adapter/policy log |
| QA-015 | P0 | stop | Submit missing, stale, unauditable, or wider-than--5% AI stop recommendation | Entry is rejected before order eligibility; AI cannot widen the stop | rule/config test |
| QA-016 | P1 | signal | Inspect approved first-pass strategy config after packet approval | Candle intervals, stale-data threshold, liquidity gates, chart confirmation gates, target, and time-stop defaults match the approved packet | config/doc review |

## 4. PASS / FAIL / BLOCKED Rules

- PASS: all P0 rows pass, all-in is blocked, every entry has a stop policy,
  reserve-floor controls are explicit, max simultaneous holdings is 5, AI stop
  output is bounded by the deterministic -5% maximum loss envelope, and
  continuous re-entry is prevented by signal and position checks. Event-first
  entries require chart confirmation by default.
- FAIL: a single symbol can consume full capital, an entry can proceed without a
  stop policy, continuous re-entry can bypass signal/position checks,
  event-first entry can bypass chart confirmation, or unapproved broker broker-adapter
  routing is reachable.
- BLOCKED: no strategy/risk config or test fixture exists for the implementation
  stage, or the prepared strategy decision packet has not been approved/excluded
  before full trading strategy Go.

## 5. Evidence Requirements

- profile/module/unit doc review
- risk config or rule test output once code exists
- adapter/backtest trade summary
- stop-loss trigger/exit log
- rejected-order log for all-in, missing stop, stale data, or averaging down
- approved strategy decision packet/config review when UNIT-004 proceeds to full
  trading strategy Go
- Current-authority rebaseline Go-Check keeps QA-007 and QA-010 documented as
  deferred to the later trading-engine execution/logging unit while requiring
  all P0 rows plus dry-run evidence, stale-data checks, and re-entry blocking to
  pass locally.
