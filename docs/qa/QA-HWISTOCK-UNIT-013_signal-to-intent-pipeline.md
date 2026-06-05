---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-013
type: qa_scenario
name: Signal to paper intent pipeline QA
unit_refs:
  - HWISTOCK-UNIT-013
  - HWISTOCK-UNIT-016
module_refs:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-007
profile_refs:
  - PROFILE-HWISTOCK
status: set
owner: hwi
updated_at: 2026-06-05
---

# Signal To Paper Intent Pipeline QA

## 1. Purpose

Prove that the program can collect KIS intraday market data and convert
Flash-written trade documents into source-grounded paper order intents without
manual hand-written intent files, while still blocking unsafe or unsupported
trades.

## 2. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | kis-data | Run KIS market-data collector in no-network and approved paper-read modes | Collector writes sanitized snapshot or classified safe block; no order endpoint is called | collector artifact |
| QA-002 | P0 | fixture | Feed normalized disclosure/news events with known source ids | Action records include source ids and source hashes | fixture output |
| QA-003 | P0 | symbol | Resolve corp/name/symbol mappings | Ambiguous or missing symbols are blocked with reason | resolver test |
| QA-004 | P0 | event-only | Provide news/disclosure without KIS market confirmation | Watch/reject action is created but no paper intent is queued | pipeline test |
| QA-005 | P0 | ai-only | Provide Flash trade document without deterministic confirmation | Intent is blocked; AI cannot call KIS order endpoints | policy test |
| QA-006 | P0 | risk | Exercise cash reserve, holdings cap, kill switch, stale data, and calendar cases | Unsafe intents are blocked before queue | risk test |
| QA-007 | P0 | idempotency | Re-run same source/trade-document bundle | No duplicate active intent is created | queue test |
| QA-008 | P0 | conflict | Provide Flash trade document whose symbol is already held, pending, exiting, cooled down, or active in a prior still-valid trade document | Action is rejected or kept as watch with a specific conflict reason; no paper intent is queued | queue artifact |
| QA-009 | P0 | approved | Provide fully valid `WAIT_BUY` or `BUY_NOW` action plus fresh KIS snapshot and no portfolio/order-state conflict | One `paper_order_intent/v0` is queued with expiry, risk refs, source refs, entry, take-profit, stop-loss, trailing, and cancel window | queue artifact |
| QA-010 | P0 | manifest | Provide incomplete or hash-mismatched Pro/Flash/KIS artifacts | Pipeline rejects the bundle before intent creation | queue artifact |
| QA-011 | P0 | reservation | Provide pending-buy/pending-sell fixtures that would breach cash reserve or max holding slots under worst-case fill | Intent is rejected with reservation/cap reason | risk log |
| QA-012 | P0 | freshness | Provide expired price, orderbook, ranking, Pro, Flash, portfolio, order-state, or calendar artifacts | Intent is rejected with the matching TTL/freshness reason | queue artifact |
| QA-013 | P0 | wait-cancel | Accept a new trade document after an older unfilled WAIT_BUY is still pending | Prior unfilled wait is canceled unless renewed by the new document and all gates still pass | queue artifact |
| QA-014 | P0 | paper-read-boundary | Enable UNIT-013 KIS paper-read collector with paper/mock credentials | Only market-data endpoints are attempted; order/cancel/modify endpoints remain uncalled and unsupported NXT/SOR branches are disabled/fallback-only | endpoint audit |

## 3. PASS / FAIL / BLOCKED Rules

- PASS: valid Flash trade-document actions with fresh KIS/source context can
  create one approved paper intent, while missing source/KIS/risk/calendar/AI
  boundary and portfolio/order-state conflict cases are blocked with reasons.
- FAIL: news-only or AI-only input can queue an executable paper intent, KIS
  order endpoints are called in this row, re-runs duplicate active intents, or
  a held/pending/exiting/cooldown symbol can queue a conflicting new intent, an
  older unfilled wait survives a superseding document without renewal, or
  stale/incomplete artifacts can produce an intent.
- BLOCKED: approved KIS market-data source is not available for rows requiring
  fresh market confirmation.
- BLOCKED: any UNIT-013 path attempts KIS order/cancel/modify transport or
  treats NXT/SOR broker-facing data as paper-proven.
