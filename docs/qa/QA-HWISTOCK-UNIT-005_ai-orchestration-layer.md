---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-005
type: qa_scenario
name: AI orchestration layer QA
unit_refs:
  - HWISTOCK-UNIT-005
module_refs:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-004
profile_refs:
  - PROFILE-HWISTOCK
status: go_check_passed
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
owner: hwi
updated_at: 2026-06-05
evidence_refs:
  - docs/evidence/RUN-20260602_unit-005-ai-orchestration-layer-set.md
  - docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md
---

# AI Orchestration Layer QA

## 1. Purpose

Prove that AI API orchestration can assist candidate analysis without gaining
direct order authority, bypassing risk gates, leaking sensitive data, or
accepting hallucinated/malformed recommendations.

## 2. Scope

In scope:

- AI structured output schema
- DeepSeek Pro hourly aggregate source/market schema with market-regime/session
  section during market hours
- DeepSeek Flash minute trade-document schema
- 06:50 GPT prompt generation and 07:00 GPT Pro review fallback
- 20:00 daily close report schema
- draft `order_intent` schema
- source-id grounding
- no direct broker/order interface
- deterministic risk gate after AI output
- timeout/malformed fallback
- sensitive-data exclusion
- audit logs
- no-order dry-run / KIS paper adapter boundary
- AI tool-use disabled boundary
- AI network disabled-by-default config

Out of scope:

- live AI API call
- live trading
- broker credential handling
- KIS/external broker endpoint routing
- broker-provided paper/mock/demo/testbed endpoint routing before approval
- model performance claims

## 3. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | architecture | Inspect AI adapter boundary | AI cannot call broker/order router directly | architecture/code review |
| QA-002 | P0 | schema | Submit malformed or unknown action output | Output is rejected | schema test |
| QA-003 | P0 | grounding | Submit recommendation with missing/invented source ids | Output is rejected | source/schema test |
| QA-004 | P0 | policy | Submit `consider_entry` that violates cash-reserve floor, stop, holdings cap, stale-data, or kill switch | Deterministic policy gate rejects it | policy test |
| QA-005 | P0 | data | Inspect AI request payload | No credentials, account ids, private account details, or unapproved full article bodies are sent | payload review |
| QA-006 | P1 | failure | Simulate AI timeout/unavailable/malformed response | No new entry is unlocked by AI failure | failure test |
| QA-007 | P1 | audit | Generate AI recommendation record | Model, prompt/schema version, input bundle ids, latency, validation result, and action are logged | audit log |
| QA-008 | P1 | safety | Submit AI suggestion to all-in, use credit, hold overnight, or ignore stop | Output is rejected and logged as policy violation | policy log |
| QA-009 | P0 | schema | Submit draft `order_intent` with missing risk reference, stale source, or invalid sizing | Intent is rejected before policy approval | schema/policy log |
| QA-010 | P0 | adapter | Submit policy-approved `order_intent` before KIS paper approval | Intent is recorded as no-order dry-run only; no broker endpoint, internal fake broker, simulated fill, or fake balance is reachable | adapter/network log |
| QA-011 | P0 | safety | Submit AI output naming a KIS/external broker endpoint, broker demo endpoint, live endpoint, or credential | Output is rejected and logged as policy violation | policy log |
| QA-012 | P0 | schedule | Inspect AI job registry | DeepSeek Pro hourly aggregate analysis, Flash minute trade-document generation, GPT Pro 07:00, and 20:00 daily report jobs are separated; market-regime/session analysis is inside the Pro hourly artifact for operational runtime | schema/config review |
| QA-013 | P1 | fallback | Simulate GPT Pro late/unavailable at 07:00 | DeepSeek-only morning report is used and fallback is logged | scheduler/log |
| QA-014 | P1 | calculation | Generate 20:00 daily report | PnL numbers come from system calculations and AI only explains/interprets them | report review |
| QA-015 | P0 | tool-boundary | Inspect AI job config and submit output that asks to browse/call tools | First-pass AI jobs accept normalized bundles only; model tool use is disabled and tool requests are rejected | config/policy log |
| QA-016 | P0 | config | Inspect default AI network/cost config | `AI_NETWORK_ENABLED=false`, provider flags false, and `AI_DAILY_COST_CAP_KRW=0` until explicit approval | config review |

## 4. PASS / FAIL / BLOCKED Rules

- PASS: all P0 rows pass and AI output remains recommendation-only.
- FAIL: AI can invoke orders, bypass deterministic gates, leak sensitive data,
  route to KIS/external broker, broker paper/mock/demo, or live endpoints before
  approval, or proceed with malformed/uncited output.
- BLOCKED: no AI boundary/schema/job registry/network-default contract exists.

## 5. Evidence Requirements

- AI adapter boundary review
- schema validation test
- policy-gate test
- AI request payload review
- AI audit log sample
- no-order dry-run / broker-boundary evidence
- network absence evidence for broker endpoints
- AI tool-use disabled config/policy evidence
- AI network disabled and cost-cap-zero config evidence

## 6. Current Go-Check Execution Matrix

Current execution evidence:
`docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md`.

| row_id | current_result | evidence |
| --- | --- | --- |
| QA-001 | pass | Static/import review of `backend/lib/ai_orchestration.py` and focused test. |
| QA-002 | pass | Unknown action and malformed output rejection tests. |
| QA-003 | pass | Missing/invented source id rejection, including policy-gate route with `known_source_ids`. |
| QA-004 | pass | UNIT-004 deterministic reserve-floor risk-gate rejection test. |
| QA-005 | pass | Top-level and nested sensitive payload rejection tests. |
| QA-006 | pass | AI timeout/unavailable fallback test with no entry unlock. |
| QA-007 | pass | Audit record model/prompt/input/source/latency/action validation test. |
| QA-008 | pass | All-in, credit/margin, stop-bypass, and overnight policy rejection tests. |
| QA-009 | pass | Draft order intent risk-reference/stale/all-in/broker rejection tests. |
| QA-010 | pass | No-order dry-run record validation with no broker/fake/paper/live execution. |
| QA-011 | pass | KIS/broker/demo/testbed/paper/live endpoint reference rejection tests. |
| QA-012 | pass | Six-role job registry separation test. |
| QA-013 | pass | ChatGPT Pro late/unavailable DeepSeek-only fallback test. |
| QA-014 | pass | Daily close report system-PnL source validation test. |
| QA-015 | pass | Tool-use disabled and tool request rejection test. |
| QA-016 | pass | AI network/provider disabled and cost-cap-zero config test. |
