---
schema_version: hwi.evidence/v0
id: RUN-20260605-gpt-pro-findings-remediation
type: evidence
name: GPT Pro findings remediation
stage: go-check
environment: local_docs_validation
status: local_remediation_complete_pending_gpt_pro_re_review
owner: hwi
created_at: 2026-06-05
updated_at: 2026-06-05
current_authority: true
review_input_ref: docs/evidence/RUN-20260605_gpt-pro-current-docs-planning-review.md
repository_url: https://github.com/LeeSeungWhui/hwiStock
secret_values_shared: false
---

# GPT Pro Findings Remediation

## 1. Scope

This run applies the current-docs GPT Pro review findings recorded in
`docs/evidence/RUN-20260605_gpt-pro-current-docs-planning-review.md`.

No broker/order network call, DeepSeek provider call, live endpoint call,
credential readout, strategy-risk numeric change, or push was performed.

## 2. Fixes Applied

| review item | remediation |
| --- | --- |
| KIS source authority contradiction | `HWISTOCK-SOURCE-REGISTRY` now separates public market-intelligence sources from UNIT-013 KIS paper-read market-data authority and keeps KIS order endpoints forbidden in UNIT-013. |
| NXT/SOR/session ambiguity | Current docs now distinguish exchange/session context from broker-facing paper-order enablement. KRX public regular-session context is 09:00-15:30 KST; current KIS paper-order enablement is KRX-only 09:00-15:00 KST; NXT/SOR broker routes abort before transport. |
| Short deterministic ids | Runtime schema now requires `tdoc_[0-9a-f]{64}`, `intent_[0-9a-f]{64}`, and `cok_[0-9a-f]{64}` and valid fixtures use full prefixed hashes. |
| Weak nested schema/validator | Schema and validator now cover nested Flash actions, action refs, portfolio conflict fields, `NO_TRADE` conditions, paper guard host-class assertions, cancel-target refs, publication manifests, freshness, and deterministic sizing bounds. |
| Source freshness/dedupe gaps | News/disclosure schemas now require `source_event_id`, `source_published_at_kst`, `dedupe_key`, `source_hash`, `collection_watermark`, and `terms_policy_ref`. |
| Abstract KIS snapshot | `kis_market_snapshot/v0` now requires venue, as-of time, heartbeat, sequence, latency, rate-limit bucket, raw payload ref, redacted payload hash, and structured payload fields. |
| Pro/Flash race | Flash trade documents now require Pro artifact ref, manifest completion/cutoff timestamps, and `pro_manifest_status`; non-latest Pro manifests force `NO_TRADE`. |
| Missing portfolio/order context | Clean Flash entry actions require authoritative portfolio and order-state refs; missing/stale/unavailable refs may only produce watch/reject behavior. |
| Cancel request gaps | `broker_order_request/v0` cancel side requires target request id, target client order key, broker-order alias, reason, superseding trade doc, and cancel deadline. |
| Ledger/locks/crash recovery | Runtime contract now defines write-ahead log, unique constraints, single-writer account/symbol lock, lock expiry, fsync/transaction semantics, and `SUBMIT_UNKNOWN` replay/reconciliation. |
| Broker alias resolution | Paper-only guard now records sanitized resolved REST/WebSocket host classes, allowlist version, redacted paper alias, and live/unknown-domain false assertions. |
| Failure fixture coverage | Invalid fixture count expanded from 5 to 27, including short ids, stale snapshots, bad refs, bad guard, missing cancel targets, reservation breach, partial publication, ambiguous submit, duplicate intent, and duplicate KIS sequence. |
| Sizing ambiguity | Contract now defines system-owned sizing from 2,000,000 KRW risk-overlay capital, 0.25 reserve, pending reserved cash, max order cash, tick/lot rounding, and reject rules. |
| UNIT-011 paper-read exception | UNIT-011 evidence now records the explicit owner-approved KIS paper read/reconciliation exception with paper order submission disabled. |
| Calendar ambiguity | Calendar docs now separate KRX session truth from conservative internal paper-order enable window. |
| Historical terminology | Historical GPT review evidence is annotated: old `per market minute` / `NO_ACTION` wording is not current authority; current terms are 10-minute bucket and `NO_TRADE`. |
| Paper balance wording | Profile/index now state broker-visible paper balance is observed evidence only and does not expand the 2,000,000 KRW risk-overlay capital. |

## 3. Validation

Commands run:

```bash
source ./env.sh && python3 scripts/validate_runtime_contracts.py
```

Result:

```text
runtime_contract_validation=PASS
valid_artifacts=12
invalid_cases=27
schema_count=12
```

Command:

```bash
source ./env.sh && python3 -m pytest backend/tests/test_market_intelligence_ingestion.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_hwistock_runner.py
```

Result:

```text
58 passed
```

## 4. Pending

GPT Pro re-review is still pending for this remediation run. The re-review must
use the GitHub URL plus exact path list, and Codex must locally interpret the
advisory result before claiming closure.
