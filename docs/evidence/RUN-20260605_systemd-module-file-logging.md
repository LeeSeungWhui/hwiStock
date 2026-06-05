---
schema_version: hwi.evidence/v0
type: runtime_logging_evidence
status: pass
project_root: /data/workspace/My/hwiStock
profile_id: PROFILE-HWISTOCK
created_at_kst: 2026-06-05T15:35:00+09:00
---

# Systemd Module File Logging Evidence

## 1. Verdict

PASS. Active hwiStock user systemd modules now write append-only stdout/stderr
files under:

- `/data/workspace/My/hwiStock/logs/systemd/*.log`
- `/data/workspace/My/hwiStock/logs/systemd/*.err.log`

The `logs/` directory remains git-ignored; runtime logs are not committed.

## 2. Configured Service Logs

| service | stdout log | stderr log |
| --- | --- | --- |
| `hwistock-ai-analysis.service` | `logs/systemd/hwistock-ai-analysis.log` | `logs/systemd/hwistock-ai-analysis.err.log` |
| `hwistock-ai-flash.service` | `logs/systemd/hwistock-ai-flash.log` | `logs/systemd/hwistock-ai-flash.err.log` |
| `hwistock-api.service` | `logs/systemd/hwistock-api.log` | `logs/systemd/hwistock-api.err.log` |
| `hwistock-frontend.service` | `logs/systemd/hwistock-frontend.log` | `logs/systemd/hwistock-frontend.err.log` |
| `hwistock-intel-collector.service` | `logs/systemd/hwistock-intel-collector.log` | `logs/systemd/hwistock-intel-collector.err.log` |
| `hwistock-kis-market-data.service` | `logs/systemd/hwistock-kis-market-data.log` | `logs/systemd/hwistock-kis-market-data.err.log` |
| `hwistock-kis-paper-health.service` | `logs/systemd/hwistock-kis-paper-health.log` | `logs/systemd/hwistock-kis-paper-health.err.log` |
| `hwistock-kis-paper-runner.service` | `logs/systemd/hwistock-kis-paper-runner.log` | `logs/systemd/hwistock-kis-paper-runner.err.log` |
| `hwistock-runner-tick.service` | `logs/systemd/hwistock-runner-tick.log` | `logs/systemd/hwistock-runner-tick.err.log` |

## 3. Runtime Installation Check

The updated service files were installed to `/home/hwi/.config/systemd/user/`,
then `systemctl --user daemon-reload` was run.

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

Observed non-empty stdout/stderr module logs after installation:

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
- This evidence only proves module-level file logging; it does not by itself
  prove external provider, broker, order, or browser Prove readiness.
