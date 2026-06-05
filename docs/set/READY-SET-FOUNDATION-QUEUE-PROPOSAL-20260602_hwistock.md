---
schema_version: hwi.ready-set-queue-proposal/v0
stage: ready-set
status: approved_active
implementation_ready_if_approved: true
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-02
updated_at: 2026-06-03
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260603_foundation.md
external_review_evidence_ref: docs/evidence/RUN-20260603_gpt-pro-foundation-ready-set-review.md
conditional_unit_006_scope: include_no_order_skeleton
---

# Foundation-Only Go Queue Proposal

## 1. Purpose

This proposal defines a narrower first Go queue that can start foundational
implementation without pretending the full trading/dashboard Ready-Set bundle is
complete.

It is now active after owner approval, ChatGPT Pro external review, findings
intake, completion report rewrite, and row-closure matrix rewrite.

## 2. Proposed Queue

| proposed_order | unit_id | include_state | allowed_first_go_scope | forbidden_in_this_queue |
| --- | --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-001 | include_docs_only | Bootstrap/profile verification and docs-only safety boundary | Product code changes |
| 2 | HWISTOCK-UNIT-008 | include | PostgreSQL schema/migration skeleton, artifact path/schema contracts, redaction-safe storage foundations | Broker calls, AI calls, trading decisions |
| 3 | HWISTOCK-UNIT-003 | include | Fixture/config-first source registry, DART disclosure schema, dedupe/event schema | Network OpenDART without later source API config approval, Naver without key/query approval, KIS/broker data, HTML scraping |
| 4 | HWISTOCK-UNIT-009 | include_docs_only | KIS capability docs/matrix refinement from local references only | KIS network calls, token issuance, account/balance calls |
| 5 | HWISTOCK-UNIT-006 | include_no_order_skeleton | No-order dry-run condition/order-state skeleton only | Broker adapter/unapproved calls, fake fills, fake balance, fake PnL, strategy-triggered orders, submitted-or-later execution |

## 3. Deferred Rows

| unit_id | defer_reason | unblock_condition |
| --- | --- | --- |
| HWISTOCK-UNIT-004 | Strategy packet not user-approved | Approve/reject/exclude `READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md` |
| HWISTOCK-UNIT-005 | AI network/cost remains disabled; foundation queue can proceed without AI orchestration | Explicit AI unit inclusion or future provider/cost approval |
| HWISTOCK-UNIT-002 | One-week runner should wait until storage/source/order skeleton exists | Start after foundation units pass Go-Check |
| HWISTOCK-UNIT-007 | Dashboard design review not run | Run/close dashboard design review or exclude dashboard from implementation bundle |

## 4. Approval Result

Owner approval result:

- Foundation-only queue approved.
- Current final external Ready-Set review for the narrowed queue selected.
- `HWISTOCK-UNIT-006` included as `include_no_order_skeleton`.

Evidence:

- `docs/evidence/RUN-20260603_gpt-pro-foundation-ready-set-review.md`
- `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260603_foundation.md`

## 5. Applied Doc Changes

Applied updates:

- `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`
- `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`
- `docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md`
- affected unit/evidence refs as needed

The completion report is now `implementation_ready: true` for this narrowed
queue only.

## 6. Safety Boundaries

- No account-affecting operation.
- No broker order placement.
- No broker network calls.
- No AI provider network calls.
- No internal fake broker fills, fake balances, or fake PnL.
- No dashboard implementation unless the dashboard row is separately closed.

## 7. Current Status

This proposal is approved and active. The current authoritative completion
report is `implementation_ready: true` for the narrowed foundation-only queue
only.
