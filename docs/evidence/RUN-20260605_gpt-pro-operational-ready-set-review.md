---
schema_version: hwi.evidence/v0
id: RUN-20260605-gpt-pro-operational-ready-set-review
type: evidence
name: GPT Pro operational Ready-Set review
stage: set
environment: chatgpt_pro_browser
status: historical_review_closed_by_unit_016_superseded_by_10m_rebaseline
owner: hwi
created_at: 2026-06-05
updated_at: 2026-06-05
current_authority: false
closed_by:
  - RUN-20260605-unit-016-runtime-contract-hardening-set
superseded_by:
  - RUN-20260605-owner-runtime-architecture-10m-trade-document-rebaseline
module_refs:
  - HWISTOCK-MOD-009
unit_refs:
  - HWISTOCK-UNIT-016
  - HWISTOCK-UNIT-012
  - HWISTOCK-UNIT-013
  - HWISTOCK-UNIT-014
profile_refs:
  - PROFILE-HWISTOCK
---

# GPT Pro Operational Ready-Set Review

Historical terminology note: this external review predates the owner-confirmed
10-minute Flash trade-document rebaseline. Any wording below that says "per
market minute" or `NO_ACTION` is historical review text; current authority uses
"at most one finalized Flash artifact per 10-minute decision bucket" and
`NO_TRADE` sentinel artifacts.

## 1. Review Route

- Tool route: Chrome extension browser runtime through `node_repl_http`.
- ChatGPT account state: logged in as a Pro account.
- Conversation title: `HwiStock Architecture Review`.
- Conversation URL: `https://chatgpt.com/c/6a222c2d-e0c0-83ec-85ff-5efde15f5c9a`.
- Prompt policy: advisory engineering/risk review only; no investment advice,
  no profit claims, no trading recommendations.
- Redaction: no credentials, account ids, secret files, env file contents, raw
  broker account values, or private config contents were sent.
- Shared material: sanitized architecture summary and local document paths only.

The first GPT response attempted to read/check external/local material and was
stopped. A follow-up instructed it to use only the provided architecture summary
and not browse or wait for attachments. The final response was copied from the
browser response action.

## 2. Prompt Summary

The sanitized prompt described:

- 24-hour free/public news/disclosure collection;
- KIS intraday market-data collection during market hours;
- DeepSeek Pro hourly aggregate analysis with market-regime/session analysis in
  the same hourly artifact;
- DeepSeek Flash every market minute writing one trade document whose candidate
  list contains at most five symbols;
- Flash reading latest Pro, new news/disclosures, KIS price/ranking/realtime
  snapshots, previous trade-document chain, and current portfolio/order-state
  snapshot;
- executor watching trade documents and submitting only KIS KRX paper/mock cash
  orders after deterministic gates; and
- live trading, credentials, AI direct broker calls, margin/credit/misu,
  hardcoded seven-day runtime, duplicate/conflicting positions, and portfolio
  conflicts as forbidden.

## 3. GPT Pro Verdict

GPT Pro verdict:

`Not implementation-ready for Go row-by-row yet. Needs another Set pass first.`

Condensed interpretation:

- Architecture direction is sound: Pro hourly, Flash per market minute,
  executor with deterministic gates, KIS paper/mock only, AI isolated from
  broker APIs, cash-only constraints, and same-artifact market-regime analysis
  are the right structure.
- Current design is still policy-rich and contract-thin.
- Next step must be a contract-hardening Set pass before order-producing Go.

## 4. Blocking Findings Accepted By Codex

| severity | accepted finding | required fix |
| --- | --- | --- |
| P0 | End-to-end data contract between collectors, Pro, Flash, executor, and KIS adapter is not explicit enough. | Define versioned schemas and required metadata for every cross-process artifact and snapshot. |
| P0 | Trade-document idempotency is under-specified. | Define deterministic `trade_doc_id`, `intent_id`, broker `client_order_key`, and append-only replay-safe ledger behavior. |
| P0 | Atomic file publication is not specified. | Require temp write, fsync, atomic rename, and manifest/hash/ready marker before downstream consumption. |
| P0 | "Exactly one trade document per minute" can overclaim during failures. | Redefine as at most one finalized artifact per market minute, with `NO_ACTION` sentinel artifacts for invalid/missing outputs. |
| P0 | Portfolio/order conflict gates are policy-level only. | Add single-writer executor or transactional account/symbol locks, plus authoritative executor snapshot before broker submission. |
| P0 | Cash reserve and max-holdings rules lack reservation accounting. | Track reserved cash, pending buy cash, pending sell quantity, open/reserved slots, and worst-case fills. |
| P0 | Ambiguous broker-submit failure path is missing. | Write intent log before submit, enter unknown state after timeout/crash, reconcile broker order/fill evidence before retry. |
| P0 | Formal order state machine is missing. | Define states, legal transitions, owning process, and recovery rules. |
| P0 | Freshness TTLs are not contractual. | Define TTLs and fail-closed behavior by input class: market, orderbook, Pro, Flash, portfolio, order state, source event, and session. |
| P0 | Live-trading prohibition is policy-level only. | Add paper/mock account allowlist, KIS paper URL allowlist, paper TR-ID allowlist, startup self-test, and fatal abort on live/unknown config. |
| P0 | Broker adapter capability map is incomplete for implementation readiness. | Record endpoint, websocket, order route, TR ID, account type, KRX-only flag, paper support status, fallback, and failure behavior. |
| P0 | AI prose could be confused with executable instruction. | Split analysis text from schema-validated executable intents; executor reads only validated executable fields. |
| P1 | Public-source terms, prompt-injection handling, websocket degradation, fill reconciliation, deterministic gate AC, rejection audit, order sizing, order type/price validation, runtime lifecycle, secret boundaries, and operator controls need explicit contracts. | Add source registry fields, untrusted input labels, heartbeat/stale flags, scheduled REST reconciliation, gate checklist, rejection codes, sizing rules, order validation, 24h service controls, secret scans, and operator modes. |
| P2 | Wording risks overclaiming "realtime" and "24h collection." | Use conditional wording: best-effort public-source collection and realtime only when paper-supported and health-checked fresh. |

## 5. Codex Response

Accepted. At review time, the operational Ready-Set was reclassified:

- previous state: `implementation_ready: true` for
  `operational_paper_trading_program_go_check_queue`;
- review-time state: `implementation_ready: false` and
  `blocked_until_runtime_contract_hardening_set_closes`.

The blocking findings were assigned to contract-hardening authority:

- `docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md`;
- `docs/qa/QA-HWISTOCK-UNIT-016_runtime-contract-hardening.md`.

Follow-up on 2026-06-05: UNIT-016 closed the Set-level runtime contracts in:

- `docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md`;
- `docs/contracts/hwistock-runtime-contracts.schema.json`;
- `docs/contracts/fixtures/runtime-contract-valid.json`;
- `docs/contracts/fixtures/runtime-contract-invalid.json`;
- `scripts/validate_runtime_contracts.py`;
- `docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md`.

Updated current-authority docs:

- `docs/profiles/PROFILE-HWISTOCK.md`;
- `docs/index.md`;
- `docs/modules/HWISTOCK-MOD-009_operational-paper-trading-program.md`;
- `docs/set/READY-SET-COMPLETION-20260605_operational-paper-trading-program_hwistock.md`;
- `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-paper-trading-program_hwistock.md`;
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-paper-trading-program_hwistock.md`.

## 6. Result

GPT Pro review completed and produced blocking findings.

Current correct status:

- `implementation_ready: true`;
- `implementation_ready_scope:
  operational_contract_hardened_go_check_queue`;
- `paper_run_ready: false`;
- `continuous_runner_ready: false`;
- `operational_trading_readiness: false`;
- `live_runner_ready: false`;
- `live_orders_enabled: false`.

Next required work is row-by-row Go/Check using the UNIT-016 contracts, not a
paper-run or live-ready claim. UNIT-012, UNIT-013, UNIT-014, and UNIT-015 still
need their own implementation and evidence before continuous paper trading can
be called ready.
