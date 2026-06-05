---
schema_version: hwi.evidence/v0
id: RUN-20260604-dashboard-design-review
stage: ready-set
status: ready_with_changes
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
environment: agy_gemini_pro
review_type: dashboard_design
reviewer_route: agy
reviewer_model: Gemini 3.1 Pro (High)
dashboard_design_review_packet_ref: docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md
review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md
owner_decision_receipt_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
---

# Dashboard Design Review Evidence

## 1. Scope

This evidence records the approved dashboard design review for
`HWISTOCK-UNIT-007`. The review was executed through `agy` with
`Gemini 3.1 Pro (High)` using the prepared dashboard design review packet and
read-only docs scope.

The review did not authorize dashboard implementation, public/LAN exposure,
broker calls, KIS calls, AI provider calls, broker orders, account-affecting orders, credential
storage, or Go implementation.

## 2. Route Notes

The first `agy` attempt used `Gemini 3.5 Flash (High)` and stopped with
`MODEL_MISMATCH` per the `agy-designer` contract. The review was then rerun with
`--model 'Gemini 3.1 Pro (High)'` and completed.

## 3. Reviewer Verdict

Reviewer verdict: `ready_with_changes`.

Local interpretation: dashboard row can move toward full Ready-Set closure only
after the P0/P1 design findings are reflected in the module, unit, and QA
contracts. This evidence itself does not make Go eligible.

## 4. Normalized Findings

| finding_id | severity | affected_area | summary | local action |
| --- | --- | --- | --- | --- |
| AGY-DASH-001 | P0 | design system / UI affordance | Dashboard controls could look like actionable trade execution controls even when no buy/sell buttons exist. | Add read-only styling rule: no primary action button variants for dashboard interaction; reserve bright colors for severity/state. |
| AGY-DASH-002 | P0 | data display / redaction | Raw account identifiers or raw balances could leak through display components or frontend error dumps. | Add required `MaskedValue` primitive and sanitized error rendering rule. |
| AGY-DASH-003 | P1 | first-screen layout | Nine first-screen sections create information-density risk. | Add desktop-first 3-pane grid layout requirement with persistent status header and truncation/overflow controls. |
| AGY-DASH-004 | P2 | AI conversation panel | AI chat can visually imply command execution if it resembles a terminal/CLI. | Render the AI conversation as a reporting/mail-style explanation thread rather than a command shell. |

## 5. Recommended Layout

Recommended first implementation layout:

- Persistent global status header:
  - system mode
  - market session
  - data/source health
  - kill-switch visibility
- Left summary pane:
  - masked cash/reserve/PnL
  - open-position count
  - AI job/report status
- Center data pane:
  - holdings table
  - candidate/watchlist grid
  - market intelligence timeline
- Right review pane:
  - AI conversation/report thread
  - audit/error log timeline

Initial dashboard implementation should target desktop monitoring first
(`min-width` style desktop viewport). Mobile responsiveness is deferred unless a
future unit explicitly adds it.

## 6. Safety Boundary

This review did not perform implementation, browser QA, server operation,
deployment, git/svn mutation, credential access, broker/KIS access, AI provider
access, broker orders, or account-affecting orders.

