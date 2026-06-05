"""
hwiStock operator user seeding.

Reads:
- HWISTOCK_OPERATOR_USERNAME or NEXT_PUBLIC_HWISTOCK_OPERATOR_USERNAME
- HWISTOCK_OPERATOR_PASSWORD

No secret values are printed.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from lib.Config import getConfig  # noqa: E402
from service.AuthService import hashPasswordPbkdf2  # noqa: E402


DEFAULT_OPERATOR_USERNAME = "operator@hwistock.local"


def require_operator_password() -> str:
    password = str(os.getenv("HWISTOCK_OPERATOR_PASSWORD") or "")
    if len(password) < 8:
        raise RuntimeError("HWISTOCK_OPERATOR_PASSWORD must be set to an 8+ character password.")
    return password


def resolve_operator_username() -> str:
    username = str(
        os.getenv("HWISTOCK_OPERATOR_USERNAME")
        or os.getenv("NEXT_PUBLIC_HWISTOCK_OPERATOR_USERNAME")
        or DEFAULT_OPERATOR_USERNAME
    ).strip().lower()
    if "@" not in username or len(username) < 3:
        raise RuntimeError("HWISTOCK_OPERATOR_USERNAME must be an email-like identifier.")
    return username


async def seed_operator_user() -> None:
    import asyncpg

    config = getConfig()
    db_conf = config["DATABASE"]
    schema = str(os.getenv("HWISTOCK_POSTGRES_SCHEMA") or "hwistock_core").strip()
    username = resolve_operator_username()
    password_hash = hashPasswordPbkdf2(require_operator_password())

    conn = await asyncpg.connect(
        host=os.getenv("HWISTOCK_POSTGRES_HOST") or db_conf.get("host", "localhost"),
        port=int(os.getenv("HWISTOCK_POSTGRES_PORT") or db_conf.get("port", "5432")),
        user=os.getenv("HWISTOCK_POSTGRES_USER") or db_conf.get("user"),
        password=os.getenv("HWISTOCK_POSTGRES_PASSWORD") or db_conf.get("password"),
        database=os.getenv("HWISTOCK_POSTGRES_DB") or "hwistock",
        server_settings={"search_path": f"{schema},public"},
    )
    try:
        await conn.execute(
            """
            INSERT INTO t_user (user_id, user_pw, user_nm, user_eml, role_cd)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO UPDATE
                SET user_pw = EXCLUDED.user_pw,
                    user_nm = EXCLUDED.user_nm,
                    user_eml = EXCLUDED.user_eml,
                    role_cd = EXCLUDED.role_cd
            """,
            username,
            password_hash,
            "hwiStock Operator",
            username,
            "operator",
        )
    finally:
        await conn.close()


def main() -> None:
    asyncio.run(seed_operator_user())
    print("operator_user_seeded")


if __name__ == "__main__":
    main()
