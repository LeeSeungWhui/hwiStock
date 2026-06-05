"""create hwistock runtime auth tables

Revision ID: 20260605_0002
Revises: 20260604_0001
Create Date: 2026-06-05
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260605_0002"
down_revision: Union[str, None] = "20260604_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA_NAME = "hwistock_core"


def upgrade() -> None:
    op.create_table(
        "t_user",
        sa.Column("user_no", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Text(), nullable=False, unique=True),
        sa.Column("user_pw", sa.Text(), nullable=False),
        sa.Column("user_nm", sa.Text(), nullable=True),
        sa.Column("user_eml", sa.Text(), nullable=True),
        sa.Column("role_cd", sa.Text(), nullable=True),
        schema=SCHEMA_NAME,
    )
    op.create_index(
        "ix_hwistock_t_user_user_id",
        "t_user",
        ["user_id"],
        unique=True,
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "t_user_log",
        sa.Column("log_id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("req_id", sa.Text(), nullable=True),
        sa.Column("req_mthd", sa.Text(), nullable=False),
        sa.Column("req_path", sa.Text(), nullable=False),
        sa.Column("res_cd", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("sql_cnt", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("client_ip", sa.Text(), nullable=True),
        sa.Column("ip_loc_txt", sa.Text(), nullable=True),
        sa.Column("ip_loc_src", sa.Text(), nullable=True),
        sa.Column("reg_dt", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        schema=SCHEMA_NAME,
    )
    op.create_index(
        "ix_hwistock_t_user_log_user_reg_dt",
        "t_user_log",
        ["user_id", "reg_dt"],
        unique=False,
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "t_token",
        sa.Column("state_tp", sa.String(length=32), nullable=False),
        sa.Column("token_jti", sa.String(length=191), nullable=False),
        sa.Column("expires_at_ms", sa.BigInteger(), nullable=False),
        sa.Column("token_payload_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("state_tp", "token_jti"),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "t_request_idempotency",
        sa.Column("scope_tp", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("status_cd", sa.Text(), nullable=False),
        sa.Column("payload_digest", sa.Text(), nullable=False),
        sa.Column("response_json", sa.Text(), nullable=True),
        sa.Column("expires_at_ms", sa.BigInteger(), nullable=False),
        sa.Column("reg_dt", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("upd_dt", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("scope_tp", "idempotency_key"),
        schema=SCHEMA_NAME,
    )

    op.create_table(
        "t_data",
        sa.Column("data_no", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("data_nm", sa.Text(), nullable=False),
        sa.Column("data_desc", sa.Text(), nullable=True),
        sa.Column("stat_cd", sa.Text(), nullable=False),
        sa.Column("amt", sa.Numeric(18, 2), nullable=True),
        sa.Column("tag_json", sa.Text(), nullable=True),
        sa.Column("reg_dt", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        schema=SCHEMA_NAME,
    )
    op.create_index(
        "ix_hwistock_t_data_user_reg_dt",
        "t_data",
        ["user_id", "reg_dt"],
        unique=False,
        schema=SCHEMA_NAME,
    )


def downgrade() -> None:
    op.drop_index("ix_hwistock_t_data_user_reg_dt", table_name="t_data", schema=SCHEMA_NAME)
    op.drop_table("t_data", schema=SCHEMA_NAME)
    op.drop_table("t_request_idempotency", schema=SCHEMA_NAME)
    op.drop_table("t_token", schema=SCHEMA_NAME)
    op.drop_index("ix_hwistock_t_user_log_user_reg_dt", table_name="t_user_log", schema=SCHEMA_NAME)
    op.drop_table("t_user_log", schema=SCHEMA_NAME)
    op.drop_index("ix_hwistock_t_user_user_id", table_name="t_user", schema=SCHEMA_NAME)
    op.drop_table("t_user", schema=SCHEMA_NAME)
