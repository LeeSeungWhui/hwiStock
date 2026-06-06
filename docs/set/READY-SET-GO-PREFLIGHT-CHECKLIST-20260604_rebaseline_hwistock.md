---
schema_version: hwi.ready-set-go-preflight/v0
stage: ready-set
status: active
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-04
updated_at: 2026-06-04
current_authority: false
historical_authority: true
superseded_by:
  - docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md
  - docs/set/READY-SET-ROW-CLOSURE-20260605_operational-automated-trading-program_hwistock.md
  - docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-automated-trading-program_hwistock.md
owner_decision_ref: docs/set/READY-SET-OWNER-DECISION-20260604_rebaseline_hwistock.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
rebaseline_evidence_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
ready_set_reissue_evidence_ref: docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md
prior_go_preflight_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
approval_actions_ref: docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md
owner_decision_receipt_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
external_review_evidence_ref: docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md
external_review_evidence_status: historical_before_mywebtemplate_import_supporting_context
dashboard_design_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md
git_init_delta_sync_ref: docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md
kis_paper_smoke_evidence_ref: docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md
selected_queue_scope: full_queue_skeleton_adapter_safe
---

# Ready-Set Go Preflight Checklist — Rebaseline 2026-06-04

> **Historical authority notice**: this checklist remains useful as the
> MyWebTemplate-import preflight history record, but it is not current
> operational authority. Use the 2026-06-05 operational automated-trading
> Ready-Set, row-closure matrix, and Go preflight listed in `superseded_by` for
> current operational claims.

> **Scope notice**: This checklist was issued for the 2026-06-04 MyWebTemplate
> code import rebaseline. It replaced the superseded checklist
> `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md` for that
> historical scope.

## 1. Purpose

This checklist defines the last local gate before any Go implementation work
against the imported MyWebTemplate code baseline. It is a preflight contract
only; it does not authorize file edits by itself.

The current selected queue scope is `full_queue_skeleton_sandbox_safe`.

## 2. Hard Blockers

Go must stop before file edits if any row below fails.

| check_id | required_state | current_expected_result |
| --- | --- | --- |
| PF-01 | `docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md` exists | pass |
| PF-02 | completion report has `implementation_ready: true` for the selected skeleton/adapter-safe rebaseline scope | pass; operational trading readiness remains false |
| PF-03 | selected unit appears in `go_check_queue` of the completion report | pass for all 9 units |
| PF-04 | selected row state is exactly `ready_for_go_check` in the row closure matrix | pass for all 9 units |
| PF-05 | selected unit, module, QA scenario, and profile refs all exist | inspect at Go time |
| PF-06 | current final external review is complete, or an explicit local-only narrowed approval phrase is recorded | conditional_pass for local skeleton rebaseline only: historical GPT Pro review is supporting context, no post-import external review was run, and owner decision records MyWebTemplate quarantine/replacement. Fail if the selected Go scope materially expands broker/KIS, AI provider, credential, public dashboard, operational trading, or visually final dashboard behavior without current review/approval. |
| PF-07 | no open P0/P1 external review findings remain | pass for historical pre-import findings: full findings intake records no open P0/P1 after fixes/accepted preflight constraints. Re-run review if Go scope crosses the PF-06 material-expansion boundary. |
| PF-08 | strategy row is approved or excluded if selected or if it affects selected implementation scope | pass for Set: first-pass strategy defaults approved for adapter-backed planning only; fail for broker-backed strategy/order behavior |
| PF-09 | dashboard design review is complete or dashboard row is excluded if dashboard implementation is selected | conditional_pass for Set constraints: historical dashboard review findings are applied as requirements, but imported MyWebTemplate UI was not reviewed as a final hwiStock dashboard. Fail for public/LAN exposure, buy/sell controls, service-control behavior, retained MyWebTemplate branding/sample routes, or visually final dashboard claims without current design Check/review. |
| PF-10 | broker network, AI network, broker order, account-affecting order, and credential-storage approvals are explicit for the selected action | pass for no-network/no-order/no-credential Go actions and for the already completed bounded KIS broker-adapter smoke; fail for any new unscoped broker, AI provider, adapter, operation, credential, public-dashboard, fake-broker, or expected-profit action |
| PF-11 | owner decision receipt fields from `docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md` are recorded for any approval-driven closure | pass for 2026-06-04 full expansion closure; plus owner decision `READY-SET-OWNER-DECISION-20260604_rebaseline_hwistock.md` is recorded |
| PF-12 | if a narrowed foundation-only Action 4 closure is selected, conditional `HWISTOCK-UNIT-006` include/exclude scope is recorded | not_applicable for current full queue; `UNIT-006` is included only as no-order dry-run skeleton |
| PF-13 | before code edits, VCS baseline is resolved by Git initialization or an explicit no-VCS exception evidence note | pass: Git initialized on `main`; evidence `docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md` |
| PF-14 | MyWebTemplate sample routes, branding, publicRoutes, generic auth/public pages, `0.0.0.0` bind behavior, and template config assumptions are removed, quarantined, disabled, renamed, or replaced in the selected unit's Go scope | **first-row requirement**; fail if any affected surface still carries MyWebTemplate product behavior, branding, or public exposure |

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

For the historical 2026-06-04 full external review, the evidence was
`docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md` and
`docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md`.

No post-import external review was run for this rebaseline issue. The current
preflight is narrowed to local skeleton/adapter-safe Go-Check and must re-gate
if the selected implementation scope crosses PF-06 or PF-09 material-expansion
boundaries.

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
- VCS decision: initialized Git ref or explicit no-VCS exception ref;
- **MyWebTemplate quarantine verification**: confirm the selected unit's
  implementation scope removes, renames, or replaces any affected MyWebTemplate
  sample/public/branding/bind/config surface.

## 5. Network And Trading Preflight

Default state for first Go implementation remains local-only and no-order
unless explicitly changed by a future owner approval. The completed
`docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md` smoke is a bounded
historical exception and does not authorize unscoped implementation behavior:

- Broker network calls outside explicitly scoped approved KIS broker-adapter units:
  denied.
- Additional KIS token/account/balance/quote/realtime/WebSocket calls outside
  explicitly scoped approved KIS broker-adapter units: denied.
- Additional KIS order/modify/cancel calls outside explicitly scoped approved
  KIS broker-adapter units: denied.
- Broker order placement outside explicitly scoped approved KIS broker-adapter units:
  denied.
- Account-affecting broker order placement: outside current scope.
- AI provider network calls: denied.
- Credential storage: denied.
- Public dashboard/LAN exposure: denied.
- Dashboard service-control actions and buy/sell controls: denied.
- Internal fake broker fills, fake balances, and fake PnL: denied.

If any selected unit needs one of these, stop and require explicit owner
approval plus matching profile/module/unit updates before proceeding.

## 6. MyWebTemplate Surface Quarantine Preflight

Before any Go-Check PASS for a unit that touches imported backend or frontend
code, verify the following surfaces are removed, quarantined, disabled,
renamed, or replaced:

- Backend sample router/service files (`backend/router/sample*`,
  `backend/service/sample*`, or equivalent generic demo endpoints).
- Frontend sample/public routes (`frontend-web/app/sample/**`,
  `frontend-web/app/public/**`, or equivalent template demo pages).
- Public route configuration entries (`publicRoutes` or unauthenticated allowlist
  entries exposing MyWebTemplate landing/auth pages).
- MyWebTemplate branding in frontend i18n and layout files (product name, logo
  references, color tokens, or copy identifying the app as MyWebTemplate).
- Generic auth/public pages carrying MyWebTemplate copy, flow, or visual identity.
- Backend bind behavior: runtime scripts must default to `127.0.0.1`, not
  `0.0.0.0`, unless a later explicit Set approval changes the exposure policy.
- Template config assumptions: `backend/config.ini` and `frontend-web/config.ini`
  remain local ignored files and must not be treated as hwiStock product config.
- Database assumptions: imported code must use `hwistock` database,
  `hwistock_core` schema, and `HWISTOCK_DATABASE_URL`; MyWebTemplate
  database/schema/migration/table/seed references are not product behavior.

## 7. Selected-Queue Network Boundary Smoke

For every included row, Go smoke must prove that the selected action does not
cross denied network or trading boundaries.

Required checks:

- Broker/KIS runtime flags remain disabled for unscoped Go rows; local secret
  files may exist but must not be loaded or used unless the selected unit
  explicitly scopes KIS broker-adapter behavior.
- No new KIS token issuance path is invoked unless the selected unit explicitly
  scopes it.
- No new KIS account, balance, quote, realtime, order, modify/cancel, HTS-ID,
  or WebSocket approval-key path is invoked unless the selected unit explicitly
  scopes it.
- No adapter or account-affecting order path is invoked.
- No AI provider network path is invoked.
- No internal fake broker fill, fake balance, or fake PnL object is produced.
- Public/LAN dashboard exposure stays disabled.
- For `HWISTOCK-UNIT-003`, network OpenDART fetch remains disabled unless a later
  source API config approval explicitly enables `DART_API_KEY`, rate cap, and
  storage policy. First Go uses fixture/config skeleton evidence.
- For `HWISTOCK-UNIT-004`, strategy defaults remain adapter-backed planning
  inputs only and cannot trigger orders.
- For `HWISTOCK-UNIT-005`, `AI_NETWORK_ENABLED=false` remains the default and no
  provider call is made.
- For `HWISTOCK-UNIT-006`, the state path stops at no-order dry-run records and
  cannot transition into submitted/accepted/fill states.
- For `HWISTOCK-UNIT-007`, UI and API surfaces remain read-only and cannot
  expose buy/sell, service-control, public/LAN, raw credential, or raw error
  behavior; MyWebTemplate branding and sample routes must not remain reachable.

## 8. Go Report Minimum Evidence

Every Go report must include:

- selected completion report and row closure refs;
- preflight PASS/FAIL table;
- changed files;
- direct-edit or worker route;
- rule-gate/manual checklist result;
- focused smoke result;
- docs/evidence output refs;
- unresolved issues;
- handoff state for Check;
- **MyWebTemplate quarantine verification result** for affected rows.

## 9. Current Status

This checklist is current authority after the 2026-06-04 MyWebTemplate
backend/frontend-web import rebaseline. All nine rows are authorized for
Go-Check **only** under the `skeleton_sandbox_safe_rebaseline_queue` scope and
with the MyWebTemplate quarantine/local-only enforcement as a first-row
requirement.

The safety boundaries below remain active constraints. They block any future
selected row if:

- the selected implementation tries to use unscoped broker/KIS, AI provider,
  adapter-order, operation-order, credential-storage, dashboard-public/LAN,
  service-control, buy/sell, fake-broker, fake-balance, fake-PnL, or
  expected-profit behavior;
- the selected unit's focused smoke rows cannot prove denied paths remain
  disabled;
- **the selected unit leaves MyWebTemplate sample routes, branding, publicRoutes,
  generic auth/public pages, `0.0.0.0` bind behavior, or template config
  assumptions in place for any implemented surface.**
