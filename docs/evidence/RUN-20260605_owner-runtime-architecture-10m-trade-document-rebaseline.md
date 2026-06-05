---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-owner-runtime-architecture-10m-trade-document-rebaseline
type: evidence
stage: ready-set
status: architecture_rebaseline_recorded
project_root: /data/workspace/My/hwiStock
docs_base: docs
current_authority: true
created_at: 2026-06-05
updated_at: 2026-06-05
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
module_ref: docs/modules/HWISTOCK-MOD-009_operational-paper-trading-program.md
ready_set_ref: docs/set/READY-SET-COMPLETION-20260605_operational-paper-trading-program_hwistock.md
contract_ref: docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md
schema_catalog_ref: docs/contracts/hwistock-runtime-contracts.schema.json
supersedes:
  - docs/evidence/RUN-20260605_owner-runtime-architecture-clarification.md
---

# Owner Runtime Architecture Rebaseline — 10-Minute Trade Document Loop

## 1. Owner-Approved Runtime Shape

The owner rebaselined the operational paper-trading target to this structure:

1. 24-hour collection:
   - NAVER Search News API;
   - OpenDART disclosure search;
   - deduplication;
   - symbol mapping;
   - importance scoring.
2. Market-hours continuous KIS WebSocket:
   - realtime trade price;
   - realtime orderbook.
3. Market-hours KIS REST every 1-3 minutes:
   - volume ranking;
   - volume-power / execution-strength style ranking;
   - fluctuation ranking;
   - program-trading aggregate status where the KIS paper capability matrix
     proves support.
4. Top-of-hour DeepSeek Pro:
   - full market analysis;
   - theme/sector organization;
   - strong conditions and conditions to avoid for the current day.
5. Every 10 minutes during market hours, DeepSeek Flash:
   - latest Pro summary;
   - recent 10-minute news/disclosures;
   - KIS ranking changes;
   - current price/orderbook for candidate symbols;
   - holdings and pending-order state;
   - writes one trade document.
6. Always-on trading program:
   - reads new trade documents;
   - cancels previous unfilled buy waits;
   - registers new `WAIT_BUY` / `BUY_NOW` paper orders only after deterministic
     gates;
   - monitors held symbols for stop-loss, take-profit, and trailing-stop in
     realtime.

## 2. Trade Document Contract Shape

The trade document must not contain only prose such as "buy" or "sell." It must
carry a validity window and machine-readable actions:

```json
{
  "schema_version": "flash_trade_document/v0",
  "created_at_kst": "2026-06-05T09:40:00+09:00",
  "valid_until": "2026-06-05T09:50:00+09:00",
  "document_kind": "TRADE_ACTIONS",
  "market_mode": "RISK_ON",
  "max_new_positions": 3,
  "max_total_positions": 5,
  "actions": [
    {
      "ticker": "123456",
      "name": "example",
      "action": "WAIT_BUY",
      "entry_zone": [12300, 12450],
      "take_profit": 12950,
      "stop_loss": 12080,
      "trailing_stop_pct": 1.2,
      "cancel_if_not_filled_until": "2026-06-05T09:50:00+09:00",
      "position_size_pct": 20,
      "reason": "volume spike plus strength rank plus positive news"
    }
  ]
}
```

Allowed action values:

- `WAIT_BUY`: place or maintain a limit buy only if the entry zone is reached
  before the action expires; superseded unfilled waits are canceled unless
  renewed by the next accepted document.
- `BUY_NOW`: attempt an immediate limit buy only if quote/spread/freshness/risk
  gates pass. It is not a market-order shortcut.
- `HOLD`: keep an existing position while realtime stop/take-profit/trailing
  rules remain active.
- `SELL`: sell only an actually held position, with a concrete reason code and
  deterministic confirmation.
- `NO_TRADE`: prohibit new buys for the document or symbol scope.

## 3. Safety Interpretation

- AI artifacts remain non-executable.
- `position_size_pct` is an advisory cap requested by Flash; the deterministic
  risk layer still enforces cash reserve, maximum holdings, available cash,
  reserved cash, pending orders, and paper-only broker guards.
- The executor must re-read authoritative portfolio/order state immediately
  before any KIS paper submission.
- Stop-loss, take-profit, and trailing-stop handling belongs to the always-on
  executor using realtime KIS state, not to a delayed AI tick.

## 4. Files Rebaselined

- `docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md`
- `docs/contracts/hwistock-runtime-contracts.schema.json`
- `docs/contracts/fixtures/runtime-contract-valid.json`
- `docs/contracts/fixtures/runtime-contract-invalid.json`
- `scripts/validate_runtime_contracts.py`
- `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`
- `docs/modules/HWISTOCK-MOD-009_operational-paper-trading-program.md`
- `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md`
- `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
- `docs/units/HWISTOCK-UNIT-014_kis-paper-order-execution-reconciliation.md`
- `docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md`
- `docs/qa/QA-HWISTOCK-UNIT-012_ai-analysis-runtime.md`
- `docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
- `docs/qa/QA-HWISTOCK-UNIT-014_kis-paper-order-execution-reconciliation.md`
- `docs/qa/QA-HWISTOCK-UNIT-016_runtime-contract-hardening.md`
- `docs/set/READY-SET-COMPLETION-20260605_operational-paper-trading-program_hwistock.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-paper-trading-program_hwistock.md`
- `docs/index.md`
- `docs/profiles/PROFILE-HWISTOCK.md`

## 5. Readiness Statement

This Ready-Set rebaseline records the corrected target architecture. It does not
claim the target runtime is complete.

Current correct status remains:

- `implementation_ready: true` only for the contract-hardened Go-Check queue;
- `paper_run_ready: false`;
- `continuous_runner_ready: false`;
- `operational_trading_readiness: false`;
- live trading: forbidden;
- KIS live orders: forbidden.
