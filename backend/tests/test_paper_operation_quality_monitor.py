"""
Read-only paper-operation quality monitor tests.

These tests encode the next-session P0 checks from the first paper experiment
review. They use only local JSON fixtures and never call KIS, brokers, AI, or
browser providers.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

baseDir = os.path.dirname(os.path.dirname(__file__))
if baseDir not in sys.path:
    sys.path.insert(0, baseDir)

from lib import paper_operation_quality_monitor as monitor  # noqa: E402


DAY = "2026-06-10"


def _write_json(root: Path, rel: str, payload: dict) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_compiled_watch(root: Path, *, count: int = 1) -> None:
    items = [
        {
            "schema_version": "compiled_watch/v0",
            "symbol": "005930",
            "entry_intent": {"position_size_pct": 10, "sizing_basis": "position_size_pct"},
        }
    ][:count]
    _write_json(
        root,
        f"compiled-watch/{DAY}/compiled-watch-latest.json",
        {
            "schema_version": "compiled_watch_batch/v0",
            "producer": "kis_intraday_market_collector",
            "produced_at_kst": f"{DAY}T09:10:00+09:00",
            "candidate_count": count,
            "items": items,
        },
    )


def _write_kis_market(root: Path, *, count: int = 1) -> None:
    _write_json(
        root,
        f"kis-market/{DAY}/kis-market-snapshot-latest.json",
        {
            "produced_at_kst": f"{DAY}T09:10:00+09:00",
            "compiled_watch": {"candidate_count": count, "items": [{} for _ in range(count)]},
            "input_results": [{"input_id": "rest_volume_rank", "status": "pass", "row_count": count}],
        },
    )


def _write_flash(root: Path, payload: dict) -> None:
    base = {
        "schema_version": "flash_trade_document/v1",
        "artifact_id": "art_flash_quality_test",
        "produced_at_kst": f"{DAY}T09:10:00+09:00",
        "document_kind": "TRADE_ACTIONS",
        "validation_status": "accepted",
        "provider_status": "ok",
        "candidate_universe_source": "kis_compiled_watch",
        "candidate_universe_count": 1,
        "actions": [],
        "position_actions": [],
        "paper_intent_pipeline": {"accepted_count": 0, "accepted_intents": []},
    }
    base.update(payload)
    _write_json(root, f"trade-documents/{DAY}/flash-trade-document-latest.json", base)


def _write_morning_watchlist(root: Path, payload: dict) -> None:
    base = {
        "schema_version": "morning_watchlist/v1",
        "artifact_id": "art_morning_quality_test",
        "target_trade_date_kst": DAY,
        "generated_at_kst": f"{DAY}T07:15:00+09:00",
        "validation_status": "accepted",
        "items": [{"ticker": "005930", "stance": "eligible_for_flash_review"}],
    }
    base.update(payload)
    _write_json(root, f"morning-watchlist/{DAY}/morning-watchlist-latest.json", base)


def _write_gpt_morning_health(root: Path, *, prompt_status: str = "ok", publish_status: str = "accepted") -> None:
    _write_json(
        root,
        f"evidence/{DAY}/gpt-morning-prompt-health.json",
        {"event": "gpt_morning_prompt_health", "status": prompt_status, "target_trade_date_kst": DAY},
    )
    _write_json(
        root,
        f"evidence/{DAY}/morning-watchlist-publish-health.json",
        {"event": "morning_watchlist_publish_health", "status": publish_status, "target_trade_date_kst": DAY},
    )


def _write_runner(root: Path, payload: dict | None = None) -> None:
    base = {
        "timestamp_kst": f"{DAY}T09:10:00+09:00",
        "intent_loaded": False,
        "loaded_intent": None,
        "base_runner_order_gate": "open",
        "account_truth": {},
        "steps": [],
    }
    if payload:
        base.update(payload)
    _write_json(root, f"evidence/{DAY}/kis-paper-continuous-latest.json", base)


def _at(value: str = f"{DAY}T09:12:00+09:00"):
    return monitor.parseKst(value)


def test_monitor_flags_candidate_universe_and_flash_safe_block_after_open_cutoff(tmp_path: Path):
    _write_compiled_watch(tmp_path, count=0)
    _write_kis_market(tmp_path, count=0)
    _write_flash(
        tmp_path,
        {
            "document_kind": "NO_TRADE",
            "validation_status": "safe_block",
            "provider_status": "safe_block",
            "no_trade_reason": "missing_compiled_watch_candidate_universe",
            "candidate_universe_source": "none",
            "candidate_universe_count": 0,
        },
    )
    _write_runner(tmp_path)

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at())

    assert result["status"] == "p0"
    assert "candidate_universe_empty_after_open_cutoff" in result["p0_conditions"]
    assert "flash_safe_block_missing_candidate_universe_after_open_cutoff" in result["p0_conditions"]
    assert result["broker_calls_enabled"] is False
    assert result["orders_enabled"] is False


def test_monitor_flags_safe_block_morning_marked_accepted(tmp_path: Path):
    _write_compiled_watch(tmp_path, count=1)
    _write_kis_market(tmp_path, count=1)
    _write_morning_watchlist(
        tmp_path,
        {
            "artifact_id": None,
            "safe_block_id": "art_morning_watchlist_20260610_071505_safe_block",
            "validation_status": "safe_block",
            "validation_errors": ["missing_morning_watchlist_payload"],
            "items": [],
        },
    )
    _write_gpt_morning_health(tmp_path, prompt_status="ok", publish_status="safe_block")
    _write_flash(
        tmp_path,
        {
            "morning_watchlist_ref": "art_morning_watchlist_20260610_071505_safe_block",
            "morning_watchlist_status": "accepted",
            "morning_watchlist_usable": True,
            "candidate_universe_source": "kis_compiled_watch",
            "candidate_universe_count": 1,
        },
    )
    _write_runner(tmp_path)

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at())

    assert result["status"] == "p0"
    assert "morning_watchlist_safe_block_but_flash_marks_accepted" in result["p0_conditions"]
    assert "flash_uses_unusable_morning_watchlist" in result["p0_conditions"]
    assert "gpt_morning_prompt_ok_publish_safe_block" in result["warnings"]


def test_monitor_keeps_after_hours_empty_candidate_as_observation_only(tmp_path: Path):
    _write_compiled_watch(tmp_path, count=0)
    _write_kis_market(tmp_path, count=0)
    _write_flash(tmp_path, {"candidate_universe_count": 0})
    _write_runner(tmp_path)

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at(f"{DAY}T17:00:00+09:00"))

    assert result["status"] == "warn"
    assert result["p0_conditions"] == []
    assert result["checks"]["candidate_universe"]["status"] == "observation_only"


def test_monitor_flags_buy_without_position_size_pct_basis(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "actions": [{"symbol": "005930", "action": "BUY_NOW", "planned_order_cash_krw": 100000}],
            "paper_intent_pipeline": {
                "accepted_count": 1,
                "accepted_intents": [
                    {
                        "symbol": "005930",
                        "side": "buy",
                        "planned_order_cash_krw": 100000,
                        "planned_order_cash_source": "absolute_cash",
                    }
                ],
            },
        },
    )
    _write_runner(tmp_path)

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at())

    assert result["status"] == "p0"
    assert "buy_order_missing_position_size_pct_basis" in result["p0_conditions"]
    assert result["checks"]["buy_sizing"]["bad_sizing_count"] == 2


def test_monitor_flags_exit_trigger_without_sell_now_or_intent(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "document_kind": "POSITION_MANAGEMENT",
            "position_actions": [
                {
                    "symbol": "005930",
                    "action": "WAIT_SELL",
                    "order_window_open": True,
                    "time_exit_reason": "hard_max_hold_exceeded",
                    "time_exit_status": "hard_max_exceeded",
                    "exit_blocked_reason": "sellable_truth_not_pass",
                    "sellable_truth_accepted": False,
                }
            ],
            "paper_intent_pipeline": {"accepted_count": 0, "accepted_intents": []},
        },
    )
    _write_runner(tmp_path)

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at())

    assert result["status"] == "p0"
    assert "exit_trigger_without_sell_now" in result["p0_conditions"]


def test_monitor_flags_sell_now_without_accepted_sell_intent(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "document_kind": "POSITION_MANAGEMENT",
            "position_actions": [
                {
                    "symbol": "005930",
                    "action": "SELL_NOW",
                    "order_window_open": True,
                    "time_exit_reason": "target_price_hit",
                    "time_exit_status": "active",
                    "sellable_truth_accepted": True,
                }
            ],
            "paper_intent_pipeline": {"accepted_count": 0, "accepted_intents": []},
        },
    )
    _write_runner(tmp_path)

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at())

    assert result["status"] == "p0"
    assert "sell_now_without_accepted_sell_intent" in result["p0_conditions"]


def test_monitor_flags_sell_intent_zero_ttl_and_expired_before_runner_pickup(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "document_kind": "POSITION_MANAGEMENT",
            "produced_at_kst": f"{DAY}T09:10:00+09:00",
            "position_actions": [
                {
                    "symbol": "005930",
                    "action": "SELL_NOW",
                    "order_window_open": True,
                    "time_exit_reason": "target_price_hit",
                    "time_exit_status": "active",
                    "sellable_truth_accepted": True,
                }
            ],
            "paper_intent_pipeline": {
                "accepted_count": 1,
                "accepted_intents": [
                    {
                        "symbol": "005930",
                        "side": "sell",
                        "action": "SELL_NOW",
                        "created_at_kst": f"{DAY}T09:10:00+09:00",
                        "valid_until_kst": f"{DAY}T09:10:00+09:00",
                    }
                ],
            },
        },
    )
    _write_runner(tmp_path, {"timestamp_kst": f"{DAY}T09:15:00+09:00"})

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at(f"{DAY}T09:15:00+09:00"))

    assert result["status"] == "p0"
    assert "sell_intent_zero_ttl" in result["p0_conditions"]
    assert "sell_intent_ttl_shorter_than_runner_pickup_window" in result["p0_conditions"]
    assert "sell_intent_expired_before_runner_pickup" in result["p0_conditions"]


def test_monitor_flags_runner_did_not_pick_nonexpired_sell_intent(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "document_kind": "POSITION_MANAGEMENT",
            "produced_at_kst": f"{DAY}T09:10:00+09:00",
            "position_actions": [
                {
                    "symbol": "005930",
                    "action": "SELL_NOW",
                    "order_window_open": True,
                    "time_exit_reason": "target_price_hit",
                    "time_exit_status": "active",
                    "sellable_truth_accepted": True,
                }
            ],
            "paper_intent_pipeline": {
                "accepted_count": 1,
                "accepted_intents": [
                    {
                        "symbol": "005930",
                        "side": "sell",
                        "action": "SELL_NOW",
                        "created_at_kst": f"{DAY}T09:10:00+09:00",
                        "valid_until_kst": f"{DAY}T09:22:00+09:00",
                    }
                ],
            },
        },
    )
    _write_runner(tmp_path, {"timestamp_kst": f"{DAY}T09:15:00+09:00", "intent_loaded": False})

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at(f"{DAY}T09:15:00+09:00"))

    assert result["status"] == "p0"
    assert "runner_did_not_pick_nonexpired_sell_intent" in result["p0_conditions"]


def test_monitor_does_not_flag_runner_pick_when_sell_cash_order_was_attempted(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "document_kind": "POSITION_MANAGEMENT",
            "produced_at_kst": f"{DAY}T09:10:00+09:00",
            "position_actions": [
                {
                    "symbol": "005930",
                    "action": "SELL_NOW",
                    "order_window_open": True,
                    "time_exit_reason": "target_price_hit",
                    "time_exit_status": "active",
                    "sellable_truth_accepted": True,
                }
            ],
            "paper_intent_pipeline": {
                "accepted_count": 1,
                "accepted_intents": [
                    {
                        "symbol": "005930",
                        "side": "sell",
                        "action": "SELL_NOW",
                        "created_at_kst": f"{DAY}T09:10:00+09:00",
                        "valid_until_kst": f"{DAY}T09:22:00+09:00",
                    }
                ],
            },
        },
    )
    _write_runner(
        tmp_path,
        {
            "timestamp_kst": f"{DAY}T09:15:00+09:00",
            "intent_loaded": True,
            "steps": [
                {
                    "step": "intent_claim",
                    "status": "pass",
                    "idempotency_key": "art_flash:bucket:005930:SELL_NOW",
                },
                {"step": "cash_order", "status": "warn", "side": "sell", "broker_endpoint_called": True},
            ],
        },
    )

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at(f"{DAY}T09:15:00+09:00"))

    assert "runner_did_not_pick_nonexpired_sell_intent" not in result["p0_conditions"]
    assert result["checks"]["sell_pipeline"]["runner_touched_sell_intent"] is True


def test_monitor_flags_runner_sellable_truth_block_and_consumed_sibling(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "document_kind": "POSITION_MANAGEMENT",
            "position_actions": [
                {
                    "symbol": "005930",
                    "action": "SELL_NOW",
                    "order_window_open": True,
                    "time_exit_reason": "stop_loss_hit",
                    "time_exit_status": "active",
                    "sellable_truth_accepted": True,
                }
            ],
            "paper_intent_pipeline": {
                "accepted_count": 1,
                "accepted_intents": [{"symbol": "005930", "side": "sell", "action": "SELL_NOW"}],
            },
        },
    )
    _write_runner(
        tmp_path,
        {
            "intent_loaded": True,
            "loaded_intent": {"symbol": "005930", "side": "sell"},
            "executionPreflight": {
                "ok": False,
                "errors": ["sellable_truth_not_accepted", "trade_document_already_consumed"],
            },
            "steps": [{"step": "cash_order", "status": "blocked_risk_overlay", "broker_endpoint_called": False}],
        },
    )

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at())

    assert result["status"] == "p0"
    assert "sell_intent_blocked_by_sellable_truth" in result["p0_conditions"]
    assert "sell_intent_did_not_reach_cash_order_broker_endpoint" in result["p0_conditions"]
    assert "sibling_intent_blocked_by_trade_document_already_consumed" in result["p0_conditions"]


def test_monitor_flags_quarantinable_head_blocking_nonexpired_sell_intents(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "document_kind": "POSITION_MANAGEMENT",
            "produced_at_kst": f"{DAY}T09:10:00+09:00",
            "position_actions": [
                {"symbol": "040350", "action": "SELL_NOW", "order_window_open": True, "time_exit_reason": "stop_loss_hit"},
                {"symbol": "126640", "action": "SELL_NOW", "order_window_open": True, "time_exit_reason": "target_price_hit"},
            ],
            "paper_intent_pipeline": {
                "accepted_count": 2,
                "accepted_intents": [
                    {
                        "symbol": "040350",
                        "side": "sell",
                        "action": "SELL_NOW",
                        "created_at_kst": f"{DAY}T09:10:00+09:00",
                        "valid_until_kst": f"{DAY}T09:22:00+09:00",
                    },
                    {
                        "symbol": "126640",
                        "side": "sell",
                        "action": "SELL_NOW",
                        "created_at_kst": f"{DAY}T09:10:00+09:00",
                        "valid_until_kst": f"{DAY}T09:22:00+09:00",
                    },
                ],
            },
        },
    )
    _write_runner(
        tmp_path,
        {
            "timestamp_kst": f"{DAY}T09:15:00+09:00",
            "intent_loaded": True,
            "loaded_intent": {"symbol": "040350", "side": "sell"},
            "executionPreflight": {"ok": False, "errors": ["sellable_truth_not_accepted"]},
            "intent_dispositions": [
                {
                    "intent_disposition": "quarantined_terminal",
                    "symbol": "040350",
                    "side": "sell",
                    "queue_continued": False,
                }
            ],
            "steps": [{"step": "cash_order", "status": "blocked_risk_overlay", "broker_endpoint_called": False}],
        },
    )

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at(f"{DAY}T09:15:00+09:00"))

    assert result["status"] == "p0"
    assert "nonexpired_sell_intents_behind_quarantinable_head" in result["p0_conditions"]
    assert "sell_intent_starvation_detected" in result["p0_conditions"]


def test_monitor_passes_after_terminal_head_quarantined_and_next_sell_processed(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "document_kind": "POSITION_MANAGEMENT",
            "produced_at_kst": f"{DAY}T09:10:00+09:00",
            "position_actions": [
                {"symbol": "040350", "action": "SELL_NOW", "order_window_open": True, "time_exit_reason": "stop_loss_hit"},
                {"symbol": "126640", "action": "SELL_NOW", "order_window_open": True, "time_exit_reason": "target_price_hit"},
            ],
            "paper_intent_pipeline": {
                "accepted_count": 2,
                "accepted_intents": [
                    {
                        "symbol": "040350",
                        "side": "sell",
                        "action": "SELL_NOW",
                        "created_at_kst": f"{DAY}T09:10:00+09:00",
                        "valid_until_kst": f"{DAY}T09:22:00+09:00",
                    },
                    {
                        "symbol": "126640",
                        "side": "sell",
                        "action": "SELL_NOW",
                        "created_at_kst": f"{DAY}T09:10:00+09:00",
                        "valid_until_kst": f"{DAY}T09:22:00+09:00",
                    },
                ],
            },
        },
    )
    _write_runner(
        tmp_path,
        {
            "timestamp_kst": f"{DAY}T09:15:00+09:00",
            "intent_loaded": True,
            "loaded_intent": {"symbol": "040350", "side": "sell"},
            "executionPreflight": {"ok": True, "errors": []},
            "intent_dispositions": [
                {
                    "intent_disposition": "quarantined_terminal",
                    "symbol": "040350",
                    "side": "sell",
                    "queue_continued": True,
                },
                {
                    "intent_disposition": "submitted",
                    "symbol": "126640",
                    "side": "sell",
                    "queue_continued": False,
                    "broker_endpoint_called": True,
                },
            ],
            "steps": [
                {"step": "intent_disposition", "intent_disposition": "quarantined_terminal", "symbol": "040350", "side": "sell", "queue_continued": True},
                {"step": "cash_order", "status": "pass", "side": "sell", "broker_endpoint_called": True},
            ],
        },
    )

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at(f"{DAY}T09:15:00+09:00"))

    assert result["status"] == "pass"
    assert result["p0_conditions"] == []


def test_monitor_passes_healthy_next_session_flow_and_writes_evidence(tmp_path: Path):
    _write_compiled_watch(tmp_path)
    _write_kis_market(tmp_path)
    _write_flash(
        tmp_path,
        {
            "actions": [
                {
                    "symbol": "005930",
                    "action": "BUY_NOW",
                    "position_size_pct": 10,
                    "sizing_basis": "position_size_pct",
                }
            ],
            "position_actions": [
                {
                    "symbol": "000660",
                    "action": "SELL_NOW",
                    "order_window_open": True,
                    "time_exit_reason": "target_price_hit",
                    "time_exit_status": "active",
                    "sellable_truth_accepted": True,
                }
            ],
            "paper_intent_pipeline": {
                "accepted_count": 2,
                "accepted_intents": [
                    {
                        "symbol": "005930",
                        "side": "buy",
                        "position_size_pct": 10,
                        "sizing_basis": "position_size_pct_of_effective_total_deposit",
                        "planned_order_cash_source": "position_size_pct",
                    },
                    {"symbol": "000660", "side": "sell", "action": "SELL_NOW"},
                ],
            },
        },
    )
    _write_runner(
        tmp_path,
        {
            "intent_loaded": True,
            "loaded_intent": {"symbol": "000660", "side": "sell"},
            "executionPreflight": {"ok": True, "errors": []},
            "steps": [{"step": "cash_order", "status": "pass", "broker_endpoint_called": True}],
        },
    )

    result = monitor.evaluatePaperOperationQuality(data_root=tmp_path, at=_at())
    paths = monitor.writePaperOperationQualityEvidence(result, data_root=tmp_path, at=_at())

    assert result["status"] == "pass"
    assert result["p0_conditions"] == []
    assert Path(paths["latest_path"]).is_file()
    assert Path(paths["stamped_path"]).is_file()
