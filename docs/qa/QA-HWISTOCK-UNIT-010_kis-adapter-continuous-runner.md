---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-010
type: qa_scenario
name: KIS broker-adapter continuous runner QA
unit_refs:
  - HWISTOCK-UNIT-010
module_refs:
  - HWISTOCK-MOD-008
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-007
profile_refs:
  - PROFILE-HWISTOCK
status: set
implementation_status: go_check_passed_local_no_network
owner: hwi
updated_at: 2026-06-05
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-continuous-adapter-runner.md
  - docs/evidence/RUN-20260605_unit-010-go-check.md
---

# KIS Adapter Continuous Runner QA

## 1. Purpose

Prove that hwiStock can run as a continuous 24-hour home-server program using
KIS broker-adapter APIs only within the approved KRX adapter boundary. The QA scenario
must also prove that the test period is not hardcoded: the operator controls the
observation window.

## 2. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | code/config | Inspect runner loop and config | No hardcoded seven-day, one-week, fixed-duration stop/pass/fail condition exists | code/test output |
| QA-002 | P0 | manifest | Start and end an observation window through config/CLI/test fixture | Manifest records operator-selected start/end/duration; service loop remains duration-agnostic | manifest |
| QA-003 | P0 | secret | Load KIS adapter config through test/masked runtime path | Secret values are never printed; docs/logs contain path/env names only | redaction scan |
| QA-004 | P0 | adapter | Attempt unapproved/unknown broker host configuration | Adapter fail-closes before network call | adapter test |
| QA-005 | P0 | adapter-smoke | Run bounded KIS KRX adapter smoke in approved environment | Supported adapter paths work or return classified adapter errors; no operation path is touched | sanitized smoke |
| QA-006 | P0 | capability | Request NXT/SOR/integrated/helper adapter capabilities | Branches are disabled or local-fallback and no unsupported broker endpoint is called | capability log |
| QA-007 | P0 | risk | Submit candidate intents across reserve, holdings, stop, stale data, calendar, and kill-switch cases | Unsafe intents are blocked before KIS call; allowed intents preserve the risk overlay | policy log |
| QA-008 | P0 | ledger | Simulate missing/rejected broker responses and unsupported helper cases | No fake fill, fake balance, fake position, or fake PnL is created | ledger test |
| QA-009 | P0 | reconciliation | Reconcile order/fill/balance/buyable snapshots | Ledger records system-calculated cash, exposure, position, and PnL fields with masked identifiers | reconciliation report |
| QA-010 | P0 | lifecycle | Restart service/timer around pending and completed adapter-visible states | Runner is idempotent and does not duplicate orders or lose reconciliation state | service smoke |
| QA-011 | P0 | calendar | Run closed/stale/off-envelope scheduler cases | Trading/order loops stay idle while service health remains visible | health/log |
| QA-012 | P0 | dashboard/API | Inspect read-only status surfaces | No buy/sell controls, operation toggles, raw credentials, raw account ids, or service-control buttons appear | API/UI review |
| QA-013 | P0 | network-boundary | Record outbound endpoint classes during focused smoke | Only approved KIS broker-adapter KRX endpoints appear; no operation/AI/public-dashboard exposure occurs | network/evidence log |
| QA-014 | P0 | evidence | Generate daily and final observation reports | Reports list covered days, runtime, P0 status, alerts, fixes, unresolved blockers, and operator window metadata; no profit target claim | evidence report |

## 3. PASS / FAIL / BLOCKED Rules

- PASS: all selected P0 rows pass, the service can run continuously, KIS use is
  KRX-adapter-bound, the observation window is operator-controlled, and no denied
  operation/fake/public/secret behavior is reachable.
- FAIL: fixed-duration runner logic exists, unapproved endpoints are reachable, secrets
  leak, unsupported KIS adapter branches call broker endpoints, fake broker state
  is created, or the dashboard exposes order controls.
- BLOCKED: KIS broker-adapter env is unavailable, market is closed for order-specific
  rows, systemd/user-service cannot be inspected, or current KIS adapter limits
  prevent safe bounded smoke. Blocked rows must be recorded with concrete dates,
  times, and endpoint class without leaking secrets.

## 4. Evidence Requirements

- focused unit/integration test output
- secret redaction scan
- sanitized KIS broker-adapter smoke summary
- capability matrix check output
- risk-gate and kill-switch logs
- adapter ledger/reconciliation report
- service lifecycle smoke
- calendar/off-envelope idle smoke
- read-only dashboard/API review
- operator observation-window manifest and daily report samples
