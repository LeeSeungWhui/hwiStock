---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-browser-ui-reprove-login-api500
stage: prove/browser-ui
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_refs:
  - docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md
module_refs:
  - docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md
supporting_refs:
  - docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md
  - docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md
  - docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md
  - docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md
created_at: 2026-06-05
environment: hwiServer_to_hwibuntu_ssh_browser_use
route_class: implementation_worker_then_orchestrator_verify
implementation_worker_route: cursor-sdk-local
implementation_worker_model: composer-2.5
browser_route: ssh_browser_use_chrome_extension
browser_artifacts:
  - docs/evidence/assets/RUN-20260605_browser-ui-reprove-login-api500/login-fixed.png
  - docs/evidence/assets/RUN-20260605_browser-ui-reprove-login-api500/dashboard-after-login-fixed.png
  - docs/evidence/assets/RUN-20260605_browser-ui-reprove-login-api500/browser-ui-reprove-summary.json
supersedes:
  - docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md
---

# Browser UI Re-Prove — Login/API 500 Fix

## 1. Verdict

PASS for the UNIT-007 browser UI re-Prove after the login public-surface and
dashboard API 500 fixes.

Confirmed:

- `frontend-web` served on hwiServer `127.0.0.1:5000`.
- `backend` served on hwiServer `127.0.0.1:5001`.
- hwibuntu exposed both ports through SSH local forwarding to hwiServer
  loopback.
- SSH browser-use discovered the local Chrome Extension backend.
- The public login page rendered as hwiStock, not MyWebTemplate.
- The login page no longer visibly exposed template/sample/demo copy,
  `/component` guidance, or sample credential hints.
- After sample local login, the browser reached `/dashboard`.
- Dashboard stats and list APIs returned 200 through the frontend BFF.
- The dashboard no longer displayed `HTTP_500_INTERNAL`.
- The first authenticated dashboard screen remained read-only and masked
  account-like values.
- No KIS, broker, order, live trading, deploy, public/LAN exposure, or git
  mutation was run.

## 2. Implementation Route / Worker Audit

Delegation route used for the code patch:

```text
route_class: implementation_worker
adapter: cursor-sdk-local
worker/model/reasoning: hwi-cursor-worker / composer-2.5 / medium
workspace: /data/workspace/My/hwiStock direct project cwd
```

Worker attempt history:

| attempt | result | note |
| --- | --- | --- |
| contract dry-run #1 | quarantined | contract fields were malformed for the wrapper parser; no product output accepted |
| real worker #1 | quarantined | worker produced a sentinel, but wrapper rejected the run with `scope_violation` because focused backend validation created `backend/logs/20260605_031645.log` outside the allowed write set |
| real worker #2 | accepted | contract allowed focused validation log side effects under `backend/logs`; wrapper accepted `WORKER_RESULT: DONE` |

Accepted worker transcript:

```text
/tmp/hwi-worker-hwistock-unit007-login-api500/transcript-2.log
```

Acceptance note: the wrapper accepted the second run, but the worker sentinel's
declared read list included additional login-route files such as
`frontend-web/app/login/view.jsx`, `page.jsx`, and `initData.jsx` beyond the
initial contract read list. These were same-scope, non-secret, read-only login
files, so the orchestrator treated them as a non-blocking acceptance anomaly and
verified the final diff locally before marking this re-Prove PASS.

Accepted worker changes were then verified by the orchestrator before this
evidence was marked PASS.

## 3. Code/Behavior Changes Verified

- Login Korean resources now identify the page as hwiStock:
  - title: `Login | hwiStock`
  - visible public copy: `hwiStock 운영 콘솔`, `운영자 인증`
- Login public UI no longer displays MyWebTemplate/sample/demo guidance.
- Backend response serialization now converts nested `Decimal` values before
  JSON response emission.
- Dashboard list/stats responses convert Decimal-like amount fields to
  JSON-safe numeric values.
- Focused tests cover the login copy quarantine and dashboard Decimal response
  serialization.

## 4. Validation

Focused automated validation:

| command | result |
| --- | --- |
| `cd backend && pytest tests/test_dashboard_api.py tests/test_dashboard_service.py` | PASS, 8 tests |
| `cd frontend-web && npm test -- --run tests/login.view.test.jsx tests/dashboard.view.test.jsx` | PASS, 2 files / 13 tests |
| `git diff --check` | PASS |

Focused local HTTP smoke:

| path | result |
| --- | --- |
| `GET /login` | 200 |
| `POST /api/bff/api/v1/auth/login` | 200 |
| `GET /api/bff/api/v1/auth/me` | 200 |
| `GET /api/bff/api/v1/dashboard/stats` | 200 JSON |
| `GET /api/bff/api/v1/dashboard?page=1&size=10` | 200 JSON |
| `GET /dashboard` | 200 |

## 5. Browser Route

```text
hwiServer Codex session
-> node_repl_http
-> Chrome browser-client
-> SSH reverse Chrome Extension backend
-> local Chrome on hwibuntu
-> http://localhost:5000
-> hwibuntu SSH local forward
-> hwiServer 127.0.0.1:5000/5001
```

The previous browser tab already held an authenticated `127.0.0.1` cookie.
For a clean unauthenticated login-page proof without clearing the user's whole
Chrome profile, this re-Prove used `localhost:5000`, which maps to the same
hwibuntu loopback tunnel while using a separate browser cookie host. This did
not expose the service beyond loopback.

Observed browser backend:

```text
type=extension
name=Chrome
```

## 6. Browser Evidence

| artifact | purpose |
| --- | --- |
| `docs/evidence/assets/RUN-20260605_browser-ui-reprove-login-api500/login-fixed.png` | public login visual evidence after copy quarantine |
| `docs/evidence/assets/RUN-20260605_browser-ui-reprove-login-api500/dashboard-after-login-fixed.png` | authenticated dashboard visual evidence after API 500 fix |
| `docs/evidence/assets/RUN-20260605_browser-ui-reprove-login-api500/browser-ui-reprove-summary.json` | captured URL/title/text/assertion summary |

Captured browser assertions:

```json
{
  "verdict": "pass",
  "baseUrl": "http://localhost:5000",
  "login": {
    "url": "http://localhost:5000/login",
    "title": "Login | hwiStock",
    "loginFieldCount": {
      "email": 1,
      "password": 1
    },
    "hwiStockVisible": true,
    "templateResidueVisible": false
  },
  "dashboard": {
    "url": "http://localhost:5000/dashboard",
    "title": "hwiStock 운영 콘솔",
    "reachedDashboard": true,
    "api500Visible": false,
    "directOrderControlTextVisible": false,
    "maskedValueVisible": true
  }
}
```

## 7. QA Row Matrix

| row_id | result | note |
| --- | --- | --- |
| QA-001 | PASS | no visible direct buy/sell/order execution button on the captured operator console |
| QA-002 | PASS_VISUAL | visible account-like values are masked on the dashboard |
| QA-003 | PASS | holdings, candidates, AI reports, audit timeline, and health/context surfaces render without dashboard API 500 |
| QA-004 | SUPPORTING | prior design review remains supporting evidence; not rerun in this re-Prove |
| QA-005 | PASS | loopback bind and hwibuntu tunnel shape are proven by supporting smoke evidence |
| QA-006 | PASS_VISUAL | AI/report area is read-only; no order-changing input/control was visible |
| QA-007 | PASS | authenticated first screen is the hwiStock operator console without the previous data-load error |
| QA-008 | PASS_VISUAL | visible controls are read-only styled, not execution-styled trade controls |
| QA-009 | PASS_VISUAL | visible account-like values are masked; raw error JSON was not displayed |
| QA-010 | PASS_VISUAL | desktop monitoring layout is visible |
| QA-011 | PASS_VISUAL | AI panel reads as report/explanation cards rather than terminal/command shell |

## 8. Remaining Notes

- The dashboard still shows `degraded` service state and fixture-style data
  source labels. That is acceptable for this local skeleton/browser Prove and
  is not an authorization for live broker operation.
- Frontend dev runtime still warns about the Next middleware-to-proxy migration,
  slow filesystem, and Node `DEP0205`. These are not the login/API 500 blocker
  but remain cleanup candidates.

## 9. Boundary

This evidence does not authorize:

- KIS/broker/API calls;
- paper or live order placement;
- live trading;
- public/LAN dashboard exposure;
- deployment;
- git stage or commit.
