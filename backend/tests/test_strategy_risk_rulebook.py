"""
HWISTOCK-UNIT-004 focused unittest coverage for the strategy/risk rulebook
rebaseline skeleton.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
from pathlib import Path

import unittest

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import strategy_risk as sr  # noqa: E402

NOW_KST = "2026-06-04T09:05:00+09:00"

FORBIDDEN_IMPORT_PREFIXES = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "socket",
    "websocket",
    "pydantic",
    "fastapi",
    "sqlalchemy",
)


def _signal_bundle(**overrides):
    payload = {
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


class StrategyRiskRulebookTests(unittest.TestCase):
    def testQa001Qa011Qa016LoadConfigCurrentAuthorityDefaults(self):
        cfg = sr.loadStrategyRiskConfig()
        self.assertEqual(cfg["starting_capital_krw"], 2_000_000)
        self.assertEqual(cfg["minimum_cash_reserve_ratio"], 0.25)
        self.assertEqual(cfg["max_simultaneous_holdings"], 5)
        self.assertEqual(cfg["max_stop_loss_pct"], -0.05)
        self.assertEqual(cfg["minimum_reward_risk_ratio"], 1.2)
        self.assertEqual(cfg["target_band_pct"]["label"], "per_position_price_move")
        self.assertEqual(cfg["holding_window_minutes"]["hypothesis_min"], 10)
        self.assertEqual(cfg["holding_window_minutes"]["hypothesis_max"], 20)
        self.assertEqual(cfg["holding_window_minutes"]["hard_max"], 30)
        self.assertEqual(cfg["execution_mode"], "no_order_dry_run")
        self.assertTrue(sr.validateStrategyRiskConfig(cfg)["ok"])

    def testQa005ConfigValidationRejectsRuleDrift(self):
        cfg = sr.loadStrategyRiskConfig()
        cfg["minimum_cash_reserve_ratio"] = 0.2
        cfg["max_simultaneous_holdings"] = 4
        cfg["max_stop_loss_pct"] = -0.06
        cfg["execution_mode"] = "kis_paper"
        result = sr.validateStrategyRiskConfig(cfg)
        self.assertFalse(result["ok"])
        self.assertIn("minimum_cash_reserve_ratio_must_be_0_25", result["errors"])
        self.assertIn("max_simultaneous_holdings_must_be_5", result["errors"])
        self.assertIn("max_stop_loss_pct_must_be_minus_5pct", result["errors"])
        self.assertIn("execution_mode_must_be_no_order_dry_run", result["errors"])

    def testQa002ReserveFloorAndAllInAreBlocked(self):
        self.assertEqual(
            sr.computeMaxOrderCashKrw(
                total_capital_krw=2_000_000,
                available_cash_krw=2_000_000,
                minimum_cash_reserve_ratio=0.25,
            ),
            1_500_000,
        )
        result = sr.validateEntryIntent(
            _entry_intent(available_cash_krw=2_000_000, planned_order_cash_krw=1_800_000),
            now_kst=NOW_KST,
        )
        self.assertFalse(result["ok"])
        self.assertIn("minimum_cash_reserve_breach", result["errors"])

        result = sr.validateEntryIntent(
            _entry_intent(available_cash_krw=2_000_000, planned_order_cash_krw=2_000_000),
            now_kst=NOW_KST,
        )
        self.assertFalse(result["ok"])
        self.assertIn("all_in_single_stock_forbidden", result["errors"])

    def testQa003CandidateOnlyIntentRejectsEntryFields(self):
        intent = {
            "intent_type": "candidate_only",
            "watchlist_only": True,
            "symbol": "005930",
            "candidate_reason": "watchlist only",
            "signal_bundle": _signal_bundle(),
            "planned_order_cash_krw": 100_000,
        }
        result = sr.validateCandidateOnlyIntent(intent, now_kst=NOW_KST)
        self.assertFalse(result["ok"])
        self.assertIn("candidate_only_intent_forbidden_field:planned_order_cash_krw", result["errors"])

    def testQa004EntryRequiresStopAndVenueRoute(self):
        missing_stop = sr.validateEntryIntent(
            _entry_intent(stop_loss=None),
            now_kst=NOW_KST,
        )
        self.assertFalse(missing_stop["ok"])
        self.assertIn("stop_loss_required", missing_stop["errors"])

        missing_venue = sr.validateEntryIntent(
            _entry_intent(venue_route=""),
            now_kst=NOW_KST,
        )
        self.assertFalse(missing_venue["ok"])
        self.assertIn("venue_route_required", missing_venue["errors"])

    def testQa006DryRunRecordExplainsDecisionWithoutSimulations(self):
        validation = sr.validateEntryIntent(_entry_intent(), now_kst=NOW_KST)
        self.assertTrue(validation["ok"], msg=validation["errors"])
        record = sr.buildNoOrderDryRunRecord(_entry_intent(), validation, now_kst=NOW_KST)
        self.assertEqual(record["decision"], "approved")
        self.assertEqual(record["execution_mode"], "no_order_dry_run")
        self.assertEqual(record["broker_adapter"], "no_order_dry_run")
        self.assertIn("candidate", record)
        self.assertIn("entry", record)
        self.assertIn("size", record)
        self.assertIn("stop", record)
        self.assertIn("target", record)
        self.assertIn("hold_window", record)
        self.assertEqual(record["rejection_reasons"], [])
        self.assertFalse(record["boundary"]["paper_orders_allowed"])
        self.assertFalse(record["boundary"]["live_orders_allowed"])
        self.assertFalse(record["boundary"]["fake_broker_allowed"])
        validate_record = sr.validateNoOrderDryRunRecord(record)
        self.assertTrue(validate_record["ok"], msg=validate_record["errors"])

    def testQa006ValidEntryPassesWithoutManualBlock(self):
        result = sr.validateEntryIntent(_entry_intent(), now_kst=NOW_KST)
        self.assertTrue(result["ok"], msg=result["errors"])

    def testQa006ManualKillSwitchOrOperatorBlockRejectsEntry(self):
        for overrides in (
            {"manual_kill_switch_active": True},
            {"operator_block_active": True},
        ):
            with self.subTest(overrides=overrides):
                result = sr.validateEntryIntent(_entry_intent(**overrides), now_kst=NOW_KST)
                self.assertFalse(result["ok"])
                self.assertIn("manual_kill_switch_or_operator_block_active", result["errors"])

    def testQa006NestedSafetyOrOperatorControlRejectsEntry(self):
        for overrides in (
            {"operator_control": {"active": True}},
            {"safety_control": {"manual_entry_block_active": True}},
        ):
            with self.subTest(overrides=overrides):
                result = sr.validateEntryIntent(_entry_intent(**overrides), now_kst=NOW_KST)
                self.assertFalse(result["ok"])
                self.assertIn("manual_kill_switch_or_operator_block_active", result["errors"])

    def testQa008AveragingDownIsRejected(self):
        result = sr.validateEntryIntent(
            _entry_intent(
                existing_position_qty=10,
                add_on_buy=True,
                average_entry_price_krw=10_000,
                latest_price_krw=9_700,
            ),
            now_kst=NOW_KST,
        )
        self.assertFalse(result["ok"])
        self.assertIn("averaging_down_forbidden", result["errors"])

    def testQa009ContinuousReentryWithoutFreshSignalIsRejected(self):
        result = sr.validateEntryIntent(
            _entry_intent(
                is_reentry=True,
                fresh_signal=False,
                recent_exit_signal_id="sig-001",
            ),
            now_kst=NOW_KST,
        )
        self.assertFalse(result["ok"])
        self.assertIn("continuous_reentry_without_fresh_signal", result["errors"])

    def testQa012EventFirstRequiresChartConfirmation(self):
        bundle = _signal_bundle(
            source_path="event_first",
            chart_confirmation={"confirmed": False, "reason": ""},
        )
        result = sr.validateEntryIntent(_entry_intent(signal_bundle=bundle), now_kst=NOW_KST)
        self.assertFalse(result["ok"])
        self.assertIn("event_first_requires_chart_confirmation", result["errors"])

    def testQa013ChartFirstCanRemainCandidatePathWithoutEventContext(self):
        bundle = _signal_bundle(
            source_path="chart_first",
            source_ids=[],
        )
        result = sr.validateSignalBundle(bundle, now_kst=NOW_KST)
        self.assertTrue(result["ok"], msg=result["errors"])
        self.assertEqual(result["signal_bundle"]["source_path"], "chart_first")

    def testQa014ForbiddenBrokerRoutesAndFakeFlagsAreRejected(self):
        for overrides, expected in (
            ({"broker_adapter": "kis_paper"}, "broker_adapter_forbidden"),
            ({"execution_route": "fake_broker_router"}, "forbidden_broker_route"),
            ({"flags": {"fake_fill": True}}, "fake_fill_forbidden"),
            ({"flags": {"fake_balance": True}}, "fake_balance_forbidden"),
            ({"flags": {"fake_pnl": True}}, "fake_pnl_forbidden"),
            ({"flags": {"fake_balance_generated": True}}, "fake_balance_generated_forbidden"),
            ({"audit": {"fake_pnl_generated": True}}, "fake_pnl_generated_forbidden"),
        ):
            with self.subTest(expected=expected):
                result = sr.validateEntryIntent(_entry_intent(**overrides), now_kst=NOW_KST)
                self.assertFalse(result["ok"])
                self.assertIn(expected, result["errors"])

    def testQa014DryRunRecordRejectsGeneratedSimulationFlags(self):
        validation = sr.validateEntryIntent(_entry_intent(), now_kst=NOW_KST)
        self.assertTrue(validation["ok"], msg=validation["errors"])
        record = sr.buildNoOrderDryRunRecord(_entry_intent(), validation, now_kst=NOW_KST)
        record["boundary"]["fake_fill_generated"] = True
        record["audit"] = {"fake_balance_generated": True}
        result = sr.validateNoOrderDryRunRecord(record)
        self.assertFalse(result["ok"])
        self.assertIn("fake_fill_generated_forbidden", result["errors"])
        self.assertIn("fake_balance_generated_forbidden", result["errors"])

    def testQa014DryRunRecordRejectsOrderAndFakeBrokerBoundaryTampering(self):
        validation = sr.validateEntryIntent(_entry_intent(), now_kst=NOW_KST)
        self.assertTrue(validation["ok"], msg=validation["errors"])
        for field_name, expected in (
            ("paper_orders_allowed", "record_paper_orders_must_be_disabled"),
            ("live_orders_allowed", "record_live_orders_must_be_disabled"),
            ("fake_broker_allowed", "record_fake_broker_must_be_disabled"),
        ):
            with self.subTest(field_name=field_name):
                record = sr.buildNoOrderDryRunRecord(_entry_intent(), validation, now_kst=NOW_KST)
                record["boundary"][field_name] = True
                result = sr.validateNoOrderDryRunRecord(record)
                self.assertFalse(result["ok"])
                self.assertIn(expected, result["errors"])

    def testQa015AiStopFailuresAreRejected(self):
        cases = [
            (_entry_intent(stop_loss=None), "stop_loss_required"),
            (
                _entry_intent(
                    stop_loss={
                        "source": "ai",
                        "stop_price_krw": 9_600,
                        "proposed_at_kst": NOW_KST,
                        "auditable": False,
                    }
                ),
                "ai_stop_must_be_auditable",
            ),
            (
                _entry_intent(
                    stop_loss={
                        "source": "ai",
                        "stop_price_krw": 9_300,
                        "proposed_at_kst": NOW_KST,
                        "auditable": True,
                    }
                ),
                "ai_stop_wider_than_minus_5pct",
            ),
            (
                _entry_intent(
                    stop_loss={
                        "source": "ai",
                        "stop_price_krw": 9_600,
                        "proposed_at_kst": "2026-06-04T08:30:00+09:00",
                        "auditable": True,
                    }
                ),
                "ai_stop_stale",
            ),
        ]
        for payload, expected in cases:
            with self.subTest(expected=expected):
                result = sr.validateEntryIntent(payload, now_kst=NOW_KST)
                self.assertFalse(result["ok"])
                self.assertIn(expected, result["errors"])

    def testP0StaleSignalDataIsRejected(self):
        result = sr.validateEntryIntent(
            _entry_intent(
                signal_bundle=_signal_bundle(
                    generated_at_kst="2026-06-04T08:30:00+09:00",
                    chart_timestamp_kst="2026-06-04T08:29:00+09:00",
                )
            ),
            now_kst=NOW_KST,
        )
        self.assertFalse(result["ok"])
        self.assertIn("signal_bundle_stale_data", result["errors"])

    def testStdlibOnlyModuleHasNoForbiddenImports(self):
        path = Path(baseDir) / "lib" / "strategy_risk.py"
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
                self.assertNotIn(root, FORBIDDEN_IMPORT_PREFIXES)

        spec = importlib.util.find_spec("lib.strategy_risk")
        self.assertIsNotNone(spec)
