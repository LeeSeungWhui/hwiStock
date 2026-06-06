---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-009
type: module
domain: backend_ops
name: Operational automated trading program
spec_status: set
build_status: not_started
verification_status: not_started
post_pro_reinforcement_status: unit011_015_go_check_passed_unit012_014_pending
implementation_ready_scope: operational_contract_hardened_go_check_queue
broker_run_ready: false
operational_readiness: false_final_operation_acceptance_only
paper_experiment_ready: conditional
live_money_trading_ready: not_applicable
production_quality_ready: partial_non_blocking
paper_order_loop_policy: session_approval_caps_evidence
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-06
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
  - docs/evidence/RUN-20260605_ready-set-operational-automated-trading-program.md
  - docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md
  - docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md
  - docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md
  - docs/evidence/RUN-20260606_monday-operation-p0-safety-gates-go-check.md
  - docs/evidence/RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix.md
  - docs/evidence/RUN-20260606_paper-experiment-readiness-split-go-check.md
  - docs/set/READY-SET-CORRECTION-20260606_mode-schedule-ai-loop-followup.md
contract_refs:
  - docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md
  - docs/contracts/hwistock-runtime-contracts.schema.json
prompt_refs:
  - docs/set/READY-SET-GPT-PRO-MORNING-PROMPT-20260606_hwistock.md
---

# Operational Automated Trading Program

> Post-Pro readiness note (2026-06-05): this module remains the architecture
> target, and the existing operational Ready-Set remains current authority.
> Service/timer visibility, local tests, and dashboard rendering are not enough
> to claim operation readiness.
>
> KIS paper/mock hotfix note (2026-06-06): latest runtime evidence preserves
> provider-unsupported account-helper truth as unknown and skips unsupported KIS
> helper TRs instead of calling real-investment TR ids. This strengthens runtime
> safety but does not by itself make the order-submit path ready.
>
> Paper experiment correction (2026-06-06): the current Monday-start goal is
> `paper_experiment_ready`, not final live-money or production-quality
> readiness. `live_money_trading_ready = not_applicable` and
> `production_quality_ready = partial_non_blocking` must not block the KIS
> paper/mock order loop. The paper loop may submit KRX paper/mock orders only
> under `paper_experiment` session approval, caps, KRX session/calendar
> preflight, account truth, duplicate lock, submit-result recording, and
> evidence-write success.
>
> Investment-mode schedule correction (2026-06-06): paper/mock KRX
> investment/order-decision time is `09:00-15:00 KST`. KRX public
> regular-session/market-data context may continue through `15:30 KST`, but
> `15:00-15:30 KST` is close/market-data/reconciliation context only and must not
> unlock new paper/mock KRX entries or broker order submissions.

## 1. Purpose

This module is the current authority for turning hwiStock from a skeleton plus
isolated runner parts into an actually runnable automated-trading program.

The target is a 24-hour home-server runtime that can be left running without a
Codex session. The runtime may use configured KIS broker-adapter credentials for the
approved KRX adapter path, run AI analysis jobs, generate trade-action/order-intent
evidence, place only approved KRX broker orders, reconcile broker-visible
state, and expose read-only operator status.

This module does not authorize unapproved adapter operation. It exists because `go_check_passed`
labels on individual skeleton units are not the same as an operational
stock-trading program.

## 2. Program Runtime Contract

The operational trading program is one coordinated system with these branches:

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
   - Collects mode-aware KIS broker adapter-supported realtime
     price/orderbook/market-operation data and 1-3-minute REST ranking/analysis
     snapshots.
   - Paper/mock mode enables KRX + integrated realtime inputs:
     - KRX realtime trade price/orderbook/market operation
       (`H0STCNT0`, `H0STASP0`, `H0STMKO0`);
     - integrated realtime trade price/orderbook/market operation
       (`H0UNCNT0`, `H0UNASP0`, `H0UNMKO0`).
   - Real investment mode additionally enables NXT realtime trade
     price/orderbook/market operation (`H0NXCNT0`, `H0NXASP0`, `H0NXMKO0`).
   - REST signal inputs, refreshed every 1-3 minutes during market hours:
     - volume rank (`volume-rank`);
     - fluctuation rank (`ranking/fluctuation`);
     - volume power (`ranking/volume-power`);
     - program-trading aggregate status where the KIS broker adapter capability matrix
       proves the endpoint/support contract.
   - Adapter fill notice (`H0STCNI9`), balances, buyable cash, supported
     sellable/cancelable truth, provider-calendar cross-checks, and order/fill
     reconciliation belong to `broker_execution` / UNIT-014, not UNIT-013
     signal generation. In paper/mock, local references mark sellable,
     cancelable, realized-PnL, and holiday TRs as unsupported, so the runtime
     skips them and fails closed where the missing truth matters.
   - NXT broker-facing market-data collection is disabled in paper/mock mode and
     enabled only in real investment mode; SOR remains disabled unless a later
     support-confirmation gate adds it.
   - Paper/mock mode may collect KRX/integrated market-data context until the
     KRX close at `15:30 KST`, but investment/order-decision and entry-intent
     windows close at `15:00 KST`.
3. `deepseek_pro_hourly`
   - Runs on the top of every hour.
   - Reads accumulated news/disclosure files and KIS market-data snapshots.
   - During market hours, market-regime/session analysis is included in the
     same hourly Pro file. It must not be designed as a detached subsystem.
   - Writes `pro_hourly_market_analysis/v0`.
3a. `gpt_morning_watchlist`
   - Starts at `07:15 KST` when the route is scoped.
   - Executes through Codex CLI on the local desktop/workstation using local
     browser-use and the user's logged-in local Chrome ChatGPT Pro session.
   - SSH browser-use, reverse-socket Chrome bridges, remote Chrome, and
     hwiServer-side browser automation are forbidden for this path.
   - Reads the prior close through current-morning Pro/news/disclosure
     artifacts, including weekend carry-over when the next trading day is
     Monday.
   - Writes `morning_watchlist/v0` or a named safe-block.
   - The first Flash bucket for the active investment mode must reference the
     latest valid morning watchlist or safe-block: `09:00 KST` for paper/mock
     and `08:00 KST` for future live mode.
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
     and cannot become order intents.
   - Paper/mock Flash buckets that may produce new entry intents run only during
     `09:00-15:00 KST`. Later paper/mock ticks may write `NO_TRADE`, watch,
     close, or reconciliation context but cannot create new entry intents.
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
6. `broker_execution`
   - Consumes approved order intents.
   - Calls only the KIS broker-adapter KRX-supported path.
   - Maintains idempotency, order state, cancellation, fill lookup, and
     reconciliation.
   - Creates no fake fills, fake balances, or fake PnL.
   - Enforces the dynamic 75% exposure cap from authoritative account truth:
     current position value plus pending buy notional plus the new order notional
     must be at or below `effective_total_deposit_krw * 0.75`, where the
     effective base remains capped by the 2,000,000 KRW risk-overlay capital
     unless a later approved profile/unit change raises it.
7. `operator_console`
   - Shows service/timer health, latest evidence, current blocks, kill-switch
     state, operation observation-window metadata, and read-only KIS broker adapter status.
   - Provides no direct buy/sell controls.
8. `daily_close_report`
   - Paper/mock mode writes the post-KRX-close operation summary after
     `15:30 KST`; future live mode targets `20:00 KST`.
   - The report uses system-calculated PnL/exposure/order-state data and AI
     interpretation only; AI does not calculate the numbers.

## 3. Runtime Gap Inventory Snapshot

Observed on 2026-06-05. This snapshot is retained as the Go-Check gap baseline;
later evidence may narrow individual gaps without making the whole program
operation-ready.

- The user systemd runtime bundle is active for API, frontend, market
  intelligence collection, DeepSeek Pro analysis, runner evidence, KIS broker adapter
  health, and KIS broker adapter continuous runner.
- The currently running market-intelligence collector covers OpenDART/NAVER/RSS
  style source collection, but the exact source-key readiness and source
  coverage must still be proven per source.
- The currently running KIS broker adapter runner can perform read/reconciliation
  ticks. KIS paper/mock cash order submission is enabled only by
  `paper_experiment` mode plus a date/cap-scoped approval file and still fails
  closed on token/account/balance/buyable, KRX-session, duplicate-lock,
  evidence-write, submit-result, or crash blockers.
- The 2026-06-05 base runner reported `blocked_calendar_unconfigured`, which
  blocked order flow until calendar/session evidence was configured. The
  2026-06-06 Monday P0 safety gate later hardened this behavior: date-specific
  KST calendar rows are required, Saturday/non-trading days block as
  `blocked_calendar_non_trading_day`, and KRX order submission additionally
  requires `krxOrderSessionOpen=true`.
- DeepSeek Pro hourly analysis exists, but the target Pro artifact must be
  upgraded to include KIS market-data snapshots and market-regime/session
  analysis during market hours.
- There is no current KIS intraday ranking/realtime collector artifact feeding
  the Flash 10-minute decision job.
- There is no current DeepSeek Flash 10-minute trade-document writer.
- The source-grounded trade-document to order-intent queue exists as a bounded
  local implementation surface and must feed the KIS broker adapter runner only
  through deterministic schema/freshness/session/risk/reservation/conflict gates.
- There is no current portfolio/order-state snapshot contract included in the
  Flash prompt or final executor gate.
- 2026-06-05 ChatGPT Pro external review classified the current operational
  architecture as directionally correct but not implementation-ready until the
  machine-checkable data/execution contracts are hardened. Blocking contract
  gaps include versioned artifact schemas, trade-document idempotency, atomic
  file publication, failure/sentinel semantics, executor locking, reservation
  accounting, broker-submit ambiguity handling, order state machine, freshness
  TTLs, and enforceable adapter-only runtime guards.

## 4. Safety Contract

P0 safety boundaries:

- KIS unapproved domains stay outside the current adapter boundary.
- Account-affecting trading requires explicit scoped approval. For the current
  KIS paper/mock experiment, that approval is session-level
  `paper_experiment` approval with date/cap/source/calendar constraints; no
  per-order human approval is required inside that approved session.
- Unapproved credentials stay outside the current adapter boundary.
- Public/LAN exposure requires a later authenticated access contract.
- Secrets must stay in `/home/hwi/.config/hwistock/*.env` and must never be
  printed, committed, or stored in evidence.
- AI cannot hold credentials, call broker APIs, or directly place orders.
- The deterministic strategy/risk layer always wins over AI.
- Cash-only policy is mandatory.
- Starting capital baseline is 2,000,000 KRW. Authoritative adapter/account
  truth is used for the dynamic 75% exposure gate, but the effective exposure
  base must not exceed the hwiStock risk overlay unless a later approved
  profile/unit change raises it.
- Maximum simultaneous holdings is 5.
- Minimum cash reserve ratio is 0.25.
- Credit, margin, 미수, borrowed funds, leverage, all-in sizing, and profit
  guarantee claims stay outside the baseline risk policy.
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
- adapter-only broker guard that aborts on unknown/unapproved KIS domain, broker account
  profile, unsupported TR ID, unsupported market/route, or missing adapter-mode
  self-test; and
- QA rows for duplicate/replayed trade docs, partial file writes, stale inputs,
  portfolio conflicts, reservation breaches, process restart after ambiguous
  submit, websocket disconnect, KIS reject/partial fill, and unapproved-endpoint
  misconfiguration.

## 6. Implementation Queue

| order | unit_id | purpose | result needed before operational operation run |
| --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-011 | Installable runtime supervisor | API, frontend, collectors, AI, KIS broker adapter health, and broker-adapter runner services/timers are installable, inspectable, and restartable under user systemd. |
| 2 | HWISTOCK-UNIT-016 | Runtime data/execution contract hardening | Set-level contracts are closed: cross-process schemas, idempotency keys, atomic publication, freshness TTLs, order state machine, reservation ledger, adapter-only broker guard, failure-mode QA, fixtures, and validator exist. |
| 3 | HWISTOCK-UNIT-012 | AI analysis runtime | DeepSeek Pro writes the hourly aggregate/market-regime file; DeepSeek Flash writes at most one finalized 10-minute trade document whose action list contains max 5 symbols, includes `NO_TRADE` sentinels on failure, and is aware of previous trade documents/current portfolio state; both remain unable to place orders. |
| 4 | HWISTOCK-UNIT-013 | Market-data/trade-document to intent pipeline | KIS intraday market data, Pro files, Flash trade documents, source refs, previous trade documents, and current portfolio/order state become deterministic condition cards and approved order intents only after schema/freshness/session/risk/reservation/conflict gates pass. |
| 5 | HWISTOCK-UNIT-014 | KIS broker adapter execution and reconciliation | Approved intents can place KRX broker orders, reconcile order/fill/balance/buyable evidence, survive restart/ambiguous-submit paths, and avoid duplicates/fake broker state. |
| 6 | HWISTOCK-UNIT-015 | Operator console and observation Prove | The owner can observe 24-hour operation, blocks, adapter evidence, and reports without direct dashboard order controls. |

`HWISTOCK-UNIT-010` remains the local no-network KIS broker adapter runner foundation and
is an input to UNIT-014, not a complete operational program by itself.

## 7. PASS Definition For "Actually Runnable"

hwiStock can be called operation-ready only when:

- the contract-hardening gate above is closed and cited by the implementation
  evidence;
- the unit queue above has Go-Check PASS or explicit non-blocking deferrals;
- selected services/timers are installed and running through user systemd or an
  approved service manager;
- KIS broker adapter network use is proven against the broker-adapter KRX domain only;
- at least one approved order-intent cycle is either safely blocked with a
  deterministic reason or placed/reconciled as a KRX broker order;
- service restart/idempotency is proven;
- dashboard/API status is read-only and local-only;
- observation-window evidence is written without a hardcoded duration; and
- final Prove evidence says `broker_run_ready: true`.

For the current KIS paper/mock experiment, the narrower Monday readiness target
is satisfied when `paper_experiment_ready = true`, not when final operation
acceptance is complete. Its hard blockers are disabled paper network/order loop,
paper token failure, account/balance/buyable failure, KRX session/calendar
failure, broken duplicate lock, evidence-write failure, missing submit-result
recording, and process crash. Non-blockers for the experiment include
`live_money_trading_ready =
not_applicable`, `production_quality_ready = partial_non_blocking`, incomplete
final observation acceptance, SELL/exit coverage gaps, unsupported paper/mock
helper TRs that are safely skipped, and dashboard menu incompleteness.

Until final operation acceptance closes, the correct broad status is:

`operational_readiness: false_final_operation_acceptance_only`.
