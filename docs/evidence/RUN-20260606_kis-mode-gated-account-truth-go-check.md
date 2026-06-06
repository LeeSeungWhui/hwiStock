# RUN — KIS Mode-Gated Account Truth Go-Check

- Date: 2026-06-06
- Stage: go-check
- Scope:
  - `backend/service/kis_paper_adapter.py`
  - `backend/lib/kis_market_data_runtime.py`
  - `backend/lib/kis_paper_continuous_runtime.py`
  - `backend/lib/trading_engine.py`
  - `backend/service/HwiStockRunnerService.py`
  - focused backend tests
  - current UNIT/profile/source/QA docs for KIS mode-gated operation
- Broker/order side effect: no real KIS transport was called by the validation
  commands in this evidence; tests used fake transports.
- Secrets: no secret values were read, printed, persisted, or committed.

## Changes Proven

1. KIS market-data collector is mode-aware.
   - Paper/mock mode enables KRX and integrated realtime market-data inputs.
   - Real investment mode additionally enables NXT realtime market-data inputs.
   - KIS order/cancel/modify endpoint ids remain safe-blocked from UNIT-013.
2. KIS adapter now wires the user-provided account-truth APIs:
   - sellable quantity: `GET /uapi/domestic-stock/v1/trading/inquire-psbl-sell`,
     `tr_id=TTTC8408R`;
   - cancelable-order lookup:
     `GET /uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl`,
     `tr_id=TTTC0084R`;
   - holiday/provider calendar cross-check:
     `GET /uapi/domestic-stock/v1/quotations/chk-holiday`,
     `tr_id=CTCA0903R`.
3. KIS realtime fill notice is wired through WebSocket approval plus
   `H0STCNI9` subscription evidence.
4. SELL execution preflight now requires provider sellable quantity truth and
   blocks before order transport when requested quantity exceeds provider
   sellable quantity.
5. Runtime status treats `kis_market_mode_aware` as an order-grade market-data
   source and keeps the older source name only as compatibility.
6. Current profile/unit/source/QA docs now describe the mode-gated policy instead
   of the previous fixed legacy-input/KRX-only helper-unsupported wording.

## Validation

| Check | Result |
| --- | --- |
| `source ./env.sh && python3 -m py_compile backend/service/kis_paper_adapter.py backend/lib/kis_market_data_runtime.py backend/lib/kis_paper_continuous_runtime.py backend/lib/trading_engine.py backend/service/HwiStockRunnerService.py` | PASS |
| `source ./env.sh && python3 -m pytest backend/tests/test_hwistock_runner.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_operational_go_check_pipeline.py backend/tests/test_trading_engine_order_state.py -q` | PASS — 87 tests, 11 subtests |
| `source ./env.sh && python /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn` | PASS — 0 errors, 0 warnings, 0 suppressions |

## Remaining Operational Notes

- Real provider WebSocket runtime still depends on the host having the
  WebSocket client dependency available and the required KIS HTS id configured.
- SOR remains disabled before transport.
- This evidence proves local code paths and fake-transport behavior. It does not
  claim provider-network PASS for a market-hours observation run.
