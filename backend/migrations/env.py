"""
파일명: backend/migrations/env.py
작성자: hwi (via Codex)
갱신일: 2026-06-04
설명: Alembic env skeleton for hwiStock.
       Uses HWISTOCK_DATABASE_URL, schema hwistock_core,
       and explicitly sets search_path to hwistock_core, public.
       No MyWebTemplate database/schema/migration overlap.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# -- Alembic Config object ------------------------------------------------
config = context.config

# -- Logger ---------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -- Database URL ---------------------------------------------------------
DATABASE_URL = os.environ.get("HWISTOCK_DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "HWISTOCK_DATABASE_URL is not set. "
        "Source env.sh or export HWISTOCK_DATABASE_URL before running migrations."
    )

config.set_main_option("sqlalchemy.url", DATABASE_URL)

# -- Metadata -------------------------------------------------------------
# Placeholder: add ORM MetaData objects here when declarative models exist.
target_metadata = None

# -- Schema isolation -----------------------------------------------------
HWISTOCK_SCHEMA = os.environ.get("HWISTOCK_POSTGRES_SCHEMA", "hwistock_core")


def include_name(name: str, type_: str, parent_names: dict) -> bool:
    """Restrict autogenerate to hwistock_core schema."""
    if type_ == "schema":
        return name in (HWISTOCK_SCHEMA,)
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=HWISTOCK_SCHEMA,
        include_schemas=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the database)."""
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        if connection.dialect.name.startswith("postgresql"):
            safe_schema = HWISTOCK_SCHEMA.replace('"', '""')
            connection.exec_driver_sql(
                f'SET search_path TO "{safe_schema}", public'
            )

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=HWISTOCK_SCHEMA,
            include_schemas=True,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
