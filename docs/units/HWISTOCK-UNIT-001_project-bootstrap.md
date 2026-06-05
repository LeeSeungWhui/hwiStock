---
schema_version: hwi.unit/v0
id: HWISTOCK-UNIT-001
type: unit
domain: docs
name: Project bootstrap
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
work_class: docs_only
completeness:
  status: sufficient
  audit_ref: docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md
owner: hwi
updated_at: 2026-06-04
last_verified_at: 2026-06-04
source_snapshot:
  input_digest: "주식자동매매단타프로젝트 시작 준비"
  legacy_doc: none
  legacy_status: greenfield
source_inputs:
  - kind: user_prompt
    path_or_url: "주식자동매매단타프로젝트"
    confidence: medium
profile_refs:
  - PROFILE-HWISTOCK
module_ids:
  - HWISTOCK-MOD-001
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  include:
    - AGENTS.md
    - docs/**
  exclude:
    - "**/*credentials*"
    - "**/*.env"
entrypoints: []
interfaces: []
verification:
  stage_skill_routes:
    ready:
      - hwi-work-harness
    set:
      - hwi-work-harness
    go:
      - hwi-work-harness
    check:
      - hwi-work-harness
    prove:
      - hwi-work-harness
  required_gates:
    - docs-bootstrap-check
  suggested_gates: []
qa_scenario_refs:
  - docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md
risk:
  tier: 1
  reasons:
    - Financial automation project, but current unit is docs-only and forbids live trading.
last_set:
  status: set
  report_id: RUN-20260602-unit-001-project-bootstrap-set
  context_fingerprint:
evidence_refs:
  - run_id: RUN-20260602-project-bootstrap
    status: set
  - run_id: RUN-20260602-unit-001-project-bootstrap-set
    status: set
  - run_id: RUN-20260604-unit-001-go-preflight
    status: historical_after_mywebtemplate_rebaseline
  - run_id: RUN-20260604-unit-001-go-check
    status: historical_after_mywebtemplate_rebaseline
  - run_id: RUN-20260604-unit-001-go-preflight-rebaseline
    status: pass
  - run_id: RUN-20260604-unit-001-go-check-rebaseline
    status: pass
links:
  - HWISTOCK-MOD-001
---

# Project Bootstrap

## 1. Goal

Prepare the empty `/data/workspace/My/hwiStock` root for a stock day-trading
automation project using Hwi Work Harness, while explicitly blocking live trading
and broker side effects until future Set contracts approve them. Actual live
operation must be preceded by an operator-selected paper/sandbox observation
window with named evidence and explicit go/no-go approval. The runner must not
hardcode the observation duration.

## 2. Baseline Module Contract

This unit creates the initial docs contract for `HWISTOCK-MOD-001`, the trading
safety core. It does not implement trading behavior.

### Module Change

Initial creation of `HWISTOCK-MOD-001`.

## 3. Included Scope

- Root `AGENTS.md`.
- Docs index.
- Active project profile draft-to-active update.
- Set trading safety module.
- Set bootstrap unit.
- Set bootstrap QA scenario.
- Bootstrap evidence summary.

## 4. Excluded Scope

- Trading strategy implementation.
- Broker/API integration.
- Credential storage.
- Market data integration.
- Backtest engine.
- Paper/sandbox order execution.
- Live account access or live orders.
- UI/dashboard implementation.

## 5. Acceptance Criteria

| ac_id | priority | criterion | observable_result | evidence | linked_qa_rows |
| --- | --- | --- | --- | --- | --- |
| AC-01 | P0 | Root instructions identify the hwiStock profile and harness route | `AGENTS.md` exists with profile path | file review | QA-001 |
| AC-02 | P0 | Profile blocks live brokerage/order operations by default | approval policy includes broker/live order gates | file review | QA-002 |
| AC-03 | P0 | Initial safety module exists | `HWISTOCK-MOD-001` exists | file review | QA-003 |
| AC-04 | P1 | Bootstrap QA scenario exists | QA file exists and references this unit | file review | QA-004 |
| AC-05 | P1 | Decisions and remaining Go/operational boundaries are listed | selected broker, stack, strategy/risk, paper-boundary, source registry, closed Ready-Set state, and remaining Go/operational restrictions are visible | file review | QA-005 |
| AC-06 | P0 | Live operation requires an observation evidence gate | profile/module mention operator-selected paper/sandbox observation evidence before live | file review | QA-006 |
| AC-07 | P0 | Capital policy is cash-only | profile/module forbid credit, margin, 미수, borrowed funds, and leveraged capital by default | file review | QA-007 |

## 6. Implementation Notes

This is a docs-only bootstrap. Future product-code units must pass Ready-Set
before Go and must not treat this bootstrap as permission to implement live
trading.

## 7. Open Questions

Closed by later Set docs:

- Broker/API provider direction is KIS; KB Securities is blocked as a practical
  personal API candidate unless future official confirmation proves otherwise.
- First market scope is Korea domestic stocks with KRX/NXT venue routing.
- Preferred stack is Python/FastAPI, TypeScript/Next.js/React, and PostgreSQL.
- Baseline allocation/risk policy is cash-only, starting capital 2,000,000 KRW,
  max simultaneous holdings 5, minimum cash reserve ratio 0.25, and AI-assisted
  stop prices capped by deterministic maximum -5% loss validation.
- Dashboard/UI scope is selected as read-only operator console with no direct
  buy/sell controls.
- First source allowlist is DART-first, with Naver/KRX/KIND conditional or
  deferred and general HTML scraping blocked by default.

Closed by rebaseline Ready-Set completion (2026-06-04):

- Strategy decision-packet approval was recorded for paper/sandbox planning
  defaults.
- Dashboard design review was executed and its Set-level findings were applied.
- Historical pre-import closure is recorded in
  `docs/set/READY-SET-COMPLETION-20260602_hwistock.md` (superseded).
- Current rebaseline closure, row closure, owner decision, and Go preflight are
  recorded in `docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md`,
  `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`,
  `docs/set/READY-SET-OWNER-DECISION-20260604_rebaseline_hwistock.md`, and
  `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md`.
- The current Ready-Set gate is `implementation_ready: true` only for the
  `skeleton_sandbox_safe_rebaseline_queue`. It is not live or operational
  trading readiness.
- MyWebTemplate sample/public/template quarantine is a documented first-row
  blocker for affected future units; UNIT-001 verified guardrails only and did
  not remove product-code surfaces.

Still future strategy/provider follow-up, not permission to infer during Go:

- First-pass alpha/chart/source/candle/liquidity/market-alert defaults are
  packaged in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`; Go must
  use those recorded defaults rather than inferring new strategy parameters.
- Nonzero AI API token/cost caps and any AI network enablement.

## 8. Spec Completeness Audit

| artifact | status | gaps | blocks_go |
| --- | --- | --- | --- |
| module | sufficient | `HWISTOCK-MOD-001` covers safety, approvals, runtime, broker boundary, risk invariants, and verification families | no |
| unit | sufficient | docs-only bootstrap contract and boundaries are explicit | no |
| qa_scenario | sufficient | docs-only QA rows cover profile, module, operator-selected paper observation gate, and capital policy | no |
| smoke | minimal_exception | docs-only unit; smoke is file/content review | no |
| prove_full_run | minimal_exception | docs-only unit; no browser/API/product flow exists | no |

## 9. Set Summary

UNIT-001 passed Go-Check as a docs-only bootstrap verification on 2026-06-04
against the rebaseline Ready-Set. Current authority:
`docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md` (preflight:
`docs/evidence/RUN-20260604_unit-001-go-preflight-rebaseline.md`). Pre-rebaseline
evidence is historical only.

The broader rebaseline queue has `implementation_ready: true` for
`skeleton_sandbox_safe_rebaseline_queue`, but this unit still does not authorize
product-code implementation beyond its docs-only scope, broker/KIS/AI network
calls, paper orders, live orders, credential storage, MyWebTemplate surface
removal, or operational trading readiness.
