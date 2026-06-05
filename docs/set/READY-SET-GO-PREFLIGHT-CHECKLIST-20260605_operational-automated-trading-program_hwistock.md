---
schema_version: hwi.go-preflight-checklist/v0
stage: ready-set
status: active
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
updated_at: 2026-06-05
current_authority: true
completion_report_ref: docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260605_operational-automated-trading-program_hwistock.md
---

# Go Preflight Checklist — Operational Automated Trading Program

Run this checklist immediately before every Go row in the operational automated
program queue.

## 1. Common Preflight

| check_id | required | check | pass condition |
| --- | --- | --- | --- |
| PF-001 | yes | Re-read current profile and AGENTS | `PROFILE-HWISTOCK` and root `AGENTS.md` are the active policy. |
| PF-002 | yes | Re-read current completion and row matrix | This operational queue is current authority for trading-program work. |
| PF-003 | yes | Protect secrets | Do not read, print, stage, or commit `/home/hwi/.config/hwistock/*.env`, `backend/config.ini`, or `frontend-web/config.ini`. |
| PF-004 | yes | Confirm dirty tree scope | Existing unrelated dirty changes are not reverted or overwritten. |
| PF-005 | yes | Confirm unapproved adapter operation denied | Unapproved endpoints, account-affecting orders, broker account login, and unapproved credentials remain forbidden. |
| PF-006 | yes | Confirm local-only bind | API/frontend/service exposure remains loopback or SSH-forwarded only. |
| PF-007 | yes | Confirm no fake broker | Missing broker responses cannot create fake fills/balances/PnL. |
| PF-008 | yes | Confirm no fixed-duration runner | No hardcoded seven-day/week stop/pass/fail logic. |
| PF-009 | yes | Confirm contract-hardening gate | UNIT-016 is closed before UNIT-012/013/014/015 order-producing work proceeds, or a stronger profile/unit update explicitly supersedes it. |
| PF-010 | yes | Confirm readiness wording | Service/timer activity, dashboard rendering, local tests, or artifact presence must not be reported as operation readiness. |
| PF-011 | yes | Confirm dashboard truth gap | If `brokerNetworkEnabled`, `brokerOrdersSubmitted`, `operationObservationAccepted`, `operationalReadiness`, fallback state, or `orderGate` is false/blocked, the operator surface must display it prominently before observation claims. |
| PF-012 | yes | Confirm runtime entrypoint split | A service-managed backend runtime must not rely on a development `reload=True` entrypoint unless the row explicitly documents a dev-only exception and an operational replacement path. |

## 2. Row-Specific Preflight

| unit_id | required preflight |
| --- | --- |
| HWISTOCK-UNIT-011 | Identify which user systemd units will be installed/started. Starting KIS broker order runner is excluded unless a later row scopes it. |
| HWISTOCK-UNIT-016 | Verify schemas, atomic publication, idempotency keys, `NO_TRADE` sentinel, executor lock/ledger, reservation accounting, order state machine, freshness TTLs, adapter-only guard, and failure-mode QA are documented before implementation Go. |
| HWISTOCK-UNIT-012 | Confirm UNIT-016 closure first, then check current official DeepSeek model ids, Pro hourly top-of-hour schedule, Flash market-minute schedule, trade-document schema, sentinel behavior, and no-order boundary before provider smoke. AI network/cost caps require explicit scope. |
| HWISTOCK-UNIT-013 | Confirm UNIT-016 closure first, then verify approved source registry, KIS broker adapter-supported intraday market-data endpoints, KRX realtime support, and schema/freshness/session/risk/reservation/conflict gates. Missing KIS/source/chart data must block intents, not invent them. |
| HWISTOCK-UNIT-014 | Confirm UNIT-016 closure first, then confirm KIS broker adapter env file existence without printing values, market/session state, adapter domain guard, idempotency storage, write-ahead log, state machine, and exact bounded order scope. |
| HWISTOCK-UNIT-015 | Confirm UNIT-016 closure first, then confirm backend/frontend services are started through approved local route and browser/tunnel QA does not expose public/LAN services. |

## 3. Allowed Network Classes By Row

| unit_id | default network allowance |
| --- | --- |
| HWISTOCK-UNIT-011 | Local loopback/service inspection only; no broker order call. |
| HWISTOCK-UNIT-016 | No broker/provider network; docs, schemas, fixture design, and local validation only. |
| HWISTOCK-UNIT-012 | No provider network by default; DeepSeek smoke only when the Go row explicitly scopes AI network operation and cost cap. |
| HWISTOCK-UNIT-013 | KIS broker-adapter market-data read network may be scoped for price/ranking/realtime collection; KIS order network is forbidden in this row. |
| HWISTOCK-UNIT-014 | KIS broker-adapter KRX broker network allowed only for bounded Go/Prove evidence; unapproved domain denied. |
| HWISTOCK-UNIT-015 | Local browser/API/tunnel QA only; no new broker/provider operations unless reading existing evidence. |

## 4. Required Output Per Go Row

Each Go row must write or update evidence with:

- gate decision;
- changed files;
- validation commands/results;
- focused smoke result;
- QA row disposition;
- service/network side effects performed;
- secret redaction status;
- unresolved blockers; and
- whether the row is ready for Check or blocked.
