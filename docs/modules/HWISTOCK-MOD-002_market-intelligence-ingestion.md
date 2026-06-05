---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-002
type: module
domain: backend
name: Market intelligence ingestion
spec_status: set
build_status: go_check_passed
verification_status: go_check_passed
ready_set_rebaseline_status: go_check_passed
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
completeness:
  status: set
  audit_ref: docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md
owner: hwi
updated_at: 2026-06-04
last_verified_at: 2026-06-04
source_inputs:
  - kind: user_prompt
    path_or_url: "인터넷 뉴스 기사 / 공시 같은 것 수집, 24시간"
    confidence: high
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  - backend/lib/market_intelligence.py
  - backend/service/market_intelligence_ingestion.py
  - backend/tests/test_market_intelligence_ingestion.py
entrypoints:
  - backend.service.market_intelligence_ingestion.ingestFixtureRows
interfaces:
  - backend.lib.market_intelligence.loadSourceRegistryConfig
  - backend.lib.market_intelligence.normalizeFixtureRow
  - backend.lib.market_intelligence.validateNormalizedEvent
  - backend.service.market_intelligence_ingestion.ingestFixtureRows
links:
  - PROFILE-HWISTOCK
  - HWISTOCK-MOD-001
  - docs/sources/HWISTOCK-SOURCE-REGISTRY.md
---

# Market Intelligence Ingestion

## 1. Purpose

This module owns the 24-hour information ingestion branch for `hwiStock`: news,
articles, disclosures, exchange/broker notices, chart/market-data context, and
other permitted public or licensed sources. It is separate from the trading/order
branch.

## 2. User Value / Representative Scenarios

- As the project owner, I can collect market-moving information continuously,
  including outside market hours.
- As a strategy reviewer, I can inspect what source produced a signal candidate.
- As an operator, I can pause or throttle ingestion without affecting kill switch
  controls for trading.

## 3. Scope

### Included

- Source allowlist.
- API/RSS-first ingestion policy.
- Crawling permission notes: robots/terms/rate limits where applicable.
- Deduplication and timestamp normalization.
- Disclosure/news event normalization.
- Chart/market-data context ingestion: OHLCV/candles, volume, price movement,
  and quote-derived indicators from approved data sources.
- Retention and audit evidence.
- Isolation from direct order placement.

### Excluded

- Direct order routing.
- Broker credential handling.
- Profit prediction claims.
- Scraping sources that disallow automated collection.
- Republishing copyrighted article bodies beyond permitted excerpts/metadata.

## 4. Product / Capability Contract

- The ingestion branch may run 24 hours.
- Each source must be explicitly allowed before implementation through
  `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`.
- Prefer official APIs, RSS feeds, public disclosure systems, or broker-provided
  feeds over generic scraping.
- First source allowlist:
  - OPENDART / DART Open API is approved for the first ingestion implementation.
  - Public news search RSS metadata is approved for the first live collector
    path without API keys. It stores feed metadata and RSS summaries/excerpts
    only and must not crawl article bodies, login pages, paywalled pages, or
    general HTML pages.
  - NAVER Developers Search API news is conditionally allowed only after API
    credentials, query list, rate cap, and storage policy are approved.
  - KRX KIND and KRX Data Marketplace are registered as official sources, but
    automated collection is deferred until source-specific terms/access checks
    are complete.
  - KIS market/realtime/news APIs are deferred to KIS API verification and
    broker-network approval.
  - General media HTML scraping and unofficial finance APIs are forbidden by
    default.
- Prefer raw market-data fields over chart-image scraping. Rendered chart images
  are visualization only; OHLCV, tick, quote, and volume data are the source of
  truth for chart signals.
- Store source URL/id, collected_at, published_at when available, title/summary,
  source name, and deduplication key.
- Store market-data timestamp, venue, symbol, interval, OHLCV, volume spike
  metrics, and data-latency status when chart data is used.
- Do not store secrets or private account data.
- Ingestion output may create candidate events/signals, but must not directly
  place orders.

## 4-1. Contract Surface Map

| surface | names / paths / ids | behavior owned | out of scope | evidence needed |
| --- | --- | --- | --- | --- |
| source registry | `backend.lib.market_intelligence.loadSourceRegistryConfig` | allowed sources and limits | unapproved sources | config review |
| crawler/fetcher | `backend.service.market_intelligence_ingestion.ingestFixtureRows` | fixture-only metadata/events | direct trading/live fetch | logs/tests |
| disclosure source | DART first; KIND conditional | public disclosure events | private data | source evidence |
| news source | Public RSS metadata approved; Naver Search API conditional; general HTML scraping forbidden | news/article metadata and permitted RSS summaries/excerpts | full article copying beyond allowed policy | source evidence |
| chart data source | KRX delayed conditional; KIS realtime deferred | candles/OHLCV/volume/latency | chart image scraping | data evidence |
| event bus/store | future store | normalized candidate events | orders | data review |

## 5. Interfaces

Current rebaseline Go-Check implementation interfaces:

- `backend.lib.market_intelligence.loadSourceRegistryConfig`: deterministic
  foundation source registry/config model.
- `backend.lib.market_intelligence.normalizeFixtureRow`: in-memory fixture row
  normalization into the required UNIT-003 event schema.
- `backend.lib.market_intelligence.validateNormalizedEvent`: normalized event
  schema and foundation-boundary validation.
- `backend.service.market_intelligence_ingestion.ingestFixtureRows`: fixture-only
  ingestion orchestration returning events, summary, and health dictionaries.

The current MyWebTemplate-derived backend now contains these files again after
the 2026-06-04 UNIT-003 rebaseline Go-Check.

Future interfaces may include:

- live fetch scheduler after explicit source approval
- dedupe store
- normalized event store
- chart/market-data adapter after source terms/access approval
- downstream strategy signal input that still cannot place orders directly
- ingestion health API output

## 6. State / Data / Permission Rules

- Source allowlist is required before implementation.
- Source registry is `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`.
- Retention default: keep normalized events, source metadata, and summaries
  through the operator-selected paper/sandbox observation gate. Longer retention
  and compression remain storage-policy questions.
- Copyright/terms handling is source-specific. Full article body storage is
  forbidden unless the registry explicitly allows it.
- News/disclosure/chart events must be labeled as informational until
  strategy/risk layers evaluate them.

## 7. Existing Assets / Reuse Points

- Historical UNIT-003 Go added a stdlib-only fixture/config-first implementation
  under `backend/lib/` and `backend/service/`. The current rebaseline Go-Check
  reintroduced that surface into the MyWebTemplate-derived backend skeleton.
- The current implementation uses no network client, broker adapter, order
  router, AI provider, or credential loader.

## 8. Module-Level Verification

- Source allowlist exists.
- Rate limit and robots/terms notes exist for crawled sources.
- Deduplication behavior is testable.
- Chart source, interval, latency, and OHLCV schema are testable when chart
  signals are enabled.
- Ingestion output cannot directly call order routing.

## 9. Included Units

- `HWISTOCK-UNIT-003`: 24-hour market intelligence ingestion foundation
  implementation.

## 10. Decisions / Open Contract Questions

- Decision: market intelligence ingestion is a separate 24-hour branch.
- Decision: ingestion cannot directly place orders.
- Decision: news/disclosure and chart/market-data context should both feed
  candidate generation, but neither can bypass strategy/risk checks.
- Decision: chart signals must use approved raw market data, not scraped chart
  images.
- Decision: OPENDART / DART Open API is the first approved disclosure source.
- Decision: no-key public RSS news metadata search is approved for first live
  collection when it stores metadata/excerpts only and does not crawl article
  bodies.
- Decision: NAVER Search API news is conditional after key/query/rate approval.
- Decision: KIND/KRX are official source candidates but automated collection is
  deferred until terms/access checks are complete.
- Decision: general HTML scraping and unofficial finance APIs are blocked by
  default.
- Open: exact query list for news collection.
- Pending approval: first-pass chart data source, realtime quote source, and
  candle intervals are packaged in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`. Broker
  data calls remain disabled until later explicit broker-network approval.

## 10-1. Completeness Audit

| coverage_area | status | notes | blocks_unit_set |
| --- | --- | --- | --- |
| source inventory | set | source registry added | no |
| actors and roles | sufficient | owner/operator/reviewer | no |
| entrypoints | go_check_passed | fixture/config-first interfaces were reintroduced into the imported backend skeleton during UNIT-003 rebaseline Go-Check | no |
| behavior contract | set | allowlist and forbidden sources defined | no |
| state and data | set | event fields and storage refs defined | no |
| permissions | set | per-source status model defined | no |
| design basis | minimal_exception | no UI yet | no |
| invariants | sufficient | no direct order placement | no |
| verification families | set | QA scenario updated for source registry | no |

## 11. Evidence References

- `docs/evidence/RUN-20260602_unit-003-market-intelligence-set.md`
- `docs/evidence/RUN-20260604_unit-003-go-preflight.md`
- `docs/evidence/RUN-20260604_unit-003-go-check.md`
- `docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md`

## 11-1. Go-Check Summary

UNIT-003 passed current-tree rebaseline Go-Check on 2026-06-04 for the local
market-intelligence ingestion skeleton scope. The implementation defines a
deterministic source registry, fixture-only event normalization, duplicate
linking, summary/health output, blocked-source enforcement, KST `+09:00`
timestamp validation, registry-controlled body storage policy, and focused
tests. No live source API call, broker/KIS call, AI provider call, order
placement, credential read, runtime scheduler, runtime artifact write, server
operation, browser QA, or deploy was performed.

Current evidence:

- `docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md`

## 12. Design References

- None.
