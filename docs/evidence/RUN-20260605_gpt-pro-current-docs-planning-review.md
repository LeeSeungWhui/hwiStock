---
schema_version: hwi.evidence/v0
id: RUN-20260605-gpt-pro-current-docs-planning-review
type: external_review_evidence
name: GPT Pro current docs planning review
status: completed
current_authority: true
created_at: 2026-06-05
reviewer_route: chatgpt_pro_browser
review_scope: current_docs_planning
repository_url: https://github.com/LeeSeungWhui/hwiStock
repository_commit: 2ab58fc85f6fb9d5bc3b1cdf0f14fbef942bad7e
advisory_only: true
secret_values_shared: false
---

# GPT Pro Current Docs Planning Review

## 1. Review Packet

Codex sent GPT Pro a path-scoped review packet with the GitHub repository URL
and explicit review paths, rather than an unscoped full-repo prompt.

Primary paths included:

- `AGENTS.md`
- `docs/index.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/set/READY-SET-COMPLETION-20260605_operational-paper-trading-program_hwistock.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-paper-trading-program_hwistock.md`
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-paper-trading-program_hwistock.md`
- `docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md`
- `docs/contracts/hwistock-runtime-contracts.schema.json`
- `docs/contracts/fixtures/runtime-contract-valid.json`
- `docs/contracts/fixtures/runtime-contract-invalid.json`
- `docs/modules/HWISTOCK-MOD-008_continuous-paper-runtime.md`
- `docs/modules/HWISTOCK-MOD-009_operational-paper-trading-program.md`
- `docs/units/HWISTOCK-UNIT-011_operational-runtime-supervisor.md`
- `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md`
- `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
- `docs/units/HWISTOCK-UNIT-014_kis-paper-order-execution-reconciliation.md`
- `docs/units/HWISTOCK-UNIT-015_operator-console-observation-prove.md`
- `docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md`
- `docs/qa/QA-HWISTOCK-UNIT-011_operational-runtime-supervisor.md`
- `docs/qa/QA-HWISTOCK-UNIT-012_ai-analysis-runtime.md`
- `docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
- `docs/qa/QA-HWISTOCK-UNIT-014_kis-paper-order-execution-reconciliation.md`
- `docs/qa/QA-HWISTOCK-UNIT-015_operator-console-observation-prove.md`
- `docs/qa/QA-HWISTOCK-UNIT-016_runtime-contract-hardening.md`
- `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`
- `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`
- `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`
- `docs/evidence/RUN-20260605_owner-runtime-architecture-10m-trade-document-rebaseline.md`
- `docs/evidence/RUN-20260605_ready-set-operational-paper-trading-program.md`
- `docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md`
- `docs/evidence/RUN-20260605_unit-011-runtime-start-go.md`
- `docs/evidence/RUN-20260605_kis-paper-mock-api-runtime-recheck.md`
- `docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md`

GPT reported that GitHub raw documents were partially accessible, but a local
clone attempt failed due DNS. It still produced a path-cited review against the
listed GitHub docs and the supplied current-state summary.

## 2. GPT Pro Verdict

GPT Pro verdict:

`ready with conditions for row-by-row Go-Check implementation of UNIT-012/013/014/015, but not paper-run-ready`

Interpretation:

- The docs are coherent enough to continue row-by-row Go-Check after UNIT-016.
- The docs correctly keep `paper_run_ready`, `continuous_runner_ready`, and
  `operational_trading_readiness` false.
- UNIT-016 closes earlier architecture-level P0 gaps at Set/planning level, but
  not runtime-proof level.
- UNIT-013/014 must not enable unattended paper orders until the remaining
  P0/P1 fixes are resolved and proven.

## 3. Findings Summary

| severity | scope | finding | recommended fix |
| --- | --- | --- | --- |
| P0 before UNIT-013 Go | `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`, `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md` | KIS market/realtime data authority is contradictory: the source registry still marks KIS market/realtime data deferred while UNIT-013 scopes KIS WebSocket and REST market-data collectors. | Split public market-intelligence sources from KIS paper-read market-data sources, and add an explicit UNIT-013 paper-read-pending-proof status while keeping order calls forbidden in UNIT-013. |
| P0 before paper order enablement | `docs/index.md`, `docs/profiles/PROFILE-HWISTOCK.md`, `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`, `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` | NXT/SOR/session wording is stale and could imply broker-facing NXT routing even though KIS paper orders are KRX-only. | Normalize current-authority docs: analysis may annotate KRX/NXT session context, but broker-facing paper orders are KRX-only and NXT/SOR broker routes abort before transport. |
| P0 before paper order enablement | `docs/contracts/hwistock-runtime-contracts.schema.json`, `docs/contracts/fixtures/runtime-contract-valid.json` | Deterministic ID formulas are SHA-256 in prose, but schema/fixtures allow short toy IDs. | Require full hash patterns such as `tdoc_[0-9a-f]{64}`, `intent_[0-9a-f]{64}`, and `cok_[0-9a-f]{64}` and add invalid short-ID fixtures. |
| P0 before paper order enablement | `docs/contracts/hwistock-runtime-contracts.schema.json`, `docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md` | Schema catalog is not strong enough as final runtime enforcement for nested Flash actions, portfolio conflict, paper-only guard, and conditional `NO_TRADE`. | Tighten nested schema constraints or state that `scripts/validate_runtime_contracts.py` is authoritative, then add checks for action enum, ticker pattern, `NO_TRADE`, nested paper guard values, and source/market/portfolio refs. |
| P1 | contracts/source registry | News/disclosure freshness and dedupe fields are inconsistent across source registry and event schemas. | Require source-published timestamp, source event id, dedupe key, source hash, collection watermark, and terms policy ref. |
| P1 | KIS market snapshot contract | `kis_market_snapshot/v0` is too abstract for downstream trading gates. | Add per-kind payload specs for price, orderbook, realtime trade, ranking, bars, heartbeat, latency, rate-limit state, and raw payload hash/ref. |
| P1 | Pro/Flash scheduling | Top-of-hour Pro/Flash race behavior is not deterministic enough. | Flash must read the latest complete Pro manifest before cutoff; otherwise write `NO_TRADE` with a named reason. |
| P1 | Flash portfolio/order-state inputs | UNIT-012 says previous trade-doc chain or portfolio/order snapshot, while schema appears to require both refs. | Define that clean trade actions require portfolio/order context; missing context becomes `NO_TRADE` or watch-only. |
| P1 | cancel requests | Cancel order contract lacks original order refs and cancel reasons. | Require original request/client/broker aliases, cancel reason, superseding trade doc id, and cancel deadline. |
| P1 | ledger/locks | Append-only ledger and locks are required but backend/transaction semantics are not defined. | Define DB or file ledger, unique constraints, transaction isolation, lock expiry, crash recovery, and reconciliation replay. |
| P1 | paper-only guard | Broker alias is not enough unless resolved REST/WebSocket host class is proven. | Add startup assertion with sanitized resolved host class, TR-ID allowlist version, account alias, and `PAPER_ONLY` label. |
| P1 | UNIT-016 evidence | UNIT-016 evidence validates 5 invalid fixture cases while QA-016 lists many more P0 failure modes. | Expand invalid fixtures/tests for stale market, stale portfolio, duplicate intent, reservation breach, partial write, websocket stale/duplicate, KIS reject, partial fill, and ambiguous submit replay. |
| P1 | sizing | Position sizing is not deterministic enough. | Define system-owned sizing formula for risk overlay capital, reserve, pending cash, max order cash, tick/lot rounding, and reject rules. |
| P1 | UNIT-011 scope | UNIT-011 preflight was local-only by default, but evidence shows KIS paper read/reconciliation timers ran with orders disabled. | Amend evidence/preflight to record an explicit owner-approved paper-read/reconciliation exception with order endpoint disabled and no live domain. |
| P1 | market calendar | Calendar doc says KRX 09:00-15:00; KRX public regular session is 09:00-15:30 unless this is an intentionally conservative internal order window. | Rename to internal order window or update exchange session truth with separate order-enable policy. |
| P2 | terminology | Historical/current evidence still contains per-minute and `NO_ACTION` wording after the architecture moved to 10-minute Flash and `NO_TRADE`. | Replace or annotate as historical; current wording is 10-minute decision bucket and `NO_TRADE`. |
| P2 | capital wording | 2,000,000 KRW live/risk-overlay capital and paper/mock budget language can be misread. | Standardize that risk-overlay capital is 2,000,000 KRW unless approved otherwise; broker paper balance is observed only. |

## 4. Must Fix Before Paper-Run

- Normalize KIS market-data source status for UNIT-013 paper-read authority
  while keeping order calls forbidden.
- Normalize NXT/SOR/session wording: KIS paper orders are KRX-only; NXT/SOR
  broker routes abort.
- Tighten deterministic ID patterns and fixtures.
- Add nested schema constraints for Flash actions, paper guard, cancel requests,
  and `NO_TRADE`.
- Add source-published timestamps, dedupe keys, source hashes, and watermarks.
- Define exact Pro/Flash top-of-hour cutoff behavior.
- Define durable ledger storage, locks, uniqueness constraints, and crash
  recovery.
- Add broker alias resolution guard for actual REST/WebSocket host classes.
- Add deterministic sizing/quantity formula.
- Expand failure fixtures/tests beyond the current invalid fixture subset.
- Prove restart, duplicate replay, ambiguous submit, partial fill/reject,
  websocket stale, and `WAIT_BUY` cancellation.
- Configure and prove market calendar/source gates.
- Keep `paperOrderEnabled=false` until UNIT-014 order-specific Go/Prove
  explicitly enables it.

## 5. Deferrable Until Live Readiness

- NXT/SOR live brokerage support confirmation.
- Live account login, live endpoint allowlist, and live TR-ID matrix.
- Full live order-route parity testing.
- External alerts such as Telegram/email/Discord/SMS.
- Public/LAN dashboard exposure or authenticated remote access.
- Advanced daily account-level risk policies unless the owner wants them before
  paper-run.
- Live tax/fee/PnL reconciliation against broker statements.

## 6. Codex Acceptance

Codex accepts the review as advisory external Check input. The review does not
claim paper-run readiness or live readiness. No docs fixes from this review have
been applied in this evidence step.
