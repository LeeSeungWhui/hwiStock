---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-002-go-check
stage: check
unit_id: HWISTOCK-UNIT-002
status: pass
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-002_home-server-paper-runner.md
module_refs:
  - docs/modules/HWISTOCK-MOD-001_trading-safety-core.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-002_home-server-paper-runner.md
preflight_ref: docs/evidence/RUN-20260604_unit-002-go-preflight.md
ready_set_completion_ref: docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
created_at: 2026-06-04
---

# UNIT-002 Go-Check Evidence — 2026-06-04

## 1. Verdict

PASS for the UNIT-002 bounded skeleton scope.

The current tree now contains a local-only home-server paper runner skeleton,
read-only runner status API, no-order intent metadata, KRX/NXT routing preview,
calendar/source idle behavior, local alert/audit metadata, focused tests, and
`systemd` service templates.

This verdict does **not** authorize broker/KIS/API calls, AI provider calls,
paper orders, live orders, real systemd installation/execution, public/LAN
exposure, credential storage, or a one-week paper evidence claim.

## 2. Implemented Files

- `backend/run.py`
- `backend/run.sh`
- `backend/service/HwiStockRunnerService.py`
- `backend/router/HwiStockRunnerRouter.py`
- `backend/tests/test_hwistock_runner.py`
- `ops/systemd/hwistock-api.service`
- `ops/systemd/hwistock-runner.service`

## 3. Go Changes

- Replaced imported MyWebTemplate public bind defaults with loopback-only
  resolution. Empty, wildcard, LAN, public, and non-loopback hostname values
  resolve to `127.0.0.1`; `127.0.0.1`, `localhost`, and `::1` remain allowed.
- Added read-only runner API routes under `/api/v1/hwistock/runner`:
  - `GET /status`
  - `GET /route-preview`
  - `GET /daily-close-template`
  - `POST /no-order-intent-record`
- Added a no-network/no-order runner service skeleton with:
  - paper/sandbox mode defaults;
  - `liveOrdersEnabled=false`;
  - `brokerCallsEnabled=false`;
  - kill-switch visibility and order-gate blocking;
  - KRX/NXT/idle routing for 08:30, 09:30, 15:30, and 20:30 KST;
  - missing/stale calendar idle states;
  - source-unconfigured idle state;
  - local alert metadata;
  - explicit audit categories for signal, decision, risk reject,
    no-order intent, error, calendar, kill switch, lifecycle, and status;
  - one-week evidence template metadata.
- Added `--once` runner entrypoint that emits local runner status/audit JSON and
  exits without broker, network, DB, order, fake-fill, fake-balance, or fake-PnL
  behavior.
- Added `systemd` templates:
  - API service binds `127.0.0.1`.
  - Runner service executes the skeleton `--once` tick loop rather than a pure
    sleep placeholder.
- Added focused backend tests for all current UNIT-002 Go smoke requirements.

## 4. Check Review Findings

| finding_id | priority | status | evidence |
| --- | --- | --- | --- |
| F-001 | P0 | closed | GPT-5.4 read-only audit found non-loopback bind bypass in `run.py`, `run.sh`, and runner service; patch now routes bind resolution through loopback-only helper. |
| F-002 | P1 | closed | GPT-5.4 read-only audit found `hwistock-runner.service` was a pure sleep placeholder; patch now runs `backend/service/HwiStockRunnerService.py --once` inside the runner loop. |
| new | none | pass | GPT-5.4 re-audit reported no new P0/P1/P2 findings in the reviewed UNIT-002 skeleton scope. |

## 5. QA Row Results

These results are for the Go skeleton scope only. Host-level systemd
installation/execution and one-week paper evidence remain future Prove/ops
work, not part of this Go-Check.

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass_for_go_scope | `hwistock-runner.service` now launches the skeleton `--once` runner loop; direct `--once` smoke exits 0 with local status JSON. Real installed systemd execution was not run. |
| QA-002 | pass | Runner status reports `mode=paper_sandbox`, `liveOrdersEnabled=false`, and `brokerCallsEnabled=false`; focused tests pass. |
| QA-003 | pass | Kill switch blocks no-order intent recording and sets `blocked_kill_switch`; focused tests pass. |
| QA-004 | pass | `/status` service payload exposes routing, calendar, market data, order gate, kill switch, budget, alerts, audit, and readiness fields. |
| QA-005 | pass | `auditLog` metadata exposes distinguishable local audit categories for signal, decision, risk reject, dry-run order intent, error, calendar, kill switch, system lifecycle, and system status. |
| QA-006 | pass | `daily_close_template()` exposes `daily-close-2000.md` sections for runtime duration, mode, failures, dry-run intents, risk rejects, kill-switch events, calendar state, and alert summary. |
| QA-007 | pass | 20:30 KST routes to `idle`; off-session status blocks order gate. |
| QA-008 | pass | Runner branch metadata separates market intelligence from trading, and both report `canPlaceOrders=false`. |
| QA-009 | pass | Focused tests cover 08:30 -> NXT, 09:30 -> KRX, 15:30 -> NXT, 20:30 -> idle. |
| QA-010 | pass | No-order intent records `noBrokerCall=true`, `fakeFillCreated=false`, `fakeBalanceCreated=false`, and `fakePnlCreated=false`. |
| QA-011 | pass_for_reviewed_scope | Reviewed UNIT-002 files contain no broker/KIS network implementation or credentials. Broker/KIS/API calls were not run. |
| QA-012 | pass | Status metadata keeps paper mock candidate budget at 10,000,000 KRW and live baseline at 2,000,000 KRW. |
| QA-013 | pass_for_go_scope | `ops/systemd/hwistock-api.service` and `ops/systemd/hwistock-runner.service` exist and use the project root plus `/home/hwi/.config/hwistock/hwistock.env`; installed service execution is deferred. |
| QA-014 | pass | Missing market-data source reports `source_unconfigured` and blocks order gate. |
| QA-015 | pass | `run.py`, `run.sh`, service helper, and API systemd template enforce loopback-only bind by default. |
| QA-016 | pass | Missing or stale local calendar cache reports `calendar_unconfigured` or `calendar_stale` and blocks order gate; KIS holiday lookup remains deferred. |
| QA-017 | pass | Alert metadata is local-only: systemd journal, `data/alerts`, future dashboard audit panel, and daily close report; no external delivery. |
| QA-018 | pass | One-week gate metadata requires 7 calendar days, at least 5 valid market-open days, P0 safety/evidence criteria, and no profit threshold. |

## 6. Local Validation

Executed locally from `/data/workspace/My/hwiStock` on 2026-06-04:

1. `source ./env.sh >/dev/null && cd backend && python -m pytest tests/test_hwistock_runner.py -q`
   - Result: PASS, `32 passed`.

2. `source ./env.sh >/dev/null && python -m py_compile backend/run.py backend/service/HwiStockRunnerService.py backend/tests/test_hwistock_runner.py`
   - Result: PASS.

3. `source ./env.sh >/dev/null && python backend/service/HwiStockRunnerService.py --once`
   - Result: PASS.
   - Observed JSON summary: `event=runner_once`, `mode=paper_sandbox`,
     `bindHostDefault=127.0.0.1`, `brokerCallsEnabled=false`,
     `liveOrdersEnabled=false`, audit policy
     `AC-05_QA-005_category_separation`.

4. Direct router function smoke from `backend/`
   - Result: PASS before the P0/P1 fix and still covered by unchanged router
     code path.
   - Covered `status`, `route-preview`, `daily-close-template`, and
     `no-order-intent-record` JSON responses.

5. `source ./env.sh >/dev/null && git diff --check`
   - Result: PASS.

6. Static grep/text checks
   - Result: PASS.
   - Confirmed local bind strings, no-order flags, audit categories,
     `--once` systemd runner entrypoint, and no `time.sleep` runner placeholder.

No broker/KIS/API, AI provider, server, database, browser, deploy, SSH, real
systemd execution, credential, paper order, live order, fake fill, fake balance,
or fake PnL action was run for this Go-Check.

## 7. Worker Output Acceptance

### Attempt 1 — quarantined

- Gate id: `HWISTOCK-UNIT002-GO-CHECK-CURSOR-20260604`.
- Route/model: `cursor-sdk-local` / `composer-2.5`.
- Contract: `/tmp/hwistock-unit002-go-cursor-20260604/contract.md`.
- Transcript: `/tmp/hwistock-unit002-go-cursor-20260604/transcript.jsonl`.
- Observed result: implementation files were produced and sentinel text existed
  inside the transcript result.
- Failure: wrapper classified the run as `scope_violation` because Cursor
  runtime produced zero-byte `logs/20260604_*.log` files outside the initial
  allowed write set.
- Acceptance state: quarantined; not used as accepted worker output.

### Attempt 2 — accepted current-tree audit

- Gate id: `HWISTOCK-UNIT002-GO-CHECK-CURSOR-20260604-RERUN1`.
- Route/model: `cursor-sdk-local` / `composer-2.5`.
- Contract: `/tmp/hwistock-unit002-go-cursor-20260604/contract-rerun1.md`.
- Transcript: `/tmp/hwistock-unit002-go-cursor-20260604/transcript-rerun1.jsonl`.
- Observed result: `WORKER_RESULT: DONE`, `CHANGED_FILES: none`, focused tests
  reported `18 passed`.
- Acceptance state: accepted for the initial skeleton current-tree audit.

### Attempt 3 — quarantined audit-category patch

- Gate id: `HWISTOCK-UNIT002-GO-CHECK-CURSOR-20260604-AUDIT-GAP`.
- Route/model: `cursor-sdk-local` / `composer-2.5`.
- Contract: `/tmp/hwistock-unit002-go-cursor-20260604/contract-audit-gap.md`.
- Transcript: `/tmp/hwistock-unit002-go-cursor-20260604/transcript-audit-gap.jsonl`.
- Observed result: audit metadata/test patch was made.
- Failure: wrapper classified the run as `incomplete_worker_result` because the
  assistant stream contained prose before the final `WORKER_RESULT` sentinel.
- Acceptance state: quarantined; later verified by local tests and external
  read-only re-audit.

### Attempt 4 — quarantined audit-category rerun

- Gate id: `HWISTOCK-UNIT002-GO-CHECK-CURSOR-20260604-AUDIT-GAP-RERUN1`.
- Route/model: `cursor-sdk-local` / `composer-2.5`.
- Contract:
  `/tmp/hwistock-unit002-go-cursor-20260604/contract-audit-gap-rerun1.md`.
- Transcript:
  `/tmp/hwistock-unit002-go-cursor-20260604/transcript-audit-gap-rerun1.jsonl`.
- Observed result: no implementation changes; focused tests reported
  `21 passed`.
- Failure: wrapper again classified the run as `incomplete_worker_result` due to
  streamed prose before sentinel even though the final result text began with
  `WORKER_RESULT`.
- Acceptance state: quarantined.

### Attempt 5 — blocked review worker contract

- Gate id:
  `HWISTOCK-UNIT002-GO-CHECK-GPT54-READONLY-AUDIT-20260604`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Failure: orchestrator packaged an incomplete review-worker contract missing
  `ALLOWED_WRITES` and `ABORT_CONDITIONS`.
- Worker result: `WORKER_RESULT: BLOCKED`, `READ_FILES: none`,
  `VALIDATION: not_run`.
- Acceptance state: blocked, no repo read, no output used.

### Attempt 6 — rejected review

- Gate id:
  `HWISTOCK-UNIT002-GO-CHECK-GPT54-READONLY-AUDIT-20260604-RERUN1`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Worker result: `WORKER_RESULT: DONE`.
- Finding: rejected current files due to:
  - P0 non-loopback bind bypass;
  - P1 systemd runner pure sleep placeholder.
- Acceptance state: accepted as read-only review; verdict required fixes before
  Go-Check PASS.

### Attempt 7 — quarantined P0/P1 patch

- Gate id: `HWISTOCK-UNIT002-GO-CHECK-CURSOR-20260604-P0P1-FIX`.
- Route/model: `cursor-sdk-local` / `composer-2.5`.
- Contract: `/tmp/hwistock-unit002-go-cursor-20260604/contract-p0p1-fix.md`.
- Transcript: `/tmp/hwistock-unit002-go-cursor-20260604/transcript-p0p1-fix.jsonl`.
- Observed result: P0/P1 patch was made and the final result reported
  `32 passed`, `py_compile` pass, `--once` pass, and `git diff --check` pass.
- Failure: wrapper classified the run as `incomplete_worker_result` because the
  assistant stream contained prose before the final sentinel.
- Acceptance state: quarantined as worker output; current tree was accepted only
  after independent local validation plus GPT-5.4 read-only re-audit.

### Attempt 8 — accepted closure review

- Gate id:
  `HWISTOCK-UNIT002-GO-CHECK-GPT54-READONLY-REAUDIT-20260604`.
- Route/model: `codex multi-agent` / `gpt-5.4`.
- Worker result: `WORKER_RESULT: DONE`.
- Verdict: previous P0/P1 findings closed and no new P0/P1/P2 findings in the
  reviewed UNIT-002 skeleton scope.
- Acceptance state: accepted as Check closure review.

## 8. Remaining Boundaries

- Real host `systemd` installation/start/restart/status evidence is not run.
- One-week paper/sandbox evidence is not started and not claimed.
- Broker/KIS paper/mock integration remains approval-gated by later KIS/order
  units.
- Dashboard UI remains out of this UNIT-002 row.
- Installed environment files under `/home/hwi/.config/hwistock/` were not read.
