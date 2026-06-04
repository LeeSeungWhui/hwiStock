---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-unit-005-go-check-rebaseline
stage: go-check
unit_id: HWISTOCK-UNIT-005
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-005_ai-orchestration-layer.md
module_refs:
  - docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md
  - docs/modules/HWISTOCK-MOD-001_trading-safety-core.md
  - docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md
preflight_ref: docs/evidence/RUN-20260605_unit-005-go-preflight-rebaseline.md
created_at: 2026-06-05
environment: local_only
route_class: implementation_worker
route: cursor-sdk-local
adapter: hwi-cursor-worker
model: composer-2.5
reasoning: medium
orchestration_gate_ids:
  - DG-HWISTOCK-UNIT-005-GO-CURSOR-20260605-001
  - DG-HWISTOCK-UNIT-005-GO-CURSOR-20260605-002
---

# UNIT-005 Go-Check Evidence — Rebaseline

## 1. Verdict

PASS. `HWISTOCK-UNIT-005` now has a current-authority local AI orchestration
foundation in the imported backend tree.

Validated scope is limited to deterministic local helpers for AI job registry,
disabled-by-default AI provider/network/cost configuration, structured
recommendation validation, source grounding, sensitive-payload review, draft
order intent rejection, deterministic strategy/risk gate handoff, no-order
dry-run records, audit records, fallback reports, daily-close PnL source
validation, and tool-use-disabled enforcement.

This closure does **not** authorize AI provider calls, ChatGPT browser
automation, DeepSeek network calls, nonzero AI cost caps, broker/KIS calls,
paper/live orders, fake fills, fake balances, fake PnL, public dashboard
exposure, server start, DB work, or credential reads.

## 2. Route

Primary implementation worker:

- Route: `cursor-sdk-local`
- Launcher: `hwi-cursor-worker run`
- Model: `composer-2.5`
- Gate id: `DG-HWISTOCK-UNIT-005-GO-CURSOR-20260605-001`
- Transcript: `/tmp/hwistock-unit005-cursor/run.jsonl`
- Worker result: `DONE`
- Changed files:
  - `backend/lib/ai_orchestration.py`
  - `backend/tests/test_ai_orchestration_layer.py`

Follow-up implementation worker:

- Route: `cursor-sdk-local`
- Launcher: `hwi-cursor-worker run`
- Model: `composer-2.5`
- Gate id: `DG-HWISTOCK-UNIT-005-GO-CURSOR-20260605-002`
- Transcript: `/tmp/hwistock-unit005-cursor-followup/run.jsonl`
- Worker result: `DONE`
- Reason: orchestrator review found that the policy-gate route needed explicit
  `known_source_ids` source-grounding and nested sensitive payload keys needed
  stricter detection.

No Codex multi-agent, DeepSeek/Kimi multi-agent, MoonBridge, browser, KIS,
broker, server, DB, deploy, package install, or git mutation route was used.

## 3. Implemented Scope

- `backend/lib/ai_orchestration.py`
  - `loadAiOrchestrationConfig()` with disabled defaults.
  - `getAiJobRegistry()` for the six first-pass scheduled roles.
  - `validateAiRecommendation()` for `ai_recommendation/v0`, allowed actions,
    KST timestamps, source grounding, stale-data rejection, broker/policy/tool
    request rejection, and non-executable draft order intent validation.
  - `reviewAiRequestPayload()` for credential/account/private-data and
    unapproved full-body field rejection, including nested sensitive keys.
  - `routeAiRecommendationThroughPolicyGate()` for deterministic UNIT-004
    strategy/risk gate handoff and source-grounded recommendation validation.
  - `buildAiNoOrderDryRunDecisionRecord()` and
    `validateAiNoOrderDryRunDecisionRecord()` for no-order-only approved
    recommendations without broker calls, order submission, paper/live orders,
    fake fills, fake balances, or fake PnL.
  - `buildAiAuditRecord()`, `buildAiFallbackReport()`,
    `validateDailyCloseReport()`, and `simulateAiFailure()` for audit/fallback
    evidence.
- `backend/tests/test_ai_orchestration_layer.py`
  - focused unittest coverage for QA-001 through QA-016.

## 4. Boundary Evidence

- The new implementation is stdlib-only except for the existing local
  `strategy_risk` import.
- No implementation path imports AI SDKs, HTTP/network clients, FastAPI,
  SQLAlchemy, broker, KIS, router, paper adapter, or live adapter modules.
- AI outputs are recommendation-only; `entry_unlocked` remains false even after
  deterministic policy approval.
- Policy-approved `consider_entry` outputs produce no-order dry-run records
  only.
- Invented source ids are rejected when the policy-gate route receives the
  known source id set.
- Nested sensitive payload keys such as account identifiers and credentials are
  rejected.
- Daily-close reports require system-calculated PnL source fields.
- Tool-use requests are rejected and AI tool use is disabled by default.

## 5. QA Row Coverage

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | Import/static review confirms no broker/order router interface and no forbidden network/AI SDK imports. |
| QA-002 | pass | Malformed or unknown-action AI output is rejected. |
| QA-003 | pass | Missing or invented source ids are rejected, including on the policy-gate route when `known_source_ids` is supplied. |
| QA-004 | pass | Deterministic UNIT-004 risk gate rejects reserve-floor violations and AI cannot override it. |
| QA-005 | pass | AI request payload review rejects top-level and nested credentials/account/private data. |
| QA-006 | pass | AI timeout/unavailable simulation produces rejected fallback with no entry unlock. |
| QA-007 | pass | Audit record captures model role/name, prompt schema, input bundle ids, source ids, latency, validation status, and action. |
| QA-008 | pass | All-in, credit/margin, stop-bypass, and overnight language are rejected. |
| QA-009 | pass | Draft order intent rejects missing risk reference, stale source, all-in sizing, credit/margin, and broker endpoint references. |
| QA-010 | pass | Policy-approved intent is recorded as no-order dry-run only, with no broker endpoint, fake broker, simulated fill, fake balance, paper order, or live order. |
| QA-011 | pass | KIS/external broker, broker demo/testbed, paper/live endpoint, and credential references are rejected. |
| QA-012 | pass | Job registry separates all six planned AI roles and schedules. |
| QA-013 | pass | ChatGPT Pro late/unavailable fallback uses DeepSeek-only morning mode. |
| QA-014 | pass | Daily close report requires system-calculated PnL source fields and AI interpretation only. |
| QA-015 | pass | AI tool use is disabled and tool/browse requests are rejected. |
| QA-016 | pass | AI network/provider flags are disabled and AI daily cost cap is zero by default. |

## 6. Validation

```text
python -m unittest backend.tests.test_ai_orchestration_layer
=> Ran 17 tests
=> OK

python -m unittest backend.tests.test_ai_orchestration_layer backend.tests.test_strategy_risk_rulebook backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract backend.tests.test_trading_engine_order_state
=> Ran 63 tests
=> OK

python -m py_compile $(find backend -name '*.py' -print)
=> PASS

git diff --check
=> PASS
```

Rule-gate:

```text
fastapi-backend-rule-preset overall status: fail due broader imported baseline findings
total findings: 92
UNIT-005 code findings: 0
```

Secret marker scan:

```text
known KIS paper credential/account/id markers in UNIT-005 changed code/tests
=> no matches
```

## 7. Remaining Boundaries / Follow-Up

- Nonzero AI provider use, provider pricing/cost cap changes, DeepSeek API
  calls, ChatGPT browser review execution, and live model/tool execution remain
  future approval scopes.
- `HWISTOCK-UNIT-007` remains pending Go-Check for dashboard/operator console.
- The broader imported backend rule-gate baseline still has unrelated findings
  outside the UNIT-005 changed files.
