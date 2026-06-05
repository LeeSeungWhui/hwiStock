---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-009-kis-api-portal-verification-set
type: evidence
name: UNIT-009 KIS API portal verification Set
stage: set
environment: docs_only
status: partial_pass
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
unit_refs:
  - HWISTOCK-UNIT-009
profile_refs:
  - PROFILE-HWISTOCK
---

# UNIT-009 KIS API Portal Verification Set

## 1. Scope

This run verified public official KIS Developers docs and official GitHub sample
code before any KIS broker network call, token request, login, or order
placement.

## 2. Sources Checked

| source | url | result |
| --- | --- | --- |
| KIS API service summary | `https://apiportal.koreainvestment.com/apiservice-summary` | Listed domestic stock order/account APIs, quote APIs, realtime KRX/integrated/NXT APIs, and realtime fill notice. |
| KIS API reference overview | `https://apiportal.koreainvestment.com/apiservice` | Identified REST/WebSocket mode and operation/adapter endpoint separation. |
| KIS Open API service intro | `https://apiportal.koreainvestment.com/about-open-api` | Identified personal/general-corporate self-asset use and REST/WebSocket invocation model. |
| KIS service usage guide | `https://apiportal.koreainvestment.com/about-howto` | Identified account opening, ID linking, and Open API application flow. |
| KIS official GitHub sample repo | `https://github.com/koreainvestment/open-trading-api` | Confirmed sample code organization for domestic stock REST/WebSocket, adapter-mode switching, and strategy/order examples. |
| KIS sample config | `https://github.com/koreainvestment/open-trading-api/blob/main/kis_devlp.yaml` | Confirmed operation/adapter key separation, HTS ID, account/product-code fields, and operation/adapter REST/WebSocket domains. |
| Domestic cash-order sample | `https://github.com/koreainvestment/open-trading-api/blob/main/examples_llm/domestic_stock/order_cash/order_cash.py` | Confirmed `/uapi/domestic-stock/v1/trading/order-cash`, real/adapter TR IDs, and `EXCG_ID_DVSN_CD` request field. |
| Domestic stock user examples | `https://github.com/koreainvestment/open-trading-api/blob/main/examples_user/domestic_stock/domestic_stock_examples.py` | Confirmed an official sample runner uses `excg_id_dvsn_cd="SOR"` for cash order. |
| NXT realtime samples | `https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock` | Confirmed NXT realtime 체결가, 호가, 예상체결, 장운영정보, 회원사, and 프로그램매매 sample functions exist. |
| Local KIS API reference spreadsheets | `apiRefer/*.xlsx` | Rechecked 22 user-provided KIS reference files, including cash order, modify/cancel, buyable, balance, daily fill/order, sellable quantity, holiday, realtime KRX/NXT/integrated quotes, realtime fill notice, token issue/revoke, and WebSocket approval-key issuance. |
| KIS API capability matrix | `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` | Records adapter-supported, adapter-constrained, adapter-unsupported, fallback, and runtime-verification handling for the local KIS reference files. |

## 3. Findings

| finding | verdict | note |
| --- | --- | --- |
| Domestic stock cash order exists | pass | `주식주문(현금)` appears in the official API list and sample code. |
| Modify/cancel and order/fill lookup exist | pass | Official API list and sample code include modify/cancel and daily order/fill lookup. |
| Balance/cash/position style account APIs exist | pass | Official API list includes balance, buyable amount, sellable quantity, realized PnL, account asset, and profit/loss APIs. |
| KRX/NXT realtime exists | pass | Official API list and sample code expose KRX, integrated, and NXT realtime quote/market-status feeds. |
| SOR/NXT order routing | constrained | Official sample code and local references expose `EXCG_ID_DVSN_CD` and SOR/NXT-related values, but local cash-order and modify/cancel references state broker-adapter is KRX-only. Treat NXT/SOR as venue/session parameters in the engine, not as adapter-proven broker behavior. |
| Broker adapter mode exists | pass_with_constraints | Official config and auth samples separate adapter app key/secret, adapter account, and adapter REST/WebSocket domains. Local references support the KRX adapter path, but NXT/SOR order routing and NXT/integrated realtime feeds are not adapter-supported. |
| WebSocket approval key | pass | `실시간 (웹소켓) 접속키 발급[실시간-000]` documents `/oauth2/Approval`; app key/secret are request inputs and returned `approval_key` is used for WebSocket authorization. |
| Realtime quote adapter support | constrained | KRX realtime 체결가/호가 and realtime 체결통보 have adapter-supporting references; NXT and integrated realtime quote references are marked adapter-unsupported. |
| Modify/cancel adapter support | constrained | Modify/cancel order supports a adapter TR, but the precheck query `주식정정취소가능주문조회` is adapter-unsupported. Adapter simulation should use local open-order state plus daily order/fill lookup, or keep this branch disabled until a later approved smoke. |
| Holiday and sellable quantity | constrained | `국내휴장일조회` and `매도가능수량조회` are marked adapter-unsupported. Holiday lookup should be cached when used, and adapter sellability should derive from adapter balance/local position state. |
| Adapter starting budget | blocked_for_public_docs | Public docs/samples did not confirm a fixed 10,000,000 KRW balance. Verify with future adapter balance evidence. |
| Current exact rate limits | blocked_for_public_docs | KIS publishes current rate-limit notices, and official GitHub warns adapter REST limits are lower, but this pass did not capture the exact current numeric notice body. |

## 3.1 User Decision Captured

NXT/SOR are not a separate strategy family for the first engine. They are treated
as venue/session-routing parameters: KRX uses the 09:00-15:00 KST core route,
and NXT/SOR extends the same deterministic order-state semantics into the longer
08:00-20:00 KST envelope when supported. Because KIS adapter references do not
support NXT/SOR adapter proof, the pre-approval path must keep those
broker-specific branches disabled or explicit-fallback-only and may record only
no-order dry-run decisions. Verify NXT/SOR later through a separately approved
real-account/support-confirmation path before account-affecting use.

## 4. Safety Evidence

- No pasted credential was copied into a repository file.
- No broker login was attempted.
- No OAuth token request was made.
- No KIS operation, adapter, testbed, REST, or WebSocket broker endpoint was called.
- No order, balance, quote, or account API call was made.
- Public documentation and public GitHub sample files were read only.
- The temporary GitHub checkout was public sample code under `/tmp` and contains
  no hwiStock credential data.
- Local `apiRefer/*.xlsx` files were read only and summarized into
  `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`.

## 5. Result

UNIT-009 docs-only Set: PARTIAL PASS WITH KIS ADAPTER CONSTRAINTS

Use these results to shape the next trading-engine/order-state Set, but do not
enable a KIS adapter yet. A future approved broker-network smoke must confirm:

- adapter account number/product-code/HTS ID shape in hwiStock env,
- actual adapter balance,
- exact current rate limits,
- KRX adapter WebSocket realtime and order/fill notification behavior.

NXT/SOR domestic cash-order acceptance cannot be proven by the current KIS adapter
references. Keep NXT/SOR as internal venue/session parameters during no-order
dry-run and KIS adapter-capability handling, with broker-specific KIS NXT/SOR
branches disabled or explicit-fallback-only until a later approved
real-account/support-confirmation gate.
