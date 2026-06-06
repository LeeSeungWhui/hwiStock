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
status: go_check_local_passed_provider_smoke_blocked
owner: hwi
updated_at: 2026-06-06
evidence_refs:
  - docs/evidence/RUN-20260605_operational-go-check-units-012-015.md
  - docs/set/READY-SET-CORRECTION-20260606_mode-schedule-ai-loop-followup.md
  - docs/set/READY-SET-GPT-PRO-MORNING-PROMPT-20260606_hwistock.md
---

# AI Analysis Runtime QA

## 1. Purpose

Prove that DeepSeek Pro, morning watchlist, and Flash run the owner-defined file
pipeline: hourly Pro aggregate/market-regime analysis, `07:15 KST` morning
watchlist through local Codex CLI browser-use, 10-minute Flash trade-document
generation during the active investment-mode decision window, and no direct
order execution. SSH browser-use is forbidden for the GPT Pro morning path.

## 2. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | config | Inspect model defaults and service env | Runtime defaults use `deepseek-v4-pro` / `deepseek-v4-flash`; placeholder `moonbridge` is not the default | config/test output |
| QA-002 | P0 | no-key | Run AI tick without provider key | Safe block is recorded; no order/intents are unlocked | artifact |
| QA-003 | P0 | fixture | Run AI schema validation with fixture outputs | Malformed, uncited, stale, or policy-violating output is rejected | unit tests |
| QA-004 | P0 | schedule | Inspect hourly Pro, morning watchlist, and active-window Flash schedules | Pro runs top-of-hour; morning watchlist starts at `07:15 KST` through local Codex CLI browser-use; SSH browser-use is not configured; Flash runs every 10 minutes during the active investment-mode decision window; market-regime analysis is included in Pro hourly artifact | schedule audit |
| QA-005 | P0 | flash | Trigger Flash trade-document fixture with latest Pro file, recent 10-minute sources, KIS ranking/quote/orderbook refs, previous trade-doc refs, and portfolio/order-state refs | Flash writes one `flash_trade_document/v0` for the 10-minute bucket, caps the document's action-symbol list at 5, includes WAIT_BUY/BUY_NOW/HOLD/SELL/NO_TRADE semantics, entry/take-profit/stop-loss/trailing/cancel windows, marks portfolio conflicts, and cannot call broker/order code | fixture output |
| QA-006 | P0 | redaction | Review AI input payload | Credentials, account ids, and unapproved full article bodies are rejected | redaction report |
| QA-007 | P0 | provider | Approved provider smoke with real key, if scoped | Provider response is stored sanitized with model/usage/error only | sanitized smoke |
| QA-008 | P0 | conflict | Provide a fixture where the previous trade document or portfolio snapshot already holds/has pending order for the symbol | Flash marks the action as conflict/watch/reject instead of emitting a clean new-entry action | fixture output |
| QA-009 | P0 | sentinel | Simulate Flash timeout, malformed output, provider unavailable, or off-session tick | Runtime writes one finalized `NO_TRADE` sentinel artifact for the 10-minute bucket with no executable intents | fixture output |
| QA-010 | P0 | atomic | Simulate downstream read while Pro/Flash artifact is still being written | Downstream reader ignores temp/incomplete files and accepts only manifest/hash-valid finalized artifacts | fixture output |
| QA-011 | P0 | wait-cancel | Provide an older accepted WAIT_BUY action that remains unfilled when a newer document arrives | New accepted document cancels the old unfilled wait unless it explicitly renews the action and all gates still pass | fixture output |
| QA-012 | P0 | morning | Run or fixture the `07:15 KST` local Codex CLI browser-use morning watchlist path, then trigger the first paper Flash bucket | Flash references `morning_watchlist/v0` or writes `NO_TRADE` with no executable intents; any SSH browser-use route fails this row | artifact |
| QA-013 | P0 | paper-window | Simulate paper/mock Flash ticks at 14:50, 15:00, 15:10, and 15:30 KST | 14:50 can produce a valid entry candidate if all gates pass; 15:00 and later cannot create new entry intents and must write close/watch/reconciliation or `NO_TRADE` context | schedule fixture |

## 3. PASS / FAIL / BLOCKED Rules

- PASS: AI jobs produce validated Pro/Flash artifacts or safe blocks, use
  approved current model ids, cap each Flash document's action-symbol list at
  five, require morning-watchlist evidence before the first active Flash bucket,
  respect the paper/mock `09:00-15:00 KST` decision window, and cannot place or
  unlock orders by themselves.
- FAIL: AI can call broker/order code, defaults to an invalid/stale model id,
  leaks sensitive data, stores unapproved source bodies, or emits clean entry
  actions that conflict with current holdings/pending orders/previous valid
  trade documents, exposes a partial/malformed artifact as executable, or
  creates new paper/mock entry actions after `15:00 KST`.
- BLOCKED: provider key unavailable, AI network operation not scoped, or provider
  outage/rate limit prevents smoke.
