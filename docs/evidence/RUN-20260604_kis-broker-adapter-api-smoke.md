---
schema_version: hwi.evidence/v0
id: RUN-20260604-kis-adapter-adapter-api-smoke
stage: go-preflight
status: pass_rest_and_websocket_smoke
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
environment: local_shell
approval_type: kis_paper_mock_api_smoke_with_mock_orders
approval_scope: kis_krx_paper_mock_supported_paths
smoke_matrix_ref: docs/set/KIS-BROKER-ADAPTER-API-SMOKE-MATRIX-20260604_hwistock.md
preflight_ref: docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke-approval-preflight.md
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
capability_matrix_ref: docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md
credential_values_printed: false
broker_network_calls_made: true
kis_token_calls_made: true
kis_order_calls_made: true
paper_orders_placed: true
paper_orders_cancelled: true
live_orders_placed: false
live_domain_calls_made: false
raw_responses_stored: false
---

# KIS Broker Adapter API Smoke Run

## 1. Boundary And Source Grounding

This run used the owner-approved KIS broker-adapter scope from
`docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke-approval-preflight.md`.

Hard boundaries observed:

- KIS broker-adapter REST domain only: `openapivts.koreainvestment.com`.
- KRX route only.
- One minimal broker-adapter cash buy order was submitted and immediately cancelled.
- No unapproved domain, broker account, account-affecting order, account-affecting behavior, NXT, SOR,
  credit, margin, 미수, or borrowed capital path was used.
- No app key, app secret, access token, account number, order id, raw response,
  exact balance, or order identifier was written to this document.

Official-source checks used before execution:

- KIS Developers token endpoint documentation for `/oauth2/tokenP` and the
  adapter REST domain.
- KIS Developers token revoke documentation for `/oauth2/revokeP`.
- Korea Investment official `open-trading-api` sample `kis_devlp.yaml` for
  adapter REST/WS domain conventions.
- Korea Investment official `open-trading-api` sample domestic stock functions
  for adapter TR IDs:
  - adapter balance: `VTTC8434R`
  - adapter buyable inquiry: `VTTC8908R`
  - broker cash buy order: `VTTC0012U`
  - broker order cancel/modify: `VTTC0013U`
  - broker daily order/fill inquiry: `VTTC0081R`

## 2. Environment Proof

Observed locally before API calls:

| check | result |
| --- | --- |
| secret file path | `/home/hwi/.config/hwistock/kis-paper.env` |
| file mode | `600` |
| `KIS_PAPER_APP_KEY` | present |
| `KIS_PAPER_APP_SECRET` | present |
| `KIS_PAPER_ACCOUNT_NO` | present |
| `KIS_PAPER_ACCOUNT_PRODUCT_CODE` | present |
| `KIS_PAPER_BASE_URL` | present, adapter REST host only |
| `KIS_PAPER_WS_URL` | present, official adapter WS host form |
| `KIS_PAPER_HTS_ID` | present |

`KIS_PAPER_HTS_ID` was added after the initial REST smoke and used only as a
redacted websocket subscription key for the adapter fill-notice ACK check.

## 3. Smoke Result Summary

Run time: `2026-06-04T10:09:10+09:00` for the main REST smoke, token revoke
retry at `2026-06-04T10:11:47+09:00`, and websocket fill-notice ACK smoke at
`2026-06-04T10:16:38+09:00`.

| smoke_id | API family | result | evidence summary |
| --- | --- | --- | --- |
| KIS-ADAPTER-001 | OAuth token issue | PASS | HTTP 200; token present; token value not printed or stored. |
| KIS-ADAPTER-002 | Balance/position lookup | PASS | HTTP 200; adapter account reachable; holding-row count summarized only. |
| KIS-ADAPTER-003 | Buyable amount lookup | PASS | HTTP 200; response shape present; account and amounts not stored. |
| KIS-ADAPTER-004 | KRX quote | PASS | HTTP 200; quote output shape present for KRX domestic stock symbol. |
| KIS-ADAPTER-005 | Cash buy order | PASS | Hash key issued; one minimal KRX broker cash buy order accepted; order id redacted. |
| KIS-ADAPTER-006 | Cancel order | PASS | Cancel hash key issued; accepted broker order was cancelled; order id redacted. |
| KIS-ADAPTER-007 | Daily order/fill lookup | PASS | HTTP 200; broker daily order/fill output shape present; order ids redacted. |
| KIS-ADAPTER-008 | Realtime fill notice | PASS | Websocket approval key issued; adapter fill-notice TR `H0STCNI9` subscription ACK received; approval key and HTS ID redacted. |
| KIS-ADAPTER-009 | Token revoke | PASS | First immediate reissue attempt received HTTP 403; after wait/retry, token issued and `/oauth2/revokeP` returned HTTP 200. |

## 4. Main REST Smoke Step Details

Sanitized execution summary:

| step | status | HTTP | message class |
| --- | --- | --- | --- |
| `oauth_token` | pass | 200 | token present, expiry class present |
| `quote_inquire_price` | pass | 200 | `MCA00000`, normal processing |
| `balance_inquire` | pass | 200 | broker inquiry complete |
| `buyable_inquire_psbl_order` | pass | 200 | broker inquiry complete |
| `hashkey_order_cash` | pass | 200 | hash present |
| `mock_cash_buy_order` | pass | 200 | broker buy order complete |
| `hashkey_cancel` | pass | 200 | hash present |
| `mock_order_cancel` | pass | 200 | broker cancel order complete |
| `daily_order_fill_inquire` | pass | 200 | broker inquiry complete |

The smoke runner used only response status, message class, output-shape
presence, and redacted counts for evidence. It did not persist tokens, raw
account responses, balances, order numbers, or order identifiers.

## 5. Websocket Fill-Notice Smoke Details

Sanitized websocket execution summary:

| step | status | evidence summary |
| --- | --- | --- |
| `ws_approval_key` | pass | HTTP 200; approval key present; approval key value not printed or stored. |
| `fill_notice_subscribe_send` | pass | Adapter fill-notice TR `H0STCNI9` subscription request sent; HTS ID redacted. |
| `fill_notice_subscribe_ack` | pass | One ACK received for `H0STCNI9`; response class was OK; raw payload not printed or stored. |

No realtime fill data payload was required for this connectivity smoke; the
gate only needed to prove that the adapter websocket approval and subscription
path can be reached safely with redaction.

## 6. Residual Items

- Because the app key and app secret were pasted into chat before this run,
  treat them as exposed in principle and consider rotating/regenerating the KIS
  adapter API credentials after the current smoke/debugging phase.
- Future automated smoke code should preserve the same fail-closed behavior:
  prove adapter domain first, redact identifiers, and stop before unapproved endpoints.
