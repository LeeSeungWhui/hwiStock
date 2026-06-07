---
schema_version: hwi.evidence/v0
stage: go-check
status: pass
project_root: /data/workspace/My/hwiStock
run_id: RUN-20260607_gpt-pro-local-browser-systemd-hardening
unit_refs:
  - docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md
profile_refs:
  - docs/profiles/PROFILE-HWISTOCK.md
updated_at: 2026-06-07
---

# GPT Pro Local Browser-Use Systemd Hardening Evidence

## Scope

This run hardened the ChatGPT Pro morning-watchlist route:

```text
Codex CLI -> local browser-use / Chrome browser-client -> ChatGPT Pro
  -> strict JSON -> backend publish-morning-watchlist
```

The forbidden routes remain SSH browser-use, reverse socket browser-use,
remote Chrome, CDP fallback, headless Playwright, and DeepSeek substitution for
the GPT Pro leg.

No broker API, order API, credential read, order placement, or repo commit was
performed during this evidence run.

## Failure Findings From 12:40 / 12:45 Attempts

| item | result |
| --- | --- |
| 12:40 scheduled transient run | Failed in about 6 seconds with Codex exit `247`. The event stream recorded the cause: `--dangerously-bypass-hook-trust` was enabled and Codex refused the invocation. |
| 12:45 scheduled transient run | Failed in about 5 seconds with exit `247`, but the failure event file was later overwritten by the foreground retry because the temporary wrapper reused the same `/tmp` paths. Exact root-cause text is therefore not recoverable from the preserved artifacts. |
| foreground retry | Succeeded through GPT Pro, JSON parse validation, and backend publish. Elapsed time: `527` seconds. Artifact: `art_morning_watchlist_20260608_125434_imported`. |

The hardening change therefore focuses on removing the hook-trust flag and
preventing future failure evidence from being overwritten.

## Changes

- Added `ops/gpt_pro_morning_watchlist.sh`.
  - Uses a unique `logs/gpt-pro-morning/<date>/<run-id>/` directory per run.
  - Runs Codex CLI preflight and Chrome browser-client preflight before GPT Pro.
  - Never passes `--dangerously-bypass-hook-trust`.
  - Preserves Codex JSONL events, last message, stderr, raw GPT output,
    response JSON, publish output, and summary JSON.
  - Publishes a backend `morning_watchlist/v0` safe-block when the prompt,
    Codex, browser preflight, GPT output, or validation path fails.
- Added `ops/systemd/user/hwistock-gpt-morning-watchlist.service`.
- Added `ops/systemd/user/hwistock-gpt-morning-watchlist.timer`.
- Updated `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md` code paths.

## Validation

| command / run | result | evidence |
| --- | --- | --- |
| `bash -n ops/gpt_pro_morning_watchlist.sh` | PASS | Shell syntax validated. |
| `systemd-analyze verify --user ops/systemd/user/hwistock-gpt-morning-watchlist.service ops/systemd/user/hwistock-gpt-morning-watchlist.timer` | PASS | Unit/timer syntax validated. |
| systemd smoke-only run `hwistock-gpt-morning-wrapper-smoke` | PASS | `logs/gpt-pro-morning/2026-06-07/hwistock-gpt-pro-morning-smoke-systemd/summary.json` recorded `status=smoke_ok`, `elapsed_seconds=25`; browser preflight returned `{"ok":true,"browser_count":1}`. |
| systemd small GPT Pro E2E run `hwistock-gpt-morning-small-e2e` | PASS | `logs/gpt-pro-morning/2026-06-07/hwistock-gpt-pro-morning-small-e2e-systemd/summary.json` recorded `status=ok`, `elapsed_seconds=278`, `route=codex_cli_local_browser_use`, `reviewer=chatgpt_pro`, `validation_status=accepted`. |

The small E2E run used `HWISTOCK_DATA_DIR=/tmp/hwistock-gpt-wrapper-smoke-data`
so the production `data/` latest artifacts were not overwritten by the smoke
test. Temporary published files were written under:

- `/tmp/hwistock-gpt-wrapper-smoke-data/ai/2026-06-08/morning-watchlist-latest.json`
- `/tmp/hwistock-gpt-wrapper-smoke-data/morning-watchlist/2026-06-08/morning-watchlist-latest.json`
- `/tmp/hwistock-gpt-wrapper-smoke-data/evidence/2026-06-07/morning-watchlist-publish-health.json`

## Current Verdict

PASS for the wrapper/timer hardening and systemd viability:

- Codex CLI works under the user systemd manager.
- `node_repl_http` MCP works under systemd.
- Chrome browser-client/local browser-use preflight works under systemd.
- A real ChatGPT Pro browser leg completed under systemd and produced a valid
  `morning_watchlist/v0` JSON artifact.

Remaining operational note: production `07:15 KST` use still requires a fresh
sanitized prompt file via `HWISTOCK_GPT_PROMPT_PATH` or one of the wrapper's
default prompt locations. If the prompt is missing, the wrapper intentionally
publishes a safe-block instead of silently switching routes.

## Follow-up Hardening: Logs vs Canonical Data

The wrapper now separates execution logs from the canonical artifacts that
Flash/runtime consumers read.

Every run summary includes:

- `run_log_dir`: the `logs/gpt-pro-morning/<date>/<run-id>/` execution
  black-box directory.
- `data_dir`: the data root used for backend publish.
- `is_smoke_data_dir`: true when the data root is not the production
  `data/` directory.
- `canonical_artifact_paths`: expected latest paths under `data_dir` for
  `ai`, `morning-watchlist`, and publish health.
- `published_to_canonical_data`: true only when publish returned
  `accepted`/`safe_block` and the canonical latest files exist.

Status policy:

| condition | wrapper status |
| --- | --- |
| GPT/Codex/browser path fails, safe-block publish succeeds | `safe_block` |
| safe-block publish fails | `safe_block_publish_failed` with nonzero exit |
| GPT response validates but canonical publish fails | `publish_failed` with nonzero exit |
| GPT response validates and canonical publish succeeds | `ok` |

This prevents a run from looking successful merely because a GPT response or
debug log exists under `logs/`.
