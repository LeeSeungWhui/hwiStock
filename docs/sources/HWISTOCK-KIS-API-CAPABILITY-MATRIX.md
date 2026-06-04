---
schema_version: hwi.source/v0
id: HWISTOCK-KIS-API-CAPABILITY-MATRIX
type: broker_api_capability_matrix
name: KIS API capability matrix
status: set
owner: hwi
updated_at: 2026-06-02
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
assuming that every live-capable KIS API is also available in paper/mock
investment mode.

Key rule: when a KIS API is paper-unsupported or paper-constrained, KIS paper
runs must use local state, no-order dry-run records, or an explicit
disabled/fallback branch. Do not silently call a live-only API during paper
runs, and do not replace unsupported broker behavior with an internal fake
broker.

## 2. Status Labels

| label | meaning |
| --- | --- |
| `paper_ok` | KIS reference indicates paper/mock support for the relevant path. |
| `paper_constrained` | KIS reference supports paper/mock only for a narrower path, usually KRX-only. |
| `paper_unsupported` | KIS reference marks paper/mock investment as unsupported. |
| `live_verify` | Needs later explicit real-account/support-confirmation evidence before live use. |
| `local_fallback` | Use internal state, fixtures, scheduler, or system-calculated values during simulation. |

## 3. Auth / Token APIs

| API reference | KIS mode | paper/mock handling | live follow-up |
| --- | --- | --- | --- |
| `접근토큰발급(P)[인증-001].xlsx` | REST OAuth token issue | Use only inside an approved KIS paper-network unit; no-order dry-run does not need broker tokens. | Verify current token TTL, rate limits, and domain before any adapter run. |
| `접근토큰폐기(P)[인증-002].xlsx` | REST OAuth token revoke | Use only if the approved paper adapter obtains a KIS token. | Verify revoke behavior and logging/masking before live. |
| `실시간 (웹소켓) 접속키 발급[실시간-000].xlsx` | WebSocket approval key via `/oauth2/Approval` | `paper_ok` for approval-key issuance after broker-network approval; no-order dry-run uses no KIS WebSocket key. The returned `approval_key` replaces app key/secret for WebSocket authorization. | Verify current approval-key TTL, reconnect behavior, and KRX subscription behavior before live. |

## 4. Order / Account APIs

| API reference | KIS mode | paper/mock handling | live follow-up |
| --- | --- | --- | --- |
| `주식주문(현금)[v1_국내주식-001].xlsx` | Cash buy/sell order | `paper_constrained`: paper buy/sell TRs exist, but `EXCG_ID_DVSN_CD` is KRX-only in paper/mock. NXT/SOR broker branches stay disabled or explicit-fallback-only. | Verify live KRX/NXT/SOR order acceptance before enabling live venue routing. Enforce hwiStock cash-only policy even if KIS permits 미수. |
| `주식주문(정정취소)[v1_국내주식-003].xlsx` | Modify/cancel order | `paper_constrained`: paper modify/cancel TR exists, but precheck API below is paper-unsupported. Use local open-order state plus daily fill/order reconciliation. | Verify live modify/cancel workflow with `정정취소가능주문조회` before live route enablement. |
| `주식정정취소가능주문조회[v1_국내주식-004].xlsx` | Query modify/cancel-eligible orders | `paper_unsupported` / `local_fallback`: derive eligibility from local submitted/open order state and `주식일별주문체결조회`; keep strict reject if state is ambiguous. | Verify in real account/support-confirmation before relying on live cancel eligibility. |
| `주식일별주문체결조회[v1_국내주식-005].xlsx` | Daily order/fill lookup | `paper_constrained`: paper TR exists; local reference indicates paper provides KRX only. Use for KRX paper reconciliation. | Verify live KRX/NXT/SOR query filters and pagination. |
| `주식잔고조회[v1_국내주식-006].xlsx` | Balance/position lookup | `paper_ok`: use in approved KIS KRX paper adapter for cash/position reconciliation. | Verify live response fields, masking, and account/product-code mapping. |
| `매수가능조회[v1_국내주식-007].xlsx` | Buyable amount lookup | `paper_ok`: use in approved KIS paper adapter as an input to cash gate, while still applying hwiStock 2,000,000 KRW virtual capital cap if configured. | Verify live cash-only fields and ensure 미수/credit buying power is ignored. |
| `매도가능수량조회 [국내주식-165].xlsx` | Sellable quantity lookup | `paper_unsupported` / `local_fallback`: derive sellable quantity from paper balance, local fills, unsettled orders, and local position locks. | Verify live behavior before using as sell gate. |
| `주식잔고조회_실현손익[v1_국내주식-041].xlsx` | Realized PnL lookup | `paper_unsupported` / `local_fallback`: calculate PnL from fills, fees, tax model, and position ledger during simulation. | Verify live response and compare against system-calculated PnL before trusting it. |

## 5. Realtime Quote / Fill APIs

| API reference | KIS mode | paper/mock handling | live follow-up |
| --- | --- | --- | --- |
| `국내주식 실시간체결가 (KRX) [실시간-003].xlsx` | KRX realtime trade price | `paper_ok`: use after approved WebSocket paper setup. | Verify reconnect, heartbeat, and symbol subscription behavior. |
| `국내주식 실시간호가 (KRX) [실시간-004].xlsx` | KRX realtime order book | `paper_ok`: use after approved WebSocket paper setup. | Verify quote depth fields and stale-data detection. |
| `국내주식 실시간체결통보 [실시간-005].xlsx` | Realtime order/fill notice | `paper_ok`: paper fill-notice TR is documented; use for KRX paper order reconciliation when approved. | Verify live/paper TR split and masking before live. |
| `국내주식 실시간체결가 (NXT).xlsx` | NXT realtime trade price | `paper_unsupported` / `local_fallback`: simulate NXT session timing and quote events internally. | Verify live subscription support before enabling live NXT. |
| `국내주식 실시간호가 (NXT).xlsx` | NXT realtime order book | `paper_unsupported` / `local_fallback`: simulate or disable NXT order-book conditions in paper. | Verify live subscription support before enabling live NXT. |
| `국내주식 실시간체결가 (통합).xlsx` | Integrated realtime trade price | `paper_unsupported` / `local_fallback`: use KRX paper feed plus local routing metadata, or disable integrated feed dependency. | Verify live integrated feed semantics before use. |
| `국내주식 실시간호가 (통합).xlsx` | Integrated realtime order book | `paper_unsupported` / `local_fallback`: use KRX paper feed plus local routing metadata, or disable integrated feed dependency. | Verify live integrated feed semantics before use. |
| `국내주식 장운영정보 (KRX) [실시간-049].xlsx` | KRX market operation status | `paper_unsupported` / `local_fallback`: use configured market calendar/session scheduler during simulation. | Verify live feed before replacing scheduler evidence. |
| `국내주식 장운영정보 (NXT).xlsx` | NXT market operation status | `paper_unsupported` / `local_fallback`: use configured NXT session scheduler during simulation. | Verify live feed before enabling live NXT scheduler overrides. |
| `국내주식 장운영정보 (통합).xlsx` | Integrated market operation status | `paper_unsupported` / `local_fallback`: use configured market calendar/session scheduler during simulation. | Verify live feed before integrated operation-status use. |

## 6. Calendar / Session APIs

| API reference | KIS mode | paper/mock handling | live follow-up |
| --- | --- | --- | --- |
| `국내휴장일조회[국내주식-040].xlsx` | Holiday/open-day lookup | `paper_unsupported` / `local_fallback`: use an approved calendar source or local cached calendar in simulation. If called later, cache at most once per day and use `opnd_yn` as an input, not the only gate. | Verify live response before relying on it for order-day gating. |

## 7. Implementation Contract

- Adapter capabilities must be explicit, for example:
  `supportsPaperKrxOrder=true`, `supportsPaperNxtOrder=false`,
  `supportsPaperSorOrder=false`, `supportsPaperNxtRealtime=false`.
- KIS paper adapter code must reject or fallback on unsupported NXT/SOR branches
  instead of trying live-only endpoints.
- Internal fake broker execution is not used. NXT/SOR may be recorded as
  intended venue/session parameters in no-order dry-run records, but must not be
  presented as broker fill evidence.
- Live verification of NXT/SOR must be a separate approved gate. Passing a KRX
  KIS paper week does not prove NXT/SOR live brokerage behavior.
