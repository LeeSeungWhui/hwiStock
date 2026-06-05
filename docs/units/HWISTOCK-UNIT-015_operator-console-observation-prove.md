---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-015
type: unit
domain: frontend_backend_ops
name: Operator console and observation Prove
status: set
implementation_status: not_started
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-05
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-006
  - HWISTOCK-MOD-007
  - HWISTOCK-MOD-008
code_paths:
  include:
    - backend/router/HwiStockRunnerRouter.py
    - backend/service/HwiStockRunnerService.py
    - frontend-web/app/dashboard/**
    - frontend-web/app/portfolio/**
    - frontend-web/tests/**
    - ops/tunnel/*
  exclude:
    - "**/*.env"
    - backend/config.ini
    - frontend-web/config.ini
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-015_operator-console-observation-prove.md
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-operational-paper-trading-program.md
---

# Operator Console And Observation Prove

## 1. Goal

Make the owner able to tell whether the paper program is actually running,
blocked, trading, reconciling, or safe-stopped.

This unit is read-only from the dashboard perspective. It can display state and
evidence, but it must not expose direct buy/sell controls.

## 2. Included Scope

- Dashboard/API cards for:
  - service/timer health;
  - latest market-intelligence tick;
  - latest AI analysis artifacts;
  - latest signal/intent state;
  - latest KIS paper health/runner tick;
  - order gate and block reasons;
  - kill-switch state;
  - observation-window start/end/operator note;
  - daily/final paper observation reports.
- Evidence writer for daily and final observation summaries.
- Browser/tunnel Prove route over loopback/SSH forwarding.
- Clear distinction between:
  - running service;
  - paper network enabled;
  - paper orders submitted;
  - paper observation accepted;
  - live readiness.

## 3. Excluded Scope

- Dashboard buy/sell buttons.
- Dashboard live toggle.
- Public/LAN bind.
- Raw account numbers, raw KIS responses, credentials, or full article bodies.
- Profit guarantee or "live-ready" claims.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result |
| --- | --- | --- | --- |
| AC-01 | P0 | Runtime status is visible | API/dashboard show installed/running/failed timers and latest tick paths. |
| AC-02 | P0 | Paper vs live readiness is separated | UI can show paper-run progress while `operational_trading_readiness` remains false until explicit live approval. |
| AC-03 | P0 | Dashboard is read-only | No buy/sell, live-order, or service-control buttons are visible. |
| AC-04 | P0 | Sensitive data is masked | Account-like values and raw broker/provider data are absent or masked. |
| AC-05 | P0 | Observation reports are operator-window based | Reports include start/end/runtime chosen by the operator and no hardcoded duration. |
| AC-06 | P0 | Browser Prove can verify the state | Chrome/tunnel evidence confirms dashboard/API status and no public exposure. |

## 5. Go Notes

This unit is not a trading strategy. It is the proof surface that prevents
future sessions from claiming completion without seeing actual service/timer,
broker, AI, intent, and reconciliation evidence.
