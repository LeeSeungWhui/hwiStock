---
schema_version: hwi.kis-adapter-smoke-matrix/v0
stage: set-preflight
status: pass_rest_and_websocket_smoke
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
capability_matrix_ref: docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md
approval_evidence_ref: docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke-approval-preflight.md
latest_smoke_evidence_ref: docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md
owner_approval_scope: kis_paper_mock_api_smoke_with_mock_orders
broker_network_scope: kis_krx_paper_mock_only
account_affecting_scope: not_scoped
---

# KIS Broker Adapter API Smoke Matrix

## 1. Purpose

This matrix defines the first approved KIS broker-adapter API smoke. The owner
approved including broker orders. The first REST and websocket smoke passed on
2026-06-04.

The goal is to prove the broker-provided KIS broker-adapter KRX path with actual API
calls, not an internal fake broker.

## 2. Hard Boundaries

Allowed only inside this smoke:

- KIS broker-adapter REST OAuth token issue/revoke.
- KIS broker-adapter KRX-supported account/balance/buyable reads.
- KIS broker-adapter KRX-supported quote/realtime setup when credentials allow.
- KIS broker-adapter KRX cash order smoke.
- KIS broker-adapter KRX modify/cancel smoke.
- KIS broker-adapter KRX order/fill/balance reconciliation.

Denied:

- unapproved domain calls;
- broker account calls;
- account-affecting order placement;
- account-affecting trading;
- KIS NXT/SOR support verification;
- adapter-unsupported helper APIs through unapproved endpoints;
- credential value printing, committing, or storing in docs/evidence;
- expected-profit claims.

## 3. Credential And Redaction Rules

Use only a local user-managed secret file such as:

`/home/hwi/.config/hwistock/hwistockApi.env`

Required variables for REST token, quote, balance, buyable, order, cancel, and
daily order/fill smoke:

| variable | purpose | output policy |
| --- | --- | --- |
| `KIS_PAPER_APP_KEY` | adapter app key | never print |
| `KIS_PAPER_APP_SECRET` | adapter app secret | never print |
| `KIS_PAPER_ACCOUNT_NO` | adapter account number first 8 digits | redact in evidence |
| `KIS_PAPER_ACCOUNT_PRODUCT_CODE` | account product code such as `01` | may record as class, not account id |
| `KIS_PAPER_BASE_URL` | optional adapter REST base URL | may record hostname only |

Required only for websocket realtime/fill-notice smoke:

| variable | purpose | output policy |
| --- | --- | --- |
| `KIS_PAPER_HTS_ID` | HTS ID for realtime/order notice where required | redact in evidence |
| `KIS_PAPER_WS_URL` | optional adapter WebSocket URL | may record hostname only |

Evidence must summarize response shapes and status without raw credential,
token, account id, order id, or balance dumps.

## 4. Smoke Sequence

| order | smoke_id | API family | mode | expected result | evidence policy |
| --- | --- | --- | --- | --- | --- |
| 1 | KIS-ADAPTER-001 | OAuth token issue | adapter REST | access token is obtained from adapter endpoint only | record status and token TTL class; never print token |
| 2 | KIS-ADAPTER-002 | Balance/position lookup | adapter REST / KRX | account is reachable; actual adapter balance can be summarized | redact account and exact raw response; summarize balance class only |
| 3 | KIS-ADAPTER-003 | Buyable amount lookup | adapter REST / KRX | buyable response shape is confirmed | redact account; summarize fields |
| 4 | KIS-ADAPTER-004 | KRX quote/realtime capability | adapter REST/WebSocket if available | KRX quote/realtime setup works or fails with documented adapter error | redact approval key/token; summarize subscription status |
| 5 | KIS-ADAPTER-005 | Cash order | adapter REST / KRX | a minimal safe broker order is accepted, rejected, or blocked with known reason | redact order number/id; record only accepted/rejected/block class |
| 6 | KIS-ADAPTER-006 | Modify/cancel order | adapter REST / KRX | modify/cancel path works against the broker order when possible | redact order id; record state transition class |
| 7 | KIS-ADAPTER-007 | Daily order/fill lookup | adapter REST / KRX | broker order/fill query can reconcile the smoke order | redact order/account ids; summarize state |
| 8 | KIS-ADAPTER-008 | Realtime fill notice | adapter WebSocket / KRX if available | fill notice subscription is reachable or fails with documented adapter error | redact HTS/account/order ids |
| 9 | KIS-ADAPTER-009 | Token revoke | adapter REST | token is revoked or expires according to adapter behavior | record status only |

## 5. Negative / Disabled Tests

The following should not be forced through unapproved APIs during the adapter smoke:

| test_id | API family | expected handling |
| --- | --- | --- |
| KIS-ADAPTER-NEG-001 | NXT order route | disabled/fallback in KIS adapter because local references constrain broker order to KRX |
| KIS-ADAPTER-NEG-002 | SOR order route | disabled/fallback in KIS adapter because local references constrain broker order to KRX |
| KIS-ADAPTER-NEG-003 | NXT/integrated realtime | disabled/fallback unless official adapter support is proven |
| KIS-ADAPTER-NEG-004 | cancelable-order eligibility query | local fallback because current matrix marks adapter unsupported |
| KIS-ADAPTER-NEG-005 | sellable quantity query | local fallback because current matrix marks adapter unsupported |
| KIS-ADAPTER-NEG-006 | realized PnL query | local fallback because current matrix marks adapter unsupported |
| KIS-ADAPTER-NEG-007 | holiday lookup | local cached calendar fallback; do not call unapproved endpoint during adapter smoke |

## 6. Safe Order Constraints

Before `KIS-PAPER-005`:

- Use broker-adapter account only.
- Use KRX route only.
- Use a minimal safe quantity and price/price-type chosen by the smoke runner
  from current adapter-account/buyable evidence.
- Prefer an order path that can be cancelled immediately if accepted.
- Do not use broker account number, operation app key, unapproved domain, NXT, SOR, credit,
  margin, 미수, or borrowed funds.
- If preflight cannot prove adapter mode, stop before order submission.

## 7. PASS / FAIL / BLOCKED

PASS:

- Adapter endpoint mode is proven.
- Token, account/buyable, KRX quote/realtime where supported, minimal adapter
  order, modify/cancel, and reconciliation are either successful or fail with
  documented adapter-mode errors.
- All secrets/account/order identifiers are redacted.
- No unapproved endpoint, broker account, or real order is touched.

FAIL:

- Any unapproved endpoint or broker account is used.
- Credential/token/account/order identifiers are printed or written to docs.
- A adapter-unsupported API is silently replaced with a unapproved call.
- NXT/SOR behavior is claimed as adapter-proven without evidence.

BLOCKED:

- Required KIS broker-adapter env variables are missing.
- Adapter account access is not enabled.
- KIS portal/account requires manual user action.
- Rate limits, trading session, or adapter service downtime prevents safe smoke.

## 8. Current Status

Current status: `pass_rest_and_websocket_smoke`.

The owner approved the broker-adapter API smoke including broker orders. The local
adapter env file was populated outside the repository and the REST smoke passed:
OAuth token issue, KRX quote, adapter balance, buyable inquiry, broker cash buy,
broker cancel, daily order/fill inquiry, and token revoke were called without
printing or storing credential/account/token/order identifiers. After
`KIS_PAPER_HTS_ID` was added to the local secret file, the adapter websocket
approval key and fill-notice subscription ACK also passed without printing or
storing the approval key or HTS ID.

Latest evidence:

- `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`
