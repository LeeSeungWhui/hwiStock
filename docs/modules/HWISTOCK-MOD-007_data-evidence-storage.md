---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-007
type: module
domain: backend
name: Data and evidence storage
spec_status: set
build_status: go_check_passed
verification_status: go_check_passed
ready_set_rebaseline_status: go_check_passed
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-04
last_verified_at: 2026-06-04
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
links:
  - PROFILE-HWISTOCK
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-004
  - HWISTOCK-MOD-005
---

# Data And Evidence Storage

## 1. Purpose

This module owns durable storage of market-intelligence inputs, AI analysis,
candidate cards, orders, fills, positions, PnL calculations, and evidence
reports. The goal is to keep AI context, dashboard state, adapter testing, and
future operation-readiness review reproducible.

## 2. Product / Capability Contract

- Store data by date and type.
- Separate raw collected metadata, normalized events, AI analysis, candidate
  cards, order/fill logs, and reports.
- Use PostgreSQL as the first implementation database, matching the intended
  MyWebTemplate-style stack direction:
  - PostgreSQL is the queryable source of truth for normalized events,
    candidates, orders, fills, positions, daily PnL, reports, and evidence links
  - hwiStock must use its own PostgreSQL database/schema and must not share
    MyWebTemplate database names, schemas, migrations, or tables
  - append-only JSON/JSONL/Markdown artifacts under `data/` preserve raw source
    bundles, AI outputs, report snapshots, and operation evidence manifests
  - database rows must store artifact paths and content hashes so runtime state
    can be audited back to files
- Do not store credentials or private account identifiers in reports.
- Do not store full copyrighted article bodies unless source terms explicitly
  allow it. Store URL, title, source metadata, collected timestamps, content
  hash, permitted excerpts/summaries, and source ids instead.
- PnL numbers are calculated by the system, not by AI.
- AI may interpret PnL and candidate outcomes, but AI output must reference
  system-calculated fields instead of inventing or recalculating numbers.
- 07:00 morning reports synthesize overnight analysis artifacts.
- 20:00 daily reports combine system-calculated profit, loss, net PnL,
  fees/taxes when available, trade logs, AI candidate outcomes, and AI
  interpretation.
- Every adapter/operation-readiness claim must link named evidence.
- Artifact writes are append-only by default. Corrections create a new artifact
  with `supersedes_artifact_id`; they do not mutate historical trading or AI
  evidence silently.
- Secrets, API keys, raw account numbers, and private account identifiers are
  forbidden in artifacts and reports. Use redacted aliases such as
  `paper_account_alias`.
- Retain normalized events, AI artifacts, trading logs, reports, and evidence
  through the operator-selected adapter-backed observation gate. Long-term
  retention defaults to local-only until backup policy is explicitly selected.

## 3. Storage Backend

First implementation backend:

- PostgreSQL is required for the application store.
- Preferred isolation:
  - PostgreSQL database: `hwistock`
  - PostgreSQL schema: `hwistock_core`
  - application env var: `HWISTOCK_DATABASE_URL`
  - migrations must use the hwiStock schema explicitly or set `search_path` to
    `hwistock_core, public`
- `data/` is local runtime artifact storage and should not be committed by
  default.
- Files are immutable evidence snapshots for raw source payload metadata,
  permitted excerpts/summaries, AI outputs, Markdown reports, and daily
  manifests.
- PostgreSQL stores normalized rows, trading state, PnL, report metadata,
  artifact links, and dashboard query state.
- A future migration or audit job may rebuild selected database rows from file
  artifacts, but PostgreSQL is the normal runtime source for queries.
- SQLite is not part of the first implementation.

## 4. Required Paths

Use KST trading date partitioning. For non-trading-day news, use the local KST
date on which the artifact was collected.

- `data/raw/YYYY-MM-DD/news/*.json`
- `data/raw/YYYY-MM-DD/disclosures/*.json`
- `data/raw/YYYY-MM-DD/market-data/*.jsonl`
- `data/normalized/YYYY-MM-DD/events.jsonl`
- `data/ai/YYYY-MM-DD/deepseek-pro/hourly/HH00.json`
- `data/ai/YYYY-MM-DD/deepseek-flash/trade-documents/HHMM.json`
- `data/candidates/YYYY-MM-DD/*.json`
- `data/trading/YYYY-MM-DD/orders.jsonl`
- `data/trading/YYYY-MM-DD/fills.jsonl`
- `data/trading/YYYY-MM-DD/positions.jsonl`
- `data/trading/YYYY-MM-DD/pnl.json`
- `data/reports/YYYY-MM-DD/morning-0700.json`
- `data/reports/YYYY-MM-DD/morning-0700.md`
- `data/reports/YYYY-MM-DD/daily-close-2000.json`
- `data/reports/YYYY-MM-DD/daily-close-2000.md`
- `data/evidence/YYYY-MM-DD/paper-day.json`
- PostgreSQL database: logical name `hwistock`
- PostgreSQL schema: `hwistock_core`
- `docs/evidence/`

## 5. Common Artifact Fields

Every JSON/JSONL artifact must include:

- `schema_version`
- `artifact_id`
- `artifact_type`
- `created_at_kst`
- `trading_date`
- `environment`: `docs_only`, `backtest`, `paper`, `sandbox`,
  `live_readonly`, or `live_order`
- `source_ids` or `related_artifact_ids`
- `symbols`
- `redaction_status`
- `content_hash` when derived from an external source or generated bundle

Source-derived artifacts also include:

- `source_type`
- `source_name`
- `source_url`
- `collected_at_kst`
- `published_at_kst` when known
- `body_storage_policy`: `metadata_only`, `excerpt_allowed`,
  `summary_only`, or `full_body_allowed`
- `license_or_terms_note`

Trading-derived artifacts also include:

- `order_id` / `fill_id` / `position_id` where applicable
- `broker_adapter`: `no_order_dry_run`, `kis_paper`, `kis_live_readonly`, or
  `kis_live_order`
- `cash_amount_krw`
- `quantity`
- `price_krw`
- `fees_krw`
- `taxes_krw`
- `gross_pnl_krw`
- `net_pnl_krw`
- `calculation_source`: must be `system`

## 6. PostgreSQL Data Contract

The PostgreSQL schema should include tables or equivalent query surfaces for:

- `artifacts`: artifact id, type, path, date, environment, schema version,
  created time, hash
- `sources`: source id, source type, source name, URL, permission note
- `events`: normalized news/disclosure/market-data events
- `ai_outputs`: model, prompt id, source ids, candidate ids, confidence,
  output path
- `candidates`: symbol, reason, status, source ids, AI output ids
- `orders`
- `fills`
- `positions`
- `pnl_daily`
- `evidence_links`

The first implementation should use Alembic migrations rather than ad hoc table
creation. The database contract must remain explicit enough for dashboard,
report, and QA queries.

Isolation rules:

- Do not create hwiStock tables in a MyWebTemplate database/schema.
- Do not use MyWebTemplate migration history tables.
- Do not use unqualified table names in migrations unless `search_path` is
  explicitly controlled for hwiStock.
- Prefer schema-qualified names such as `hwistock_core.artifacts`.
- If a shared local PostgreSQL instance is used, hwiStock still gets its own
  database or at minimum its own schema and role.

## 7. Decisions / Open Questions

- Decision: storage uses PostgreSQL plus date-partitioned file artifacts.
- Decision: hwiStock uses separate PostgreSQL isolation from MyWebTemplate:
  database `hwistock`, schema `hwistock_core`, env var
  `HWISTOCK_DATABASE_URL`.
- Decision: date-based storage is required.
- Decision: raw/normalized/AI/candidate/trading/report/evidence artifacts are
  type-separated.
- Decision: full article bodies are excluded unless source terms allow storage.
- Decision: PnL is system-calculated and AI may only interpret referenced
  computed fields.
- Decision: SQLite is excluded from the first implementation.
- Decision: migrations use Alembic under `backend/migrations/` after backend
  implementation begins.
- Decision: first backup policy is local-only until the Postgres backup target
  and encryption policy are selected.
- Open: exact backup destination and encryption policy.
- Open: whether long-term retention should compress or archive artifacts after
  30/90/365 days.

## 8. Go-Check Implementation References

- `backend/lib/storage_schemas.py`: typed artifact contracts, deterministic
  SHA-256 hashing, KST date/path helper, redaction/sensitive-key checks,
  DailyPnL system-calculation validation, and adapter-day evidence linkage
  validation.
- `backend/lib/request_payload.py`: FastAPI-profile request payload helper names
  introduced before route implementation.
- `backend/migrations/`: Alembic skeleton using `HWISTOCK_DATABASE_URL`,
  schema `hwistock_core`, schema-qualified storage tables, and no
  MyWebTemplate/public table overlap.
- `backend/tests/test_storage_contract.py`: focused storage contract tests.
- `docs/evidence/RUN-20260604_unit-008-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md`
