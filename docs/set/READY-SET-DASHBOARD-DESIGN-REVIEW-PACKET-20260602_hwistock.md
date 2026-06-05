---
schema_version: hwi.ready-set-design-review-packet/v0
stage: ready-set
status: prepared_not_sent
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
unit_id: HWISTOCK-UNIT-007
module_id: HWISTOCK-MOD-006
created_at: 2026-06-02
updated_at: 2026-06-03
external_route: agy_gemini_pro
---

# Dashboard Design Review Packet

## 1. Purpose

This packet prepares the `agy` Gemini Pro design review requested for the
dashboard/operator console. It is not a UI implementation request. It defines
the visual/product constraints that a reviewer should challenge before dashboard
Go.

Use the active profile, module, unit, and QA documents as the design source of
truth:

- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md`
- `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md`
- `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md`
- `docs/evidence/RUN-20260603_ready-set-current-state-snapshot.md`

If an older evidence note preserves a superseded brainstorming assumption,
prefer the active profile/module/unit/QA contracts and current-state snapshot.
This review may propose layout and component improvements only; it must not
authorize dashboard implementation, public/LAN exposure, order controls, broker
network calls, AI provider calls, or service-control actions.

## 2. Product Boundary

The dashboard is read-only:

- no buy/sell buttons
- no order placement controls
- no broker adapter toggles
- no strategy/risk parameter editing
- no prompt/model editing
- no service start/stop controls
- no operation-trading approval controls

The operator may inspect state and talk with the investment AI, but any action
that could change trading behavior remains outside this dashboard unit.

## 3. First Screen Requirements

The first screen should be the actual operator console, not a landing page.
Expected state sections:

- system mode: dry-run, KIS adapter, or future read-only broker-adapter
- market session: KRX/NXT/out-of-session, calendar status, stale-data status
- cash and reserve state: current capital, minimum reserve floor, available
  order cash
- positions/holdings summary
- candidate/watchlist table with source reasons
- AI analysis status: hourly analysis, morning review, daily close report
- risk/order-intent timeline
- local alerts and errors
- AI conversation panel for state review and explanation

## 4. Visual Direction

- Quiet operational dashboard, dense but readable.
- Designed for scanning and repeated monitoring.
- Avoid marketing hero layouts, decorative cards, and large explanation blocks.
- Use tables, compact panels, status badges, log timelines, filters, and
  operator-friendly detail drawers.
- Keep sensitive values masked or absent.
- Use color for state severity, not decoration.

## 5. Reviewer Questions

1. Does the first screen expose the most important operator state without
   encouraging manual trading?
2. Are read-only boundaries obvious in the UI model?
3. Is the layout suitable for a 24-hour home-server monitor?
4. Are alerts, stale data, calendar idle, kill switch, and adapter-mode state
   visible enough?
5. Does the AI conversation panel look like analysis/explanation, not command
   execution?
6. Does the proposed layout preserve local-only, masked, read-only operation
   without implying public access or operator-side trade controls?
7. Are any suggestions in tension with the active profile/module/unit/QA
   contracts or the current Ready-Set state snapshot?
8. What component hierarchy should be used for the first implementation?
9. What should be considered P0/P1/P2 design feedback before dashboard Go?

## 6. Expected Output Format

- Design verdict: `ready`, `not_ready`, or `ready_with_changes`
- P0/P1/P2 findings
- Recommended layout sections
- Component list
- Mobile/desktop risks
- Redaction and read-only risks

Record the received design review through
`docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-TEMPLATE-20260603_hwistock.md`
before changing dashboard row closure or completion status.
