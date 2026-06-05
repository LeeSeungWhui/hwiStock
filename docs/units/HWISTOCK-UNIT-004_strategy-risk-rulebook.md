---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-004
type: unit
domain: backend
name: Strategy risk rulebook
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
work_class: product_api
completeness:
  status: set
  audit_ref: docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md
owner: hwi
updated_at: 2026-06-04
last_verified_at: 2026-06-04
source_snapshot:
  input_digest: "2,000,000 KRW cash-only short-term trading strategy/risk rulebook"
  legacy_doc: none
  legacy_status: greenfield
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
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  include:
    - backend/lib/strategy_risk.py
    - backend/tests/test_strategy_risk_rulebook.py
  exclude:
    - "**/*credentials*"
    - "**/*.env"
entrypoints: []
interfaces:
  - backend.lib.strategy_risk.loadStrategyRiskConfig
  - backend.lib.strategy_risk.validateStrategyRiskConfig
  - backend.lib.strategy_risk.validateSignalBundle
  - backend.lib.strategy_risk.validateCandidateOnlyIntent
  - backend.lib.strategy_risk.validateEntryIntent
  - backend.lib.strategy_risk.buildNoOrderDryRunRecord
  - backend.lib.strategy_risk.validateNoOrderDryRunRecord
  - backend.lib.strategy_risk.computeMaxOrderCashKrw
verification:
  stage_skill_routes:
    ready:
      - hwi-work-harness
    set:
      - hwi-work-harness
    go:
      - hwi-work-harness
      - delegation-guard
    check:
      - hwi-work-harness
    prove:
      - hwi-work-harness
  required_gates:
    - risk-contract-check
  suggested_gates:
    - strategy-rulebook-smoke
    - automated-trading-smoke
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md
risk:
  tier: 3
  reasons:
    - Trading strategy/risk parameters can affect account-affecting order behavior once operation mode exists.
    - Incorrect all-in, stop-loss, cash-reserve, or holdings-cap logic can cause outsized loss.
last_set:
  status: set
  report_id: RUN-20260602-unit-004-strategy-risk-rulebook-set
  context_fingerprint:
evidence_refs:
  - docs/evidence/RUN-20260602_strategy-risk-rulebook.md
  - docs/evidence/RUN-20260602_unit-004-strategy-risk-rulebook-set.md
  - docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md
  - run_id: RUN-20260604-unit-004-go-preflight
    status: superseded_by_code_import
  - run_id: RUN-20260604-unit-004-go-check
    status: superseded_by_code_import
links:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
---

# Strategy Risk Rulebook

## 1. Goal

Define the first stock-selection, position-sizing, entry, exit, and kill-switch
contract for the short-term Korea domestic stock trading project.

## 2. Baseline Module Contract

This unit implements `HWISTOCK-MOD-003` and updates `HWISTOCK-MOD-001` safety
expectations. Current-authority rebaseline Go-Check on 2026-06-04 restored a
stdlib-only local strategy/risk skeleton with config constants, signal and
entry-intent validators, watchlist-only candidate validation, no-order dry-run
records, and focused unittest coverage. It does not authorize broker, KIS, AI
provider, broker order, account-affecting order, fake fill, fake balance, or fake PnL
behavior.

### Module Change

Initial creation of `HWISTOCK-MOD-003`.

## 3. Included Scope

- Starting capital: 2,000,000 KRW cash.
- All-in single-stock prohibition.
- Candidate stock filters.
- News/disclosure plus chart/market-data signal bundle.
- Fast scalping/momentum hypothesis: 10-20 minute hold and per-trade 1-5%
  price-move target band.
- Position sizing controls: maximum simultaneous holdings is 5, and every entry
  must preserve a minimum cash reserve ratio of 0.25 of total capital.
- Entry preconditions.
- Exit rules.
- Daily halt and kill-switch rules.
- Backtest/adapter evidence requirements.

## 4. Excluded Scope

- Specific stock picks.
- Profit expectation.
- Broker/API code.
- KIS/external broker network calls before approved verification.
- Account-affecting broker order placement.
- Final alpha/signal formula.
- Credit, margin, 미수, borrowed funds, or leveraged capital.

## 5. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | Starting capital is fixed to 2,000,000 KRW cash | Profile/module/unit use the same amount | doc review | QA-001 |
| AC-02 | P0 | All-in deployment is blocked by reserve floor | Order sizing preserves `minimum_cash_reserve_ratio = 0.25`; all-in is forbidden | doc/config review | QA-002 |
| AC-03 | P0 | Candidate selection is separate from entry | Candidate reason alone cannot create an order | architecture/code review | QA-003 |
| AC-04 | P0 | Every entry has a predefined stop policy | Stop trigger, exit reason, and venue route are required | config/log review | QA-004 |
| AC-05 | P0 | Minimal position risk controls are explicit | Minimum cash reserve ratio 0.25, max simultaneous holdings 5, max -5% stop envelope, and AI stop-validation boundary are documented | config/doc review | QA-005 |
| AC-06 | P1 | No-order dry-run evidence can explain each candidate decision | Candidate, entry, size, stop, target, hold window, and rejection reason are recorded without fill/PnL simulation | evidence file | QA-006 |
| AC-07 | P1 | Fast strategy tempo is bounded | 10-20 minute hypothesis and no automatic continuous trading are documented | config/log review | QA-009 |
| AC-08 | P1 | 1-5% is not treated as a daily account target | Target band is recorded as per-position price movement only | doc/config review | QA-011 |
| AC-09 | P0 | Signal bundle combines context and chart confirmation | Entry logs include event/chart path, source ids, chart interval, and stale-data status | config/log review | QA-012 |
| AC-10 | P0 | Risk-approved intents respect broker boundary | Before KIS adapter approval, approved intent is recorded as no-order dry-run only; no broker call, simulated fill, or fake balance is produced | adapter/policy review | QA-014 |

## 6. Implementation Notes

- Treat `HWISTOCK-MOD-003` values as draft defaults for backtest and operation runs.
- Do not implement operation, KIS/external broker, or broker-provided broker-adapter/demo
  order routing from this unit. Before a KIS adapter unit is explicitly approved,
  first order-intent tests must terminate at no-order dry-run records only, with
  no simulated fills or fake balances.
- Do not let market-intelligence events directly bypass candidate, entry,
  cash-reserve, holdings-cap, stop, stale-data, and kill-switch checks.
- Require a signal bundle before entry. Event-first candidates need chart
  confirmation; chart-first candidates should search approved news/disclosure
  context and must label the entry as chart-first if no context exists.
- If a future implementation derives position size from stop distance, apply the
  reserve floor first: `max_order_cash = available_cash_krw - (total_capital_krw * minimum_cash_reserve_ratio)`.
  Any stop-distance sizing must fit inside `max_order_cash` before lot-size and
  broker-specific rounding.
- If AI orchestration is enabled for entry review, AI may propose
  `recommended_stop_price_krw` for the specific symbol/setup. The deterministic
  risk gate must validate that the implied stop is not wider than -5% from
  average entry and must reject unauditable, missing, or stale AI stop output.
  There is no first-pass deterministic fallback stop when AI stop output is
  unavailable or invalid.
- Treat 1-5% as a per-position price-move target band for adapter experiments, not
  a daily account return target and not a guaranteed outcome. Reject entries when
  expected reward/risk is below the configured threshold.
- Do not implement a loop that automatically enters a new trade every 10-20
  minutes. Entry must remain signal-gated, reserve-gated, and holdings-gated.

## 7. Open Questions

- The first-pass strategy defaults that would close the broad alpha/chart/source
  questions are packaged in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md` and require
  user approval before full trading strategy Go.
- Later refinement of liquidity, take-profit, and trailing parameters remains a
  follow-up item after backtest/adapter evidence.
- Operation observation criteria are closed by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`; the gate is
  operator-selected, safety/evidence/reconciliation based, and has no profit
  threshold.
