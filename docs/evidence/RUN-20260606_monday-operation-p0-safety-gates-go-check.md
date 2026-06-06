# RUN — Monday Operation P0 Safety Gates Go-Check

- Date: 2026-06-06
- Stage: go-check
- Scope:
  - `backend/service/HwiStockRunnerService.py`
  - `backend/lib/kis_paper_continuous_runtime.py`
  - `backend/lib/operator_console_runtime.py`
  - `backend/run.py`
  - `backend/run.sh`
  - `frontend-web/app/dashboard/operatorData.js`
  - `frontend-web/app/dashboard/view.jsx`
  - focused backend/frontend tests
- Broker/order side effect: no order endpoint was called by the smoke command in
  this evidence.
- Secrets: no secret values were read, printed, or committed.

## Changes Proven

1. Date-specific KST calendar rows are mandatory. A future cache expiry no longer
   turns a missing date or Saturday into a usable trading state.
2. KRX order preflight requires `krxOrderSessionOpen=true`.
3. The default local calendar cache now contains the Monday 2026-06-08 trading
   row and a short `validUntil` of 2026-06-10.
4. Account truth now comes from latest KIS read-step summaries, not AI/intent
   cash or holding fields.
5. Exit/realtime sell intents are prioritized ahead of new entry intents while
   preserving FIFO within each priority class.
6. Operator snapshot now reports live/effective user-systemd policy and runtime
   artifact freshness.
7. Dashboard now renders a freshness strip for stale/missing artifacts, effective
   order policy, and live unit/timer state.
8. `HwiStockRunnerService.py` runtime definitions were normalized to camelCase
   without profile exceptions; legacy snake aliases remain only where they do not
   violate the active rule gate.

## Validation

| Check | Result |
| --- | --- |
| `source ./env.sh && python3 -m pytest backend/tests/test_hwistock_runner.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_operational_go_check_pipeline.py` | PASS — 76 tests |
| `source ./env.sh && pnpm --dir frontend-web exec vitest run tests/dashboard.view.test.jsx` | PASS — 9 tests |
| `source ./env.sh && pnpm --dir frontend-web exec eslint app/dashboard/view.jsx app/dashboard/operatorData.js tests/dashboard.view.test.jsx` | PASS |
| `source ./env.sh && python3 -m py_compile backend/service/HwiStockRunnerService.py backend/run.py backend/lib/kis_paper_continuous_runtime.py backend/lib/operator_console_runtime.py backend/service/kis_paper_continuous_runner.py` | PASS |
| `source ./env.sh && python /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn` | PASS — 0 errors, 0 warnings, 0 suppressions |
| `source ./env.sh && python3 backend/service/HwiStockRunnerService.py --once --write-evidence --output-root "$tmpdir"` | PASS — Saturday order gate `blocked_calendar_non_trading_day`, evidence paths written, `brokerCallsEnabled=false` |

## Remaining Operational Notes

- This Go-Check hardens the Monday P0 safety layer. It does not by itself prove a
  full market-hours observation run.
- Runtime observation should still watch dashboard freshness, KIS read-step
  status, AI artifact cadence, and order-gate state during market hours.
