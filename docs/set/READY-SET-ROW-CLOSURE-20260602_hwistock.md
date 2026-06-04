---
schema_version: hwi.ready-set-row-closure/v0
stage: ready-set
status: superseded_by_mywebtemplate_code_import
implementation_ready: false
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
updated_at: 2026-06-04
current_authority: false
superseded_by_rebaseline_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
superseded_reason: MyWebTemplate backend/frontend-web import invalidated the current row states; queue must be reopened/reissued.
completion_report_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
completion_audit_ref: docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md
approval_actions_ref: docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_full.md
external_review_evidence_ref: docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md
dashboard_design_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md
owner_decision_receipt_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
git_init_delta_sync_ref: docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md
kis_paper_smoke_evidence_ref: docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md
selected_queue_scope: full_queue_skeleton_sandbox_safe
---

# Ready-Set Row Closure Matrix

> Superseded notice: this matrix is historical after the 2026-06-04
> MyWebTemplate backend/frontend-web code import. The row states below are not
> current `ready_for_go_check` authority until a new row-closure matrix is
> issued against the imported code baseline.

## 1. Queue Rows

All rows below are historical after the MyWebTemplate code import. The old
`ready_for_go_check` state has been replaced with `superseded_by_code_import`;
scope limits remain only as historical context for the next reissued matrix.

| order | unit_id | unit_ref | qa_ref | row_state | allowed_first_go_scope | hard_exclusions |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-001 | `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md` | `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md` | superseded_by_code_import | Bootstrap/profile verification, docs safety boundary, project skeleton guardrails. | Product behavior, runtime trading approval. |
| 2 | HWISTOCK-UNIT-008 | `docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md` | `docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md` | superseded_by_code_import | PostgreSQL schema/migration skeleton, `hwistock_core`, artifact paths, hashes, redaction-safe evidence storage, system PnL fields. | Credentials, private identifiers, broker data ingestion, AI-calculated PnL. |
| 3 | HWISTOCK-UNIT-003 | `docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md` | `docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md` | superseded_by_code_import | Source registry, fixture/config-first ingestion, DART schema, dedupe/event schema, health/evidence outputs. | Live OpenDART without future source API approval; Naver/KIND/KRX/KIS/broker data calls; HTML scraping. |
| 4 | HWISTOCK-UNIT-009 | `docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md` | `docs/qa/QA-HWISTOCK-UNIT-009_kis-api-portal-verification.md` | superseded_by_code_import | KIS docs/capability matrix refinement and local-reference analysis only. | KIS token, account, balance, quote, realtime, order, modify/cancel, WebSocket, or broker network call. |
| 5 | HWISTOCK-UNIT-004 | `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md` | `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md` | superseded_by_code_import | Strategy/risk config, validators, rule tests, approved paper/sandbox defaults, cash reserve, holdings cap, stop validation. | Broker/AI network, paper/live orders, expected-profit claims, unapproved parameter changes. |
| 6 | HWISTOCK-UNIT-006 | `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md` | `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md` | superseded_by_code_import | Condition compiler, `condition_card/v0`, no-order dry-run records, state-machine skeleton, disabled KIS adapter boundary. | Submitted/accepted/fill transitions, broker calls, fake fills, fake balances, fake PnL. |
| 7 | HWISTOCK-UNIT-005 | `docs/units/HWISTOCK-UNIT-005_ai-orchestration-layer.md` | `docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md` | superseded_by_code_import | AI job registry, schemas, validators, prompt templates, fixture outputs, audit records with provider network disabled. | DeepSeek/ChatGPT provider calls, browser automation, model/tool execution, nonzero AI cost. |
| 8 | HWISTOCK-UNIT-002 | `docs/units/HWISTOCK-UNIT-002_home-server-paper-runner.md` | `docs/qa/QA-HWISTOCK-UNIT-002_home-server-paper-runner.md` | superseded_by_code_import | systemd files, local runner lifecycle skeleton, health/status, calendar idle behavior, local alert plumbing, no-order mode wiring. | Paper orders, broker/KIS calls, AI calls, live runner claim, one-week paper evidence claim. |
| 9 | HWISTOCK-UNIT-007 | `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md` | `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md` | superseded_by_code_import | Local read-only dashboard UI/API surfaces, masked values, sanitized errors, status/candidate/report/log panels, AI report thread. | Buy/sell controls, public/LAN exposure, service-control actions, risk/prompt/model changes. |

## 2. Scope Result

Selected queue scope: `full_queue_skeleton_sandbox_safe`.

No row is approved for operational trading, broker-backed paper trading,
AI-provider runtime behavior, public dashboard exposure, or live operation.
Every selected row must still pass the Go preflight checklist immediately before
file edits.

## 3. Closure Evidence

This matrix was rewritten after:

- owner decisions in
  `docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md`;
- dashboard design review evidence in
  `docs/evidence/RUN-20260604_dashboard-design-review.md`;
- dashboard design findings intake in
  `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md`;
- full external GPT Pro review evidence in
  `docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md`;
- full review findings intake in
  `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_full.md`;
- KIS paper/mock REST and websocket smoke evidence in
  `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md`;
- Git initialization and `.env` ignore evidence in
  `docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md`.

The full review verdict was `ready_with_exclusions`. The exclusions are encoded
in this matrix and in the completion report.

## 4. Go Boundary

Go may start only after the selected row passes
`docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md`.

Before code edits, `PF-13` required Git initialization or an explicit no-VCS
exception evidence note. This is now resolved by
`docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md`.

The row states above do not authorize:

- broker network calls outside explicitly scoped approved KIS paper/mock units;
- additional KIS token/account/balance/quote/realtime/order/modify/cancel/WebSocket calls outside the completed bounded smoke or future explicitly scoped approved KIS paper/mock units;
- AI provider network calls;
- paper order placement outside explicitly scoped approved KIS paper/mock units;
- live order placement;
- credential storage;
- public or LAN dashboard exposure;
- dashboard service-control actions or buy/sell controls;
- fake broker fills, fake balances, or fake PnL;
- expected-profit claims.
