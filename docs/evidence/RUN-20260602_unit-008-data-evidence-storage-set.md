---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-008-data-evidence-storage-set
type: evidence
name: UNIT-008 data/evidence storage Set pass
stage: set
environment: docs_only
status: set
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
unit_id: HWISTOCK-UNIT-008
unit_set_ready: true
go_allowed: false
---

# UNIT-008 Data/Evidence Storage Set Pass

## 1. Scope

This Set pass closes the first storage-backend decision for hwiStock.

The storage direction is:

- PostgreSQL for the queryable application store.
- hwiStock-specific database/schema isolation from MyWebTemplate.
- Date-partitioned local artifacts under `data/` for raw source bundles, AI
  outputs, report snapshots, and paper-run evidence manifests.
- System-calculated PnL only. AI may interpret referenced PnL fields but must
  not calculate profit/loss numbers.

## 2. Final Storage Decision

Selected backend:

- PostgreSQL database: `hwistock`
- PostgreSQL schema: `hwistock_core`
- Project-specific env var: `HWISTOCK_DATABASE_URL`

Isolation requirements:

- Do not share MyWebTemplate database names, schemas, migrations, tables, or
  seed data.
- Do not create hwiStock application tables in `public`.
- Migrations must schema-qualify tables or explicitly set `search_path` to
  `hwistock_core, public`.
- If the same local PostgreSQL instance is reused, hwiStock still gets a
  separate database/schema/role boundary.

## 3. Corrected Direction

During this Set pass, an initial local-only SQLite index direction was rejected
by the user. The corrected direction is PostgreSQL, because MyWebTemplate also
uses PostgreSQL as a default stack pattern and hwiStock should align with that
runtime shape while keeping a separate database/schema.

SQLite is not part of the first implementation.

## 4. Updated Documents

- `docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md`
- `docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md`
- `docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/index.md`
- `docs/evidence/RUN-20260602_ready-set-architecture.md`

## 5. Unit Closure

`HWISTOCK-UNIT-008` is Set-ready as a storage contract.

Go is still not globally allowed because the overall Ready-Set bundle has not
yet reached `implementation_ready: true`. The broader bundle still needs Set
closure for source allowlist, AI schemas/cost caps, trading engine state,
KIS API verification, home-server runner shape, and dashboard access/design.

## 6. QA Contract

`QA-HWISTOCK-UNIT-008` now verifies:

- PostgreSQL backend selection.
- hwiStock database/schema isolation.
- `HWISTOCK_DATABASE_URL` usage.
- artifact path separation.
- common artifact fields.
- system-calculated PnL.
- one-week paper evidence linkability.
- redaction of secrets/private identifiers.
- artifact-to-DB path/hash traceability.
- article-body storage policy.

## 7. Verdict

UNIT-008 Set status: PASS

Implementation readiness for whole bundle: BLOCKED

Blocking condition: remaining Set units are not closed yet.
