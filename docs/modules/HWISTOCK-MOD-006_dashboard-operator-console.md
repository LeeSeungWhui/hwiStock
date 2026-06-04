---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-006
type: module
domain: frontend
name: Dashboard operator console
spec_status: set
build_status: planned
verification_status: pending
priority: P1
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-04
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
links:
  - PROFILE-HWISTOCK
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-007
---

# Dashboard Operator Console

## 1. Purpose

This module owns the read-only web dashboard and investor-AI conversation
surface. It is for understanding the system state, AI reports, candidates,
positions, logs, and daily review. It must not expose direct buy/sell controls.

## 2. Product / Capability Contract

- Dashboard is read-only for trading actions.
- No direct manual buy/sell buttons.
- It may show current holdings, today PnL, candidate cards, AI analysis state,
  news/disclosure timeline, risk flags, order/fill logs, 07:00 morning report,
  20:00 daily report, service health, and AI conversation.
- It may include operator controls for non-ordering actions such as refresh,
  filter, log export, and kill-switch visibility. Any future kill-switch action
  requires an explicit Set decision.
- Dashboard access must be restricted when deployed on the home server.
- Default access policy is local-only: bind dashboard/API surfaces to
  `127.0.0.1` and access through local browser, Chrome Remote Desktop, or SSH
  tunnel. LAN/public IP exposure requires a later explicit Set contract with
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
  - account summary: paper/live-readonly mode, cash reserve, system-calculated
    PnL, open-position count, and today's risk rejects
  - candidates/watchlist with reason, source ids, AI status, risk flags, and
    order eligibility state
  - holdings/positions and order-state timeline
  - market-intelligence timeline for news/disclosures/source events
  - AI job/report panel for hourly analysis, 07:00 morning review, and 20:00
    daily close
  - audit log/error panel
  - AI conversation panel scoped to stored reports and sanitized current state
- Dashboard visual model is desktop-first for the initial implementation. Use a
  persistent global status header and a three-pane operator layout:
  left summary/context, center holdings/candidates/intelligence data, and right
  AI/report thread plus audit/error timeline. Mobile responsiveness is deferred
  unless a future unit explicitly adds it.
- Dashboard interactions must look read-only. Do not use primary action button
  variants, trade-like red/green execution affordances, or command-console
  styling for filters, tabs, sorts, refresh, or report controls. Reserve strong
  color for severity/state indicators such as kill-switch, stale data, or
  errors.
- Sensitive display must go through a masking/redaction primitive such as
  `MaskedValue`. Account identifiers, credential-like values, raw balances, and
  raw API/error JSON must be masked or sanitized before rendering.
- The AI conversation surface must look like a read-only report/explanation
  thread, not a terminal or command shell.

## 3. Interfaces

Future interfaces:

- dashboard API
- websocket or polling state feed
- AI report viewer
- candidate-card viewer
- position/PnL viewer
- order log viewer
- market-intelligence timeline
- AI conversation endpoint

AI conversation constraints:

- The frontend never calls AI providers directly.
- The conversation backend may read stored reports, candidate cards, sanitized
  current state, and audit summaries.
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
- Decision: dashboard design review result is `ready_with_changes`; P0/P1
  findings are incorporated as read-only styling, `MaskedValue` redaction,
  desktop-first three-pane layout, and report-style AI conversation
  requirements.
- Decision: MyWebTemplate docs are not reused.
- Design review evidence:
  `docs/evidence/RUN-20260604_dashboard-design-review.md`.
  Findings intake:
  `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md`.
