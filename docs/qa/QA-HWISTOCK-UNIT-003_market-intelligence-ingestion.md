---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-003
type: qa_scenario
name: Market intelligence ingestion QA
unit_refs:
  - HWISTOCK-UNIT-003
module_refs:
  - HWISTOCK-MOD-002
profile_refs:
  - PROFILE-HWISTOCK
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
owner: hwi
updated_at: 2026-06-04
evidence_refs:
  - docs/evidence/RUN-20260602_unit-003-market-intelligence-set.md
  - docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md
---

# Market Intelligence Ingestion QA

## 1. Purpose

Prove that the 24-hour information ingestion branch can collect permitted public
market intelligence without violating source policy and without directly placing
orders.

## 2. Scope

In scope:

- source allowlist
- source registry status model
- source permission notes
- rate limiting
- deduplication
- chart/market-data source policy
- ingestion health
- event metadata evidence
- branch separation from trading
- blocked HTML scraping and broker data checks
- foundation-only fixture/config-first source mode

Out of scope:

- live trading
- strategy scoring
- broker order routing
- credential handling
- KIS broker network calls
- realtime quote/order-book integration

## 3. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | docs/config | Inspect `docs/sources/HWISTOCK-SOURCE-REGISTRY.md` | Every source has status, collection method, credential/env policy, and storage policy | config/doc |
| QA-002 | P0 | safety | Inspect ingestion output path | Ingestion cannot directly call order routing | architecture/code review |
| QA-003 | P0 | compliance | Inspect source policy notes | API/RSS/robots/terms/rate notes exist for each source | source ledger |
| QA-004 | P1 | data | Submit duplicate fixture events | Duplicate events collapse or link deterministically | test/log |
| QA-005 | P1 | health | Inspect ingestion health | Last fetch time, failures, and backlog are visible | health output |
| QA-006 | P1 | evidence | Generate ingestion summary | Summary lists source, count, duplicates, failures, and retention notes | evidence file |
| QA-007 | P1 | market-data | Inspect chart data config | Chart source, interval, OHLCV schema, venue, and latency budget are listed before chart signals are enabled | config/doc |
| QA-008 | P0 | blocked-source | Inspect source registry and implementation config | General media HTML scraping and unofficial finance APIs are disabled by default | config/source review |
| QA-009 | P0 | broker-boundary | Inspect source registry and implementation config | KIS/broker quote/news/realtime sources are deferred and cannot run in this unit | config/profile review |
| QA-010 | P1 | event-schema | Inspect normalized event schema | Required fields include source ids, timestamps, symbol/corp code, dedupe key, body storage policy, and candidate eligibility | schema review |
| QA-011 | P0 | network-boundary | Run first foundation Go smoke with source credentials absent/disabled | Fixture/config ingestion succeeds; live OpenDART, Naver, KIS/broker, KRX/KIND, unofficial API, and HTML scraping calls are not attempted | network/config log |

## 3-1. Go Smoke Mapping

Current Go smoke coverage lives in
`backend/tests/test_market_intelligence_ingestion.py`.

| row_id | Go coverage |
| --- | --- |
| QA-001 | `testQa001AndQa003SourceRegistryCarriesPolicyFields` validates source status, method, credential policy, storage policy, rate, terms, and retention fields. |
| QA-002 | `testQa002AndQa011NoNetworkEnvOrRoutingImports` inspects implementation imports for no broker/order/trading routing modules. |
| QA-003 | `testQa001AndQa003SourceRegistryCarriesPolicyFields` validates source permission/rate/terms notes. |
| QA-004 | `testQa004DuplicateFixtureEventsLinkDeterministically` verifies deterministic duplicate linking. |
| QA-005 | `testQa005AndQa006HealthAndSummaryExposeRequiredOperatorFields` checks last fetch, failures, backlog, source counts, duplicates, and disabled live sources. |
| QA-006 | `testQa005AndQa006HealthAndSummaryExposeRequiredOperatorFields` checks the returned summary dictionary. No runtime evidence file is written by ingestion. |
| QA-007 | `testQa007MarketDataContextFieldsAreDeclaredBeforeSignals` verifies venue, interval, OHLCV, and latency fields are declared while live chart sources remain disabled/deferred. |
| QA-008 | `testQa008AndQa009BlockedSourcesCannotIngestInFoundation` verifies HTML scraping and unofficial APIs are blocked. |
| QA-009 | `testQa008AndQa009BlockedSourcesCannotIngestInFoundation` verifies KIS/broker market/realtime/news data is deferred and cannot ingest. |
| QA-010 | `testQa010NormalizedEventSchemaContainsRequiredFields` verifies required normalized event fields and validation. |
| QA-011 | `testQa011FoundationSmokeSucceedsWithoutCredentialsOrNetwork` and `testQa002AndQa011NoNetworkEnvOrRoutingImports` prove fixture/config ingestion succeeds while live network/credential/order paths are absent. |

## 4. PASS / FAIL / BLOCKED Rules

- PASS: only approved fixture/config sources are collected in first foundation
  Go, rate/terms notes exist, duplicates are handled, blocked/deferred sources
  cannot run, chart source policy exists when chart signals are enabled, and
  ingestion cannot directly place orders.
- FAIL: unapproved scraping occurs, conditional/deferred sources run without Set
  approval, source policies are missing, broker network calls are made, or
  ingestion can invoke order routing.
- BLOCKED: no source allowlist exists.

## 5. Evidence Requirements

- source allowlist
- permission/rate-limit notes
- source registry review
- chart/realtime data source and latency notes when chart signals are enabled
- deduplication test/log
- ingestion health output
- summary evidence
- blocked-source review
- network/config proof that live OpenDART and all conditional/deferred sources
  remain disabled during first foundation Go

Current Go-Check evidence:

- `docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md`
- `python -m unittest backend.tests.test_market_intelligence_ingestion`
- `python -m unittest backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract`
- `python -m py_compile backend/lib/market_intelligence.py backend/service/market_intelligence_ingestion.py backend/tests/test_market_intelligence_ingestion.py`

## 6. Current Go-Check Execution Matrix

Current evidence:
`docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md`.

| row_id | go_check_result | evidence |
| --- | --- | --- |
| QA-001 | PASS | Source registry config entries expose status, method, credential policy, storage policy, rate, terms, retention, and body policy fields. |
| QA-002 | PASS | Import inspection confirms no broker/order/trading routing imports in UNIT-003 implementation modules. |
| QA-003 | PASS | Source policy notes and rate/terms text are present in the implementation config. |
| QA-004 | PASS | Duplicate disclosure fixtures link deterministically by dedupe key. |
| QA-005 | PASS | Health output exposes source counts, failures, backlog, disabled live sources, blocked source ids, duplicate links, and last fetch timestamps. |
| QA-006 | PASS | Summary dictionary exposes source counts, duplicate count, failures, disabled live sources, and retention notes without writing runtime evidence files. |
| QA-007 | PASS | Market-data context fields include venue, interval, OHLCV schema, and latency budget while live chart sources remain disabled/deferred. |
| QA-008 | PASS | General HTML scraping and unofficial finance APIs are blocked in foundation mode. |
| QA-009 | PASS | KIS/broker market/realtime/news source remains deferred and cannot ingest. |
| QA-010 | PASS | Normalized event schema includes all required UNIT-003 fields; validation rejects non-KST/ambiguous timestamps and caller body-policy overrides. |
| QA-011 | PASS | Foundation fixture smoke succeeds without credentials, network imports, live source calls, broker/KIS imports, or order-routing imports. |
