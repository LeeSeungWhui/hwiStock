---
schema_version: hwi.run_evidence/v0
stage: go-check
status: pass
project_root: /data/workspace/My/hwiStock
created_at_kst: 2026-06-07T14:05:00+09:00
scope:
  - canonical runtime investment-mode switch
  - user-systemd mode propagation
  - 2026-06-08 KIS paper/mock order-loop approval preflight
---

# RUN 2026-06-07 — Runtime Mode Systemd And Paper Approval

## Summary

The user-systemd runtime now loads a single local investment-mode switch from
`/home/hwi/.config/hwistock/runtime-mode.env` and normalizes it through
`ops/systemd/load_runtime_mode_env.sh`.

Paper/mock mode resolves to:

- `HWISTOCK_INVESTMENT_MODE=paper`
- `HWISTOCK_MARKET_ANALYSIS_FEED_MODE=integrated`
- `HWISTOCK_EXECUTION_VENUE_MODE=krx_only`
- `HWISTOCK_NXT_ENABLED=false`
- `HWISTOCK_NXT_READY_SET_APPROVED=false`

The 2026-06-08 paper/mock run is approved by local config only for the bounded
paper session:

- run id: `paper-20260608`
- approval file: `/home/hwi/.config/hwistock/approvals/paper-20260608.approval.json`
- valid date: `2026-06-08`
- valid until: `2026-06-08T15:00:00+09:00`
- max daily paper orders: `20`
- max paper notional: `2,000,000 KRW`
- live money scope: `not_applicable`

## Verification

- Focused pytest passed:
  - `backend/tests/test_kis_paper_continuous_runner.py::test_systemd_runner_enables_paper_experiment_orders_with_session_gate`
  - `backend/tests/test_kis_paper_continuous_runner.py::test_systemd_ai_and_market_ticks_use_shared_runtime_mode_policy`
  - `backend/tests/test_operational_go_check_pipeline.py::test_unit013_kis_collector_gates_nxt_by_investment_mode`
- Runtime loader shell check:
  - paper default: `paper krx_only false false`
  - paper with NXT env forced true: `paper krx_only false false`
  - live default: `live krx_only false false`
- Runtime policy dry-run:
  - paper `09:00` and `14:59`: order window open
  - paper `15:01`: order window closed, market-analysis context open
  - paper with NXT env forced true: `executionVenueMode=krx_only`, `nxtEnabled=false`
  - live `08:00` and `19:59`: order window open by policy, while live order
    execution remains unapproved and not enabled by this run
- User-systemd deployment:
  - installed `hwistock-*.service` and `hwistock-*.timer`
  - reloaded user systemd
  - restarted API/frontend
  - `systemctl --user list-units --failed 'hwistock*'`: 0 failed units
- Manual paper-runner one-shot after deploy:
  - `hwistock-kis-paper-runner.service`: `status=0/SUCCESS`
  - latest evidence path:
    `data/evidence/2026-06-07/kis-paper-continuous-latest.json`
  - Sunday evidence correctly reports `paper_order_requested=true`,
    `paper_order_enabled=false`, reason
    `order_approval_valid_for_date_mismatch`, because the approval is scoped to
    `2026-06-08`.
- Monday preflight dry-run at `2026-06-08T09:30:00 KST`:
  - `investment_mode=paper`
  - `execution_venue_mode=krx_only`
  - `nxt_enabled=false`
  - `paper_order_enabled=true`
  - `paper_order_loop_enabled=true`
  - `paper_experiment_readiness.ready=true`

## Remaining Boundary

This run does not approve or enable live-money trading. `HWISTOCK_INVESTMENT_MODE=live`
is a policy branch only until a future live-production unit, approval gate, and
broker proof explicitly enable it.
