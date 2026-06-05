---
schema_version: hwi.ready-set-row-closure-activation-draft/v0
stage: ready-set
status: draft_inactive
implementation_ready: false
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-03
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
owner_decision_brief_ref: docs/set/READY-SET-OWNER-DECISION-BRIEF-20260602_hwistock.md
foundation_queue_proposal_ref: docs/set/READY-SET-FOUNDATION-QUEUE-PROPOSAL-20260602_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
---

# Ready-Set Row Closure Activation Draft

## 1. Purpose

This draft records how row closure may be rewritten after explicit owner
approval and required review evidence. It is inactive and does not authorize Go.

The current authoritative row closure matrix remains
`docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`.

## 2. Activation Rules

This draft can be applied only after one of these owner-approved routes exists:

- full queue route: strategy decision is approved or revised, dashboard design
  review is closed or dashboard is excluded, and current final external review
  findings are closed or explicitly accepted as non-blocking
- foundation-only route: owner explicitly approves the foundation-only queue and
  also either runs current final external review for the narrowed queue or
  explicitly approves local-only Ready-Set completion for the narrowed queue,
  using one of the exact review route phrases in
  `docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md`, and explicitly
  chooses whether conditional `HWISTOCK-UNIT-006` is included as a no-order
  dry-run skeleton or excluded from the first queue

General continuation, "go", "ㄱㄱ", or "가자" is not enough.

## 3. Exact Row-State Rule

Before any Go attempt, every included row must be rewritten to exactly:

`ready_for_go_check`

If the row is docs-only, foundation-only, or otherwise constrained, preserve the
scope in a separate `scope_note`, `work_class`, or reason field instead of
changing the row state string. This keeps the Go preflight check unambiguous.

Excluded rows must use an explicit excluded state and reason, for example:

`excluded_from_first_go_queue`

## 4. Full Queue Activation Draft

Use this only if the full project Ready-Set route is approved and all full-route
reviews/decisions are closed.

| order | unit_id | activation_state | required_precondition | scope_note |
| --- | --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-001 | ready_for_go_check | completion report and final review closed | docs-only bootstrap/profile boundary; no product behavior |
| 2 | HWISTOCK-UNIT-008 | ready_for_go_check | final review closed | PostgreSQL/data/evidence storage |
| 3 | HWISTOCK-UNIT-003 | ready_for_go_check | final review closed | DART-first market intelligence ingestion |
| 4 | HWISTOCK-UNIT-009 | ready_for_go_check | final review closed | KIS docs/capability verification only; no broker network |
| 5 | HWISTOCK-UNIT-004 | ready_for_go_check | strategy decision packet approved/revised and final review closed | strategy/risk rulebook; no broker/AI network by itself |
| 6 | HWISTOCK-UNIT-006 | ready_for_go_check | final review closed and strategy boundary accepted | no-order dry-run/order-state work first; broker calls still require later explicit approval |
| 7 | HWISTOCK-UNIT-005 | ready_for_go_check | final review closed and AI cost/network remains disabled unless separately approved | AI orchestration schemas/jobs; provider network disabled by default |
| 8 | HWISTOCK-UNIT-002 | ready_for_go_check | final review closed | systemd runner/adapter evidence shell; no broker orders unless later approved |
| 9 | HWISTOCK-UNIT-007 | ready_for_go_check | dashboard design review closed and final review closed | read-only local dashboard; no buy/sell controls |

Completion report may become `implementation_ready: true` only if:

- all included rows are exactly `ready_for_go_check`
- `open_external_findings_count: 0`, or accepted non-blocking findings are
  explicitly recorded
- current final review evidence is linked
- Go preflight passes

## 5. Foundation-Only Activation Draft

Use this only if the owner explicitly approves
`docs/set/READY-SET-FOUNDATION-QUEUE-PROPOSAL-20260602_hwistock.md` and chooses
exactly one final review route from
`docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md`.

The owner must also choose the conditional `HWISTOCK-UNIT-006` scope. If the
owner includes it, use the row below. If the owner excludes it, do not include
row 5; instead rewrite `HWISTOCK-UNIT-006` as
`excluded_from_first_go_queue` with the explicit owner reason.

| order | unit_id | activation_state | required_precondition | scope_note |
| --- | --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-001 | ready_for_go_check | foundation-only queue approved | docs-only bootstrap/profile boundary |
| 2 | HWISTOCK-UNIT-008 | ready_for_go_check | foundation-only queue approved and selected final review route phrase recorded | PostgreSQL schema/migration and artifact contracts |
| 3 | HWISTOCK-UNIT-003 | ready_for_go_check | foundation-only queue approved and selected final review route phrase recorded | DART-first ingestion skeleton/source registry |
| 4 | HWISTOCK-UNIT-009 | ready_for_go_check | foundation-only queue approved and selected final review route phrase recorded | KIS docs/matrix only; no broker network |
| 5 | HWISTOCK-UNIT-006 | ready_for_go_check | include only if no-order dry-run skeleton is explicitly selected | no-order condition/order-state skeleton; no fake broker/fills/balances |
| deferred | HWISTOCK-UNIT-004 | excluded_from_first_go_queue | strategy packet not approved for implementation | strategy/risk remains Set-only until approved/revised |
| deferred | HWISTOCK-UNIT-005 | excluded_from_first_go_queue | AI implementation is not needed for foundation skeleton | AI provider network and cost remain disabled |
| deferred | HWISTOCK-UNIT-002 | excluded_from_first_go_queue | runner waits for storage/source/order skeleton | systemd runner deferred |
| deferred | HWISTOCK-UNIT-007 | excluded_from_first_go_queue | dashboard design review not closed | dashboard deferred |

Completion report may become `implementation_ready: true` for this narrowed
queue only if:

- all included rows are exactly `ready_for_go_check`
- excluded rows have explicit reasons
- the conditional `HWISTOCK-UNIT-006` include/exclude owner choice is recorded
- selected final review route phrase is recorded as either current final
  external review complete or explicit local-only narrowed approval
- Go preflight passes for the selected included row

## 6. Required Completion Report Changes If Activated

If any route is activated, update
`docs/set/READY-SET-COMPLETION-20260602_hwistock.md`:

- `status`
- `implementation_ready`
- `spec_completeness_status`
- `row_closure_status`
- `external_review_findings_status`
- `gpt_collaboration_status`
- `gpt_final_review_status`
- `gpt_final_review_evidence_ref`, if external review ran
- `open_external_findings_count`
- `go_check_queue`
- `blocked_go_reasons`

Do not change these fields until the route's evidence exists.

## 7. Safety Defaults

The activation draft never approves:

- broker network calls
- KIS token/account/balance/order calls
- KIS broker order placement
- account-affecting order placement
- AI provider network calls
- public or LAN dashboard exposure
- internal fake broker fills, fake balances, or fake PnL

Those remain denied unless a later explicit owner approval and unit/profile
change says otherwise.
