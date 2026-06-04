---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-007
type: unit
domain: frontend
name: Dashboard operator console
status: browser_prove_passed
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
prove_status: pass
priority: P1
source_of_truth: user_intent
work_class: product_ui
owner: hwi
updated_at: 2026-06-05
last_set:
  status: set
  report_id: RUN-20260602-unit-007-dashboard-operator-console-set
  context_fingerprint:
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-006
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md
evidence_refs:
  - docs/evidence/RUN-20260602_unit-007-dashboard-operator-console-set.md
  - docs/evidence/RUN-20260604_dashboard-design-review.md
  - docs/evidence/RUN-20260605_unit-007-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md
  - docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md
  - docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md
  - docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md
  - docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md
  - docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md
links:
  - HWISTOCK-MOD-006
---

# Dashboard Operator Console

## 1. Goal

Define the read-only web dashboard and AI conversation surface for hwiStock.

## 2. Included Scope

- Current holdings and paper/live mode state.
- Today PnL and daily summary.
- Candidate cards and risk flags.
- News/disclosure timeline.
- AI analysis status, 07:00 report, 20:00 report.
- Order/fill logs.
- Service health.
- AI conversation about stored reports and current state.
- Local-only default access through `127.0.0.1`, SSH tunnel, or Chrome Remote
  Desktop. Current local ports are dashboard/frontend `5000` and backend/API
  `5001`; hwibuntu access uses SSH local forwarding to hwiServer loopback.
- No-design fallback plus design collaboration through `agy` with Gemini Pro
  before Go.
- MyWebTemplate `frontend-web`/backend code skeleton reuse after stack selection.
- Desktop-first operator layout: persistent status header plus left summary,
  center data, and right AI/log panes. Mobile layout is deferred unless a future
  unit explicitly adds it.
- Read-only styling system: dashboard controls must not resemble execution
  controls or use primary trade-action affordances.
- Masked sensitive display primitive and sanitized error rendering for account
  identifiers, balances, credentials, and raw API/error payloads.

## 3. Excluded Scope

- Direct buy/sell buttons.
- Credential display.
- Broker adapter toggles, risk-parameter changes, prompt/model changes, service
  lifecycle controls, or live-readiness approval controls.
- MyWebTemplate `docs/` copy.
- Public internet exposure without access control.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | Dashboard has no order buttons | No direct buy/sell control exists | UI review | QA-001 |
| AC-02 | P0 | Sensitive data is masked | Credentials/account ids are absent | UI/API review | QA-002 |
| AC-03 | P1 | Operator can see core state | Holdings, PnL, candidates, reports, logs, and health are represented | UI review | QA-003 |
| AC-04 | P1 | Design route is defined | Gemini Pro via `agy` is used for design review when dashboard Set starts | review record | QA-004 |
| AC-05 | P0 | Dashboard is local-only by default | Dashboard/API bind `127.0.0.1`; dashboard/frontend uses port `5000`, backend/API uses port `5001`; remote access is SSH tunnel or Chrome Remote Desktop | config/network review | QA-005 |
| AC-06 | P0 | AI conversation is read-only | Conversation can inspect stored reports and sanitized state but cannot place orders or change configs | UI/API review | QA-006 |
| AC-07 | P1 | First screen is the operator console | No landing page; status, PnL, candidates, positions, intelligence, AI reports, logs, and conversation are visible | UI review | QA-007 |
| AC-08 | P0 | Read-only styling cannot imply execution | Filters, tabs, refresh, sorts, report controls, and conversation UI do not look like buy/sell or command execution controls | UI/design review | QA-008 |
| AC-09 | P0 | Sensitive value rendering uses masking primitives | Account ids, credential-like values, raw balances, and raw API/error JSON are masked or sanitized before display | component/API review | QA-009 |
| AC-10 | P1 | First screen uses desktop-first monitoring layout | Persistent status header and three-pane operator layout keep dense state scannable without mobile scope | UI/design review | QA-010 |
| AC-11 | P2 | AI conversation looks like explanation, not command shell | AI panel is styled as a report/mail-style thread rather than terminal/CLI control | UI/design review | QA-011 |

## 5. Decisions / Open Questions

- Decision: dashboard is read-only and has no direct buy/sell controls.
- Decision: default access is local-only `127.0.0.1`; remote access uses SSH
  tunnel or Chrome Remote Desktop.
- Decision: public/LAN IP exposure is excluded unless a future Set contract
  approves authenticated access controls.
- Decision: AI conversation reads stored reports and sanitized current state
  through backend APIs only; it cannot place orders or change system settings.
- Decision: first screen is the operator console, not a landing page.
- Decision: no prepared design source exists. Use no-design fallback and require
  `agy` Gemini Pro design review before Go.
- Decision: `agy` Gemini Pro dashboard design review completed with
  `ready_with_changes`; required findings are incorporated into AC-08 through
  AC-11.
- Design review evidence:
  `docs/evidence/RUN-20260604_dashboard-design-review.md`.
- Findings intake:
  `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md`.

## 6. Current Browser Prove Status

Browser UI re-Prove on 2026-06-05 passed after the login/API 500 fix.

Confirmed:

- the local Chrome/browser-use path renders the app through the hwibuntu tunnel;
- the public `/login` surface is hwiStock-branded and no longer exposes
  MyWebTemplate sample/demo copy or `/component` guidance;
- local sample login reaches the hwiStock operator console;
- dashboard stats/list APIs return 200 through the frontend BFF;
- the authenticated dashboard no longer displays `HTTP_500_INTERNAL`;
- the operator console is visually read-only and masks account-like values.

Current evidence:
`docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`.

Superseded failure evidence:
`docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md`.
