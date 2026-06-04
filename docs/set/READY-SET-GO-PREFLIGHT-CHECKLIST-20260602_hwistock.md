---
schema_version: hwi.ready-set-go-preflight/v0
stage: ready-set
status: ready_for_full_queue_skeleton_sandbox_safe_go_preflight
implementation_ready: true
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-02
updated_at: 2026-06-04
completion_report_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
owner_decision_brief_ref: docs/set/READY-SET-OWNER-DECISION-BRIEF-20260602_hwistock.md
approval_actions_ref: docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md
owner_decision_receipt_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
owner_decision_receipt_template_ref: docs/set/READY-SET-OWNER-DECISION-RECEIPT-TEMPLATE-20260603_hwistock.md
external_review_presend_evidence_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_full.md
external_review_evidence_ref: docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md
dashboard_design_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md
git_init_delta_sync_ref: docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md
kis_paper_smoke_evidence_ref: docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md
selected_queue_scope: full_queue_skeleton_sandbox_safe
---

# Ready-Set Go Preflight Checklist

## 1. Purpose

This checklist defines the last local gate before any Go implementation work.
It is a preflight contract only; it does not authorize file edits by itself.

The current selected queue scope is `full_queue_skeleton_sandbox_safe`.

## 2. Hard Blockers

Go must stop before file edits if any row below fails.

| check_id | required_state | current_expected_result |
| --- | --- | --- |
| PF-01 | `docs/set/READY-SET-COMPLETION-20260602_hwistock.md` exists | pass |
| PF-02 | completion report has `implementation_ready: true` for the selected scope | pass for `full_queue_skeleton_sandbox_safe` |
| PF-03 | selected unit appears in `go_check_queue` | inspect at Go time; all nine units are listed |
| PF-04 | selected row state is exactly `ready_for_go_check` | pass for all nine rows, subject to row scope |
| PF-05 | selected unit, module, QA scenario, and profile refs all exist | inspect at Go time |
| PF-06 | current final external review is complete, or an explicit local-only narrowed approval phrase is recorded | pass: current final GPT Pro external review complete for full queue |
| PF-07 | no open P0/P1 external review findings remain | pass: full findings intake records no open P0/P1 after fixes/accepted preflight constraints |
| PF-08 | strategy row is approved or excluded if selected or if it affects selected implementation scope | pass for Set: first-pass strategy defaults approved for paper/sandbox planning only; fail for broker-backed strategy/order behavior |
| PF-09 | dashboard design review is complete or dashboard row is excluded if dashboard implementation is selected | pass for Set: dashboard design review complete and findings applied; fail for public/LAN exposure, buy/sell controls, or service-control behavior |
| PF-10 | broker network, AI network, paper order, live order, and credential-storage approvals are explicit for the selected action | pass for no-network/no-order/no-credential Go actions and for the already completed bounded KIS paper/mock smoke; fail for any new unscoped broker, AI provider, paper, live, credential, public-dashboard, fake-broker, or expected-profit action |
| PF-11 | owner decision receipt fields from `docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md` are recorded for any approval-driven closure | pass for 2026-06-04 full expansion closure |
| PF-12 | if a narrowed foundation-only Action 4 closure is selected, conditional `HWISTOCK-UNIT-006` include/exclude scope is recorded | not_applicable for current full queue; `UNIT-006` is included only as no-order dry-run skeleton |
| PF-13 | before code edits, VCS baseline is resolved by Git initialization or an explicit no-VCS exception evidence note | pass: Git initialized on `main`; evidence `docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md` |

## 3. Secret And Data Safety

Before any external review, implementation worker prompt, generated report, or
Go evidence is sent outside the local workspace, verify:

- No `env.sh` content is included.
- No `/home/hwi/.config/hwistock/*.env` content is included.
- No `.env` or secret shell files are included.
- No `apiRefer/*.xlsx` files are sent unless separately approved.
- No broker app key, app secret, access token, approval key, account id, product
  code, AI API key, real balance, or runtime fill data is included.
- The candidate-scoped fail-closed secret-pattern scan over the intended share
  set returns `no_matches`.

For the 2026-06-04 full external review, the current evidence is
`docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md` and
`docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md`.

## 4. Unit-Level Preflight

For the selected unit, record:

- selected unit id;
- queue order;
- owner decision receipt ref, if the row was closed by owner approval or
  exclusion;
- module ref;
- unit ref;
- QA scenario ref;
- allowed change area;
- forbidden change area;
- required smoke rows;
- expected evidence output path under `docs/evidence/`;
- whether code edits require `delegation-guard`;
- whether worker delegation is used;
- focused Go smoke rows mapped from the selected unit's QA scenario;
- VCS decision: initialized Git ref or explicit no-VCS exception ref.

## 5. Network And Trading Preflight

Default state for first Go implementation remains local-only and no-order
unless explicitly changed by a future owner approval. The completed
`docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md` smoke is a bounded
exception and does not authorize unscoped implementation behavior:

- Broker network calls outside explicitly scoped approved KIS paper/mock units:
  denied.
- Additional KIS token/account/balance/quote/realtime/WebSocket calls outside
  explicitly scoped approved KIS paper/mock units: denied.
- Additional KIS order/modify/cancel calls outside explicitly scoped approved
  KIS paper/mock units: denied.
- Paper order placement outside explicitly scoped approved KIS paper/mock units:
  denied.
- Live order placement: denied.
- AI provider network calls: denied.
- Credential storage: denied.
- Public dashboard/LAN exposure: denied.
- Dashboard service-control actions and buy/sell controls: denied.
- Internal fake broker fills, fake balances, and fake PnL: denied.

If any selected unit needs one of these, stop and require explicit owner
approval plus matching profile/module/unit updates before proceeding.

## 6. Selected-Queue Network Boundary Smoke

For every included row, Go smoke must prove that the selected action does not
cross denied network or trading boundaries.

Required checks:

- Broker/KIS runtime flags remain disabled for unscoped Go rows; local secret
  files may exist but must not be loaded or used unless the selected unit
  explicitly scopes KIS paper/mock behavior.
- No new KIS token issuance path is invoked unless the selected unit explicitly
  scopes it.
- No new KIS account, balance, quote, realtime, order, modify/cancel, HTS-ID,
  or WebSocket approval-key path is invoked unless the selected unit explicitly
  scopes it.
- No paper or live order path is invoked.
- No AI provider network path is invoked.
- No internal fake broker fill, fake balance, or fake PnL object is produced.
- Public/LAN dashboard exposure stays disabled.
- For `HWISTOCK-UNIT-003`, live OpenDART fetch remains disabled unless a later
  source API config approval explicitly enables `DART_API_KEY`, rate cap, and
  storage policy. First Go uses fixture/config skeleton evidence.
- For `HWISTOCK-UNIT-004`, strategy defaults remain paper/sandbox planning
  inputs only and cannot trigger orders.
- For `HWISTOCK-UNIT-005`, `AI_NETWORK_ENABLED=false` remains the default and no
  provider call is made.
- For `HWISTOCK-UNIT-006`, the state path stops at no-order dry-run records and
  cannot transition into submitted/accepted/fill states.
- For `HWISTOCK-UNIT-007`, UI and API surfaces remain read-only and cannot
  expose buy/sell, service-control, public/LAN, raw credential, or raw error
  behavior.

## 7. Go Report Minimum Evidence

Every Go report must include:

- selected completion report and row closure refs;
- preflight PASS/FAIL table;
- changed files;
- direct-edit or worker route;
- rule-gate/manual checklist result;
- focused smoke result;
- docs/evidence output refs;
- unresolved issues;
- handoff state for Check.

## 8. Current Status

This checklist can now be applied to all nine included rows under
`full_queue_skeleton_sandbox_safe`.

It still blocks any selected row if:

- the selected implementation tries to use unscoped broker/KIS, AI provider,
  paper-order, live-order, credential-storage, dashboard-public/LAN,
  service-control, buy/sell, fake-broker, fake-balance, fake-PnL, or
  expected-profit behavior;
- the selected unit's focused smoke rows cannot prove denied paths remain
  disabled.
