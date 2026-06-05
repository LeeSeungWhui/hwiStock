---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-012
type: qa_scenario
name: AI analysis runtime QA
unit_refs:
  - HWISTOCK-UNIT-012
  - HWISTOCK-UNIT-016
module_refs:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-003
profile_refs:
  - PROFILE-HWISTOCK
status: set
owner: hwi
updated_at: 2026-06-05
---

# AI Analysis Runtime QA

## 1. Purpose

Prove that DeepSeek Pro and Flash run the owner-defined file pipeline:
hourly Pro aggregate/market-regime analysis, 10-minute Flash trade-document
generation, and no direct order execution.

## 2. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | config | Inspect model defaults and service env | Runtime defaults use `deepseek-v4-pro` / `deepseek-v4-flash`; placeholder `moonbridge` is not the default | config/test output |
| QA-002 | P0 | no-key | Run AI tick without provider key | Safe block is recorded; no order/intents are unlocked | artifact |
| QA-003 | P0 | fixture | Run AI schema validation with fixture outputs | Malformed, uncited, stale, or policy-violating output is rejected | unit tests |
| QA-004 | P0 | schedule | Inspect hourly Pro and market-hours Flash schedules | Pro runs top-of-hour; Flash runs every 10 minutes during market hours; market-regime analysis is included in Pro hourly artifact | schedule audit |
| QA-005 | P0 | flash | Trigger Flash trade-document fixture with latest Pro file, recent 10-minute sources, KIS ranking/quote/orderbook refs, previous trade-doc refs, and portfolio/order-state refs | Flash writes one `flash_trade_document/v0` for the 10-minute bucket, caps the document's action-symbol list at 5, includes WAIT_BUY/BUY_NOW/HOLD/SELL/NO_TRADE semantics, entry/take-profit/stop-loss/trailing/cancel windows, marks portfolio conflicts, and cannot call broker/order code | fixture output |
| QA-006 | P0 | redaction | Review AI input payload | Credentials, account ids, and unapproved full article bodies are rejected | redaction report |
| QA-007 | P0 | provider | Approved provider smoke with real key, if scoped | Provider response is stored sanitized with model/usage/error only | sanitized smoke |
| QA-008 | P0 | conflict | Provide a fixture where the previous trade document or portfolio snapshot already holds/has pending order for the symbol | Flash marks the action as conflict/watch/reject instead of emitting a clean new-entry action | fixture output |
| QA-009 | P0 | sentinel | Simulate Flash timeout, malformed output, provider unavailable, or off-session tick | Runtime writes one finalized `NO_TRADE` sentinel artifact for the 10-minute bucket with no executable intents | fixture output |
| QA-010 | P0 | atomic | Simulate downstream read while Pro/Flash artifact is still being written | Downstream reader ignores temp/incomplete files and accepts only manifest/hash-valid finalized artifacts | fixture output |
| QA-011 | P0 | wait-cancel | Provide an older accepted WAIT_BUY action that remains unfilled when a newer document arrives | New accepted document cancels the old unfilled wait unless it explicitly renews the action and all gates still pass | fixture output |

## 3. PASS / FAIL / BLOCKED Rules

- PASS: AI jobs produce validated Pro/Flash artifacts or safe blocks, use
  approved current model ids, cap each Flash document's action-symbol list at
  five, and cannot place or unlock orders by themselves.
- FAIL: AI can call broker/order code, defaults to an invalid/stale model id,
  leaks sensitive data, stores unapproved source bodies, or emits clean entry
  actions that conflict with current holdings/pending orders/previous valid
  trade documents, or exposes a partial/malformed artifact as executable.
- BLOCKED: provider key unavailable, AI network operation not scoped, or provider
  outage/rate limit prevents smoke.
