---
schema_version: hwi.run-evidence/v0
stage: go-check
status: pass
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_refs:
  - docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md
  - docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md
created_at_kst: 2026-06-07T11:33:00+09:00
---

# RUN 2026-06-07 - Monday GPT Morning Watchlist Provisional Guard

## Objective

The `2026-06-07 07:15 KST` Sunday rehearsal window was already missed by the
time of this run. The remediation is to allow a late Sunday rehearsal artifact
as a provisional/candidate artifact for the Monday `2026-06-08` first Flash
bucket without silently treating it as a final Monday preopen artifact.

## Scope

- No ChatGPT Pro browser session was opened from this server-side Codex session.
- SSH browser-use was not used.
- No broker API, KIS order endpoint, live order, paper order, or secret-bearing
  config was read or called.
- The approved route remains:

```text
local Codex CLI -> local browser-use -> user's logged-in local Chrome -> ChatGPT Pro
```

## Changes

- `backend/lib/ai_orchestration.py`
  - First Flash still safe-blocks when the morning watchlist artifact is missing.
  - If a correct-target Sunday rehearsal/candidate artifact exists, Flash keeps
    it usable but marks the trade document as provisional with refresh-required
    warning metadata.
- `backend/tests/test_ai_orchestration_layer.py`
  - Added coverage that Sunday late rehearsal and stale generated-date metadata
    do not force `NO_TRADE`, while remaining visible as provisional warnings.
- `docs/set/READY-SET-GPT-PRO-MORNING-PROMPT-20260606_hwistock.md`
  - Added explicit late Sunday rehearsal metadata for
    `target_trade_date_kst=2026-06-08`.
- `docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md`
  - Clarified that Sunday rehearsal/candidate artifacts cannot be silently
    relabeled as final, but also do not by themselves force `NO_TRADE`.
- `docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md`
  - Added QA-013A stale-watchlist/provisional-watchlist P0 row.

## Validation

All commands were run from `/data/workspace/My/hwiStock`.

| Check | Result |
| --- | --- |
| `source ./env.sh && python3 -m pytest backend/tests/test_ai_orchestration_layer.py -q` | PASS - 22 passed, 6 subtests |
| `source ./env.sh && python3 -m py_compile backend/lib/ai_orchestration.py backend/tests/test_ai_orchestration_layer.py` | PASS |
| `source ./env.sh && python3 -m pytest backend/tests/test_operational_go_check_pipeline.py backend/tests/test_kis_paper_continuous_runner.py -q` | PASS - 46 passed |
| `source ./env.sh && python3 -m py_compile $(find backend scripts -name '*.py' -not -path '*/__pycache__/*')` | PASS |
| `systemd-analyze --user verify ops/systemd/user/hwistock-*.service ops/systemd/user/hwistock-*.timer` | PASS |
| `git diff --check` | PASS |
| `source ./env.sh && python3 scripts/validate_runtime_contracts.py --schema docs/contracts/hwistock-runtime-contracts.schema.json --valid docs/contracts/fixtures/runtime-contract-valid.json --invalid docs/contracts/fixtures/runtime-contract-invalid.json` | PASS - runtime_contract_validation=PASS, valid_artifacts=12, invalid_cases=28, schema_count=12 |
| LF scan for `backend`, `ops/systemd`, `docs`, `scripts`, `.gitattributes` | PASS - line_ending_issues=0 |

## Result

PASS. A late Sunday rehearsal can still be used to verify the local GPT Pro path
and can remain available to Monday Flash as a correct-target provisional
artifact. It cannot be silently mistaken for the Monday final preopen artifact.
The first Flash document records `morning_watchlist_status=provisional`,
`morning_watchlist_refresh_required=true`, and named warning reasons, while the
existing deterministic gates still decide whether a paper action may proceed.
