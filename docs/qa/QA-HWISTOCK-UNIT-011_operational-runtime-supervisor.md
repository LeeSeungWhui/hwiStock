---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-011
type: qa_scenario
name: Operational runtime supervisor QA
unit_refs:
  - HWISTOCK-UNIT-011
module_refs:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-008
  - HWISTOCK-MOD-007
profile_refs:
  - PROFILE-HWISTOCK
status: set
owner: hwi
updated_at: 2026-06-05
---

# Operational Runtime Supervisor QA

## 1. Purpose

Prove that hwiStock can be installed and supervised as a local-only service
bundle, not a manual Codex shell run.

## 2. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | unit-file | Inspect every `ops/systemd/user/hwistock-*` file | No env values, live endpoints, public bind, or shell-only assumptions | unit-file audit |
| QA-002 | P0 | install | Sync selected unit files into user systemd and run daemon reload | Units are visible to `systemctl --user` | status output |
| QA-003 | P0 | local-only | Start API/frontend non-order services | Ports 5000/5001 bind only to 127.0.0.1 | port/status smoke |
| QA-004 | P0 | timers | Enable/start non-order timers first | Intel, AI, runner-tick, and health timers are listed with next/last times | timer list |
| QA-005 | P0 | broker-boundary | Verify KIS paper runner is not accidentally started by UNIT-011 | No paper order call occurs in supervisor-only scope | systemd + evidence |
| QA-006 | P0 | restart | Restart non-order services/timers | Services recover without duplicate intents/orders | restart smoke |
| QA-007 | P0 | health | Query read-only runtime status | Calendar/kill/source/order blocks are visible and classified | API/evidence |

## 3. PASS / FAIL / BLOCKED Rules

- PASS: selected services/timers are installable, local-only, restartable, and
  produce evidence without starting broker-order side effects.
- FAIL: public bind, secret leak, unmanaged manual shell dependency, or
  accidental broker order path.
- BLOCKED: user systemd unavailable, required toolchain missing, or side-effect
  approval not available for the selected row.
