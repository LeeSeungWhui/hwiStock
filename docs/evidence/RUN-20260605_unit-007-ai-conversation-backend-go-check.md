---
schema_version: hwi.evidence/v0
id: RUN-20260605-unit-007-ai-conversation-backend-go-check
type: evidence
unit_refs:
  - HWISTOCK-UNIT-007
module_refs:
  - HWISTOCK-MOD-006
stage: go-check
status: pass_pending_browser_tunnel_prove
created_at: 2026-06-05
owner: codex
---

# UNIT-007 AI Conversation Backend Go-Check Evidence

## 1. Scope

This run completed the backend side of the corrected dashboard AI conversation
contract.

Implemented scope:

- `backend/router/HwiStockAiRouter.py`
  - Adds `POST /api/v1/hwistock/ai/conversation`.
  - Returns the standard hwiStock JSON response with `Cache-Control: no-store`.
- `backend/lib/operator_console_runtime.py`
  - Builds a sanitized, artifact-only conversation context from stored runtime
    files.
  - Does not call broker APIs, KIS adapters, AI providers, service controls, or
    order mutation paths.
  - Refuses order execution, setting mutation, credential disclosure, and
    service lifecycle prompts.
  - Writes local JSONL audit records under `data/audit/ai_conversation/YYYY-MM-DD/`.
- `backend/tests/test_hwistock_ai_conversation.py`
  - Covers grounded answers from stored artifacts, unsafe prompt refusal,
    secret-like audit preview redaction, and the router response contract.

## 2. Result

Go-Check PASS for backend AI conversation implementation:

- Normal questions return an answer grounded in stored Pro/Flash/intelligence
  artifacts and runner readiness state.
- Unsafe action prompts are refused with visible explanation text.
- Conversation audit records include request id, question hash, redacted preview,
  sanitized context refs, model route, latency, refusal state, and side-effect
  flags.
- The route is local deterministic dashboard answering only:
  `local_deterministic_dashboard_answer`.
- The implementation records `networkCallMade=false`, `brokerCallMade=false`,
  `orderMutationAttempted=false`, `serviceMutationAttempted=false`, and
  `credentialValuesPrinted=false`.

## 3. Validation

Commands:

- `source ./env.sh && python -m pytest backend/tests/test_hwistock_ai_conversation.py backend/tests/test_hwistock_runner.py -q`
  - PASS, 38 tests
- `source ./env.sh && pnpm --dir frontend-web exec vitest run tests/dashboard.view.test.jsx`
  - PASS, 9 tests
- `source ./env.sh && pnpm --dir frontend-web exec eslint app/dashboard/view.jsx app/dashboard/lang.ko.js tests/dashboard.view.test.jsx`
  - PASS
- `source ./env.sh && python /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn`
  - PASS, changed scan files: 4, findings: error=0, warning=0, info=0
- `git diff --check`
  - PASS
- `source ./env.sh && pnpm --dir frontend-web build`
  - PASS
  - Existing warning remains: Next.js `middleware` convention deprecation and
    Turbopack NFT trace warning from `next.config.mjs`/server config import
    path. No dashboard compile failure.

## 4. Remaining Risk

This evidence closes the backend Go-Check gap for the corrected conversation
contract, but it is not browser/tunnel Prove. A later Prove pass still needs to
exercise the authenticated dashboard conversation input against the running
frontend/backend pair and capture UI/API/audit evidence.
