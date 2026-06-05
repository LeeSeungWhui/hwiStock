---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-003-go-preflight-rebaseline
stage: go
unit_id: HWISTOCK-UNIT-003
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md
module_refs:
  - docs/modules/HWISTOCK-MOD-002_market-intelligence-ingestion.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md
source_registry_ref: docs/sources/HWISTOCK-SOURCE-REGISTRY.md
ready_set_completion_ref: docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md
rebaseline_evidence_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
created_at: 2026-06-04
supersedes:
  - docs/evidence/RUN-20260604_unit-003-go-preflight.md
---

# UNIT-003 Go Preflight Evidence — Rebaseline 2026-06-04

## 1. Verdict

PASS. `HWISTOCK-UNIT-003` may enter Go-Check for the current MyWebTemplate
import baseline under the fixture/config-first market-intelligence ingestion
skeleton scope.

This preflight authorizes only local source-registry loading, in-memory fixture
ingestion, normalized event shaping, duplicate linking, summary/health output,
blocked-source guards, focused tests, and docs/evidence synchronization. It
does not authorize network OpenDART calls, Naver calls, KRX/KIND automated
collection, KIS/broker data calls, AI provider calls, orders, credential
storage, HTML scraping, runtime schedulers, server operations, browser QA,
deploy, or runtime `data/` artifact commits.

## 2. Current Baseline

The historical `RUN-20260604-unit-003-go-preflight` evidence is superseded
because the 2026-06-04 MyWebTemplate import changed the backend/frontend code
baseline. This rebaseline preflight uses:

- `docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md`
- `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`
- `docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md`

## 3. Delegation Guard

- Stage: go
- Gate size: FULL_GATE
- Route class: implementation_worker
- Workspace: `/data/workspace/My/hwiStock`
- Workspace mode: direct project cwd
- Primary non-GPT preference: Cursor SDK and MoonBridge routes where available
  and launch-verified.
- Forbidden:
  - `.env*`, `/home/hwi/.config/hwistock/**`, `backend/config.ini`,
    `backend/config.test.ini`, `frontend-web/config.ini`, and `apiRefer/**`
  - broker/KIS/API/AI network calls
  - token/account/balance/quote/realtime/order/WebSocket calls
  - database connections and migration execution
  - server/deploy/browser/systemd/git mutation
  - runtime `data/` artifact commits
  - fake fills, fake balances, fake PnL, broker orders, account-affecting orders

## 4. Selected Row Scope

Included implementation/check surface:

- `backend/lib/market_intelligence.py`
- `backend/service/market_intelligence_ingestion.py`
- `backend/tests/test_market_intelligence_ingestion.py`
- UNIT-003 module/unit/QA/index/evidence documentation

Excluded surface:

- network OpenDART API calls
- Naver API calls
- KRX/KIND automated collection
- KIS/broker market/realtime/news calls
- general media HTML scraping
- strategy scoring
- direct order routing
- runtime scheduler/service loop

## 5. Pre-Go Checklist

| check_id | result | evidence |
| --- | --- | --- |
| PF-01 | PASS | Current rebaseline Ready-Set completion report exists. |
| PF-02 | PASS | Rebaseline completion report has `implementation_ready: true` for `skeleton_sandbox_safe_rebaseline_queue`. |
| PF-03 | PASS | `HWISTOCK-UNIT-003` appears in the rebaseline Go-Check queue. |
| PF-04 | PASS | At preflight time `HWISTOCK-UNIT-003` queue row was `ready_for_go_check`; after Go-Check this row is updated to `go_check_passed` in the row-closure matrix. |
| PF-05 | PASS | Unit, module, QA scenario, profile, source registry, and index refs exist. |
| PF-06 | PASS | Current scope is local fixture/config ingestion only; no broker/API/order action is authorized. |
| PF-07 | PASS | Source registry decisions remain: DART fixture source approved, Naver/KIND/KRX conditional, KIS deferred, HTML/unofficial scraping forbidden. |
| PF-08 | PASS | MyWebTemplate import invalidated old UNIT-003 evidence, so a new current Go-Check evidence file is required. |

## 6. Pre-Go Action

Proceed with UNIT-003 current-tree market-intelligence ingestion skeleton
implementation, validation, Check review, and rebaseline evidence
synchronization.
