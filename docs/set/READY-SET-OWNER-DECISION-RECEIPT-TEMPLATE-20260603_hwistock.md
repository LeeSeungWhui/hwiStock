---
schema_version: hwi.ready-set-owner-decision-receipt-template/v0
stage: ready-set
status: prepared_template
implementation_ready: false
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-03
updated_at: 2026-06-03
approval_actions_ref: docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md
external_review_presend_dry_run_ref: docs/evidence/RUN-20260602_external-review-presend-dry-run.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
---

# Owner Decision Receipt Template

## 1. Purpose

This template is used only after the owner gives an explicit Ready-Set
approval, exclusion, review-run instruction, or local-only narrowed-queue
instruction.

It is a template only. It does not record any actual owner approval and does not
authorize Go, external review sending, broker calls, AI provider calls, adapter
orders, account-affecting orders, or credential storage.

## 2. Receipt Header

Copy this header into the next evidence/update note when an owner decision is
received:

| field | value |
| --- | --- |
| receipt_id | `OWNER-DECISION-YYYYMMDD-name` |
| received_at | timestamp or conversation turn reference |
| owner_message | exact owner phrase, or a clearly equivalent explicit instruction |
| matched_action | Action 1 / Action 2 / Action 3 / Action 4 / no_match |
| matched_phrase_ref | quote the exact phrase from `docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md`, or explain the equivalent instruction |
| route_scope | full queue / foundation-only queue / dashboard-only / strategy-only / external-review-only |
| conditional_unit_006_scope | required for Action 4: `include_no_order_skeleton` / `exclude_from_first_queue` / `not_applicable` |
| external_review_presend_dry_run_ref | required for Action 3 before external send |
| outgoing_candidate_count | required for Action 3; current prepared count is `80` |
| candidate_exact_match_result | required for Action 3; must be `pass` before external send |
| candidate_secret_scan_result | required for Action 3; fail-closed scan must be `no_matches` before external send |
| approvals_granted | list only approvals actually granted by the owner message |
| approvals_not_granted | broker calls, AI calls, broker orders, account-affecting orders, credential storage, public/LAN dashboard exposure, and Go remain denied unless explicitly granted |
| docs_to_update | completion report, row closure matrix, completion audit, review findings intake, Go preflight, or evidence refs supported by the decision |
| pf11_effect | `fail` / `pass_candidate` / `not_applicable`; only `pass_candidate` can later become PF-11 pass after the receipt is written |
| still_blocked_by | remaining owner/review blockers after this decision |

## 3. Classification Rules

- `no_match`: continuation, enthusiasm, vague "go", "continue", "looks good",
  or partial wording that does not clearly match an approval action.
- `Action 1`: strategy defaults are approved for adapter-backed planning only.
- `Action 2`: dashboard design review may be run; dashboard implementation is
  still not approved.
- `Action 3`: current final external Ready-Set review may be run only after a
  fresh pre-send file rebuild, exact-match comparison against the dry-run list,
  and fail-closed candidate-scoped secret-pattern scan.
- `Action 4`: foundation-only queue is approved only when the queue approval
  phrase is paired with exactly one final review route phrase and exactly one
  conditional `HWISTOCK-UNIT-006` include/exclude scope phrase.

When the message is ambiguous, keep all row/completion states blocked and ask
for the missing decision instead of inferring approval.

## 4. Non-Grant Defaults

Unless explicitly granted in the same owner decision, the following remain
denied:

- broker network calls
- KIS token/account/balance/order calls
- KIS broker order placement
- account-affecting order placement
- AI provider network calls
- credential storage
- public or LAN dashboard exposure
- dashboard buy/sell controls
- internal fake broker fills, fake balances, or fake PnL
- Go implementation

## 5. Required Follow-Up By Receipt Type

| matched_action | required_follow_up |
| --- | --- |
| Action 1 | Record receipt, update strategy row blocker only if the message is explicit, keep broker/AI/order/Go denied. |
| Action 2 | Record receipt, run or prepare design review only after route/tool approval remains current, normalize findings before row closure. |
| Action 3 | Record receipt, rebuild outgoing candidate list, require exact match against the current dry-run list, rerun fail-closed candidate-scoped secret scan, then send only sanitized docs if still approved. |
| Action 4 | Record receipt, verify exactly one final review route phrase and exactly one conditional `HWISTOCK-UNIT-006` scope, then rewrite row closure only if included/excluded rows are explicit. |
| no_match | Do not update row closure, completion, or preflight pass state. Ask for the missing explicit decision. |

## 6. Current Status

No owner decision has been received in this template. Ready-Set remains
`implementation_ready: false`.
