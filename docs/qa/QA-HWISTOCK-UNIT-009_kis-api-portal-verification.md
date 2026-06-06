---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-009
type: qa_scenario
name: KIS API portal verification QA
unit_refs:
  - HWISTOCK-UNIT-009
module_refs:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-005
profile_refs:
  - PROFILE-HWISTOCK
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
owner: hwi
updated_at: 2026-06-04
evidence_refs:
  - docs/evidence/RUN-20260602_unit-009-kis-api-portal-verification-set.md
  - docs/evidence/RUN-20260604_unit-009-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md
  - docs/evidence/RUN-20260604_unit-009-go-preflight.md
  - docs/evidence/RUN-20260604_unit-009-go-check.md
---

# KIS API Portal Verification QA

## Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | docs | Review official KIS API service summary | Domestic stock order, account, realtime, and quote endpoints are listed | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md` |
| QA-002 | P0 | docs | Review official broker-adapter docs, samples, and local `apiRefer` files | Broker adapter availability, endpoint separation, mode-gated KRX/NXT/SOR handling, provider-query-required helper APIs, exact balance, and numeric-limit follow-ups are documented | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`; `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md` |
| QA-003 | P0 | docs | Review KRX/NXT/SOR-related API behavior | KRX/NXT/SOR fields are documented; paper/mock mode rejects NXT broker branches, real investment mode enables NXT where capability flags allow it, and SOR operation behavior remains disabled/fallback | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`; `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md` |
| QA-004 | P0 | safety | Inspect commands/evidence | No credential use, login, token request, broker API call, or order placement occurred | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md` |

## PASS / FAIL / BLOCKED Rules

- PASS: official docs answer endpoint, broker-adapter availability, KRX/NXT/SOR
  field/route design, eligibility, and operation/adapter separation questions without
  network calls.
- FAIL: verification uses credentials or operation/adapter API calls.
- PARTIAL: public docs confirm the endpoint family but leave actual account-mode
  behavior, adapter balance, exact current rate-limit numbers, disabled SOR
  behavior, or provider helper edge cases to local fallback or a future approved
  smoke.
- BLOCKED: official docs are inaccessible or do not expose the endpoint family
  needed to design the next unit.

## Current Verdict

- QA-001: PASS
- QA-002: PASS with partial boundary (adapter KRX paths cross-referenced to sanitized
  `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`; budget numeric and some
  helper APIs still deferred)
- QA-003: PASS with partial boundary (NXT/SOR remain `live_verify`; adapter KRX limits
  preserved)
- QA-004: PASS

Overall: **Go-Check PASS** for the current-authority rebaseline docs-only capability
verification per `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`.
No new KIS/broker/network calls are authorized by this closure. Future
broker-network adapter work still requires an explicitly scoped approved unit.
Use `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` as the adapter-mode
capability and fallback contract.

After the MyWebTemplate backend/frontend-web import and the 2026-06-04
Ready-Set reissue, this remains docs-only capability evidence and supporting
context for the current-authority `go_check_passed` rebaseline row. That
closure authorizes only local docs/capability-matrix refinement. Any new KIS token/account/quote,
realtime, order, modify/cancel, WebSocket, broker-network, or credential action
still requires an explicitly scoped approval and matching Go preflight.
