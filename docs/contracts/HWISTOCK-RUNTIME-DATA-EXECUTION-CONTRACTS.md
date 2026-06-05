---
schema_version: hwi.runtime-contract/v0
id: HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS
type: runtime_contract
name: Runtime data and execution contracts
status: set
owner: hwi
updated_at: 2026-06-05
profile_refs:
  - PROFILE-HWISTOCK
module_refs:
  - HWISTOCK-MOD-009
unit_refs:
  - HWISTOCK-UNIT-016
schema_catalog_ref: docs/contracts/hwistock-runtime-contracts.schema.json
fixture_refs:
  - docs/contracts/fixtures/runtime-contract-valid.json
  - docs/contracts/fixtures/runtime-contract-invalid.json
validation_command: source ./env.sh && python3 scripts/validate_runtime_contracts.py
---

# hwiStock Runtime Data And Execution Contracts

## 1. Contract Status

This document closes the contract shape required by `HWISTOCK-UNIT-016` before
order-producing Go rows may start. It does not implement broker calls, place
orders, call DeepSeek, or authorize live trading.

The machine-checkable catalog is
`docs/contracts/hwistock-runtime-contracts.schema.json`. The local validator is
`scripts/validate_runtime_contracts.py`.

## 2. Runtime Data Flow

| step | producer | artifact | consumer | executable? |
| --- | --- | --- | --- | --- |
| 1 | `news_disclosure_collector` | `news_event/v0`, `disclosure_event/v0` | Pro/Flash/context builders | no |
| 2 | `kis_intraday_market_collector` | `kis_market_snapshot/v0` | Pro/Flash/intent pipeline | no |
| 3 | `deepseek_pro_hourly` | `pro_hourly_market_analysis/v0` | Flash | no |
| 4 | `deepseek_flash_decision_10m` | `flash_trade_document/v0` | intent pipeline | no |
| 5 | portfolio/order reconciler | `portfolio_snapshot/v0`, `order_state_snapshot/v0` | Flash and executor | no |
| 6 | intent pipeline | `paper_order_intent/v0` | executor | yes, only after gates |
| 7 | executor | `executor_decision/v0`, `broker_order_request/v0` | KIS paper adapter/reconciliation | request only |
| 8 | KIS paper adapter/reconciler | `broker_order_result/v0`, `reconciliation_event/v0` | ledger/dashboard/report | no |

AI artifacts are never directly executable. The executor reads only
schema-validated `paper_order_intent/v0` records and still re-checks
authoritative portfolio/order state before any KIS paper submission.

## 3. Common Artifact Rules

Every artifact in the schema catalog must include:

- `schema_version`;
- `artifact_id`;
- `artifact_type`;
- `run_id`;
- `trading_date`;
- `environment`;
- `created_at_kst`;
- `collected_at_kst`;
- `valid_until`;
- `content_hash`;
- `redaction_status`;
- `producer`;
- `input_refs`;
- `validation`.
- `publication`.

Timestamps are KST ISO-8601 strings. `valid_until` must be after
`created_at_kst`. `content_hash` is a lowercase 64-character SHA-256 hex digest
of the normalized artifact payload or input manifest.

Source-origin events must additionally include `source_event_id`,
`source_published_at_kst`, `dedupe_key`, `source_hash`,
`collection_watermark`, and `terms_policy_ref`. News/disclosure freshness is
evaluated from the source timestamp where provided, not from collector receipt
alone.

## 4. Atomic Publication

Pro, Flash, intent, executor, and broker-result artifacts must be published
atomically:

1. write the payload to a temporary path under the target directory;
2. fsync the file where the platform supports it;
3. fsync the containing directory where the platform supports it;
4. atomically rename into the final path;
5. write a manifest or ready marker containing schema version, byte size, hash,
   producer, completed timestamp, and validator result.

Consumers must ignore temp files and finalized files without a matching
manifest/hash. A partial artifact must fail closed and cannot produce intents or
orders.

## 5. Flash 10-Minute Decision-Document Semantics

Flash writes **at most one finalized decision document per 10-minute market
decision bucket**.

- If the model produces a valid trade document, the artifact is
  `flash_trade_document/v0`.
- If the model times out, returns malformed data, is unavailable, has stale
  inputs, or the tick is off-session, the artifact is still
  `flash_trade_document/v0` but `document_kind` is `NO_TRADE`.
- `NO_TRADE` artifacts contain no executable intents and no clean entry actions.
- Valid trade documents may contain at most five symbol actions.
- Allowed action values are `WAIT_BUY`, `BUY_NOW`, `HOLD`, `SELL`, and
  `NO_TRADE`.
- Every document and every action must carry a validity window. Pending
  `WAIT_BUY` orders from a previous document are canceled when the next accepted
  document supersedes them unless the new document explicitly renews the wait
  and deterministic gates still pass.
- `BUY_NOW` still means immediate limit-order attempt only when current quote,
  spread, freshness, reserve, holdings, and paper-only gates pass. It is not a
  market-order shortcut.
- `HOLD`, `SELL`, stop-loss, take-profit, and trailing-stop handling are checked
  continuously by the executor against realtime price/orderbook state; AI prose
  never bypasses the deterministic exit rules.
- Flash must read the latest **complete** Pro manifest that is finalized before
  the bucket cutoff. If the Pro manifest is missing, stale, incomplete, or
  fails hash validation, Flash writes `NO_TRADE` with a named reason instead of
  generating clean entry actions.
- Clean entry actions (`WAIT_BUY` / `BUY_NOW`) require both current portfolio
  and order-state refs. Missing, stale, unavailable, or advisory-only refs may
  produce watch/reject records, but cannot produce a clean
  `paper_order_intent/v0`.
- A clean `paper_order_intent/v0` must carry the authoritative refs that made it
  executable, not merely rely on the parent Flash document. Required intent-level
  refs are `flash_trade_document_ref`, `source_refs`, `market_data_refs`,
  `portfolio_snapshot_ref`, `order_state_snapshot_ref`, and
  `authoritative_refs_verified_at_kst`. The `input_refs` array must include
  those same source, market-data, portfolio, order-state, and Flash artifact refs
  so the executor can prove why the intent was accepted before it re-checks
  fresh state.

## 6. Deterministic IDs

| id | required shape | formula |
| --- | --- |
| `trade_doc_id` | `tdoc_` + 64 lowercase SHA-256 hex chars | `sha256(run_id + trading_date + decision_bucket_kst + input_manifest_hash)` |
| `intent_id` | `intent_` + 64 lowercase SHA-256 hex chars | `sha256(trade_doc_id + trade_action_id + ticker + side + normalized_order_rule_hash)` |
| `client_order_key` | `cok_` + 64 lowercase SHA-256 hex chars | `sha256(intent_id + execution_attempt_no)` |

Reprocessing the same `trade_doc_id` or `intent_id` is a no-op after the ledger
records consumption. Duplicate ids across a day are a P0 failure.

## 7. Portfolio, Reservation, And Conflict Rules

Flash portfolio context is advisory. Executor portfolio/order state is
authoritative.

The executor must acquire an account/symbol single-writer lock, re-read the
authoritative state, update the reservation ledger, and then submit at most one
paper request. It must reject conflicts for:

- held symbol duplicate buy;
- pending duplicate order;
- active stop/take-profit exit;
- cooldown;
- position lock;
- consumed trade document;
- still-valid prior decision;
- scale-in not explicitly authorized;
- reserved cash or holding-slot breach.

Reservation accounting must include `available_cash`, `reserved_cash`,
`settled_cash`, `pending_buy_cash`, `pending_sell_qty`, `open_holding_slots`,
and `reserved_holding_slots`. Cash reserve and max-holdings gates evaluate
worst-case fills of pending orders.

Durable execution storage must provide:

- write-ahead log before broker transport;
- unique constraints for `trade_doc_id`, `intent_id`, and `client_order_key`;
- account/symbol single-writer lock with expiry;
- transaction or fsync-backed append semantics;
- restart replay that reconciles `SUBMIT_UNKNOWN` before retry; and
- lock release only after fresh authoritative portfolio/order snapshots.

Until the DB-backed implementation unit defines a stronger backend, the
fallback file ledger must use append-only JSONL plus fsync and atomic manifest
publication. A partial file or missing manifest is non-executable.

## 7-1. Deterministic Sizing Formula

The sizing calculator is system-owned. AI may propose a sizing hint, but the
accepted `paper_order_intent/v0` quantity is computed from:

1. `risk_overlay_capital_krw` (baseline 2,000,000 KRW unless a future approved
   profile/unit change overrides it);
2. `minimum_cash_reserve_ratio` (baseline 0.25);
3. current available cash and already reserved pending-buy cash;
4. `max_order_cash_krw = min(action_cash_cap, risk_overlay_capital_krw *
   (1 - minimum_cash_reserve_ratio) - reserved_cash_before_order)`;
5. fresh limit-price source and KRX tick rounding rule; and
6. lot-size rounding with reject-if-below-min-lot behavior.

If computed quantity would breach reserve, holdings slots, stale price, or tick
rules, the intent is rejected before executor submission.

## 8. Freshness TTLs

| input class | max age / validity |
| --- | --- |
| portfolio/order state before broker submit | must be re-read within 5 seconds before submit |
| current price/quote | 5 seconds |
| realtime orderbook | 3 seconds when required; stale if heartbeat gap exceeds 10 seconds |
| REST ranking/analysis snapshot | 1-3 minute polling interval; stale after 180 seconds |
| Pro hourly artifact | current hour bucket plus 10-minute tolerance |
| Flash trade document | 10-minute decision window or its earlier `valid_until` |
| news/disclosure event | source timestamp required; not executable alone |
| calendar/session evidence | session check must be evaluated within 60 seconds before submit |

Expired inputs fail closed. The pipeline may write watch/reject/`NO_TRADE`
artifacts, but expired inputs cannot produce an executable paper order request.

## 9. Order State Machine

Allowed states and transitions are defined in the schema catalog. The important
runtime rule is:

- unknown broker submit results enter `SUBMIT_UNKNOWN`;
- retry is forbidden until KIS order/fill reconciliation proves no matching
  `client_order_key` or local intent metadata exists;
- illegal transitions become `ERROR_LOCKED` and require operator inspection.

## 10. Paper-Only Broker Guard

KIS broker transport is allowed only when all conditions pass:

- runtime label is `PAPER_ONLY`;
- broker adapter is `kis_paper`;
- base URL alias is `kis_paper_vts`;
- order route is KRX paper cash order;
- TR ID alias exists in the paper allowlist from the capability matrix;
- account identity is a redacted paper account alias, not a raw account number;
- startup self-test proves no live/unknown endpoint is configured.

Unknown/live domains, live profile names, raw account ids, unsupported TR IDs,
or unsupported NXT/SOR/integrated broker routes abort before network transport.

The guard must also record sanitized resolved host classes:

- `resolved_rest_base_url_alias = kis_paper_vts`;
- `resolved_rest_host_class = kis_paper`;
- `resolved_websocket_host_class = kis_paper`;
- `tr_id_allowlist_version`;
- `paper_account_alias` with raw account values redacted; and
- `live_domain_detected = false`, `unknown_domain_detected = false`.

## 10-1. Cancel Request Contract

`side = cancel` broker requests are executable only when they include:

- `cancel_target_request_id`;
- `cancel_target_client_order_key`;
- `cancel_target_broker_order_id_alias`;
- `cancel_reason`;
- `superseding_trade_doc_id`; and
- `cancel_deadline_kst`.

Cancels without target ids/reason/deadline are rejected before KIS transport.

## 11. Validation

Run:

```bash
source ./env.sh && python3 scripts/validate_runtime_contracts.py
```

The validator checks:

- all valid fixtures satisfy the catalog;
- all invalid fixtures fail with expected error classes;
- Flash action max is enforced;
- nested Flash action fields, source/market/portfolio refs, and action enums are
  enforced;
- Flash executable intent fields are false and `NO_TRADE` documents carry no
  actions;
- exact `tdoc_`, `intent_`, and `cok_` hash id patterns are enforced;
- source timestamp/dedupe/hash/watermark fields are required;
- KIS market snapshot payload, heartbeat, latency, rate-limit, raw-ref, and
  payload-hash fields are required;
- KIS, portfolio, and order snapshots must be fresh for executable inputs;
- broker requests are paper-only and include resolved host-class assertions;
- cancel requests include target refs/reason/deadline;
- deterministic sizing rejects reserve breaches;
- ambiguous submit results require reconciliation;
- partial publications without manifest are rejected;
- executor state transitions are legal;
- required ids and common metadata exist; and
- obvious secret-looking keys or values are rejected.
