---
schema_version: hwi.evidence/v0
id: RUN-20260602-stack-rule-preset-set
type: evidence
name: Stack and rule preset Set pass
stage: set
environment: docs_only
status: pass_with_followups
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
implementation_ready: false
---

# Stack And Rule Preset Set Pass

## 1. Scope

This docs-only Set pass closes the project technology stack and HWI rule preset
selection for hwiStock.

## 2. Decisions

- Backend/API/trading runtime stack: Python 3 + FastAPI.
- Backend source root: `backend/`.
- Backend entrypoint: `backend/server.py`.
- Backend layers: `backend/router/`, `backend/service/`, `backend/query/`,
  `backend/lib/`, and `backend/tests/`.
- Backend migrations: Alembic under `backend/migrations/`.
- Dashboard stack: TypeScript + Next.js/React.
- Dashboard source root: `frontend-web/`.
- Dashboard scope: read-only operator console only.
- Durable storage: PostgreSQL database `hwistock`, schema `hwistock_core`,
  env var `HWISTOCK_DATABASE_URL`.
- MyWebTemplate reuse: suitable `backend/` and `frontend-web/` skeleton/tooling
  patterns only. MyWebTemplate docs, product PST content, database names,
  schemas, migrations, tables, seed data, and app-specific behavior are
  excluded.
- Active HWI presets:
  - `fastapi-backend-rule-preset`
  - `next-frontend-rule-preset`
  - `db-naming-rule-preset`

## 3. Evidence

- `docs/profiles/PROFILE-HWISTOCK.md` frontmatter now lists the selected
  frameworks and rule presets.
- `docs/profiles/PROFILE-HWISTOCK.md` records planned backend/frontend paths,
  FastAPI profile values, Next dashboard profile values, and the rule-gate
  adapter.
- `docs/index.md` records the selected stack under open decisions.
- `docs/evidence/RUN-20260602_ready-set-architecture.md` marks stack selection
  closed.
- `docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md` and
  `docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md` now close the
  migration-tool question with Alembic.
- Residual docs that treated stack as unresolved were normalized.

## 4. Boundaries

- No source-code folders were created in this pass.
- No broker API, AI API, database, or network call was made.
- No order placement, broker order, simulated fill, or fake balance was created.
- The stack decision does not make the Ready-Set bundle implementation-ready.

## 5. Follow-Ups

- UNIT-004 still needs exact minimal risk values.
- UNIT-002 still needs process-manager and home-server lifecycle Set closure.
- UNIT-007 still needs dashboard access policy, data surfaces, and design-route
  detail before Go.
- Future implementation must run `hwi-rule-gate` with the selected presets after
  code exists; docs-only work remains manual checklist evidence.

## 6. Verdict

Stack/rule preset Set: PASS WITH FOLLOW-UPS.

Implementation readiness: BLOCKED.
