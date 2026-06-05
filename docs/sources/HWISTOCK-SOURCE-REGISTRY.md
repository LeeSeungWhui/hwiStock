---
schema_version: hwi.source-registry/v0
id: HWISTOCK-SOURCE-REGISTRY
type: source_registry
name: hwiStock market intelligence source registry
status: set
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-05
unit_refs:
  - HWISTOCK-UNIT-003
  - HWISTOCK-UNIT-002
  - HWISTOCK-UNIT-013
module_refs:
  - HWISTOCK-MOD-002
  - HWISTOCK-MOD-001
---

# hwiStock Market Intelligence Source Registry

## 1. Policy

This registry is the first source allowlist for the 24-hour market intelligence
branch.

Default policy:

- Prefer official APIs, official RSS feeds, and licensed data products.
- Do not scrape general HTML pages by default.
- Do not store full copyrighted article bodies unless a source-specific policy
  explicitly allows it.
- Store source metadata, URLs, ids, timestamps, hashes, permitted summaries, and
  source-derived event fields.
- Source outputs may create candidate events, but cannot directly invoke order
  routing.
- Public market-intelligence sources and KIS paper-read market-data sources are
  separated. KIS market-data reads may be implemented only inside the explicit
  UNIT-013 paper-read scope; KIS order calls remain forbidden there.

## 2. Source Status Values

- `approved_first_go`: may be implemented in the first ingestion unit.
- `conditional_after_key`: allowed only after explicit API-key/config approval.
- `conditional_after_terms_check`: source is official, but implementation must
  first record terms, rate, and access method.
- `approved_unit_013_paper_read_pending_proof`: broker API market-data read
  source is allowed only for UNIT-013 Go-Check with paper/mock credentials,
  sanitized artifacts, rate/backoff evidence, and no order endpoint calls.
- `deferred`: not used in the first ingestion implementation.
- `forbidden_default`: blocked unless a later Set contract explicitly changes
  the policy.

## 3. Allowlist

| source_id | source | status | method | env / credential | storage policy | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `dart_openapi_disclosures` | OPENDART / DART Open API | `approved_first_go` | official API | `DART_API_KEY` | metadata, filing ids, timestamps, summaries, selected XML snapshots only when needed | Primary disclosure source for first Go. Use list/search endpoints and source ids. |
| `public_news_rss_search` | Public news search RSS metadata feed | `approved_first_go` | public RSS/search feed metadata | none | title, link, source, published timestamp, query metadata, and RSS summary/excerpt only | No-key news source for first live collector hotfix. No article-body crawling, login scraping, paywall scraping, or general HTML scraping. |
| `naver_search_news_api` | NAVER Developers Search API - news | `conditional_after_key` | official API | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | title, original link, Naver link, description/excerpt, timestamps, query metadata | General news source after API credentials and query/rate config are approved. No article-body scraping. |
| `kind_krx_disclosure_portal` | KRX KIND disclosure portal | `conditional_after_terms_check` | official web portal / future approved method | none until approved | metadata only until method is approved | Official disclosure portal, but automated collection needs source-specific terms/access confirmation. DART remains first source. |
| `krx_data_marketplace_delayed` | KRX Data Marketplace | `conditional_after_terms_check` | official data portal/product | none until approved | delayed market-data metadata/OHLCV only after terms/access confirmation | Use for delayed/context data only after access policy is recorded. Realtime trading feed is not approved here. |
| `kis_market_or_realtime_data` | KIS market/realtime/news APIs | `approved_unit_013_paper_read_pending_proof` | broker API paper-read only | `/home/hwi/.config/hwistock/hwistockApi.env` alias only; values never stored | sanitized metadata/snapshot fields, payload refs, hashes, watermarks; no raw secrets/account ids | UNIT-013 may collect KIS paper-supported KRX market-data snapshots for signal confirmation. UNIT-013 must not call KIS order endpoints. NXT/SOR/integrated broker-facing branches stay disabled/fallback-only until later proof. |
| `krx_nxt_market_calendar_cache` | KRX trading-days/holidays + NXT session references | `approved_first_go` | local cached calendar generated from official sources | none | trading-day/session metadata only | Runtime scheduler source for open/closed/stale-calendar decisions. See `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`. |
| `general_media_html_scrape` | General news/media HTML scraping | `forbidden_default` | HTML scraping | none | none | Blocked by default due copyright/terms/anti-bot risk. |
| `unofficial_finance_apis` | Unofficial finance/news/quote APIs | `forbidden_default` | unofficial API/scraping | none | none | Blocked unless a later source-specific review approves terms and data quality. |

## 3-1. Official Reference URLs

Checked on 2026-06-02.

| source_id | reference_url | purpose |
| --- | --- | --- |
| `dart_openapi_disclosures` | `https://opendart.fss.or.kr/intro/main.do` | DART Open API introduction |
| `dart_openapi_disclosures` | `https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DE001&apiId=AE00001` | DART disclosure search API guide |
| `kind_krx_disclosure_portal` | `https://kind.krx.co.kr/` | KRX KIND disclosure portal |
| `krx_data_marketplace_delayed` | `https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=ko` | KRX Data Marketplace |
| `naver_search_news_api` | `https://developers.naver.com/products/service-api/search/search.md` | NAVER Developers Search API introduction |
| `kis_market_or_realtime_data` | `https://apiportal.koreainvestment.com/apiservice-summary` | KIS API service summary |
| `kis_market_or_realtime_data` | `https://github.com/koreainvestment/open-trading-api` | KIS official GitHub samples |
| `krx_nxt_market_calendar_cache` | `https://global.krx.co.kr/contents/GLB/06/0606/0606030101/GLB0606030101T3.jsp` | KRX trading-days and holidays reference |
| `krx_nxt_market_calendar_cache` | `https://www.nextrade.co.kr/` | NXT session reference |

## 4. Rate / Collection Defaults

- OPENDART: respect official API limits and error codes. First implementation
  should also apply a local conservative cap and backoff.
- Public RSS news search: no credential required; use conservative polling,
  metadata/excerpt-only storage, and no article-body HTML crawling.
- NAVER Search API: use only after credentials are approved; first config must
  include daily cap, query list, and backoff.
- KRX/KIND: no automated collection until terms/access method is recorded.
- Every source must record:
  - `source_id`
  - `source_status`
  - `collection_method`
  - `terms_checked_at`
  - `rate_limit_policy`
  - `body_storage_policy`
  - `source_published_at_kst` when the source provides it
  - `dedupe_key`
  - `source_hash`
  - `collection_watermark`
  - `last_success_at`
  - `last_failure_at`

## 5. Event Types

The first normalized event schema should support:

- `disclosure_event`
- `news_event`
- `market_notice_event`
- `market_data_event`

Required shared fields:

- `event_id`
- `source_id`
- `source_event_id`
- `symbol`
- `corp_code` when available
- `market`
- `title`
- `source_url`
- `source_published_at_kst`
- `collected_at_kst`
- `event_type`
- `dedupe_key`
- `body_storage_policy`
- `source_hash`
- `collection_watermark`
- `terms_policy_ref`
- `candidate_eligible`

## 6. Deduplication

Default dedupe key:

- disclosures: `source_id + rcept_no` when available
- news: normalized `original_link` or canonical URL plus title hash
- market data: `source_id + symbol + venue + interval + timestamp`

Duplicates must be linked, not discarded silently.

## 7. Chart / Market-Data Policy

- Raw data fields are required for chart signals; chart images are not source
  data.
- First approved realtime broker feed is not selected in this registry.
- KRX Data Marketplace may be used only for delayed/context data after terms and
  access are approved.
- KIS realtime quote/order-book feeds are documented by UNIT-009 and may be
  attempted only inside UNIT-013's paper-read market-data collector where
  paper-supported. Unsupported NXT/SOR/integrated feeds must write
  disabled/fallback evidence and cannot unlock broker-facing orders.
