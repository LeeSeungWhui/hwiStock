---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-unit-005-go-preflight-rebaseline
stage: go-preflight
unit_id: HWISTOCK-UNIT-005
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-005_ai-orchestration-layer.md
module_ref: docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
created_at: 2026-06-05
environment: local_only
route_class: implementation_worker
route: cursor-sdk-local
adapter: hwi-cursor-worker
model: composer-2.5
orchestration_gate_id: DG-HWISTOCK-UNIT-005-GO-CURSOR-20260605-001
---

# UNIT-005 Go Preflight Evidence — Rebaseline

## 1. Verdict

PASS. `HWISTOCK-UNIT-005` was eligible to enter current-tree Go-Check for the
bounded local AI orchestration foundation.

The approved first Go scope was limited to deterministic local helpers and
focused tests for AI job registry, disabled-by-default AI provider/network
configuration, structured recommendation validation, source grounding,
sensitive-payload review, draft order intent rejection, deterministic
strategy/risk gate handoff, no-order dry-run records, audit records, and
fallback reports.

## 2. Delegation / Worker Route

- Route class: `implementation_worker`
- Adapter: `cursor-sdk-local` through `hwi-cursor-worker run`
- Model: `composer-2.5`
- Workspace: `/data/workspace/My/hwiStock`
- Workspace mode: `direct_project_cwd`
- Contract file: `/tmp/hwistock-unit005-cursor/contract.md`
- Dry-run transcript: `/tmp/hwistock-unit005-cursor/dry-run.jsonl`

Dry-run result:

```text
status=accepted
exit_code=0
message=dry_run_ok
gate_id=DG-HWISTOCK-UNIT-005-GO-CURSOR-20260605-001
```

## 3. Allowed / Forbidden Scope

Allowed writes:

- `backend/lib/ai_orchestration.py`
- `backend/tests/test_ai_orchestration_layer.py`

Forbidden:

- secret/env/config reads or writes;
- `/home/hwi/.config/hwistock` reads;
- broker/KIS/API/network calls;
- AI provider calls;
- browser automation;
- server, DB, migration, deploy, systemd, or git mutation;
- edits outside the allowed write set.

## 4. Preconditions Checked

- Current row closure listed `HWISTOCK-UNIT-005` as `ready_for_go_check`.
- `hwi-cursor-worker run --dry-run` accepted the contract/config.
- Cursor SDK local route was treated as a CLI wrapper route, not an MCP
  `tool_search` route.
- No new broker, KIS, AI-provider, browser, server, DB, or deployment approval
  was requested or used.
- Secrets were referenced only by forbidden path/pattern, not read or copied.

## 5. Proceeded Work

After this preflight, the implementation worker produced
`docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md`.
