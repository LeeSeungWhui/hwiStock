---
schema_version: hwi.kis-paper-smoke-matrix/v0
stage: set-preflight
status: pass_rest_and_websocket_smoke
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
capability_matrix_ref: docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md
approval_evidence_ref: docs/evidence/RUN-20260604_kis-paper-mock-api-smoke-approval-preflight.md
latest_smoke_evidence_ref: docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md
owner_approval_scope: kis_paper_mock_api_smoke_with_mock_orders
broker_network_scope: kis_krx_paper_mock_only
live_scope: denied
---

# KIS Paper/Mock API Smoke Matrix

## 1. Purpose

This matrix defines the first approved KIS paper/mock API smoke. The owner
approved including mock orders. The first REST and websocket smoke passed on
2026-06-04.

The goal is to prove the broker-provided KIS paper/mock KRX path with actual API
calls, not an internal fake broker.

## 2. Hard Boundaries

Allowed only inside this smoke:

- KIS paper/mock REST OAuth token issue/revoke.
- KIS paper/mock KRX-supported account/balance/buyable reads.
- KIS paper/mock KRX-supported quote/realtime setup when credentials allow.
- KIS paper/mock KRX cash order smoke.
- KIS paper/mock KRX modify/cancel smoke.
- KIS paper/mock KRX order/fill/balance reconciliation.

Denied:

- live domain calls;
- real account calls;
- live order placement;
- real-money trading;
- KIS NXT/SOR live verification;
- paper-unsupported helper APIs through live endpoints;
- credential value printing, committing, or storing in docs/evidence;
- expected-profit claims.

## 3. Credential And Redaction Rules

Use only a local user-managed secret file such as:

`/home/hwi/.config/hwistock/kis-paper.env`

Required variables for REST token, quote, balance, buyable, order, cancel, and
daily order/fill smoke:

| variable | purpose | output policy |
| --- | --- | --- |
| `KIS_PAPER_APP_KEY` | paper app key | never print |
| `KIS_PAPER_APP_SECRET` | paper app secret | never print |
| `KIS_PAPER_ACCOUNT_NO` | paper account number first 8 digits | redact in evidence |
| `KIS_PAPER_ACCOUNT_PRODUCT_CODE` | account product code such as `01` | may record as class, not account id |
| `KIS_PAPER_BASE_URL` | optional paper REST base URL | may record hostname only |

Required only for websocket realtime/fill-notice smoke:

| variable | purpose | output policy |
| --- | --- | --- |
| `KIS_PAPER_HTS_ID` | HTS ID for realtime/order notice where required | redact in evidence |
| `KIS_PAPER_WS_URL` | optional paper WebSocket URL | may record hostname only |

Evidence must summarize response shapes and status without raw credential,
token, account id, order id, or balance dumps.

## 4. Smoke Sequence

| order | smoke_id | API family | mode | expected result | evidence policy |
| --- | --- | --- | --- | --- | --- |
| 1 | KIS-PAPER-001 | OAuth token issue | paper REST | access token is obtained from paper endpoint only | record status and token TTL class; never print token |
| 2 | KIS-PAPER-002 | Balance/position lookup | paper REST / KRX | account is reachable; actual paper balance can be summarized | redact account and exact raw response; summarize balance class only |
| 3 | KIS-PAPER-003 | Buyable amount lookup | paper REST / KRX | buyable response shape is confirmed | redact account; summarize fields |
| 4 | KIS-PAPER-004 | KRX quote/realtime capability | paper REST/WebSocket if available | KRX quote/realtime setup works or fails with documented paper error | redact approval key/token; summarize subscription status |
| 5 | KIS-PAPER-005 | Cash order | paper REST / KRX | a minimal safe paper order is accepted, rejected, or blocked with known reason | redact order number/id; record only accepted/rejected/block class |
| 6 | KIS-PAPER-006 | Modify/cancel order | paper REST / KRX | modify/cancel path works against the paper order when possible | redact order id; record state transition class |
| 7 | KIS-PAPER-007 | Daily order/fill lookup | paper REST / KRX | paper order/fill query can reconcile the smoke order | redact order/account ids; summarize state |
| 8 | KIS-PAPER-008 | Realtime fill notice | paper WebSocket / KRX if available | fill notice subscription is reachable or fails with documented paper error | redact HTS/account/order ids |
| 9 | KIS-PAPER-009 | Token revoke | paper REST | token is revoked or expires according to paper behavior | record status only |

## 5. Negative / Disabled Tests

The following should not be forced through live APIs during the paper smoke:

| test_id | API family | expected handling |
| --- | --- | --- |
| KIS-PAPER-NEG-001 | NXT order route | disabled/fallback in KIS paper because local references constrain paper order to KRX |
| KIS-PAPER-NEG-002 | SOR order route | disabled/fallback in KIS paper because local references constrain paper order to KRX |
| KIS-PAPER-NEG-003 | NXT/integrated realtime | disabled/fallback unless official paper support is proven |
| KIS-PAPER-NEG-004 | cancelable-order eligibility query | local fallback because current matrix marks paper unsupported |
| KIS-PAPER-NEG-005 | sellable quantity query | local fallback because current matrix marks paper unsupported |
| KIS-PAPER-NEG-006 | realized PnL query | local fallback because current matrix marks paper unsupported |
| KIS-PAPER-NEG-007 | holiday lookup | local cached calendar fallback; do not call live endpoint during paper smoke |

## 6. Safe Order Constraints

Before `KIS-PAPER-005`:

- Use paper/mock account only.
- Use KRX route only.
- Use a minimal safe quantity and price/price-type chosen by the smoke runner
  from current paper-account/buyable evidence.
- Prefer an order path that can be cancelled immediately if accepted.
- Do not use live account number, live app key, live domain, NXT, SOR, credit,
  margin, 미수, or borrowed funds.
- If preflight cannot prove paper mode, stop before order submission.

## 7. PASS / FAIL / BLOCKED

PASS:

- Paper endpoint mode is proven.
- Token, account/buyable, KRX quote/realtime where supported, minimal paper
  order, modify/cancel, and reconciliation are either successful or fail with
  documented paper-mode errors.
- All secrets/account/order identifiers are redacted.
- No live endpoint, live account, or real order is touched.

FAIL:

- Any live endpoint or real account is used.
- Credential/token/account/order identifiers are printed or written to docs.
- A paper-unsupported API is silently replaced with a live call.
- NXT/SOR behavior is claimed as paper-proven without evidence.

BLOCKED:

- Required KIS paper env variables are missing.
- Paper account access is not enabled.
- KIS portal/account requires manual user action.
- Rate limits, trading session, or paper service downtime prevents safe smoke.

## 8. Current Status

Current status: `pass_rest_and_websocket_smoke`.

The owner approved the paper/mock API smoke including mock orders. The local
paper env file was populated outside the repository and the REST smoke passed:
OAuth token issue, KRX quote, paper balance, buyable inquiry, paper cash buy,
paper cancel, daily order/fill inquiry, and token revoke were called without
printing or storing credential/account/token/order identifiers. After
`KIS_PAPER_HTS_ID` was added to the local secret file, the paper websocket
approval key and fill-notice subscription ACK also passed without printing or
storing the approval key or HTS ID.

Latest evidence:

- `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md`
