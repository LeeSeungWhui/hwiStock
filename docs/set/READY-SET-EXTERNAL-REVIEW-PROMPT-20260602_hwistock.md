---
schema_version: hwi.ready-set-external-review-prompt/v0
stage: ready-set
status: sent_completed_for_foundation_only
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-02
updated_at: 2026-06-03
external_review_evidence_ref: docs/evidence/RUN-20260603_gpt-pro-foundation-ready-set-review.md
review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260603_foundation.md
---

# External Review Prompt

## 1. Use

This prompt was used after explicit owner approval for the narrowed
foundation-only ChatGPT Pro external review.

## 2. Prompt

You are reviewing a greenfield stock-trading automation project named hwiStock.
Review only the provided sanitized project docs. Do not ask for broker
credentials, account ids, env files, private balances, or unredacted personal
data.

Treat current contracts as authoritative. If older evidence notes preserve
superseded brainstorming assumptions, prefer the active `AGENTS.md`, profile,
current module/unit/QA/source docs, completion report, row closure matrix, gate
evidence matrix, and current-state snapshot.

Review goal:

- Determine whether the Ready-Set planning bundle is implementation-ready.
- Use findings first, with P0/P1/P2 severity.
- Focus on safety, broker/API boundaries, AI/order separation, strategy/risk
  gaps, QA adequacy, evidence requirements, and whether the first Go queue
  should include or exclude trading/dashboard rows.

Important project constraints:

- No account-affecting operation is approved.
- No broker network calls are approved.
- No AI provider network calls are approved.
- Before KIS adapter approval, order intents must stop at no-order dry-run records.
- If a foundation-only queue is chosen, `HWISTOCK-UNIT-006` must be explicitly
  included as a no-order dry-run condition/order-state skeleton or explicitly
  excluded from the first queue.
- Internal fake broker fills, fake balances, and fake PnL are forbidden.
- Capital is cash-only; credit, margin, 미수, borrowed funds, and leverage are
  forbidden.
- Starting operation capital is 2,000,000 KRW; KIS adapter target budget is 10,000,000
  KRW pending adapter balance evidence.
- Maximum simultaneous holdings is 5.
- There is no fixed per-symbol allocation cap; every buy must preserve
  `minimum_cash_reserve_ratio = 0.25`.
- AI can analyze/rank/explain but cannot place orders or override deterministic
  gates.
- Dashboard is read-only and must not expose buy/sell controls.

Artifacts to review:

- `AGENTS.md`
- `docs/index.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/modules/*.md`
- `docs/units/*.md`
- `docs/qa/*.md`
- `docs/sources/*.md`
- `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`
- `docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md`
- `docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md`
- `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`
- `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`
- `docs/set/READY-SET-FOUNDATION-QUEUE-PROPOSAL-20260602_hwistock.md`
- `docs/set/READY-SET-EXTERNAL-REVIEW-SHARE-MANIFEST-20260602_hwistock.md`
- `docs/set/READY-SET-OWNER-DECISION-BRIEF-20260602_hwistock.md`
- `docs/set/READY-SET-OWNER-DECISION-RECEIPT-TEMPLATE-20260603_hwistock.md`
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md`
- `docs/set/READY-SET-GATE-EVIDENCE-MATRIX-20260603_hwistock.md`
- `docs/set/READY-SET-RULE-PRESET-APPLICABILITY-MATRIX-20260603_hwistock.md`
- `docs/evidence/RUN-20260603_root-vcs-env-scan.md`
- `docs/evidence/RUN-20260603_ready-set-current-state-snapshot.md`
- `docs/evidence/RUN-20260602_external-review-presend-dry-run.md`
- `docs/evidence/*.md`

Questions:

1. Are there any P0 blockers before any implementation starts?
2. Is the broker boundary safe and internally consistent?
3. Is the AI boundary safe and internally consistent?
4. Are there any apparent conflicts where older evidence notes contradict the
   current profile/module/unit/completion/snapshot state?
5. Is the strategy decision packet safe enough for adapter-backed planning only?
6. Should the first Go queue be full, or foundation-only with strategy/dashboard
   excluded?
7. Are the QA scenarios sufficient for Go/Check and later one-week Prove?
8. Does the owner-decision brief make the remaining approval boundaries clear?
9. Does the owner decision receipt checklist in
   `docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md` prevent ambiguous
   owner messages from being treated as broker, AI, order, Go, strategy, or
   external-review approval?
10. Does
   `docs/set/READY-SET-OWNER-DECISION-RECEIPT-TEMPLATE-20260603_hwistock.md`
   provide a safe classification shape for approval-driven closure evidence?
11. Does the Go preflight checklist correctly block implementation until the
   completion report, row closure, review, strategy, design, and network/trading
   gates are satisfied, including `PF-11` owner decision receipt recording for
   approval-driven closure?
12. Does the Go preflight checklist correctly block foundation-only closure with
   `PF-12` until `HWISTOCK-UNIT-006` is explicitly included as a no-order
   skeleton or excluded from the first queue?
13. Does the gate evidence matrix accurately distinguish local Set completeness
   from approval/review blockers?
14. Does the root/VCS/env baseline create any additional blocker or required
   first-Go sequencing decision?
15. Does the current Ready-Set state snapshot accurately preserve the current
   foundation-only pass state and remaining full-queue exclusions?
16. What must change before `implementation_ready: true`?

Output format:

- Findings first: P0, P1, P2.
- Then readiness verdict: `ready`, `not_ready`, or `ready_with_exclusions`.
- Then required doc changes.
- Then acceptable exclusions, if any.
- Then residual risks.
