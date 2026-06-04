---
schema_version: hwi.ready-set-rule-preset-applicability/v0
stage: ready-set
status: ready_for_foundation_only_go
implementation_ready: true
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-03
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
row_closure_matrix_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
selected_queue_scope: foundation_only
---

# Ready-Set Rule Preset Applicability Matrix

## 1. Purpose

This matrix records which active HWI rule presets apply to each hwiStock unit
before Go. It does not run the rule gate by itself. The narrowed
foundation-only queue is implementation-ready only after selected-row Go
preflight.

## 2. Active Presets

From `docs/profiles/PROFILE-HWISTOCK.md`:

- `fastapi-backend-rule-preset`: applies to `backend/`, including FastAPI API,
  runner services, adapters, AI orchestration, storage services, and tests.
- `next-frontend-rule-preset`: applies to `frontend-web/`, limited to the
  read-only dashboard/operator console.
- `db-naming-rule-preset`: applies to PostgreSQL schemas, migrations, queries,
  table/view/column names, and database evidence.

Manual checklist review always applies to safety, credentials, broker boundary,
AI/order separation, market session handling, cash-only policy, and evidence.

## 3. Applicability Matrix

| unit_id | work_class | primary path/surface | fastapi-backend-rule-preset | next-frontend-rule-preset | db-naming-rule-preset | manual safety checklist |
| --- | --- | --- | --- | --- | --- | --- |
| HWISTOCK-UNIT-001 | docs_only | `AGENTS.md`, `docs/**` | not_applicable | not_applicable | not_applicable | required |
| HWISTOCK-UNIT-002 | quality_only | `backend/`, `ops/systemd/` | required if backend health/status or runner service code changes | not_applicable | conditional if service writes PostgreSQL state/evidence | required |
| HWISTOCK-UNIT-003 | product_api | `backend/` ingestion/services | required | not_applicable | conditional if normalized event persistence or migrations change | required |
| HWISTOCK-UNIT-004 | product_api | `backend/` strategy/risk config and policy gates | required | not_applicable | conditional if risk/config storage or migrations change | required |
| HWISTOCK-UNIT-005 | product_api | `backend/` AI orchestration services | required | not_applicable | conditional if AI job/report persistence or migrations change | required |
| HWISTOCK-UNIT-006 | product_api | `backend/` engine/order-state/adapters | required | not_applicable | required if order-state, intent, fill, reconciliation, or migration storage changes | required |
| HWISTOCK-UNIT-007 | product_ui | `frontend-web/` dashboard | conditional only if backend read API code also changes | required | not_applicable unless the unit explicitly adds dashboard query migrations | required |
| HWISTOCK-UNIT-008 | product_api | `backend/`, `backend/migrations/`, PostgreSQL | required if storage service/API code changes | not_applicable | required | required |
| HWISTOCK-UNIT-009 | docs_only | `docs/sources/`, `apiRefer/*.xlsx` docs analysis only | not_applicable for current docs-only row | not_applicable | not_applicable | required |

## 4. Go Preflight Rule

Before a selected row can enter Go:

1. Read the selected unit, profile, QA scenario, and this matrix.
2. Identify the actual changed paths.
3. Apply every preset whose path/surface is `required` or whose `conditional`
   condition is triggered by the planned change.
4. Run `hwi-rule-gate` after code exists, or record `not_run` plus manual
   checklist evidence if the gate is unavailable.
5. Treat warnings as blocking unless the unit/profile records an explicit
   accepted exception.

## 5. Path Boundary Notes

- `frontend-web/` is dashboard-only. It must not call broker or AI provider APIs
  directly.
- `backend/` owns FastAPI, trading services, schedulers, adapters, AI
  orchestration, storage services, and health/status APIs.
- `backend/migrations/` owns Alembic migrations and must follow the DB naming
  preset.
- `apiRefer/*.xlsx` remains a local KIS reference source and is not part of the
  external review share bundle unless separately approved.
- No product source folder exists yet. This matrix prepares Go routing only.

## 6. Current Status

The rule preset mapping is prepared for the narrowed foundation-only queue.
Strategy, AI, runner, and dashboard rows remain excluded from the first Go
queue.
