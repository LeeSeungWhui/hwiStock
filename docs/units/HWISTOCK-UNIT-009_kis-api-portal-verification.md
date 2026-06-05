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
updated_at: 2026-06-04
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
  - docs/evidence/RUN-20260604_unit-009-go-preflight.md
  - docs/evidence/RUN-20260604_unit-009-go-check.md
---

# KIS API Portal Verification

## 1. Goal

Verify the current official KIS API portal before any KIS, broker, paper/mock,
or live network call is implemented. Target portal:
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
- Official paper/mock-investment API availability.
- Paper/mock starting budget and whether 10,000,000 KRW is supported.
- Live vs paper endpoint separation.
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
| AC-02 | P0 | Paper/mock mode is confirmed | Paper endpoint separation is confirmed; KRX paper core order/account/quote/realtime paths are cross-referenced to sanitized bounded smoke `RUN-20260604_kis-paper-mock-api-smoke.md`; exact paper budget and current numeric limits still require future account evidence | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `RUN-20260604_unit-009-go-check-rebaseline.md` | QA-002 | pass_with_partial_boundary |
| AC-03 | P0 | KRX/NXT/SOR behavior is confirmed | KRX/NXT/SOR fields are documented for live-capable APIs; KIS paper remains KRX-limited where references say paper-unsupported; NXT/SOR routing stays `live_verify` | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `RUN-20260604_unit-009-go-check-rebaseline.md` | QA-003 | pass_with_partial_boundary |
| AC-04 | P0 | No network call is made during verification | Unit remained docs/public-sample only; no credential use, login, token request, broker API call, or order placement occurred during Set or the current-authority rebaseline closure | `RUN-20260602_unit-009-kis-api-portal-verification-set.md`; `RUN-20260604_unit-009-go-check-rebaseline.md` | QA-004 | pass |

## 5. Official Source Snapshot

Checked on 2026-06-02 KST.

| source | url | use |
| --- | --- | --- |
| KIS API service summary | `https://apiportal.koreainvestment.com/apiservice-summary` | official endpoint-family list |
| KIS API reference overview | `https://apiportal.koreainvestment.com/apiservice` | REST/WebSocket and live/paper domain separation |
| KIS Open API service intro | `https://apiportal.koreainvestment.com/about-open-api` | personal/general-corporate eligibility, REST/WebSocket model |
| KIS service usage guide | `https://apiportal.koreainvestment.com/about-howto` | account opening, ID linking, Open API application flow |
| KIS official GitHub sample repo | `https://github.com/koreainvestment/open-trading-api` | sample configuration and domestic-stock function contracts |
| KIS sample config | `https://github.com/koreainvestment/open-trading-api/blob/main/kis_devlp.yaml` | app key separation, account/product-code shape, live/paper domains |
| Local KIS API reference spreadsheets | `apiRefer/*.xlsx` | exact KIS REST/WebSocket TR IDs, paper support flags, exchange-route constraints, and approval-key flow from user-provided API reference files |
| KIS API capability matrix | `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` | project-local list of paper-supported, paper-constrained, paper-unsupported, fallback, and live-verification API behavior |

## 6. Verification Results

| area | status | result |
| --- | --- | --- |
| Personal eligibility | confirmed | KIS Open API is documented for personal/general-corporate users trading their own assets after account opening, ID linking, and Open API application. Quote data is not approved for third-party redistribution. |
| Domestic cash order | confirmed | The API list includes domestic stock cash order, credit order, modify/cancel, daily order/fill lookup, balance, buyable amount, sellable quantity, and related account APIs. |
| Credit order | documented but excluded | KIS exposes credit-order APIs, but hwiStock capital policy is cash-only. Credit, margin, 미수, and leverage remain forbidden by project policy. |
| Realtime quotes | confirmed | The API list includes KRX, integrated, and NXT realtime 체결가/호가/예상체결/member/program/장운영정보 categories. Official GitHub samples include NXT WebSocket functions such as `H0NXCNT0`, `H0NXASP0`, and `H0NXMKO0`. |
| Realtime order/fill notice | confirmed | The API list includes domestic stock realtime 체결통보, and the OAuth category includes WebSocket approval-key issuance. |
| Live/paper separation | confirmed | Official sample config separates live app key/secret and paper app key/secret, live REST/WebSocket domains, and paper REST/WebSocket domains. Sample auth uses `svr="prod"` for live and `svr="vps"` for paper. |
| Required account fields | confirmed | Official samples require app key, app secret, HTS ID, account number first 8 digits, and product code such as `01` for a comprehensive stock account. Paper stock account number is separate from live stock account number. |
| WebSocket approval key | confirmed | Local reference `실시간 (웹소켓) 접속키 발급[실시간-000]` documents `/oauth2/Approval`: app key/secret are inputs, `approval_key` is returned, and the approval key is used for WebSocket session authorization instead of app key/secret in the WebSocket header. |
| Paper/mock availability | confirmed with hard KRX limits | Official samples and local references support paper credentials and paper endpoints. Local order/account/realtime references show KIS paper supports the core KRX path, but NXT/SOR order routing and NXT/integrated realtime feeds are not paper-supported in several files. |
| Paper/mock budget | not confirmed | Public docs/samples did not confirm a fixed 10,000,000 KRW starting balance. Treat 10,000,000 KRW as the project target/expectation until a future paper balance smoke confirms the actual account balance. |
| KRX/NXT/SOR order field | constrained | Local cash-order and modify/cancel references document `EXCG_ID_DVSN_CD` values `KRX`, `NXT`, and `SOR`, but the same references say paper/mock investment is KRX-only. Treat NXT/SOR order routing as live-capable but not paper-proven. |
| Modify/cancel support | constrained | `주식주문(정정취소)` supports paper TR `VTTC0013U`, but `주식정정취소가능주문조회` is marked paper-unsupported. Paper cancel flows must rely on local open-order state plus daily fill/order lookup, or be deferred until a later approved smoke. |
| Holiday and sellable-quantity checks | constrained | `국내휴장일조회` and `매도가능수량조회` are marked paper-unsupported. Holiday checks should be cached and read at most once per day when used; paper sellability should be derived from paper balance/position evidence and local order state. |
| Current rate limits | partially confirmed | KIS publishes a current rate-limit notice, and official GitHub warns paper REST limits are lower. This docs-only pass did not confirm exact current numeric limits from the notice body. Implementation must use conservative local throttles and record current official numbers before any broker network unit. |

## 7. hwiStock Broker Boundary Decisions

- Internal fake broker execution is not used.
- KIS adapter code may be designed around the confirmed endpoint families, but
  broker network calls must stay disabled until a future approved KIS paper
  broker-network unit.
- AI layers cannot hold KIS credentials, request KIS tokens, or call order APIs.
- Cash-only remains mandatory. The existence of KIS credit-order APIs does not
  change hwiStock policy.
- NXT/SOR routing may be represented in the order-state contract as a requested
  exchange route, but KIS paper testing cannot prove it where the local KIS
  references say paper/mock is KRX-only. Use no-order dry-run records or
  disabled/fallback markers for NXT/SOR before requiring a separate approved
  live-readonly/support-confirmation path for live NXT/SOR routing.
- The operator-selected KIS paper/sandbox observation window can prove only the
  KIS-supported KRX paper path unless a future official document or account-mode
  change expands paper NXT/SOR support.
- Paper-unsupported helper APIs, such as modify/cancel eligibility lookup,
  sellable quantity, realized PnL, holiday lookup, and NXT/integrated realtime
  feeds, are tracked in
  `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` with local fallback and
  live-verification requirements.
- Paper budget must be read from KIS paper account balance evidence, not assumed
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
  bounded KIS paper/mock smoke for proven KRX paper paths only.
- The completed smoke does **not** authorize new KIS calls, paper orders, live orders,
  credential use, or broker network activity in ordinary Go rows.
- Residual partial items (paper budget amount, exact rate limits, NXT/SOR live proof,
  paper-unsupported helpers) remain deferred to future explicitly approved units.

## 9. Open Questions / Follow-Up Inputs

- KIS paper account number first 8 digits, product code, and HTS ID are needed
  for any future paper smoke. Do not store or print secrets in docs/evidence.
- Confirm actual paper-account balance through a balance API or KIS paper screen
  before calling the paper budget `10,000,000 KRW`.
- Confirm exact current REST/WebSocket/OAuth rate limits from the official notice
  body immediately before implementation.
- Confirm whether domestic live cash order accepts `EXCG_ID_DVSN_CD=NXT` and
  `EXCG_ID_DVSN_CD=SOR` for the specific real account mode before any live
  routing is enabled.
- Confirm exact paper behavior for KRX realtime order/fill notification after
  WebSocket approval-key issuance.
