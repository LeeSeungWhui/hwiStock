"""
HWISTOCK-UNIT-005 focused unittest coverage for the AI orchestration layer
foundation skeleton.
"""

from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import sys
import unittest

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import ai_orchestration as ao  # noqa: E402

NOW_KST = "2026-06-04T09:05:00+09:00"
KNOWN_SOURCE_IDS = ["dart_openapi_disclosures:20260604-1"]

FORBIDDEN_IMPORT_PREFIXES = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "socket",
    "websocket",
    "openai",
    "anthropic",
    "pydantic",
    "fastapi",
    "sqlalchemy",
)
FORBIDDEN_MODULE_SUBSTRINGS = (
    "kis_client",
    "broker",
    "trading_router",
    "order_router",
    "paper_adapter",
    "live_adapter",
)


def _signal_bundle(**overrides):
    payload = {
        "signal_id": "sig-001",
        "source_path": "combined",
        "source_ids": KNOWN_SOURCE_IDS,
        "generated_at_kst": NOW_KST,
        "chart_interval": "1m",
        "chart_timestamp_kst": "2026-06-04T09:04:00+09:00",
        "candidate_reason": "disclosure plus volume breakout",
        "price_volume_reason": "volume spike with breakout candle",
        "stale_data": False,
        "fresh_signal": True,
        "chart_confirmation": {
            "confirmed": True,
            "reason": "breakout candle closed above trigger",
        },
    }
    payload.update(overrides)
    return payload


def _entry_intent(**overrides):
    payload = {
        "intent_type": "entry",
        "symbol": "005930",
        "candidate_reason": "disclosure plus volume breakout",
        "signal_bundle": _signal_bundle(),
        "venue_route": "KRX",
        "available_cash_krw": 1_700_000,
        "total_capital_krw": 2_000_000,
        "planned_order_cash_krw": 1_150_000,
        "current_holdings_count": 2,
        "entry_price_krw": 10_000,
        "stop_loss": {
            "source": "ai",
            "stop_price_krw": 9_600,
            "proposed_at_kst": NOW_KST,
            "auditable": True,
        },
        "target_profit_pct": 0.05,
        "execution_mode": "no_order_dry_run",
        "broker_adapter": "no_order_dry_run",
        "fresh_signal": True,
    }
    payload.update(overrides)
    return payload


def _draft_order_intent(**overrides):
    payload = {
        "symbol": "005930",
        "side": "buy",
        "risk_reference_id": "risk-ref-001",
        "price_type": "limit",
        "max_cash_krw": 1_150_000,
        "expires_at_kst": "2026-06-04T10:00:00+09:00",
        "execution_route": "no_order_dry_run",
    }
    payload.update(overrides)
    return payload


def _ai_recommendation(**overrides):
    payload = {
        "schema_version": "ai_recommendation/v0",
        "job_id": "deepseek_flash_intraday_label",
        "model_role": "deepseek_flash",
        "model_name": "deepseek-flash-local-fixture",
        "prompt_schema_version": "intraday_candidate_label/v0",
        "input_bundle_ids": ["bundle-001"],
        "produced_at_kst": NOW_KST,
        "source_ids": KNOWN_SOURCE_IDS,
        "validation_status": "pending",
        "redaction_status": "none",
        "recommendation_id": "rec-001",
        "action": "watch",
        "candidate_id": "candidate-001",
        "symbol": "005930",
        "source_path": "combined",
        "chart_interval": "1m",
        "thesis": "watch for breakout continuation",
        "risk_notes": "stale chart invalidates thesis",
        "confidence": "medium",
        "missing_inputs": [],
    }
    payload.update(overrides)
    return payload


class AiOrchestrationLayerTests(unittest.TestCase):
    def testQa016DefaultConfigKeepsNetworkAndProvidersDisabled(self):
        cfg = ao.loadAiOrchestrationConfig()
        self.assertFalse(cfg["AI_NETWORK_ENABLED"])
        self.assertEqual(cfg["AI_DAILY_COST_CAP_KRW"], 0)
        self.assertFalse(cfg["DEEPSEEK_PRO_ENABLED"])
        self.assertFalse(cfg["DEEPSEEK_FLASH_ENABLED"])
        self.assertFalse(cfg["CHATGPT_PRO_BROWSER_REVIEW_ENABLED"])
        self.assertEqual(cfg["GPT_PRO_MORNING_REVIEW_CUTOFF_KST"], "07:20")
        self.assertTrue(ao.validateAiOrchestrationConfig(cfg)["ok"])

    def testQa012JobRegistrySeparatesScheduledRoles(self):
        registry = ao.getAiJobRegistry()
        self.assertEqual(
            set(registry.keys()),
            {
                "deepseek_pro_news_hourly",
                "deepseek_pro_market_regime",
                "deepseek_flash_intraday_label",
                "gpt_prompt_0650",
                "chatgpt_pro_morning_review",
                "daily_close_2000",
            },
        )
        self.assertEqual(
            registry["deepseek_pro_news_hourly"]["output_schema"],
            "hourly_intel_analysis/v0",
        )
        self.assertEqual(
            registry["deepseek_pro_market_regime"]["output_schema"],
            "market_regime_report/v0",
        )
        self.assertEqual(
            registry["chatgpt_pro_morning_review"]["output_schema"],
            "morning_review_report/v0",
        )
        self.assertEqual(registry["daily_close_2000"]["output_schema"], "daily_close_report/v0")
        for job in registry.values():
            self.assertFalse(job["tool_use_enabled"])

    def testQa002MalformedOrUnknownActionIsRejected(self):
        malformed = ao.validateAiRecommendation({"action": "place_order"}, now_kst=NOW_KST)
        self.assertFalse(malformed["ok"])
        self.assertIn("missing_field:schema_version", malformed["errors"])

        unknown_action = ao.validateAiRecommendation(
            _ai_recommendation(action="auto_buy"),
            known_source_ids=KNOWN_SOURCE_IDS,
            now_kst=NOW_KST,
        )
        self.assertFalse(unknown_action["ok"])
        self.assertIn("action_unknown_or_missing", unknown_action["errors"])

    def testQa003MissingOrInventedSourceIdsAreRejected(self):
        missing = ao.validateAiRecommendation(
            _ai_recommendation(source_ids=[]),
            known_source_ids=KNOWN_SOURCE_IDS,
            now_kst=NOW_KST,
        )
        self.assertFalse(missing["ok"])
        self.assertIn("source_ids_required", missing["errors"])

        invented = ao.validateAiRecommendation(
            _ai_recommendation(source_ids=["invented:source"]),
            known_source_ids=KNOWN_SOURCE_IDS,
            now_kst=NOW_KST,
        )
        self.assertFalse(invented["ok"])
        self.assertIn("source_ids_not_grounded", invented["errors"])

    def testQa005SensitivePayloadReviewRejectsSecretsAndAccountDetails(self):
        review = ao.reviewAiRequestPayload(
            {
                "bundle_id": "bundle-001",
                "api_key": "secret-key",
                "account_id": "1234567890",
                "full_article_body": "long copyrighted body",
            }
        )
        self.assertFalse(review["ok"])
        self.assertTrue(any("sensitive" in item for item in review["violations"]))

        nested_account = ao.reviewAiRequestPayload(
            {
                "bundle_id": "bundle-002",
                "account": {"id": "1234567890"},
            }
        )
        self.assertFalse(nested_account["ok"])
        self.assertIn("account.id", nested_account["redacted_fields"])

        nested_credentials = ao.reviewAiRequestPayload(
            {
                "bundle_id": "bundle-003",
                "credentials": {"app_key": "secret-app-key"},
            }
        )
        self.assertFalse(nested_credentials["ok"])
        self.assertIn("credentials.app_key", nested_credentials["redacted_fields"])

    def testQa006AiFailureDoesNotUnlockEntries(self):
        failure = ao.simulateAiFailure("timeout")
        self.assertFalse(failure["entry_unlocked"])
        self.assertEqual(failure["validation_status"], "rejected")
        self.assertEqual(failure["fallback_report"]["entry_unlocked"], False)

    def testQa007AuditRecordCapturesModelLatencyAndValidation(self):
        output = _ai_recommendation()
        validation = ao.validateAiRecommendation(
            output,
            known_source_ids=KNOWN_SOURCE_IDS,
            now_kst=NOW_KST,
        )
        audit = ao.buildAiAuditRecord(
            "deepseek_flash_intraday_label",
            output,
            validation,
            latency_ms=42,
            now_kst=NOW_KST,
        )
        self.assertEqual(audit["model_role"], "deepseek_flash")
        self.assertEqual(audit["prompt_schema_version"], "intraday_candidate_label/v0")
        self.assertEqual(audit["input_bundle_ids"], ["bundle-001"])
        self.assertEqual(audit["latency_ms"], 42)
        self.assertEqual(audit["action"], "watch")
        self.assertEqual(audit["validation_status"], "accepted")
        self.assertFalse(audit["entry_unlocked"])
        self.assertFalse(audit["broker_call_allowed"])

    def testQa008PolicyViolationsRejectAllInCreditAndStopBypassLanguage(self):
        for thesis, expected in (
            ("use all-in sizing on breakout", "risk_policy_violation_detected"),
            ("buy on credit margin", "risk_policy_violation_detected"),
            ("ignore_stop and hold overnight", "risk_policy_violation_detected"),
        ):
            with self.subTest(thesis=thesis):
                result = ao.validateAiRecommendation(
                    _ai_recommendation(thesis=thesis),
                    known_source_ids=KNOWN_SOURCE_IDS,
                    now_kst=NOW_KST,
                )
                self.assertFalse(result["ok"])
                self.assertIn(expected, result["errors"])

    def testQa009DraftOrderIntentRejectsMissingRiskStaleAndAllIn(self):
        missing_risk = ao.validateDraftOrderIntent(
            _draft_order_intent(risk_reference_id=""),
            now_kst=NOW_KST,
        )
        self.assertFalse(missing_risk["ok"])
        self.assertIn("draft_intent_risk_reference_required", missing_risk["errors"])

        stale = ao.validateDraftOrderIntent(
            _draft_order_intent(stale_data=True),
            now_kst=NOW_KST,
        )
        self.assertFalse(stale["ok"])
        self.assertIn("draft_intent_stale_source_forbidden", stale["errors"])

        all_in = ao.validateDraftOrderIntent(
            _draft_order_intent(all_in=True),
            now_kst=NOW_KST,
        )
        self.assertFalse(all_in["ok"])
        self.assertIn("all_in_sizing_forbidden", all_in["errors"])

    def testQa003bPolicyGateRejectsInventedSourceIdsWhenKnownSourcesSupplied(self):
        recommendation = _ai_recommendation(
            action="consider_entry",
            source_ids=["invented:source"],
            draft_order_intent=_draft_order_intent(),
        )
        gate = ao.routeAiRecommendationThroughPolicyGate(
            recommendation,
            entry_intent=_entry_intent(),
            known_source_ids=KNOWN_SOURCE_IDS,
            now_kst=NOW_KST,
        )
        self.assertFalse(gate["ok"])
        self.assertIn("source_ids_not_grounded", gate["blocked_reasons"])

    def testQa004ConsiderEntryViolatingRiskGateIsRejected(self):
        recommendation = _ai_recommendation(
            action="consider_entry",
            draft_order_intent=_draft_order_intent(),
        )
        gate = ao.routeAiRecommendationThroughPolicyGate(
            recommendation,
            entry_intent=_entry_intent(
                available_cash_krw=2_000_000,
                planned_order_cash_krw=1_900_000,
            ),
            now_kst=NOW_KST,
        )
        self.assertFalse(gate["ok"])
        self.assertFalse(gate["entry_unlocked"])
        self.assertIn("minimum_cash_reserve_breach", gate["blocked_reasons"])

    def testQa010PolicyApprovedIntentRecordsNoOrderDryRunOnly(self):
        recommendation = _ai_recommendation(
            action="consider_entry",
            draft_order_intent=_draft_order_intent(),
        )
        gate = ao.routeAiRecommendationThroughPolicyGate(
            recommendation,
            entry_intent=_entry_intent(),
            now_kst=NOW_KST,
        )
        self.assertTrue(gate["ok"], msg=gate.get("blocked_reasons"))
        self.assertFalse(gate["entry_unlocked"])
        self.assertEqual(gate["policy_gate_result"], "approved_no_order_dry_run")
        record = gate["dry_run_record"]
        self.assertTrue(record["no_broker_call"])
        self.assertTrue(record["no_order_submission"])
        self.assertTrue(record["no_simulated_fill"])
        self.assertTrue(record["no_simulated_balance"])
        self.assertTrue(record["no_paper_order"])
        self.assertTrue(record["no_live_order"])
        record_validation = ao.validateAiNoOrderDryRunDecisionRecord(record)
        self.assertTrue(record_validation["ok"], msg=record_validation["errors"])

    def testQa011BrokerEndpointReferencesAreRejected(self):
        for field_name, value in (
            ("thesis", "route to kis paper endpoint"),
            ("risk_notes", "use broker demo testbed"),
            ("draft_order_intent", _draft_order_intent(execution_route="kis_paper")),
        ):
            with self.subTest(field_name=field_name):
                overrides = {field_name: value}
                result = ao.validateAiRecommendation(
                    _ai_recommendation(**overrides),
                    known_source_ids=KNOWN_SOURCE_IDS,
                    now_kst=NOW_KST,
                )
                self.assertFalse(result["ok"])
                self.assertIn("broker_endpoint_reference_forbidden", result["errors"])

    def testQa013GptProFallbackUsesDeepseekOnlyMorningMode(self):
        report = ao.buildAiFallbackReport(
            "chatgpt_pro_morning_review",
            "gpt_pro_unavailable_after_cutoff",
            now_kst="2026-06-04T07:25:00+09:00",
        )
        self.assertEqual(report["alternate_job_id"], "gpt_prompt_0650")
        self.assertEqual(report["morning_review_mode"], "deepseek_only")
        self.assertFalse(report["entry_unlocked"])

    def testQa014DailyCloseReportRequiresSystemCalculatedPnL(self):
        invalid = ao.validateDailyCloseReport(
            {
                "schema_version": "daily_close_report/v0",
                "pnl": {"net_pnl_krw_source": "ai"},
                "ai_interpretation": "explains day",
            }
        )
        self.assertFalse(invalid["ok"])
        self.assertIn("pnl_net_pnl_krw_must_be_system_calculated", invalid["errors"])

        valid = ao.validateDailyCloseReport(
            {
                "schema_version": "daily_close_report/v0",
                "pnl": {
                    "net_pnl_krw": 12000,
                    "net_pnl_krw_source": "system",
                    "gross_pnl_krw_source": "system",
                    "fees_krw_source": "system",
                    "taxes_krw_source": "system",
                },
                "ai_interpretation": "loss driven by one failed candidate",
                "ai_calculated_pnl": False,
            }
        )
        self.assertTrue(valid["ok"], msg=valid["errors"])

    def testQa015ToolUseDisabledAndToolRequestsRejected(self):
        cfg = ao.loadAiOrchestrationConfig()
        self.assertFalse(cfg["AI_TOOL_USE_ENABLED"])
        self.assertFalse(cfg["boundaries"]["tool_use_allowed"])

        result = ao.validateAiRecommendation(
            _ai_recommendation(
                thesis="please browse the web",
                tool_request={"name": "web_search"},
            ),
            known_source_ids=KNOWN_SOURCE_IDS,
            now_kst=NOW_KST,
        )
        self.assertFalse(result["ok"])
        self.assertIn("tool_use_request_forbidden", result["errors"])

    def testQa001ModuleHasNoForbiddenImportsOrBrokerSubmodules(self):
        path = Path(baseDir) / "lib" / "ai_orchestration.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                self.assertNotIn(root, FORBIDDEN_IMPORT_PREFIXES)
                lowered = name.lower()
                for fragment in FORBIDDEN_MODULE_SUBSTRINGS:
                    self.assertNotIn(fragment, lowered)

        self.assertNotIn("def place_order", source)
        self.assertNotIn("def submit_order", source)
        spec = importlib.util.find_spec("lib.ai_orchestration")
        self.assertIsNotNone(spec)


if __name__ == "__main__":
    unittest.main()
