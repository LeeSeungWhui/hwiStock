schema_version: hwi.run-evidence/v0
id: RUN-20260605-runtime-db-dashboard-remediation
created_at_kst: 2026-06-05T19:31:00+09:00
scope:
  - backend runtime DB isolation
  - hwiStock PostgreSQL migration activation
  - operator dashboard runtime artifact mapping
  - password-only dashboard login smoke

# RUN-20260605 runtime DB/dashboard remediation

## Trigger

The running API was observed connecting to the imported MyWebTemplate database
instead of the hwiStock database boundary. The operator dashboard also rendered
thin placeholder-style rows such as artifact present/missing instead of the
actual runtime artifacts already being produced under `data/`.

## Changes

- Runtime DB connection now prefers hwiStock-specific env boundaries:
  - database: `hwistock`
  - schema/search path: `hwistock_core,public`
  - primary source: `HWISTOCK_DATABASE_URL` or `HWISTOCK_POSTGRES_DB`
- The API refuses to silently fall back to `mywebtemplate` when hwiStock DB
  isolation is enabled.
- Alembic runtime was completed with:
  - `backend/alembic.ini`
  - `alembic==1.18.4`
  - `psycopg[binary]==3.3.4`
  - ConfigParser percent escaping for URL-encoded passwords
  - SQLAlchemy 2 implicit transaction fix after `SET search_path`
- New migration `20260605_0002` creates hwiStock runtime auth tables under
  `hwistock_core`:
  - `t_user`
  - `t_user_log`
  - `t_token`
  - `t_request_idempotency`
  - `t_data`
- Operator dashboard snapshot now parses actual artifacts:
  - normalized news/disclosure events
  - compiled watch candidates
  - DeepSeek Pro hourly analysis
  - DeepSeek Flash trade document
  - KIS market endpoint results
  - runner evidence
- The hidden default operator username was changed from the template demo user
  to `operator@hwistock.local`.

## Runtime DB evidence

Observed after migration and seed:

```text
database=hwistock
schema=hwistock_core
alembic_version=20260605_0002
table_count=17
operator_user_exists=True
tables=ai_outputs,alembic_version,artifacts,candidate_cards,daily_pnl,evidence_links,fill_events,normalized_events,order_events,position_snapshots,reports,sources,t_data,t_request_idempotency,t_token,t_user,t_user_log
```

API restart log confirmed the service now connects to `/hwistock`, not
`/mywebtemplate`:

```text
hwistock.db.isolation database=hwistock schema=hwistock_core
Connected to database postgresql://...@127.0.0.1:5432/hwistock
database connected: main_db
```

## Validation

```text
pytest -q backend/tests/test_db_url_encoding.py backend/tests/test_operational_go_check_pipeline.py
15 passed

pnpm --dir frontend-web test -- login.view.test.jsx dashboard.view.test.jsx
Test Files 27 passed
Tests 133 passed

pnpm --dir frontend-web build
Compiled successfully

python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --changed --fail-on-warn --profile docs/profiles/PROFILE-HWISTOCK.md
Status: pass
Findings: error=0 warning=0 info=0
```

Production service smoke after redeploy:

```text
login_page_http=200
bff_login_http=200
bff_me_http=200
dashboard_http=200
snapshot_http=200
snapshot_candidates=5
snapshot_intelligence=8
snapshot_ai=DeepSeek Pro 정각 분석 · RISK_OFF,DeepSeek Flash 10분 매매문서 · 5개
```

## Notes

- Operator password is stored only in the local secret env file under
  `/home/hwi/.config/hwistock/` and was not committed.
- Existing Next.js build warnings remain:
  - deprecated middleware convention
  - Turbopack NFT trace warning from config import path
