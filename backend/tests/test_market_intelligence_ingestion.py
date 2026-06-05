"""
HWISTOCK-UNIT-003 foundation smoke tests (QA-001 through QA-011).
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import unittest

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import market_intelligence as mi  # noqa: E402
from service import market_intelligence_ingestion as ingestion  # noqa: E402

FORBIDDEN_IMPORT_PREFIXES = (
    "socket",
    "websocket",
    "kis",
    "broker",
    "order",
    "trading",
)

FORBIDDEN_MODULE_SUBSTRINGS = (
    "HwiStockOrder",
    "order_router",
    "kis_",
    "broker_",
    "trading_router",
)


def _fixture_row(**overrides):
    base = {
        "source_id": "dart_openapi_disclosures",
        "source_event_id": "20260604000001",
        "rcept_no": "20260604000001",
        "symbol": "005930",
        "corp_code": "00126380",
        "market": "KRX",
        "title": "Fixture disclosure",
        "source_url": "https://opendart.fss.or.kr/example",
        "published_at_kst": "2026-06-04T09:00:00+09:00",
        "collected_at_kst": "2026-06-04T09:01:00+09:00",
        "event_type": "disclosure_event",
    }
    base.update(overrides)
    return base


def _calendar_row(**overrides):
    base = {
        "source_id": "krx_nxt_market_calendar_cache",
        "source_event_id": "2026-06-04-session",
        "symbol": "",
        "market": "KRX",
        "title": "Trading session calendar",
        "source_url": "local://krx-nxt-calendar",
        "published_at_kst": "2026-06-04T08:00:00+09:00",
        "collected_at_kst": "2026-06-04T08:00:01+09:00",
        "event_type": "market_data_event",
        "venue": "KRX+NXT",
        "interval": "session_calendar",
    }
    base.update(overrides)
    return base


class MarketIntelligenceIngestionTests(unittest.TestCase):
    def testQa001AndQa003SourceRegistryCarriesPolicyFields(self):
        reg = mi.loadSourceRegistryConfig()
        self.assertEqual(
            reg["approved_first_go_source_ids"],
            ["dart_openapi_disclosures", "krx_nxt_market_calendar_cache", "public_news_rss_search"],
        )
        required_keys = {
            "source_status",
            "collection_method",
            "credential_policy",
            "storage_policy",
            "rate_limit_policy",
            "terms_notes",
            "retention_notes",
            "body_storage_policy",
        }
        for source_id, cfg in reg["sources"].items():
            with self.subTest(source_id=source_id):
                self.assertTrue(required_keys.issubset(cfg.keys()))
                self.assertIn(
                    cfg["source_status"],
                    {
                        mi.SOURCE_STATUS_APPROVED_FIRST_GO,
                        mi.SOURCE_STATUS_CONDITIONAL_AFTER_KEY,
                        mi.SOURCE_STATUS_CONDITIONAL_AFTER_TERMS,
                        mi.SOURCE_STATUS_DEFERRED,
                        mi.SOURCE_STATUS_FORBIDDEN_DEFAULT,
                    },
                )

    def testQa002AndQa011NoNetworkEnvOrRoutingImports(self):
        module_paths = [
            Path(baseDir) / "lib" / "market_intelligence.py",
            Path(baseDir) / "service" / "market_intelligence_ingestion.py",
        ]
        for path in module_paths:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    root = name.split(".")[0]
                    self.assertNotIn(
                        root,
                        FORBIDDEN_IMPORT_PREFIXES,
                        msg=f"{path.name} imports forbidden module {name}",
                    )
                    lowered = name.lower()
                    for fragment in FORBIDDEN_MODULE_SUBSTRINGS:
                        self.assertNotIn(
                            fragment.lower(),
                            lowered,
                            msg=f"{path.name} imports routing/broker module {name}",
                        )

        mi_spec = importlib.util.find_spec("lib.market_intelligence")
        ing_spec = importlib.util.find_spec("service.market_intelligence_ingestion")
        self.assertIsNotNone(mi_spec)
        self.assertIsNotNone(ing_spec)

    def testQa004DuplicateFixtureEventsLinkDeterministically(self):
        row = _fixture_row()
        duplicate = _fixture_row(
            source_event_id="20260604000001-dup",
            title="Fixture disclosure duplicate title",
        )
        result = ingestion.ingestFixtureRows(
            [row, duplicate],
            run_collected_at_kst="2026-06-04T10:00:00+09:00",
        )
        events = result["events"]
        self.assertEqual(len(events), 2)
        primaries = [e for e in events if not e.get("duplicate_of_event_id")]
        duplicates = [e for e in events if e.get("duplicate_of_event_id")]
        self.assertEqual(len(primaries), 1)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["duplicate_of_event_id"], primaries[0]["event_id"])
        self.assertIn(duplicates[0]["event_id"], primaries[0]["linked_duplicate_event_ids"])
        self.assertEqual(result["summary"]["duplicate_links"], 1)

    def testQa005AndQa006HealthAndSummaryExposeRequiredOperatorFields(self):
        result = ingestion.ingestFixtureRows(
            [_fixture_row(), _calendar_row()],
            run_collected_at_kst="2026-06-04T11:00:00+09:00",
        )
        summary = result["summary"]
        health = result["health"]
        self.assertEqual(summary["submitted_rows"], 2)
        self.assertGreaterEqual(summary["ingested_events"], 2)
        self.assertIn("dart_openapi_disclosures", summary["per_source_counts"])
        self.assertFalse(summary["evidence_written"])
        self.assertEqual(health["last_fetch_at_kst"], "2026-06-04T11:00:00+09:00")
        self.assertFalse(health["live_sources_enabled"])
        self.assertIn("dart_openapi_disclosures", health["disabled_live_source_ids"])

    def testQa007MarketDataContextFieldsAreDeclaredBeforeSignals(self):
        reg = mi.loadSourceRegistryConfig()
        ctx = reg["market_data_context"]
        self.assertFalse(ctx["chart_signals_enabled"])
        self.assertFalse(ctx["live_chart_sources_enabled"])
        self.assertIn("ohlcv_schema", ctx)
        self.assertIn("open", ctx["ohlcv_schema"])
        delayed = reg["sources"]["krx_data_marketplace_delayed"]
        self.assertEqual(delayed["source_status"], mi.SOURCE_STATUS_CONDITIONAL_AFTER_TERMS)
        self.assertFalse(delayed["live_enabled"])
        kis = reg["sources"]["kis_market_or_realtime_data"]
        self.assertEqual(kis["source_status"], mi.SOURCE_STATUS_DEFERRED)

    def testQa008AndQa009BlockedSourcesCannotIngestInFoundation(self):
        blocked_rows = [
            {"source_id": "general_media_html_scrape", "source_event_id": "x1", "title": "t"},
            {"source_id": "unofficial_finance_apis", "source_event_id": "x2", "title": "t"},
            {"source_id": "kis_market_or_realtime_data", "source_event_id": "x3", "title": "t"},
            {"source_id": "naver_search_news_api", "source_event_id": "x4", "title": "t"},
        ]
        result = ingestion.ingestFixtureRows(
            blocked_rows,
            run_collected_at_kst="2026-06-04T12:00:00+09:00",
        )
        self.assertEqual(result["events"], [])
        self.assertEqual(len(result["summary"]["failures"]), 4)
        blocked = set(result["summary"]["blocked_source_ids"])
        self.assertTrue(
            {
                "general_media_html_scrape",
                "unofficial_finance_apis",
                "kis_market_or_realtime_data",
                "naver_search_news_api",
            }.issubset(blocked)
        )

    def testQa010NormalizedEventSchemaContainsRequiredFields(self):
        event = mi.normalizeFixtureRow(
            _fixture_row(),
            collected_at_kst="2026-06-04T13:00:00+09:00",
        )
        for field in mi.REQUIRED_EVENT_FIELDS:
            self.assertIn(field, event)
        mi.validateNormalizedEvent(event)

    def testQa010RejectsNonKstOrAmbiguousTimestamps(self):
        with self.assertRaisesRegex(ValueError, r"published_at_kst.*\+09:00"):
            mi.normalizeFixtureRow(
                _fixture_row(published_at_kst="2026-06-04T13:00:00Z"),
                collected_at_kst="2026-06-04T13:00:01+09:00",
            )

        with self.assertRaisesRegex(ValueError, r"published_at_kst.*\+09:00"):
            mi.normalizeFixtureRow(
                _fixture_row(published_at_kst="2026-06-04T13:00:00"),
                collected_at_kst="2026-06-04T13:00:01+09:00",
            )

    def testQa010EnforcesRegistryBodyStoragePolicy(self):
        event = mi.normalizeFixtureRow(
            _fixture_row(body_storage_policy="metadata_only"),
            collected_at_kst="2026-06-04T13:00:00+09:00",
        )
        self.assertEqual(event["body_storage_policy"], "metadata_only")

        with self.assertRaisesRegex(ValueError, "source registry policy"):
            mi.normalizeFixtureRow(
                _fixture_row(body_storage_policy="full_body"),
                collected_at_kst="2026-06-04T13:00:00+09:00",
            )

    def testQa011FoundationSmokeSucceedsWithoutCredentialsOrNetwork(self):
        result = ingestion.ingestFixtureRows(
            [_fixture_row(), _calendar_row()],
            run_collected_at_kst="2026-06-04T14:00:00+09:00",
        )
        self.assertEqual(result["health"]["status"], "ok")
        self.assertEqual(result["summary"]["foundation_mode"], True)
        self.assertGreater(result["summary"]["unique_events"], 0)
        for event in result["events"]:
            self.assertEqual(event["ingestion_mode"], "foundation_fixture")

    def testLiveCollectorWritesFailClosedHealthWhenKeysAreMissing(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = {
                key: os.environ.pop(key, None)
                for key in ("DART_API_KEY", "NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET")
            }
            try:
                result = ingestion.runCollectorOnce(
                    output_root=Path(tmp),
                    enable_network=True,
                    include_public_rss=False,
                    now=ingestion.datetime(2026, 6, 5, 4, 30, tzinfo=ingestion.KST),
                )
            finally:
                for key, value in previous.items():
                    if value is not None:
                        os.environ[key] = value

            health = result["health"]
            self.assertEqual(health["status"], "blocked_no_source_rows")
            self.assertFalse(health["orders_enabled"])
            self.assertFalse(health["broker_calls_enabled"])
            self.assertEqual(health["normalized_event_count"], 0)
            statuses = {row["source_id"]: row["status"] for row in health["source_results"]}
            self.assertEqual(statuses["dart_openapi_disclosures"], "skipped_missing_key")
            self.assertEqual(statuses["naver_search_news_api"], "skipped_missing_key")
            self.assertTrue((Path(tmp) / "evidence" / "2026-06-05" / "market-intel-collector-health.json").is_file())

    def testLiveCollectorNoNetworkModeDoesNotCallSourcesButWritesHealth(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ingestion.runCollectorOnce(
                output_root=Path(tmp),
                enable_network=False,
                now=ingestion.datetime(2026, 6, 5, 4, 35, tzinfo=ingestion.KST),
            )

            health = result["health"]
            self.assertEqual(health["source_results"][0]["status"], "skipped_network_disabled")
            self.assertEqual(health["source_results"][1]["status"], "skipped_network_disabled")
            self.assertEqual(health["source_results"][2]["status"], "skipped_network_disabled")
            self.assertTrue((Path(tmp) / "evidence" / "2026-06-05" / "market-intel-collector-health.json").is_file())

    def testPublicRssRowsCanNormalizeWithoutApiKeys(self):
        rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss><channel>
          <item>
            <title>삼성전자 주가 상승</title>
            <link>https://news.example.test/article/1</link>
            <guid>rss-1</guid>
            <pubDate>Thu, 04 Jun 2026 23:00:00 GMT</pubDate>
            <description>시장 요약</description>
            <source>Example News</source>
          </item>
        </channel></rss>
        """
        sanitized = ingestion._sanitize_rss_payload({"_http_status": 200, "text": rss}, query="삼성전자")
        rows = ingestion._public_rss_rows(
            sanitized["items"],
            query="삼성전자",
            collected_at_kst="2026-06-05T08:01:00+09:00",
        )
        result = ingestion.ingestFixtureRows(
            rows,
            registry=ingestion._runtime_registry_for_sources(["public_news_rss_search"]),
            run_collected_at_kst="2026-06-05T08:01:00+09:00",
        )

        self.assertEqual(result["summary"]["unique_events"], 1)
        self.assertEqual(result["events"][0]["source_id"], "public_news_rss_search")
        self.assertEqual(result["events"][0]["event_type"], "news_event")
        self.assertEqual(result["events"][0]["body_storage_policy"], "excerpt_allowed")

    def testCollectorJsonlAppendSkipsExistingEventIds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "normalized" / "2026-06-05" / "events.jsonl"
            first = {"event_id": "public-news-rss-search:1", "title": "first"}
            duplicate = {"event_id": "public-news-rss-search:1", "title": "duplicate"}
            second = {"event_id": "public-news-rss-search:2", "title": "second"}

            self.assertEqual(ingestion._append_jsonl_unique(path, [first]), 1)
            self.assertEqual(ingestion._append_jsonl_unique(path, [duplicate, second]), 1)

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertIn('"title": "first"', lines[0])
            self.assertIn('"title": "second"', lines[1])

    def testSystemdCollectorTimerTemplatesExist(self):
        ops = Path(__file__).resolve().parents[2] / "ops" / "systemd"
        service = (ops / "hwistock-intel-collector.service").read_text(encoding="utf-8")
        timer = (ops / "hwistock-intel-collector.timer").read_text(encoding="utf-8")

        self.assertIn("market_intelligence_ingestion.py --once", service)
        self.assertIn("EnvironmentFile=-/home/hwi/.config/hwistock/hwistock.env", service)
        self.assertIn("OnUnitActiveSec=10min", timer)
        self.assertIn("Persistent=true", timer)


if __name__ == "__main__":
    unittest.main()
