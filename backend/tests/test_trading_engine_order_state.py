"""
HWISTOCK-UNIT-006 focused unittest coverage for the current-authority rebaseline
trading engine/order-state foundation skeleton.
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

from lib import trading_engine as te  # noqa: E402

NOW_KST = "2026-06-04T09:05:00+09:00"

FORBIDDEN_IMPORT_PREFIXES = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "socket",
    "websocket",
    "fastapi",
    "pydantic",
    "sqlalchemy",
    "openai",
)
FORBIDDEN_MODULE_SUBSTRINGS = (
    "kis_client",
    "broker",
    "trading_router",
    "order_router",
    "paper_adapter",
    "live_adapter",
)


def _signal_bundle():
    return {
        "signal_id": "sig-001",
        "source_path": "combined",
        "source_ids": ["dart_openapi_disclosures:20260604-1"],
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


def _condition_card(**overrides):
    payload = {
        "schema_version": "condition_card/v0",
        "candidate_id": "candidate-001",
        "symbol": "005930",
        "source_ids": ["dart_openapi_disclosures:20260604-1"],
        "created_at_kst": "2026-06-04T09:00:00+09:00",
        "valid_until_kst": "2026-06-04T09:30:00+09:00",
        "venue_route": "KRX",
        "watch_conditions": [
            {
                "type": "price_cross",
                "operator": "gte",
                "threshold_price_krw": 10000,
            },
            {
                "type": "source_freshness",
                "max_age_seconds": 300,
            },
        ],
        "risk_refs": [
            "minimum_cash_reserve_ratio",
            "max_simultaneous_holdings",
            "ai_stop_validation",
        ],
        "entry_intent": _entry_intent(),
        "exit_plan": {
            "stop_loss_ref": "ai-stop",
            "target_band_ref": "1-5pct",
            "time_stop_kst": "19:50",
        },
    }
    payload.update(overrides)
    return payload


class TradingEngineOrderStateTests(unittest.TestCase):
    def testQa001Qa007ValidConditionCardCompilesButRemainsNonExecutable(self):
        validation = te.validateConditionCard(_condition_card(), now_kst=NOW_KST)
        self.assertTrue(validation["ok"], msg=validation["errors"])
        compiled = te.compileConditionCard(_condition_card(), now_kst=NOW_KST)
        self.assertTrue(compiled["ok"], msg=compiled["errors"])
        self.assertEqual(compiled["compiled_watch"]["schema_version"], "compiled_watch/v0")
        self.assertEqual(compiled["compiled_watch"]["watch_state"], "compiled_watch")
        self.assertTrue(compiled["compiled_watch"]["non_executable"])
        self.assertTrue(compiled["compiled_watch"]["no_broker_call"])
        self.assertTrue(te.isAiCandidateNonExecutable(validation["card"]))
        self.assertTrue(te.isAiCandidateNonExecutable(compiled["compiled_watch"]))

    def testQa002VagueNaturalLanguageConditionsAreRejected(self):
        result = te.validateConditionCard(
            _condition_card(
                watch_conditions=[
                    {"type": "natural_language", "text": "looks good"},
                    {"type": "price_cross", "note": "looks good"},
                ]
            ),
            now_kst=NOW_KST,
        )
        self.assertFalse(result["ok"])
        self.assertIn("watch_condition_vague_natural_language_only:0", result["errors"])
        self.assertIn("watch_condition_vague_natural_language_only:1", result["errors"])

    def testQa003RiskGateDelegatesToStrategyRiskRulebook(self):
        ok_result = te.evaluateEntryRiskGate(_entry_intent(), now_kst=NOW_KST)
        self.assertTrue(ok_result["ok"], msg=ok_result["blocked_reasons"])
        self.assertEqual(ok_result["risk_gate_result"], "pass")
        self.assertEqual(ok_result["next_state"], "eligible")
        self.assertEqual(ok_result["requested_venue_route"], "KRX")
        self.assertEqual(ok_result["risk_gate_venue_route"], "KRX")
        self.assertEqual(ok_result["venue_resolution_status"], "direct_foundation_route")

        blocked = te.evaluateEntryRiskGate(
            _entry_intent(
                available_cash_krw=2_000_000,
                planned_order_cash_krw=1_800_000,
            ),
            now_kst=NOW_KST,
        )
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["risk_gate_result"], "blocked")
        self.assertIn("minimum_cash_reserve_breach", blocked["blocked_reasons"])
        self.assertEqual(blocked["next_state"], "blocked")

    def testQa003Qa006RouteNormalizationPreservesMetadataAndBlocksUnresolvedAutoSession(self):
        sor_result = te.evaluateEntryRiskGate(
            _entry_intent(venue_route="SOR"),
            now_kst=NOW_KST,
        )
        self.assertTrue(sor_result["ok"], msg=sor_result["blocked_reasons"])
        self.assertEqual(sor_result["requested_venue_route"], "SOR")
        self.assertEqual(sor_result["risk_gate_venue_route"], "KRX")
        self.assertEqual(
            sor_result["venue_resolution_status"],
            "normalized_sor_to_krx_for_foundation",
        )
        self.assertEqual(sor_result["validation"]["intent"]["venue_route"], "KRX")

        auto_blocked = te.evaluateEntryRiskGate(
            _entry_intent(venue_route="AUTO_SESSION", session_venue_hint=""),
            now_kst=NOW_KST,
        )
        self.assertFalse(auto_blocked["ok"])
        self.assertEqual(auto_blocked["requested_venue_route"], "AUTO_SESSION")
        self.assertEqual(auto_blocked["risk_gate_venue_route"], None)
        self.assertEqual(auto_blocked["venue_resolution_status"], "blocked_auto_session_unresolved")
        self.assertIn(
            "auto_session_requires_resolved_underlying_venue",
            auto_blocked["blocked_reasons"],
        )

        auto_nxt = te.evaluateEntryRiskGate(
            _entry_intent(venue_route="AUTO_SESSION", session_venue_hint="NXT"),
            now_kst=NOW_KST,
        )
        self.assertTrue(auto_nxt["ok"], msg=auto_nxt["blocked_reasons"])
        self.assertEqual(auto_nxt["requested_venue_route"], "AUTO_SESSION")
        self.assertEqual(auto_nxt["risk_gate_venue_route"], "NXT")
        self.assertEqual(auto_nxt["venue_resolution_status"], "resolved_auto_session_from_hint")
        self.assertEqual(auto_nxt["validation"]["intent"]["venue_route"], "NXT")

    def testQa004ExplicitOrderStateSkeletonRejectsFoundationSubmittedPath(self):
        foundation_ok = te.validateOrderStateTransition("compiled_watch", "dry_run_recorded")
        self.assertTrue(foundation_ok["ok"], msg=foundation_ok["errors"])
        self.assertEqual(foundation_ok["execution_boundary"], "no_order_dry_run_foundation")

        blocked = te.validateOrderStateTransition("eligible", "submitted")
        self.assertFalse(blocked["ok"])
        self.assertIn("foundation_scope_rejects_submitted_or_later", blocked["errors"])

        approved = te.validateOrderStateTransition(
            "eligible",
            "submitted",
            approved_adapter_enabled=True,
        )
        self.assertTrue(approved["ok"], msg=approved["errors"])
        self.assertFalse(approved["state_update_executed"])
        self.assertEqual(approved["execution_boundary"], "representation_only_adapter_metadata")
        late_states = (
            ("submitted", "accepted"),
            ("accepted", "partial_fill"),
            ("accepted", "failed"),
            ("submitted", "rejected"),
            ("rejected", "retrying"),
            ("submitted", "cancel_requested"),
            ("cancel_requested", "cancelled"),
        )
        for from_state, to_state in late_states:
            with self.subTest(from_state=from_state, to_state=to_state):
                result = te.validateOrderStateTransition(
                    from_state,
                    to_state,
                    approved_adapter_enabled=True,
                )
                self.assertTrue(result["ok"], msg=result["errors"])
                self.assertFalse(result["state_update_executed"])
                self.assertEqual(result["execution_boundary"], "representation_only_adapter_metadata")

    def testQa005DryRunDecisionRecordIsNoOrderOnlyAndRejectsBrokerishFields(self):
        record = te.buildNoOrderDryRunDecisionRecord(
            candidate_id="candidate-001",
            condition_card_id="candidate-001",
            decision="would_enter",
            would_venue_route="KRX",
            would_order_side="buy",
            would_order_price_type="limit",
            would_cash_amount_krw=1_150_000,
            risk_gate_result={"ok": True, "rulebook": "HWISTOCK-MOD-003"},
            blocked_reasons=[],
            created_at_kst=NOW_KST,
        )
        validation = te.validateNoOrderDryRunDecisionRecord(record)
        self.assertTrue(validation["ok"], msg=validation["errors"])
        self.assertTrue(record["no_broker_call"])
        self.assertTrue(record["no_simulated_fill"])
        self.assertTrue(record["no_simulated_balance"])
        self.assertTrue(record["no_simulated_pnl"])
        self.assertTrue(record["no_paper_order"])
        self.assertTrue(record["no_live_order"])

        invalid = dict(record)
        invalid.update(
            {
                "broker_order_id": "forbidden",
                "order_id": "kis-order-no-001",
                "fake_fill_generated": False,
                "no_broker_call": False,
            }
        )
        invalid_result = te.validateNoOrderDryRunDecisionRecord(invalid)
        self.assertFalse(invalid_result["ok"])
        self.assertIn("broker_order_id_forbidden", invalid_result["errors"])
        self.assertIn("broker_like_order_id_forbidden", invalid_result["errors"])
        self.assertIn("forbidden_record_field:fake_fill_generated", invalid_result["errors"])
        self.assertIn("no_broker_call_must_be_true", invalid_result["errors"])

    def testQa006Qa008VenueRoutesShareStateMachineAndUnsupportedPaperBranchesStayDisabled(self):
        capabilities = te.loadKisPaperCapabilityFlags()
        self.assertTrue(capabilities["supports_paper_krx_order"])
        self.assertTrue(capabilities["supports_paper_krx_realtime"])
        self.assertFalse(capabilities["supports_paper_nxt_order"])
        self.assertFalse(capabilities["supports_paper_sor_order"])
        self.assertFalse(capabilities["supports_paper_integrated_realtime"])
        self.assertFalse(capabilities["supports_paper_cancelable_query"])

        dry_run_routes = [
            te.resolveVenueRoute(route, mode="no_order_dry_run")
            for route in ("KRX", "NXT", "SOR", "AUTO_SESSION")
        ]
        first_state_machine = dry_run_routes[0]["state_machine"]
        for resolved in dry_run_routes:
            with self.subTest(route=resolved["route"]):
                self.assertTrue(resolved["ok"], msg=resolved["errors"])
                self.assertEqual(resolved["state_machine"], first_state_machine)
                self.assertEqual(resolved["branch_status"], "local_fallback")
                self.assertTrue(resolved["no_broker_call"])

        nxt = te.resolveVenueRoute("NXT", mode="kis_paper")
        sor = te.resolveVenueRoute("SOR", mode="kis_paper")
        auto = te.resolveVenueRoute("AUTO_SESSION", mode="kis_paper")
        self.assertEqual(nxt["branch_status"], "disabled_branch")
        self.assertEqual(sor["branch_status"], "disabled_branch")
        self.assertEqual(auto["branch_status"], "local_fallback")
        self.assertFalse(nxt["broker_capability_enabled"])
        self.assertFalse(sor["broker_capability_enabled"])

    def testQa009KisPaperEvidenceEventsStayRepresentationOnly(self):
        for mapped_state in ("submitted", "accepted", "rejected", "retrying", "failed"):
            order_event = te.representKisPaperEvidenceEvent(
                {"event_kind": "order", "mapped_order_state": mapped_state, "source": "fixture"}
            )
            self.assertEqual(order_event["mapped_order_state"], mapped_state)
            self.assertTrue(order_event["no_broker_call"])
            self.assertFalse(order_event["state_update_executed"])

        for mapped_state in ("partial_fill", "filled"):
            fill_event = te.representBrokerEventState(
                {"event_kind": "fill", "mapped_order_state": mapped_state, "source": "fixture"}
            )
            self.assertEqual(fill_event["mapped_order_state"], mapped_state)
            self.assertTrue(fill_event["no_broker_call"])
            self.assertFalse(fill_event["state_update_executed"])

        for mapped_state in ("cancel_requested", "cancelled", "rejected", "failed"):
            cancel_event = te.representKisPaperEvidenceEvent(
                {"event_kind": "cancel", "mapped_order_state": mapped_state, "source": "fixture"}
            )
            self.assertEqual(cancel_event["mapped_order_state"], mapped_state)
            self.assertTrue(cancel_event["no_broker_call"])
            self.assertFalse(cancel_event["state_update_executed"])

        balance_event = te.representKisPaperEvidenceEvent(
            {"event_kind": "balance", "cash_krw": 2_000_000}
        )
        helper_event = te.representKisPaperEvidenceEvent(
            {"event_kind": "helper", "helper_name": "sellable_quantity_query"}
        )
        disabled_event = te.representKisPaperEvidenceEvent({"event_kind": "disabled_branch"})
        fallback_event = te.representKisPaperEvidenceEvent({"event_kind": "local_fallback"})

        for event in (balance_event, helper_event, disabled_event, fallback_event):
            self.assertTrue(event["no_broker_call"])
            self.assertFalse(event["state_update_executed"])
            self.assertTrue(event["no_simulated_fill"])
            self.assertTrue(event["no_simulated_balance"])
            self.assertTrue(event["no_simulated_pnl"])

        self.assertEqual(balance_event["mapped_order_state"], None)
        self.assertEqual(helper_event["event_kind"], "local_fallback")
        self.assertEqual(disabled_event["mapped_order_state"], None)
        self.assertEqual(fallback_event["mapped_order_state"], None)

        with self.assertRaisesRegex(ValueError, "mapped_order_state_required_for_order_fill_cancel"):
            te.representKisPaperEvidenceEvent({"event_kind": "order"})
        with self.assertRaisesRegex(ValueError, "mapped_order_state_required_for_order_fill_cancel"):
            te.representKisPaperEvidenceEvent(
                {"event_kind": "order", "mapped_order_state": "filled"}
            )
        with self.assertRaisesRegex(ValueError, "mapped_order_state_required_for_order_fill_cancel"):
            te.representKisPaperEvidenceEvent(
                {"event_kind": "fill", "mapped_order_state": "submitted"}
            )
        with self.assertRaisesRegex(ValueError, "mapped_order_state_required_for_order_fill_cancel"):
            te.representKisPaperEvidenceEvent(
                {"event_kind": "cancel", "mapped_order_state": "accepted"}
            )
        with self.assertRaisesRegex(ValueError, "balance_event_cannot_set_order_state"):
            te.representKisPaperEvidenceEvent(
                {"event_kind": "balance", "mapped_order_state": "accepted"}
            )
        with self.assertRaisesRegex(ValueError, "helper_event_cannot_set_order_state"):
            te.representKisPaperEvidenceEvent(
                {"event_kind": "helper", "helper_name": "sellable_quantity_query", "mapped_order_state": "retrying"}
            )
        with self.assertRaisesRegex(ValueError, "fallback_event_cannot_set_order_state"):
            te.representKisPaperEvidenceEvent(
                {"event_kind": "disabled_branch", "mapped_order_state": "failed"}
            )

    def testQa010FoundationSmokeKeepsModuleLocalAndNonNetworked(self):
        module_path = Path(baseDir) / "lib" / "trading_engine.py"
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
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
                    msg=f"trading_engine.py imports forbidden module {name}",
                )
                lowered = name.lower()
                for fragment in FORBIDDEN_MODULE_SUBSTRINGS:
                    self.assertNotIn(
                        fragment.lower(),
                        lowered,
                        msg=f"trading_engine.py imports forbidden module fragment {name}",
                    )

        spec = importlib.util.find_spec("lib.trading_engine")
        self.assertIsNotNone(spec)

        config = te.loadTradingEngineConfig()
        self.assertEqual(config["execution_mode"], "no_order_dry_run")
        self.assertFalse(config["boundaries"]["broker_calls_allowed"])
        self.assertFalse(config["boundaries"]["fill_simulation_allowed"])
        self.assertIn("submitted", config["late_executable_states"])
        self.assertIn("accepted", config["representation_only_states"])
        self.assertFalse(
            te.isAiCandidateNonExecutable(
                {"state": "submitted", "no_broker_call": True, "no_paper_order": True}
            )
        )


if __name__ == "__main__":
    unittest.main()
