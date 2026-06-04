---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-003-market-intelligence-set
type: evidence
name: UNIT-003 market intelligence ingestion Set pass
stage: set
environment: docs_only
status: set
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
unit_id: HWISTOCK-UNIT-003
unit_set_ready: true
go_allowed: false
---

# UNIT-003 Market Intelligence Ingestion Set Pass

## 1. Scope

This Set pass closes the first source-allowlist contract for hwiStock's
24-hour market intelligence branch.

The branch may collect market intelligence continuously, but it cannot place
orders, call broker APIs, or bypass strategy/risk gates.

## 2. Official Source Check

Checked current official/public source pages on 2026-06-02:

- OPENDART / DART Open API: official disclosure API source. The DART OpenAPI
  introduction says DART disclosure reports and major disclosure/financial
  information can be used through OpenAPI. The disclosure search guide provides
  list endpoints and request/response fields.
  - `https://opendart.fss.or.kr/intro/main.do`
  - `https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DE001&apiId=AE00001`
- KRX KIND: official Korea Exchange disclosure portal. It is registered as an
  official source candidate, but automated collection is deferred until
  source-specific terms/access checks are complete.
  - `https://kind.krx.co.kr/`
- KRX Data Marketplace: official KRX market-data portal. It is registered as a
  delayed/context-data candidate, but automated collection and market-data use
  are deferred until terms/access checks are complete.
  - `https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=ko`
- NAVER Developers Search API: official API source that includes news search
  results and publishes an API daily processing limit. It is conditional until
  credentials, query list, rate cap, and storage policy are approved.
  - `https://developers.naver.com/products/service-api/search/search.md`

## 3. Final Source Direction

Approved first Go:

- `dart_openapi_disclosures`: OPENDART / DART Open API.

Conditional after explicit approval:

- `naver_search_news_api`: NAVER Search API news, after
  `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, query list, rate cap, and storage
  policy are approved.
- `kind_krx_disclosure_portal`: after terms/access/method check.
- `krx_data_marketplace_delayed`: after terms/access/method check.

Deferred:

- `kis_market_or_realtime_data`: KIS/broker market/news/realtime data. This is
  broker network scope and belongs to the KIS API verification path.

Forbidden by default:

- `general_media_html_scrape`
- `unofficial_finance_apis`

## 4. Updated Documents

- `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`
- `docs/modules/HWISTOCK-MOD-002_market-intelligence-ingestion.md`
- `docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md`
- `docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/index.md`

## 5. Unit Closure

`HWISTOCK-UNIT-003` is Set-ready for a first implementation that builds:

- source registry loading
- DART disclosure fetcher
- dedupe
- normalized event storage
- ingestion health
- evidence output

The first implementation must not enable Naver, KIND, KRX Data Marketplace, KIS
broker feeds, general HTML scraping, or unofficial APIs until their status is
changed through a later Set decision.

## 6. QA Contract

`QA-HWISTOCK-UNIT-003` verifies:

- source registry completeness
- no direct order path
- source terms/rate notes
- deduplication
- ingestion health
- evidence summaries
- chart/market-data source policy
- blocked HTML scraping/unofficial APIs
- deferred broker data boundary
- normalized event schema

## 7. Verdict

UNIT-003 Set status: PASS

Implementation readiness for whole bundle: BLOCKED

Blocking condition: remaining Set units are not closed yet.
