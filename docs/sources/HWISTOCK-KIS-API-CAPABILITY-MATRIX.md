---
schema_version: hwi.source/v0
id: HWISTOCK-KIS-API-CAPABILITY-MATRIX
type: broker_api_capability_matrix
name: KIS API capability matrix
status: go_check_passed
owner: hwi
updated_at: 2026-06-04
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
| `paper_constrained` | KIS reference supports broker-adapter only for a narrower path, usually KRX-only. |
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
| `주식주문(현금)[v1_국내주식-001].xlsx` | Cash buy/sell order | `paper_constrained` + `paper_proven_bounded_20260604` for minimal KRX broker cash buy/cancel smoke only; `EXCG_ID_DVSN_CD` remains KRX-only in broker-adapter. NXT/SOR broker branches stay disabled or explicit-fallback-only. | Verify operation KRX/NXT/SOR order acceptance before enabling operation venue routing. Enforce hwiStock cash-only policy even if KIS permits 미수. |
| `주식주문(정정취소)[v1_국내주식-003].xlsx` | Modify/cancel order | `paper_constrained` + `paper_proven_bounded_20260604` for broker cancel on the bounded smoke path; precheck API below remains adapter-unsupported. Use local open-order state plus daily fill/order reconciliation. | Verify operation modify/cancel workflow with `정정취소가능주문조회` before operation route enablement. |
| `주식정정취소가능주문조회[v1_국내주식-004].xlsx` | Query modify/cancel-eligible orders | `paper_unsupported` / `local_fallback`: derive eligibility from local submitted/open order state and `주식일별주문체결조회`; keep strict reject if state is ambiguous. | Verify in broker account/support-confirmation before relying on operation cancel eligibility. |
| `주식일별주문체결조회[v1_국내주식-005].xlsx` | Daily order/fill lookup | `paper_constrained` + `paper_proven_bounded_20260604` on KRX adapter path. | Verify operation KRX/NXT/SOR query filters and pagination. |
| `주식잔고조회[v1_국내주식-006].xlsx` | Balance/position lookup | `paper_proven_bounded_20260604` on KRX adapter path; use in approved KIS KRX broker adapter for cash/position reconciliation. | Verify operation response fields, masking, and account/product-code mapping. |
| `매수가능조회[v1_국내주식-007].xlsx` | Buyable amount lookup | `paper_proven_bounded_20260604` on KRX adapter path; use in approved KIS broker adapter as an input to cash gate, while still applying hwiStock 2,000,000 KRW virtual capital cap if configured. | Verify operation cash-only fields and ensure 미수/credit buying power is ignored. |
| `매도가능수량조회 [국내주식-165].xlsx` | Sellable quantity lookup | `paper_unsupported` / `local_fallback`: derive sellable quantity from adapter balance, local fills, unsettled orders, and local position locks. | Verify operation behavior before using as sell gate. |
| `주식잔고조회_실현손익[v1_국내주식-041].xlsx` | Realized PnL lookup | Adapter endpoint implemented from the supplied API reference: `GET /uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl`, `tr_id=TTTC8494R`; sanitized runner evidence records status and `rlzt_pfls` summary when returned. | Compare provider-realized PnL against system-calculated fill/fee/tax PnL before trusting discrepancies. |

## 5. Realtime Quote / Fill APIs

| API reference | KIS mode | broker-adapter handling | operation follow-up |
| --- | --- | --- | --- |
| `국내주식 실시간체결가 (KRX) [실시간-003].xlsx` | KRX realtime trade price | `paper_ok`: use after approved WebSocket adapter setup. | Verify reconnect, heartbeat, and symbol subscription behavior. |
| `국내주식 실시간호가 (KRX) [실시간-004].xlsx` | KRX realtime order book | `paper_ok`: use after approved WebSocket adapter setup. | Verify quote depth fields and stale-data detection. |
| `국내주식 실시간체결통보 [실시간-005].xlsx` | Realtime order/fill notice | `paper_proven_bounded_20260604` for KRX fill-notice subscription ACK on bounded smoke path; use for KRX broker order reconciliation when approved. | Verify operation/adapter TR split and masking before operation. |
| `국내주식 실시간체결가 (NXT).xlsx` | NXT realtime trade price | `paper_unsupported` / `local_fallback`: simulate NXT session timing and quote events internally. | Verify operation subscription support before enabling operation NXT. |
| `국내주식 실시간호가 (NXT).xlsx` | NXT realtime order book | `paper_unsupported` / `local_fallback`: simulate or disable NXT order-book conditions in adapter. | Verify operation subscription support before enabling operation NXT. |
| `국내주식 실시간체결가 (통합).xlsx` | Integrated realtime trade price | `paper_unsupported` / `local_fallback`: use KRX adapter feed plus local routing metadata, or disable integrated feed dependency. | Verify operation integrated feed semantics before use. |
| `국내주식 실시간호가 (통합).xlsx` | Integrated realtime order book | `paper_unsupported` / `local_fallback`: use KRX adapter feed plus local routing metadata, or disable integrated feed dependency. | Verify operation integrated feed semantics before use. |
| `국내주식 장운영정보 (KRX) [실시간-049].xlsx` | KRX market operation status | `paper_unsupported` / `local_fallback`: use configured market calendar/session scheduler during simulation. | Verify operation feed before replacing scheduler evidence. |
| `국내주식 장운영정보 (NXT).xlsx` | NXT market operation status | `paper_unsupported` / `local_fallback`: use configured NXT session scheduler during simulation. | Verify operation feed before enabling operation NXT scheduler overrides. |
| `국내주식 장운영정보 (통합).xlsx` | Integrated market operation status | `paper_unsupported` / `local_fallback`: use configured market calendar/session scheduler during simulation. | Verify operation feed before integrated operation-status use. |

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

UNIT-013 first signal-input allowlist is intentionally narrower than this
matrix. For the owner-selected first runtime scope, UNIT-013 may attempt only:
KRX realtime trade price, KRX realtime orderbook, volume ranking,
execution-strength/volume-power ranking, fluctuation ranking, and
program-trading aggregate status where adapter-supported. Current-price REST,
minute bars, intraday executions, top-interest stocks, fill notices, balances,
buyable cash, and helper APIs are out of UNIT-013 signal scope unless a later
approved unit changes this list.

## 7. Calendar / Session APIs

| API reference | KIS mode | broker-adapter handling | operation follow-up |
| --- | --- | --- | --- |
| `국내휴장일조회[국내주식-040].xlsx` | Holiday/open-day lookup | `paper_unsupported` / `local_fallback`: use an approved calendar source or local cached calendar in simulation. If called later, cache at most once per day and use `opnd_yn` as an input, not the only gate. | Verify operation response before relying on it for order-day gating. |

## 8. Implementation Contract

- Adapter capabilities must be explicit, for example:
  `supportsPaperKrxOrder=true`, `supportsPaperNxtOrder=false`,
  `supportsPaperSorOrder=false`, `supportsPaperNxtRealtime=false`.
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

This section references completed bounded smoke only. It does not replace
`paper_unsupported`, `paper_constrained`, `local_fallback`, or `live_verify` labels
for NXT/SOR orders, integrated/NXT realtime, holiday lookup, sellable quantity,
modify/cancel eligibility lookup, or operation-domain behavior.
