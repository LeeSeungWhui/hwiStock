---
schema_version: hwi.evidence/v0
id: RUN-20260602-project-bootstrap
type: evidence
name: Project bootstrap evidence
unit_refs:
  - HWISTOCK-UNIT-001
module_refs:
  - HWISTOCK-MOD-001
profile_refs:
  - PROFILE-HWISTOCK
status: set
created_at: 2026-06-02
environment: docs_only
---

# Project Bootstrap Evidence

## Supersession Note

Later 2026-06-02 profile updates supersede the internal `mock_broker_api`
direction in this historical bootstrap evidence. Current policy: no internal
fake broker execution path; pre-approval behavior is no-order dry-run only, and
the first broker-backed path is approved KIS KRX paper/mock-investment.

## Summary

Created initial Hwi Work Harness docs for `hwiStock`, a stock day-trading
automation project. This bootstrap is docs-only and does not create trading
code, credentials, broker connections, paper orders, or live orders.

## Created / Expected Files

- `AGENTS.md`
- `docs/index.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/modules/HWISTOCK-MOD-001_trading-safety-core.md`
- `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md`
- `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md`
- `docs/evidence/RUN-20260602_project-bootstrap.md`

## Bootstrap QA Notes

- `AGENTS.md` points to `docs/profiles/PROFILE-HWISTOCK.md`.
- Profile approval policy requires explicit approval for broker operations, live
  orders, credentials, and real-money trading.
- Profile/module/unit require at least one full week of paper/sandbox testing
  evidence before actual live operation.
- Profile/module define strategy direction as short-term day trading (`단타`) and
  capital policy as cash-only.
- Credit, margin, 미수, borrowed funds, and leveraged capital are forbidden by
  default.
- Module contract states no live orders by default.
- Broker/API direction is now KIS because KB Securities is blocked as a practical
  personal API candidate. Internal fake broker execution is not used. Before an
  explicitly approved broker-network unit, execution stops at no-order dry-run
  records. The first broker-backed path is approved KIS KRX paper/mock
  investment; NXT/SOR support remains later confirmation work.
- Remaining Ready-Set blockers are strategy decision-packet approval or row
  exclusion, dashboard design review execution or row exclusion, current final
  external review, and final Ready-Set row closure. Market calendar, alert
  channel, and one-week test acceptance criteria are now closed by later Set
  evidence.

## Result

Status: set PASS for docs bootstrap creation. Later Set evidence closes the
bootstrap-level profile, broker, stack, source, storage, risk, AI, runner, KIS,
and dashboard decisions. Full Ready-Set implementation readiness is still
tracked separately by the Ready-Set completion gate.
