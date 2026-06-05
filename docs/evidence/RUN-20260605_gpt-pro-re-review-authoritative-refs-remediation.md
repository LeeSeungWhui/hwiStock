---
schema_version: hwi.evidence/v0
id: RUN-20260605-gpt-pro-re-review-authoritative-refs-remediation
type: evidence
name: GPT Pro re-review authoritative refs remediation
stage: go-check
environment: local_docs_validation
status: local_remediation_complete_pending_gpt_pro_re_review
owner: hwi
created_at: 2026-06-05
updated_at: 2026-06-05
current_authority: true
repository_url: https://github.com/LeeSeungWhui/hwiStock
reviewed_commit: 8e3549124d56512850b9f9f0ed980b474740dfbd
secret_values_shared: false
---

# GPT Pro Re-Review Authoritative Refs Remediation

## 1. Pro Re-Review Result

GPT Pro re-reviewed commit `8e3549124d56512850b9f9f0ed980b474740dfbd` through
GitHub raw/web access. It reported:

- P0: none.
- P1: final `paper_order_intent/v0` artifacts and validator logic under-enforced
  authoritative source/KIS-market/portfolio/order provenance refs at the intent
  layer.
- P2: `terms_policy_ref` wording in the source registry should match the event
  required fields.
- P2: `ops/systemd` runner files are no-order skeleton infrastructure and must
  not be treated as runtime-ready evidence.

## 2. Follow-Up Fixes

- `docs/contracts/hwistock-runtime-contracts.schema.json`
  - `paper_order_intent/v0` now requires:
    - `flash_trade_document_ref`;
    - `source_refs`;
    - `market_data_refs`;
    - `portfolio_snapshot_ref`;
    - `order_state_snapshot_ref`;
    - `authoritative_refs_verified_at_kst`.
- `scripts/validate_runtime_contracts.py`
  - Adds intent-level authoritative-ref validation.
  - Emits `paper_order_intent_authoritative_refs_missing` when final intent refs
    are absent, unavailable, weakly typed, or missing from `input_refs`.
- `docs/contracts/fixtures/runtime-contract-valid.json`
  - Valid `paper_order_intent/v0` carries final source, KIS market-data,
    portfolio, order-state, and Flash refs directly.
- `docs/contracts/fixtures/runtime-contract-invalid.json`
  - Adds `paper_order_intent_missing_authoritative_refs`.
- `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`
  - Aligns the source-level required metadata list with `terms_policy_ref`.
- `ops/systemd/hwistock-runner.service`
  - Explicitly labels the runner service as no-order scaffolding, not
    broker-adapter runtime-ready evidence.

## 3. Local Validation

```text
runtime_contract_validation=PASS
valid_artifacts=12
invalid_cases=28
schema_count=12
```

```text
python3 -m py_compile scripts/validate_runtime_contracts.py
PASS
```

```text
pytest backend/tests/test_market_intelligence_ingestion.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_hwistock_runner.py
58 passed
```

`git diff --check` passed.

## 4. Boundaries

- No KIS broker/API network call was made.
- No order, cancel, or modify call was made.
- No unapproved endpoint was called.
- No secret env/config file was read or printed.
- No strategy-risk numeric policy was changed.

## 5. Pending

Push this follow-up commit and request GPT Pro re-review using the GitHub URL and
the exact changed paths before claiming the Pro P1/P2 findings closed.
