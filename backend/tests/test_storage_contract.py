from __future__ import annotations

from datetime import date
from pathlib import Path
import unittest

from pydantic import BaseModel, ValidationError

from backend.lib.request_payload import (
    artifact_detail_payload_model,
    artifact_list_payload_model,
    paper_day_manifest_payload_model,
    pnl_query_payload_model,
    report_payload_model,
)
from backend.lib.storage_schemas import (
    ArtifactPathClass,
    BodyStoragePolicy,
    DailyPnL,
    PaperDayEvidenceManifest,
    SourceArtifact,
    build_artifact_path,
    compute_sha256_hex,
    validate_no_sensitive_keys,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = (
    PROJECT_ROOT
    / "backend"
    / "migrations"
    / "versions"
    / "20260604_0001_create_hwistock_core_storage.py"
)


class StorageContractTests(unittest.TestCase):
    def test_sha256_hash_is_deterministic_for_dict_order(self) -> None:
        payload_a = {"z": [1, 2], "a": {"x": 1, "y": 2}}
        payload_b = {"a": {"y": 2, "x": 1}, "z": [1, 2]}

        self.assertEqual(compute_sha256_hex(payload_a), compute_sha256_hex(payload_b))

    def test_build_artifact_path_uses_kst_date_partition(self) -> None:
        trading_date = date(2026, 6, 4)
        cases = [
            (
                ArtifactPathClass.source_news,
                "sample.json",
                "data/raw/2026-06-04/news/sample.json",
            ),
            (
                ArtifactPathClass.source_disclosures,
                "sample.json",
                "data/raw/2026-06-04/disclosures/sample.json",
            ),
            (
                ArtifactPathClass.source_market_data,
                "sample.jsonl",
                "data/raw/2026-06-04/market-data/sample.jsonl",
            ),
            (
                ArtifactPathClass.normalized,
                "",
                "data/normalized/2026-06-04/events.jsonl",
            ),
            (
                ArtifactPathClass.ai_hourly,
                "0900.json",
                "data/ai/2026-06-04/deepseek-pro/hourly/0900.json",
            ),
            (
                ArtifactPathClass.ai_market_regime,
                "0800.json",
                "data/ai/2026-06-04/deepseek-pro/market-regime/0800.json",
            ),
            (
                ArtifactPathClass.ai_intraday,
                "risk.json",
                "data/ai/2026-06-04/deepseek-flash/intraday/risk.json",
            ),
            (
                ArtifactPathClass.candidate,
                "candidate-a.json",
                "data/candidates/2026-06-04/candidate-a.json",
            ),
            (
                ArtifactPathClass.order,
                "",
                "data/trading/2026-06-04/orders.jsonl",
            ),
            (
                ArtifactPathClass.fill,
                "",
                "data/trading/2026-06-04/fills.jsonl",
            ),
            (
                ArtifactPathClass.position,
                "",
                "data/trading/2026-06-04/positions.jsonl",
            ),
            (
                ArtifactPathClass.pnl,
                "",
                "data/trading/2026-06-04/pnl.json",
            ),
            (
                ArtifactPathClass.morning_report,
                "",
                "data/reports/2026-06-04/morning-0700.json",
            ),
            (
                ArtifactPathClass.daily_close_report,
                "",
                "data/reports/2026-06-04/daily-close-mode-aware.json",
            ),
            (
                ArtifactPathClass.evidence,
                "",
                "data/evidence/2026-06-04/paper-day.json",
            ),
        ]

        for category, sub_path, expected in cases:
            with self.subTest(category=category.value):
                self.assertEqual(
                    build_artifact_path(
                        category=category,
                        trading_date=trading_date,
                        sub_path=sub_path,
                    ),
                    expected,
                )

        with self.assertRaises(ValueError):
            build_artifact_path(
                category=ArtifactPathClass.candidate,
                trading_date=trading_date,
                sub_path="../secret.json",
            )

    def test_source_artifact_blocks_body_without_full_body_policy(self) -> None:
        with self.assertRaises(ValidationError):
            SourceArtifact(
                artifact_id="src-001",
                source_type="news",
                source_name="example",
                source_url="https://example.invalid/news/1",
                body_storage_policy=BodyStoragePolicy.summary_only,
                body="forbidden body",
            )

        artifact = SourceArtifact(
            artifact_id="src-002",
            source_type="news",
            source_name="example",
            source_url="https://example.invalid/news/2",
            body_storage_policy=BodyStoragePolicy.full_body_allowed,
            body="allowed body",
        )
        self.assertEqual(artifact.body, "allowed body")

    def test_daily_pnl_requires_system_calculation_source(self) -> None:
        artifact = DailyPnL(
            artifact_id="pnl-001",
            gross_profit_krw=1000,
            gross_loss_krw=-250,
            gross_pnl_krw=750,
            fees_krw=10,
            taxes_krw=20,
            net_pnl_krw=720,
            cash_start_krw=2_000_000,
            cash_end_krw=2_000_720,
            open_position_value_krw=0,
        )
        self.assertEqual(artifact.calculation_source.value, "system")

        with self.assertRaises(ValidationError):
            DailyPnL(
                artifact_id="pnl-002",
                calculation_source="manual",
                gross_profit_krw=1000,
                gross_loss_krw=-250,
                gross_pnl_krw=750,
                fees_krw=10,
                taxes_krw=20,
                net_pnl_krw=720,
                cash_start_krw=2_000_000,
                cash_end_krw=2_000_720,
                open_position_value_krw=0,
            )

    def test_manifest_requires_cross_artifact_linkability(self) -> None:
        with self.assertRaises(ValidationError):
            PaperDayEvidenceManifest(
                artifact_id="manifest-001",
                paper_day_date="2026-06-04",
                source_artifact_ids=["src-001"],
                ai_analysis_ids=["ai-001"],
                candidate_card_ids=["candidate-001"],
                order_event_ids=["order-001"],
            )

        manifest = PaperDayEvidenceManifest(
            artifact_id="manifest-002",
            paper_day_date="2026-06-04",
            source_artifact_ids=["src-001"],
            normalized_event_ids=["event-001"],
            ai_analysis_ids=["ai-001"],
            candidate_card_ids=["candidate-001"],
            order_event_ids=["order-001"],
            fill_event_ids=["fill-001"],
            position_snapshot_ids=["position-001"],
            pnl_artifact_id="pnl-001",
            morning_report_id="report-am-001",
            daily_close_report_id="report-pm-001",
        )
        self.assertEqual(manifest.daily_close_report_id, "report-pm-001")

    def test_sensitive_key_validation_rejects_private_identifiers(self) -> None:
        payload = {
            "safe": {"nested": "ok"},
            "token": "should not be stored",
            "metadata": {"private-id": "blocked"},
        }

        violations = validate_no_sensitive_keys(payload, location="unit-008")
        self.assertEqual(violations, ["metadata.private-id", "token"])

    def test_request_payload_helpers_return_basemodel_types(self) -> None:
        for helper in (
            artifact_list_payload_model,
            artifact_detail_payload_model,
            paper_day_manifest_payload_model,
            pnl_query_payload_model,
            report_payload_model,
        ):
            model = helper()
            self.assertTrue(issubclass(model, BaseModel))

    def test_migration_skeleton_is_schema_qualified_and_isolated(self) -> None:
        text = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn('SCHEMA_NAME = "hwistock_core"', text)
        self.assertIn('CREATE SCHEMA IF NOT EXISTS "{SCHEMA_NAME}"', text)
        self.assertIn('f"{SCHEMA_NAME}.artifacts.artifact_id"', text)
        self.assertIn(
            'name="ck_hwistock_daily_pnl_calculation_source_system"',
            text,
        )
        self.assertNotIn("mywebtemplate", text.lower())
        self.assertNotIn('schema="public"', text)


if __name__ == "__main__":
    unittest.main()
