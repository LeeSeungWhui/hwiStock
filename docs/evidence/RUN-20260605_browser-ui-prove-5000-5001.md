---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-browser-ui-prove-5000-5001
stage: prove/browser-ui
status: fail
current_authority: false
superseded_by: docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_refs:
  - docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md
module_refs:
  - docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md
supporting_refs:
  - docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md
  - docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md
  - docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md
created_at: 2026-06-05
environment: hwiServer_to_hwibuntu_ssh_browser_use
route_class: no_delegation
route: ssh_browser_use_chrome_extension
browser_artifacts:
  - docs/evidence/assets/RUN-20260605_browser-ui-prove/dashboard-redirect-login.png
  - docs/evidence/assets/RUN-20260605_browser-ui-prove/login-direct.png
  - docs/evidence/assets/RUN-20260605_browser-ui-prove/dashboard-after-demo-login.png
  - docs/evidence/assets/RUN-20260605_browser-ui-prove/browser-ui-prove-summary.json
---

# Browser UI Prove — 5000/5001 hwibuntu Tunnel

## 1. Verdict

FAIL for full browser UI Prove.

Confirmed positive behavior:

- SSH browser-use discovered the local Chrome Extension backend.
- hwiServer served the frontend on `127.0.0.1:5000` and backend on
  `127.0.0.1:5001`.
- hwibuntu exposed both ports through SSH local forwarding to hwiServer
  loopback.
- Browser navigation to `http://127.0.0.1:5000/dashboard` redirected an
  unauthenticated user to `/login`.
- The login page rendered in real Chrome through the hwibuntu tunnel.
- Using the visible sample credentials shown by the page reached the
  hwiStock operator console at `/dashboard`.
- The operator console is visually read-only and did not expose visible
  buy/sell/order execution buttons.
- Visible account-like values were masked in the operator console.
- No KIS, broker, order, live trading, deploy, public/LAN exposure, or git
  mutation was run.

Blocking product findings:

1. P1 — the unauthenticated login surface still exposes MyWebTemplate sample
   copy, demo credentials, and `/component` guidance.
2. P1 — after login, the dashboard renders but shows a visible data-load
   failure banner because `/api/v1/dashboard` and dashboard stats return 500.
   Backend logs show `TypeError: Object of type Decimal is not JSON
   serializable` while serializing dashboard response fields.

Because this is a browser Prove stage, the page can render is not enough. The
user-facing auth surface and the first operator console must be product-clean
and free of runtime API errors before UNIT-007 browser Prove can pass.

## 2. Evidence Artifacts

| artifact | purpose |
| --- | --- |
| `docs/evidence/assets/RUN-20260605_browser-ui-prove/dashboard-redirect-login.png` | `/dashboard` unauthenticated redirect landing on login |
| `docs/evidence/assets/RUN-20260605_browser-ui-prove/login-direct.png` | direct `/login` visual evidence |
| `docs/evidence/assets/RUN-20260605_browser-ui-prove/dashboard-after-demo-login.png` | visible hwiStock operator console after local sample login |
| `docs/evidence/assets/RUN-20260605_browser-ui-prove/browser-ui-prove-summary.json` | captured URL/title/text/assertion summary |

## 3. Browser Route

```text
hwiServer Codex session
-> node_repl_http
-> Chrome browser-client
-> SSH reverse Chrome Extension backend
-> local Chrome on hwibuntu
-> http://127.0.0.1:5000
-> hwibuntu SSH local forward
-> hwiServer 127.0.0.1:5000/5001
```

Observed browser backend:

```text
type=extension
name=Chrome
```

The browser-client emitted non-blocking Statsig POST warnings because the
node_repl HTTP route only allows the relevant authenticated fetch shape. The
warnings did not block navigation, interaction, or screenshot capture.

## 4. Browser Observations

### 4.1 Unauthenticated dashboard redirect

Requested:

```text
http://127.0.0.1:5000/dashboard
```

Observed:

```text
http://127.0.0.1:5000/login
title: Login | MyWebTemplate
```

Result:

- PASS: unauthenticated dashboard access is guarded by login redirect.
- FAIL: the public login page still displays template/sample copy.

Visible sample residue included:

```text
웹페이지 템플릿
샘플 로그인 화면
/component에서 컴포넌트 목록 조회
demo@demo.demo / password123
```

### 4.2 Direct login route

Requested:

```text
http://127.0.0.1:5000/login
```

Observed:

```text
title: Login | MyWebTemplate
```

Result:

- PASS: login route renders through the hwibuntu tunnel.
- FAIL: the direct public login route repeats the same template/sample/demo
  surface.

### 4.3 Local sample login to dashboard

Action:

```text
Fill the visible sample login credentials shown by the page.
Click the visible login button.
```

Observed after the login action:

```text
http://127.0.0.1:5000/dashboard
title: hwiStock 운영 콘솔
```

Result:

- PASS: the hwiStock operator console is reachable in the browser.
- PASS: the first authenticated screen is an operator-console style screen.
- PASS: visible account-like values are masked.
- PASS: no visible direct buy/sell/order execution button was present.
- FAIL: the console shows a visible data-load error:

```text
운영 콘솔 데이터를 불러오지 못했습니다.
code: HTTP_500_INTERNAL
```

Frontend dev log:

```text
POST /api/bff/api/v1/auth/login 200
GET /api/bff/api/v1/auth/me 200
GET /api/bff/api/v1/dashboard/stats 500
GET /api/bff/api/v1/dashboard 500
GET /dashboard 200
```

Backend failure root evidence:

```text
TypeError: Object of type Decimal is not JSON serializable
when serializing dict item 'amountSum'
when serializing dict item 'statusSummaryList'
```

and:

```text
TypeError: Object of type Decimal is not JSON serializable
when serializing dict item 'amount'
when serializing dict item 'dataTemplateList'
```

## 5. QA Row Matrix

| row_id | result | note |
| --- | --- | --- |
| QA-001 | PASS | no visible direct buy/sell/order execution button on the captured operator console |
| QA-002 | PARTIAL_PASS | visible account-like values are masked; full API payload privacy review remains separate |
| QA-003 | FAIL | operator state is visible only with fallback/degraded data because dashboard APIs return 500 |
| QA-004 | SUPPORTING | prior design review remains supporting evidence; not rerun in this browser Prove |
| QA-005 | PASS | loopback bind and hwibuntu tunnel shape were already proven by supporting smoke evidence |
| QA-006 | PASS_VISUAL | AI/report area is read-only; no order-changing input/control was visible |
| QA-007 | PARTIAL_PASS | authenticated first screen is an operator console, but it contains a visible data-load error |
| QA-008 | PASS_VISUAL | visible controls are read-only styled, not execution-styled trade controls |
| QA-009 | PARTIAL_PASS | visible values are masked; API serialization failure blocks clean payload confirmation |
| QA-010 | PASS_VISUAL | desktop monitoring layout is visible |
| QA-011 | PASS_VISUAL | AI panel reads as report/explanation cards rather than terminal/command shell |

## 6. Required Follow-up Before Browser Prove PASS

1. Replace/quarantine the public MyWebTemplate sample login surface:
   title, left-panel copy, demo credential hint, `/component` mention, and
   sample-dashboard wording.
2. Fix dashboard API JSON serialization for Decimal values in
   `backend/router/DashboardRouter.py` or its response conversion boundary.
3. Re-run browser UI Prove through hwibuntu tunnel and capture fresh
   `/login`, unauthenticated `/dashboard`, and authenticated `/dashboard`
   screenshots.

## 7. Boundary

This evidence does not authorize:

- KIS/broker/API calls;
- paper or live order placement;
- live trading;
- public/LAN dashboard exposure;
- deployment;
- git stage or commit.
