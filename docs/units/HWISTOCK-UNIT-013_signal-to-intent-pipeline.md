---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-013
type: unit
domain: backend
name: Signal to paper intent pipeline
status: set
implementation_status: ready_for_go_check
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-05
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-007
code_paths:
  include:
    - backend/lib/market_intelligence.py
    - backend/lib/ai_orchestration.py
    - backend/lib/strategy_risk.py
    - backend/lib/trading_engine.py
    - backend/service/market_intelligence_ingestion.py
    - backend/service/kis_market_data_collector.py
    - backend/service/ai_analysis_runner.py
    - backend/tests/test_ai_orchestration_layer.py
    - backend/tests/test_strategy_risk_rulebook.py
    - backend/tests/test_trading_engine_order_state.py
  exclude:
    - "**/*.env"
    - backend/config.ini
    - frontend-web/config.ini
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-operational-paper-trading-program.md
  - docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md
---

# Signal To Paper Intent Pipeline

## 1. Goal

Create the missing bridge between real-time source collection, KIS intraday
market data, DeepSeek Flash trade documents, and the KIS paper runner.

Current Go status: ready for Go-Check after `HWISTOCK-UNIT-016` closed the
runtime data/execution contracts for schemas, artifact manifests, idempotency
keys, freshness TTLs, reservation accounting, and portfolio/order-state conflict
reject codes.

The program must be able to generate paper order intents from newly written
trade documents without relying on a human-written intent file for every test.
The intent still must be source-grounded, KIS-market-data-confirmed,
session-confirmed, portfolio/order-state-compatible, risk-checked, and non-live.

Source-authority correction: `docs/sources/HWISTOCK-SOURCE-REGISTRY.md` now
splits public 24-hour market-intelligence sources from KIS paper-read market
data. UNIT-013 may perform only KIS paper/mock **market-data reads** needed for
signal confirmation and snapshot artifacts. UNIT-013 must not call KIS order,
cancel, balance-changing, or live endpoints.

## 2. Included Scope

- Build a trade-action pipeline from:
  - normalized disclosure/news events;
  - KIS intraday WebSocket snapshots for realtime trade price/orderbook where
    paper-supported;
  - KIS REST ranking/analysis snapshots refreshed every 1-3 minutes, including
    volume rank, volume power, fluctuation rank, and program-trading aggregate
    status where the capability matrix proves support;
  - DeepSeek Pro hourly aggregate/market-regime artifacts;
  - DeepSeek Flash `flash_trade_document/v0` artifacts;
  - previous trade-document chain and current portfolio/order-state snapshots;
  - approved symbol mapping sources such as DART stock codes or approved KRX/KIS
    symbol master data;
  - approved quote/chart/market features available in the paper runtime.
- Implement or wire the KIS intraday market-data collector for:
  - `inquire-price`;
  - `inquire-time-itemchartprice`;
  - `inquire-time-itemconclusion`;
  - `volume-rank`;
  - `ranking/fluctuation`;
  - `ranking/volume-power`;
  - program-trading aggregate status where paper-supported;
  - `ranking/top-interest-stock`;
  - KRX realtime trade price/orderbook subscription contracts where supported.
  Unsupported NXT/SOR/integrated broker-facing market-data branches must produce
  disabled/fallback evidence and cannot be treated as paper-proven.
- Produce deterministic `condition_card/v0` and `compiled_watch/v0` records.
- Produce `paper_order_intent/v0` only when:
  - all input artifacts are schema-valid and manifest/hash complete;
  - source ids are grounded;
  - KIS market-data confirmation is fresh;
  - current holdings, pending orders, open exits, cooldowns, and prior
    still-valid trade decisions do not conflict;
  - reservation accounting shows cash reserve and holding slots remain safe
    under worst-case pending-order fills;
  - calendar/session route is valid;
  - Flash action fields are valid: `WAIT_BUY`, `BUY_NOW`, `HOLD`, `SELL`, and
    `NO_TRADE`, including validity/cancel windows, entry zone, take-profit,
    stop-loss, trailing-stop percent, position-size cap, and action reason;
  - AI invalidation/stop notes are present;
  - deterministic strategy/risk gates pass;
  - live endpoint, margin, all-in, fake broker, and stale-data checks pass.
- Write the intent queue to a durable data path consumed by UNIT-014.
- Persist rejected actions with reasons so the dashboard and daily report can
  explain why no trade happened.
- Persist conflict decisions such as `already_holding_symbol`,
  `pending_order_exists`, `active_exit_order_exists`,
  `prior_trade_document_still_valid`, `cooldown_active`, and
  `scale_in_not_authorized`.

## 3. Excluded Scope

- Direct KIS order calls.
- KIS cancel/modify/order submission calls, even when paper/mock credentials are
  present.
- Live trading.
- Fake fills/balances/PnL.
- News-only automatic orders.
- AI-only orders.
- Strategy-risk parameter changes.
- Broad unapproved scraping or unofficial data sources.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result |
| --- | --- | --- | --- |
| AC-01 | P0 | KIS intraday market-data collector exists | Collector writes sanitized KIS price/ranking/realtime snapshot artifacts or classified safe blocks. |
| AC-02 | P0 | Source-grounded actions exist | Action records include source ids and reject invented/empty ids. |
| AC-03 | P0 | Symbol resolution is auditable | Corp/name-to-symbol mapping records the source and rejects ambiguous mappings. |
| AC-04 | P0 | News-only cannot order | Event-only actions become watch records until KIS market/session confirmation passes. |
| AC-05 | P0 | AI cannot unlock orders alone | Flash trade documents require deterministic validation and cannot call KIS order endpoints. |
| AC-06 | P0 | Risk gates run before intent queue | Cash reserve, holdings cap, stop/invalidation, stale-data, kill-switch, and calendar gates block unsafe intents. |
| AC-07 | P0 | Intent queue is idempotent | Re-running the pipeline does not duplicate the same active intent. |
| AC-08 | P0 | Rejections are visible | Rejected actions write machine-readable block reasons. |
| AC-09 | P0 | Portfolio conflicts are blocked | Held symbols, pending orders, active exits, cooldowns, and prior valid trade-doc decisions block conflicting new intents unless a scale-in/exit action is explicitly permitted by deterministic rules. |
| AC-10 | P0 | UNIT-016 contracts are applied | Intent generation consumes only schema-valid, manifest-complete, fresh, idempotent, reservation-safe artifacts defined by UNIT-016. |
| AC-11 | P0 | Pending waits are superseded safely | A new accepted trade document cancels prior unfilled `WAIT_BUY` orders unless renewed explicitly and still gate-valid. |
| AC-12 | P0 | UNIT-013 is paper-read only | KIS order/cancel/modify endpoints are not called by this unit; unsupported NXT/SOR broker-facing branches write disabled/fallback evidence. |

## 5. Go Notes

This is the unit that makes the system a trading program instead of a status
runner. UNIT-014 must not be asked to invent trades; it consumes approved
`paper_order_intent/v0` rows derived from Flash trade-document actions and KIS market
data in this unit. The executor is still required to re-check portfolio/order
state immediately before broker submission because holdings and open orders can
change after Flash writes the document.

If portfolio or order-state refs are missing, unavailable, stale, or only
advisory, this unit may write watch/reject records but must not produce a clean
entry `paper_order_intent/v0`.
