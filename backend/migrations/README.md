
# hwiStock Alembic Migrations

ENV-DRIVEN: every migration command below requires `HWISTOCK_DATABASE_URL`.

## Database isolation

- Database: `hwistock`
- Schema: `hwistock_core`
- Connection env var: `HWISTOCK_DATABASE_URL`
- Search path: `hwistock_core, public`

No tables are created in `public` and no MyWebTemplate database/schema/migration
names are reused.

## Quick reference

```bash
source ./env.sh

# Generate a new revision
alembic -c backend/alembic.ini revision --autogenerate -m "description"

# Upgrade to head
alembic -c backend/alembic.ini upgrade head

# Seed/update the local dashboard operator user after migrations
HWISTOCK_OPERATOR_PASSWORD='<local secret>' \
  python backend/scripts/seed_operator_user.py

# Downgrade one step
alembic -c backend/alembic.ini downgrade -1
```

## Important

- Do not run migrations against a live production database without explicit
  approval.
- Keep revision files schema-qualified (e.g. `hwistock_core.artifacts`).
