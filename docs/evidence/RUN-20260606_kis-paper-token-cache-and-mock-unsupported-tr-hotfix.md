---
schema_version: hwi.run_evidence/v0
id: RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix
status: pass
created_at_kst: 2026-06-06T17:19:24+09:00
stage: go-check-hotfix
profile: docs/profiles/PROFILE-HWISTOCK.md
scope:
  - backend/lib/kis_paper_token_cache.py
  - backend/lib/kis_paper_continuous_runtime.py
  - backend/service/kis_paper_adapter.py
  - backend/lib/trading_engine.py
  - backend/tests/test_kis_paper_continuous_runner.py
  - backend/tests/test_trading_engine_order_state.py
  - docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md
  - docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md
  - docs/modules/HWISTOCK-MOD-009_operational-automated-trading-program.md
  - docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md
  - docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md
  - docs/units/HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md
---

# KIS paper token cache and mock-unsupported TR hotfix

## Summary

Runtime smoke found two operational defects after the mode-gated KIS runner was
started:

1. KIS token cache was not used by the real `KisPaperAdapter` because the cache
   detector looked for a stale private `_request` marker instead of the current
   `requestBrokerJson` method / `UrllibJsonTransport` runtime shape.
2. Local KIS references mark these APIs as `모의투자 미지원`, but the paper/mock
   runner still called their real-investment TR IDs and accumulated HTTP 500
   warnings:
   - `매도가능수량조회 [국내주식-165]` / `TTTC8408R`
   - `주식정정취소가능주문조회[v1_국내주식-004]` / `TTTC0084R`
   - `주식잔고조회_실현손익[v1_국내주식-041]` / `TTTC8494R`
   - `국내휴장일조회[국내주식-040]` / `CTCA0903R`

## Changes

- Token cache now recognizes the current `KisPaperAdapter.requestBrokerJson`
  capability and the real `UrllibJsonTransport` runtime path.
- Invalid cached token responses from account-read steps trigger one cache
  invalidation and fresh-token retry.
- Paper/mock runtime now skips provider-unsupported sellable quantity,
  cancelable-order, realized-PnL, and holiday TRs with
  `skipped_provider_unsupported` instead of calling real-investment TR IDs.
- Paper/mock account truth preserves `sellable_quantity=null` when provider
  truth is unsupported instead of collapsing unknown to zero.
- Capability docs and tests now record paper/mock unsupported account helper
  branches explicitly.

## Validation

- `source ./env.sh && python3 -m pytest backend/tests/test_hwistock_runner.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_operational_go_check_pipeline.py backend/tests/test_trading_engine_order_state.py -q`
  - Result: `90 passed, 11 subtests passed`
- `source ./env.sh && python /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn`
  - Result: pass, error=0 warning=0 info=0
- `git diff --check`
  - Result: pass

## Runtime smoke

Manual systemd one-shot:

- `systemctl --user start hwistock-kis-paper-runner.service`

Latest sanitized evidence:

- `/data/workspace/My/hwiStock/data/evidence/2026-06-06/kis-paper-continuous-latest.json`
- Result summary:
  - `status=ok`
  - `oauth_token_cache=pass`
  - `websocket_approval=pass`
  - `quote_inquire_price=pass`
  - `balance_inquire=pass`
  - `buyable_inquire_psbl_order=pass`
  - `daily_order_fill_inquire=pass`
  - `sellable_inquire_psbl_sell=skipped_provider_unsupported`
  - `realized_pnl_inquire=skipped_provider_unsupported`
  - `cancelable_order_inquire=skipped_provider_unsupported`
  - `holiday_inquire=skipped_provider_unsupported`

No credential values or raw KIS response payloads were printed or committed.
