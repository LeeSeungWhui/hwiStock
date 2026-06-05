---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-004
type: module
domain: backend
name: AI orchestration layer
spec_status: set
build_status: go_check_passed
verification_status: go_check_passed
ready_set_rebaseline_status: go_check_passed
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
completeness:
  status: go_check_passed
  audit_ref: docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md
owner: hwi
updated_at: 2026-06-05
last_verified_at: 2026-06-05
source_inputs:
  - kind: user_prompt
    path_or_url: "단순 알고리즘이 아니라 ai api로 오케스트레이트"
    confidence: high
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  - backend/lib/ai_orchestration.py
  - backend/tests/test_ai_orchestration_layer.py
entrypoints: []
interfaces: []
links:
  - PROFILE-HWISTOCK
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-003
operational_runtime_authority:
  superseded_by_module_ref: docs/modules/HWISTOCK-MOD-009_operational-paper-trading-program.md
  superseded_by_unit_ref: docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md
  note: UNIT-005/MOD-004 remain the safety foundation; operational Pro/Flash scheduling and trade-document schemas are governed by MOD-009/UNIT-012.
---

# AI Orchestration Layer

## 1. Purpose

This module defines how `hwiStock` may use an AI API to orchestrate market
information, chart context, candidate ranking, and paper-run review. AI is an
analysis/orchestration layer, not a broker, not a risk engine, and not an order
router. AI may propose a draft `order_intent`, but that object is not executable
unless deterministic policy gates approve it and the active broker boundary is
explicitly approved. Before KIS paper approval, approved intents are recorded
only as no-order dry-run decisions.

## 2. User Value / Representative Scenarios

- As the owner, I can have AI summarize why a symbol is interesting from news,
  disclosure, and chart context.
- As a reviewer, I can inspect the exact sources and model output behind a
  candidate recommendation.
- As an operator, I can disable AI without unlocking unsafe trading behavior.
- As a paper-run reviewer, I can compare AI explanations with actual outcomes
  without treating them as proof of profitability.

## 3. Scope

### Included

- AI API provider/model selection policy.
- Selected planning model roles: DeepSeek Pro, DeepSeek Flash, and ChatGPT Pro
  morning review.
- Structured AI output schema.
- Draft `order_intent` schema for recommendation-only buy/sell intent.
- Source-grounded candidate synthesis.
- Candidate ranking and explanation.
- Paper/backtest review summaries.
- AI call audit logs: model, prompt/schema version, source ids, latency, and
  validation status.
- Deterministic policy gate after AI output.
- Fallback behavior when AI is unavailable, slow, malformed, or low-confidence.

### Excluded

- Direct broker API calls from AI.
- Direct order placement from AI.
- Routing approved intents to KIS or any other broker network endpoint before an
  explicitly approved KIS paper unit.
- AI override of cash-reserve floor, stop-loss, holdings cap, kill switch, or stale-data
  gates.
- Sending credentials, account identifiers, private account details, or
  unapproved copyrighted article bodies to an AI API.
- Profit guarantee or investment advice claims.

## 4. Product / Capability Contract

### 4.1 Allowed AI Roles

AI may:

- classify news/disclosure/chart context
- summarize event impact hypotheses
- rank watchlist candidates
- explain why a candidate should be watched or rejected
- propose `consider_entry` for deterministic review
- propose a non-executable draft `order_intent` for deterministic review
- flag `exit_review` or `hold_review` for operator/risk review
- summarize paper/backtest results after the fact
- generate 06:50 GPT Pro morning-review prompt from overnight analysis artifacts
- generate 20:00 daily close analysis from system-calculated PnL and trade logs

AI may not:

- call broker/order interfaces
- calculate final order quantity without risk-engine validation
- override a hard stop, kill switch, cash-reserve/holdings cap, or stale-data block
- invent source ids or facts not present in the input bundle
- trade when data is stale, missing, or malformed

### 4.2 Execution Boundary

The default flow is:

1. `market_intelligence` collects approved news/disclosure/chart data.
2. DeepSeek Pro produces scheduled news/disclosure/market analysis artifacts.
3. Normalizer builds a `signal_bundle` or morning/daily report bundle with
   source ids and raw market features.
4. AI orchestrator returns a structured `ai_recommendation`, report, or
   candidate-card draft.
5. Schema validator rejects malformed, uncited, stale, or low-confidence output.
6. Deterministic policy gate applies cash-reserve floor, stop-loss, holdings cap,
   stale-data, and kill-switch rules.
7. Before KIS paper approval, approved intent may only be recorded as a no-order
   dry-run decision without simulated fills or balances.
8. After KIS paper approval, the first broker-backed path is KIS KRX
   paper/mock-investment only; KIS live and external broker endpoints remain
   unreachable until a later approved broker-integration unit verifies official
   docs and endpoint modes.

AI output never skips step 4 or step 5.

### 4.2-1 Model Schedule / Roles

- DeepSeek Pro hourly aggregate analysis: runs 24 hours, delta-only,
  source-grounded, and stores hourly artifacts.
- DeepSeek Pro market-regime/session analysis: during market hours this is a
  section inside the hourly Pro artifact, not a detached operational subsystem.
- 06:50 aggregator: combines overnight hourly analysis artifacts into a GPT Pro
  prompt. It must not reprocess all raw news when existing analysis artifacts
  are sufficient.
- 07:00 ChatGPT Pro morning review: external web-session reviewer that ranks
  08:00 watchlist candidates, themes, risks, and invalidation conditions. If it
  misses the configured cutoff, the system falls back to the DeepSeek-only
  morning report.
- DeepSeek Flash minute trade document: during market hours, reads latest Pro
  analysis, new news/disclosures, KIS price/ranking/realtime snapshots, previous
  trade documents and/or current portfolio/order-state snapshots, then writes
  one `flash_trade_document/v0` for the minute. It does not decide final orders.
- 20:00 daily close report: uses system-calculated profit, loss, net PnL,
  fees/taxes when available, trade logs, AI candidate results, and market/news
  context. AI explains; the system calculates numbers.

### 4.2-2 Job Registry Contract

The first job registry is schedule-driven and source-bundle-driven. AI models do
not crawl, retrieve, or call broker tools in the first implementation.

| job_id | schedule | model role | input schema | output schema | latency/cutoff |
| --- | --- | --- | --- | --- | --- |
| `deepseek_pro_hourly_market_analysis` | top of every hour, 24h | DeepSeek Pro | `pro_hourly_input_bundle/v0` | `pro_hourly_market_analysis/v0` | soft 10m, hard 20m |
| `deepseek_flash_minute_trade_document` | every minute during market hours | DeepSeek Flash | `flash_minute_input_bundle/v0` | `flash_trade_document/v0` | soft 15s, hard 30s |
| `gpt_prompt_0650` | 06:50 KST | local orchestrator / DeepSeek Pro summary artifacts | `overnight_analysis_bundle/v0` | `gpt_morning_prompt/v0` | hard 07:00 |
| `chatgpt_pro_morning_review` | 07:00 KST | ChatGPT Pro external reviewer | `gpt_morning_prompt/v0` | `morning_review_report/v0` | hard 07:20 |
| `daily_close_2000` | 20:00 KST | DeepSeek Pro | `daily_close_bundle/v0` | `daily_close_report/v0` | soft 20m, hard 21:00 |

If a job misses its hard cutoff, the result is invalid for that cycle. Late
outputs may be stored as commentary but cannot unlock entries or overwrite
already-published decision evidence.

### 4.3 Structured Output Contract

All AI outputs are JSON documents with `schema_version`, `job_id`,
`model_role`, `model_name`, `prompt_schema_version`, `input_bundle_ids`,
`produced_at_kst`, `source_ids`, `validation_status`, and `redaction_status`.

`ai_recommendation/v0` includes:

- `recommendation_id`
- `action`: `watch`, `reject`, `consider_entry`, `hold_review`, or `exit_review`
- `candidate_id`
- `symbol`
- `source_path`: `event_first`, `chart_first`, or `combined`
- `source_ids`
- `chart_interval`
- `thesis`
- `risk_notes`
- `confidence`: `low`, `medium`, or `high`
- `missing_inputs`
- optional `draft_order_intent`: symbol, side, venue hint, max cash, max shares,
  limit/market intent, expiry timestamp, and risk reference id
- `model`
- `prompt_schema_version`
- `valid_for_minutes` when used for intraday candidate labels

`pro_hourly_market_analysis/v0` includes: theme summaries, affected symbols,
disclosure/news source ids, KIS market-data refs, risk notes, novelty/dedup
flags, `next_watch` candidates, and during market hours a market-regime/session
section. It cannot include executable order fields.

`flash_trade_document/v0` is one document per Flash minute tick. Its
`candidates` list contains at most five symbols. Each candidate includes entry
price/rule, take-profit, stop-loss, sizing/cash cap, validity window, source
refs, KIS market-data refs, portfolio-conflict status, and risk notes.

`gpt_morning_prompt/v0` includes: overnight analysis digest, source ids, themes,
candidate list, questions for GPT Pro, and explicit forbidden actions.

`morning_review_report/v0` includes: ranked watchlist, reasons, risk notes,
invalidation conditions, missing data, and no-order disclaimer.

`daily_close_report/v0` includes: system-calculated PnL references, trade/result
summaries, AI interpretation, failure notes, and next-day watch themes. AI does
not calculate PnL numbers.

Any unknown action is rejected.
`draft_order_intent` is also rejected if it references live broker endpoints,
credit/margin, all-in sizing, stale source data, or a missing risk reference.

### 4.4 Fallback Policy

- AI API unavailable: do not unlock new AI-originated live/paper entries. Record
  `ai_unavailable` and keep candidates watchlist-only unless a later unit
  explicitly approves a deterministic non-AI entry path.
- GPT Pro morning review unavailable or late: use DeepSeek-only morning report
  and record fallback reason. GPT Pro hard cutoff is 07:20 KST.
- AI output malformed: reject the recommendation.
- AI output lacks source ids: reject the recommendation.
- AI latency exceeds the configured budget: reject for that decision cycle.
- AI contradicts hard risk rules: deterministic risk gate wins.
- AI suggests all-in, credit/margin, overnight holding, or bypassing
  cash-reserve/holdings checks, stop-loss, or stale-data:
  reject and log policy violation.
- AI suggests broker paper/mock/demo/testbed or live endpoint routing before the
  approved KIS integration unit: reject and log policy violation.

### 4.5 Tool / Retrieval Policy

First-pass AI jobs receive only normalized input bundles prepared by hwiStock.
AI tool use is disabled. Retrieval, crawling, API collection, source
normalization, redaction, and deduplication are owned by the ingestion/runtime
system, not by the model.

Allowed model input:

- source ids
- source metadata
- permitted excerpts/summaries
- chart/market features produced by approved data sources
- system-calculated PnL/trade summaries
- prior stored AI analysis artifacts

Forbidden model input:

- broker credentials
- account ids or account balances not explicitly redacted for reporting
- unapproved full article bodies
- raw secrets or env values
- executable broker/order tool handles

### 4.6 Budget / Network Defaults

AI network use remains disabled until explicit approval. First implementation
may build schemas, validators, prompt registries, audit logs, and dry-run
fixtures without calling an AI API.

Default config values:

- `AI_NETWORK_ENABLED=false`
- `AI_DAILY_COST_CAP_KRW=0`
- `DEEPSEEK_PRO_ENABLED=false`
- `DEEPSEEK_FLASH_ENABLED=false`
- `CHATGPT_PRO_BROWSER_REVIEW_ENABLED=false`
- `GPT_PRO_MORNING_REVIEW_CUTOFF_KST=07:20`

Before enabling real AI network calls, a future Set/Go unit must set nonzero
cost and token caps from current provider pricing and record approval evidence.

## 5. Interfaces

No code interfaces exist yet.

Future interfaces may include:

- AI provider adapter
- DeepSeek Pro adapter
- DeepSeek Flash adapter
- ChatGPT Pro browser-automation adapter
- prompt/schema registry
- signal bundle builder
- AI output validator
- recommendation store
- order intent validator
- policy gate adapter
- no-order dry-run recorder
- KIS paper adapter boundary
- paper-run review summarizer
- daily close report builder
- morning GPT prompt builder

## 6. State / Data / Permission Rules

- DeepSeek Pro, DeepSeek Flash, and ChatGPT Pro morning-review direction is
  selected for planning. Final prompt/schema/cost limits and any live AI network
  use still require explicit approval.
- AI API calls require explicit approval before network use.
- Prompt, schema, tool permissions, and fallback changes require docs updates.
- Do not send secrets, broker credentials, account identifiers, or private
  account details to AI.
- Do not send full copyrighted article bodies unless the source policy permits
  it. Prefer metadata, short summaries, and source ids.
- All AI decisions must be reproducible from stored input bundle ids and output
  records.

## 7. Existing Assets / Reuse Points

- `HWISTOCK-MOD-002`: source and chart context ingestion.
- `HWISTOCK-MOD-003`: deterministic signal/risk rulebook.
- `HWISTOCK-MOD-001`: safety core and live-operation gates.

## 8. Module-Level Verification

- Verify AI cannot call broker/order interfaces.
- Verify malformed or uncited AI output is rejected.
- Verify deterministic risk gate wins over AI recommendations.
- Verify AI audit logs include model, prompt/schema version, input bundle ids,
  latency, validation result, and action.
- Verify paper evidence separates AI hypothesis from actual outcome.

## 9. Included Units

- `HWISTOCK-UNIT-005`: AI orchestration foundation implementation and
  safety-gate contract.
- `HWISTOCK-UNIT-006`: trading engine/order state consumes validated candidate
  cards but never raw executable AI instructions.
- `HWISTOCK-UNIT-008`: data/evidence storage persists AI analysis artifacts,
  morning reports, and daily close reports.

## 10. Decisions / Open Contract Questions

- Decision: AI API orchestration is allowed only as analysis/recommendation.
- Decision: AI cannot directly place orders or override deterministic gates.
- Decision: AI output must be structured and source-grounded.
- Decision: AI may propose draft `order_intent`, but only deterministic gates can
  approve it.
- Decision: internal fake broker execution is not used. Before KIS paper
  approval, approved intents are no-order dry-run records only; KIS and external
  broker endpoints are forbidden until a later approved unit.
- Decision: DeepSeek Pro is the hourly aggregate source/market analyst; during
  market hours the same artifact includes market-regime/session analysis.
- Decision: DeepSeek Flash writes one market-minute trade document whose
  candidates list contains at most five symbols and is aware of prior trade
  documents and/or current portfolio/order state.
- Decision: ChatGPT Pro is the 07:00 morning external reviewer through browser
  automation when available before cutoff.
- Decision: 20:00 daily close report includes system-calculated PnL and AI
  interpretation.
- Decision: official broker paper/mock API use is deferred pending KIS API
  portal verification and explicit approval.
- Decision: first-pass AI schemas are versioned as `*/v0`, with a job registry
  and prompt schema version on every output.
- Decision: AI tool use is disabled; models receive normalized bundles only.
- Decision: AI network is disabled by default and has a KRW cap of 0 until a
  future approved network/cost unit sets nonzero caps from current pricing.
- Decision: GPT Pro morning review hard cutoff is 07:20 KST.
- Decision: AI failure does not unlock new AI-originated entries; late or
  malformed output is stored only as rejected/fallback commentary.
- Open: exact nonzero token/cost caps for live AI API calls require future
  provider-pricing verification and explicit approval.

## 11. Evidence References

- `docs/evidence/RUN-20260602_ai-orchestration-layer.md`
- `docs/evidence/RUN-20260605_unit-005-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md`
- `docs/evidence/RUN-20260602_unit-005-ai-orchestration-layer-set.md`

## 12. Design References

- None.
