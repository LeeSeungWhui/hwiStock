---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-001-project-bootstrap-set
type: evidence
name: UNIT-001 project bootstrap Set pass
stage: set
environment: docs_only
status: set
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
unit_id: HWISTOCK-UNIT-001
unit_set_ready: true
go_allowed: false
---

# UNIT-001 Project Bootstrap Set Pass

## 1. Scope

This Set pass closes the docs-only bootstrap contract for hwiStock. It verifies
that the project has an active HWI profile, a safety-core module, a bootstrap
unit, and a bootstrap QA scenario, without implying product implementation or
live-trading readiness.

## 2. Closed Bootstrap Decisions

- Project root: `/data/workspace/My/hwiStock`.
- Profile: `docs/profiles/PROFILE-HWISTOCK.md`.
- Harness route: `hwi-work-harness`.
- Stack direction: Python/FastAPI backend, TypeScript/Next.js dashboard, and
  PostgreSQL storage.
- Broker direction: KIS; KB is blocked for personal-use automation unless later
  official evidence changes that.
- Broker boundary: no internal fake broker execution; pre-approval execution is
  no-order dry-run only.
- Capital policy: cash-only, live starting capital 2,000,000 KRW.
- Paper/mock budget: KIS paper/mock target budget 10,000,000 KRW until account
  evidence proves actual balance.
- Live readiness: at least one full week of paper/sandbox evidence plus explicit
  user go/no-go approval.

## 3. Updated Documents

- `docs/modules/HWISTOCK-MOD-001_trading-safety-core.md`
- `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md`
- `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md`
- `docs/evidence/RUN-20260602_project-bootstrap.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/index.md`

## 4. QA Contract

`QA-HWISTOCK-UNIT-001` verifies:

- root harness/profile wiring
- default live-order prohibition
- safety module presence
- one-week paper/sandbox gate
- cash-only capital policy
- visible closed decisions and remaining Ready-Set blockers

## 5. Verdict

UNIT-001 Set status: PASS

Implementation readiness for whole bundle: BLOCKED

Blocking condition: the Ready-Set completion gate still has
`implementation_ready: false`; this docs-only bootstrap does not authorize Go.
