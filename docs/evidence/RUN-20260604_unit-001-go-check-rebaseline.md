---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-001-go-check-rebaseline
stage: check
unit_id: HWISTOCK-UNIT-001
status: pass
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-001_project-bootstrap.md
module_refs:
  - docs/modules/HWISTOCK-MOD-001_trading-safety-core.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md
preflight_ref: docs/evidence/RUN-20260604_unit-001-go-preflight-rebaseline.md
owner_decision_ref: docs/set/READY-SET-OWNER-DECISION-20260604_rebaseline_hwistock.md
rebaseline_evidence_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
ready_set_reissue_evidence_ref: docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md
created_at: 2026-06-04
supersedes:
  - docs/evidence/RUN-20260604_unit-001-go-check.md
---

# UNIT-001 Go-Check Evidence — Rebaseline 2026-06-04

## 1. Verdict

PASS. `HWISTOCK-UNIT-001` completed Go-Check as a docs-only bootstrap
verification row against the 2026-06-04 rebaseline Ready-Set.

This result does not authorize product-code implementation outside this
docs-only unit, broker/KIS network calls, AI provider calls, paper orders, live
orders, credential storage, or operational trading readiness.

## 2. Go Changes

- Marked `docs/evidence/RUN-20260604_unit-001-go-preflight.md` as historical /
  superseded by this rebaseline evidence.
- Marked `docs/evidence/RUN-20260604_unit-001-go-check.md` as historical /
  superseded by this rebaseline evidence.
- Created current rebaseline preflight evidence:
  `docs/evidence/RUN-20260604_unit-001-go-preflight-rebaseline.md`.
- Created current rebaseline Go-Check evidence:
  `docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md`.
- Updated `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md` evidence refs and
  set summary wording to current rebaseline.
- Updated `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md` evidence refs to
  current rebaseline.
- Verified MyWebTemplate quarantine guardrails are documented in the rebaseline
  Ready-Set docs, row closure matrix, and owner decision.
- Recorded quarantined Kimi MoonBridge worker attempt and accepted Cursor
  patch-only audit closure in section 7.
- Set UNIT-001/QA/MOD-001/index statuses to `go_check_passed` for docs-only
  rebaseline scope (MOD-001 `build_status` remains `pending_implementation`).

## 3. Check Review

| finding_id | priority | status | note |
| --- | --- | --- | --- |
| none | none | pass | No open P0/P1/P2 findings remain for UNIT-001 docs-only rebaseline scope. |

## 4. QA Row Results

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | `AGENTS.md` exists and identifies `docs/profiles/PROFILE-HWISTOCK.md` plus Hwi Work Harness routing. |
| QA-002 | pass | Profile approval policy keeps broker/live order/real-money operations approval-gated. |
| QA-003 | pass | `HWISTOCK-MOD-001` states no live orders by default and keeps order placement disabled unless an active unit explicitly approves it. |
| QA-004 | pass | QA scenario references `HWISTOCK-UNIT-001`, `HWISTOCK-MOD-001`, and `PROFILE-HWISTOCK`. |
| QA-005 | pass | Index/profile/unit/module show KIS direction, stack/risk decisions, closed rebaseline Ready-Set state, bounded KIS smoke, and residual operational restrictions. |
| QA-006 | pass | Profile/module/unit preserve the one full week paper/sandbox evidence gate before live go/no-go. |
| QA-007 | pass | Profile/module/unit preserve cash-only/no-leverage policy. |

## 5. MyWebTemplate Quarantine Verification

For UNIT-001 (docs-only bootstrap), no product-code quarantine action was taken.
The quarantine guardrails were verified as documented first-row blockers:

- Owner decision records quarantine targets:
  `docs/set/READY-SET-OWNER-DECISION-20260604_rebaseline_hwistock.md`.
- Row closure matrix encodes quarantine as first-row requirement for all
  affected units: `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`.
- Go preflight checklist requires PF-14 quarantine verification:
  `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md`.

Backend and frontend filename inventories from the import are recorded in
`docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`.
Sample/public routes exist in the imported tree but are not removed in UNIT-001;
their removal/replacement is explicitly scoped to future rows (UNIT-002 through
UNIT-007) per the rebaseline row closure matrix.

## 6. Validation Commands

Executed locally from `/data/workspace/My/hwiStock` on 2026-06-04:

1. Read-only doc existence and content review for AGENTS.md, index.md,
   PROFILE-HWISTOCK.md, MOD-001, UNIT-001, QA-001, and all rebaseline Ready-Set
   docs.
   - Result: PASS.
   - Coverage:
     - required doc existence
     - rebaseline Ready-Set `implementation_ready: true` for
       `skeleton_sandbox_safe_rebaseline_queue`
     - `HWISTOCK-UNIT-001` queue row `ready_for_go_check`
     - PF-13 Git baseline
     - one-week gate
     - cash-only/no-leverage gate
     - no stale pre-import current-authority wording in UNIT-001 or MOD-001
     - exact known secret marker absence in docs/AGENTS/.gitignore

2. `git status --short`
   - Result: PASS.
   - Worktree has only expected docs/evidence changes.

3. `git diff --check`
   - Result: PASS.

4. `git check-ignore -v backend/config.ini frontend-web/config.ini`
   - Result: PASS. Both template config files remain ignored.

5. `rg` stale-reference scan on allowed UNIT-001 docs/evidence (pre-rebaseline
   current-authority wording, `pending_go_check` on UNIT-001/QA).
   - Result: PASS after Cursor patch-only closure.

6. YAML/frontmatter parse review for UNIT-001 unit, QA, MOD-001, and rebaseline
   evidence files.
   - Result: PASS.

No broker/KIS/API, AI provider, server, database, browser, deploy, network,
credential, order, or product-code action was run for this UNIT-001 rebaseline
Go-Check.

## 7. Worker Output Acceptance

### Attempt 1 — quarantined (not accepted)

- Gate id: `HWISTOCK-UNIT001-GO-CHECK-KIMI-20260604` (orchestrator contract).
- Route/model: `codex-cli-moonbridge` / `Kimi-2.6`.
- Launch: `/data/workspace/My/hwiStock` / `direct_project_cwd`.
- Contract: `/tmp/hwistock-unit001-go-check-kimi-20260604/contract.md`.
- Transcript: `/tmp/hwistock-unit001-go-check-kimi-20260604/transcript.log` (plus
  orchestrator PTY output).
- Last message: `/tmp/hwistock-unit001-go-check-kimi-20260604/last-message.txt` was
  **not created** before termination.
- Observed failure: no final sentinel, no last-message artifact, repeated
  `ReasoningSummaryDelta` stream noise, `apply_patch` verification failures,
  killed by orchestrator after ~6 minutes (exit code 143).
- Acceptance state: **quarantined / not accepted**. Any partial edits were not
  trusted; closure used independent audit only.

### Attempt 2 — accepted (current closure)

- Gate id: `HWISTOCK-UNIT001-GO-CHECK-CURSOR-20260604`.
- Route/model: `cursor-sdk-local` / `composer-2.5` (`cursor-agent-headless`).
- Mode: patch-only write on allowed docs/evidence paths only.
- Acceptance state: **accepted** after independent read of rebaseline Ready-Set
  docs, historical relabeling, stale-reference cleanup, and validation commands
  below. No broker/network/server/product-code actions.
