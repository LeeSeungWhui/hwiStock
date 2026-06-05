---
schema_version: hwi.evidence/v0
id: RUN-20260602-broker-selection-kis
type: evidence
name: Broker selection KIS evidence
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

# Broker Selection KIS Evidence

## Supersession Note

Later 2026-06-02 profile updates supersede the internal `mock_broker_api`
direction in this historical evidence. Current policy: no internal fake broker
execution path; pre-approval behavior is no-order dry-run only, and the first
broker-backed path is approved KIS KRX broker-adapter.

## Summary

The project owner selected Korea Investment & Securities Open API (`KIS`,
한국투자증권) as the broker/API integration direction for `hwiStock` after KB
Securities was blocked for practical personal-account API use.

This is a direction decision, not permission to call broker APIs. Internal fake
broker execution is not used. Before an explicitly approved broker-network unit,
execution stops at no-order dry-run records. The first broker-backed path is
approved KIS KRX broker-adapter. KIS operation network calls remain out of
scope until a future approved unit verifies current official docs, credentials,
endpoint modes, call limits, NXT/KRX routing support, and adapter safety
requirements.

## Source Notes

- KIS Developers official portal describes Open API support, REST/WebSocket
  calling styles, API application, domestic stock API documents, and
  OAuth-style access.
- KIS Developers API overview lists domestic stock order/account and market-data
  families, including cash stock order.
- The official KIS GitHub sample repository documents separate real and adapter
  investment app keys, Python REST/WebSocket samples, and auth environment
  switching. These samples are reference material only until the approved KIS
  adapter unit verifies the current official behavior.

## Decisions

- Broker/API provider direction: KIS.
- Pre-approval execution behavior: no-order dry-run records only.
- KIS KRX broker-adapter is the planned first broker-backed path after an
  approved KIS unit and smoke.
- KIS API network calls: forbidden until a future broker-integration unit.
- Other broker-provided adapter/adapter APIs remain deferred unless a
  later unit approves them.
- KIS KRX broker-adapter APIs require explicit approved KIS adapter unit
  and smoke before any network call.
- Credential storage: forbidden until a future approved credentials unit.
- KB Securities remains blocked as a practical personal API candidate.

## References

- KIS Developers portal: `https://apiportal.koreainvestment.com/intro`
- KIS Open API service overview:
  `https://apiportal.koreainvestment.com/about-open-api`
- KIS API docs overview: `https://apiportal.koreainvestment.com/apiservice`
- KIS API category docs:
  `https://apiportal.koreainvestment.com/apiservice-category`
- KIS official GitHub sample repository:
  `https://github.com/koreainvestment/open-trading-api`

## Follow-Up

- Define no-order dry-run schema and KIS KRX broker adapter schema/fallback.
- Confirm KIS current domestic stock order APIs, quote APIs, REST/WebSocket
  endpoints, call limits, and auth flow from official docs.
- Confirm whether KIS exposes the NXT/KRX routing details needed for the owner
  policy.
- Keep KIS adapter network disabled until an approved unit and smoke; NXT/SOR are
  not adapter-proven yet and need separate confirmation.
