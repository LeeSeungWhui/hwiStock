---
schema_version: hwi.source/v0
id: HWISTOCK-KIS-API-CAPABILITY-MATRIX
type: broker_api_capability_matrix
name: KIS API capability matrix
status: go_check_passed
owner: hwi
updated_at: 2026-06-06
profile_refs:
  - PROFILE-HWISTOCK
unit_refs:
  - HWISTOCK-UNIT-009
source_refs:
  - apiRefer/*.xlsx
---

# KIS API Capability Matrix

## 1. Purpose

This matrix records the local KIS API reference files under `apiRefer/` and how
each API may be used in hwiStock. It exists to prevent the implementation from
assuming that every operation-capable KIS API is also available in broker-adapter
investment mode.

Key rule: when a KIS API is adapter-unsupported or adapter-constrained, KIS adapter
runs must use local state, no-order dry-run records, or an explicit
disabled/fallback branch. Do not silently call a operation-only API during adapter
runs, and do not replace unsupported broker behavior with an internal fake
broker.

## 2. Status Labels

| label | meaning |
| --- | --- |
| `paper_ok` | KIS reference indicates broker-adapter support for the relevant path. |
| `paper_constrained` | KIS reference supports broker-adapter only for a narrower or mode-gated path. |
| `paper_unsupported` | KIS reference marks broker-adapter as unsupported. |
| `live_verify` | Needs later explicit real-account/support-confirmation evidence before account-affecting use. |
| `local_fallback` | Use internal state, fixtures, scheduler, or system-calculated values during simulation. |
| `paper_proven_bounded_20260604` | KRX broker-adapter path proven only by sanitized bounded smoke `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`; does not authorize new broker calls. |
| `to_verify_in_UNIT_013` | Target endpoint for the operational market-data collector; not accepted for recurring operation use until UNIT-013 proves adapter-read support, rate limits, freshness, and sanitized storage. |

## 3. Auth / Token APIs

| API reference | KIS mode | broker-adapter handling | operation follow-up |
| --- | --- | --- | --- |
| `접근토큰발급(P)[인증-001].xlsx` | REST OAuth token issue | `paper_proven_bounded_20260604` on KRX adapter REST domain; use only inside an approved KIS adapter-network unit; no-order dry-run does not need broker tokens. | Verify current token TTL, rate limits, and domain before any adapter run. |
| `접근토큰폐기(P)[인증-002].xlsx` | REST OAuth token revoke | `paper_proven_bounded_20260604` after approved adapter token issue; use only if the approved adapter adapter obtains a KIS token. | Verify revoke behavior and logging/masking before operation. |
| `실시간 (웹소켓) 접속키 발급[실시간-000].xlsx` | WebSocket approval key via `/oauth2/Approval` | `paper_proven_bounded_20260604` for approval-key issuance on the bounded KRX adapter path; no-order dry-run uses no KIS WebSocket key. The returned `approval_key` replaces app key/secret for WebSocket authorization. | Verify current approval-key TTL, reconnect behavior, and KRX subscription behavior before operation. |

## 4. Order / Account APIs

| API reference | KIS mode | broker-adapter handling | operation follow-up |
| --- | --- | --- | --- |
| `주식주문(현금)[v1_국내주식-001].xlsx` | Cash buy/sell order | `paper_constrained` + `paper_proven_bounded_20260604` for minimal KRX broker cash buy/cancel smoke. Current runtime separates authority: integrated feed is analysis context; paper/mock execution is KRX-only; future live mode also defaults to KRX-only until a separate owner approval and Ready-Set enable NXT. SOR stays disabled. | Verify active-mode KRX order acceptance before enabling each operation venue route. NXT order acceptance requires a future separate gate. Enforce hwiStock cash-only policy even if KIS permits 미수. |
| `주식주문(정정취소)[v1_국내주식-003].xlsx` | Modify/cancel order | `paper_constrained` + `paper_proven_bounded_20260604` for broker cancel on the bounded smoke path. Cancel calls must still fail closed when provider cancelable-order truth is unavailable. | Verify operation modify/cancel workflow with provider cancelable-order truth before operation route enablement. |
| `주식정정취소가능주문조회[v1_국내주식-004].xlsx` | Query modify/cancel-eligible orders | Local reference marks mock as `모의투자 미지원`; paper/mock runtime must not call `TTTC0084R` and records `skipped_provider_unsupported`. Real-investment support remains a later explicit proof item. | Compare provider cancelable list against local pending-order state before cancel automation; in paper/mock, rely on local pending-order state and fail closed on ambiguity. |
| `주식일별주문체결조회[v1_국내주식-005].xlsx` | Daily order/fill lookup | `paper_constrained` + `paper_proven_bounded_20260604` on KRX adapter path. | Verify operation KRX/NXT/SOR query filters and pagination. |
| `주식잔고조회[v1_국내주식-006].xlsx` | Balance/position lookup | `paper_proven_bounded_20260604` on KRX adapter path; use in approved KIS KRX broker adapter for cash/position reconciliation. | Verify operation response fields, masking, and account/product-code mapping. |
| `매수가능조회[v1_국내주식-007].xlsx` | Buyable amount lookup | `paper_proven_bounded_20260604` on KRX adapter path; use in approved KIS broker adapter as an input to cash gate, while still applying hwiStock 2,000,000 KRW virtual capital cap if configured. | Verify operation cash-only fields and ensure 미수/credit buying power is ignored. |
| `매도가능수량조회 [국내주식-165].xlsx` | Sellable quantity lookup | Local reference marks mock as `모의투자 미지원`; paper/mock runtime must not call `TTTC8408R` and records `skipped_provider_unsupported`. SELL preflight therefore blocks unless a supported provider truth source is available. | Compare provider sellable quantity against local position/lock state before broad exit automation. |
| `주식잔고조회_실현손익[v1_국내주식-041].xlsx` | Realized PnL lookup | Local reference marks mock as `모의투자 미지원`; paper/mock runtime must not call `TTTC8494R` and records `skipped_provider_unsupported`. Realized PnL should be derived from supported fills/ledger until real-investment proof exists. | Compare provider-realized PnL against system-calculated fill/fee/tax PnL before trusting discrepancies. |

## 5. Realtime Quote / Fill APIs

| API reference | KIS mode | broker-adapter handling | operation follow-up |
| --- | --- | --- | --- |
| `국내주식 실시간체결가 (KRX) [실시간-003].xlsx` | KRX realtime trade price | `paper_ok`: use after approved WebSocket adapter setup. | Verify reconnect, heartbeat, and symbol subscription behavior. |
| `국내주식 실시간호가 (KRX) [실시간-004].xlsx` | KRX realtime order book | `paper_ok`: use after approved WebSocket adapter setup. | Verify quote depth fields and stale-data detection. |
| `국내주식 실시간체결통보 [실시간-005].xlsx` | Realtime order/fill notice | `paper_proven_bounded_20260604` for KRX fill-notice subscription ACK on bounded smoke path; use for KRX broker order reconciliation when approved. | Verify operation/adapter TR split and masking before operation. |
| `국내주식 실시간체결가 (NXT).xlsx` | NXT realtime trade price | Mode-gated implementation exists as TR `H0NXCNT0`; disabled in paper/mock and disabled by default in future live mode until separate NXT approval and Ready-Set. | Verify provider subscription ACK and field semantics before relying on NXT for order routing. |
| `국내주식 실시간호가 (NXT).xlsx` | NXT realtime order book | Mode-gated implementation exists as TR `H0NXASP0`; disabled in paper/mock and disabled by default in future live mode until separate NXT approval and Ready-Set. | Verify provider subscription ACK and field semantics before relying on NXT for order routing. |
| `국내주식 실시간체결가 (통합).xlsx` | Integrated realtime trade price | Implemented as TR `H0UNCNT0`; enabled as the default market-analysis authority for paper/mock and future live modes. | Verify integrated feed semantics and duplicate handling against KRX/NXT feeds; integrated feed alone cannot authorize execution. |
| `국내주식 실시간호가 (통합).xlsx` | Integrated realtime order book | Implemented as TR `H0UNASP0`; enabled as the default market-analysis authority for paper/mock and future live modes. | Verify integrated feed semantics and duplicate handling against KRX/NXT feeds; integrated feed alone cannot authorize execution. |
| `국내주식 장운영정보 (KRX) [실시간-049].xlsx` | KRX market operation status | Implemented as TR `H0STMKO0`; enabled in paper/mock and real modes as market-session evidence, while local calendar remains the order gate. | Verify feed/session disagreement handling before replacing calendar evidence. |
| `국내주식 장운영정보 (NXT).xlsx` | NXT market operation status | Mode-gated implementation exists as TR `H0NXMKO0`; disabled in paper/mock and disabled by default in future live mode until separate NXT approval and Ready-Set. | Verify feed/session disagreement handling before NXT order routing. |
| `국내주식 장운영정보 (통합).xlsx` | Integrated market operation status | Implemented as TR `H0UNMKO0`; enabled as default market-analysis context in paper/mock and future live modes. | Verify feed/session disagreement handling before replacing calendar evidence. |

## 6. Intraday REST Quote / Ranking / Analysis APIs

These are the operational Ready-Set targets for the 1-3-minute market-hours REST
collector. They are not order endpoints, but they still require explicit
adapter-read approval, rate-limit handling, and sanitized storage before Go-Check
PASS.

| API reference | KIS mode | broker-adapter handling | operation follow-up |
| --- | --- | --- | --- |
| `주식현재가 시세[v1_국내주식-008].xlsx` | Current price/quote context | `paper_proven_bounded_20260604` only for the bounded KRX adapter quote smoke; UNIT-013 must prove recurring sanitized collector behavior before use in trade documents. | Verify operation response fields and quote staleness handling. |
| `주식당일분봉조회[v1_국내주식-022].xlsx` | Intraday minute-bar context | `paper_constrained` / `to_verify_in_UNIT_013`: use only after an approved adapter-read collector proves fields and rate limits. | Verify operation continuity and session gaps. |
| `주식현재가 당일시간대별체결[v1_국내주식-023].xlsx` | Intraday execution context | `paper_constrained` / `to_verify_in_UNIT_013`: use only after an approved adapter-read collector proves fields and rate limits. | Verify operation pagination and timestamp semantics. |
| `거래량순위[v1_국내주식-047].xlsx` | Volume ranking | `to_verify_in_UNIT_013`: target 1-3-minute REST collector; fail closed if unsupported or stale. | Verify operation/adapter parity before account-affecting use. |
| `국내주식 등락률 순위[v1_국내주식-088].xlsx` | Fluctuation ranking | `to_verify_in_UNIT_013`: target 1-3-minute REST collector; fail closed if unsupported or stale. | Verify operation/adapter parity before account-affecting use. |
| `국내주식 체결강도 상위[v1_국내주식-101].xlsx` | Execution-strength / volume-power ranking | `to_verify_in_UNIT_013`: target 1-3-minute REST collector; fail closed if unsupported or stale. | Verify operation/adapter parity before account-affecting use. |
| `프로그램매매 종합현황(시간) [국내주식-114].xlsx` | Program-trading aggregate status by time | `to_verify_in_UNIT_013`: optional market-context input; fail closed if unsupported or stale. | Verify operation/adapter parity before account-affecting use. |

UNIT-013 signal-input allowlist is now authority-aware. The default
market-analysis feed is integrated realtime trade/orderbook/market-operation
plus the four REST ranking/context endpoints. KRX quote/session evidence remains
the executable-order authority in UNIT-014. NXT realtime
trade/orderbook/market-operation subscriptions are disabled in paper/mock and in
future live mode unless a separate owner approval plus Ready-Set enables NXT.
Current-price REST, minute bars, intraday executions, top-interest stocks,
balances, buyable cash, sellable quantity, cancelable-order lookup, and
order/fill reconciliation remain outside the market-signal collector and belong
to broker execution/account truth.

## 7. Calendar / Session APIs

| API reference | KIS mode | broker-adapter handling | operation follow-up |
| --- | --- | --- | --- |
| `국내휴장일조회[국내주식-040].xlsx` | Holiday/open-day lookup | Local reference marks mock as `모의투자 미지원`; paper/mock runtime must not call `CTCA0903R` and records `skipped_provider_unsupported`. Local cached KRX/NXT calendar remains the primary order gate. | Cache provider holiday truth only after a supported mode is explicitly proven; fail closed on calendar/provider disagreement before orders. |

## 8. Implementation Contract

- Adapter capabilities must be explicit, for example:
  `supportsPaperKrxOrder=true`, `supportsPaperNxtOrder=false`,
  `supportsPaperIntegratedRealtime=true`, `supportsPaperCancelableQuery=false`,
  `supportsPaperSellableQuantityQuery=true`, and
  `supportsRealNxtRealtime=true`.
- KIS broker adapter code must reject or fallback on unsupported NXT/SOR branches
  instead of trying operation-only endpoints.
- Internal fake broker execution is not used. NXT/SOR may be recorded as
  intended venue/session parameters in no-order dry-run records, but must not be
  presented as broker fill evidence.
- Operation verification of NXT/SOR must be a separate approved gate. Passing a KRX
  KIS operation observation window does not prove NXT/SOR brokerage behavior.

## 9. Bounded Adapter/Adapter Smoke Cross-Reference (2026-06-04)

Sanitized evidence: `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`.
Current-authority UNIT-009 rebaseline closure reference:
`docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`.

| smoke_family | matrix effect | still denied without future scoped unit |
| --- | --- | --- |
| OAuth token issue/revoke (adapter REST) | `paper_proven_bounded_20260604` | new token calls in ordinary Go rows |
| balance, buyable, KRX quote | `paper_proven_bounded_20260604` | unscoped account/quote runtime |
| broker cash buy + cancel (KRX only) | `paper_proven_bounded_20260604` | additional adapter/account-affecting orders |
| daily order/fill inquiry (KRX) | `paper_proven_bounded_20260604` | unscoped reconciliation polling |
| WebSocket approval + fill-notice ACK | `paper_proven_bounded_20260604` | unscoped realtime subscriptions |

This section references the completed 2026-06-04 bounded smoke only. It does
not replace the later mode-gated runtime proof for NXT orders, SOR disabled
behavior, real-mode provider holiday/calendar cross-checks, sellable quantity,
cancelable-order lookup, or operation-domain behavior.
