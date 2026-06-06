---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-016
type: unit
domain: backend_ops
name: Runtime data and execution contract hardening
status: set
implementation_status: contract_defined
priority: P0
source_of_truth: gpt_pro_review
owner: hwi
updated_at: 2026-06-05
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-007
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-016_runtime-contract-hardening.md
evidence_refs:
  - docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md
  - docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md
contract_refs:
  - docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md
  - docs/contracts/hwistock-runtime-contracts.schema.json
fixture_refs:
  - docs/contracts/fixtures/runtime-contract-valid.json
  - docs/contracts/fixtures/runtime-contract-invalid.json
validation_command: source ./env.sh && python3 scripts/validate_runtime_contracts.py
---

# Runtime Data And Execution Contract Hardening

## 1. Goal

Close the P0 contract gaps identified during the 2026-06-05 ChatGPT Pro
external review before any order-producing Go row proceeds.

This unit does not place orders and does not call broker APIs. It defines the
machine-checkable contracts that UNIT-012, UNIT-013, and UNIT-014 must implement
or cite when they move to Go.

Current Set closure artifacts:

- `docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md`;
- `docs/contracts/hwistock-runtime-contracts.schema.json`;
- `docs/contracts/fixtures/runtime-contract-valid.json`;
- `docs/contracts/fixtures/runtime-contract-invalid.json`;
- `scripts/validate_runtime_contracts.py`.

Validation command:

```bash
source ./env.sh && python3 scripts/validate_runtime_contracts.py
```

## 2. Included Scope

- Define versioned JSON artifact schemas for:
  - `news_event/v0`;
  - `disclosure_event/v0`;
  - `kis_market_snapshot/v0`;
  - `pro_hourly_market_analysis/v0`;
  - `flash_trade_document/v0`;
  - `portfolio_snapshot/v0`;
  - `order_state_snapshot/v0`;
  - `paper_order_intent/v0`;
  - `executor_decision/v0`;
  - `broker_order_request/v0`;
  - `broker_order_result/v0`;
  - `reconciliation_event/v0`.
- Define required artifact metadata:
  - `schema_version`;
  - `run_id`;
  - `artifact_id`;
  - `source_id` or input refs;
  - `collected_at_kst`;
  - `source_published_at_kst` when source-provided;
  - `dedupe_key`, `source_hash`, `collection_watermark`, and
    `terms_policy_ref` for news/disclosure events;
  - `valid_until`;
  - `content_hash`;
  - validation status and error codes.
- Define deterministic identifiers:
  - `trade_doc_id` from trading date, 10-minute decision bucket, run id, and input manifest
    hash;
  - `intent_id` from trade doc id, trade action id, ticker, side, and normalized
    order rule;
  - broker `client_order_key` from intent id and execution attempt number.
  Each runtime id must use the full prefixed SHA shape:
  `tdoc_[0-9a-f]{64}`, `intent_[0-9a-f]{64}`, or `cok_[0-9a-f]{64}`.
- Define atomic artifact publication:
  - write to temp path;
  - fsync file and containing directory where supported;
  - atomic rename;
  - manifest or `READY` marker with byte size, hash, schema version, and
    completed timestamp.
- Define Flash failure behavior:
  - at most one finalized Flash artifact per 10-minute decision bucket;
  - valid trade documents contain at most five symbol actions;
  - action values are `WAIT_BUY`, `BUY_NOW`, `HOLD`, `SELL`, and `NO_TRADE`;
  - every document/action carries `valid_until`, and pending `WAIT_BUY` orders
    are canceled or explicitly renewed by the next accepted document;
  - invalid, timed-out, skipped, off-session, or model-unavailable ticks produce
    `NO_TRADE` sentinel artifacts with no executable intents.
  - Flash reads the latest complete Pro manifest before the cutoff or writes
    `NO_TRADE` with a named reason.
- Define portfolio/order conflict model:
  - Flash portfolio snapshots are advisory context only;
  - executor portfolio/order snapshots are authoritative at submit time;
  - final `paper_order_intent/v0` artifacts must carry their own
    Flash/source/KIS-market/portfolio/order refs and verification timestamp;
  - held symbols, pending orders, active exits, cooldowns, position locks,
    consumed trade docs, and still-valid prior decisions block conflicts unless
    deterministic strategy rules explicitly allow scale-in/exit behavior.
- Define reservation accounting:
  - `available_cash`;
  - `reserved_cash`;
  - `settled_cash`;
  - `pending_buy_cash`;
  - `pending_sell_qty`;
  - `open_holding_slots`;
  - `reserved_holding_slots`;
  - worst-case fill evaluation before accepting a new intent.
- Define executor ownership:
  - single-writer executor or transactional account/symbol locks;
  - append-only idempotency ledger;
  - replay of an already consumed trade document or intent is a no-op;
  - no parallel submission path may bypass the lock/ledger.
- Define order state machine:
  - `INTENT_CREATED`;
  - `GATE_REJECTED`;
  - `RESERVED`;
  - `SUBMITTING`;
  - `SUBMITTED_ACKED`;
  - `SUBMIT_UNKNOWN`;
  - `BROKER_REJECTED`;
  - `PARTIALLY_FILLED`;
  - `FILLED`;
  - `CANCEL_REQUESTED`;
  - `CANCELED`;
  - `EXPIRED`;
  - `RECONCILED`;
  - `ERROR_LOCKED`.
- Define ambiguous-submit handling:
  - write-ahead intent log before broker call;
  - after timeout/crash/unknown response, reconcile with KIS order/fill inquiry
    before retry;
  - retry only when broker evidence proves no matching order exists.
- Define freshness TTLs and fail-closed behavior for:
  - current price/quote;
  - orderbook/realtime ticks;
  - ranking/analysis snapshots;
  - Pro hourly artifacts;
  - Flash trade documents;
  - portfolio snapshots;
  - order-state snapshots;
  - news/disclosure events;
  - calendar/session evidence.
- Define adapter-bound broker guard:
  - broker-adapter account alias allowlist;
  - KIS broker-adapter base URL allowlist;
  - adapter-supported TR ID allowlist;
  - investment-mode broker order route allowlist: paper/mock KRX, real
    investment KRX/NXT where capability flags allow it, SOR disabled;
  - startup self-test;
  - resolved REST/WebSocket host-class assertions;
  - TR-ID allowlist version;
  - fatal abort on unapproved/unknown domain, operation profile, unsupported route, or
    missing adapter-mode evidence.
- Define cancel-request requirements:
  - target request id;
  - target client order key;
  - target broker-order alias;
  - cancel reason;
  - superseding trade document; and
  - cancel deadline.

## 3. Excluded Scope

- Broker network calls.
- DeepSeek provider calls.
- Account-affecting operation.
- Real account login.
- Credential reads or prints.
- Runtime strategy-risk parameter changes.
- Dashboard order controls.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result |
| --- | --- | --- | --- |
| AC-01 | P0 | Artifact schemas are explicit | Every artifact listed in scope has a schema name, required fields, validation errors, and owner unit. |
| AC-02 | P0 | Publication is atomic | Pro/Flash/executor artifacts define temp-write, fsync, atomic rename, and manifest/hash consumption rules. |
| AC-03 | P0 | Flash 10-minute document semantics are safe | Contract says at most one finalized artifact per 10-minute decision bucket and requires `NO_TRADE` sentinel on invalid/missing output. |
| AC-04 | P0 | Idempotency keys are deterministic | `trade_doc_id`, `intent_id`, and `client_order_key` formulas are documented and replay-safe. |
| AC-05 | P0 | Executor is single-writer or locked | Account/symbol locks and append-only idempotency ledger prevent duplicate submissions across restarts/replays. |
| AC-06 | P0 | Portfolio conflicts are deterministic | Held/pending/exiting/cooldown/lock/consumed-doc conflicts produce named reject codes before KIS submission. |
| AC-07 | P0 | Reservation accounting protects cash/slots | Pending buys/sells and reserved holding slots are included in cash reserve and max-holdings checks. |
| AC-08 | P0 | Order state machine is formal | Allowed order states, transitions, owning process, and recovery rules are defined. |
| AC-09 | P0 | Ambiguous broker submit is fail-safe | Unknown submit/crash paths require reconciliation before retry and cannot duplicate broker orders. |
| AC-10 | P0 | Freshness TTLs are explicit | Each input class has a TTL, source timestamp rule, and fail-closed behavior. |
| AC-11 | P0 | Adapter-bound guard is enforceable | Unknown/operation KIS domain/account/TR ID/route aborts before transport. |
| AC-12 | P0 | Failure-mode QA exists | QA covers duplicate docs, partial writes, stale inputs, conflicts, reservation breach, restart, KIS reject, partial fill, websocket disconnect, and operation misconfiguration. |
| AC-13 | P0 | Validator fixtures cover Pro findings | Invalid fixtures cover short deterministic ids, nested Flash action failures, missing refs, stale KIS/portfolio/order snapshots, bad adapter guard, cancel target gaps, reservation breach, partial publication, ambiguous submit, duplicate intent, and duplicate KIS snapshot sequence. |

## 5. Go Notes

This unit is a Set-hardening gate. UNIT-012, UNIT-013, and UNIT-014 must not
claim implementation readiness for order-producing behavior until this contract
is closed or explicitly superseded by a stronger profile/unit update.
