---
schema_version: hwi.ready-set-row-closure/v0
stage: ready-set
status: active
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
updated_at: 2026-06-05
current_authority: true
implementation_ready: true
implementation_ready_scope: skeleton_sandbox_safe_rebaseline_queue
owner_decision_ref: docs/set/READY-SET-OWNER-DECISION-20260604_rebaseline_hwistock.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md
rebaseline_evidence_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
ready_set_reissue_evidence_ref: docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md
prior_row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
completion_audit_ref: docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md
completion_audit_status: historical_before_mywebtemplate_import
approval_actions_ref: docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md
external_review_evidence_ref: docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md
external_review_evidence_status: historical_before_mywebtemplate_import_supporting_context
dashboard_design_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md
owner_decision_receipt_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
git_init_delta_sync_ref: docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md
kis_paper_smoke_evidence_ref: docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md
selected_queue_scope: full_queue_skeleton_sandbox_safe
---

# Ready-Set Row Closure Matrix — Rebaseline 2026-06-04

> **Scope notice**: This matrix is current authority after the 2026-06-04
> MyWebTemplate code import rebaseline. Every row's allowed first Go scope
> explicitly includes MyWebTemplate sample/public quarantine and local-only
> bind/access enforcement as a **first-row requirement**, not optional cleanup.

## 1. Queue Rows

| order | unit_id | unit_ref | qa_ref | row_state | allowed_first_go_scope | hard_exclusions |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-001 | `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md` | `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md` | go_check_passed | Bootstrap/profile verification, docs safety boundary, project skeleton guardrails, and **MyWebTemplate sample/public quarantine verification**. | Product behavior, runtime trading approval, unscoped broker/AI/network calls. |
| 2 | HWISTOCK-UNIT-008 | `docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md` | `docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md` | go_check_passed | PostgreSQL schema/migration skeleton, `hwistock_core`, artifact paths, hashes, redaction-safe evidence storage, system PnL fields, and **hwiStock DB isolation from MyWebTemplate assumptions**. | Credentials, private identifiers, broker data ingestion, AI-calculated PnL, MyWebTemplate database/schema sharing. |
| 3 | HWISTOCK-UNIT-003 | `docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md` | `docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md` | go_check_passed | Source registry, fixture/config-first ingestion, DART schema, dedupe/event schema, health/evidence outputs, KST timestamp/body-policy enforcement, and **no sample/demo backend surface exposure**. | Live OpenDART without future source API approval; Naver/KIND/KRX/KIS/broker data calls; HTML scraping; MyWebTemplate sample routes. |
| 4 | HWISTOCK-UNIT-009 | `docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md` | `docs/qa/QA-HWISTOCK-UNIT-009_kis-api-portal-verification.md` | go_check_passed | KIS docs/capability matrix refinement and local-reference analysis only. | KIS token, account, balance, quote, realtime, order, modify/cancel, WebSocket, or broker network call; MyWebTemplate assumptions in generated reference code. |
| 5 | HWISTOCK-UNIT-004 | `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md` | `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md` | go_check_passed | Strategy/risk config, validators, rule tests, approved paper/sandbox defaults, cash reserve, holdings cap, stop validation, and **no sample/demo backend surface exposure**. | Broker/AI network, paper/live orders, expected-profit claims, unapproved parameter changes, MyWebTemplate sample routes. |
| 6 | HWISTOCK-UNIT-006 | `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md` | `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md` | go_check_passed | Condition compiler, `condition_card/v0`, no-order dry-run records, state-machine skeleton, disabled KIS adapter boundary, and **no sample/demo backend surface exposure**. | Submitted/accepted/fill transitions, broker calls, fake fills, fake balances, fake PnL, MyWebTemplate sample routes. |
| 7 | HWISTOCK-UNIT-005 | `docs/units/HWISTOCK-UNIT-005_ai-orchestration-layer.md` | `docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md` | go_check_passed | AI job registry, schemas, validators, source grounding, sensitive-payload review, audit/no-order dry-run records with provider network disabled, and **no sample/demo backend surface exposure**. | DeepSeek/ChatGPT provider calls, browser automation, model/tool execution, nonzero AI cost, broker/KIS calls, MyWebTemplate sample routes. |
| 8 | HWISTOCK-UNIT-002 | `docs/units/HWISTOCK-UNIT-002_home-server-paper-runner.md` | `docs/qa/QA-HWISTOCK-UNIT-002_home-server-paper-runner.md` | go_check_passed | systemd files, local runner lifecycle skeleton, health/status, calendar idle behavior, local alert plumbing, no-order mode wiring, and **local-only `127.0.0.1` bind enforcement**. | Paper orders, broker/KIS calls, AI calls, live runner claim, one-week paper evidence claim, public/LAN exposure. |
| 9 | HWISTOCK-UNIT-007 | `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md` | `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md` | go_check_passed | Local read-only dashboard UI/API surfaces, masked values, sanitized errors, status/candidate/report/log panels, AI report thread, and **removal/replacement of MyWebTemplate branding, sample routes, publicRoutes, and generic auth/public pages**. | Buy/sell controls, public/LAN exposure, service-control actions, risk/prompt/model changes, MyWebTemplate branding/sample pages as reachable surfaces. |

## 2. Scope Result

Selected queue scope: `full_queue_skeleton_sandbox_safe`.

MyWebTemplate quarantine and local-only bind/access are **first-row requirements**
for the rebaseline queue. No row is approved for operational trading,
broker-backed paper trading, AI-provider runtime behavior, public dashboard
exposure, or live operation. Every selected row must still pass the Go
preflight checklist immediately before file edits.

## 3. Closure Evidence

This matrix is issued after:

- Owner decision to quarantine MyWebTemplate sample/public surfaces:
  `docs/set/READY-SET-OWNER-DECISION-20260604_rebaseline_hwistock.md`.
- Rebaseline evidence that the prior queue is superseded:
  `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`.
- Direct-CWD worker reissue evidence:
  `docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md`.
- Historical owner decisions, external review evidence, dashboard design
  evidence, and KIS paper/mock smoke preserved as supporting context. These
  historical reviews were not re-run after the MyWebTemplate code import.

## 4. Go Boundary

Go may start only after the selected row passes
`docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md`.

Before code edits, `PF-13` requires Git initialization or an explicit no-VCS
exception evidence note. This is resolved by
`docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md`.

The row states above do not authorize:

- broker network calls outside explicitly scoped approved KIS paper/mock units;
- additional KIS token/account/balance/quote/realtime/WebSocket calls outside the completed bounded smoke or future explicitly scoped approved KIS paper/mock units;
- additional KIS order/modify/cancel calls outside the completed bounded smoke;
- paper order placement outside explicitly scoped approved KIS paper/mock units;
- live order placement;
- AI provider network calls;
- credential storage;
- public or LAN dashboard exposure;
- dashboard service-control actions or buy/sell controls;
- fake broker fills, fake balances, or fake PnL;
- expected-profit claims;
- leaving MyWebTemplate sample routes, branding, publicRoutes, generic auth/public
  pages, `0.0.0.0` bind behavior, or template config assumptions in place for
  any implemented surface.

## 5. Go-Check Progress

This section records implementation progress without changing the Ready-Set
queue authorization meaning of `row_state`.

| unit_id | go_check_status | evidence | note |
| --- | --- | --- | --- |
| HWISTOCK-UNIT-001 | pass | `docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md` | Docs-only rebaseline verification. |
| HWISTOCK-UNIT-002 | pass | `docs/evidence/RUN-20260604_unit-002-go-check.md` | Local-only runner/systemd skeleton, no-order metadata, loopback-only bind, and accepted GPT-5.4 closure review. |
| HWISTOCK-UNIT-008 | pass | `docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md` | Current-tree storage skeleton with typed artifact contracts, canonical artifact paths, `hwistock_core` Alembic migration skeleton, system-only daily PnL, focused tests, and bounded Check review. |
| HWISTOCK-UNIT-003 | pass | `docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md` | Current-tree fixture/config-first market-intelligence ingestion skeleton with approved/conditional/deferred/forbidden source registry, duplicate linking, KST timestamp validation, registry-controlled body policy, focused tests, and bounded Check review remediation. |
| HWISTOCK-UNIT-004 | pass | `docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md` | Current-tree stdlib-only strategy/risk rulebook skeleton with reserve-floor sizing, holdings cap, AI-stop validation, no-order dry-run records, focused tests, and preserved no-broker/no-fake-simulation boundaries. |
| HWISTOCK-UNIT-005 | pass | `docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md` | Current-tree stdlib-only AI orchestration foundation with disabled AI network/provider/cost defaults, six-role job registry, `ai_recommendation/v0` validation, source grounding, sensitive-payload review, deterministic UNIT-004 policy-gate handoff, no-order dry-run records, audit/fallback reports, tool-use-disabled behavior, and focused tests. |
| HWISTOCK-UNIT-006 | pass | `docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md` | Current-tree stdlib-only trading-engine/order-state foundation skeleton with `condition_card/v0` validation, deterministic compiler, UNIT-004 risk-gate delegation plus SOR/AUTO_SESSION route normalization-or-blocking, dry-run-only state transitions through `dry_run_recorded`, KIS paper capability flags, fixture-only evidence representation, and focused tests. |
| HWISTOCK-UNIT-009 | pass | `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md` | Docs-only current-authority rebaseline closure for KIS capability verification, sanitized KRX paper smoke cross-reference, and preserved partial boundaries without new broker/KIS network authorization. |
| HWISTOCK-UNIT-007 | pass | `docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md` | Current-tree read-only dashboard operator console with tasks/settings subroutes, root/public/sample quarantine, masked/sanitized values, local-only/public boundary, focused frontend tests/eslint, and scoped rule-gate zero findings; broader imported frontend baseline and quarantined route files remain documented limitations. |
