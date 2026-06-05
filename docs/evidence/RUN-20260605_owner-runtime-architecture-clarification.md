---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-owner-runtime-architecture-clarification
type: evidence
stage: ready-set
status: superseded_by_10m_trade_document_rebaseline
project_root: /data/workspace/My/hwiStock
docs_base: docs
current_authority: false
updated_at: 2026-06-05
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
module_ref: docs/modules/HWISTOCK-MOD-009_operational-paper-trading-program.md
ready_set_ref: docs/set/READY-SET-COMPLETION-20260605_operational-paper-trading-program_hwistock.md
superseded_by:
  - docs/evidence/RUN-20260605_owner-runtime-architecture-10m-trade-document-rebaseline.md
  - docs/evidence/RUN-20260605_owner-selected-naver-kis6-scope.md
---

# Owner Runtime Architecture Clarification

## 1. Clarified Target

The owner clarified that the intended hwiStock program is a file-driven,
continuously running paper-trading pipeline:

1. 24-hour news/disclosure collection from permitted/free public sources.
2. Continuous KIS intraday market-data collection during the approved intraday
   window, including price/quote context, ranking/analysis data, and
   paper-supported KRX realtime price/orderbook feeds.
3. DeepSeek Pro runs on the top of every hour and writes an aggregate analysis
   file. During market hours, market-regime/session analysis belongs inside this
   Pro artifact.
4. DeepSeek Flash runs every minute during market hours and writes one trade
   document for that minute. The document contains at most five symbol
   candidates. Each candidate must include entry, take-profit, stop-loss,
   sizing/cash cap, validity, source refs, portfolio-conflict status, and risk
   notes.
5. The auto-trading runner watches newly written trade documents, validates them
   through deterministic risk gates plus current holdings/pending-order/active
   exit checks, and submits only approved KIS KRX paper/mock cash orders.

Additional owner clarification: Flash must avoid conflicts with the current
portfolio. It must read the previous trade-document chain and/or current
portfolio/order-state snapshot, preferably both, before writing a new
trade-document candidate list. The executor must re-check the same class of
conflicts immediately before KIS submission because holdings and pending orders
can change after Flash writes the document.

This replaces any design implication that market-regime analysis is a detached
subsystem or that the current KIS paper runner foundation alone is the complete
program.

## 2. Source Recommendations Captured

Initial free/public source recommendation:

- OpenDART official disclosure API for disclosure events.
- NAVER Developers Search News API for keyed news search metadata.
- Public RSS/news-search metadata as a no-key fallback.
- KRX KIND or other portal collection remains deferred until terms/access are
  explicitly recorded.

Historical note: this recommendation is superseded by the later owner-selected
`NAVER + KIS 6` scope. Current first-runtime news source is NAVER Search News
API, with public RSS fallback-only.

KIS intraday collection scope:

- REST/current quote: `inquire-price`.
- REST/intraday chart and execution context:
  `inquire-time-itemchartprice`, `inquire-time-itemconclusion`.
- REST ranking/analysis:
  `volume-rank`, `ranking/fluctuation`, `ranking/volume-power`,
  `ranking/top-interest-stock`.
- WebSocket/realtime, where paper-supported:
  KRX realtime trade price `H0STCNT0`, KRX realtime orderbook `H0STASP0`, and
  paper fill notice `H0STCNI9`.

Historical note: this broad KIS list is not the current UNIT-013 signal scope.
Current UNIT-013 signal scope is the six-input allowlist recorded in
`docs/evidence/RUN-20260605_owner-selected-naver-kis6-scope.md`.

## 3. Files Updated

- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/index.md`
- `docs/modules/HWISTOCK-MOD-009_operational-paper-trading-program.md`
- `docs/set/READY-SET-COMPLETION-20260605_operational-paper-trading-program_hwistock.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-paper-trading-program_hwistock.md`
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-paper-trading-program_hwistock.md`
- `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md`
- `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
- `docs/units/HWISTOCK-UNIT-014_kis-paper-order-execution-reconciliation.md`
- `docs/qa/QA-HWISTOCK-UNIT-012_ai-analysis-runtime.md`
- `docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
- `docs/qa/QA-HWISTOCK-UNIT-014_kis-paper-order-execution-reconciliation.md`

## 4. Readiness Statement

This evidence clarifies the target architecture. It does not claim the target
runtime is already complete.

Current correct status remains:

- `paper_run_ready: false`
- `operational_trading_readiness: false`
- live trading: forbidden
- KIS live orders: forbidden
