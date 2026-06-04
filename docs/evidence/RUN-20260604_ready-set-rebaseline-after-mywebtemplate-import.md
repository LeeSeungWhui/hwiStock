---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-ready-set-rebaseline-after-mywebtemplate-import
stage: ready-set
status: rebaseline_required_after_code_import
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
created_at: 2026-06-04
environment: local_docs_inventory
current_authority: true
implementation_ready: false
prior_ready_set_completion_ref: docs/set/READY-SET-COMPLETION-20260602_hwistock.md
prior_row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md
prior_go_preflight_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md
worker_scout_route: codex-cli-moonbridge
worker_scout_model: Kimi-2.6
worker_workspace_cwd: /data/workspace/My/hwiStock
worker_workspace_mode: direct_project_cwd
worker_output_acceptance: accepted
---

# Ready-Set Rebaseline After MyWebTemplate Import

## 1. Verdict

REBASELINE REQUIRED. On 2026-06-04, `backend/` and `frontend-web/` were
replaced with MyWebTemplate-derived code. That import is now the current code
baseline, but it invalidates the earlier Ready-Set row closure and the Go-Check
evidence that referenced hwiStock-specific backend files no longer present in
the tree.

This artifact does not mark Ready-Set complete. It marks the previous
`implementation_ready: true` queue as superseded until a new Ready-Set
completion, row closure, and Go preflight are issued against the imported
MyWebTemplate code baseline.

## 2. Current Imported Code Inventory

Read-only local inventory:

- `backend/`: 65 files.
- `frontend-web/`: 273 files.
- `backend/config.ini` and `frontend-web/config.ini`: present as local template
  config files and ignored by Git. Their contents were not read or printed.

Observed imported surfaces:

- Backend is the MyWebTemplate FastAPI skeleton with `backend/server.py`,
  `backend/run.sh`, `backend/lib/`, `backend/router/`, `backend/service/`,
  `backend/query/`, and `backend/tests/`.
- Backend router/service surfaces include generic MyWebTemplate auth, common,
  dashboard, profile, sample, and transaction areas.
- Frontend is the MyWebTemplate Next.js app with public landing/auth routes,
  sample/component docs surfaces, dashboard/portfolio routes, scripts, tests,
  and MyWebTemplate branding still present.
- The imported backend runtime script currently binds `0.0.0.0`; hwiStock's
  profile still requires local-only dashboard/API exposure unless a future
  explicit approval changes that.

## 3. Invalidated Prior Go-Check Evidence

The following earlier Go-Check evidence is now historical only. The code files
it validated are missing after the MyWebTemplate import.

| evidence | unit | missing current files |
| --- | --- | --- |
| `docs/evidence/RUN-20260604_unit-003-go-check.md` | UNIT-003 | `backend/lib/market_intelligence.py`, `backend/service/market_intelligence_ingestion.py`, `backend/tests/test_market_intelligence_ingestion.py` |
| `docs/evidence/RUN-20260604_unit-004-go-check.md` | UNIT-004 | `backend/lib/strategy_risk.py`, `backend/tests/test_strategy_risk_rulebook.py` |
| `docs/evidence/RUN-20260604_unit-006-go-check.md` | UNIT-006 | `backend/lib/trading_engine.py`, `backend/tests/test_trading_engine_order_state.py` |
| `docs/evidence/RUN-20260604_unit-008-go-check.md` | UNIT-008 | `backend/lib/storage_schemas.py`, `backend/lib/request_payload.py`, `backend/migrations/env.py`, `backend/migrations/script.py.mako`, `backend/migrations/versions/20260604_0001_create_hwistock_core_storage.py`, `backend/tests/test_storage_contract.py` |

## 4. Queue Disposition

Before Go-Check resumes:

- Reopen immediately: `HWISTOCK-UNIT-001`, `HWISTOCK-UNIT-008`,
  `HWISTOCK-UNIT-003`, `HWISTOCK-UNIT-004`, `HWISTOCK-UNIT-006`,
  `HWISTOCK-UNIT-007`.
- Pause pending rebaseline mapping: `HWISTOCK-UNIT-005`,
  `HWISTOCK-UNIT-002`.
- Treat `HWISTOCK-UNIT-009` as least impacted, but still require a reissued
  queue/preflight before treating it as current `ready_for_go_check`.

## 5. Required Next Ready-Set Work

1. Reconcile profile, index, module, unit, and QA docs with the imported
   MyWebTemplate backend/frontend code.
2. Decide which generic MyWebTemplate routes, branding, sample surfaces, config
   assumptions, and bind behavior are kept, renamed, quarantined, or removed
   for hwiStock.
3. Re-port or re-implement the missing hwiStock domain files into the
   MyWebTemplate backend structure.
4. Reissue Ready-Set completion, row closure, and Go preflight after docs and
   code paths agree.
5. Treat MyWebTemplate sample/public surfaces as explicit rebaseline decisions,
   not harmless leftovers. Current observed examples include backend sample
   router/service files, `frontend-web/app/sample/**`, dashboard links to sample
   routes, MyWebTemplate branding in frontend i18n files, and public-route
   config entries for `/sample`.
6. Re-check local-only bind/access behavior before any server run. The current
   imported backend script still needs hwiStock-specific local-only enforcement
   before it can support a Go-Check PASS.

## 6. Direct-CWD Worker Scout

Delegation record:

- route: `codex-cli-moonbridge`
- adapter: `hwi-codex-moonbridge-worker`
- model: `Kimi-2.6`
- mode: read-only advisor/scout
- workspace: `/data/workspace/My/hwiStock`
- workspace mode: `direct_project_cwd`
- contract: `/tmp/hwistock-readyset-directcwd-kimi-20260604/contract.md`
- transcript: `/tmp/hwistock-readyset-directcwd-kimi-20260604/transcript.log`
- last message:
  `/tmp/hwistock-readyset-directcwd-kimi-20260604/last-message.txt`
- final sentinel:
  `HWI_WORKER_RESULT_READYSET_REBASELINE_SCOUT_20260604_DONE`
- acceptance: accepted for Ready-Set rebaseline scouting after local
  orchestrator verification.

Acceptance notes:

- The worker ran in the real project root and did not use a partial snapshot.
- The worker returned the required final sentinel.
- `git status --short` after the worker matched the pre-worker project file
  state; no project files were modified by the worker.
- The worker did not require broker/API/network/server/db/deploy actions.
- The first launch exposed invalid YAML frontmatter in three global worker
  skills. Those skill descriptions were repaired outside this project evidence,
  and a follow-up MoonBridge loader smoke returned `SKILL_LOADER_SMOKE_OK`
  without the prior invalid-YAML loader errors.

## 7. Validation

Read-only checks only; no server, DB, broker/API, network, migration, deploy, or
browser run was performed.

```text
find backend -type f | wc -l
=> 65

find frontend-web -type f | wc -l
=> 273
```

All prior hwiStock domain implementation files listed in section 3 were checked
with `test -e` and are missing.

`git check-ignore -v backend/config.ini frontend-web/config.ini` confirmed both
template config files are ignored.
