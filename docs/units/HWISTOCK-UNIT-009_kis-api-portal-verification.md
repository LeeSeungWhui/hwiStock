---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-009
type: unit
domain: broker
name: KIS API portal verification
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
priority: P0
source_of_truth: official_docs_required
work_class: docs_only
owner: hwi
updated_at: 2026-06-06
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-005
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-009_kis-api-portal-verification.md
links:
  - PROFILE-HWISTOCK
evidence_refs:
  - docs/evidence/RUN-20260602_unit-009-kis-api-portal-verification-set.md
  - docs/evidence/RUN-20260604_unit-009-go-preflight-rebaseline.md
  - docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md
  - docs/evidence/RUN-20260606_kis-mode-gated-account-truth-go-check.md
  - docs/evidence/RUN-20260604_unit-009-go-preflight.md
  - docs/evidence/RUN-20260604_unit-009-go-check.md
---

# KIS API Portal Verification

## 1. Goal

Verify the current official KIS API portal before any KIS, broker, broker-adapter,
or operation network call is implemented. Target portal:
`https://apiportal.koreainvestment.com/apiservice-summary`.

## 2. Included Scope

- Domestic stock buy/sell order APIs.
- Order modify/cancel APIs.
- Order/fill status APIs.
- Balance/cash/position APIs.
- Realtime quote/WebSocket APIs.
- Order book/체결강도 support.
- KRX/NXT venue support.
- SOR support and API availability.
- Official broker-adapter API availability.
- Broker adapter starting budget and whether 10,000,000 KRW is supported.
- Operation vs adapter endpoint separation.
- Personal-account eligibility.
- Credential/token flow.
- Rate limits and throttling.

## 3. Excluded Scope

- API key storage.
- Actual API calls.
- Any broker login.
- Any order placement.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows | result |
| --- | --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | Official API list is reviewed | Required order/quote/account endpoints are enumerated | `RUN-20260602_unit-009-kis-api-portal-verification-set.md` | QA-001 | pass |
| AC-02 | P0 | Broker adapter mode is confirmed | Adapter endpoint separation is confirmed; KRX adapter core order/account/quote/realtime paths are cross-referenced to sanitized bounded smoke `RUN-20260604_kis-paper-mock-api-smoke.md`; exact adapter budget and current numeric limits still require future account evidence | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `RUN-20260604_unit-009-go-check-rebaseline.md` | QA-002 | pass_with_partial_boundary |
| AC-03 | P0 | KRX/NXT/SOR behavior is confirmed | KRX/NXT/SOR fields are documented for operation-capable APIs; hwiStock applies paper/mock KRX-only broker routing, real investment KRX/NXT routing where capability flags allow it, and SOR disabled/fallback routing | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `RUN-20260604_unit-009-go-check-rebaseline.md` | QA-003 | pass_with_partial_boundary |
| AC-04 | P0 | No network call is made during verification | Unit remained docs/public-sample only; no credential use, login, token request, broker API call, or order placement occurred during Set or the current-authority rebaseline closure | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `RUN-20260604_unit-009-go-check-rebaseline.md` | QA-004 | pass |

## 5. Official Source Snapshot

Checked on 2026-06-02 KST.

| source | url | use |
| --- | --- | --- |
| KIS API service summary | `https://apiportal.koreainvestment.com/apiservice-summary` | official endpoint-family list |
| KIS API reference overview | `https://apiportal.koreainvestment.com/apiservice` | REST/WebSocket and operation/adapter domain separation |
| KIS Open API service intro | `https://apiportal.koreainvestment.com/about-open-api` | personal/general-corporate eligibility, REST/WebSocket model |
| KIS service usage guide | `https://apiportal.koreainvestment.com/about-howto` | account opening, ID linking, Open API application flow |
| KIS official GitHub sample repo | `https://github.com/koreainvestment/open-trading-api` | sample configuration and domestic-stock function contracts |
| KIS sample config | `https://github.com/koreainvestment/open-trading-api/blob/main/kis_devlp.yaml` | app key separation, account/product-code shape, operation/adapter domains |
| Local KIS API reference spreadsheets | `apiRefer/*.xlsx` | exact KIS REST/WebSocket TR IDs, adapter support flags, exchange-route constraints, and approval-key flow from user-provided API reference files |
| KIS API capability matrix | `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` | project-local list of adapter-supported, adapter-constrained, mode-gated, provider-query-required, fallback, and runtime-verification API behavior |

## 6. Verification Results

| area | status | result |
| --- | --- | --- |
| Personal eligibility | confirmed | KIS Open API is documented for personal/general-corporate users trading their own assets after account opening, ID linking, and Open API application. Quote data is not approved for third-party redistribution. |
| Domestic cash order | confirmed | The API list includes domestic stock cash order, credit order, modify/cancel, daily order/fill lookup, balance, buyable amount, sellable quantity, and related account APIs. |
| Credit order | documented but excluded | KIS exposes credit-order APIs, but hwiStock capital policy is cash-only. Credit, margin, 미수, and leverage remain forbidden by project policy. |
| Realtime quotes | confirmed | The API list includes KRX, integrated, and NXT realtime 체결가/호가/예상체결/member/program/장운영정보 categories. Official GitHub samples include NXT WebSocket functions such as `H0NXCNT0`, `H0NXASP0`, and `H0NXMKO0`. |
| Realtime order/fill notice | confirmed | The API list includes domestic stock realtime 체결통보, and the OAuth category includes WebSocket approval-key issuance. |
| Operation/adapter separation | confirmed | Official sample config separates operation app key/secret and adapter app key/secret, operation REST/WebSocket domains, and adapter REST/WebSocket domains. Sample auth uses `svr="prod"` for operation and `svr="vps"` for adapter. |
| Required account fields | confirmed | Official samples require app key, app secret, HTS ID, account number first 8 digits, and product code such as `01` for a comprehensive stock account. Adapter stock account number is separate from operation stock account number. |
| WebSocket approval key | confirmed | Local reference `실시간 (웹소켓) 접속키 발급[실시간-000]` documents `/oauth2/Approval`: app key/secret are inputs, `approval_key` is returned, and the approval key is used for WebSocket session authorization instead of app key/secret in the WebSocket header. |
| Broker adapter availability | confirmed with mode gates | Official samples and local references support adapter credentials and adapter endpoints. hwiStock now treats paper/mock as KRX plus integrated market-data/account-truth helpers, real investment mode as KRX plus NXT where KIS capability flags allow it, and SOR as disabled until a future contract proves it. |
| Broker adapter budget | not confirmed | Public docs/samples did not confirm a fixed 10,000,000 KRW starting balance. Treat 10,000,000 KRW as the project target/expectation until a future adapter balance smoke confirms the actual account balance. |
| KRX/NXT/SOR order field | mode-gated | Local cash-order and modify/cancel references document `EXCG_ID_DVSN_CD` values `KRX`, `NXT`, and `SOR`. hwiStock enables KRX in paper/mock mode, enables KRX/NXT in real investment mode, and keeps SOR disabled. |
| Modify/cancel support | provider-query-required | `주식주문(정정취소)` supports adapter TR `VTTC0013U`, and `주식정정취소가능주문조회` is wired as `TTTC0084R`. Automated cancel/replace flows must compare provider cancelable-order truth with local pending-order state before any cancel call. |
| Holiday and sellable-quantity checks | provider-query-required | `국내휴장일조회` is wired as `CTCA0903R`, and `매도가능수량조회` is wired as `TTTC8408R`. Local calendar remains the schedule authority, while provider holiday/sellable truth is recorded as cross-check/account truth; SELL preflight blocks if requested quantity exceeds provider sellable quantity. |
| Current rate limits | partially confirmed | KIS publishes a current rate-limit notice, and official GitHub warns adapter REST limits are lower. This docs-only pass did not confirm exact current numeric limits from the notice body. Implementation must use conservative local throttles and record current official numbers before any broker network unit. |

## 7. hwiStock Broker Boundary Decisions

- Internal fake broker execution is not used.
- KIS adapter code may be designed around the confirmed endpoint families, but
  broker network calls must stay disabled until a future approved KIS adapter
  broker-network unit.
- AI layers cannot hold KIS credentials, request KIS tokens, or call order APIs.
- Cash-only remains mandatory. The existence of KIS credit-order APIs does not
  change hwiStock policy.
- NXT/SOR routing may be represented in the order-state contract as a requested
  exchange route. Paper/mock mode must reject NXT broker branches; real
  investment mode may enable NXT where KIS capability flags allow it; SOR
  remains disabled/fallback until a future approved contract enables it.
- The operator-selected KIS adapter-backed observation window must record which
  investment mode was active and which venues were enabled.
- Provider helper APIs, such as modify/cancel eligibility lookup, sellable
  quantity, realized PnL, holiday lookup, and NXT/integrated realtime feeds, are
  tracked in `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` with
  provider-query-required and mode-gated runtime-verification requirements.
- Adapter budget must be read from KIS broker-adapter account balance evidence, not assumed
  from the project target.

## 8. Go-Check Boundary (2026-06-04 Rebaseline)

Current-authority Go-Check closed this unit as docs-only / local-reference
verification. Evidence:
`docs/evidence/RUN-20260604_unit-009-go-preflight-rebaseline.md` and
`docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`.

Historical supporting docs-only evidence remains preserved at
`docs/evidence/RUN-20260604_unit-009-go-preflight.md` and
`docs/evidence/RUN-20260604_unit-009-go-check.md`, but those files are superseded
as current Go authorization by the rebaseline closure above.

- `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` now cross-references sanitized
  bounded KIS broker-adapter smoke for proven KRX adapter paths only.
- The completed smoke does **not** authorize new KIS calls, broker orders, account-affecting orders,
  credential use, or broker network activity in ordinary Go rows.
- Residual partial items (adapter budget amount, exact rate limits, NXT/SOR operation proof,
  disabled SOR behavior, provider helper edge cases, and extended account-truth
  reconciliation) remain deferred to future explicitly approved units.

## 9. Open Questions / Follow-Up Inputs

- KIS broker-adapter account number first 8 digits, product code, and HTS ID are needed
  for any future adapter smoke. Do not store or print secrets in docs/evidence.
- Confirm actual adapter-account balance through a balance API or KIS adapter screen
  before calling the adapter budget `10,000,000 KRW`.
- Confirm exact current REST/WebSocket/OAuth rate limits from the official notice
  body immediately before implementation.
- Confirm whether domestic operation cash order accepts `EXCG_ID_DVSN_CD=NXT` and
  `EXCG_ID_DVSN_CD=SOR` for the specific broker account mode before any operation
  routing is enabled.
- Confirm exact adapter behavior for KRX realtime order/fill notification after
  WebSocket approval-key issuance.
