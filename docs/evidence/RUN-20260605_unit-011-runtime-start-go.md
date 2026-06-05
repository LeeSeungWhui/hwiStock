---
schema_version: hwi.evidence-summary/v0
id: RUN-20260605-unit-011-runtime-start-go
type: evidence
stage: go
status: runtime_started_check_pending
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-05
owner: hwi
profile_refs:
  - PROFILE-HWISTOCK
unit_refs:
  - HWISTOCK-UNIT-011
  - HWISTOCK-UNIT-012
  - HWISTOCK-UNIT-014
module_refs:
  - HWISTOCK-MOD-009
---

# UNIT-011 Go Evidence — Runtime Bundle Start

## 1. Scope

The owner approved starting the full local user-systemd runtime bundle. This Go
pass installed/enabled/started hwiStock user services and timers, and performed
bounded runtime smoke checks.

This pass also added a safety guard so the KIS broker-adapter runner can run read-health
and reconciliation ticks while broker cash order submission remains disabled
unless a later explicit order unit enables `HWISTOCK_KIS_PAPER_ORDER_ENABLED`
and also provides a matching operator approval file/run id. Passing
`--allow-paper-orders` alone is not sufficient.

Explicit scope exception: although UNIT-011 was primarily a local runtime
supervisor/startup pass, the owner approved starting the KIS adapter
read-health/reconciliation timers as part of "turn the runtime bundle on".
That exception is limited to broker-adapter read and reconciliation evidence with
orders disabled. It does not authorize KIS broker order submission, KIS
order/cancel/modify endpoints, unapproved domains, raw account output, or credential
printing.

## 2. Side Effects Performed

- Installed repo unit files into `/home/hwi/.config/systemd/user/`.
- Ran `systemctl --user daemon-reload`.
- Enabled and started:
  - `hwistock-api.service`
  - `hwistock-frontend.service`
  - `hwistock-intel-collector.timer`
  - `hwistock-ai-analysis.timer`
  - `hwistock-runner-tick.timer`
  - `hwistock-kis-paper-health.timer`
  - `hwistock-kis-paper-runner.timer`
- Manually triggered one tick for:
  - `hwistock-runner-tick.service`
  - `hwistock-ai-analysis.service`
  - `hwistock-kis-paper-health.service`
  - `hwistock-kis-paper-runner.service`
- Restarted `hwistock-api.service` after correcting the readiness note.

No unapproved endpoint, account-affecting order, public/LAN bind, secret print, staging, or
commit operation was performed.

## 3. Code / Config Changes

Changed runtime safety/config files:

- `backend/service/kis_paper_continuous_runner.py`
  - Added `paper_order_enabled`.
  - Added CLI flag `--allow-paper-orders`.
  - Blocks `cash_order` with `blocked_paper_order_disabled` when an intent is
    present but broker order submission is not explicitly enabled.
  - Preserves risk-overlay block reasons before the order-disabled block.
  - Requires `HWISTOCK_ORDER_APPROVAL_FILE` plus
    `HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID` before an order-enabled run can
    reach broker order submission.
  - Claims an idempotency key before broker submission and locks ambiguous
    submit outcomes until reconciliation.
- `ops/systemd/user/hwistock-kis-paper-runner.service`
  - Sets `HWISTOCK_KIS_PAPER_ORDER_ENABLED=false`.
  - Keeps `--allow-paper-network` so read-health/reconciliation can run.
  - Does not pass `--allow-paper-orders`.
- `ops/systemd/user/hwistock-ai-analysis.service`
  - Replaced stale `moonbridge` default with `deepseek-v4-pro`.
- `backend/service/kis_paper_health.py`
  - Treats token-missing/token-block health states as classified evidence, not
    process crashes.
- `backend/service/HwiStockRunnerService.py`
  - Removed stale readiness note saying systemd templates were not executed.
- `backend/tests/test_kis_paper_continuous_runner.py`
  - Added order-disabled coverage and explicit order-enabled fixture coverage.

## 4. Runtime Status Evidence

Observed after start:

| surface | result |
| --- | --- |
| user systemd timers | 5 active/waiting hwiStock timers |
| long-running services | `hwistock-api.service` active/running; `hwistock-frontend.service` active/running |
| API bind | `127.0.0.1:5001` |
| frontend bind | `127.0.0.1:5000` |
| API runner status | HTTP 200 |
| API KIS status | HTTP 200 |
| frontend root | HTTP 307 |

Timer list after start:

- `hwistock-runner-tick.timer`
- `hwistock-kis-paper-runner.timer`
- `hwistock-intel-collector.timer`
- `hwistock-kis-paper-health.timer`
- `hwistock-ai-analysis.timer`

## 5. AI Runtime Evidence

Evidence file:
`data/evidence/2026-06-05/ai-analysis-health.json`

Summary:

- status: `ok`
- provider route: `deepseek_direct`
- requested model: `deepseek-v4-pro`
- actual model: `deepseek-v4-pro`
- source event count: `12`
- orders enabled: `false`

## 6. KIS Adapter Read Runtime Evidence

KIS adapter health evidence:
`data/evidence/2026-06-05/kis-paper-health.json`

Summary:

- status: `ok`
- adapter domain only: true
- unapproved domain calls made: false
- orders enabled: false
- order endpoint called: false
- credential values printed: false
- raw responses stored: false
- token, quote, balance, buyable, daily order/fill lookup, and revoke steps
  recorded `pass`.

KIS broker-adapter continuous runner evidence:
`data/evidence/2026-06-05/kis-paper-continuous-latest.json`

Summary:

- status: `ok`
- adapter network enabled: true
- broker order enabled: false
- unapproved domain calls made: false
- public dashboard exposed: false
- raw responses stored: false
- credential values printed: false
- token, quote, balance, buyable, daily order/fill lookup, and revoke steps
  recorded `pass`.
- No `cash_order` step was executed.

## 7. Current Blocks / Non-Readiness

The program is now running as a service bundle, but it is not operationally
ready to trade automatically.

Current API status still reports:

- `orderGate = blocked_calendar_unconfigured`
- calendar cache missing:
  `/data/workspace/My/hwiStock/config/market-calendar/krx-nxt-trading-days.json`
- market data source unconfigured
- `liveOrdersEnabled = false`
- `brokerCallsEnabled = false` on the base runner
- KIS status: `paperRunReady = false`
- KIS status: `operationalTradingReadiness = false`
- KIS status: `paperOrderEnabled = false`

Remaining implementation blockers:

- UNIT-013 signal-to-intent pipeline is not implemented.
- UNIT-014 broker order submission remains disabled until explicit adapter-order
  execution Go/Prove scope.
- Calendar/source configuration is missing.
- Dashboard operator observation Prove is not complete.

## 8. Validation

Commands run:

- `python -m pytest backend/tests/test_hwistock_runner.py backend/tests/test_kis_paper_continuous_runner.py`
  - result: `43 passed`
- `python -m pytest backend/tests/test_kis_paper_continuous_runner.py`
  - result: `11 passed`
- `python -m py_compile backend/service/kis_paper_continuous_runner.py backend/service/kis_paper_adapter.py backend/service/ai_analysis_runner.py backend/service/HwiStockRunnerService.py backend/router/HwiStockRunnerRouter.py`
  - result: pass
- `python -m py_compile backend/service/kis_paper_health.py backend/service/kis_paper_continuous_runner.py`
  - result: pass
- `git diff --check`
  - result: pass

## 9. Verdict

Runtime start Go is complete, but Check is still pending.

Current status:

- service bundle: running
- KIS broker-adapter read/reconciliation tick: running
- DeepSeek Pro analysis tick: running
- KIS broker cash order submission: disabled
- automatic signal-to-intent trading: not implemented
- operational automated trading readiness: false
- account-affecting operation readiness: false
