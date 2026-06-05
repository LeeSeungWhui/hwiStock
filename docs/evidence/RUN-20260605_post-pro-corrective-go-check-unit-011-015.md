# RUN-20260605 post-Pro corrective Go-Check UNIT-011/015

Date: 2026-06-05 KST
Workspace: `/data/workspace/My/hwiStock`

## Scope

Corrective Go-Check for the existing operational Ready-Set reinforcement rows:

- `HWISTOCK-UNIT-011`: runtime entrypoint/systemd hardening.
- `HWISTOCK-UNIT-015`: dashboard/API readiness truth surface.

This is not a new Ready-Set. It reinforces the existing operational Ready-Set:

- `docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-automated-trading-program_hwistock.md`
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-automated-trading-program_hwistock.md`

No broker order, KIS unapproved endpoint, account-affecting action, credential print, or
public bind was performed.

## Changes

### UNIT-011 runtime entrypoint hardening

- `backend/run.py` no longer hardcodes `reload=True`.
- `resolveReloadEnabled(config)` defaults to false.
- Development reload now requires explicit `HWISTOCK_BACKEND_RELOAD=true` or
  `SERVER.reload=true`.
- `ops/systemd/user/hwistock-api.service` already starts uvicorn without
  `--reload`; focused tests now assert that the service template does not
  include reload flags.

### UNIT-015 readiness truth surface

- `backend/lib/operator_console_runtime.py` now emits `readinessTruth` with:
  - `headline=NOT_READY_FOR_PAPER_TRADING`;
  - `serviceVisibilityIsNotReadiness=true`;
  - adapter network/order/observation/operational readiness booleans;
  - `orderGate`;
  - blocker codes including `blocked_calendar_unconfigured` where applicable.
- `frontend-web/app/dashboard/view.jsx` renders a large
  `operator-readiness-truth` alert before the status strip.
- Fallback fixture data now carries explicit not-ready/fallback blockers so a
  fallback dashboard cannot look like account-affecting operational truth.

## Validation

### Python compile

```text
source ./env.sh && python3 -m py_compile \
  backend/run.py \
  backend/lib/operator_console_runtime.py \
  backend/tests/test_hwistock_runner.py \
  backend/tests/test_operational_go_check_pipeline.py
```

Result: pass.

### Backend focused tests

```text
source ./env.sh && python3 -m pytest \
  backend/tests/test_hwistock_runner.py \
  backend/tests/test_operational_go_check_pipeline.py -q
```

Result:

```text
41 passed
```

### Frontend focused tests

```text
source ./env.sh && cd frontend-web && pnpm exec vitest run \
  tests/dashboard.view.test.jsx \
  __tests__/dashboardDataStrategy.test.jsx
```

Result:

```text
2 test files passed
11 tests passed
```

### Rule gate

```text
source ./env.sh && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py \
  /data/workspace/My/hwiStock \
  --changed \
  --fail-on-warn \
  --profile docs/profiles/PROFILE-HWISTOCK.md
```

Result:

```text
Status: pass
Findings: error=0 warning=0 info=0
```

### Runtime smoke

The local API/frontend user services were restarted to load the new backend and
frontend code:

```text
systemctl --user restart hwistock-api.service hwistock-frontend.service
```

Observed:

```text
hwistock-api.service active
hwistock-frontend.service active
```

Local API smoke:

```text
GET http://127.0.0.1:5001/api/v1/hwistock/runner/operator-snapshot
```

Sanitized result:

```text
readinessTruth.headline=NOT_READY_FOR_PAPER_TRADING
serviceVisibilityIsNotReadiness=true
blockers=paper_network_disabled,paper_orders_not_submitted,paper_observation_not_accepted,operational_readiness_false,blocked_calendar_unconfigured
operationalReadiness=false
orderGate=blocked_calendar_unconfigured
```

HTTP smoke:

```text
frontend:307
api:200
```

hwibuntu tunnel smoke:

```text
readinessTruth.headline=NOT_READY_FOR_PAPER_TRADING
orderGate=blocked_calendar_unconfigured
operationalReadiness=false
hwibuntu_frontend:307
hwibuntu_api:200
```

## Check verdict

PASS for the corrective Go-Check scope:

- UNIT-011 runtime entrypoint reload ambiguity is closed for the local
  service-managed runtime.
- UNIT-015 operator snapshot and dashboard now expose false readiness loudly.
- Service/timer visibility is explicitly separated from operation readiness.

Remaining blockers for operation readiness:

- KIS broker adapter market/order side-effect rows are still not proved as a complete
  operation observation run.
- Calendar/source readiness still blocks the current order gate.
- Browser visual proof of the new banner was not captured in this Go-Check; the
  API/tunnel smoke proves the data contract and frontend tests prove rendering.
