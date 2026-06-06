---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-012
type: unit
domain: backend
name: AI analysis runtime
status: go_check_local_passed
implementation_status: go_check_passed_local_no_network_provider_smoke_blocked
post_pro_reinforcement_status: corrective_gap_recorded
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-06
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-003
code_paths:
  include:
    - backend/lib/ai_orchestration.py
    - backend/lib/ai_analysis_runtime.py
    - backend/service/ai_analysis_runner.py
    - backend/lib/market_intelligence_ingestion_runtime.py
    - backend/service/market_intelligence_ingestion.py
    - backend/tests/test_ai_orchestration_layer.py
    - ops/systemd/user/hwistock-ai-analysis.service
    - ops/systemd/user/hwistock-ai-analysis.timer
  exclude:
    - "**/*.env"
    - backend/config.ini
    - frontend-web/config.ini
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-012_ai-analysis-runtime.md
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-operational-automated-trading-program.md
  - docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md
  - docs/evidence/RUN-20260605_operational-go-check-units-012-015.md
external_refs:
  - https://api-docs.deepseek.com/
  - https://api-docs.deepseek.com/api/list-models
---

# AI Analysis Runtime

> Post-Pro corrective note (2026-06-05): local artifacts and timer activity are
> not enough. This unit must reconcile actual Pro/Flash timers, provider-backed
> versus safe-block outputs, and readiness wording before it can support a
> operation observation claim.

## 1. Goal

Make the AI layer an actual scheduled analysis pipeline for the trading program,
not a vague description and not a fake order brain.

Current Go status: local no-network Go-Check passed on 2026-06-05. Provider
network smoke remains blocked until explicitly scoped and approved. This does
not make the whole trading program operation-ready.

The current contract is:

- DeepSeek Pro: top-of-hour aggregate analysis across 24 hours.
- DeepSeek Pro: during market hours, include market-regime/session analysis in
  the same hourly Pro artifact instead of running it as a detached subsystem.
- DeepSeek Flash: every 10 minutes during market hours, read the latest Pro
  file, the recent 10-minute NAVER news/OpenDART disclosure window, KIS REST
  ranking changes, current KIS realtime trade/orderbook snapshots, the
  deterministic candidate universe, and risk context. It must also read the
  previous trade-document chain and/or current portfolio/order-state snapshot so
  actions do not conflict with held positions, pending orders, active
  stop/take-profit exits, cooldowns, or still-valid prior decisions. It then
  writes at most one finalized trade document for that 10-minute decision bucket
  and writes a `NO_TRADE` sentinel artifact when the tick is invalid,
  unavailable, malformed, or off-session. A valid trade document contains at
  most five symbol actions.
- ChatGPT Pro: optional 07:00 external morning review through browser
  automation when available before cutoff.

AI output remains non-executable. The deterministic strategy/risk/order layers
own all broker-order eligibility.

## 2. Included Scope

- Replace placeholder or stale model defaults with current official DeepSeek
  API model ids:
  - `deepseek-v4-pro`
  - `deepseek-v4-flash`
- Support `thinking` and `reasoning_effort` config only where the provider
  accepts it.
- Split AI jobs into distinct artifacts:
  - `pro_hourly_market_analysis/v0`
  - `flash_trade_document/v0`
  - `gpt_morning_prompt/v0`
  - `morning_review_report/v0`
  - `daily_close_report/v0`
- `flash_trade_document/v0` is one document per Flash 10-minute decision tick.
  Its `actions` list must contain at most five symbols. For each action it must
  provide ticker/name, one of `WAIT_BUY`, `BUY_NOW`, `HOLD`, `SELL`, or
  `NO_TRADE`, entry zone if relevant, take-profit, stop-loss, trailing-stop
  percent, cancel-if-not-filled window, position-size cap, source refs, KIS
  market-data refs, confidence/risk notes, portfolio-conflict status, and
  explicit adapter-only/no-adapter-order metadata.
- Flash must not invent ticker candidates. Its executable action universe is the
  deterministic `compiled_watch/v0` input created from NAVER/OpenDART events,
  the mode-enabled KIS signal collector inputs, symbol mapping,
  freshness/session filters, and strategy/risk prefilters. Off-universe symbols
  become reject/watch records or a `NO_TRADE` safe block; they cannot become
  order intents.
- Flash input must include at least one portfolio-consistency source:
  - previous `flash_trade_document/v0` chain with active/expired trade-action
    status; or
  - current portfolio/order-state snapshot with holdings, pending orders,
    active exits, cooldowns, cash/reserve state, and position locks.
  Prefer both when available.
- Enforce source ids, redaction status, prompt/schema versions, latency/cutoff,
  and no-order boundaries.
- Keep AI provider keys external under `/home/hwi/.config/hwistock/deepseek.env`.
- Make the scheduled service fail closed when keys are missing, sources are
  absent, provider errors occur, or outputs are malformed.

## 3. Excluded Scope

- AI order placement.
- Sending broker credentials, account values, or private account details to AI.
- Enabling nonzero AI cost caps without explicit approval.
- Browser automation for ChatGPT Pro unless the Go/Prove route explicitly
  scopes browser side effects.
- Profit guarantees or investment advice claims.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result |
| --- | --- | --- | --- |
| AC-01 | P0 | Official DeepSeek model ids are used | Service/config/tests reject `moonbridge` or deprecated aliases as default runtime models. |
| AC-02 | P0 | Hourly Pro aggregate job exists | A top-of-hour tick writes source-grounded `pro_hourly_market_analysis/v0` or a classified safe block. |
| AC-03 | P0 | Pro market-regime analysis is integrated | During market hours the Pro artifact includes market-regime/session analysis in the same file; no detached market-regime subsystem is required. |
| AC-04 | P0 | Flash 10-minute trade document exists | During market hours Flash writes `flash_trade_document/v0` every 10 minutes or safe-blocks; actions are capped at five symbols and include entry/take-profit/stop-loss/trailing/cancel windows where relevant. |
| AC-05 | P0 | AI outputs are non-executable | No AI artifact can directly invoke broker/order code or bypass deterministic risk gates. |
| AC-06 | P0 | Secrets and copyrighted bodies are excluded | AI input payload review rejects credentials, account ids, and unapproved full article bodies. |
| AC-07 | P0 | Missing provider/key is safe | Missing key or provider failure records a safe block and does not unlock new entries. |
| AC-08 | P0 | Flash is portfolio-aware | Flash input includes previous trade-document and/or portfolio/order-state context, and output marks conflicts instead of proposing duplicate/conflicting entries. |
| AC-09 | P0 | Flash candidate universe is deterministic | Flash can only score/select symbols from a prebuilt `compiled_watch/v0`; off-universe tickers are rejected and cannot produce order intents. |

## 5. Go Notes

The current `hwistock-ai-analysis.service` / timer shape must be reviewed
because a single hourly analysis tick is not enough for the rebaselined runtime.
This unit should make the runtime match the profile:

- DeepSeek Pro hourly artifact by official model id;
- DeepSeek Flash 10-minute trade-document artifact by official model id;
- separate schedule/command paths for Pro and Flash;
- `NO_TRADE` safe blocks when source, provider, schema, freshness, or session
  gates fail;
- ChatGPT Pro as a separate optional browser review path, not part of the
  always-on runtime loop.
