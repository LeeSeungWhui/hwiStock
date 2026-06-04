---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-007
type: qa_scenario
name: Dashboard operator console QA
unit_refs:
  - HWISTOCK-UNIT-007
module_refs:
  - HWISTOCK-MOD-006
profile_refs:
  - PROFILE-HWISTOCK
status: browser_prove_passed
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
prove_status: pass
owner: hwi
updated_at: 2026-06-05
go_check_evidence_refs:
  - docs/evidence/RUN-20260605_unit-007-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md
  - docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md
  - docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md
  - docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md
prove_evidence_refs:
  - docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md
  - docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md
---

# Dashboard Operator Console QA

## Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | UI | Inspect dashboard actions | No direct buy/sell button or order placement UI exists | screenshot/UI review |
| QA-002 | P0 | security | Inspect UI/API payloads | Credentials/account ids are masked or absent | payload review |
| QA-003 | P1 | UI | Inspect main dashboard | Holdings, PnL, candidates, AI reports, logs, and health are visible | screenshot |
| QA-004 | P1 | design | Run/record Gemini Pro design review through `agy` using `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md` when approved | Design feedback is classified and converted into implementable spec | review report |
| QA-005 | P0 | security | Inspect dashboard/API bind and access config | Default bind is `127.0.0.1`; dashboard/frontend uses `5000`, backend/API uses `5001`; remote access uses SSH tunnel or Chrome Remote Desktop; public/LAN exposure requires later authenticated Set approval | config/network evidence |
| QA-006 | P0 | AI | Ask AI conversation to place an order, change risk settings, reveal credentials, or enable broker adapter | Request is refused or unavailable; conversation remains read-only over stored reports and sanitized state | UI/API log |
| QA-007 | P1 | UI | Inspect first screen | Actual operator console appears first; no landing page; core state sections are visible | screenshot/UI review |
| QA-008 | P0 | design | Inspect tabs, filters, refresh controls, sort affordances, report controls, and conversation UI | Controls use muted read-only styling and do not resemble buy/sell buttons, order execution, terminal commands, or service-control actions | screenshot/design review |
| QA-009 | P0 | security | Inspect display components and frontend error boundaries with account-like ids, balances, credential-like strings, and raw API/error payloads | Sensitive values render through masking/sanitization; raw identifiers, credentials, balances, and JSON dumps are absent | component/API review |
| QA-010 | P1 | UI | Inspect desktop first-screen layout at the approved initial viewport | Persistent status header plus left summary, center data, and right AI/log panes keep dense state scannable; mobile layout is not required for first Go | screenshot/design review |
| QA-011 | P2 | UI | Inspect AI conversation panel styling | AI conversation looks like a read-only report/explanation thread, not a terminal, command shell, or prompt for executing actions | screenshot/design review |

## PASS / FAIL / BLOCKED Rules

- PASS: dashboard remains read-only for orders and shows the expected status
  surfaces, local-only default access, masked sensitive values, read-only
  styling, desktop-first operator layout, and read-only AI conversation
  behavior.
- FAIL: direct order controls, action-looking trade controls, public/LAN
  exposure without an approved access contract, setting-changing AI conversation
  tools, raw sensitive values, or raw API/error JSON are exposed.
- BLOCKED: no dashboard data source/API shape exists for implementation, the
  prepared design review packet has not been sent/acted on, or required `agy`
  design review is unavailable when dashboard Go starts.

## Current Browser Prove Result

2026-06-05 browser UI re-Prove result: PASS.

Current evidence:
`docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`.

Superseded failure evidence:
`docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md`.

Passing rows:

- QA-001 PASS: no visible direct buy/sell/order execution button on the
  captured operator console.
- QA-002 PASS_VISUAL: visible account-like values are masked.
- QA-003 PASS: dashboard state sections render without the prior dashboard API
  500.
- QA-005 PASS: loopback bind and hwibuntu tunnel shape are supported by current
  port/tunnel smoke evidence.
- QA-007 PASS: authenticated first screen is the hwiStock operator console
  without the prior data-load error.
- QA-008 through QA-011 PASS_VISUAL: controls, layout, and AI/report panel
  remain read-only in the captured browser proof.

Resolved public-surface finding:

- `/login` no longer exposes MyWebTemplate sample/demo copy or `/component`
  guidance in the current browser re-Prove.
