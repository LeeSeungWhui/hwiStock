---
schema_version: hwi.evidence/v0
id: RUN-20260605-unit-010-go-check
type: go_check_evidence
status: pass_local_no_network
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-05
stage: go-check
environment: local_no_network
unit_refs:
  - HWISTOCK-UNIT-010
module_refs:
  - HWISTOCK-MOD-008
---

# UNIT-010 Go-Check Evidence — Continuous KIS Broker-Adapter Runner

## 1. Verdict

PASS for local no-network Go-Check.

`HWISTOCK-UNIT-010` now has a local implementation of the continuous KIS
broker-adapter runner foundation:

- adapter-domain-guarded KIS adapter;
- operator-selected observation-window manifest;
- system-calculated adapter ledger/reconciliation helpers;
- duration-agnostic runner tick CLI;
- read-only status API;
- systemd user service/timer templates;
- focused tests for no fixed duration, adapter/unapproved domain separation, KRX-only
  broker order path, risk overlay, no fake broker state, and secret redaction.

This is not Prove and not an operational operation start.

## 2. Changed Files

- `backend/service/kis_paper_adapter.py`
- `backend/lib/paper_trading_ledger.py`
- `backend/service/kis_paper_continuous_runner.py`
- `backend/router/HwiStockRunnerRouter.py`
- `backend/service/HwiStockRunnerService.py`
- `backend/tests/test_kis_paper_continuous_runner.py`
- `backend/tests/test_hwistock_runner.py`
- `ops/systemd/user/hwistock-kis-paper-runner.service`
- `ops/systemd/user/hwistock-kis-paper-runner.timer`

## 3. Verification

- `source ./env.sh && python -m pytest backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_hwistock_runner.py`
  - result: 42 passed
- `source ./env.sh && python -m unittest backend.tests.test_trading_engine_order_state backend.tests.test_strategy_risk_rulebook backend.tests.test_storage_contract backend.tests.test_hwistock_runner`
  - result: 36 tests OK
- `source ./env.sh && python backend/service/kis_paper_continuous_runner.py --once`
  - result: exit 0
  - status: `idle_paper_network_disabled`
  - boundary flags: no unapproved domain calls, no AI provider calls, no fake broker,
    no raw responses, no credential values printed
- `source ./env.sh && python -m py_compile backend/service/kis_paper_adapter.py backend/service/kis_paper_continuous_runner.py backend/lib/paper_trading_ledger.py backend/router/HwiStockRunnerRouter.py backend/service/HwiStockRunnerService.py`
  - result: pass
- `git diff --check`
  - result: pass

## 4. Explicit Non-Actions

- No KIS API call was made by this Go-Check.
- No KIS secret file was read or printed.
- No broker order was placed.
- No systemd unit was installed, enabled, started, stopped, or reloaded.
- No unapproved endpoint was called.
- No AI provider call was made.
- No git staging, commit, or push was performed.

## 5. Remaining Boundary

The code can run a broker-adapter KRX tick when explicitly started with
`--allow-paper-network` or through the new systemd user service, but this run
did not start it. Operational operation evidence still requires an operator
chosen observation window and a separate Prove/runtime evidence report.
