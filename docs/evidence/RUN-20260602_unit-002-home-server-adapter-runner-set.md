---
schema_version: hwi.evidence/v0
id: RUN-20260602-unit-002-home-server-adapter-runner-set
type: evidence
name: Home-server broker-adapter runner Set pass
stage: set
environment: docs_only
status: pass_with_followups
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
implementation_ready: false
---

# Home-Server Broker-Adapter Runner Set Pass

## 1. Scope

This docs-only Set pass closes the first home-server runner process and access
policy for hwiStock.

## 2. Decisions

- The official one-week adapter-backed evidence runner uses `systemd`.
- Planned systemd config root: `ops/systemd/`.
- Planned service split:
  - `hwistock-api.service`: FastAPI health/status/read-only dashboard API,
    local-only bind.
  - `hwistock-runner.service`: 24-hour scheduler/worker for ingestion,
    AI-orchestration jobs when enabled, no-order dry-run, and later approved KIS
    KRX adapter jobs.
- tmux/screen/manual shell sessions are allowed only for early experiments and
  do not count as official one-week evidence.
- Docker Compose is deferred.
- Missing market data, calendar, AI, or broker adapters must report explicit
  `*_unconfigured` state and remain idle or no-order dry-run only.
- Calendar source hierarchy, local alert channel, and one-week adapter pass
  criteria are closed by
  `docs/evidence/RUN-20260602_calendar-alert-operation-gate-set.md`.
- Health/API/dashboard surfaces bind `127.0.0.1` by default.
- LAN/public exposure requires a later authenticated Set contract.

## 3. Evidence

- `docs/units/HWISTOCK-UNIT-002_home-server-adapter-runner.md` is marked `set` and
  records systemd, source-unconfigured, local-only, and no-order dry-run
  contracts.
- `docs/qa/QA-HWISTOCK-UNIT-002_home-server-adapter-runner.md` is marked `set` and
  adds QA rows for systemd lifecycle, unconfigured-source idle behavior, and
  local-only binding.
- `docs/profiles/PROFILE-HWISTOCK.md`, `AGENTS.md`, `docs/index.md`, and
  `docs/evidence/RUN-20260602_ready-set-architecture.md` were updated to reflect
  systemd/local-only decisions.

## 4. Boundaries

- No service files, source-code folders, broker API calls, AI API calls, database
  calls, or network calls were created or run.
- No order placement, broker order, simulated fill, fake balance, or PnL claim was
  created.
- Trading-grade market-data source remains a future Set input. Calendar source,
  alert channel, and one-week pass criteria are closed by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`.

## 5. Verdict

UNIT-002 Set: PASS WITH FOLLOW-UPS.

Implementation readiness: BLOCKED until Ready-Set completion gate and remaining
bundle items are closed.
