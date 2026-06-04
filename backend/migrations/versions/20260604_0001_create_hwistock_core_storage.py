"""create hwistock core storage

Revision ID: 20260604_0001
Revises:
Create Date: 2026-06-04
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA_NAME = "hwistock_core"


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA_NAME}"'))

    op.create_table(
        "artifacts",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("artifact_path", sa.Text(), nullable=False),
        sa.Column("artifact_hash", sa.String(length=64), nullable=True),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("created_at_kst", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redaction_status", sa.String(length=32), nullable=False),
        sa.Column("source_ids_json", sa.JSON(), nullable=False),
        sa.Column("related_artifact_ids_json", sa.JSON(), nullable=False),
        sa.Column("symbols_json", sa.JSON(), nullable=False),
        schema=SCHEMA_NAME,
    )
    op.create_index(
        "ix_hwistock_artifacts_trading_date_type",
        "artifacts",
        ["trading_date", "artifact_type"],
        unique=False,
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "sources",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("collected_at_kst", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at_kst", sa.DateTime(timezone=True), nullable=True),
        sa.Column("body_storage_policy", sa.String(length=32), nullable=False),
        sa.Column("license_or_terms_note", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "normalized_events",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("event_kind", sa.String(length=64), nullable=False),
        sa.Column("event_summary", sa.Text(), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "ai_outputs",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("model_provider", sa.String(length=64), nullable=False),
        sa.Column("prompt_id", sa.String(length=128), nullable=True),
        sa.Column("analysis_kind", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("input_source_ids_json", sa.JSON(), nullable=False),
        sa.Column("output_candidate_ids_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "candidate_cards",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_artifact_ids_json", sa.JSON(), nullable=False),
        sa.Column("ai_output_ids_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )
    op.create_index(
        "ix_hwistock_candidate_cards_symbol",
        "candidate_cards",
        ["symbol"],
        unique=False,
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "order_events",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("order_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("broker_adapter", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("order_side", sa.String(length=16), nullable=False),
        sa.Column("order_type", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("cash_amount_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("fees_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("taxes_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("order_state", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "fill_events",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("fill_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("order_id", sa.String(length=128), nullable=False),
        sa.Column("broker_adapter", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("fill_side", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("cash_amount_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("fees_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("taxes_krw", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "position_snapshots",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("position_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("broker_adapter", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("avg_price_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("current_price_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("market_value_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("unrealized_pnl_krw", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "daily_pnl",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("calculation_source", sa.String(length=16), nullable=False),
        sa.Column("gross_profit_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("gross_loss_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("gross_pnl_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("fees_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("taxes_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("net_pnl_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("cash_start_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("cash_end_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("open_position_value_krw", sa.Numeric(18, 2), nullable=False),
        sa.Column("realized_trade_ids_json", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "calculation_source = 'system'",
            name="ck_hwistock_daily_pnl_calculation_source_system",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "reports",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("report_kind", sa.String(length=32), nullable=False),
        sa.Column("report_time_kst", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pnl_artifact_id", sa.String(length=128), nullable=True),
        sa.Column("morning_report_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "evidence_links",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("paper_day_date", sa.Date(), nullable=False),
        sa.Column("source_artifact_ids_json", sa.JSON(), nullable=False),
        sa.Column("normalized_event_ids_json", sa.JSON(), nullable=False),
        sa.Column("ai_analysis_ids_json", sa.JSON(), nullable=False),
        sa.Column("candidate_card_ids_json", sa.JSON(), nullable=False),
        sa.Column("order_event_ids_json", sa.JSON(), nullable=False),
        sa.Column("fill_event_ids_json", sa.JSON(), nullable=False),
        sa.Column("position_snapshot_ids_json", sa.JSON(), nullable=False),
        sa.Column("pnl_artifact_id", sa.String(length=128), nullable=False),
        sa.Column("morning_report_id", sa.String(length=128), nullable=False),
        sa.Column("daily_close_report_id", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            [f"{SCHEMA_NAME}.artifacts.artifact_id"],
            ondelete="CASCADE",
        ),
        schema=SCHEMA_NAME,
    )


def downgrade() -> None:
    op.drop_table("evidence_links", schema=SCHEMA_NAME)
    op.drop_table("reports", schema=SCHEMA_NAME)
    op.drop_table("daily_pnl", schema=SCHEMA_NAME)
    op.drop_table("position_snapshots", schema=SCHEMA_NAME)
    op.drop_table("fill_events", schema=SCHEMA_NAME)
    op.drop_table("order_events", schema=SCHEMA_NAME)
    op.drop_index(
        "ix_hwistock_candidate_cards_symbol",
        table_name="candidate_cards",
        schema=SCHEMA_NAME,
    )
    op.drop_table("candidate_cards", schema=SCHEMA_NAME)
    op.drop_table("ai_outputs", schema=SCHEMA_NAME)
    op.drop_table("normalized_events", schema=SCHEMA_NAME)
    op.drop_table("sources", schema=SCHEMA_NAME)
    op.drop_index(
        "ix_hwistock_artifacts_trading_date_type",
        table_name="artifacts",
        schema=SCHEMA_NAME,
    )
    op.drop_table("artifacts", schema=SCHEMA_NAME)
