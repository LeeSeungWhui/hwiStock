---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-005
type: unit
domain: backend
name: AI orchestration layer
status: go_check_passed
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
work_class: product_api
completeness:
  status: go_check_passed
  audit_ref: docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md
owner: hwi
updated_at: 2026-06-06
last_verified_at: 2026-06-05
source_snapshot:
  input_digest: "AI API orchestration for news/disclosure/chart candidate synthesis"
  legacy_doc: none
  legacy_status: greenfield
source_inputs:
  - kind: user_prompt
    path_or_url: "단순 알고리즘이 아니라 ai api로 오케스트레이트"
    confidence: high
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-004
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  include:
    - backend/lib/ai_orchestration.py
    - backend/tests/test_ai_orchestration_layer.py
  exclude:
    - "**/*credentials*"
    - "**/*.env"
entrypoints: []
interfaces: []
verification:
  stage_skill_routes:
    ready:
      - hwi-work-harness
    set:
      - hwi-work-harness
    go:
      - hwi-work-harness
      - delegation-guard
    check:
      - hwi-work-harness
    prove:
      - hwi-work-harness
  required_gates:
    - ai-orchestration-smoke
    - ai-policy-gate-smoke
  suggested_gates:
    - risk-contract-check
    - credential-safety-check
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md
risk:
  tier: 3
  reasons:
    - AI output can be persuasive but wrong, stale, or hallucinated.
    - AI must not gain broker/order capability or override deterministic risk gates.
last_set:
  status: set
  report_id: RUN-20260602-unit-005-ai-orchestration-layer-set
  context_fingerprint:
evidence_refs:
  - docs/evidence/RUN-20260602_ai-orchestration-layer.md
  - docs/evidence/RUN-20260602_unit-005-ai-orchestration-layer-set.md
  - docs/evidence/RUN-20260605_unit-005-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md
  - docs/set/READY-SET-CORRECTION-20260606_mode-schedule-ai-loop-followup.md
  - docs/set/READY-SET-GPT-PRO-MORNING-PROMPT-20260606_hwistock.md
links:
  - HWISTOCK-MOD-004
operational_runtime_authority:
  superseded_by_module_ref: docs/modules/HWISTOCK-MOD-009_operational-automated-trading-program.md
  superseded_by_unit_ref: docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md
  note: UNIT-005 remains the AI safety foundation; operational Pro/Flash runtime and Flash trade-document contract are governed by UNIT-012.
---

# AI Orchestration Layer

## 1. Goal

Define a safe AI orchestration layer that can summarize, rank, and explain
news/disclosure/chart candidates, route the 07:15 GPT Pro morning watchlist when
scoped, and produce mode-aware daily reports while leaving all order eligibility
to deterministic policy and risk gates.

## 2. Baseline Module Contract

This unit implements `HWISTOCK-MOD-004` and updates safety expectations in
`HWISTOCK-MOD-001` and strategy expectations in `HWISTOCK-MOD-003`. It remains
docs-only until a future Go unit creates code.

## 3. Included Scope

- DeepSeek Pro / DeepSeek Flash / ChatGPT Pro role and approval policy.
- AI input bundle boundaries.
- Structured AI recommendation schema.
- Draft `order_intent` schema for recommendation-only trade intent.
- Output validation and source grounding.
- No-direct-order boundary.
- Deterministic risk/policy gate after AI output.
- Failure/fallback behavior.
- 24h hourly aggregate source/market analysis schedule.
- Market-regime/session analysis as a market-hours section of the hourly Pro
  artifact for the operational runtime.
- Flash 10-minute trade-document generation as the operational intraday artifact.
- 07:15 GPT morning-watchlist generation from prior-close/overnight analysis
  artifacts, requested by Codex CLI on the local desktop/workstation through
  local browser-use.
- GPT Pro morning review with fallback before the first Flash bucket for the
  active investment mode. SSH browser-use is forbidden for this route.
- Mode-aware daily close report using system-calculated PnL: paper/mock after
  15:30 KST, future live mode at 20:00 KST.
- Audit and operation evidence requirements.

## 4. Excluded Scope

- Changing selected AI provider/model direction without approval.
- Creating AI API keys or env files.
- Calling an AI API.
- Broker/order implementation.
- Routing to KIS/external broker endpoints or broker-provided broker-adapter/demo/testbed
  endpoints.
- Account-affecting operation.
- Profit expectation.

## 5. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | AI cannot directly place orders | No broker/order interface is reachable from AI output handler | architecture/code review | QA-001 |
| AC-02 | P0 | AI output is structured | Unknown action or malformed JSON is rejected | schema test | QA-002 |
| AC-03 | P0 | AI output is source-grounded | Missing or invented source ids are rejected | schema/source test | QA-003 |
| AC-04 | P0 | Deterministic gates win | Stop/capital/position/stale-data/kill-switch rejects override AI | policy test | QA-004 |
| AC-05 | P0 | Sensitive data is excluded | Credentials, account ids, and private account details are not sent to AI | data review | QA-005 |
| AC-06 | P1 | AI failure is safe | Timeout/unavailable/malformed AI produces reject/no-new-entry behavior | failure test | QA-006 |
| AC-07 | P1 | AI calls are auditable | Model, prompt/schema version, input bundle ids, latency, and output are logged | audit log | QA-007 |
| AC-08 | P0 | AI draft order intents are non-executable | Draft `order_intent` cannot bypass schema or deterministic policy gates | schema/policy test | QA-009 |
| AC-09 | P0 | Approved intents respect broker boundary | Before KIS adapter approval, policy-approved intent becomes no-order dry-run only; after approval it may target only the approved KIS KRX broker-adapter path | adapter test | QA-010 |
| AC-10 | P0 | Scheduled AI jobs are role-bounded | Pro hourly aggregate analysis, Flash 10-minute trade documents, 07:15 morning watchlist, and mode-aware daily close jobs have separate schemas/logs; market-regime/session analysis is inside the Pro hourly artifact for operational runtime | schedule/schema review | QA-011 |
| AC-11 | P0 | AI tool use is disabled first-pass | AI receives normalized bundles only and cannot browse, retrieve, or call tools directly | boundary/config review | QA-015 |
| AC-12 | P0 | AI network is disabled by default | Config defaults keep AI calls off and cost cap at 0 until explicit approval | config review | QA-016 |

## 6. Implementation Notes

- Use provider-specific schedules but keep schemas provider-agnostic enough to
  validate and audit outputs.
- Prefer normalized input bundles over raw crawled content.
- Treat AI output as a recommendation object, never as executable code.
- The only action that can proceed toward a buy review is `consider_entry`, and
  it still must pass deterministic risk gates.
- AI may produce a draft `order_intent`, but it remains recommendation-only until
  deterministic gates approve it.
- Before KIS adapter approval, the first approved execution sink is no-order
  dry-run only. It records decisions but does not simulate broker fills or fake
  balances. After approval, the first broker-backed sink is the approved KIS KRX
  broker-adapter path.
- If a future provider supports tool use, restrict tools to retrieval and
  summarization. Broker/order tools are forbidden.

## 7. Set Decisions

### 7.1 Job Registry

| job_id | schedule | model role | input schema | output schema | latency/cutoff |
| --- | --- | --- | --- | --- | --- |
| `deepseek_pro_hourly_market_analysis` | top of every hour, 24h | DeepSeek Pro | `pro_hourly_input_bundle/v0` | `pro_hourly_market_analysis/v0` | soft 10m, hard 20m |
| `deepseek_flash_10m_trade_document` | every 10 minutes during active investment-mode decision window | DeepSeek Flash | `flash_10m_input_bundle/v0` | `flash_trade_document/v0` | soft 2m, hard before next bucket |
| `gpt_morning_watchlist_0715` | 07:15 KST | local Codex CLI / local browser-use / ChatGPT Pro external reviewer when scoped; SSH browser-use forbidden | `overnight_analysis_bundle/v0` | `morning_watchlist/v0` or explicit `NO_TRADE` safe-block | hard before first Flash bucket |
| `daily_close_mode_aware` | paper after 15:30 KST; live 20:00 KST | DeepSeek Pro | `daily_close_bundle/v0` | `daily_close_report/v0` | soft 20m, hard before next operation day |

Late outputs are invalid for the decision cycle and may only be stored as
commentary/fallback evidence.

### 7.2 Output Schemas

First-pass output schemas:

- `ai_recommendation/v0`
- `pro_hourly_market_analysis/v0`
- `flash_trade_document/v0`
- `gpt_morning_prompt/v0`
- `morning_watchlist/v0` or explicit `NO_TRADE` safe-block artifact
- `daily_close_report/v0`

Every output must include `schema_version`, `job_id`, `model_role`,
`model_name`, `prompt_schema_version`, `input_bundle_ids`, `produced_at_kst`,
`source_ids`, `validation_status`, and `redaction_status`.

`ai_recommendation/v0` actions are limited to `watch`, `reject`,
`consider_entry`, `hold_review`, and `exit_review`. Unknown actions are rejected.
`draft_order_intent` remains non-executable and is rejected if it lacks risk
refs, uses stale data, references broker endpoints, asks for credit/margin, or
uses all-in sizing.

### 7.3 Tool / Retrieval Boundary

First-pass AI jobs receive only normalized input bundles. AI tool use is
disabled. Retrieval, crawling, source normalization, redaction, and
deduplication are owned by hwiStock ingestion/runtime code, not by the model.

### 7.4 Network / Cost Defaults

AI network use is disabled by default:

- `AI_NETWORK_ENABLED=false`
- `AI_DAILY_COST_CAP_KRW=0`
- `DEEPSEEK_PRO_ENABLED=false`
- `DEEPSEEK_FLASH_ENABLED=false`
- `CHATGPT_PRO_BROWSER_REVIEW_ENABLED=false`
- `GPT_PRO_MORNING_REVIEW_START_KST=07:15`

Nonzero token/cost caps require a future approved AI network/cost Set using
current provider pricing.

### 7.5 Fallback

- AI unavailable: no new AI-originated entry is unlocked.
- GPT Pro late/unavailable before the first Flash bucket for the active
  investment mode: write either a DeepSeek-derived `morning_watchlist/v0`
  artifact or an explicit `NO_TRADE` safe-block artifact and record fallback.
- Malformed, uncited, stale, low-confidence, or policy-violating output:
  rejected and logged.
- AI output can never bypass deterministic risk gates or broker-boundary gates.

## 8. Remaining Open Questions

- Exact nonzero token/cost caps for paid AI API calls require future current
  provider-pricing verification and explicit approval.
- Exact prompt file paths remain implementation details, but must use the
  `*/v0` schema names and job ids above.

## 9. Go-Check Summary

UNIT-005 passed current-tree rebaseline Go-Check on 2026-06-05 for the local
deterministic AI orchestration foundation in `backend/lib/ai_orchestration.py`
with focused coverage in `backend/tests/test_ai_orchestration_layer.py`.

Validated scope includes disabled-by-default AI network/provider/cost config,
job registry separation, structured `ai_recommendation/v0` validation, source
grounding, sensitive-payload review, draft order intent rejection, deterministic
UNIT-004 risk-gate handoff, no-order dry-run records, audit records, fallback
reports, daily-close system-PnL source checks, and tool-use-disabled behavior.

This Go-Check does not authorize AI provider calls, local browser-use execution,
nonzero AI cost caps, broker/KIS calls, adapter/account-affecting orders, fake
fills, fake balances, fake PnL, server start, DB work, or credential reads.
