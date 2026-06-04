---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-002
type: unit
domain: ops
name: Home-server paper runner
status: set
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
work_class: quality_only
completeness:
  status: set
  audit_ref: docs/qa/QA-HWISTOCK-UNIT-002_home-server-paper-runner.md
owner: hwi
updated_at: 2026-06-02
last_verified_at:
source_snapshot:
  input_digest: "홈서버에서 프로그램을 24시간 돌리는 운영 목표"
  legacy_doc: none
  legacy_status: greenfield
source_inputs:
  - kind: user_prompt
    path_or_url: "프로그램을 홈서버에서 24시간 돌린다"
    confidence: high
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-001
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  include:
    - backend/
    - ops/systemd/
  exclude:
    - "**/*credentials*"
    - "**/*.env"
entrypoints: []
interfaces: []
verification:
  stage_skill_routes:
    ready:
      - hwi-work-harness
    set:
      - hwi-work-harness
    go:
      - hwi-work-harness
      - delegation-guard
    check:
      - hwi-work-harness
    prove:
      - hwi-work-harness
  required_gates:
    - service-lifecycle-smoke
    - risk-contract-check
    - no-order-dry-run-smoke
    - market-calendar-smoke
  suggested_gates:
    - paper-trading-smoke
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-002_home-server-paper-runner.md
risk:
  tier: 2
  reasons:
    - 24-hour automation can create operational risk even when paper-only.
    - Future live-trading paths must stay disabled by default.
last_set:
  status: set
  report_id: RUN-20260602-unit-002-home-server-paper-runner-set
  context_fingerprint:
evidence_refs:
  - run_id: RUN-20260602-broker-selection-kis
    status: draft
  - run_id: RUN-20260602-market-session-source-check
    status: draft
  - run_id: RUN-20260602-broker-candidate-kb-blocked
    status: draft
  - run_id: RUN-20260602-unit-002-home-server-paper-runner-set
    status: pass_with_followups
links:
  - HWISTOCK-MOD-001
  - docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md
---

# Home-Server Paper Runner

## 1. Goal

Define the first runtime target: an independently restartable program/service
that can run on the home server 24 hours a day in paper/sandbox mode, without
requiring a Codex session to stay alive. The service may run 24 hours, but its
active trading loop must use the simple KRX/NXT routing policy: KRX from
09:00-15:00 KST, NXT from 08:00-09:00 and 15:00-20:00 KST, and no trading
outside 08:00-20:00 KST. Separately, the market-intelligence ingestion branch may
run 24 hours. hwiStock will not use an internal fake broker adapter for the
first order/fill path. Before explicit KIS paper approval, the runner may only
record no-order dry-run decisions. The first broker-backed order/fill path is
the approved KIS KRX paper/mock-investment adapter. The official paper/mock
starting budget candidate is 10,000,000 KRW.

The first one-week evidence runner uses `systemd`. Manual shell, tmux, or screen
sessions are allowed only for early experiments and do not count as official
one-week evidence. Docker Compose is deferred until a later unit explicitly
chooses containerized operation.

## 2. Baseline Module Contract

This unit implements the runtime side of `HWISTOCK-MOD-001` safety expectations:
paper-only operation, health checks, audit logging, restartability, and kill
switch behavior.

### Module Change

None. This unit uses the existing safety-core module contract.

## 3. Included Scope

- Runtime process shape for a home server.
- `systemd` service lifecycle for the one-week paper/sandbox evidence path.
- Paper/sandbox-only default mode.
- No-order dry-run behavior before KIS paper approval: candidate/risk/order
  intent records only, with no simulated fills or fake balances.
- Approved KIS KRX paper/mock-investment adapter boundary for future orders,
  fills, balances, positions, rejects, and reconciliation.
- KRX/NXT simple time-window routing contract.
- Separation between 24-hour information ingestion and market-session trading.
- Off-hours idle/maintenance/reporting behavior.
- Start/stop/restart expectations.
- Health check expectations.
- Audit log categories.
- Kill switch behavior.
- Daily paper-run summary evidence.
- Requirements for the future one-week paper/sandbox test period.
- Local-only API/dashboard binding policy for service health surfaces.
- Market calendar source hierarchy, local cached calendar behavior, local alert
  channel, and one-week pass criteria from
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`.

## 4. Excluded Scope

- Live brokerage order placement.
- Broker credential storage.
- KIS/external broker network calls before the KIS API verification unit.
- Official paper/mock-investment broker API calls until explicitly approved by
  the KIS verification/integration unit.
- Final strategy implementation.
- Real-money trading.
- Production deployment beyond the home server.

## 5. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | Runner is independent from Codex sessions | Service/process can run after Codex exits | process/service evidence | QA-001 |
| AC-02 | P0 | Default mode is paper/sandbox only | Config defaults forbid live orders | config/log review | QA-002 |
| AC-03 | P0 | Kill switch blocks dry-run and future order routing | Kill switch state is visible and enforced | log/health output | QA-003 |
| AC-04 | P1 | Health state is observable | Health check reports loop/data/risk/order-gate state | health output | QA-004 |
| AC-05 | P1 | Audit logs are separated by event type | signal/decision/risk/order/error logs are inspectable | log file review | QA-005 |
| AC-06 | P1 | One-week paper test evidence can be produced | Daily summary format is defined | evidence summary | QA-006 |
| AC-07 | P0 | Runner is market-session aware | Out-of-session mode does not run active trading/order loops | calendar/health/log output | QA-007 |
| AC-08 | P0 | Information ingestion branch is separate | 24h crawler/news/disclosure branch cannot place orders | config/log review | QA-008 |
| AC-09 | P0 | Venue routing is simple and deterministic | 09:00-15:00 routes KRX; 08:00-09:00 and 15:00-20:00 route NXT | calendar/route test | QA-009 |
| AC-10 | P0 | Pre-approval execution is dry-run only | Approved order intents are recorded without broker calls, simulated fills, or fake balances before KIS paper approval | adapter/log review | QA-010 |
| AC-11 | P0 | KIS/external broker and broker paper/mock network use requires approval | KIS/external broker endpoints, paper/mock/demo/testbed endpoints, credentials, and tokens are absent from runner config until an approved KIS unit enables them | config/network review | QA-011 |
| AC-12 | P0 | Paper budget is separated from live capital | Official paper/mock budget candidate is 10,000,000 KRW while live baseline remains 2,000,000 KRW cash | config/doc review | QA-012 |
| AC-13 | P0 | Official evidence runner uses systemd | Planned service files and health checks are under `ops/systemd/`; tmux/screen/manual shells do not count for the one-week evidence run | service config review | QA-013 |
| AC-14 | P0 | Missing market-data source does not create unsafe trading | Data-dependent trading loops report `source_unconfigured`/idle and cannot route orders | health/config review | QA-014 |
| AC-15 | P0 | Health/API surfaces bind local-only by default | Runner/API/dashboard health surfaces bind `127.0.0.1` unless a future Set contract approves authenticated exposure | config review | QA-015 |
| AC-16 | P0 | Calendar source hierarchy is selected | Runtime uses local cached calendar generated from KRX/NXT official sources; KIS holiday lookup is later-approved broker cross-check only | config/doc review | QA-016 |
| AC-17 | P0 | Alert channel is local-only first pass | Alerts write systemd journal, `data/alerts`, dashboard audit panel when implemented, and daily close report; no external delivery | config/log review | QA-017 |
| AC-18 | P0 | One-week pass criteria are explicit | Minimum 7 calendar days, at least 5 valid market-open days, P0 safety/evidence criteria, and no profit threshold are documented | evidence contract review | QA-018 |

## 6. Implementation Notes

Selected process manager:

- `systemd` is the official runner/process-manager path for one-week
  paper/sandbox evidence.
- Planned service config root: `ops/systemd/`.
- Planned services:
  - `hwistock-api.service`: FastAPI health/status/read-only dashboard API,
    local-only bind.
  - `hwistock-runner.service`: 24-hour scheduler/worker for market
    intelligence, AI orchestration jobs when enabled, no-order dry-run records,
    and later approved KIS KRX paper jobs.
- Planned target/dependency behavior:
  - PostgreSQL must be available before data-dependent loops become active.
  - If market data, calendar, AI, or broker adapters are not configured, the
    related loop reports an explicit `*_unconfigured` state and stays idle or
    dry-run only.
  - Missing market-data configuration must not create fake fills, fake balances,
    or order routing.
- Planned market-calendar behavior:
  - Use `config/market-calendar/krx-nxt-trading-days.json` as the runtime cache.
  - Cache must be generated from KRX official trading-days/holidays and notices
    plus NXT official session references.
  - Missing, expired, or out-of-range calendar cache forces trading/order loops
    to idle with `calendar_unconfigured` or `calendar_stale`.
  - KIS `국내휴장일조회` is a later-approved broker-side cross-check only; it is
    paper-unsupported and not required for no-order dry-run.
- Planned alert behavior:
  - First-pass alerts are local-only: systemd journal,
    `data/alerts/YYYY-MM-DD/alerts.jsonl`, dashboard audit/error panel when
    implemented, and `daily-close-2000.md`.
  - External alert delivery is deferred.
- Docker Compose is deferred.
- tmux/screen/manual shell is acceptable only for early manual experiments and
  cannot count toward the official one-week evidence run.

Broker direction is KIS because KB Securities is blocked as a practical personal
API candidate. This unit should define the no-order dry-run runner behavior
first so pre-approval evidence can be produced without credentials, KIS
paper/mock investment APIs, or broker network calls. A later KIS paper unit can
approve official KIS KRX paper/mock API use for the one-week evidence run.

## 7. Open Questions

Closed by Set:

- Systemd service root, local-only health/API bind, no-order dry-run boundary,
  and KIS KRX paper adapter boundary are selected by this unit.
- No-order dry-run and KIS paper state contracts are selected by
  `HWISTOCK-UNIT-006`.
- Official/broker calendar source, local alert channel, and one-week pass
  criteria are selected by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`.

Remaining follow-up:

- Exact systemd service file names and environment-file paths are implementation
  details, but must follow this unit and the profile.
- Which market data source can run continuously on the home server?
