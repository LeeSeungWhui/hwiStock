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


def _morning_watchlist(**overrides):
    payload = {
        "schema_version": "morning_watchlist/v1",
        "artifact_id": "art_morning_watchlist_20260604_0715",
        "route": "codex_cli_local_browser_use",
        "target_trade_date_kst": "2026-06-04",
        "generated_at_kst": "2026-06-04T07:15:00+09:00",
        "purpose": "daily_preopen_final",
        "requires_monday_refresh": False,
        "forbidden_actions_acknowledged": True,
        "items": [{"ticker": "005930", "stance": "eligible_for_flash_review"}],
    }
    payload.update(overrides)
    return payload


def _ai_recommendation(**overrides):
    payload = {
        "schema_version": "ai_recommendation/v0",
            "job_id": "deepseek_flash_trade_document_10m",
            "model_role": "deepseek_flash",
            "model_name": "deepseek-v4-flash",
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
        self.assertEqual(cfg["GPT_PRO_MORNING_REVIEW_START_KST"], "07:15")
        self.assertEqual(cfg["GPT_PRO_APPROVED_ROUTE"], "codex_cli_local_browser_use")
        self.assertTrue(cfg["MORNING_WATCHLIST_REQUIRED_BEFORE_FIRST_FLASH"])
        self.assertEqual(cfg["DEEPSEEK_PRO_MODEL"], "deepseek-v4-pro")
        self.assertEqual(cfg["DEEPSEEK_FLASH_MODEL"], "deepseek-v4-flash")
        self.assertTrue(ao.validateAiOrchestrationConfig(cfg)["ok"])

    def testQa012JobRegistrySeparatesScheduledRoles(self):
        registry = ao.getAiJobRegistry()
        self.assertEqual(
            set(registry.keys()),
            {
                "deepseek_pro_hourly",
                "deepseek_flash_trade_document_10m",
                "gpt_morning_watchlist_0715",
                "daily_close_mode_aware",
            },
        )
        self.assertEqual(
            registry["deepseek_pro_hourly"]["output_schema"],
            "pro_hourly_market_analysis/v1",
        )
        self.assertTrue(registry["deepseek_pro_hourly"]["includes_market_regime"])
        self.assertEqual(registry["deepseek_flash_trade_document_10m"]["model_name"], "deepseek-v4-flash")
        self.assertEqual(registry["deepseek_flash_trade_document_10m"]["max_action_symbols"], 5)
        self.assertEqual(
            registry["gpt_morning_watchlist_0715"]["output_schema"],
            "morning_watchlist/v1",
        )
        self.assertEqual(registry["gpt_morning_watchlist_0715"]["approved_route"], "codex_cli_local_browser_use")
        self.assertFalse(registry["gpt_morning_watchlist_0715"]["ssh_browser_use_allowed"])
        self.assertEqual(registry["daily_close_mode_aware"]["output_schema"], "daily_close_report/v0")
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
            "deepseek_flash_trade_document_10m",
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
            "gpt_morning_watchlist_0715",
            "gpt_pro_unavailable_before_first_flash",
            now_kst="2026-06-04T07:25:00+09:00",
        )
        self.assertEqual(report["alternate_job_id"], "deepseek_pro_hourly")
        self.assertEqual(report["morning_review_mode"], "deepseek_only")
        self.assertFalse(report["entry_unlocked"])

    def testQa012FlashTradeDocumentCapsActionsAndRequiresCompiledWatch(self):
        compiled_watch = [
            {
                "schema_version": "compiled_watch/v0",
                "candidate_id": f"candidate-{index}",
                "symbol": f"00593{index}",
                "source_ids": KNOWN_SOURCE_IDS,
                "entry_intent": {
                    "entry_zone": [10000, 10100],
                    "take_profit": 10500,
                    "stop_loss": 9800,
                    "trailing_stop_pct": 1.2,
                    "position_size_pct": 20,
                },
                "valid_until_kst": "2026-06-04T09:20:00+09:00",
            }
            for index in range(7)
        ]
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260604_0900"},
            recent_events=[{"source_event_id": KNOWN_SOURCE_IDS[0]}],
            kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260604_0905"}],
            compiled_watch=compiled_watch,
            portfolio_snapshot={"artifact_id": "art_portfolio_20260604_0905", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260604_0905", "pending_orders": []},
            morning_watchlist=_morning_watchlist(),
            produced_at_kst=NOW_KST,
        )
        self.assertEqual(doc["schema_version"], "flash_trade_document/v1")
        self.assertEqual(doc["model_name"], "deepseek-v4-flash")
        self.assertLessEqual(len(doc["actions"]), 5)
        self.assertRegex(doc["actions"][0]["action_id"], r"^act_\d{6}_\d{4}_\d{2}$")
        validation = ao.validateFlashTradeDocument(doc, compiled_watch=compiled_watch)
        self.assertTrue(validation["ok"], msg=validation["errors"])
        self.assertFalse(doc["no_broker_call"] is False)

    def testQa012OffUniverseFlashActionIsRejected(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260604_0900"},
            recent_events=[{"source_event_id": KNOWN_SOURCE_IDS[0]}],
            kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260604_0905"}],
            compiled_watch=[{"schema_version": "compiled_watch/v0", "symbol": "005930", "source_ids": KNOWN_SOURCE_IDS}],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260604_0905", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260604_0905", "pending_orders": []},
            morning_watchlist=_morning_watchlist(),
            produced_at_kst=NOW_KST,
        )
        doc["actions"][0]["ticker"] = "999999"
        validation = ao.validateFlashTradeDocument(
            doc,
            compiled_watch=[{"schema_version": "compiled_watch/v0", "symbol": "005930"}],
        )
        self.assertFalse(validation["ok"])
        self.assertIn("actions_item_0_off_universe_ticker", validation["errors"])

    def testQa012FirstFlashRequiresMorningWatchlistOrSafeBlock(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260604_0900"},
            recent_events=[{"source_event_id": KNOWN_SOURCE_IDS[0]}],
            kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260604_0905"}],
            compiled_watch=[{"schema_version": "compiled_watch/v0", "symbol": "005930", "source_ids": KNOWN_SOURCE_IDS}],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260604_0905", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260604_0905", "pending_orders": []},
            produced_at_kst=NOW_KST,
        )
        self.assertEqual(doc["document_kind"], "NO_TRADE")
        self.assertEqual(doc["no_trade_reason"], "missing_morning_watchlist_for_first_flash_bucket")
        self.assertTrue(doc["morning_watchlist_required"])

    def testQa012FirstFlashMarksSundayRehearsalAsProvisionalWithoutNoTrade(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260608_0900"},
            recent_events=[{"source_event_id": KNOWN_SOURCE_IDS[0]}],
            kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260608_0900"}],
            compiled_watch=[{"schema_version": "compiled_watch/v0", "symbol": "005930", "source_ids": KNOWN_SOURCE_IDS}],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260608_0900", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260608_0900", "pending_orders": []},
            morning_watchlist=_morning_watchlist(
                artifact_id="art_morning_watchlist_20260608_sunday_rehearsal",
                target_trade_date_kst="2026-06-08",
                generated_at_kst="2026-06-07T11:33:00+09:00",
                purpose="monday_preopen_rehearsal_late",
                non_trading_day_carryover=True,
                requires_monday_refresh=True,
            ),
            produced_at_kst="2026-06-08T09:00:00+09:00",
        )
        self.assertEqual(doc["document_kind"], "TRADE_ACTIONS")
        self.assertEqual(doc["morning_watchlist_ref"], "art_morning_watchlist_20260608_sunday_rehearsal")
        self.assertTrue(doc["morning_watchlist_required"])
        self.assertEqual(doc["morning_watchlist_status"], "provisional")
        self.assertTrue(doc["morning_watchlist_refresh_required"])
        self.assertIn("monday_final_morning_watchlist_refresh_recommended", doc["morning_watchlist_warnings"])
        self.assertIn("morning_watchlist_is_rehearsal_or_candidate", doc["morning_watchlist_warnings"])
        self.assertIn("morning_watchlist_generated_before_trade_date", doc["morning_watchlist_warnings"])
        self.assertEqual(doc["actions"][0]["action"], "WAIT_BUY")

    def testQa012FirstFlashMarksWatchlistGeneratedBeforeTradeDateAsProvisional(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260608_0900"},
            recent_events=[{"source_event_id": KNOWN_SOURCE_IDS[0]}],
            kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260608_0900"}],
            compiled_watch=[{"schema_version": "compiled_watch/v0", "symbol": "005930", "source_ids": KNOWN_SOURCE_IDS}],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260608_0900", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260608_0900", "pending_orders": []},
            morning_watchlist=_morning_watchlist(
                artifact_id="art_morning_watchlist_20260608_stale_sunday",
                target_trade_date_kst="2026-06-08",
                generated_at_kst="2026-06-07T11:33:00+09:00",
                purpose="daily_preopen_final",
                requires_monday_refresh=False,
            ),
            produced_at_kst="2026-06-08T09:00:00+09:00",
        )
        self.assertEqual(doc["document_kind"], "TRADE_ACTIONS")
        self.assertEqual(doc["morning_watchlist_ref"], "art_morning_watchlist_20260608_stale_sunday")
        self.assertEqual(doc["morning_watchlist_status"], "provisional")
        self.assertIn("morning_watchlist_generated_before_trade_date", doc["morning_watchlist_warnings"])
        self.assertEqual(doc["actions"][0]["action"], "WAIT_BUY")

    def testQa012FlashUsesKisCompiledWatchWhenAvailable(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260604_0900"},
            recent_events=[{"source_event_id": KNOWN_SOURCE_IDS[0]}],
            kis_market_snapshots=[{"artifact_id": "art_kis_snapshot_20260604_0905"}],
            compiled_watch=[{"schema_version": "compiled_watch/v0", "symbol": "005930", "source_ids": KNOWN_SOURCE_IDS}],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260604_0905", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260604_0905", "pending_orders": []},
            morning_watchlist=_morning_watchlist(),
            produced_at_kst=NOW_KST,
        )

        self.assertEqual(doc["candidate_universe_source"], "kis_compiled_watch")
        self.assertEqual(doc["candidate_universe_count"], 1)
        self.assertNotIn("kis_compiled_watch_empty_using_morning_watchlist_fallback", doc.get("warnings", []))

    def testQa012FlashUsesGptMorningProvisionalUniverseWhenKisCompiledEmpty(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260604_0900"},
            recent_events=[],
            kis_market_snapshots=[],
            compiled_watch=[],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260604_0905", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260604_0905", "pending_orders": []},
            morning_watchlist=_morning_watchlist(
                items=[
                    {
                        "ticker": "005930",
                        "name": "삼성전자",
                        "stance": "eligible_for_flash_review",
                        "thesis": "장전 후보",
                        "source_refs": [KNOWN_SOURCE_IDS[0]],
                    }
                ]
            ),
            provider_actions=[
                {
                    "symbol": "005930",
                    "action": "WAIT_BUY",
                    "entry_price_limit": 70000,
                    "target_price": 72100,
                    "stop_loss_price": 67900,
                    "planned_order_cash_krw": 100000,
                    "confidence": 0.55,
                }
            ],
            produced_at_kst=NOW_KST,
        )
        validation = ao.validateFlashTradeDocument(doc)

        self.assertEqual(doc["document_kind"], "TRADE_ACTIONS")
        self.assertEqual(doc["candidate_universe_source"], "gpt_morning_watchlist_provisional")
        self.assertEqual(doc["candidate_universe_count"], 1)
        self.assertIn("kis_compiled_watch_empty_using_morning_watchlist_fallback", doc["warnings"])
        self.assertEqual(doc["actions"][0]["action_source"], "deepseek_flash_provider")
        self.assertTrue(validation["ok"], msg=validation["errors"])

    def testQa012NoTradeOnlyWhenBothKisAndMorningUniverseEmpty(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260604_0900"},
            recent_events=[],
            kis_market_snapshots=[],
            compiled_watch=[],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260604_0905", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260604_0905", "pending_orders": []},
            morning_watchlist=_morning_watchlist(items=[]),
            produced_at_kst=NOW_KST,
        )

        self.assertEqual(doc["document_kind"], "NO_TRADE")
        self.assertEqual(doc["no_trade_reason"], "missing_compiled_watch_candidate_universe")
        self.assertEqual(doc["candidate_universe_source"], "none")
        self.assertEqual(doc["candidate_universe_count"], 0)

    def testQa012GptFallbackWithoutKisQuoteDowngradesBuyNowToWaitBuy(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260604_0900"},
            recent_events=[],
            kis_market_snapshots=[],
            compiled_watch=[],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260604_0905", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260604_0905", "pending_orders": []},
            morning_watchlist=_morning_watchlist(items=[{"ticker": "005930", "stance": "eligible_for_flash_review", "source_refs": [KNOWN_SOURCE_IDS[0]]}]),
            provider_actions=[{"symbol": "005930", "action": "BUY_NOW", "entry_price_limit": 70000, "target_price": 72100, "stop_loss_price": 67900, "planned_order_cash_krw": 100000, "confidence": 0.8}],
            produced_at_kst=NOW_KST,
        )

        action = doc["actions"][0]
        self.assertEqual(action["action"], "WAIT_BUY")
        self.assertTrue(action["requires_kis_confirmation_before_order"])
        self.assertFalse(action["kis_quote_confirmed"])
        self.assertIn("gpt_morning_fallback_buy_now_downgraded_until_kis_quote_confirmed", action["risk_flags"])

    def testQa012GptFallbackWithKisQuoteAllowsValidBuyNow(self):
        doc = ao.buildFlashTradeDocument(
            pro_artifact={"artifact_id": "art_pro_hourly_20260604_0900"},
            recent_events=[],
            kis_market_snapshots=[
                {
                    "artifact_id": "art_kis_snapshot_20260604_0905",
                    "input_results": [
                        {
                            "input_id": "krx_realtime_trade_price_ws",
                            "rows_preview": [
                                {"stck_shrn_iscd": "005930", "stck_prpr": "70000", "askp1": "70100", "bidp1": "70000"}
                            ],
                        }
                    ],
                }
            ],
            compiled_watch=[],
            portfolio_snapshot={"artifact_id": "art_portfolio_20260604_0905", "holdings": []},
            order_state_snapshot={"artifact_id": "art_order_state_20260604_0905", "pending_orders": []},
            morning_watchlist=_morning_watchlist(items=[{"ticker": "005930", "stance": "eligible_for_flash_review", "source_refs": [KNOWN_SOURCE_IDS[0]]}]),
            provider_actions=[{"symbol": "005930", "action": "BUY_NOW", "quantity": 1, "entry_price_limit": 70000, "target_price": 72100, "stop_loss_price": 67900, "planned_order_cash_krw": 100000, "confidence": 0.8}],
            produced_at_kst=NOW_KST,
        )
        validation = ao.validateFlashTradeDocument(doc)

        action = doc["actions"][0]
        self.assertEqual(action["action"], "BUY_NOW")
        self.assertTrue(action["kis_quote_confirmed"])
        self.assertTrue(action["kis_orderbook_confirmed"])
        self.assertTrue(validation["ok"], msg=validation["errors"])

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
