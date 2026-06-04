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
owner: hwi
updated_at: 2026-06-03
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
