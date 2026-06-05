---
schema_version: hwi.evidence/v0
type: go_check_evidence
status: pass_local_no_network_with_side_effect_rows_blocked
project_root: /data/workspace/My/hwiStock
profile_id: PROFILE-HWISTOCK
units:
  - HWISTOCK-UNIT-012
  - HWISTOCK-UNIT-013
  - HWISTOCK-UNIT-014
  - HWISTOCK-UNIT-015
scope_decision_ref: docs/evidence/RUN-20260605_owner-selected-naver-kis6-scope.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260605_operational-paper-trading-program_hwistock.md
created_at_kst: 2026-06-05T15:15:00+09:00
---

# Operational Go-Check Evidence — UNIT-012 through UNIT-015

## 1. Verdict

Local no-network Go-Check passed for the owner-selected operational scope:
**NAVER/OpenDART public-source grounding plus exactly six KIS paper-read signal
inputs**.

This evidence does **not** claim paper-run readiness or live readiness.

- `paper_run_ready`: `false`
- `continuous_runner_ready`: `false`
- `operational_trading_readiness`: `false`
- KIS paper order transport: not enabled in this run
- AI provider network: not called in this run
- Browser/tunnel Prove: not executed in this run

## 2. Implemented Scope

| unit | local Go-Check result | implemented / verified |
| --- | --- | --- |
| UNIT-012 | PASS local, provider smoke BLOCKED | `deepseek_pro_hourly` writes `pro_hourly_market_analysis/v0`; `deepseek_flash_trade_document_10m` writes one `flash_trade_document/v0` per 10-minute bucket; Flash action list is capped at five symbols; off-universe actions are rejected; `NO_TRADE` sentinel safe-block is written when required. |
| UNIT-013 | PASS local, KIS paper-read network BLOCKED | Public ingestion is NAVER/OpenDART first-go with public RSS fallback only by explicit flag; KIS signal collector is bounded to six inputs; extra KIS endpoints and all order/cancel/modify surfaces safe-block; Flash documents convert to `paper_order_intent/v0` only with source, KIS market, portfolio, and order-state refs. |
| UNIT-014 | PASS local preflight, KIS order smoke BLOCKED | Executor preflight rejects unsafe/conflicting/duplicate intents; already-consumed idempotency keys block duplicate submission; realtime stop-loss/take-profit/trailing decisions do not wait for the next Flash tick; no broker transport is called unless paper network/order flags are explicitly enabled. |
| UNIT-015 | PASS local API/frontend, browser Prove BLOCKED | Read-only operator snapshot API and dashboard normalization exist; account/provider values remain masked; observation reports are operator-window based and do not hardcode a fixed duration. |

## 3. Code Surface

- `backend/lib/ai_orchestration.py`
- `backend/lib/ai_analysis_runtime.py`
- `backend/lib/kis_market_data_runtime.py`
- `backend/lib/kis_paper_continuous_runtime.py`
- `backend/lib/market_intelligence_ingestion_runtime.py`
- `backend/lib/operator_console_runtime.py`
- `backend/lib/trading_engine.py`
- `backend/service/ai_analysis_runner.py`
- `backend/service/kis_market_data_collector.py`
- `backend/service/kis_paper_continuous_runner.py`
- `backend/service/market_intelligence_ingestion.py`
- `backend/router/HwiStockRunnerRouter.py`
- `frontend-web/app/dashboard/*`
- `ops/systemd/user/hwistock-ai-analysis.service`
- `ops/systemd/user/hwistock-ai-flash.service`
- `ops/systemd/user/hwistock-ai-flash.timer`
- `ops/systemd/user/hwistock-kis-market-data.service`
- `ops/systemd/user/hwistock-kis-market-data.timer`

The service files for the new runners are intentionally thin wrappers. Runtime
implementations live in `backend/lib/` so service files preserve the FastAPI rule
gate contract while keeping the existing systemd entrypoints stable.

## 4. QA Disposition Matrix

| row | status | evidence |
| --- | --- | --- |
| UNIT-012 QA-001/003/004/005/008/009/010/011 | PASS | Focused backend pytest, runtime contract validator, AI CLI safe-block smoke. |
| UNIT-012 QA-002 | PASS | DeepSeek key removed for smoke; Pro/Flash artifacts safe-blocked without unlocking orders. |
| UNIT-012 QA-007 | BLOCKED | Real AI provider network operation was not scoped for this Go-Check run. |
| UNIT-013 QA-001/004/005/008/009/015/016 | PASS | Focused backend pytest and KIS collector safe-block smoke. |
| UNIT-013 QA-014 | BLOCKED | KIS paper-read network transport was not approved/executed in this run; no order endpoint was called. |
| UNIT-014 QA-001/002/003/006/008/010/013/014 | PASS | Focused backend pytest and KIS paper runner no-network smoke. |
| UNIT-014 QA-004/005/009 | BLOCKED | Order-specific KIS paper transport/reconciliation smoke requires explicit side-effect approval and market/account conditions. |
| UNIT-015 QA-001/003/004/005/006 | PASS | Focused backend pytest, full frontend vitest, and local operator API/dashboard data tests. |
| UNIT-015 QA-002 | PASS local render | Frontend tests verify dashboard render and read-only controls. |
| UNIT-015 QA-006 browser/tunnel proof | BLOCKED | Browser/tunnel Prove was not run in this Go-Check patch. |

## 5. Validation Evidence

Commands were run with `source ./env.sh` in the same shell invocation.

| command | result |
| --- | --- |
| `python3 -m py_compile backend/lib/ai_orchestration.py backend/lib/trading_engine.py backend/lib/market_intelligence.py backend/lib/ai_analysis_runtime.py backend/lib/kis_market_data_runtime.py backend/lib/kis_paper_continuous_runtime.py backend/lib/market_intelligence_ingestion_runtime.py backend/lib/operator_console_runtime.py backend/service/ai_analysis_runner.py backend/service/kis_market_data_collector.py backend/service/kis_paper_continuous_runner.py backend/service/market_intelligence_ingestion.py backend/router/HwiStockRunnerRouter.py` | PASS |
| `python3 -m pytest backend/tests/test_ai_orchestration_layer.py backend/tests/test_market_intelligence_ingestion.py backend/tests/test_operational_go_check_pipeline.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_hwistock_runner.py` | PASS, 82 tests |
| `python3 scripts/validate_runtime_contracts.py` | PASS, `valid_artifacts=12`, `invalid_cases=28`, `schema_count=12` |
| `python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --changed --fail-on-warn --profile docs/profiles/PROFILE-HWISTOCK.md` | PASS, scanned files 16, findings 0 |
| `pnpm --dir frontend-web exec vitest run` | PASS, 27 files / 132 tests |
| no-network CLI smoke under `/tmp/hwistock-go-check-smoke-20260605` | PASS: Pro safe-block, Flash safe-block, KIS market safe-block, KIS paper runner idle, base runner blocked by calendar/source config |
| `git diff --check` | PASS |
| `python3 -m pytest backend/tests` | FAIL outside operational scope: 197 passed / 12 failed. Failures are imported MyWebTemplate auth refresh/logout CSRF expectations returning 403 instead of expected 200/204/503. |

## 6. No-Side-Effect Boundary

- No live brokerage endpoint was called.
- No KIS order/cancel/modify endpoint was called.
- No AI provider network operation was called.
- No secrets, env values, raw account ids, raw KIS payloads, or provider tokens
  were printed or committed.
- The smoke data root was `/tmp/hwistock-go-check-smoke-20260605`.

## 7. Remaining Go/Prove Gates

The following rows remain blocked until explicitly scoped:

1. KIS paper-read network smoke for the six signal inputs.
2. KIS KRX paper order/reconciliation smoke with market/account conditions.
3. Browser/tunnel Prove for the read-only operator console.
4. Final operator observation-window acceptance.

Until those pass, `operational_trading_readiness` remains `false`.
