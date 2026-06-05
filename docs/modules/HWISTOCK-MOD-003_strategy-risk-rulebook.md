---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-003
type: module
domain: backend
name: Strategy risk rulebook
spec_status: set
build_status: go_check_passed
verification_status: go_check_passed
ready_set_rebaseline_status: go_check_passed
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
completeness:
  status: set
  audit_ref: docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md
owner: hwi
updated_at: 2026-06-04
last_verified_at: 2026-06-04
source_inputs:
  - kind: user_prompt
    path_or_url: "종목을 어떻게 고르는지, 한종목에 올인 하는지, 얼마씩 매수할지, 매도 시점은 언제인지"
    confidence: high
  - kind: user_prompt
    path_or_url: "총자금은 200만원에서 시작"
    confidence: high
  - kind: user_prompt
    path_or_url: "종목은 5개로 하고 최대 투입금은 내 총자금의 퍼센티지로"
    confidence: high
  - kind: user_prompt
    path_or_url: "손절은 최대 -5%이고 AI가 그때그때 들어갈 종목 손절가를 정한다"
    confidence: high
  - kind: user_prompt
    path_or_url: "한 종목 최대 투입금 대신 최소치 남겨둘 자금을 0.25로 둔다"
    confidence: high
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  - backend/lib/strategy_risk.py
  - backend/tests/test_strategy_risk_rulebook.py
entrypoints:
  - backend.lib.strategy_risk.loadStrategyRiskConfig
  - backend.lib.strategy_risk.validateEntryIntent
  - backend.lib.strategy_risk.buildNoOrderDryRunRecord
interfaces:
  - backend.lib.strategy_risk.loadStrategyRiskConfig
  - backend.lib.strategy_risk.validateStrategyRiskConfig
  - backend.lib.strategy_risk.validateSignalBundle
  - backend.lib.strategy_risk.validateCandidateOnlyIntent
  - backend.lib.strategy_risk.validateEntryIntent
  - backend.lib.strategy_risk.buildNoOrderDryRunRecord
  - backend.lib.strategy_risk.validateNoOrderDryRunRecord
  - backend.lib.strategy_risk.computeMaxOrderCashKrw
evidence_refs:
  - docs/evidence/RUN-20260602_unit-004-strategy-risk-rulebook-set.md
  - docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md
  - docs/evidence/RUN-20260604_unit-004-go-preflight.md
  - docs/evidence/RUN-20260604_unit-004-go-check.md
links:
  - PROFILE-HWISTOCK
  - HWISTOCK-MOD-001
---

# Strategy Risk Rulebook

## 1. Purpose

This module defines the first strategy/risk rulebook for `hwiStock`. It is a
software safety contract, not investment advice. The rulebook decides what the
automation may consider, how much cash it may deploy, when it must exit, and
when it must stop trading.

## 2. User Value / Representative Scenarios

- As the owner, I can see why a symbol became a candidate before any order is
  considered.
- As the owner, I can prevent a single stock from consuming the full account.
- As a reviewer, I can verify every entry has a predefined stop trigger and
  exit reason.
- As an operator, I can verify the first test does not add broad account-level
  risk controls unless a later Set decision approves them.
- As the owner, I can paper-test the rules for an observation window I choose
  before approving live operation.

## 3. Scope

### Included

- Candidate stock selection filters.
- Multi-source signal bundle: news/disclosure context plus chart/market-data
  confirmation.
- Optional AI API orchestration: candidate synthesis and ranking before
  deterministic risk gates.
- All-in prohibition.
- Starting capital and position sizing limits.
- Fast intraday strategy tempo: 10-20 minute holding hypothesis and per-trade
  1-5% price-move target band.
- Cash reserve floor, maximum simultaneous holdings, and entry-price-based
  stop-loss policy.
- Entry preconditions.
- Stop-loss, optional take-profit/time exits, and day-end flat policy.
- No-averaging-down rule.
- Manual kill switch and operational error blocks.
- Paper/backtest evidence requirements.

### Excluded

- Specific stock recommendations.
- Profit expectation.
- Final alpha/signal formula.
- Broker/API implementation.
- KIS/external broker network calls before the KIS API verification unit.
- Live order placement.
- Credit, margin, 미수, borrowed funds, or leveraged capital.

## 4. Product / Capability Contract

### 4.1 Capital Baseline

- Starting capital: 2,000,000 KRW cash.
- Capital mode: cash-only.
- All-in single-stock deployment: forbidden by default.
- Live starting capital baseline: 2,000,000 KRW cash.
- Official paper/mock-investment starting budget candidate: 10,000,000 KRW after
  KIS API verification. Paper sizing must be scalable down to the 2,000,000 KRW
  live baseline.
- Required first-pass allocation controls:
  - minimum cash reserve ratio: 0.25 of total capital
  - maximum simultaneous holdings: 5
  - no all-in single-stock deployment
- There is no fixed per-symbol maximum allocation in the first policy. Position
  sizing may concentrate into fewer symbols when the strategy/risk gates approve
  it, but every buy decision must preserve the cash reserve floor. With
  2,000,000 KRW live starting capital, the runner must keep at least 500,000 KRW
  unallocated by default; with the 10,000,000 KRW KIS paper target budget, it
  must keep at least 2,500,000 KRW unallocated by default.
- Averaging down is forbidden by default unless a future approved unit changes
  the rule.

### 4.2 Minimal Stop Policy

- Broad account-level loss management is intentionally not part of the first
  policy unless a later Set decision adds it.
- Required first-pass stop rule: every entry must have a concrete stop price
  before it can become order-eligible.
- Maximum stop distance: the stop price must not allow a loss greater than 5%
  below average entry price, before fees/taxes/slippage.
- AI may propose a per-symbol stop price from the normalized signal bundle, but
  the deterministic risk gate owns validation. If the AI stop is missing,
  wider than -5%, inconsistent with the latest quote, or not auditable to source
  data, the entry is rejected. AI cannot widen the stop, disable the stop, or
  override cash-reserve or holdings-cap gates.
- Stop execution must record trigger price, observed price, attempted order
  style, fill result, retry result, slippage, and final position state.
- Daily loss halt, consecutive-loss halt, max-trade count, and cooldown are
  excluded from the first minimal policy by default, but may be added later
  after paper evidence.

### 4.3 Strategy Tempo

- Strategy hypothesis: fast intraday scalping/momentum.
- Candidate holding window: 10-20 minutes while the signal remains valid.
- Hard maximum holding window: 30 minutes unless a future approved unit changes
  this rule.
- Candidate take-profit/price-move target band per position: 1-5%.
- The 1-5% band is not a daily account return target and not a promise. It is
  only the draft target band for an individual position. It is not enough to
  justify an entry by itself. The entry must still pass candidate filters,
  liquidity checks, stop policy, cash-reserve floor, and holdings cap.
- Reward/risk guard is approved for the first-pass paper/sandbox default: an
  entry must meet `minimum_reward_risk_ratio = 1.2` before it can become a
  no-order dry-run entry intent.
- The 08:00-20:00 trading envelope is an observation/opportunity window. It does
  not allow automatic continuous trading every 10-20 minutes.
- Overtrading guard values are deferred. The first policy still rejects entries
  without a fresh signal, valid data, allowed symbol, available cash, reserve
  floor pass, and holdings-cap pass.

### 4.4 Signal Bundle

The strategy should evaluate two candidate paths:

- Event-first path: official disclosure, exchange/broker notice, or approved
  news creates a watchlist candidate. Chart/market-data confirmation is required
  before entry.
- Chart-first path: approved market data shows unusual price/volume behavior.
  The system should search for related news/disclosure context before entry, and
  must label the candidate as chart-first when no event context is found.

A buy decision requires a `signal_bundle` with:

- source path: `event_first`, `chart_first`, or `combined`
- source ids/URLs for news/disclosures/notices when available
- chart interval and timestamp
- price/volume setup reason
- stale-data and latency status
- risk plan from this module

News, disclosure, or chart movement alone is never allowed to bypass the risk
engine. A missing chart confirmation rejects event-first entries by default.

### 4.4-1 AI-Orchestrated Signal Review

If AI API orchestration is enabled, it may review a normalized `signal_bundle`
and produce only a structured recommendation or non-executable draft
`order_intent`:

- `watch`
- `reject`
- `consider_entry`
- `hold_review`
- `exit_review`

The AI recommendation is not an order. `consider_entry` only means the candidate
may proceed to deterministic risk checks. The risk engine still owns position
sizing, stop-loss validation, cash-reserve/holdings checks, stale-data rejection, and
  order eligibility. Before KIS paper approval, an approved order intent can only
  be recorded as a no-order dry-run decision. It must not route to KIS, any
  external broker, or an internal fake broker/fill simulator. After explicit
  broker-network approval, the first broker-backed route is KIS KRX paper/mock.

### 4.5 Candidate Stock Selection

The automation may only consider a symbol when all P0 filters pass:

- It is a Korea domestic stock tradable through KIS on the selected venue route.
  Before broker approval, dry-run checks may use static fixture metadata for
  validation, but no internal broker/fill simulation is allowed.
- It is not halted, suspended, delisted, liquidation-only, or otherwise not
  normally tradable.
- It is not under an active investment warning/risk/watch state selected as an
  exclusion by the source registry. The initial default is to exclude automated
  entries for market-alert states until the rule is explicitly narrowed.
- Current and recent liquidity are sufficient for the planned order size.
- The symbol has a logged candidate reason from at least one approved source:
  realtime price/volume condition, official disclosure/news event, exchange
  notice, or broker-provided market data.

Candidate selection is not an entry signal. It only creates a watchlist item.

### 4.6 Entry Preconditions

Before any buy order decision, the strategy must log:

- signal bundle path and source ids
- AI recommendation id and model/prompt version when AI orchestration is enabled
- candidate reason
- chart confirmation reason
- venue route
- available cash
- planned order cash
- configured minimum cash reserve ratio
- projected cash after order
- stop-loss condition
- AI-proposed stop price, when AI orchestration is enabled
- deterministic stop validation result
- take-profit condition
- expected holding window
- configured stop-loss trigger
- stale-data check
- duplicate-position check
- cash-reserve and holdings-cap check

The order decision must be rejected when any required field is missing.

### 4.7 Exit Rules

Every position must have an exit plan before entry:

- Hard stop: exit when the predefined stop is hit or when estimated loss would
  cross the maximum allowed entry-price stop.
- Stop distance: AI may recommend the per-entry stop price, but the accepted stop
  must stay within the -5% maximum loss envelope. Missing or invalid AI stop
  output blocks entry.
- Take-profit candidate: the smaller usable rule between the 1-5% target band
  and the configured R-multiple target, as long as reward/risk minimums still
  pass. `R` is the expected loss if the hard stop is hit.
- Trailing exit candidate: after the trade reaches at least 1R profit, trail the
  stop according to the selected signal rule.
- Time stop: exit if the position does not make progress within the selected
  intraday window. Initial expected window is 10-20 minutes and hard max is 30
  minutes.
- Signal invalidation: exit when the entry reason is no longer true.
- Chart invalidation: exit when the chart setup that justified the entry breaks
  before the target is reached.
- Day-end flat policy: no overnight positions by default. New entries stop by
  19:30 KST, and all positions must be flat by 19:50 KST unless a future
  approved unit explicitly changes this.

### 4.8 Blocks / Kill Switch

The system must block new entries and alert the operator when:

- order/broker/data adapter returns an unexplained error
- market data is stale or inconsistent
- venue routing cannot be determined
- cash/position state cannot be reconciled
- manual kill switch is active

Daily realized-loss halt, consecutive-loss halt, completed-trade cap, and
cooldown are intentionally not first-pass defaults. They may be added in a later
Set decision if the paper run shows they are needed.

## 5. Interfaces

Current current-authority rebaseline implementation files:

- `backend/lib/strategy_risk.py`
- `backend/tests/test_strategy_risk_rulebook.py`

Current stdlib-only local interfaces:

- `loadStrategyRiskConfig()` — approved paper/sandbox defaults
- `validateStrategyRiskConfig()` — config contract validation
- `validateEntryIntent()` — deterministic entry-intent rejection reasons
- `validateCandidateOnlyIntent()` — watchlist-only boundary
- `buildNoOrderDryRunRecord()` — no-order dry-run record builder
- `validateNoOrderDryRunRecord()` — dry-run boundary validation
- `computeMaxOrderCashKrw()` — reserve-floor sizing helper

Future interfaces may include:

- strategy rule config
- candidate selector
- risk engine
- position sizing calculator
- exit planner
- audit log
- AI recommendation input/output audit

## 6. State / Data / Permission Rules

- The rulebook must be configuration-backed once code exists.
- Strategy/risk parameter changes require explicit approval and docs updates.
- Audit logs must include candidate, entry, sizing, exit, and halt reasons.
- AI output must be logged with model, prompt/schema version, source ids,
  latency, cost metadata when available, and structured validation result.
- Paper/backtest/live evidence must never imply guaranteed profitability.

## 7. Existing Assets / Reuse Points

- `HWISTOCK-MOD-001` safety core.
- `HWISTOCK-MOD-002` market intelligence ingestion can provide candidate events,
  but cannot directly place orders.

## 8. Module-Level Verification

- Verify cash-reserve and holdings caps are enforced before order decisions.
- Verify all-in and averaging-down are blocked by default.
- Verify every entry has a stop, target, and exit plan.
- Verify stale-data, cash-reserve/holdings-cap, and manual kill-switch blocks prevent new
  entries.
- Verify UNIT-004 no-order dry-run evidence records candidate, entry, size, stop,
  target, hold window, and rejection reason without fill/PnL simulation; later
  trading-engine paper evidence owns real exit/fill/PnL fields.

## 9. Included Units

- `HWISTOCK-UNIT-004`: strategy/risk rulebook planning and paper-readiness
  contract.
- `HWISTOCK-UNIT-006`: trading engine/order state implementation contract uses
  this rulebook as its deterministic policy source.

## 10. Decisions / Open Contract Questions

- Decision: starting capital is 2,000,000 KRW cash.
- Decision: official paper/mock-investment starting budget is 10,000,000 KRW if
  KIS verification confirms a usable mode.
- Decision: all-in single-stock deployment is forbidden by default.
- Decision: first-pass risk policy is minimal: minimum cash reserve floor,
  maximum simultaneous holdings, and entry-price-based stop-loss.
- Decision: maximum simultaneous holdings is 5.
- Decision: no fixed per-symbol maximum allocation is used in the first policy.
  Instead, every entry must preserve `minimum_cash_reserve_ratio = 0.25` of total
  capital.
- Decision: stop-loss is AI-assisted per entry but capped by a deterministic
  maximum -5% loss envelope. AI may suggest a stop price; the risk gate validates
  it and rejects missing, unauditable, stale, or wider-than-envelope output.
- Decision: broad account-level loss management is excluded for now.
- Decision: draft strategy tempo is 10-20 minute fast intraday scalping/momentum
  with a per-position candidate 1-5% price-move target band.
- Decision: strategy signals should combine news/disclosure context and
  chart/market-data confirmation. Event-first entries require chart confirmation
  by default, and chart-first candidates must look for event context when
  possible.
- Decision: AI API orchestration may rank/explain candidates, but cannot create
  executable broker orders or override deterministic risk gates.
- Decision: KIS is the selected broker/API direction.
- Decision: KB Securities is blocked as a practical personal API candidate unless
  future official confirmation proves otherwise.
- Decision: internal fake broker execution is not used. Before KIS paper
  approval, approved order intents are recorded only as no-order dry-run
  decisions.
- Decision: official KIS paper/mock-investment API use is the first
  broker-backed route after KIS API portal verification and explicit approval.
- Decision: the 08:00-20:00 envelope is observation/opportunity time, not
  continuous trading permission.
- Decision: no overnight positions by default.
- Decision: if AI stop output is unavailable or invalid, the entry is rejected;
  there is no first-pass deterministic fallback stop.
- Open: exact AI stop-recommendation prompt wording and runtime enablement
  remain governed by `HWISTOCK-UNIT-005` AI network/tool-boundary policy.
- Decision: the first-pass alpha family, chart/realtime source, candle
  intervals, liquidity behavior, reward/risk guard, market-alert source,
  take-profit label, and time-stop behavior are approved by
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.
- Open: later refinement of liquidity, take-profit, and trailing parameters after
  backtest/paper evidence.
- Decision: paper-run observation criteria are defined by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md` and are safety/
  evidence criteria, not a profit target. The observation duration is selected
  by the operator and is not hardcoded into the runner.

## 11. Evidence References

- `docs/evidence/RUN-20260602_strategy-risk-rulebook.md`
- `docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md`

## 12. Design References

- None.
