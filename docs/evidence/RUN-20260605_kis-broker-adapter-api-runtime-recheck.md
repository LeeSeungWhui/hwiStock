---
schema_version: hwi.evidence/v0
id: RUN-20260605-kis-adapter-adapter-api-runtime-recheck
stage: prove/kis-operationtime-recheck
status: partial_pass_order_blocked_by_market_time
current_authority: true
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-05
environment: local_shell
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
smoke_matrix_ref: docs/set/KIS-BROKER-ADAPTER-API-SMOKE-MATRIX-20260604_hwistock.md
previous_full_smoke_ref: docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md
approval_source: owner_chat_2026-06-05_kis_mock_api_run_all
approval_scope: kis_paper_mock_api_runtime_recheck_with_mock_order_attempt
credential_values_printed: false
broker_network_calls_made: true
kis_token_calls_made: true
kis_order_calls_made: true
paper_orders_placed: false
paper_order_block_reason: market_not_started
paper_orders_cancelled: false
live_orders_placed: false
live_domain_calls_made: false
raw_responses_stored: false
---

# KIS Broker Adapter API Runtime Recheck — 2026-06-05

## 1. Verdict

Runtime recheck result: **PARTIAL PASS**.

The KIS broker-adapter REST and WebSocket paths were called again from the local
shell on 2026-06-05. OAuth, KRX quote, balance, buyable amount, hash key,
daily order/fill inquiry, token revoke, WebSocket approval key, and adapter
fill-notice subscription ACK all worked.

The broker cash buy order endpoint was also called, but KIS rejected the order
with the adapter-mode class `모의투자 장시작전 입니다.` because the run happened
before the market opened. Therefore no broker order was accepted and there was no
accepted order to cancel in this recheck.

The previous full smoke on 2026-06-04 remains the current evidence that a
minimal broker-adapter cash buy order can be accepted and immediately cancelled
during a valid automated trading window.

## 2. Boundary

Observed hard boundaries:

- REST host was the KIS broker-adapter host `openapivts.koreainvestment.com`.
- WebSocket host class was the KIS broker-adapter WebSocket host form
  `ws://ops.koreainvestment.com:31000`.
- KRX domestic stock sample symbol class only.
- Minimal one-share broker order attempt only.
- No unapproved domain call.
- No account-affecting order.
- No account-affecting order.
- No app key, app secret, access token, approval key, account number, order
  number, exact balance, raw response, or fill payload was printed or stored.

## 3. Execution Timeline

| time_kst | run | result |
| --- | --- | --- |
| 2026-06-05T04:01:10+09:00 | first REST recheck without enough throttle | PARTIAL; KIS returned `EGW00201` rate-limit responses for buyable/order |
| 2026-06-05T04:02:14+09:00 | throttled REST recheck with 1.35s minimum call gap | PARTIAL PASS; all reads/hash/revoke passed, order endpoint rejected as market-not-started |
| 2026-06-05T04:03:00+09:00 | WebSocket approval and fill-notice subscription ACK | PASS |

The first run intentionally remained sanitized and was used only to identify the
KIS rate-limit behavior. The throttled run is the REST result of record.

## 4. REST Result Of Record

Sanitized REST result from the throttled run:

| step | result | HTTP | KIS code/class | note |
| --- | --- | --- | --- | --- |
| `oauth_token` | PASS | 200 | token present | token value not printed or stored |
| `quote_inquire_price` | PASS | 200 | `MCA00000` | quote shape present |
| `balance_inquire` | PASS | 200 | `20310000` | holding row count summarized only |
| `buyable_inquire_psbl_order` | PASS | 200 | `20310000` | buyable output shape present |
| `hashkey_order_cash` | PASS | 200 | hash present | hash value not printed or stored |
| `mock_cash_buy_order` | EXPECTED_REJECT | 200 | `40570000`, market not started | order endpoint was called; no broker order accepted |
| `mock_order_cancel` | SKIPPED | n/a | order not accepted | no order number existed to cancel |
| `daily_order_fill_inquire` | PASS | 200 | `70070000` | no same-day order/fill row in this pre-market recheck |
| `oauth_revoke` | PASS | 200 | revoke response shape present | token value not printed or stored |

Result counts for the throttled REST run:

- pass: 7
- fail/expected reject: 1
- skipped: 1
- blocked/error: 0

## 5. WebSocket Result

Sanitized WebSocket result:

| step | result | evidence |
| --- | --- | --- |
| `ws_approval_key` | PASS | HTTP 200, approval key present, key value not printed |
| `fill_notice_subscribe_ack` | PASS | TR class `H0STCNI9`, `rt_cd=0`, `msg_cd=OPSP0000`, raw payload not printed |

## 6. Interpretation

This recheck proves that the local KIS broker-adapter credentials and current
network path are usable at runtime. It also proves that the broker order endpoint
was actually invoked during the recheck, but the current pre-market time window
prevented acceptance.

Use this evidence together with
`docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`:

- 2026-06-04 proves accepted broker buy + cancel during a valid trading window.
- 2026-06-05 proves current credential/connectivity health and documents the
  market-not-started rejection class for pre-market order attempts.

This evidence does not authorize account-affecting operation, unapproved endpoint calls, ongoing
unbounded broker polling, or unattended broker order loops.
