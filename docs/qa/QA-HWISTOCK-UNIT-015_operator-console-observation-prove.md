---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-015
type: qa_scenario
name: Operator console and observation Prove QA
unit_refs:
  - HWISTOCK-UNIT-015
module_refs:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-006
  - HWISTOCK-MOD-007
  - HWISTOCK-MOD-008
profile_refs:
  - PROFILE-HWISTOCK
status: go_check_local_passed_browser_prove_blocked
owner: hwi
updated_at: 2026-06-05
evidence_refs:
  - docs/evidence/RUN-20260605_operational-go-check-units-012-015.md
---

# Operator Console And Observation Prove QA

## 1. Purpose

Prove that the owner can observe the paper program as a real 24-hour runtime
without gaining unsafe dashboard order controls.

## 2. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | API | Query runner/status endpoints | Service/timer health, blocks, latest evidence paths, and readiness flags are visible | API output |
| QA-002 | P0 | dashboard | Open dashboard through loopback/tunnel | hwiStock runtime cards render without API 500 | browser evidence |
| QA-003 | P0 | read-only | Inspect visible controls | No buy/sell, live toggle, public bind, or direct service-control button appears | screenshot/review |
| QA-004 | P0 | masking | Inspect account/provider-like values | Account ids, tokens, raw responses, and secrets are absent or masked | browser/API review |
| QA-005 | P0 | reports | Generate daily/final observation reports | Reports use operator-selected window metadata and no fixed-duration auto-pass | report artifact |
| QA-006 | P0 | readiness | Compare readiness flags | Running service, paper network, paper orders, observation accepted, and live readiness are separate flags | API/evidence |

## 3. PASS / FAIL / BLOCKED Rules

- PASS: dashboard/API prove actual runtime status, remain read-only/local-only,
  and generate operator-window evidence.
- FAIL: order controls exposed, public bind, secret leak, API 500, or
  false `operational_trading_readiness` claim.
- BLOCKED: browser/tunnel route unavailable or backend/frontend services not
  started by previous units.
