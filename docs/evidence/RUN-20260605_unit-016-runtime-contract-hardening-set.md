---
schema_version: hwi.evidence/v0
id: RUN-20260605-unit-016-runtime-contract-hardening-set
type: evidence
name: UNIT-016 runtime contract hardening Set
stage: set
environment: local_docs_validation
status: pass
owner: hwi
created_at: 2026-06-05
updated_at: 2026-06-05
current_authority: true
module_refs:
  - HWISTOCK-MOD-009
unit_refs:
  - HWISTOCK-UNIT-016
qa_scenario_refs:
  - QA-HWISTOCK-UNIT-016
profile_refs:
  - PROFILE-HWISTOCK
contract_refs:
  - docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md
  - docs/contracts/hwistock-runtime-contracts.schema.json
fixture_refs:
  - docs/contracts/fixtures/runtime-contract-valid.json
  - docs/contracts/fixtures/runtime-contract-invalid.json
validation_refs:
  - scripts/validate_runtime_contracts.py
gpt_pro_review_ref: docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md
---

# UNIT-016 Runtime Contract Hardening Set Evidence

## 1. Trigger

GPT Pro reviewed the owner-clarified hwiStock operational architecture and found
it directionally correct but not implementation-ready until hard runtime
contracts existed for schemas, idempotency, atomic publication, failure
sentinels, executor locking, reservation accounting, order state, freshness,
adapter-bound guard, and failure-mode QA.

## 2. Artifacts Created

- Contract document:
  `docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md`
- Machine-readable schema catalog:
  `docs/contracts/hwistock-runtime-contracts.schema.json`
- Valid fixture set:
  `docs/contracts/fixtures/runtime-contract-valid.json`
- Invalid/failure fixture set:
  `docs/contracts/fixtures/runtime-contract-invalid.json`
- Local validator:
  `scripts/validate_runtime_contracts.py`

## 3. Contract Coverage

The Set artifacts define:

- twelve versioned runtime artifact schemas:
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
  - `reconciliation_event/v0`;
- common artifact metadata and timestamp/hash rules;
- Flash at-most-one-finalized-artifact-per-10-minute-decision-bucket semantics;
- `NO_TRADE` sentinel behavior;
- max five Flash candidates per document;
- deterministic `trade_doc_id`, `intent_id`, and `client_order_key` formulas;
- atomic artifact publication requirements;
- portfolio/order conflict reject codes;
- reservation accounting fields;
- order state machine transitions;
- ambiguous `SUBMIT_UNKNOWN` submit handling;
- freshness TTLs; and
- KIS adapter-bound broker guard.

## 4. Validation

Command:

```bash
source ./env.sh && python3 scripts/validate_runtime_contracts.py
```

Result:

```text
runtime_contract_validation=PASS
valid_artifacts=12
invalid_cases=28
schema_count=12
```

The validator uses the standard library only. It checks required fields,
primitive types, const/enum/pattern/min/max rules, KST timestamps, Flash
candidate caps, nested Flash action refs, final adapter-order intent authoritative
refs, exact deterministic hash id patterns, `NO_TRADE` conditional behavior,
KIS snapshot/portfolio/order freshness,
adapter-bound broker request guards, cancel-target requirements, executor state
transitions, duplicate artifact ids/intent ids, deterministic sizing bounds,
ambiguous-submit reconciliation, publication-manifest completeness, and obvious
secret-like key/value leaks.

## 5. Accepted Invalid Cases

The invalid fixture set proves the validator blocks:

- missing `content_hash`;
- Flash documents with more than five candidates;
- Flash artifacts attempting to allow executable intents;
- unapproved/unknown broker request configuration;
- illegal order state transition;
- short `trade_doc_id`, `intent_id`, and `client_order_key` values;
- invalid Flash action enum and missing authoritative portfolio/order refs;
- `NO_TRADE` documents with actions or missing reason;
- final adapter-order intents missing source/KIS-market/portfolio/order refs;
- stale KIS/portfolio/order snapshots;
- missing source dedupe/hash/watermark fields;
- bad resolved KIS adapter host guard;
- cancel requests without target ids/reason/deadline;
- deterministic sizing/reservation breach;
- partial publication without manifest;
- ambiguous submit without reconciliation; and
- duplicate intent / duplicate KIS snapshot sequence collections.

## 6. Boundaries Preserved

- No KIS broker/API call was made.
- No DeepSeek provider call was made.
- No unapproved endpoint was called.
- No order was placed.
- No secret env/config file was read or printed.
- No strategy-risk numeric policy was changed.

## 7. Result

UNIT-016 Set: PASS.

The operational Ready-Set may now be reclassified from
`blocked_until_runtime_contract_hardening_set_closes` to a contract-hardened
Go-Check queue for UNIT-012, UNIT-013, UNIT-014, and UNIT-015.

This does not mean the program is operation-ready or operationally complete.
Actual collectors, AI runtime, intent pipeline, executor, KIS broker order
submission, reconciliation, and observation Prove still require Go/Check/Prove
evidence.
