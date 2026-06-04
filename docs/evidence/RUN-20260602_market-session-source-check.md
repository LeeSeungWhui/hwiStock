---
schema_version: hwi.evidence/v0
id: RUN-20260602-market-session-source-check
type: evidence
name: Market session source check
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

# Market Session Source Check

## Summary

Checked current public market-session references for the initial hwiStock
planning contract. The working runtime model is:

- 24-hour `market_intelligence` ingestion branch.
- KRX/NXT venue-routed `trading` branch.
- Owner routing policy: 09:00-15:00 KST routes to KRX; 08:00-09:00 and
  15:00-20:00 KST routes to NXT; outside 08:00-20:00 KST is idle for trading.
- Implementation should not split the trading envelope into additional session
  modes by default. It should keep the routing simple unless a future approved
  unit changes this policy.

## Source Notes

- KRX Global trading procedures page was checked as a reference for KRX trading
  hours, but the owner policy intentionally routes only 09:00-15:00 KST to KRX.
- NXT official market/trading-system page describes the NXT market as spanning
  08:00-20:00, which is used as the non-KRX trading venue envelope.

## References

- KRX Global trading procedures:
  `https://global.krx.co.kr/contents/GLB/06/0602/0602010201/GLB0602010201T1.jsp`
- NXT trading system:
  `https://www.nextrade.co.kr/en/transactionSys/content.do`

## Follow-Up

- Select a broker/API and confirm KRX/NXT routing support for the owner-defined
  time windows.
- Broker/API direction is now KIS because KB Securities is blocked as a practical
  personal API candidate. KIS support for the owner-defined KRX/NXT routing
  fields and order behavior still requires a future official-doc contract check
  before any network call.
- Select an official/broker market-calendar source for holidays, first trading
  day schedule changes, and exceptional market operations.
