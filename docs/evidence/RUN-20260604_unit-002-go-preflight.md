---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-002-go-preflight
stage: go
unit_id: HWISTOCK-UNIT-002
status: pass
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-002_home-server-adapter-runner.md
module_refs:
  - docs/modules/HWISTOCK-MOD-001_trading-safety-core.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-002_home-server-adapter-runner.md
ready_set_completion_ref: docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md
unit_001_go_check_ref: docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md
created_at: 2026-06-04
---

# UNIT-002 Go Preflight Evidence — 2026-06-04

## 1. Verdict

PASS. `HWISTOCK-UNIT-002` may enter Go as a bounded local runner/systemd
skeleton row.

This verdict does not authorize broker/KIS network calls, AI provider calls,
broker orders, account-affecting orders, credential storage, public/LAN exposure, systemd
deployment/execution, or a one-week adapter evidence claim.

## 2. Delegation Guard

- Stage: go-check / UNIT-002.
- Gate size: FULL_GATE.
- Route class: implementation_worker.
- Selected route/model: `cursor-sdk-local` through `hwi-cursor-worker run` with
  `composer-2.5`.
- Workspace: `/data/workspace/My/hwiStock` with `WORKSPACE_MODE:
  direct_project_cwd`.
- Permission: bounded write for backend runner/status/no-order skeleton,
  `ops/systemd/` templates, focused backend tests, and this row's evidence/docs.
- Reason: UNIT-002 touches backend/ops product code and local runtime safety
  boundaries. Direct local implementation is not the default path.
- Re-gate triggers: any KIS/broker/API/AI network call, credential handling,
  public/LAN exposure, service-managed execution/deploy, DB migration, adapter-mode
  order behavior, fake fills/balances/PnL, or scope outside UNIT-002.

## 3. Selected Row Scope

Allowed first Go scope from the current row closure matrix:

- systemd file templates
- local runner lifecycle skeleton
- health/status payloads
- calendar idle/routing behavior
- local alert plumbing
- no-order mode wiring
- local-only `127.0.0.1` bind enforcement

Hard exclusions:

- broker orders
- broker/KIS calls
- AI calls
- operation runner claim
- one-week adapter evidence claim
- public/LAN exposure
- credential reads or storage

## 4. Preflight Checklist

| check_id | result | evidence |
| --- | --- | --- |
| PF-01 | pass | Current completion report exists at `docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md`. |
| PF-02 | pass | Completion report is `implementation_ready: true` only for `skeleton_sandbox_safe_rebaseline_queue`. |
| PF-03 | pass | `HWISTOCK-UNIT-002` is listed in the current Go-Check queue. |
| PF-04 | pass | `HWISTOCK-UNIT-002` row state is `ready_for_go_check`. |
| PF-05 | pass | Unit, module, QA scenario, profile, and source policy docs exist. |
| PF-06 | conditional_pass | No post-import external review was run; selected scope is local skeleton/adapter-safe only and does not expand broker/AI/credential/public dashboard behavior. |
| PF-07 | pass | No open P0/P1 finding is known for this bounded skeleton row. |
| PF-08 | pass | Strategy behavior is not implemented in this row. |
| PF-09 | not_applicable | Dashboard UI is not implemented in this row. |
| PF-10 | pass | Selected action is no-network, no-order, no-credential-storage. |
| PF-11 | pass | Owner rebaseline decision is recorded in the current Ready-Set owner decision doc. |
| PF-12 | not_applicable | Current full rebaseline queue includes all rows; no foundation-only exclusion applies. |
| PF-13 | pass | Git baseline exists and `.env`/local config files remain ignored. |
| PF-14 | pass_for_selected_scope | UNIT-002 must enforce local-only bind and must not treat imported MyWebTemplate `0.0.0.0` behavior or template config assumptions as hwiStock behavior. |

## 5. Required Go Smoke

Focused smoke for this row must cover at minimum:

- runner/service status payload reports adapter/no-order/local-only defaults;
- kill switch blocks order routing;
- 08:30 -> NXT, 09:30 -> KRX, 15:30 -> NXT, 20:30 -> idle;
- missing/stale calendar keeps trading/order loops idle;
- no-order intent records do not create broker calls, fake fills, fake balances,
  or fake PnL;
- local alert output is file/journal/dashboard-future only, with no external
  delivery;
- backend runtime launch defaults to `127.0.0.1`, not `0.0.0.0`.
