---
schema_version: hwi.ready-set-owner-decision-brief/v0
stage: ready-set
status: foundation_only_selected
implementation_ready: true
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-02
updated_at: 2026-06-03
strategy_decision_packet_ref: docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md
approval_actions_ref: docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md
foundation_queue_proposal_ref: docs/set/READY-SET-FOUNDATION-QUEUE-PROPOSAL-20260602_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260603_foundation.md
external_review_evidence_ref: docs/evidence/RUN-20260603_gpt-pro-foundation-ready-set-review.md
selected_queue_scope: foundation_only
conditional_unit_006_scope: include_no_order_skeleton
---

# Ready-Set Owner Decision Brief

## 1. Current Verdict

Ready-Set is implementation-ready for the narrowed foundation-only queue only.

Current authoritative report:
`docs/set/READY-SET-COMPLETION-20260602_hwistock.md`.

Current status:

- `implementation_ready: true` for selected foundation rows only.
- Go is allowed only after selected-row preflight passes.
- No broker network call is approved.
- No AI provider network call is approved.
- ChatGPT Pro external review has run for the narrowed foundation-only queue.
- No live or paper order placement is approved.

## 2. Decisions Already Closed

These do not need a new owner decision unless the policy changes:

- Capital mode is cash-only.
- Live starting capital baseline is 2,000,000 KRW.
- KIS is the selected broker direction; KB is blocked for now.
- No internal fake broker fills, fake balances, or fake PnL.
- KIS paper/mock target budget is 10,000,000 KRW until account evidence proves
  the actual paper balance.
- Maximum simultaneous holdings is 5.
- There is no fixed per-symbol maximum allocation in the first policy.
- Every buy must preserve `minimum_cash_reserve_ratio = 0.25` of total capital.
- AI may recommend a per-entry stop price, but deterministic gates reject
  missing, stale, unauditable, disabled, or wider-than--5% stop output.
- Dashboard is read-only and local-only by default.
- First Go queue is narrowed to foundation-only rows.
- `HWISTOCK-UNIT-006` is included only as a no-order dry-run condition/order
  state skeleton.
- Strategy, AI implementation, runner, and dashboard rows are excluded from the
  first Go queue.

## 3. Future Owner Choices

These choices are not needed for the current foundation-only Go queue. They are
needed only when expanding beyond the selected first queue.

### Choice A: Strategy Defaults

Future strategy Go requires deciding whether to approve, reject, revise, or
exclude the first-pass strategy defaults in
`docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.

Recommended approval phrase:

> Approve the first-pass strategy defaults in
> `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md` for
> paper/sandbox planning only. Keep broker and AI network calls disabled until
> later explicit approval.

This does not approve broker calls, AI calls, paper orders, live orders, or
claims of expected profit.

### Choice B: Further External Review Route

The current final external review has already run for the narrowed foundation
queue. Future full-queue expansion may require a new current review after
strategy/dashboard/AI/runner docs change.

### Choice C: Dashboard Design Review

Dashboard implementation remains blocked because the dashboard row is excluded
from the first Go queue.

Recommended phrase:

> Run `agy` Gemini Pro dashboard design review using
> `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`.

This does not authorize dashboard implementation by itself.

### Choice D: Full Queue Expansion

Full queue expansion requires strategy approval/revision, dashboard design
review or explicit dashboard exclusion, and a fresh review if the Set closure
artifacts materially change.

## 4. Recommended Next Move

Run selected-row Go preflight for one included foundation row:

1. Resolve the no-VCS baseline by initializing Git or recording an explicit
   no-VCS exception.
2. Prove selected-queue network boundaries remain disabled.
3. Route non-trivial edits through `delegation-guard`.

## 5. Non-Approval Reminder

Continuation, "go", "가자", "ㄱㄱ", or general enthusiasm does not count as
approval for:

- broker network calls
- token issuance
- account/balance calls
- paper order placement
- live order placement
- AI provider network calls
- external review sending
- full-queue expansion
- strategy parameter changes
- dashboard design review execution
- Ready-Set gate override
