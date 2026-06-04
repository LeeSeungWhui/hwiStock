---
schema_version: hwi.evidence/v0
id: RUN-20260604-kis-paper-mock-api-smoke
stage: go-preflight
status: pass_rest_and_websocket_smoke
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
environment: local_shell
approval_type: kis_paper_mock_api_smoke_with_mock_orders
approval_scope: kis_krx_paper_mock_supported_paths
smoke_matrix_ref: docs/set/KIS-PAPER-MOCK-API-SMOKE-MATRIX-20260604_hwistock.md
preflight_ref: docs/evidence/RUN-20260604_kis-paper-mock-api-smoke-approval-preflight.md
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

# KIS Paper/Mock API Smoke Run

## 1. Boundary And Source Grounding

This run used the owner-approved KIS paper/mock scope from
`docs/evidence/RUN-20260604_kis-paper-mock-api-smoke-approval-preflight.md`.

Hard boundaries observed:

- KIS paper REST domain only: `openapivts.koreainvestment.com`.
- KRX route only.
- One minimal paper/mock cash buy order was submitted and immediately cancelled.
- No live domain, real account, live order, real-money behavior, NXT, SOR,
  credit, margin, 미수, or borrowed capital path was used.
- No app key, app secret, access token, account number, order id, raw response,
  exact balance, or order identifier was written to this document.

Official-source checks used before execution:

- KIS Developers token endpoint documentation for `/oauth2/tokenP` and the
  paper REST domain.
- KIS Developers token revoke documentation for `/oauth2/revokeP`.
- Korea Investment official `open-trading-api` sample `kis_devlp.yaml` for
  paper REST/WS domain conventions.
- Korea Investment official `open-trading-api` sample domestic stock functions
  for paper TR IDs:
  - paper balance: `VTTC8434R`
  - paper buyable inquiry: `VTTC8908R`
  - paper cash buy order: `VTTC0012U`
  - paper order cancel/modify: `VTTC0013U`
  - paper daily order/fill inquiry: `VTTC0081R`

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
| `KIS_PAPER_BASE_URL` | present, paper REST host only |
| `KIS_PAPER_WS_URL` | present, official paper WS host form |
| `KIS_PAPER_HTS_ID` | present |

`KIS_PAPER_HTS_ID` was added after the initial REST smoke and used only as a
redacted websocket subscription key for the paper fill-notice ACK check.

## 3. Smoke Result Summary

Run time: `2026-06-04T10:09:10+09:00` for the main REST smoke, token revoke
retry at `2026-06-04T10:11:47+09:00`, and websocket fill-notice ACK smoke at
`2026-06-04T10:16:38+09:00`.

| smoke_id | API family | result | evidence summary |
| --- | --- | --- | --- |
| KIS-PAPER-001 | OAuth token issue | PASS | HTTP 200; token present; token value not printed or stored. |
| KIS-PAPER-002 | Balance/position lookup | PASS | HTTP 200; paper account reachable; holding-row count summarized only. |
| KIS-PAPER-003 | Buyable amount lookup | PASS | HTTP 200; response shape present; account and amounts not stored. |
| KIS-PAPER-004 | KRX quote | PASS | HTTP 200; quote output shape present for KRX domestic stock symbol. |
| KIS-PAPER-005 | Cash buy order | PASS | Hash key issued; one minimal KRX paper cash buy order accepted; order id redacted. |
| KIS-PAPER-006 | Cancel order | PASS | Cancel hash key issued; accepted paper order was cancelled; order id redacted. |
| KIS-PAPER-007 | Daily order/fill lookup | PASS | HTTP 200; paper daily order/fill output shape present; order ids redacted. |
| KIS-PAPER-008 | Realtime fill notice | PASS | Websocket approval key issued; paper fill-notice TR `H0STCNI9` subscription ACK received; approval key and HTS ID redacted. |
| KIS-PAPER-009 | Token revoke | PASS | First immediate reissue attempt received HTTP 403; after wait/retry, token issued and `/oauth2/revokeP` returned HTTP 200. |

## 4. Main REST Smoke Step Details

Sanitized execution summary:

| step | status | HTTP | message class |
| --- | --- | --- | --- |
| `oauth_token` | pass | 200 | token present, expiry class present |
| `quote_inquire_price` | pass | 200 | `MCA00000`, normal processing |
| `balance_inquire` | pass | 200 | paper inquiry complete |
| `buyable_inquire_psbl_order` | pass | 200 | paper inquiry complete |
| `hashkey_order_cash` | pass | 200 | hash present |
| `mock_cash_buy_order` | pass | 200 | paper buy order complete |
| `hashkey_cancel` | pass | 200 | hash present |
| `mock_order_cancel` | pass | 200 | paper cancel order complete |
| `daily_order_fill_inquire` | pass | 200 | paper inquiry complete |

The smoke runner used only response status, message class, output-shape
presence, and redacted counts for evidence. It did not persist tokens, raw
account responses, balances, order numbers, or order identifiers.

## 5. Websocket Fill-Notice Smoke Details

Sanitized websocket execution summary:

| step | status | evidence summary |
| --- | --- | --- |
| `ws_approval_key` | pass | HTTP 200; approval key present; approval key value not printed or stored. |
| `fill_notice_subscribe_send` | pass | Paper fill-notice TR `H0STCNI9` subscription request sent; HTS ID redacted. |
| `fill_notice_subscribe_ack` | pass | One ACK received for `H0STCNI9`; response class was OK; raw payload not printed or stored. |

No realtime fill data payload was required for this connectivity smoke; the
gate only needed to prove that the paper websocket approval and subscription
path can be reached safely with redaction.

## 6. Residual Items

- Because the app key and app secret were pasted into chat before this run,
  treat them as exposed in principle and consider rotating/regenerating the KIS
  paper API credentials after the current smoke/debugging phase.
- Future automated smoke code should preserve the same fail-closed behavior:
  prove paper domain first, redact identifiers, and stop before live endpoints.
