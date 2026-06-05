---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-007
type: unit
domain: frontend
name: Dashboard operator console
status: go_check_passed_pending_browser_tunnel_prove
ready_set_rebaseline_status: ai_conversation_go_check_done
implementation_status: frontend_backend_ai_conversation_done
prove_status: pending_browser_tunnel_conversation_prove
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
design_refs:
  - docs/design/HWISTOCK-DESIGN-20260605_lucid-command-dashboard.md
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
  - docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md
  - docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md
corrective_set_refs:
  - docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md
links:
  - HWISTOCK-MOD-006
---

# Dashboard Operator Console

## 1. Goal

Define the read-only web dashboard and AI conversation surface for hwiStock.

## 2. Included Scope

- Current holdings and adapter-mode mode state.
- Today PnL and daily summary.
- Candidate cards and risk flags.
- News/disclosure timeline.
- AI analysis status and report viewer for stored Pro/Flash reports.
- Interactive AI conversation that lets the operator ask questions about stored
  reports, current dashboard state, candidates, positions, market intelligence,
  and audit logs through a dashboard input.
- Order/fill logs.
- Service health.
- AI conversation must be a real user-question flow, not only a static report
  card/thread. A report-only panel cannot satisfy this unit.
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
  lifecycle controls, or operation-readiness approval controls.
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
| AC-06 | P0 | AI conversation is interactive and read-only | Operator can submit a natural-language question through the dashboard; backend returns an answer grounded in stored reports and sanitized state, without placing orders or changing configs | UI/API/browser review | QA-006 |
| AC-07 | P1 | First screen is the operator console | No landing page; status, PnL, candidates, positions, intelligence, AI reports, logs, and conversation are visible | UI review | QA-007 |
| AC-08 | P0 | Read-only styling cannot imply execution | Filters, tabs, refresh, sorts, report controls, and conversation UI do not look like buy/sell or command execution controls | UI/design review | QA-008 |
| AC-09 | P0 | Sensitive value rendering uses masking primitives | Account ids, credential-like values, raw balances, and raw API/error JSON are masked or sanitized before display | component/API review | QA-009 |
| AC-10 | P1 | First screen uses desktop-first monitoring layout | Persistent status header and three-pane operator layout keep dense state scannable without mobile scope | UI/design review | QA-010 |
| AC-11 | P2 | AI conversation looks like explanation, not command shell | Conversation panel is styled as a report/mail-style Q&A thread rather than terminal/CLI control | UI/design review | QA-011 |
| AC-12 | P1 | AI report viewer remains available | Stored Pro/Flash report cards can be read without opening a conversation turn | UI/API review | QA-012 |
| AC-13 | P0 | Conversation input and endpoint exist | Dashboard includes a question input/submit affordance wired to a backend conversation endpoint; missing or disabled conversation input fails this unit | UI/API review | QA-013 |
| AC-14 | P0 | Conversation refuses unsafe requests | Order placement, risk setting changes, credential disclosure, provider prompt/model edits, and service lifecycle requests are refused with a visible explanation | UI/API log | QA-014 |
| AC-15 | P1 | Conversation is auditable | User question, sanitized context refs, answer, refusal reason when applicable, model/provider route, latency, and request id are logged without secrets | audit/API review | QA-015 |
| AC-16 | P0 | Static report panel is not enough | A dashboard that only renders `aiThread`/report cards without user question input and backend answer flow must remain `conversation_missing` | code/browser review | QA-016 |

## 5. Decisions / Open Questions

- Decision: dashboard is read-only and has no direct buy/sell controls.
- Decision: default access is local-only `127.0.0.1`; remote access uses SSH
  tunnel or Chrome Remote Desktop.
- Decision: public/LAN IP exposure is excluded unless a future Set contract
  approves authenticated access controls.
- Decision: AI report viewing and AI conversation are separate dashboard
  capabilities. Report cards alone are insufficient.
- Decision: AI conversation reads stored reports and sanitized current state
  through backend APIs only; it cannot place orders or change system settings.
- Decision: the corrected Go scope must add a real question input, submit flow,
  backend conversation endpoint, safe refusal behavior, and audit logging.
- Decision: first screen is the operator console, not a landing page.
- Decision: no prepared design source exists. Use no-design fallback and require
  `agy` Gemini Pro design review before Go.
- Decision: `agy` Gemini Pro dashboard design review completed with
  `ready_with_changes`; required findings are incorporated into AC-08 through
  AC-11.
- Decision: Lucid Command dark desktop-first operator cockpit design artifact
  recorded at
  `docs/design/HWISTOCK-DESIGN-20260605_lucid-command-dashboard.md`.
- Design review evidence:
  `docs/evidence/RUN-20260604_dashboard-design-review.md`.
- Findings intake:
  `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md`.

## 6. Current Browser Prove Status

Browser UI re-Prove on 2026-06-05 passed only for the login/API 500 fix,
read-only static dashboard rendering, and report-card style AI thread. It does
not by itself prove the full authenticated interactive AI conversation flow in
this corrected unit.

Confirmed:

- the local Chrome/browser-use path renders the app through the hwibuntu tunnel;
- the public `/login` surface is hwiStock-branded and no longer exposes
  MyWebTemplate sample/demo copy or `/component` guidance;
- local sample login reaches the hwiStock operator console;
- dashboard stats/list APIs return 200 through the frontend BFF;
- the authenticated dashboard no longer displays `HTTP_500_INTERNAL`;
- the operator console is visually read-only and masks account-like values;
- stored AI report cards can render as a read-only thread.

Current status after backend Go-Check:

- dashboard question input/submit affordance and frontend POST wiring are now
  proven in `docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md`;
- backend AI conversation endpoint, safe refusal, grounded artifact answer, and
  local audit logging are now proven in
  `docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`;
- browser/tunnel Prove has not yet exercised the authenticated dashboard input
  against the running backend endpoint;
- QA rows that previously allowed "conversation unavailable" as PASS are
  superseded by this correction.

Current evidence:
`docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`.

Superseded failure evidence:
`docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md`.
