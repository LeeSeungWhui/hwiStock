---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-hwibuntu-tunnel-smoke-5000-5001
stage: check/runtime-tunnel-smoke
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
supporting_refs:
  - docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md
  - docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md
created_at: 2026-06-05
environment: hwiServer_to_hwibuntu_ssh_tunnel
route_class: no_delegation
route: local_runtime_plus_ssh_tunnel_smoke
---

# hwibuntu Tunnel Smoke — 5000/5001

## 1. Verdict

PASS. `hwibuntu` can reach the hwiStock local-only runtime through SSH local
forwarding while the actual frontend/backend services remain bound to
`hwiServer` loopback.

Confirmed:

- hwiServer backend listened on `127.0.0.1:5001`;
- hwiServer frontend listened on `127.0.0.1:5000`;
- hwibuntu created local SSH forwards:
  - `127.0.0.1:5000 -> hwiServer 127.0.0.1:5000`
  - `127.0.0.1:5001 -> hwiServer 127.0.0.1:5001`
- hwibuntu HTTP checks over its own loopback returned expected responses;
- frontend BFF over the hwibuntu tunnel reached the same backend instance as
  direct backend tunnel checks;
- no KIS, broker, order, account-affecting operation, browser, deploy, public/LAN exposure, or
  git operation was run.

This smoke proves the SSH tunnel access shape for HTTP-level checks. It does
not prove visual browser rendering or screenshot evidence.

## 2. Runtime / Tunnel Shape

hwiServer runtime launch shape:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1
cd backend
uvicorn server:app --host 127.0.0.1 --port 5001
```

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1
cd frontend-web
./node_modules/.bin/next dev --turbopack --hostname 127.0.0.1 --port 5000
```

hwibuntu tunnel shape:

```text
ssh -o BatchMode=yes -o ExitOnForwardFailure=yes -N \
  -L 5000:127.0.0.1:5000 \
  -L 5001:127.0.0.1:5001 \
  hwiServer
```

The project helper `ops/tunnel/hwibuntu-dashboard-tunnel.sh` uses the same
forwarding shape.

All runtime and tunnel processes were stopped after the smoke. Final port scans
showed no remaining `5000`/`5001` listeners on hwiServer or hwibuntu.

## 3. hwibuntu HTTP Results

All URLs below were called from hwibuntu against hwibuntu loopback.

| URL | result | note |
| --- | --- | --- |
| `http://127.0.0.1:5001/healthz` | 200 JSON | direct backend over tunnel |
| `http://127.0.0.1:5000/api/bff/healthz` | 200 JSON | BFF backend `startedAt` matched direct backend |
| `http://127.0.0.1:5001/api/v1/hwistock/runner/status` | 200 JSON | direct runner over tunnel |
| `http://127.0.0.1:5000/api/bff/api/v1/hwistock/runner/status` | 200 JSON | BFF runner over tunnel |
| `http://127.0.0.1:5000/login` | 200 HTML | login route renders over tunnel |
| `http://127.0.0.1:5000/dashboard` | 307 redirect | unauthenticated dashboard redirects to `/login` |
| `http://127.0.0.1:5000/api/session/bootstrap` | 307 redirect | unauthenticated bootstrap redirects to `/login` |

Runner safety flags confirmed over BFF/tunnel:

```text
liveOrdersEnabled=false
brokerCallsEnabled=false
orderExecution=no_order_dry_run
```

Tunnel assertions:

```text
HWIBUNTU_TUNNEL_BFF_STARTED_AT_MATCH=PASS
HWIBUNTU_TUNNEL_BFF_RUNNER_MATCH=PASS
HWIBUNTU_TUNNEL_SAFETY_FLAGS=PASS
```

## 4. Notes / Warnings

Frontend dev startup emitted the existing warning:

```text
The "middleware" file convention is deprecated. Please use "proxy" instead.
```

This warning did not block tunnel smoke, but remains a cleanup candidate under
the project's warning-cleanup policy.

The first remote HTTP probe attempt failed because of a smoke-script formatting
bug in the test harness. The corrected probe was rerun successfully. No product
failure was inferred from that script error.

## 5. Remaining Proof Boundary

- Browser/screenshot Prove is still not run.
- KIS/broker/API/provider calls are still not authorized by this evidence.
- Account-affecting operation, public/LAN exposure, deployment, and git mutation are still not
  authorized by this evidence.
