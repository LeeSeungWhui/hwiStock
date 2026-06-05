---
schema_version: hwi.evidence/v0
type: runtime_logging_evidence
status: pass_daily_partitioned
project_root: /data/workspace/My/hwiStock
profile_id: PROFILE-HWISTOCK
created_at_kst: 2026-06-05T15:35:00+09:00
---

# Systemd Module Daily File Logging Evidence

## 1. Verdict

PASS. hwiStock systemd modules now write stdout/stderr to date-partitioned log
files under:

- `/data/workspace/My/hwiStock/logs/systemd/YYYY-MM-DD/*.log`
- `/data/workspace/My/hwiStock/logs/systemd/YYYY-MM-DD/*.err.log`

The `logs/` directory remains git-ignored; runtime logs are not committed.

Long-running services are wrapped by `ops/systemd/run_with_daily_logs.py`, which
reopens output files when the KST date changes. This avoids the common failure
mode where a service started yesterday keeps writing into yesterday's file after
midnight.

## 2. Configured Service Logs

| service | stdout log | stderr log |
| --- | --- | --- |
| `hwistock-ai-analysis.service` | `logs/systemd/YYYY-MM-DD/hwistock-ai-analysis.log` | `logs/systemd/YYYY-MM-DD/hwistock-ai-analysis.err.log` |
| `hwistock-ai-flash.service` | `logs/systemd/YYYY-MM-DD/hwistock-ai-flash.log` | `logs/systemd/YYYY-MM-DD/hwistock-ai-flash.err.log` |
| `hwistock-api.service` | `logs/systemd/YYYY-MM-DD/hwistock-api.log` | `logs/systemd/YYYY-MM-DD/hwistock-api.err.log` |
| `hwistock-frontend.service` | `logs/systemd/YYYY-MM-DD/hwistock-frontend.log` | `logs/systemd/YYYY-MM-DD/hwistock-frontend.err.log` |
| `hwistock-intel-collector.service` | `logs/systemd/YYYY-MM-DD/hwistock-intel-collector.log` | `logs/systemd/YYYY-MM-DD/hwistock-intel-collector.err.log` |
| `hwistock-kis-market-data.service` | `logs/systemd/YYYY-MM-DD/hwistock-kis-market-data.log` | `logs/systemd/YYYY-MM-DD/hwistock-kis-market-data.err.log` |
| `hwistock-kis-paper-health.service` | `logs/systemd/YYYY-MM-DD/hwistock-kis-paper-health.log` | `logs/systemd/YYYY-MM-DD/hwistock-kis-paper-health.err.log` |
| `hwistock-kis-paper-runner.service` | `logs/systemd/YYYY-MM-DD/hwistock-kis-paper-runner.log` | `logs/systemd/YYYY-MM-DD/hwistock-kis-paper-runner.err.log` |
| `hwistock-runner-tick.service` | `logs/systemd/YYYY-MM-DD/hwistock-runner-tick.log` | `logs/systemd/YYYY-MM-DD/hwistock-runner-tick.err.log` |

## 3. Runtime Installation Check

The daily-log wrapper service files were installed to
`/home/hwi/.config/systemd/user/`, then `systemctl --user daemon-reload` was
run.

After reload:

- `hwistock-api.service` and `hwistock-frontend.service` were restarted and
  remained active/running.
- `GET /api/v1/hwistock/runner/operator-snapshot` returned 200 from the local
  API on `127.0.0.1:5001`.
- `GET /dashboard` on `127.0.0.1:5000` safely resolved to the local login page
  with status 200.
- One-shot/timer services were manually started once to create their module log
  files.
- Active timers remained loaded/waiting:
  - `hwistock-ai-analysis.timer`
  - `hwistock-ai-flash.timer`
  - `hwistock-intel-collector.timer`
  - `hwistock-kis-market-data.timer`
  - `hwistock-kis-paper-health.timer`
  - `hwistock-kis-paper-runner.timer`
  - `hwistock-runner-tick.timer`

## 4. Observed Log Files

Observed non-empty stdout/stderr module logs after installation under the
current KST date directory:

- `hwistock-ai-analysis.log`
- `hwistock-ai-flash.log`
- `hwistock-api.err.log`
- `hwistock-frontend.log`
- `hwistock-frontend.err.log`
- `hwistock-intel-collector.log`
- `hwistock-kis-market-data.log`
- `hwistock-kis-paper-health.log`
- `hwistock-kis-paper-runner.log`
- `hwistock-runner-tick.log`

Empty `.err.log` files are acceptable when a service has not emitted stderr.

## 5. Boundary

- No secrets or raw env values were printed.
- Runtime logs and data artifacts remain outside git tracking.
- This evidence only proves module-level daily file logging; it does not by
  itself prove external provider, broker, order, or browser Prove readiness.

## 6. Validation

| check | result |
| --- | --- |
| `python3 -m py_compile ops/systemd/run_with_daily_logs.py` | PASS |
| daily wrapper smoke under `/tmp/hwistock-daily-log-smoke` | PASS: `2026-06-05/smoke.log` and `2026-06-05/smoke.err.log` were created |
| `systemd-analyze --user verify ...` for active user services | PASS |
| `systemd-analyze verify` for system service templates | PASS |
| install to `/home/hwi/.config/systemd/user/` + `systemctl --user daemon-reload` | PASS |
| restart `hwistock-api.service` and `hwistock-frontend.service` | PASS: both active/running |
| one-shot starts for runner, KIS, AI, and intelligence services | PASS: current-date log files created |
| local operator snapshot API | PASS: HTTP 200 |
| local dashboard route | PASS: HTTP 200 ending at `/login` |
