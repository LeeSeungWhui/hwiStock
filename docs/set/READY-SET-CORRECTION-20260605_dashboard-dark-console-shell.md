---
schema_version: hwi.set-correction/v0
id: READY-SET-CORRECTION-20260605-dashboard-dark-console-shell
type: set_correction
status: set
unit_refs:
  - HWISTOCK-UNIT-007
module_refs:
  - HWISTOCK-MOD-006
profile_refs:
  - PROFILE-HWISTOCK
owner: hwi
created_at: 2026-06-05
source: agy_gemini_3_1_pro_high_dashboard_screenshot_review
---

# Dashboard Dark Console Shell Correction

## 1. Trigger

After the deployed dashboard screenshot review, the operator rejected a local
visual judgment and requested a Gemini Pro design review. The follow-up
`agy-designer` run used Gemini 3.1 Pro (High) against the authenticated
dashboard screenshot and classified the current visual state as:

- practicality: `NEEDS_CHANGES`
- aesthetic: `NOT_PRETTY_ENOUGH`
- redesign direction: `broad visual rework`

The review found that the inner Lucid Command dashboard already uses a dark
operator cockpit direction, but the global dashboard shell, header, sidebar, and
footer still look like a bright template shell. This creates a visible product
quality mismatch.

## 2. Corrective Set Scope

This correction does not add trading capability. It is a UI/design follow-up for
`HWISTOCK-UNIT-007`.

Included:

- make the dashboard route family visually consistent with the existing Lucid
  Command dark operator cockpit;
- align dashboard header/sidebar/footer treatment with slate/cyan high-trust
  console styling;
- strengthen the not-ready/readiness banner severity treatment;
- reduce dashboard card/list/table padding for denser operator scanning;
- flatten dashboard-local badges/status chips so they do not look like toy
  buttons or trade-action controls.

Excluded:

- broker/API behavior changes;
- backend runtime changes;
- direct buy/sell/order controls;
- public/LAN exposure changes;
- secrets or credential display;
- mobile redesign beyond preserving existing responsive behavior.

## 3. Acceptance Criteria Delta

The existing UNIT-007 AC/QA remains active. This correction tightens AC-08,
AC-10, and AC-11:

- `AC-08`: read-only controls must also visually avoid bright trade-action
  affordances and template-like primary SaaS styling.
- `AC-10`: the desktop first screen must read as one coherent dark operational
  console, not a dark widget inside a light admin shell.
- `AC-11`: AI conversation and report panes must stay explanatory/read-only
  while matching the dark console visual system.

## 4. Required Go-Check Evidence

The Go-Check for this correction must include:

- focused dashboard unit test;
- focused dashboard ESLint;
- changed-file HWI rule-gate;
- production frontend build;
- authenticated dashboard screenshot after rebuild/redeploy or local browser
  proof;
- local review that no direct order controls or service-control affordances were
  introduced.

