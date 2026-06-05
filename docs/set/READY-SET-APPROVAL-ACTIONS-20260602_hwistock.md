---
schema_version: hwi.ready-set-approval-actions/v0
stage: ready-set
status: full_queue_action_closed
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-02
updated_at: 2026-06-04
owner_decision_receipt_template_ref: docs/set/READY-SET-OWNER-DECISION-RECEIPT-TEMPLATE-20260603_hwistock.md
external_review_presend_dry_run_ref: docs/evidence/RUN-20260602_external-review-presend-dry-run.md
foundation_review_evidence_ref: docs/evidence/RUN-20260603_gpt-pro-foundation-ready-set-review.md
foundation_review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260603_foundation.md
full_queue_owner_decision_receipt_ref: docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md
dashboard_design_review_evidence_ref: docs/evidence/RUN-20260604_dashboard-design-review.md
dashboard_design_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md
full_review_evidence_ref: docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md
full_review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_full.md
selected_queue_scope: full_queue_skeleton_adapter_safe
---

# Ready-Set Approval Actions

## 1. Purpose

This file lists the exact owner choices that can move hwiStock from
`implementation_ready: false` toward `implementation_ready: true`.

Current result: Actions 1, 2, and 3 are closed for full Ready-Set expansion.
The active selected queue is now `full_queue_skeleton_sandbox_safe` after the
strategy approval, dashboard design review, and current final external GPT Pro
review were recorded and normalized.

The earlier Action 4 foundation-only route remains historical evidence, but it
is no longer the active selected queue.

Owner-facing decision summary:
`docs/set/READY-SET-OWNER-DECISION-BRIEF-20260602_hwistock.md`.

Go preflight checklist:
`docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md`.

## 2. Available Actions

### Action 1: Approve First-Pass Strategy Defaults

Approval phrase:

> Approve the first-pass strategy defaults in
> `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md` for
> adapter-backed planning only. Keep broker and AI network calls disabled until
> later explicit approval.

Effect:

- Allows `HWISTOCK-UNIT-004` to move from
  `blocked_until_strategy_decision_approval` to final-review-pending.
- Does not approve broker network calls.
- Does not approve AI network calls.
- Does not approve account-affecting operation.

### Action 2: Run Dashboard Design Review

Approval phrase:

> Run `agy` Gemini Pro dashboard design review using
> `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`.

Effect:

- Produces design review findings for `HWISTOCK-UNIT-007`.
- Allows dashboard row closure only after P0/P1 design findings are applied,
  accepted, or row-excluded.
- Does not authorize dashboard implementation by itself.

### Action 3: Run Current Final External Review

Approval phrase:

> Run current final external Ready-Set review using
> `docs/set/READY-SET-EXTERNAL-REVIEW-PACKET-20260602_hwistock.md`.

Effect:

- Produces current final review evidence.
- Can close a current-final-review blocker only if review findings are closed or
  explicitly non-blocking. This is now closed for the narrowed foundation-only
  queue and remains a future requirement for material full-queue expansion.
- Does not authorize sharing secrets, env files, keys, account ids, or private
  account data.

Pre-send requirements:

- Re-read
  `docs/set/READY-SET-EXTERNAL-REVIEW-SHARE-MANIFEST-20260602_hwistock.md`.
- Rebuild the outgoing candidate list and confirm it exactly matches the
  current pre-send dry-run list in
  `docs/evidence/RUN-20260602_external-review-presend-dry-run.md`.
- Run a fresh fail-closed candidate-scoped secret-pattern scan over the intended
  share set and require `no_matches`.
- Confirm that `env.sh`, `/home/hwi/.config/hwistock/*`, `apiRefer/*.xlsx`,
  credentials, account identifiers, AI keys, real balances, and runtime data are
  absent from the outgoing bundle.
- Record the final review output under `docs/evidence/` and link it back into
  the completion report before changing `gpt_final_review_status`.

### Action 4: Approve Narrow Foundation-Only Queue

Queue approval phrase:

> Approve the foundation-only Go queue proposal in
> `docs/set/READY-SET-FOUNDATION-QUEUE-PROPOSAL-20260602_hwistock.md`.

The queue approval must be paired with exactly one final review route phrase:

> Run current final external Ready-Set review for the narrowed foundation-only
> queue using
> `docs/set/READY-SET-EXTERNAL-REVIEW-PACKET-20260602_hwistock.md`.

or:

> Approve local-only Ready-Set completion for the narrowed foundation-only queue.
> Do not run external review for this narrowed queue.

The same owner decision must also include exactly one conditional
`HWISTOCK-UNIT-006` scope phrase:

> Include `HWISTOCK-UNIT-006` no-order dry-run condition/order-state skeleton in
> the narrowed foundation-only queue.

or:

> Exclude `HWISTOCK-UNIT-006` from the narrowed foundation-only queue for now.

Effect:

- Lets the Ready-Set completion report be rewritten around an explicitly
  narrowed queue only if the row closure matrix also marks excluded rows with
  reasons.
- Keeps `HWISTOCK-UNIT-006` not Go-eligible unless the owner explicitly selects
  the no-order dry-run skeleton scope for this conditional row.
- Avoids implementing full trading/dashboard behavior before strategy/design
  approvals.
- Still requires the selected final review route to be recorded in the
  completion report.

## 3. Owner Decision Receipt Checklist

Before changing row closure, completion status, or Go preflight state based on
an owner message, record a short decision receipt in the next evidence/update
note. The receipt must include:

| field | required_value |
| --- | --- |
| received_at | timestamp or conversation turn reference |
| owner_message | exact owner phrase, or a clearly equivalent explicit instruction |
| matched_action | Action 1 / Action 2 / Action 3 / Action 4 |
| route_scope | full queue / foundation-only queue / dashboard-only / strategy-only |
| conditional_unit_006_scope | required for Action 4: `include_no_order_skeleton` / `exclude_from_first_queue` / `not_applicable` |
| external_review_presend_dry_run_ref | required for Action 3 before external send |
| outgoing_candidate_count | required for Action 3; current prepared count is `80` |
| candidate_exact_match_result | required for Action 3; must be `pass` before external send |
| candidate_secret_scan_result | required for Action 3; fail-closed scan must be `no_matches` before external send |
| approvals_granted | list only approvals actually granted by the owner message |
| approvals_not_granted | broker calls, AI calls, broker orders, account-affecting orders, credential storage, and Go remain denied unless explicitly granted |
| docs_to_update | completion report, row closure matrix, audit, findings intake, or preflight refs supported by the decision |
| pf11_effect | `fail` / `pass_candidate` / `not_applicable`; only written receipt evidence can move PF-11 toward pass |
| still_blocked_by | any remaining owner/review blocker after this decision |

Ambiguous enthusiasm, continuation, or partial wording is not enough. If the
message does not clearly match one of the approval phrases or an equally explicit
instruction, keep the row blocked and ask for the missing decision.

Receipt template:
`docs/set/READY-SET-OWNER-DECISION-RECEIPT-TEMPLATE-20260603_hwistock.md`.

## 4. Recommended Next Action

Recommended next action after full Ready-Set closure:

1. Select a single row from the full queue.
2. Run `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md` for
   that row.
3. Resolve `PF-13` before code edits by initializing Git or recording an
   explicit no-VCS exception evidence note.
4. Proceed to Go-Check only inside the selected row's
   `full_queue_skeleton_sandbox_safe` scope.

## 5. Non-Approval Reminder

Continuation, "go", or general enthusiasm does not count as approval for broker
network calls, AI network calls, external review sending, strategy parameter
changes, dashboard design review execution, or Ready-Set gate override. Use the
approval phrases above or an equally explicit instruction.
