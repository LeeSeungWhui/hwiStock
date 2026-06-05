---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-unit-003-operation-collector-hotfix
stage: go/prove-hotfix
unit_id: HWISTOCK-UNIT-003
status: pass_public_rss_timer_active_api_keys_missing_for_dart_naver
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md
previous_unit003_evidence_ref: docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md
created_at: 2026-06-05
environment: hwiServer_user_systemd
service_template_refs:
  - ops/systemd/hwistock-intel-collector.service
  - ops/systemd/hwistock-intel-collector.timer
runtime_health_artifact: data/evidence/2026-06-05/market-intel-collector-health.json
credential_values_printed: false
broker_network_calls_made: false
kis_order_calls_made: false
live_orders_placed: false
---

# UNIT-003 Operation Collector Hotfix — 2026-06-05

## 1. Verdict

PASS for the no-key public RSS news collector and 24-hour timer path.

PARTIAL for the broader OpenDART/Naver API-source plan because those
credentialed sources are still skipped until their local keys exist.

The previous UNIT-003 implementation was only a fixture/config-first ingestion
skeleton. That was not enough to satisfy the operational expectation that a
24-hour news/disclosure collector should be running.

This hotfix adds a real collector entrypoint and a systemd timer path:

- `backend/service/market_intelligence_ingestion.py --once`
- `ops/systemd/hwistock-intel-collector.service`
- `ops/systemd/hwistock-intel-collector.timer`

The collector is now installed as a user systemd timer on hwiServer and is
active. It ran a service tick successfully at `2026-06-05T04:29:23+09:00`.

Actual news rows are now collected through the no-key
`public_news_rss_search` source. The collector stores RSS/search-feed
metadata only: title, source URL, source name when provided, published
timestamp, query metadata, and RSS summary/excerpt. It does not crawl article
bodies, login pages, paywalled pages, or general HTML pages.

OpenDART and Naver API collection remain skipped because the local secret store
currently has no `DART_API_KEY`, `NAVER_CLIENT_ID`, or `NAVER_CLIENT_SECRET`.

## 2. Runtime Status

Observed user systemd state after public RSS hotfix:

| check | result |
| --- | --- |
| `hwistock-intel-collector.timer` enabled | yes |
| `hwistock-intel-collector.timer` active | yes |
| last successful service tick | 2026-06-05 04:29:23 KST |
| next timer trigger observed | 2026-06-05 04:39:23 KST |
| service exit status | 0/SUCCESS |
| health artifact written | `data/evidence/2026-06-05/market-intel-collector-health.json` |
| normalized artifact written | `data/normalized/2026-06-05/events.jsonl` |

Sanitized health result:

| field | result |
| --- | --- |
| network_enabled | true |
| orders_enabled | false |
| broker_calls_enabled | false |
| normalized_event_count | 150 |
| unique_event_count | 150 |
| appended_event_count after dedupe | 0 on repeat run |
| status | `ok` |
| DART source | `skipped_missing_key` |
| Naver news source | `skipped_missing_key` |
| public RSS news source | `pass` |

Runtime JSONL integrity after cleanup:

| field | result |
| --- | --- |
| JSONL line count | 150 |
| unique event ids | 150 |
| duplicate event ids | 0 |
| bad JSON lines | 0 |
| source count | `public_news_rss_search`: 150 |

## 3. Code Changes

| path | change |
| --- | --- |
| `backend/lib/market_intelligence.py` | Adds `public_news_rss_search` as an approved first-Go source with no credential requirement and metadata/excerpt-only storage policy. |
| `backend/service/market_intelligence_ingestion.py` | Adds bounded OpenDART/Naver collector helpers, no-key public RSS news collection, sanitized raw artifact writes, duplicate-safe normalized event appends, health evidence writes, and CLI `--once` / `--no-public-rss`. Missing OpenDART/Naver keys skip only those sources. |
| `backend/tests/test_market_intelligence_ingestion.py` | Adds collector health/timer tests, public RSS normalization coverage, and JSONL duplicate-append regression coverage while broker/order/KIS routing imports remain blocked. |
| `ops/systemd/hwistock-intel-collector.service` | Adds collector tick service with optional `/home/hwi/.config/hwistock/hwistock.env`. |
| `ops/systemd/hwistock-intel-collector.timer` | Runs the collector every 10 minutes across 24-hour uptime. |

## 4. Validation

Executed locally from `/data/workspace/My/hwiStock`:

| command | result |
| --- | --- |
| `python -m py_compile backend/lib/market_intelligence.py backend/service/market_intelligence_ingestion.py backend/tests/test_market_intelligence_ingestion.py` | PASS |
| `python -m unittest backend.tests.test_market_intelligence_ingestion` | PASS, 15 tests |
| `python backend/service/market_intelligence_ingestion.py --once` | PASS; public RSS collected 150 normalized news events, repeat run appended 0 duplicates |
| `systemctl --user enable --now hwistock-intel-collector.timer` | PASS |
| `systemctl --user is-enabled hwistock-intel-collector.timer` | `enabled` |
| `systemctl --user is-active hwistock-intel-collector.timer` | `active` |
| `systemctl --user start hwistock-intel-collector.service` | PASS; service exit 0/SUCCESS and public RSS source status `pass` |

## 5. Residual Gap

Public RSS news rows are collecting now without API keys.

To add credentialed disclosure/news APIs, populate the local secret store with
the approved source credentials:

- `DART_API_KEY` for OpenDART disclosure collection.
- `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET` for Naver news collection.

The collector intentionally does not fall back to general media HTML scraping,
unofficial finance APIs, KIS broker data, or fake event generation.

DeepSeek analysis is not part of this hotfix and is still not running as a
hwiStock analysis job/timer. The MoonBridge DeepSeek proxy being active is only
provider infrastructure; it is not the same thing as a scheduled hwiStock
analysis pipeline.
