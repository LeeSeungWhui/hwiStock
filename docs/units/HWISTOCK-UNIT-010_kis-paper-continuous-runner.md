---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-010
type: unit
domain: backend_ops
name: KIS paper continuous runner
status: set
ready_set_rebaseline_status: ready_for_go_check
implementation_status: go_check_passed_local_no_network
paper_run_ready: false
continuous_runner_ready: false
priority: P0
source_of_truth: user_intent
work_class: product_api_ops
completeness:
  status: set
  audit_ref: docs/qa/QA-HWISTOCK-UNIT-010_kis-paper-continuous-runner.md
owner: hwi
updated_at: 2026-06-05
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-008
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-007
code_paths:
  include:
    - backend/service/kis_paper_adapter.py
    - backend/service/kis_paper_continuous_runner.py
    - backend/lib/paper_trading_ledger.py
    - backend/service/HwiStockRunnerService.py
    - backend/router/HwiStockRunnerRouter.py
    - backend/tests/test_kis_paper_adapter.py
    - backend/tests/test_kis_paper_continuous_runner.py
    - ops/systemd/user/hwistock-kis-paper-runner.service
    - ops/systemd/user/hwistock-kis-paper-runner.timer
  exclude:
    - "**/*credentials*"
    - "**/*.env"
    - backend/config.ini
    - frontend-web/config.ini
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-010_kis-paper-continuous-runner.md
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-continuous-paper-runner.md
  - docs/evidence/RUN-20260605_unit-010-go-check.md
links:
  - HWISTOCK-MOD-008
  - docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md
  - docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md
---

# KIS Paper Continuous Runner

## 1. Goal

Implement the KIS paper runner foundation for hwiStock: a 24-hour continuous
home-server runner that can use the configured KIS paper/mock API key for
KRX-supported paper trading tests, while keeping live trading, real-money
orders, fake broker simulation, and public exposure blocked.

This unit is not the whole operational stock-trading program. The actual
paper-trading program queue is `HWISTOCK-UNIT-011` through `HWISTOCK-UNIT-015`,
which adds service supervision, AI runtime, signal-to-intent generation,
execution/reconciliation, and operator observation Prove.

This unit must not implement a fixed seven-day runner. The program keeps
running until the operator stops or disables it. The operator decides the test
period/observation window and the evidence report records that window as
metadata.

## 2. Included Scope

- KIS paper/mock credential loading from `/home/hwi/.config/hwistock/kis-paper.env`
  without printing or committing values.
- Paper/live domain guard that fail-closes on any live endpoint, partner
  endpoint, or unknown host.
- KIS paper token lifecycle for the approved KRX paper path.
- KIS paper REST/WebSocket wrapper for supported KRX functions:
  token/approval key as needed, quote/orderbook, buyable, balance, cash order,
  modify/cancel, daily order/fill lookup, and fill notice.
- KIS paper capability registry that disables NXT/SOR/integrated/helper branches
  according to the current capability matrix.
- Continuous runner loop with explicit health states for calendar, market data,
  source freshness, risk gate, order gate, broker adapter, reconciliation, and
  kill switch.
- Deterministic risk overlay using the hwiStock capital policy: 2,000,000 KRW
  live baseline, cash-only, max simultaneous holdings 5, and
  `minimum_cash_reserve_ratio = 0.25`.
- Paper ledger and reconciliation records for submitted, accepted, rejected,
  cancel, fill, balance, buyable, and fallback/disabled branches.
- Operator observation-window manifests. Start/end/duration are metadata chosen
  by the operator; no fixed duration is hardcoded.
- systemd service/timer or equivalent user service files for continuous runtime
  health. Manual shell runs are not official long-running evidence.
- Read-only status/API extension so the dashboard can show paper runner health
  without buy/sell controls.
- Focused tests and smoke/evidence output proving safety boundaries.

## 3. Excluded Scope

- Live order placement.
- Live KIS credentials, real account login, live balance, or real-money trading.
- NXT/SOR broker order routing through KIS paper.
- Internal fake broker adapter, fake fills, fake balances, or fake PnL.
- AI provider network calls unless a later approved AI-runtime unit enables
  them; AI output cannot call this runner directly.
- Public/LAN dashboard exposure.
- Direct dashboard buy/sell controls or service-control buttons.
- Expected-profit claims.
- Any auto-pass, auto-fail, or auto-stop behavior based on a hardcoded test
  duration.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | Runner is continuous, not fixed-duration | Service loop has no hardcoded seven-day stop/pass/fail condition | code/test review | QA-001 |
| AC-02 | P0 | Observation window is operator-controlled | Evidence records start/end/duration as operator metadata | manifest test | QA-002 |
| AC-03 | P0 | Secrets stay external and redacted | KIS paper env file is referenced by path only; values never printed or committed | secret scan/log review | QA-003 |
| AC-04 | P0 | Paper/live domain guard fail-closes | Live/unknown broker hosts cannot be called | adapter test | QA-004 |
| AC-05 | P0 | KIS paper KRX path is supported | Supported token/quote/buyable/balance/order/cancel/fill lookup/fill notice flows work or fail with classified paper errors | smoke/evidence | QA-005 |
| AC-06 | P0 | KIS paper unsupported branches are disabled/fallback | NXT/SOR/integrated/helper calls do not hit broker endpoints | capability test | QA-006 |
| AC-07 | P0 | Risk overlay controls paper orders | Cash reserve, holdings cap, stop/kill/stale/calendar gates block unsafe intents | policy test | QA-007 |
| AC-08 | P0 | No fake broker evidence exists | Missing KIS responses never become fake fills, fake balances, or fake PnL | ledger test | QA-008 |
| AC-09 | P0 | Reconciliation is auditable | Order/fill/balance/buyable snapshots reconcile into system-calculated ledger fields | reconciliation test | QA-009 |
| AC-10 | P0 | Runner is restartable | systemd/user-service restart preserves idempotent state and does not duplicate orders | lifecycle smoke | QA-010 |
| AC-11 | P0 | Market/session idle behavior is safe | Closed/stale calendar or off-envelope session blocks trading/order loops while service stays healthy | calendar smoke | QA-011 |
| AC-12 | P0 | Dashboard remains read-only | Status surfaces show health/evidence only; no buy/sell or live controls | API/UI review | QA-012 |

## 5. Go Boundary

`HWISTOCK-UNIT-010` passed local no-network Go-Check on 2026-06-05. The
continuous paper runner code, adapter boundary, ledger helpers, read-only status
surface, and systemd user templates now exist. This still does not mean an
operational paper run has started or passed: no KIS API call, secret read, paper
order, or systemd enable/start was performed during the local Go-Check.

Allowed runtime/Prove actions inside this unit only:

- KIS paper/mock KRX-supported REST/WebSocket calls.
- KIS paper order placement/cancel/reconciliation in the paper environment.
- Read-only KIS paper balance/buyable/quote/order/fill evidence collection.
- systemd/user-service file creation for continuous paper runtime.
- Local evidence/ledger/report generation.

Forbidden even inside this unit:

- live KIS endpoint calls;
- real-money orders;
- NXT/SOR KIS paper broker routing;
- fake broker simulation;
- secret printing;
- public dashboard exposure;
- direct AI-to-order calls;
- hardcoded fixed-duration runner behavior.

## 6. Remaining Follow-Up

- Go must inspect current code and final file split before editing.
- Go must run focused tests and a bounded paper smoke only after preflight.
- Prove must run the operator-selected observation window for as long as the
  operator chooses; the program itself must not decide that duration.
