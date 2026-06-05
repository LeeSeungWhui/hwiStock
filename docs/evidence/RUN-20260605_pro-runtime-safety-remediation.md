# RUN-20260605 Pro Runtime Safety Remediation

Date: 2026-06-05 KST
Workspace: `/data/workspace/My/hwiStock`

## Trigger

External Pro review flagged that the repository and installed user systemd KIS
runner could enable broker-adapter order submission while the docs and operator
console still declared operational readiness false.

## Remediation

- `ops/systemd/user/hwistock-kis-paper-runner.service`
  - Keeps KIS broker-adapter read/reconciliation network ticks enabled through
    `--allow-paper-network`.
  - Sets `HWISTOCK_KIS_PAPER_ORDER_ENABLED=false`.
  - Does not pass `--allow-paper-orders`.
- `backend/lib/kis_paper_continuous_runtime.py`
  - Requires `HWISTOCK_ORDER_APPROVAL_FILE` and
    `HWISTOCK_OPERATOR_APPROVED_ORDER_RUN_ID` before an order-requested run can
    become order-enabled.
  - Creates an atomic per-intent claim file before broker order submission.
  - Records ambiguous/warn/exception submit outcomes and blocks retry until
    reconciliation clears the idempotency key.
- `backend/lib/operator_console_runtime.py`
  - Inspects the repo/user systemd runner service file without reading secret
    env files.
  - Surfaces service-level paper network/order flags in the operator snapshot.
  - Adds `systemd_order_enabled_contradicts_readiness` when a runner service
    enables orders while operational readiness is false.
- `frontend-web/app/dashboard/view.jsx`
  - Shows the runner order-enabled truth value in the readiness banner.
- `docs/index.md`
  - Separates historical UNIT-003 collector evidence from later DeepSeek timer
    installation evidence.
  - Keeps broker/continuous/operational readiness false until side-effect rows
    and observation acceptance close.

## Required Validation

- `source ./env.sh && python3 -m pytest backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_operational_go_check_pipeline.py`
- `source ./env.sh && pnpm --dir frontend-web exec vitest run tests/dashboard.view.test.jsx`
- `source ./env.sh && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --changed --fail-on-warn --profile docs/profiles/PROFILE-HWISTOCK.md`
- `source ./env.sh && pnpm --dir frontend-web build`

