---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-008
type: qa_scenario
name: Data and evidence storage QA
unit_refs:
  - HWISTOCK-UNIT-008
module_refs:
  - HWISTOCK-MOD-007
profile_refs:
  - PROFILE-HWISTOCK
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
owner: hwi
updated_at: 2026-06-04
evidence_refs:
  - docs/evidence/RUN-20260602_unit-008-data-evidence-storage-set.md
  - docs/evidence/RUN-20260604_unit-008-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md
---

# Data And Evidence Storage QA

## 1. Purpose

Prove that hwiStock's first storage implementation uses an isolated PostgreSQL
database/schema plus date-partitioned artifacts, while preserving auditable
links between sources, AI outputs, trading state, PnL, reports, and
operator-selected paper observation evidence.

## 2. Scope

In scope:

- PostgreSQL database/schema isolation from MyWebTemplate
- `HWISTOCK_DATABASE_URL` connection boundary
- migration/table contract
- date-partitioned runtime artifacts under `data/`
- artifact paths and hashes linked to PostgreSQL rows
- system-calculated PnL
- redaction and article-body storage policy
- operator-selected paper observation manifest linkage

Out of scope:

- broker network calls
- AI API network calls
- dashboard UI implementation
- cloud backup and remote replication
- live trading

## 3. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | contract | Inspect storage backend contract | PostgreSQL plus date-partitioned artifacts is selected; SQLite is not in scope | unit/module review |
| QA-002 | P0 | db-isolation | Inspect DB config and migrations | hwiStock uses database `hwistock`, schema `hwistock_core`, and `HWISTOCK_DATABASE_URL`; no MyWebTemplate DB/schema/migration overlap | config/migration review |
| QA-003 | P0 | path | Inspect artifact path contract | Raw, normalized, AI, candidate, reports, trading, and evidence files are separated by path | path/schema review |
| QA-004 | P0 | schema | Inspect common artifact schemas | Artifacts include id, type, KST timestamps, environment, source links, redaction status, and hashes where applicable | schema review |
| QA-005 | P0 | report | Generate or inspect daily close schema | Profit/loss/net PnL come from system calculation fields with `calculation_source: system` | report/schema review |
| QA-006 | P0 | evidence | Inspect paper observation evidence manifest | Each observation day can link source artifacts, AI outputs, candidates, trades, PnL, morning report, and daily close | evidence review |
| QA-007 | P0 | redaction | Inspect sample artifacts/reports | Credentials, API keys, raw account ids, and private account identifiers are absent or redacted | redaction review |
| QA-008 | P1 | audit | Inspect artifact-to-DB linkage | PostgreSQL rows store artifact id/path/hash and can be traced back to files | db/file review |
| QA-009 | P1 | copyright | Inspect source artifact storage policy | Article bodies are not stored unless source terms allow it; metadata/hash/summary policy is recorded | source artifact review |

## 4. PASS / FAIL / BLOCKED Rules

- PASS: PostgreSQL isolation is explicit, path/schema contracts exist, evidence
  links are auditable, PnL is system-calculated, and sensitive/copyrighted data
  policies are enforced.
- FAIL: hwiStock tables overlap MyWebTemplate schema/migrations, PnL is
  AI-calculated, evidence is not linkable, secrets are stored, or unsupported
  article bodies are retained.
- BLOCKED: PostgreSQL access/config is unavailable for implementation, database
  schema naming changes without Set approval, or storage backend is changed.

## 5. Evidence Requirements

- database/schema/migration review output
- env-name review showing project-specific `HWISTOCK_DATABASE_URL`
- path/schema review
- sample daily PnL schema or generated report
- sample paper-day evidence manifest
- redaction review
- artifact-to-DB linkage review

## 6. Current Go-Check Execution Matrix

Current evidence:
`docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md`.

| row_id | go_check_result | evidence |
| --- | --- | --- |
| QA-001 | PASS | PostgreSQL plus date-partitioned artifacts selected; SQLite excluded. |
| QA-002 | PASS | `HWISTOCK_DATABASE_URL`, database `hwistock`, and schema `hwistock_core` documented; migration skeleton is schema-qualified and does not use MyWebTemplate names. |
| QA-003 | PASS | `build_artifact_path` separates required raw, normalized, AI, candidate, trading, report, and evidence paths. |
| QA-004 | PASS | Typed artifact contracts include shared artifact fields and focused tests compile/instantiate the contract. |
| QA-005 | PASS | `DailyPnL` enforces `calculation_source: system`; migration adds a DB CHECK for system-only daily PnL. |
| QA-006 | PASS | `PaperDayEvidenceManifest` requires source, normalized, AI, candidate, order, fill, position, PnL, morning, and daily-close links. |
| QA-007 | PASS | Sensitive-key validation and marker grep found no actual KIS app key, secret, HTS id, or account number in UNIT-008 files. |
| QA-008 | PASS | Migration stores artifact id/path/hash/date/environment and child rows link through artifact foreign keys. Runtime DB writes are future scope. |
| QA-009 | PASS | `SourceArtifact` body storage policy blocks full bodies unless explicitly allowed. |
