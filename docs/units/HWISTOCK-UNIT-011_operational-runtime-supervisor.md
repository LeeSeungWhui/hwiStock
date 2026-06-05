---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-011
type: unit
domain: backend_ops
name: Operational runtime supervisor
status: go_check_passed
implementation_status: go_check_passed_post_pro_runtime_entrypoint
post_pro_reinforcement_status: go_check_passed
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-05
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-009
  - HWISTOCK-MOD-008
  - HWISTOCK-MOD-007
code_paths:
  include:
    - ops/systemd/user/*.service
    - ops/systemd/user/*.timer
    - ops/tunnel/*
    - backend/service/HwiStockRunnerService.py
    - backend/router/HwiStockRunnerRouter.py
  exclude:
    - "**/*.env"
    - backend/config.ini
    - frontend-web/config.ini
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-011_operational-runtime-supervisor.md
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-operational-automated-trading-program.md
  - docs/evidence/RUN-20260605_unit-011-runtime-start-go.md
  - docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md
---

# Operational Runtime Supervisor

> Post-Pro corrective note (2026-06-05): this unit must harden or split the
> backend service-managed runtime entrypoint so development `reload=True`
> behavior cannot be counted as operational readiness.
> Corrective Go-Check passed in
> `docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md`.

## 1. Goal

Make hwiStock installable and restartable as a local-only home-server runtime
instead of a Codex/manual-shell program.

This unit prepares the service manager layer for the trading program. It may
install/enable/start user systemd units only during Go/Prove after the preflight
confirms the allowed scope. It must not place KIS broker orders by itself.

## 2. Included Scope

- Normalize user systemd units for:
  - `hwistock-api.service`
  - `hwistock-frontend.service`
  - `hwistock-intel-collector.service` / `.timer`
  - `hwistock-ai-analysis.service` / `.timer`
  - `hwistock-runner-tick.service` / `.timer`
  - `hwistock-kis-paper-health.service` / `.timer`
  - `hwistock-kis-paper-runner.service` / `.timer`
- Provide an install/sync procedure that copies or links repo unit files into
  the user systemd unit directory without exposing secrets.
- Run `daemon-reload`, enable/start selected non-order units, and inspect status
  when the Go scope authorizes side effects.
- Keep API/frontend loopback-only: dashboard `127.0.0.1:5000`, API
  `127.0.0.1:5001`.
- Record service/timer health evidence and restart behavior.
- Ensure manual shell/tmux sessions are not treated as official long-run
  evidence.

## 3. Excluded Scope

- KIS broker order placement.
- AI provider cost/model changes.
- Strategy parameter changes.
- Public/LAN binding.
- Credential creation or printing.
- Account-affecting broker operations.

## 4. Acceptance Criteria

| ac_id | priority | criterion | observable_result |
| --- | --- | --- | --- |
| AC-01 | P0 | Runtime is service-managed | Services/timers can be installed and listed through user systemd. |
| AC-02 | P0 | Local-only bind is preserved | API/frontend units bind only to `127.0.0.1`. |
| AC-03 | P0 | Side-effect scope is explicit | KIS broker adapter runner is not started unless the current Go/Prove scope authorizes broker-adapter network operation. |
| AC-04 | P0 | Restart is safe | Restarting units does not duplicate order intents or broker orders. |
| AC-05 | P0 | Evidence is durable | Status, enabled-state, latest tick paths, and failures are written to docs/runtime evidence without secrets. |
| AC-06 | P0 | Calendar/risk blocks are visible | `blocked_calendar_unconfigured`, kill switch, source-stale, and off-session states appear as safe blocks, not crashes. |

## 5. Go Notes

The first Go pass should install/start non-order services first, then leave KIS
broker order runner start for UNIT-014 or a Prove pass that explicitly scopes
broker-adapter operations. This prevents service activation from silently becoming
order placement.
