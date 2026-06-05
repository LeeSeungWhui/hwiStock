---
schema_version: hwi.evidence/v0
id: RUN-20260602-broker-candidate-kb-blocked
type: evidence
name: Broker candidate KB Securities blocked evidence
unit_refs:
  - HWISTOCK-UNIT-002
module_refs:
  - HWISTOCK-MOD-001
profile_refs:
  - PROFILE-HWISTOCK
status: draft
created_at: 2026-06-02
environment: docs_only
---

# Broker Candidate KB Securities Blocked Evidence

## Supersession Note

Later 2026-06-02 profile updates supersede the internal `mock_broker_api`
direction in this historical evidence. Current policy: no internal fake broker
execution path; pre-approval behavior is no-order dry-run only, and the first
broker-backed path is approved KIS KRX broker-adapter.

## Summary

KB Securities (`KB증권`) is no longer selected as the broker/API direction for
`hwiStock`. The project owner confirmed that KB does not provide the needed API
path for personal use. Treat KB as blocked for this personal-account automation
project unless a future official confirmation proves otherwise.

Internal fake broker execution is not used. Before an explicitly approved
broker-network unit, execution stops at no-order dry-run records. The first
broker-backed path is approved KIS KRX broker-adapter; KB remains blocked
for this project.

## Source Notes

- KB Securities Fintech Store public pages show an institution/partner-style
  signup and approval flow before API-market use.
- KB Securities partner pages describe open APIs and screen APIs for investment
  services, including stock order, quote lookup, and balance checking.
- Public KB pages also expose simulated/demo experience content, including
  domestic stock order flows. These KB paths remain excluded because KB is not
  the selected broker direction.
- Owner confirmation on 2026-06-02: KB does not provide the needed personal-use
  API path for this project.

## Decisions

- Broker/API provider: KIS is selected in
  `docs/evidence/RUN-20260602_broker-selection-kis.md`.
- KB Securities: blocked as a practical personal API candidate.
- Pre-approval execution behavior: no-order dry-run records only.
- KIS KRX broker-adapter is allowed only after an approved KIS unit and
  smoke; other broker-provided adapter/adapter APIs remain deferred
  unless a later unit approves them.
- External broker network calls: forbidden until a future broker-integration
  unit.
- Credential storage: forbidden until a future approved credentials unit.

## References

- KB Securities Fintech Store login/API area: `https://store.kbsec.com/apis`
- KB Securities partner page: `https://store.kbsec.com/aboutpartner`
- KB Securities Fintech Store intro: `https://store.kbsec.com/intro`
- KB Group Open API portal: `https://apiportal.kbfg.com/`

## Follow-Up

- Define no-order dry-run schema and KIS KRX broker adapter schema/fallback.
- Choose a broker that supports personal-account domestic-stock order APIs, if
  operation integration remains a goal.
- Verify current official docs for personal eligibility, domestic stock order
  APIs, quote APIs, credential flow, rate limits, and KRX/NXT route support
  before any network call.
- Keep KB broker/broker-adapter paths out of scope and verify KIS KRX broker-adapter behavior from
  official docs before any broker-network call.
