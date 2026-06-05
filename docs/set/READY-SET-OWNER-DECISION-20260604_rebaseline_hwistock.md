---
schema_version: hwi.ready-set-owner-decision/v0
stage: ready-set
status: active
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-04
updated_at: 2026-06-04
current_authority: true
decision_owner: hwi
decision_scope: mywebtemplate_import_rebaseline
supersedes_decision_refs:
  - docs/set/READY-SET-OWNER-DECISION-BRIEF-20260602_hwistock.md
  - docs/set/READY-SET-OWNER-DECISION-RECEIPT-TEMPLATE-20260603_hwistock.md
rebaseline_evidence_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
prior_completion_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
prior_row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
prior_go_preflight_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
---

# Ready-Set Owner Decision — MyWebTemplate Code Import Rebaseline

## 1. Decision Summary

The owner has decided how to treat the imported MyWebTemplate `backend/` and
`frontend-web/` code after the 2026-06-04 baseline replacement.

**Decision**: MyWebTemplate sample, public, template, branding, and generic
auth/public surfaces are **quarantine targets** and must be replaced with
hwiStock-specific dashboard/API behavior during Go-Check implementation.

This is a binding Ready-Set decision, not optional cleanup. The quarantine
scope affects the first-row allowed Go scope for every unit that touches the
imported backend or frontend code.

## 2. Quarantine Targets

The following imported MyWebTemplate surfaces must be removed, quarantined,
disabled, renamed, or replaced before any Go-Check PASS for affected rows:

1. **Backend sample router/service files**: any `backend/router/sample*`,
   `backend/service/sample*`, or equivalent generic demo endpoints.
2. **Frontend sample/public routes**: `frontend-web/app/sample/**`,
   `frontend-web/app/public/**`, or equivalent template demo pages.
3. **Public route configuration entries**: any `publicRoutes` or unauthenticated
   allowlist entries that expose MyWebTemplate landing/auth pages as public
   surfaces.
4. **MyWebTemplate branding in frontend i18n and layout files**: product name,
   logo references, color tokens, or copy that identifies the app as
   MyWebTemplate rather than hwiStock.
5. **Generic auth/public pages**: imported login/register/landing pages that
   carry MyWebTemplate copy, flow, or visual identity.
6. **Backend bind behavior**: any runtime script that binds `0.0.0.0` by
   default must be changed to `127.0.0.1` (local-only) unless a later
   explicit Set approval changes the dashboard/API exposure policy.
7. **Template config assumptions**: `backend/config.ini` and
   `frontend-web/config.ini` are local ignored files and must not be treated
   as hwiStock product config; durable hwiStock secrets/config belong under
   `/home/hwi/.config/hwistock/*.env`.
8. **MyWebTemplate database/schema references**: any imported backend code that
   assumes the MyWebTemplate database name, schema, migrations, tables, or seed
   data must be redirected to hwiStock isolation (`hwistock` database,
   `hwistock_core` schema, `HWISTOCK_DATABASE_URL`).

## 3. Replacement Policy

During Go-Check for each affected unit, implementers must:

- Replace quarantined routes with hwiStock-specific read-only dashboard/API
  behavior as defined in the unit contract.
- Preserve only suitable skeleton/tooling patterns (FastAPI layer layout,
  Next.js app structure, test conventions) that do not carry product-specific
  behavior or branding.
- Ensure no MyWebTemplate sample page, public route, or generic auth flow
  remains reachable in the implemented surface.
- Enforce local-only bind (`127.0.0.1`) for every backend and frontend dev/prod
  runner unless a later explicit approval records a different exposure policy.

## 4. Scope Impact

This decision makes MyWebTemplate quarantine and local-only enforcement a
**first-row requirement**, not a post-implementation cleanup item. The Ready-Set
row closure matrix and Go preflight checklist encode this requirement as part
of the allowed first Go scope for:

- `HWISTOCK-UNIT-001` (bootstrap): skeleton guardrails must include quarantine
  verification.
- `HWISTOCK-UNIT-002` (runner): systemd/local runner must bind `127.0.0.1`.
- `HWISTOCK-UNIT-003` (ingestion): backend ingestion surface must not expose
  sample/demo endpoints.
- `HWISTOCK-UNIT-004` (strategy): backend risk/config surface must not expose
  sample/demo endpoints.
- `HWISTOCK-UNIT-005` (AI): backend AI surface must not expose sample/demo
  endpoints.
- `HWISTOCK-UNIT-006` (engine): backend trading surface must not expose
  sample/demo endpoints.
- `HWISTOCK-UNIT-007` (dashboard): frontend must remove/replace MyWebTemplate
  branding, sample routes, publicRoutes, and generic auth pages.
- `HWISTOCK-UNIT-008` (storage): backend storage surface must not expose
  sample/demo endpoints and must use hwiStock DB isolation.
- `HWISTOCK-UNIT-009` (KIS verification): least impacted, but any generated
  reference code must not include MyWebTemplate assumptions.

## 5. Historical Evidence Preservation

The bounded KIS broker-adapter REST and websocket smoke recorded in
`docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md` is preserved as
historical evidence only. It proves the 2026-06-04 bounded smoke passed, but
it does **not** authorize new KIS/broker network calls, additional adapter
orders, account-affecting orders, credential storage, or unscoped adapter integration.

## 6. References

- Rebaseline evidence: `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`
- Superseded prior docs:
  - `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`
  - `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`
  - `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md`
- Profile: `docs/profiles/PROFILE-HWISTOCK.md`
- Unit contracts: `docs/units/HWISTOCK-UNIT-*.md`
