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
status: set
owner: hwi
updated_at: 2026-06-04
---

# Dashboard Operator Console QA

## Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | UI | Inspect dashboard actions | No direct buy/sell button or order placement UI exists | screenshot/UI review |
| QA-002 | P0 | security | Inspect UI/API payloads | Credentials/account ids are masked or absent | payload review |
| QA-003 | P1 | UI | Inspect main dashboard | Holdings, PnL, candidates, AI reports, logs, and health are visible | screenshot |
| QA-004 | P1 | design | Run/record Gemini Pro design review through `agy` using `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md` when approved | Design feedback is classified and converted into implementable spec | review report |
| QA-005 | P0 | security | Inspect dashboard/API bind and access config | Default bind is `127.0.0.1`; remote access uses SSH tunnel or Chrome Remote Desktop; public/LAN exposure requires later authenticated Set approval | config/network evidence |
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
