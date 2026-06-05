---
schema_version: hwi.ready-set-go-preflight/v0
stage: ready-set
status: active
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-05
updated_at: 2026-06-05
current_authority: false
superseded_by_for_operational_claims: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-automated-trading-program_hwistock.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260605_continuous-adapter-runner_hwistock.md
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260605_continuous-adapter-runner_hwistock.md
unit_ref: docs/units/HWISTOCK-UNIT-010_kis-adapter-continuous-runner.md
module_ref: docs/modules/HWISTOCK-MOD-008_continuous-adapter-runtime.md
qa_ref: docs/qa/QA-HWISTOCK-UNIT-010_kis-adapter-continuous-runner.md
---

# Ready-Set Go Preflight Checklist — Continuous KIS Broker-Adapter Runner

## 1. Purpose

This checklist is the last local gate before implementing
`HWISTOCK-UNIT-010`. It is a preflight contract only. It does not run KIS, read
secrets, place orders, or enable services by itself.

## 2. Hard Blockers

| check_id | required_state | expected_result |
| --- | --- | --- |
| PF-01 | Current completion report exists | `docs/set/READY-SET-COMPLETION-20260605_continuous-adapter-runner_hwistock.md` exists |
| PF-02 | Selected unit appears in row closure | `HWISTOCK-UNIT-010` is `ready_for_go_check` |
| PF-03 | Unit/module/QA docs exist | UNIT-010, MOD-008, and QA-010 exist |
| PF-04 | Runner duration policy is correct | No Go plan may hardcode seven days/one week/fixed duration as service stop/pass/fail logic |
| PF-05 | Observation window is operator-controlled | Go plan includes start/end/duration metadata controlled outside the core runner loop |
| PF-06 | Secret boundary is preserved | KIS broker-adapter env path may be referenced, but values must not be read for docs, printed, committed, or sent externally |
| PF-07 | Adapter/unapproved endpoint boundary is explicit | Unknown/operation/partner hosts fail closed before network calls |
| PF-08 | KIS capability boundary is explicit | KRX adapter-supported calls only; NXT/SOR/integrated/helper branches disabled or fallback |
| PF-09 | Risk overlay is explicit | Broker orders use hwiStock policy overlay, including cash-only, 2,000,000 KRW baseline, max holdings 5, and reserve ratio 0.25 |
| PF-10 | Fake broker simulation remains forbidden | No fake fills, fake balances, fake positions, fake broker PnL, or fake success records |
| PF-11 | Dashboard remains read-only/local-only | No buy/sell/service-control UI and no public/LAN exposure |
| PF-12 | KIS broker-adapter smoke timing is safe | If market/session blocks an order row, evidence must record the blocked condition rather than fake a pass |

## 3. Allowed Go Side Effects After Preflight PASS

Within `HWISTOCK-UNIT-010` only:

- bounded KIS broker-adapter KRX network calls;
- bounded KIS broker-adapter KRX broker orders and cancels;
- token/approval-key lifecycle in adapter mode;
- read-only adapter balance/buyable/quote/order/fill evidence;
- local systemd/user-service file creation;
- local evidence, logs, ledgers, and reports.

## 4. Forbidden Side Effects

- operation KIS endpoint or account-affecting order;
- raw secret/account/token printing;
- NXT/SOR broker order routing through KIS adapter;
- fake broker simulation;
- public/LAN dashboard exposure;
- AI provider calls;
- fixed-duration runner behavior.

## 5. Required Go Evidence

- preflight PASS/FAIL table;
- changed files;
- focused tests;
- rule/manual safety gate result;
- sanitized KIS broker-adapter smoke or blocked-with-reason evidence;
- service lifecycle smoke;
- observation-window manifest sample;
- secret redaction check;
- final Check review before any Prove claim.
