---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-008
type: unit
domain: backend
name: Data and evidence storage
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
priority: P0
source_of_truth: user_intent
work_class: product_api
owner: hwi
updated_at: 2026-06-04
last_verified_at: 2026-06-04
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-007
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md
evidence_refs:
  - run_id: RUN-20260602-unit-008-data-evidence-storage-set
    status: set
  - run_id: RUN-20260604-unit-008-go-preflight
    status: superseded_by_code_import
  - run_id: RUN-20260604-unit-008-go-check
    status: superseded_by_code_import
  - run_id: RUN-20260604-unit-008-go-preflight-rebaseline
    status: current
  - run_id: RUN-20260604-unit-008-go-check-rebaseline
    status: current
links:
  - HWISTOCK-MOD-007
---

# Data And Evidence Storage

## 1. Goal

Define how hwiStock stores raw collection metadata, normalized events, AI
analysis artifacts, candidate cards, order/fill logs, PnL calculations, and
daily evidence.

This unit sets the first implementation storage contract: PostgreSQL for the
queryable application store, plus date-partitioned local artifacts under
`data/` for raw source bundles, AI outputs, report snapshots, and evidence
manifests. hwiStock must use its own PostgreSQL database/schema so it does not
overlap with MyWebTemplate.

## 2. Included Scope

- Date-based storage structure.
- PostgreSQL data contract for dashboard/report/trading queries.
- PostgreSQL database/schema isolation from MyWebTemplate.
- Date-partitioned artifact layout.
- Hourly AI analysis files.
- 07:00 morning report.
- 20:00 daily close report.
- Candidate cards.
- Order/fill/position/PnL logs.
- Evidence paths for operator-selected paper observation windows.
- Redaction and article-body storage policy.
- Artifact-link and hash behavior between PostgreSQL rows and files.

## 3. Excluded Scope

- Credentials and private account identifiers.
- Raw copyrighted article bodies unless source terms allow it.
- Live-readiness claims without evidence.
- Cloud backup or remote replication.
- Broker network calls or order placement.
- Dashboard UI implementation.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | Backend is selected | PostgreSQL plus date-partitioned artifacts is documented as the first implementation backend | contract review | QA-001 |
| AC-02 | P0 | Database/schema is isolated | hwiStock uses database `hwistock`, schema `hwistock_core`, and `HWISTOCK_DATABASE_URL` without MyWebTemplate table/migration overlap | db config/migration review | QA-002 |
| AC-03 | P0 | Storage separates data types | Raw, normalized, AI, candidate, trading, report, and evidence artifacts are type-separated by path | path/schema review | QA-003 |
| AC-04 | P0 | Common artifact fields are required | Every artifact schema includes ids, dates, environment, source links, redaction status, and hash fields where applicable | schema review | QA-004 |
| AC-05 | P0 | PnL is system-calculated | 20:00 report references computed PnL fields, not AI-calculated numbers | report review | QA-005 |
| AC-06 | P0 | Evidence is linkable | Operator-selected paper observation windows can link each day to source, AI, candidate, trading, PnL, and report artifacts | evidence review | QA-006 |
| AC-07 | P0 | Secrets and private identifiers are excluded | Credentials, keys, raw account numbers, and private account ids are absent from artifacts | redaction review | QA-007 |
| AC-08 | P1 | Artifact links are auditable | PostgreSQL rows can be traced to artifact paths and content hashes | smoke/test output | QA-008 |
| AC-09 | P1 | Copyright-sensitive bodies are controlled | Source artifacts record body storage policy and avoid full article bodies unless allowed | source artifact review | QA-009 |

## 5. Required Directory Contract

Use KST dates.

| path | purpose |
| --- | --- |
| `data/raw/YYYY-MM-DD/news/*.json` | collected news metadata, permitted excerpts/summaries, source hashes |
| `data/raw/YYYY-MM-DD/disclosures/*.json` | collected disclosure metadata and source hashes |
| `data/raw/YYYY-MM-DD/market-data/*.jsonl` | raw permitted quote/candle/order-book bundles when source is approved |
| `data/normalized/YYYY-MM-DD/events.jsonl` | normalized source events used by AI and candidate generation |
| `data/ai/YYYY-MM-DD/deepseek-pro/hourly/HH00.json` | hourly aggregate source and market analysis; during market hours includes market-regime/session section |
| `data/ai/YYYY-MM-DD/deepseek-flash/trade-documents/HHMM.json` | one Flash trade document per market-minute; candidates list max 5 symbols and includes portfolio-conflict status |
| `data/candidates/YYYY-MM-DD/*.json` | candidate cards compiled from sources and AI outputs |
| `data/trading/YYYY-MM-DD/orders.jsonl` | order intents and order-state events |
| `data/trading/YYYY-MM-DD/fills.jsonl` | fill events from later approved KIS paper/live adapters only; no fake broker fills |
| `data/trading/YYYY-MM-DD/positions.jsonl` | position snapshots and transitions |
| `data/trading/YYYY-MM-DD/pnl.json` | system-calculated daily PnL |
| `data/reports/YYYY-MM-DD/morning-0700.json` | structured morning report |
| `data/reports/YYYY-MM-DD/morning-0700.md` | human-readable morning report |
| `data/reports/YYYY-MM-DD/daily-close-2000.json` | structured daily close report |
| `data/reports/YYYY-MM-DD/daily-close-2000.md` | human-readable daily close report |
| `data/evidence/YYYY-MM-DD/paper-day.json` | daily paper-run evidence manifest |
| PostgreSQL database `hwistock`, schema `hwistock_core` | normalized application store, trading state, PnL, report metadata, and dashboard query surface |

## 6. Required Schema Contracts

The first Go implementation must define JSON schemas or typed models for:

- `SourceArtifact`
- `NormalizedEvent`
- `AIAnalysisArtifact`
- `CandidateCard`
- `OrderEvent`
- `FillEvent`
- `PositionSnapshot`
- `DailyPnL`
- `MorningReport`
- `DailyCloseReport`
- `PaperDayEvidenceManifest`

Current rebaseline Go-Check implementation files:

- `backend/lib/storage_schemas.py`
- `backend/lib/request_payload.py`
- `backend/migrations/env.py`
- `backend/migrations/script.py.mako`
- `backend/migrations/versions/20260604_0001_create_hwistock_core_storage.py`
- `backend/tests/test_storage_contract.py`

Required shared fields:

- `schema_version`
- `artifact_id`
- `artifact_type`
- `created_at_kst`
- `trading_date`
- `environment`
- `source_ids` or `related_artifact_ids`
- `symbols`
- `redaction_status`
- `content_hash` when applicable

`DailyPnL` must include:

- `gross_profit_krw`
- `gross_loss_krw`
- `gross_pnl_krw`
- `fees_krw`
- `taxes_krw`
- `net_pnl_krw`
- `cash_start_krw`
- `cash_end_krw`
- `open_position_value_krw`
- `calculation_source: system`

## 7. PostgreSQL Contract

The first implementation should create migrations for these logical tables or
equivalent ORM models:

- `artifacts`
- `sources`
- `normalized_events`
- `ai_outputs`
- `candidate_cards`
- `order_events`
- `fill_events`
- `position_snapshots`
- `daily_pnl`
- `reports`
- `evidence_links`

Database isolation requirements:

- Use database `hwistock` by default.
- Use schema `hwistock_core`; do not create app tables in `public`.
- Use `HWISTOCK_DATABASE_URL` as the project-specific connection env var.
- Do not reuse MyWebTemplate database/schema names, migration tables, or seed
  data.
- Migrations must schema-qualify tables or explicitly set `search_path` to
  `hwistock_core, public`.
- If local development uses a shared PostgreSQL instance, hwiStock still gets a
  separate role/database/schema from MyWebTemplate.

Every row that is derived from a file artifact must include:

- `artifact_id`
- `artifact_path`
- `artifact_hash`
- `created_at_kst`
- `environment`

PostgreSQL is the runtime query source for dashboard and reports. File artifacts
preserve raw/auditable snapshots and can be used for audit or rebuild tooling,
but SQLite is not part of the first implementation.

## 8. Implementation Boundaries

- Do not call broker APIs.
- Do not call AI APIs.
- Do not create dashboard UI.
- Do not store `.env`, API keys, broker credentials, raw account ids, or
  sensitive private account values.
- Do not commit runtime `data/` artifacts by default; future Go should add an
  ignore policy if version control is initialized.
- Keep `docs/evidence/` for durable run summaries, not large raw runtime data.

## 9. Open Questions

- Exact backup destination and encryption policy.
- Compression/archive timing after paper test evidence is accepted.
- Decision: migrations use Alembic under `backend/migrations/` after backend
  implementation begins.

## 10. Go-Check Summary

UNIT-008 passed current-tree rebaseline Go-Check on 2026-06-04 for the local
storage skeleton scope.
The implementation defines typed artifact contracts, deterministic content
hashing, canonical KST date-scoped artifact paths, DailyPnL system-calculation
validation, a DB CHECK for system-only daily PnL, paper-day evidence linkage
validation, Alembic migration skeletons for `hwistock_core`, and focused
contract tests. No live DB connection, broker/API call, AI provider call,
dashboard UI, paper order, live order, credential storage, or runtime `data/`
artifact commit was performed.

Current evidence:

- `docs/evidence/RUN-20260604_unit-008-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md`

The earlier `RUN-20260604_unit-008-go-preflight.md` and
`RUN-20260604_unit-008-go-check.md` files remain historical after the
MyWebTemplate code import.
