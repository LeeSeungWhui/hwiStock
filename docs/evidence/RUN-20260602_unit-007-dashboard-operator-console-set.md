---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-007-dashboard-operator-console-set
type: evidence
name: Dashboard operator console Set pass
stage: set
environment: docs_only
status: pass_with_followups
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-03
implementation_ready: false
---

# Dashboard Operator Console Set Pass

## 1. Scope

This docs-only Set pass closes the first dashboard/operator console scope,
access policy, first-screen sections, and AI conversation boundary.

## 2. Decisions

- Dashboard remains read-only for orders.
- Direct buy/sell controls, broker adapter toggles, risk-parameter changes,
  prompt/model changes, and live-readiness controls are excluded.
- Default access is local-only `127.0.0.1`.
- Remote access uses SSH tunnel or Chrome Remote Desktop by default.
- Public/LAN IP exposure requires a later explicit Set contract with
  authentication and allowlist/VPN/reverse-proxy controls.
- "Unknown URL/IP" secrecy is not accepted as access control.
- No prepared design source exists. Use no-design fallback grounded in module
  and unit contracts, then run `agy` Gemini Pro design review before dashboard Go.
- First screen is the actual operator console, not a landing page.
- Required first-screen sections: status strip, account summary, candidates,
  holdings/positions, order-state timeline, market-intelligence timeline,
  AI jobs/reports, audit/errors, and AI conversation.
- AI conversation can read stored reports and sanitized current state through
  backend APIs only. It cannot place orders, reveal credentials, change risk
  settings, enable adapters, or alter service lifecycle state.

## 3. Evidence

- `docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md` is marked `set`
  and records the dashboard capability contract.
- `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md` is marked `set`
  and records acceptance criteria.
- `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md` is marked `set`
  and adds QA rows for local-only access, read-only AI conversation, and
  operator-console first screen.
- `docs/profiles/PROFILE-HWISTOCK.md`, `AGENTS.md`, `docs/index.md`, and
  `docs/evidence/RUN-20260602_ready-set-architecture.md` were updated to reflect
  dashboard access/design decisions.
- `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md` now
  names the active profile/module/unit/QA docs and current-state snapshot as the
  design source of truth, and tells reviewers not to treat older superseded
  evidence assumptions as implementation authority.

## 4. Boundaries

- No frontend/backend source code, browser session, `agy` run, network call, or
  deployment was created or run.
- Dashboard implementation still needs backend API/data shape from earlier
  units and an `agy` design review before Go.
- The design review packet does not authorize implementation, public/LAN
  exposure, order controls, broker network calls, AI provider calls, or
  service-control actions.

## 5. Verdict

UNIT-007 Set: PASS WITH FOLLOW-UPS.

Implementation readiness: BLOCKED until Ready-Set completion gate and remaining
bundle items are closed.
