---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-003
type: unit
domain: backend
name: Market intelligence ingestion
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
work_class: product_api
completeness:
  status: set
  audit_ref: docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md
owner: hwi
updated_at: 2026-06-04
last_verified_at: 2026-06-04
source_snapshot:
  input_digest: "24시간 뉴스 기사/공시 수집 브랜치와 차트/시장데이터 컨텍스트"
  legacy_doc: none
  legacy_status: greenfield
source_inputs:
  - kind: user_prompt
    path_or_url: "인터넷에서 뉴스 기사 / 공시 같은거 수집, 크롤링, 24시간"
    confidence: high
  - kind: user_prompt
    path_or_url: "뉴스 및 공시, 차트도 같이 보게?"
    confidence: high
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-002
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  include:
    - backend/lib/market_intelligence.py
    - backend/service/market_intelligence_ingestion.py
    - backend/tests/test_market_intelligence_ingestion.py
  exclude:
    - "**/*credentials*"
    - "**/*.env"
entrypoints:
  - backend.service.market_intelligence_ingestion.ingestFixtureRows
interfaces:
  - backend.lib.market_intelligence.loadSourceRegistryConfig
  - backend.lib.market_intelligence.normalizeFixtureRow
  - backend.lib.market_intelligence.validateNormalizedEvent
  - backend.service.market_intelligence_ingestion.ingestFixtureRows
verification:
  stage_skill_routes:
    ready:
      - hwi-work-harness
    set:
      - hwi-work-harness
    go:
      - hwi-work-harness
      - delegation-guard
    check:
      - hwi-work-harness
    prove:
      - hwi-work-harness
  required_gates:
    - intel-ingestion-smoke
  suggested_gates:
    - source-rate-limit-check
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md
risk:
  tier: 2
  reasons:
    - 24-hour collection can violate source policies if source rules are not explicit.
    - News/disclosure/chart signals must not directly trigger orders.
last_set:
  status: set
  report_id: RUN-20260602-unit-003-market-intelligence-set
  context_fingerprint:
evidence_refs:
  - docs/evidence/RUN-20260602_unit-003-market-intelligence-set.md
  - docs/evidence/RUN-20260604_unit-003-go-preflight.md
  - docs/evidence/RUN-20260604_unit-003-go-check.md
  - docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md
links:
  - HWISTOCK-MOD-002
  - docs/sources/HWISTOCK-SOURCE-REGISTRY.md
---

# Market Intelligence Ingestion

## 1. Goal

Define the 24-hour information ingestion branch for news, articles, disclosures,
chart/market-data context, and other permitted market intelligence sources.

## 2. Baseline Module Contract

This unit implements `HWISTOCK-MOD-002`. It must stay separate from the trading
branch and cannot directly invoke order routing.

### Module Change

Initial creation of `HWISTOCK-MOD-002`.

## 3. Included Scope

- Source allowlist.
- API/RSS/crawling policy.
- Deduplication policy.
- Event metadata schema draft.
- Source registry status model.
- DART OpenAPI first source.
- Conditional NAVER Search API news source.
- Deferred KIND/KRX/KIS source handling.
- Chart/market-data metadata schema draft: OHLCV, interval, venue, latency, and
  volume/price movement features.
- Ingestion health/evidence expectations.
- Separation from trading/order routing.

## 4. Excluded Scope

- Live trading.
- Broker API integration.
- Strategy scoring.
- Full article republishing.
- Scraping disallowed sources.
- General media HTML scraping by default.
- KIS or broker network calls.
- Realtime quote/order-book integration.

## 5. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | Source allowlist is defined before implementation | `docs/sources/HWISTOCK-SOURCE-REGISTRY.md` lists allowed, conditional, deferred, and forbidden sources | doc/config review | QA-001 |
| AC-02 | P0 | Ingestion cannot directly place orders | No direct order interface from ingestion output | architecture/code review | QA-002 |
| AC-03 | P0 | Collection policy respects source permissions | API/RSS/robots/terms/rate notes exist per source | source review | QA-003 |
| AC-04 | P1 | Deduplication key is defined | Duplicate news/disclosures can be merged | test/log review | QA-004 |
| AC-05 | P1 | 24-hour health is observable | ingestion status and last fetch timestamps visible | health output | QA-005 |
| AC-06 | P1 | Chart data source policy is defined before chart signals | Source, interval, latency, and OHLCV schema are listed | doc/config review | QA-007 |
| AC-07 | P0 | HTML scraping is blocked by default | General media HTML scraping and unofficial APIs are forbidden unless later Set approves a source | source registry review | QA-008 |
| AC-08 | P0 | Broker data remains deferred | KIS/broker quote/news/realtime sources cannot be used in this unit | source registry and profile review | QA-009 |

## 6. Implementation Notes

Use the source registry as the implementation contract.

Foundation-only first Go mode:

- Build the source registry, configuration loader, normalized event schema,
  fixture ingestion path, dedupe behavior, health output, and evidence output.
- Keep live OpenDART network calls disabled by default.
- Do not require or read `DART_API_KEY` in the first foundation Go unless a
  later explicit source API config approval records the key name, rate cap,
  storage policy, and evidence expectations.
- Do not call KIS/broker, Naver, KRX/KIND, unofficial finance APIs, or general
  media HTML scraping sources.

Future live-source mode, after explicit source API config approval:

- `dart_openapi_disclosures`: first live-source candidate. Use `DART_API_KEY`
  only after explicit source API config approval.
- `naver_search_news_api`: conditional after `NAVER_CLIENT_ID`,
  `NAVER_CLIENT_SECRET`, query list, rate cap, and storage policy approval.
- `kind_krx_disclosure_portal`: official source candidate, but automated
  collection is deferred until terms/access checks are complete.
- `krx_data_marketplace_delayed`: official market-data source candidate for
  delayed/context data, but automated collection is deferred until terms/access
  checks are complete.
- `kis_market_or_realtime_data`: deferred to KIS API verification.
- `general_media_html_scrape` and `unofficial_finance_apis`: forbidden by
  default.

The first foundation implementation must not implement conditional/deferred
sources until their status changes in Set.

Current rebaseline Go-Check implementation status:

- Implemented as a Python stdlib-only, fixture/config-first skeleton in
  `backend/lib/market_intelligence.py` and
  `backend/service/market_intelligence_ingestion.py`.
- `loadSourceRegistryConfig()` returns the deterministic UNIT-003 foundation
  source registry/config model without reading environment variables or files.
- `ingestFixtureRows()` accepts in-memory fixture rows only and returns
  normalized events plus summary/health dictionaries. It writes no runtime
  artifacts.
- Live OpenDART, Naver, KRX/KIND, KIS/broker, general media HTML scraping, and
  unofficial API paths remain disabled. Conditional, deferred, forbidden, and
  unknown sources are reported as failures and cannot ingest in foundation mode.
- Duplicate fixture events are linked deterministically by dedupe key; they are
  not silently discarded.
- `published_at_kst` and `collected_at_kst` validation requires explicit
  `+09:00` KST timestamps.
- `body_storage_policy` is enforced from the source registry; callers cannot
  widen it through fixture rows.
- The ingestion modules do not import network, credential-loading,
  broker/KIS/order-routing, or trading router interfaces.
- Focused unittest coverage exists at
  `backend/tests/test_market_intelligence_ingestion.py` for QA-001 through
  QA-011 foundation smoke coverage. This is Go implementation/check evidence,
  not Prove evidence.

Current evidence:

- `docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md`

The earlier `RUN-20260604_unit-003-go-preflight.md` and
`RUN-20260604_unit-003-go-check.md` files remain historical after the
MyWebTemplate code import.

## 7. Required Event Fields

Normalized events must include:

- `event_id`
- `source_id`
- `source_event_id`
- `symbol`
- `corp_code` when available
- `market`
- `title`
- `source_url`
- `published_at_kst`
- `collected_at_kst`
- `event_type`
- `dedupe_key`
- `body_storage_policy`
- `source_hash`
- `candidate_eligible`

## 8. Open Questions

- What exact Naver news query list should be used if the conditional source is
  enabled?
- Trading-grade chart/realtime source and candle intervals are proposed in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`; they remain
  inactive until the user approves the packet and later broker-network approval
  enables any KIS data calls.
- Are paid KRX/data-vendor APIs acceptable later?
- How long should collected metadata/events be retained?
- Should KIND/KRX automated collection remain deferred or be promoted after a
  source-specific terms/access check?
