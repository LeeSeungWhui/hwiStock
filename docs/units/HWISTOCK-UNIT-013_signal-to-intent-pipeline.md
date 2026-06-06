---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-013
type: unit
domain: backend
name: Signal to order intent pipeline
status: go_check_local_passed
implementation_status: go_check_passed_local_no_network_kis_adapter_read_blocked
post_pro_reinforcement_status: corrective_gap_recorded
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-06
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
    - backend/lib/market_intelligence_ingestion_runtime.py
    - backend/lib/ai_orchestration.py
    - backend/lib/strategy_risk.py
    - backend/lib/trading_engine.py
    - backend/lib/kis_market_data_runtime.py
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
  - docs/evidence/RUN-20260605_ready-set-operational-automated-trading-program.md
  - docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md
  - docs/evidence/RUN-20260605_owner-selected-naver-kis6-scope.md
  - docs/evidence/RUN-20260605_operational-go-check-units-012-015.md
  - docs/evidence/RUN-20260606_kis-mode-gated-account-truth-go-check.md
---

# Signal To Order Intent Pipeline

> Post-Pro corrective note (2026-06-06): this unit must prove source/calendar
> and KIS mode-aware market-data freshness/readiness without order submission
> before any trade document can be treated as order-intent eligible.

## 1. Goal

Create the missing bridge between real-time source collection, KIS intraday
market data, DeepSeek Flash trade documents, and the KIS broker adapter runner.

Current Go status: local no-network Go-Check has been rebaselined for the
owner-selected NAVER/OpenDART + KIS mode-aware market-data scope. KIS
broker-adapter read network transport smoke remains separately scoped and must
not be confused with order readiness.

The program must be able to generate broker order intents from newly written
trade documents without relying on a human-written intent file for every test.
The intent still must be source-grounded, KIS-market-data-confirmed,
session-confirmed, portfolio/order-state-compatible, risk-checked, and adapter-validated.

Source-authority correction: `docs/sources/HWISTOCK-SOURCE-REGISTRY.md` now
splits public 24-hour market-intelligence sources from KIS broker adapter-read market
data. UNIT-013 may perform only KIS broker-adapter **market-data reads** needed for
signal confirmation and snapshot artifacts. UNIT-013 must not call KIS order,
cancel, balance-changing, or unapproved endpoints.

## 2. Included Scope

- Build a trade-action pipeline from:
  - normalized OpenDART disclosure events and NAVER Search News API events;
  - KIS intraday WebSocket snapshots for realtime trade price/orderbook where
    adapter-supported;
  - KIS REST ranking/analysis snapshots refreshed every 1-3 minutes, including
    volume rank, volume power, fluctuation rank, and program-trading aggregate
    status where the capability matrix proves support;
  - DeepSeek Pro hourly aggregate/market-regime artifacts;
  - DeepSeek Flash `flash_trade_document/v0` artifacts;
  - previous trade-document chain and current portfolio/order-state snapshots;
  - approved symbol mapping sources such as DART stock codes or approved KRX/KIS
    symbol master data;
  - deterministic candidate-universe artifacts built before Flash runs.
- Implement or wire the KIS intraday market-data collector for the mode-aware
  first-scope adapter-read inputs:
  - paper/mock mode: KRX realtime trade price/orderbook/market-operation
    WebSocket, integrated realtime trade price/orderbook/market-operation
    WebSocket, and the REST inputs below;
  - real investment mode: all paper/mock inputs plus NXT realtime trade
    price/orderbook/market-operation WebSocket;
  - REST `volume-rank`;
  - REST `ranking/volume-power` or equivalent execution-strength upper-rank
    endpoint;
  - REST `ranking/fluctuation`;
  - REST program-trading aggregate status where adapter-supported.
  NXT signal inputs must be rejected in paper/mock mode and enabled only in real
  investment mode. SOR broker-facing market-data branches remain disabled unless
  a future approved contract adds them.
- Produce deterministic `condition_card/v0` and `compiled_watch/v0` records.
- `compiled_watch/v0` is the deterministic candidate universe. Flash may score,
  rank, reject, or explain only symbols already present in that universe. If
  Flash outputs a ticker outside the compiled universe, the action is rejected
  and cannot produce `paper_order_intent/v0`.
- Produce `paper_order_intent/v0` only when:
  - all input artifacts are schema-valid and manifest/hash complete;
  - source ids are grounded;
  - KIS market-data confirmation is fresh;
  - the final intent artifact itself records `flash_trade_document_ref`,
    `source_refs`, `market_data_refs`, `portfolio_snapshot_ref`,
    `order_state_snapshot_ref`, and `authoritative_refs_verified_at_kst`;
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
  - unapproved endpoint, margin, all-in, fake broker, and stale-data checks pass.
- Write the intent queue to a durable data path consumed by UNIT-014.
- Persist rejected actions with reasons so the dashboard and daily report can
  explain why no trade happened.
- Persist conflict decisions such as `already_holding_symbol`,
  `pending_order_exists`, `active_exit_order_exists`,
  `prior_trade_document_still_valid`, `cooldown_active`, and
  `scale_in_not_authorized`.

## 3. Excluded Scope

- Direct KIS order calls.
- KIS cancel/modify/order submission calls, even when broker-adapter credentials are
  present.
- KIS signal inputs outside the mode-aware UNIT-013 scope, including intraday
  bars, intraday executions, top-interest stocks, balances, buyable cash,
  sellable quantity, cancelable-order lookup, or order helper APIs. Fill notices,
  balances, buyable/sellable cash, cancelable-order lookup, and order/fill
  reconciliation belong to UNIT-014 broker execution/account truth, not the
  market-signal collector.
- Unapproved adapter operation.
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
| AC-12 | P0 | UNIT-013 is adapter-read only | KIS order/cancel/modify endpoints are not called by this unit; unsupported NXT/SOR broker-facing branches write disabled/fallback evidence. |
| AC-13 | P0 | Flash cannot invent candidate symbols | A Flash action whose ticker is absent from deterministic `compiled_watch/v0` is rejected and produces no order intent. |
| AC-14 | P0 | KIS signal collector is mode-gated | UNIT-013 attempts only the mode-enabled KRX/integrated/NXT realtime market-data inputs plus approved REST rank/program-trading inputs; paper/mock mode rejects NXT inputs, real investment mode enables NXT inputs, and any KIS order/cancel/modify endpoint remains safe-blocked. |

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

If source, KIS market-data, Flash trade-document, portfolio, or order-state refs
are present only on the parent Flash document but absent from the final
`paper_order_intent/v0`, the intent is invalid and must be rejected before
UNIT-014 can consume it.
