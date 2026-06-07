---
schema_version: hwi.run-evidence/v0
stage: go-check
status: pass
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_refs:
  - docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md
  - docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md
created_at_kst: 2026-06-07T12:00:15+09:00
---

# RUN 2026-06-07 - AI Loop P0 Bridge Go-Check

## Objective

Close the highest-priority Monday paper-experiment gaps identified after
`12726fb`:

1. publish a local GPT Pro `morning_watchlist/v0` artifact into the Monday
   same-day latest paths that Flash actually reads;
2. add a user-level 24h market-intelligence collector timer;
3. make Flash use an exact previous 10-minute source/KIS window instead of an
   unbounded recent-N read;
4. let structured DeepSeek Flash provider `actions` become the trade-document
   action source while `compiled_watch/v0` remains the universe/guard.

## Scope

- No ChatGPT Pro browser session was opened.
- SSH browser-use was not used.
- No broker API, KIS order endpoint, live order, paper order, or secret-bearing
  config was read or called.
- DeepSeek provider behavior was unit-tested with monkeypatched local fixtures
  only.

## Changes

- `backend/lib/ai_analysis_runtime.py`
  - Added `publish_morning_watchlist_artifact(...)` and CLI job
    `--job publish-morning-watchlist`.
  - Publishes to both
    `data/morning-watchlist/<target-date>/morning-watchlist-latest.json` and
    `data/ai/<target-date>/morning-watchlist-latest.json`.
  - Added exact 10-minute Flash event/KIS snapshot readers.
  - Passes provider `actions` into Flash document construction.
- `backend/lib/ai_orchestration.py`
  - Accepts `provider_actions`.
  - Uses in-universe structured provider actions before deterministic compiled
    watch fallback.
  - Persists `input_window_kst`, `action_source`, and provider-supplied entry,
    target, stop, quantity, and planned-cash fields.
- `ops/systemd/user/hwistock-intel-collector.service`
  - Adds the user-service 24h metadata-only news/disclosure collector tick.
- `ops/systemd/user/hwistock-intel-collector.timer`
  - Runs the collector every 10 minutes with `Persistent=true`.
- `backend/tests/test_ai_analysis_runtime.py`
  - Proves Monday same-day watchlist publish paths.
  - Proves exact 10-minute Flash windowing and provider-action selection.
- `docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md`
  - Records the strict 10-minute Flash input window and provider-action source
    contract.
- `docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md`
  - Adds QA-012A/QA-012B rows and pass evidence.

## Validation

All commands were run from `/data/workspace/My/hwiStock`.

| Check | Result |
| --- | --- |
| `source ./env.sh && python3 -m py_compile backend/lib/ai_analysis_runtime.py backend/lib/ai_orchestration.py backend/service/ai_analysis_runner.py backend/tests/test_ai_analysis_runtime.py` | PASS |
| `source ./env.sh && python3 -m pytest backend/tests/test_ai_analysis_runtime.py backend/tests/test_ai_orchestration_layer.py -q` | PASS - 24 passed, 6 subtests |
| `source ./env.sh && python3 -m pytest backend/tests/test_operational_go_check_pipeline.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_market_intelligence_ingestion.py -q` | PASS - 61 passed, 9 subtests |
| `source ./env.sh && python3 -m pytest backend/tests/test_ai_analysis_runtime.py backend/tests/test_ai_orchestration_layer.py backend/tests/test_operational_go_check_pipeline.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_market_intelligence_ingestion.py -q` | PASS - 85 passed, 15 subtests |
| `source ./env.sh && python3 -m py_compile $(find backend scripts ops/systemd -name '*.py' -not -path '*/__pycache__/*')` | PASS |
| `systemd-analyze --user verify ops/systemd/user/hwistock-*.service ops/systemd/user/hwistock-*.timer` | PASS |
| `git diff --check` | PASS |
| `source ./env.sh && python3 scripts/validate_runtime_contracts.py --schema docs/contracts/hwistock-runtime-contracts.schema.json --valid docs/contracts/fixtures/runtime-contract-valid.json --invalid docs/contracts/fixtures/runtime-contract-invalid.json` | PASS - runtime_contract_validation=PASS, valid_artifacts=12, invalid_cases=28, schema_count=12 |
| LF scan for `backend`, `ops/systemd`, `docs`, `scripts`, `.gitattributes` | PASS - line_ending_issues=0 |

## Result

PASS. Monday paper experiment has a direct way to publish local GPT Pro morning
artifacts into the target trading-day paths, a user-level 24h intel collector
timer, exact 10-minute Flash input windows, and provider-action-driven Flash
trade documents guarded by compiled-watch universe membership.

## Remaining Follow-Up

- SELL action to paper sell intent remains follow-up.
- Daily close Pro job remains follow-up.
- Future live-mode KRX-only versus KRX+NXT execution-window separation remains
  follow-up before any live transition.
