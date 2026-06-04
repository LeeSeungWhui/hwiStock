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
owner: hwi
updated_at: 2026-06-02
evidence_refs:
  - docs/evidence/RUN-20260602_unit-009-kis-api-portal-verification-set.md
---

# KIS API Portal Verification QA

## Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | docs | Review official KIS API service summary | Domestic stock order, account, realtime, and quote endpoints are listed | `RUN-20260602_unit-009-kis-api-portal-verification-set.md` |
| QA-002 | P0 | docs | Review official paper/mock-investment docs, samples, and local `apiRefer` files | Paper/mock availability, endpoint separation, KRX-supported paths, paper-unsupported APIs, fallback needs, exact balance, and numeric-limit follow-ups are documented | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` |
| QA-003 | P0 | docs | Review KRX/NXT/SOR-related API behavior | KRX/NXT/SOR fields are documented; KIS paper proof is marked KRX-limited where references say paper-unsupported, and NXT/SOR live behavior is marked later verification | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` |
| QA-004 | P0 | safety | Inspect commands/evidence | No credential use, login, token request, broker API call, or order placement occurred | `RUN-20260602_unit-009-kis-api-portal-verification-set.md` |

## PASS / FAIL / BLOCKED Rules

- PASS: official docs answer endpoint, paper/mock availability, KRX/NXT/SOR
  field/route design, eligibility, and live/paper separation questions without
  network calls.
- FAIL: verification uses credentials or live/paper API calls.
- PARTIAL: public docs confirm the endpoint family but leave actual account-mode
  behavior, paper balance, exact current rate-limit numbers, or
  paper-unsupported helper/realtime APIs to local fallback or a future approved
  smoke.
- BLOCKED: official docs are inaccessible or do not expose the endpoint family
  needed to design the next unit.

## Current Verdict

- QA-001: PASS
- QA-002: PARTIAL
- QA-003: PARTIAL
- QA-004: PASS

Overall: SET with future broker-network smoke required before any KIS adapter is
enabled. Use `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` as the
paper/live capability and fallback contract.
