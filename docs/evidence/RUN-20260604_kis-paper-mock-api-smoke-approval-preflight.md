---
schema_version: hwi.evidence/v0
id: RUN-20260604-kis-paper-mock-api-smoke-approval-preflight
stage: set-preflight
status: blocked_missing_kis_paper_env
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
environment: local_shell
approval_type: kis_paper_mock_api_smoke_with_mock_orders
approval_scope: kis_krx_paper_mock_supported_paths
smoke_matrix_ref: docs/set/KIS-PAPER-MOCK-API-SMOKE-MATRIX-20260604_hwistock.md
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

# KIS Paper/Mock API Smoke Approval And Preflight

## 1. Owner Approval Receipt

| field | value |
| --- | --- |
| received_at | 2026-06-04 conversation turn |
| owner_message | User selected `모의 주문 포함` for the KIS mock API scope card, repeated once. |
| matched_scope | KIS paper/mock API smoke including mock order, modify, and cancel calls. |
| approvals_granted | KIS paper/mock broker network calls for the supported KRX paper path; KIS paper/mock token issuance; KIS paper/mock read-only account/quote calls; KIS paper/mock order/modify/cancel smoke with safe constraints. |
| approvals_not_granted | live API calls, real account calls, live orders, real-money trading, credential commits, public/LAN dashboard exposure, NXT/SOR live verification, unsupported paper helper calls through live endpoints. |
| credential_policy | Values may be loaded only from `/home/hwi/.config/hwistock/kis-paper.env` or an equivalent user-managed secret store; values must not be printed, pasted, committed, or written to docs. |
| current_result | blocked before network/API calls because the paper env file has no loadable variables. |

This approval supersedes earlier Ready-Set denial only for the bounded KIS
paper/mock API smoke described in
`docs/set/KIS-PAPER-MOCK-API-SMOKE-MATRIX-20260604_hwistock.md`.

It does not approve any live or real-money behavior.

## 2. Environment Preflight

Observed locally:

| check | result |
| --- | --- |
| `/home/hwi/.config/hwistock/kis-paper.env` exists | pass |
| file mode | `600` |
| loadable variable keys in `kis-paper.env` | `0` |
| `env.sh` loads project env files | pass |
| standard KIS paper env presence after `source ./env.sh` | missing |

Checked variable names only; no credential values were printed.

Expected paper-smoke variable names:

- `KIS_PAPER_APP_KEY`
- `KIS_PAPER_APP_SECRET`
- `KIS_PAPER_ACCOUNT_NO`
- `KIS_PAPER_ACCOUNT_PRODUCT_CODE`
- `KIS_PAPER_HTS_ID`
- optional explicit domains if not hardcoded by the smoke runner:
  - `KIS_PAPER_BASE_URL`
  - `KIS_PAPER_WS_URL`

## 3. Current Blocker

The smoke cannot run yet because there are no loadable KIS paper variables.

No KIS token request, account call, quote call, realtime call, paper order,
modify/cancel call, AI call, or live call was made during this preflight.

## 4. Next Run Conditions

Before actual API calls:

1. Populate `/home/hwi/.config/hwistock/kis-paper.env` with the expected
   paper/mock keys.
2. Re-run env presence checks without printing values.
3. Re-check the smoke matrix and paper-only/live-denied boundaries.
4. Run the smoke in a fail-closed sequence:
   token -> read-only account/balance/buyable -> quote/realtime setup ->
   minimal paper order -> modify/cancel -> order/fill/balance reconciliation ->
   token cleanup.
5. Write the result under `docs/evidence/` with all tokens, app keys, account
   identifiers, balances, order ids, and raw responses redacted or summarized.
