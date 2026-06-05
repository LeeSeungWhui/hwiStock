---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-005-ai-orchestration-layer-set
type: evidence
name: UNIT-005 AI orchestration layer Set
stage: set
environment: docs_only
status: pass_with_followups
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-05
superseded_by:
  - RUN-20260605-owner-runtime-architecture-clarification
  - RUN-20260605-ready-set-operational-automated-trading-program
superseded_note: >
  This evidence records the first-pass UNIT-005 Set state from 2026-06-02.
  The operational AI runtime roles and schemas are superseded by the
  2026-06-05 owner-clarified Ready-Set: DeepSeek Pro writes the hourly
  aggregate including market-regime analysis, and DeepSeek Flash writes one
  market-minute trade document whose candidate list contains at most five
  symbols and is portfolio/order-state aware.
unit_refs:
  - HWISTOCK-UNIT-005
module_refs:
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-001
profile_refs:
  - PROFILE-HWISTOCK
---

# UNIT-005 AI Orchestration Layer Set

> Supersession note (2026-06-05): this file is historical evidence for the
> first-pass UNIT-005 Set. Current operational AI runtime authority is
> `RUN-20260605_owner-runtime-architecture-clarification.md`,
> `RUN-20260605_ready-set-operational-paper-trading-program.md`,
> `HWISTOCK-MOD-009_operational-paper-trading-program.md`, and
> `HWISTOCK-UNIT-012_ai-analysis-runtime.md`.

## 1. Scope

This docs-only Set pass closed the first AI orchestration contract for
hwiStock. It defines schedules, schemas, validation boundaries, fallback rules,
tool-use policy, and network/cost defaults.

No AI API call, browser ChatGPT session, broker call, token request, or order
placement was attempted.

## 2. Sources Checked

| source | use |
| --- | --- |
| `docs/profiles/PROFILE-HWISTOCK.md` | AI approval policy, selected model roles, no-order dry-run and broker boundary |
| `docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md` | durable AI orchestration module contract |
| `docs/units/HWISTOCK-UNIT-005_ai-orchestration-layer.md` | execution contract for AI schedules/schemas/fallback |
| `docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md` | QA scenario rows and evidence requirements |
| `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md` | downstream `condition_card/v0` and no-order dry-run boundary |

## 3. Set Decisions

| decision | result |
| --- | --- |
| AI role | AI is analysis/recommendation only and cannot place orders or override deterministic gates. |
| Job registry | Six first-pass jobs are defined: hourly DeepSeek Pro news, hourly 08:00-19:00 DeepSeek Pro market-regime, event-triggered DeepSeek Flash intraday labels, 06:50 GPT prompt generation, 07:00 GPT Pro review, and 20:00 daily close report. |
| GPT cutoff | ChatGPT Pro morning review hard cutoff is 07:20 KST. Late output is commentary/fallback only. |
| Output schemas | First schemas are `ai_recommendation/v0`, `hourly_intel_analysis/v0`, `market_regime_report/v0`, `intraday_candidate_label/v0`, `gpt_morning_prompt/v0`, `morning_review_report/v0`, and `daily_close_report/v0`. |
| Allowed actions | `watch`, `reject`, `consider_entry`, `hold_review`, `exit_review`. Unknown actions are rejected. |
| Tool policy | AI tool use is disabled first-pass; models receive normalized input bundles only. |
| Network defaults | `AI_NETWORK_ENABLED=false`, provider enable flags false, and `AI_DAILY_COST_CAP_KRW=0` until explicit approval. |
| Fallback | AI failure does not unlock new AI-originated entries. GPT fallback uses DeepSeek-only morning report with reason logging. |
| Sensitive data | No credentials, account ids, private account details, unapproved full article bodies, or broker/order handles may be sent to AI. |
| PnL | Daily close report uses system-calculated PnL references; AI only explains/interprets. |

## 4. Acceptance Closure

| ac_id | result | note |
| --- | --- | --- |
| AC-01 | set | AI has no direct broker/order interface. |
| AC-02 | set | Structured output schemas and rejection behavior are defined. |
| AC-03 | set | Source ids are mandatory. |
| AC-04 | set | Deterministic gates win over AI recommendations. |
| AC-05 | set | Sensitive data exclusion is defined. |
| AC-06 | set | Timeout/unavailable/malformed fallback is defined. |
| AC-07 | set | Audit fields are required on outputs. |
| AC-08 | set | Draft order intents are non-executable. |
| AC-09 | set | Broker boundary follows no-order dry-run before KIS adapter approval. |
| AC-10 | set | Scheduled AI jobs are separated by role. |
| AC-11 | set | Tool-use disabled boundary is defined. |
| AC-12 | set | AI network disabled and zero-cost-cap defaults are defined. |

## 5. Follow-Ups

- Nonzero token/cost caps for actual AI network use require a future approved
  provider-pricing check.
- Exact prompt file paths are implementation details, but must use the job ids
  and `*/v0` schema names recorded here.
- Browser automation for ChatGPT Pro morning review remains a later
  implementation/runtime concern.
- The broader Ready-Set bundle is still not implementation-ready until the
  completion gate and final go-check queue are closed.

## 6. Result

UNIT-005 docs-only Set: PASS WITH FOLLOW-UPS

Implementation remains blocked at the bundle level because
`RUN-20260602_ready-set-architecture.md` still has `implementation_ready: false`.
