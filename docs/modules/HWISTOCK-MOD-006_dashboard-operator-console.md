---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-006
type: module
domain: frontend
name: Dashboard operator console
spec_status: set
build_status: frontend_backend_ai_conversation_done
verification_status: go_check_passed_backend_frontend_tests_pending_browser_prove
ready_set_rebaseline_status: ai_conversation_go_check_done
prove_status: pending_browser_tunnel_conversation_prove
post_pro_readiness_truth_status: go_check_passed_api_frontend_tunnel_smoke
priority: P1
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-05
go_check_evidence_refs:
  - docs/evidence/RUN-20260605_unit-007-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md
  - docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md
  - docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md
  - docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md
  - docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md
  - docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md
  - docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md
prove_evidence_refs:
  - docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md
  - docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md
corrective_set_refs:
  - docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md
design_refs:
  - docs/design/HWISTOCK-DESIGN-20260605_lucid-command-dashboard.md
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
links:
  - PROFILE-HWISTOCK
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-007
---

# Dashboard Operator Console

> Post-Pro readiness note (2026-06-05): browser rendering proof is not enough.
> The dashboard must loudly expose false readiness, order-gate blocks, adapter
> network/order/observation state, and fallback-data state before it can be used
> as the operational observation truth surface.
> The local API/frontend/tunnel Go-Check for this readiness truth surface passed
> in `docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md`;
> browser visual re-Prove is still a later evidence row.
>
> AI conversation correction (2026-06-05): the dashboard report cards are not
> enough. The Lucid Command frontend now has separate stored report and Q&A
> surfaces with POST wiring. The backend conversation endpoint, grounded local
> answer/refusal behavior, and audit evidence are implemented and focused-tested;
> browser/tunnel Prove remains the next evidence row.

## 1. Purpose

This module owns the read-only web dashboard and investor-AI conversation
surface. It is for understanding the system state, AI reports, candidates,
positions, logs, and daily review. It must not expose direct buy/sell controls.

## 2. Product / Capability Contract

- Dashboard is read-only for trading actions.
- No direct manual buy/sell buttons.
- It may show current holdings, today PnL, candidate cards, AI analysis state,
  news/disclosure timeline, risk flags, order/fill logs, stored Pro/Flash
  reports, service health, and AI conversation.
- It may include operator controls for non-ordering actions such as refresh,
  filter, log export, and kill-switch visibility. Any future kill-switch action
  requires an explicit Set decision.
- Dashboard access must be restricted when deployed on the home server.
- Default access policy is local-only: bind dashboard/API surfaces to
  `127.0.0.1` and access through local browser, Chrome Remote Desktop, or SSH
  tunnel. The current local ports are dashboard/frontend `5000` and backend/API
  `5001`; hwibuntu access uses SSH local forwarding to hwiServer loopback.
  LAN/public IP exposure requires a later explicit Set contract with
  authentication and allowlist/VPN/reverse-proxy controls.
- "Only people who know the IP/URL can find it" is not accepted as access
  control.
- Frontend design collaboration route: no-design fallback plus Antigravity CLI
  `agy` with Gemini Pro before Go.
- MyWebTemplate may be reused as a code skeleton for `frontend-web` and backend
  API patterns, but MyWebTemplate `docs/` must not be copied.
- First screen should be the actual operator console, not a landing page.
  Required first-screen sections:
  - status strip: mode, KST time/trading window, venue route, kill-switch state,
    service health, and data-source health
  - account summary: adapter-mode-readonly mode, cash reserve, system-calculated
    PnL, open-position count, and today's risk rejects
  - candidates/watchlist with reason, source ids, AI status, risk flags, and
    order eligibility state
  - holdings/positions and order-state timeline
  - market-intelligence timeline for news/disclosures/source events
  - AI job/report viewer for hourly Pro analysis, Flash trade documents, 07:00
    morning review, and 20:00 daily close
  - audit log/error panel
  - AI conversation panel scoped to stored reports and sanitized current state,
    with a real question input, submit flow, answer display, safe refusal display,
    and request/audit metadata
- Dashboard visual model is desktop-first for the initial implementation. Use a
  persistent global status header and a three-pane operator layout:
  left summary/context, center holdings/candidates/intelligence data, and right
  AI report viewer plus AI Q&A conversation plus audit/error timeline. Mobile
  responsiveness is deferred unless a future unit explicitly adds it.
- Dashboard interactions must look read-only. Do not use primary action button
  variants, trade-like red/green execution affordances, or command-console
  styling for filters, tabs, sorts, refresh, or report controls. Reserve strong
  color for severity/state indicators such as kill-switch, stale data, or
  errors.
- Sensitive display must go through a masking/redaction primitive such as
  `MaskedValue`. Account identifiers, credential-like values, raw balances, and
  raw API/error JSON must be masked or sanitized before rendering.
- The AI report viewer must let the operator read stored Pro/Flash outputs.
- The AI conversation surface must let the operator ask a natural-language
  question and receive a grounded answer. It must look like a read-only
  report/explanation Q&A thread, not a terminal or command shell.
- A static `aiThread`/report-card panel without question input and backend answer
  flow does not satisfy the AI conversation capability.

## 3. Interfaces

Future interfaces:

- dashboard API
- websocket or polling state feed
- AI report viewer
- candidate-card viewer
- position/PnL viewer
- order log viewer
- market-intelligence timeline
- AI report viewer endpoint or report slice from the operator snapshot
- AI conversation endpoint, for example a POST endpoint that accepts a sanitized
  operator question and returns a grounded answer/refusal plus request metadata

AI conversation constraints:

- The frontend never calls AI providers directly.
- The conversation backend may read stored reports, candidate cards, sanitized
  current state, and audit summaries.
- The conversation backend must accept an operator question, build a sanitized
  context bundle from stored artifacts/current state, and return either a
  grounded answer or an explicit refusal.
- The conversation backend must log question metadata, sanitized context refs,
  answer/refusal result, model/provider route, latency, and request id without
  credentials or raw secret values.
- It must not receive broker credentials, raw account numbers, API keys, or
  private account identifiers.
- It cannot place orders, change risk parameters, enable broker adapters, change
  prompt/model settings, or alter service lifecycle state.

## 4. Decisions / Open Questions

- Decision: dashboard is read-only for orders.
- Decision: design route is `agy` + Gemini Pro.
- Decision: no prepared design source exists; use no-design fallback grounded in
  this module, then run `agy` Gemini Pro design review before dashboard Go.
- Decision: default access is local-only `127.0.0.1`; remote access is through
  SSH tunnel or Chrome Remote Desktop unless a future authenticated exposure Set
  contract is approved.
- Decision: first screen is an operator console with status, PnL, candidates,
  positions, market-intelligence timeline, AI reports, logs, and AI conversation.
- Decision: AI report viewing and AI conversation are separate capabilities;
  report viewing alone is partial and cannot close the conversation requirement.
- Decision: dashboard design review result is `ready_with_changes`; P0/P1
  findings are incorporated as read-only styling, `MaskedValue` redaction,
  desktop-first three-pane layout, and report-style AI conversation
  requirements.
- Decision: Lucid Command visual model and implementation guardrails are
  recorded in
  `docs/design/HWISTOCK-DESIGN-20260605_lucid-command-dashboard.md`.
- Decision: MyWebTemplate docs are not reused.
- Design review evidence:
  `docs/evidence/RUN-20260604_dashboard-design-review.md`.
  Findings intake:
  `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md`.
- Browser UI Prove initially failed on 2026-06-05 because the public login
  surface still exposed MyWebTemplate sample/demo copy and the authenticated
  dashboard showed `HTTP_500_INTERNAL` from Decimal JSON serialization. The
  follow-up re-Prove passed after login copy quarantine and dashboard response
  JSON-safe conversion. That evidence is now interpreted as static report-viewer
  and browser-rendering proof only, not interactive AI conversation proof.
  Current evidence:
  `docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`; superseded
  failure evidence:
  `docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md`.
