---
schema_version: hwi.evidence/v0
id: RUN-20260602-ai-orchestration-layer
type: evidence
name: AI orchestration layer evidence
unit_refs:
  - HWISTOCK-UNIT-005
module_refs:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-004
profile_refs:
  - PROFILE-HWISTOCK
status: draft
created_at: 2026-06-02
environment: docs_only
---

# AI Orchestration Layer Evidence

## Supersession Note

Later 2026-06-02 profile updates supersede the internal `mock_broker_api`
direction in this historical evidence. Current policy: no internal fake broker
execution path; pre-approval behavior is no-order dry-run only, and the first
broker-backed path is approved KIS KRX broker-adapter.

## Summary

Created the initial docs-only AI orchestration contract for `hwiStock`. The
contract allows AI API use for candidate synthesis, ranking, explanation, and
operation review, but forbids AI from placing orders or overriding deterministic
risk gates.

## Safety Decisions

- AI output is recommendation-only.
- AI cannot call broker/order interfaces.
- AI cannot override cash-reserve floor, holdings cap, stop-loss, cooldown,
  daily loss halt, stale data rejection, or manual kill switch.
- AI output must be structured and source-grounded.
- AI may produce a draft `order_intent`, but it is non-executable until
  deterministic policy gates approve it.
- Before approved KIS broker-adapter integration, approved intents can only be recorded
  as no-order dry-run decisions; no internal fake broker/fill simulator is used.
- KIS/external broker endpoints remain disabled until an approved broker-network
  unit. KIS KRX broker-adapter is the planned first broker-backed path
  after explicit approval and smoke; no internal fake broker/fill simulator is
  used before that.
- Malformed, uncited, stale, low-confidence, or policy-violating AI output is
  rejected.
- AI provider/model/prompt/schema/network use requires explicit approval before
  implementation.

## Follow-Up

- Select AI provider/model only after provider docs, cost, latency, privacy, and
  reliability are reviewed.
- Decide whether AI gets tool access or only normalized input bundles.
- Define concrete JSON schema before implementation.
- Define concrete draft `order_intent` schema before implementation.
- Define no-order dry-run schema and KIS KRX broker adapter schema/fallback
  before implementation.
- Build adapter-bound tests before any operation-readiness discussion.
