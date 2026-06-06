# RUN — 2026-06-06 Paper Experiment Readiness Split Go-Check

## Scope

- Current owner goal: start the KIS paper/mock experiment from Monday market
  open. This is not a live-money or final production-quality readiness claim.
- Split readiness into:
  - `paper_experiment_ready`: blocking gate for the Monday KIS paper/mock run.
  - `paper_order_loop_enabled`: enabled only by `paper_experiment` mode plus
    session approval and caps.
  - `live_money_trading_ready`: `not_applicable` and non-blocking for paper.
  - `production_quality_ready`: `partial_non_blocking` for the paper experiment.

## Implemented Behavior

- `backend/lib/kis_paper_continuous_runtime.py`
  - Added `HWISTOCK_OPERATION_MODE` with `paper_experiment` as the order-loop
    mode.
  - Session approval now requires `mode` or
    `operation_mode = paper_experiment`, `allow_paper_orders = true`,
    `valid_for_date_kst`, optional `valid_until_kst`, daily order cap, notional
    cap, and `live_money_scope = not_applicable`.
  - `paperExperimentReady` now requires paper network, order-loop enablement,
    session approval, configured calendar, KRX order session, order-grade market
    data source, duplicate lock, and evidence-write readiness.
  - Added paper session cap preflight before order transport.
  - Tick evidence now writes `paper_experiment_ready` and
    `paper_experiment_readiness`.
- `backend/lib/operator_console_runtime.py`
  - `paper_orders_not_submitted`, `paper_observation_not_accepted`, and
    live/final operation readiness are evidence gaps, not paper experiment
    blockers.
  - `systemd_order_enabled_contradicts_readiness` is no longer a blocker when
    the service is intentionally configured for the paper experiment.
- `ops/systemd/user/hwistock-kis-paper-runner.service`
  - Configures `HWISTOCK_OPERATION_MODE=paper_experiment`,
    `HWISTOCK_KIS_PAPER_ORDER_ENABLED=true`, daily order cap, notional cap, and
    `--allow-paper-orders`.
- Dashboard fallback/copy now presents the current target as Paper Experiment
  GO/BLOCKED instead of final operation readiness.

## Paper Experiment Hard Blockers

- Paper network or order loop disabled.
- Paper token failure.
- Account, balance, or buyable-cash failure.
- KRX calendar/session not ready.
- Session approval missing, expired, wrong date, wrong mode, or wrong
  `live_money_scope`.
- Duplicate lock failure.
- Evidence write failure.
- Submit result not recorded.
- Process crash.
- Session daily order cap or notional cap exceeded.

## Non-Blockers For Paper Experiment

- `live_money_trading_ready = not_applicable`.
- `production_quality_ready = partial_non_blocking`.
- Final observation acceptance not yet complete.
- Unsupported KIS paper/mock helper TRs that are explicitly skipped as
  `skipped_provider_unsupported`.
- Dashboard menu incompleteness.

## Validation

- PASS:
  `source ./env.sh && python3 -m py_compile backend/lib/kis_paper_continuous_runtime.py backend/lib/operator_console_runtime.py backend/service/HwiStockRunnerService.py backend/service/kis_paper_continuous_runner.py backend/tests/test_hwistock_ai_conversation.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_operational_go_check_pipeline.py`
- PASS:
  `source ./env.sh && python3 -m pytest backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_operational_go_check_pipeline.py backend/tests/test_hwistock_runner.py backend/tests/test_hwistock_ai_conversation.py -q`
  - Result: 87 passed.
- PASS:
  `source ./env.sh && pnpm --dir frontend-web exec vitest run __tests__/dashboardDataStrategy.test.jsx __tests__/tasksQueryState.test.jsx`
  - Result: 2 files passed, 11 tests passed.
- PASS:
  `source ./env.sh && python /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn`
  - Result: pass; error=0, warning=0, info=0.
- PASS:
  `git diff --check`
  - Result: no whitespace errors.

## Side Effects

- No KIS network call was made during this Go-Check.
- No deployment, service restart, credential readout, or live-money action was
  performed.
