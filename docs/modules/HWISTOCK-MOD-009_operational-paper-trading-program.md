---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-009
type: module
domain: backend_ops
name: Operational paper trading program
spec_status: set
build_status: not_started
verification_status: not_started
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-05
profile_refs:
  - PROFILE-HWISTOCK
module_refs:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-006
  - HWISTOCK-MOD-007
  - HWISTOCK-MOD-008
unit_refs:
  - HWISTOCK-UNIT-011
  - HWISTOCK-UNIT-016
  - HWISTOCK-UNIT-012
  - HWISTOCK-UNIT-013
  - HWISTOCK-UNIT-014
  - HWISTOCK-UNIT-015
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-operational-paper-trading-program.md
  - docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md
  - docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md
contract_refs:
  - docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md
  - docs/contracts/hwistock-runtime-contracts.schema.json
---

# Operational Paper Trading Program

## 1. Purpose

This module is the current authority for turning hwiStock from a skeleton plus
isolated runner parts into an actually runnable paper-trading program.

The target is a 24-hour home-server runtime that can be left running without a
Codex session. The runtime may use configured KIS paper/mock credentials for the
approved KRX paper path, run AI analysis jobs, generate trade-action/order-intent
evidence, place only approved KRX paper orders, reconcile broker-visible paper
state, and expose read-only operator status.

This module does not authorize live trading. It exists because `go_check_passed`
labels on individual skeleton units are not the same as an operational
stock-trading program.

## 2. Program Runtime Contract

The operational paper program is one coordinated system with these branches:

1. `news_disclosure_collector`
   - Runs 24 hours.
   - Collects approved public news and disclosure metadata.
   - Selected first runtime source set is:
     - OpenDART official disclosure API for disclosure events;
     - NAVER Developers Search News API as the primary news source via env
       aliases and configured query/rate limits;
     - public RSS/news-search metadata as fallback-only, not a parallel first
       runtime source;
     - KRX KIND only after terms/access are explicitly recorded.
   - Never places orders.
2. `kis_intraday_market_collector`
   - Runs continuously during the approved intraday window.
   - Collects KIS paper-supported KRX realtime price/orderbook data and
     1-3-minute REST ranking/analysis snapshots.
   - UNIT-013 first signal input set is exactly six KIS paper-read inputs.
   - WebSocket signal inputs where paper-supported:
     - KRX realtime trade price (`H0STCNT0`);
     - KRX realtime orderbook (`H0STASP0`).
   - REST signal inputs, refreshed every 1-3 minutes during market hours:
     - volume rank (`volume-rank`);
     - fluctuation rank (`ranking/fluctuation`);
     - volume power (`ranking/volume-power`);
     - program-trading aggregate status where the KIS paper capability matrix
       proves the endpoint/support contract.
   - Paper fill notice (`H0STCNI9`), balances, buyable cash, and order/fill
     reconciliation belong to `paper_execution` / UNIT-014, not UNIT-013 signal
     generation.
   - NXT/SOR broker-facing collection remains disabled or fallback-only until a
     later approved support-confirmation gate.
3. `deepseek_pro_hourly`
   - Runs on the top of every hour.
   - Reads accumulated news/disclosure files and KIS market-data snapshots.
   - During market hours, market-regime/session analysis is included in the
     same hourly Pro file. It must not be designed as a detached subsystem.
   - Writes `pro_hourly_market_analysis/v0`.
4. `deepseek_flash_decision_10m`
   - Runs every 10 minutes during market hours.
   - Reads the latest Pro file, the recent 10-minute news/disclosure window,
     KIS REST ranking changes, current KIS realtime price/orderbook snapshots,
     deterministic candidate universe, and deterministic risk context.
   - Reads the previous trade-document chain and the current portfolio/order
     snapshot when available: holdings, pending orders, active stop/take-profit
     exits, cooldowns, and still-valid prior trade-action decisions.
   - Writes at most one `flash_trade_document/v0` per 10-minute decision bucket.
   - The document contains at most five symbol actions.
   - Each action must include ticker/name, action type, entry zone if relevant,
     take-profit, stop-loss, trailing-stop percent, validity/cancel window,
     position-size cap, source refs, market-data refs, portfolio-conflict status,
     and risk notes.
   - Supported action values are `WAIT_BUY`, `BUY_NOW`, `HOLD`, `SELL`, and
     `NO_TRADE`.
   - AI artifacts are not executable orders by themselves.
   - Flash may score/select only symbols present in the deterministic
     `compiled_watch/v0` candidate universe; off-universe tickers are rejected
     and cannot become paper intents.
5. `trade_document_executor`
   - Watches newly written `flash_trade_document/v0` files.
   - Cancels unfilled previous `WAIT_BUY` orders when a newer accepted document
     supersedes them unless the new document explicitly renews the wait.
   - Converts only valid buy actions into `paper_order_intent/v0` after
     deterministic strategy/risk checks and portfolio/order-state conflict
     checks.
   - Handles stop-loss, take-profit, and trailing-stop decisions continuously from
     realtime KIS price/orderbook state, not only at the next Flash tick.
   - News-only, AI-only, stale-data, off-session, and unsupported-venue
     actions stay as rejected/watch records.
   - Blocks duplicate buys for a held symbol unless the trade document explicitly
     marks a strategy-approved scale-in and deterministic risk permits it.
   - Blocks conflicting sell/exit instructions unless they match the current
     position, pending orders, and active stop/take-profit state.
6. `paper_execution`
   - Consumes approved paper intents.
   - Calls only the KIS paper/mock KRX-supported path.
   - Maintains idempotency, order state, cancellation, fill lookup, and
     reconciliation.
   - Creates no fake fills, fake balances, or fake PnL.
7. `operator_console`
   - Shows service/timer health, latest evidence, current blocks, kill-switch
     state, paper observation-window metadata, and read-only KIS paper status.
   - Provides no direct buy/sell controls.

## 3. Current Runtime Gap Inventory

Observed on 2026-06-05:

- The user systemd runtime bundle is active for API, frontend, market
  intelligence collection, DeepSeek Pro analysis, runner evidence, KIS paper
  health, and KIS paper continuous runner.
- The currently running market-intelligence collector covers OpenDART/NAVER/RSS
  style source collection, but the exact source-key readiness and source
  coverage must still be proven per source.
- The currently running KIS paper runner can perform read/reconciliation ticks,
  but paper cash order submission is disabled unless explicitly enabled.
- The current base runner reports `blocked_calendar_unconfigured`, which would
  block order flow until calendar/session evidence is configured.
- DeepSeek Pro hourly analysis exists, but the target Pro artifact must be
  upgraded to include KIS market-data snapshots and market-regime/session
  analysis during market hours.
- There is no current KIS intraday ranking/realtime collector artifact feeding
  the Flash 10-minute decision job.
- There is no current DeepSeek Flash 10-minute trade-document writer.
- There is no current source-grounded trade-document to paper-intent queue that
  feeds the KIS paper runner.
- There is no current portfolio/order-state snapshot contract included in the
  Flash prompt or final executor gate.
- 2026-06-05 ChatGPT Pro external review classified the current operational
  architecture as directionally correct but not implementation-ready until the
  machine-checkable data/execution contracts are hardened. Blocking contract
  gaps include versioned artifact schemas, trade-document idempotency, atomic
  file publication, failure/sentinel semantics, executor locking, reservation
  accounting, broker-submit ambiguity handling, order state machine, freshness
  TTLs, and enforceable paper-only runtime guards.

## 4. Safety Contract

P0 safety boundaries:

- KIS live domains are forbidden.
- Real-money trading is forbidden.
- Live credentials are forbidden.
- Public/LAN exposure is forbidden.
- Secrets must stay in `/home/hwi/.config/hwistock/*.env` and must never be
  printed, committed, or stored in evidence.
- AI cannot hold credentials, call broker APIs, or directly place orders.
- The deterministic strategy/risk layer always wins over AI.
- Cash-only policy is mandatory.
- Starting live baseline is 2,000,000 KRW; paper balance does not enlarge the
  hwiStock risk overlay.
- Maximum simultaneous holdings is 5.
- Minimum cash reserve ratio is 0.25.
- Credit, margin, 미수, borrowed funds, leverage, all-in sizing, and profit
  guarantee claims are forbidden.
- Observation duration is operator-selected metadata. The program must not
  hardcode a seven-day stop/pass/fail condition.

## 5. Contract-Hardening Gate

UNIT-016 has closed the Set-level runtime contracts in
`docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md` and
`docs/contracts/hwistock-runtime-contracts.schema.json`. Before UNIT-012,
UNIT-013, or UNIT-014 can claim Go-Check PASS for order-producing work, their
implementation and tests must cite and enforce these contracts:

- versioned JSON schemas for all cross-process artifacts:
  `news_event/v0`, `disclosure_event/v0`, `kis_market_snapshot/v0`,
  `pro_hourly_market_analysis/v0`, `flash_trade_document/v0`,
  `portfolio_snapshot/v0`, `order_state_snapshot/v0`,
  `paper_order_intent/v0`, `executor_decision/v0`,
  `broker_order_request/v0`, `broker_order_result/v0`, and
  `reconciliation_event/v0`;
- required metadata on every artifact: `schema_version`, `run_id`,
  `source_id` or input refs, `collected_at_kst`, `source_published_at` where
  applicable, `valid_until`, `content_hash`, and validation result;
- deterministic `trade_doc_id`, `intent_id`, and broker `client_order_key`
  generation, plus append-only idempotency ledger semantics;
- atomic artifact publication: write temp, fsync, atomic rename, and manifest
  or ready marker with byte size/hash/schema version;
- Flash failure behavior: at most one finalized artifact per 10-minute decision
  bucket, and invalid/missing model output produces a deterministic `NO_TRADE`
  sentinel
  artifact rather than an executable action;
- single-writer executor or transactional account/symbol locks, plus
  reservation accounting for pending cash, pending quantity, holdings slots,
  active exits, cooldowns, and consumed trade documents;
- formal order state machine and allowed transitions for submitted, unknown,
  rejected, partially filled, canceled, expired, reconciled, and locked states;
- freshness TTLs and fail-closed behavior for market snapshots, orderbook,
  Pro/Flash artifacts, portfolio snapshots, order snapshots, news/disclosure
  records, and calendar/session evidence;
- paper-only broker guard that aborts on unknown/live KIS domain, live account
  profile, unsupported TR ID, unsupported market/route, or missing paper-mode
  self-test; and
- QA rows for duplicate/replayed trade docs, partial file writes, stale inputs,
  portfolio conflicts, reservation breaches, process restart after ambiguous
  submit, websocket disconnect, KIS reject/partial fill, and live-endpoint
  misconfiguration.

## 6. Implementation Queue

| order | unit_id | purpose | result needed before operational paper run |
| --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-011 | Installable runtime supervisor | API, frontend, collectors, AI, KIS paper health, and paper runner services/timers are installable, inspectable, and restartable under user systemd. |
| 2 | HWISTOCK-UNIT-016 | Runtime data/execution contract hardening | Set-level contracts are closed: cross-process schemas, idempotency keys, atomic publication, freshness TTLs, order state machine, reservation ledger, paper-only broker guard, failure-mode QA, fixtures, and validator exist. |
| 3 | HWISTOCK-UNIT-012 | AI analysis runtime | DeepSeek Pro writes the hourly aggregate/market-regime file; DeepSeek Flash writes at most one finalized 10-minute trade document whose action list contains max 5 symbols, includes `NO_TRADE` sentinels on failure, and is aware of previous trade documents/current portfolio state; both remain unable to place orders. |
| 4 | HWISTOCK-UNIT-013 | Market-data/trade-document to intent pipeline | KIS intraday market data, Pro files, Flash trade documents, source refs, previous trade documents, and current portfolio/order state become deterministic condition cards and approved paper intents only after schema/freshness/session/risk/reservation/conflict gates pass. |
| 5 | HWISTOCK-UNIT-014 | KIS paper execution and reconciliation | Approved intents can place KRX paper orders, reconcile order/fill/balance/buyable evidence, survive restart/ambiguous-submit paths, and avoid duplicates/fake broker state. |
| 6 | HWISTOCK-UNIT-015 | Operator console and observation Prove | The owner can observe 24-hour operation, blocks, paper evidence, and reports without direct dashboard order controls. |

`HWISTOCK-UNIT-010` remains the local no-network KIS paper runner foundation and
is an input to UNIT-014, not a complete operational program by itself.

## 7. PASS Definition For "Actually Runnable"

hwiStock can be called paper-run-ready only when:

- the contract-hardening gate above is closed and cited by the implementation
  evidence;
- the unit queue above has Go-Check PASS or explicit non-blocking deferrals;
- selected services/timers are installed and running through user systemd or an
  approved service manager;
- KIS paper network use is proven against the paper/mock KRX domain only;
- at least one approved paper-intent cycle is either safely blocked with a
  deterministic reason or placed/reconciled as a KRX paper order;
- service restart/idempotency is proven;
- dashboard/API status is read-only and local-only;
- observation-window evidence is written without a hardcoded duration; and
- final Prove evidence says `paper_run_ready: true`.

Until then, the correct status is:

`operational_trading_readiness: false`.
