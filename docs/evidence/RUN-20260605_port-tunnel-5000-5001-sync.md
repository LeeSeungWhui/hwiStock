---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-port-tunnel-5000-5001-sync
stage: check/evidence-sync
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_refs:
  - docs/units/HWISTOCK-UNIT-002_home-server-adapter-runner.md
  - docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md
module_refs:
  - docs/modules/HWISTOCK-MOD-001_trading-safety-core.md
  - docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-002_home-server-adapter-runner.md
  - docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md
created_at: 2026-06-05
environment: local_only
route_class: no_delegation
route: local_docs_sync
---

# Port/Tunnel Evidence — 5000/5001 Local-Only Sync

## 1. Verdict

PASS. hwiStock local dashboard/API defaults are synchronized to:

- dashboard/frontend: `127.0.0.1:5000`
- backend/API: `127.0.0.1:5001`
- hwibuntu access path: SSH local forwarding from hwibuntu loopback to
  hwiServer loopback

This record does **not** prove browser rendering, server startup, or active tunnel
connectivity. It records static/default configuration, helper scripts, and
focused validation only. Runtime local-server and hwibuntu tunnel proof were
completed later in:

- `docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md`
- `docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md`

## 2. Access Model

The approved local access shape is:

```text
hwibuntu browser
  -> http://127.0.0.1:5000/dashboard
  -> SSH local forward
  -> hwiServer 127.0.0.1:5000 frontend
  -> hwiServer 127.0.0.1:5001 backend/API
```

Equivalent tunnel command from hwibuntu:

```bash
ssh -N -L 5000:127.0.0.1:5000 -L 5001:127.0.0.1:5001 hwiServer
```

Helper:

```text
ops/tunnel/hwibuntu-dashboard-tunnel.sh
```

Services must remain bound to loopback. This does not authorize `0.0.0.0`,
LAN/public IP exposure, reverse proxy exposure, broker/API calls, or operation
trading.

## 3. Changed Surfaces

Port/default sync touched:

- `AGENTS.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `backend/run.py`
- `backend/run.sh`
- `backend/config.example.ini`
- `backend/lib/OpenAPI.py`
- `backend/BackendTODO.txt`
- `backend/service/HwiStockRunnerService.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_audit_logging.py`
- `backend/tests/test_hwistock_runner.py`
- `frontend-web/package.json`
- `frontend-web/run.sh`
- `frontend-web/config.example.ini`
- `frontend-web/config_dev.ini`
- `frontend-web/config_prod.ini`
- `frontend-web/README.md`
- `frontend-web/app/common/config/getBackendHost.server.js`
- `frontend-web/app/common/config/getBackendHost.client.js`
- `frontend-web/app/common/config/getFrontendHost.server.js`
- `frontend-web/app/common/config/getFrontendHost.client.js`
- `frontend-web/app/api/bff/[...path]/route.js`
- `frontend-web/app/lib/runtime/api.js`
- `frontend-web/__tests__/middleware.test.jsx`
- `frontend-web/__tests__/sessionBootstrap.test.jsx`
- `frontend-web/__tests__/apiRuntime.test.jsx`
- `frontend-web/__tests__/frontendConfig.test.jsx`
- `ops/systemd/hwistock-api.service`
- `ops/tunnel/README.md`
- `ops/tunnel/hwibuntu-dashboard-tunnel.sh`

The local ignored `config.ini` files were not read or edited. Runtime
`config.ini` values may still override defaults and must be checked separately
without printing secrets before actual server startup.

## 4. Validation

Static stale-port scan:

```text
rg stale runtime/default port patterns for 2000/3000/2100/4001/public host
=> no matches in non-secret scanned scope
```

Frontend focused validation:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1 && pnpm --dir frontend-web test -- __tests__/middleware.test.jsx __tests__/sessionBootstrap.test.jsx __tests__/apiRuntime.test.jsx __tests__/frontendConfig.test.jsx
=> 27 files passed, 131 tests passed
=> Node DEP0205 warning only
```

Frontend lint:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1 && pnpm --dir frontend-web exec eslint app/common/config/getBackendHost.server.js app/common/config/getBackendHost.client.js app/common/config/getFrontendHost.server.js app/common/config/getFrontendHost.client.js app/api/bff/[...path]/route.js app/lib/runtime/api.js middleware.js __tests__/middleware.test.jsx __tests__/sessionBootstrap.test.jsx __tests__/apiRuntime.test.jsx __tests__/frontendConfig.test.jsx
=> exit 0
```

Backend runner validation:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1 && python3 -m pytest backend/tests/test_hwistock_runner.py
=> 32 passed
```

Python compile:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1 && python3 -m py_compile backend/run.py backend/lib/OpenAPI.py backend/service/HwiStockRunnerService.py
=> PASS
```

Shell/package syntax:

```text
bash -n backend/run.sh frontend-web/run.sh ops/tunnel/hwibuntu-dashboard-tunnel.sh
=> PASS

json.loads(frontend-web/package.json)
=> PASS
```

Whitespace/conflict check:

```text
git diff --check on changed port/tunnel files
=> PASS
```

## 5. Known Limitations / Next Proof

- No backend server was started.
- No frontend server was started.
- No SSH tunnel was opened.
- No browser or screenshot Prove was run.
- No broker/KIS/API/AI-provider/network operation was run.
- Local ignored `config.ini` files may override the synchronized defaults and
  must be checked safely before runtime smoke.

Later evidence closed the server-start, local ignored config override, and
hwibuntu HTTP tunnel proof gaps:

- `docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md`
- `docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md`
