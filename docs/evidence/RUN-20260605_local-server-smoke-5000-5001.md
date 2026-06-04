---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-local-server-smoke-5000-5001
stage: check/runtime-smoke
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_refs:
  - docs/units/HWISTOCK-UNIT-002_home-server-paper-runner.md
  - docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md
module_refs:
  - docs/modules/HWISTOCK-MOD-001_trading-safety-core.md
  - docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-002_home-server-paper-runner.md
  - docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md
created_at: 2026-06-05
environment: local_only
route_class: no_delegation
route: local_runtime_smoke
---

# Local Server Smoke — 5000/5001

## 1. Verdict

PASS after local config override cleanup. The local frontend and backend can be
started and reached on the approved loopback ports, and the frontend BFF now
routes to the just-started `127.0.0.1:5001` backend.

Initial smoke in this run was PARTIAL because `frontend-web` BFF requests were
observed returning data from a backend whose `startedAt` did not match the
foreground `5001` backend. Safe non-printing config classification then found
routing drift in ignored local config files. Only routing keys were updated:

- `frontend-web/config.ini`: `APP.backendHost`, `APP.frontendHost`,
  `APP.runtime`, `API.base`
- `backend/config.ini`: `SERVER.port`, `SERVER.backendHost`,
  `SERVER.frontendHost`, `SERVER.bind_host`, `SERVER.runtime`

No secret values were printed, and no secret-bearing sections were reported.

Confirmed:

- backend foreground smoke server listened on `127.0.0.1:5001`;
- frontend foreground smoke server listened on `127.0.0.1:5000`;
- backend `/healthz`, `/readyz`, and hwiStock runner status returned 200;
- frontend `/login` returned 200;
- unauthenticated `/dashboard` correctly redirected to `/login`;
- unauthenticated `/api/session/bootstrap` correctly redirected to `/login`;
- BFF `/api/bff/healthz` returned the same `startedAt` as direct backend
  `/healthz`;
- BFF `/api/bff/api/v1/hwistock/runner/status` returned 200 with
  `liveOrdersEnabled=false` and `brokerCallsEnabled=false`;
- no KIS, broker, order, live trading, SSH tunnel, browser, deploy, or git
  operation was run.

## 2. Runtime Method

The `run.sh start-dev` wrappers printed successful startup, but their background
processes were not alive after the shell command returned in this Codex
execution environment. For reliable smoke evidence, both servers were then run
as foreground processes held by live Codex tool sessions.

Backend foreground launch shape:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1
cd backend
uvicorn server:app --host 127.0.0.1 --port 5001
```

Frontend foreground launch shape:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1
cd frontend-web
./node_modules/.bin/next dev --turbopack --hostname 127.0.0.1 --port 5000
```

Both foreground sessions were stopped with Ctrl-C after the smoke.

## 3. Smoke Results

Backend direct checks:

| URL | result | note |
| --- | --- | --- |
| `http://127.0.0.1:5001/healthz` | 200 JSON | process health OK |
| `http://127.0.0.1:5001/readyz` | 200 JSON | local DB readiness OK |
| `http://127.0.0.1:5001/api/v1/hwistock/runner/status` | 200 JSON | `liveOrdersEnabled=false`, `brokerCallsEnabled=false` |

Frontend direct checks:

| URL | result | note |
| --- | --- | --- |
| `http://127.0.0.1:5000/login` | 200 HTML | login route renders |
| `http://127.0.0.1:5000/dashboard` | 307 redirect | unauthenticated request redirects to `/login` |
| `http://127.0.0.1:5000/api/session/bootstrap` | 307 redirect | unauthenticated request redirects to `/login` |

Frontend BFF checks:

| URL | result | interpretation |
| --- | --- | --- |
| `http://127.0.0.1:5000/api/bff/healthz` | 200 JSON | response `startedAt` matched the direct 5001 backend |
| `http://127.0.0.1:5000/api/bff/api/v1/hwistock/runner/status` | 200 JSON | same runner status as direct backend |

The final BFF smoke confirms frontend-backend integration over local loopback
for the no-order runner status path.

## 4. Warnings / Non-Blockers

Frontend dev startup emitted:

```text
The "middleware" file convention is deprecated. Please use "proxy" instead.
```

The existing Node warning also appeared:

```text
DEP0205: module.register() is deprecated. Use module.registerHooks() instead.
```

A Next local-development warning about a slow filesystem was also observed.

These warnings do not block the port smoke, but remain cleanup candidates
because this project treats warnings as active cleanup targets unless accepted.

## 5. Follow-Up Required

Possible next proof steps:

1. Run browser/screenshot Prove after tunnel smoke if UI evidence is needed.
2. Schedule warning cleanup for Next middleware/proxy naming, Node DEP0205, and
   local slow-filesystem warning if the project chooses to keep warning-zero
   completion policy strict.

Follow-up note: hwibuntu SSH tunnel smoke was completed in
`docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md`.

Do not proceed to broker/KIS calls, live orders, public/LAN exposure, or
production deployment from this evidence.
