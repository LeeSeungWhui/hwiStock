---
schema_version: hwi.evidence/v0
id: RUN-20260604-kis-adapter-adapter-api-smoke-approval-preflight
stage: set-preflight
status: blocked_missing_kis_paper_env
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
environment: local_shell
approval_type: kis_paper_mock_api_smoke_with_mock_orders
approval_scope: kis_krx_paper_mock_supported_paths
smoke_matrix_ref: docs/set/KIS-BROKER-ADAPTER-API-SMOKE-MATRIX-20260604_hwistock.md
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
capability_matrix_ref: docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md
unit_refs:
  - docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md
  - docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md
credential_values_printed: false
broker_network_calls_made: false
kis_token_calls_made: false
kis_order_calls_made: false
paper_orders_placed: false
live_orders_placed: false
blocker: kis_paper_env_has_no_loadable_variables
---

# KIS Broker Adapter API Smoke Approval And Preflight

## 1. Owner Approval Receipt

| field | value |
| --- | --- |
| received_at | 2026-06-04 conversation turn |
| owner_message | User selected `모의 주문 포함` for the KIS broker-adapter API scope card, repeated once. |
| matched_scope | KIS broker-adapter API smoke including broker order, modify, and cancel calls. |
| approvals_granted | KIS broker-adapter broker network calls for the supported KRX adapter path; KIS broker-adapter token issuance; KIS broker-adapter read-only account/quote calls; KIS broker-adapter order/modify/cancel smoke with safe constraints. |
| approvals_not_granted | unapproved API calls, broker account calls, account-affecting orders, account-affecting trading, credential commits, public/LAN dashboard exposure, NXT/SOR support verification, unsupported adapter helper calls through unapproved endpoints. |
| credential_policy | Values may be loaded only from `/home/hwi/.config/hwistock/kis-paper.env` or an equivalent user-managed secret store; values must not be printed, pasted, committed, or written to docs. |
| current_result | blocked before network/API calls because the adapter env file has no loadable variables. |

This approval supersedes earlier Ready-Set denial only for the bounded KIS
broker-adapter API smoke described in
`docs/set/KIS-BROKER-ADAPTER-API-SMOKE-MATRIX-20260604_hwistock.md`.

It does not approve any operation or account-affecting behavior.

## 2. Environment Preflight

Observed locally:

| check | result |
| --- | --- |
| `/home/hwi/.config/hwistock/kis-paper.env` exists | pass |
| file mode | `600` |
| loadable variable keys in `kis-paper.env` | `0` |
| `env.sh` loads project env files | pass |
| standard KIS broker-adapter env presence after `source ./env.sh` | missing |

Checked variable names only; no credential values were printed.

Expected adapter-smoke variable names:

- `KIS_PAPER_APP_KEY`
- `KIS_PAPER_APP_SECRET`
- `KIS_PAPER_ACCOUNT_NO`
- `KIS_PAPER_ACCOUNT_PRODUCT_CODE`
- `KIS_PAPER_HTS_ID`
- optional explicit domains if not hardcoded by the smoke runner:
  - `KIS_PAPER_BASE_URL`
  - `KIS_PAPER_WS_URL`

## 3. Current Blocker

The smoke cannot run yet because there are no loadable KIS broker-adapter variables.

No KIS token request, account call, quote call, realtime call, broker order,
modify/cancel call, AI call, or unapproved call was made during this preflight.

## 4. Next Run Conditions

Before actual API calls:

1. Populate `/home/hwi/.config/hwistock/kis-paper.env` with the expected
   broker-adapter keys.
2. Re-run env presence checks without printing values.
3. Re-check the smoke matrix and adapter-bound/operation-denied boundaries.
4. Run the smoke in a fail-closed sequence:
   token -> read-only account/balance/buyable -> quote/realtime setup ->
   minimal broker order -> modify/cancel -> order/fill/balance reconciliation ->
   token cleanup.
5. Write the result under `docs/evidence/` with all tokens, app keys, account
   identifiers, balances, order ids, and raw responses redacted or summarized.
