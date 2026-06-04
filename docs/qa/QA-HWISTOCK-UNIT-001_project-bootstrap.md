---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-001
type: qa_scenario
name: Project bootstrap QA
unit_refs:
  - HWISTOCK-UNIT-001
module_refs:
  - HWISTOCK-MOD-001
profile_refs:
  - PROFILE-HWISTOCK
status: set
owner: hwi
updated_at: 2026-06-02
evidence_refs:
  - docs/evidence/RUN-20260602_unit-001-project-bootstrap-set.md
---

# Project Bootstrap QA

## 1. Purpose

Verify that the empty `hwiStock` project root has enough Hwi Work Harness
structure to begin planning without accidentally implying live-trading readiness.

## 2. Scope

In scope:

- root `AGENTS.md`
- `docs/index.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/modules/HWISTOCK-MOD-001_trading-safety-core.md`
- `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md`
- `docs/evidence/RUN-20260602_project-bootstrap.md`

Out of scope:

- code execution
- broker/API calls
- credentials
- trading strategy validation
- live or paper order execution

## 3. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | docs | Inspect `AGENTS.md` | Profile path and harness routing are present | file path |
| QA-002 | P0 | docs | Inspect profile approval policy | Broker/live order/real-money gates require explicit approval | file path |
| QA-003 | P0 | docs | Inspect module doc | Safety module states no live orders by default | file path |
| QA-004 | P1 | docs | Inspect QA scenario | Scenario references bootstrap unit/module/profile | file path |
| QA-005 | P1 | docs | Inspect index/profile/unit | Selected broker, stack, strategy/risk, paper-boundary, source registry, and remaining full Ready-Set blockers are visible | file path |
| QA-006 | P0 | docs | Inspect profile/module/unit | Live operation requires at least one full week of paper/sandbox testing evidence before go/no-go approval | file path |
| QA-007 | P0 | docs | Inspect profile/module/unit | Capital policy is cash-only and leveraged capital is forbidden by default | file path |

## 4. PASS / FAIL / BLOCKED Rules

- PASS: all required docs exist, live-trading side effects remain explicitly
  forbidden, the one-week paper/sandbox test gate is documented, and capital is
  cash-only by default.
- FAIL: docs imply real-money trading or broker side effects may happen without
  approval.
- BLOCKED: required docs cannot be read.

## 5. Evidence Requirements

- File list of created docs.
- Short content review of profile approval gates.
- No screenshots or browser evidence required for this docs-only bootstrap.
