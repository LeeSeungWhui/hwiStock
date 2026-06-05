---
schema_version: hwi.evidence/v0
id: RUN-20260605-unit-007-lucid-command-dashboard-go
type: evidence
unit_refs:
  - HWISTOCK-UNIT-007
module_refs:
  - HWISTOCK-MOD-006
stage: go
status: pass_frontend_backend_followup_required
created_at: 2026-06-05
owner: codex
---

# UNIT-007 Lucid Command Dashboard Go Evidence

## 1. Scope

This run applied the fresh `agy` dashboard design direction to the existing
dashboard frontend without using the old screen as design input.

Implemented frontend/docs scope:

- `docs/design/HWISTOCK-DESIGN-20260605_lucid-command-dashboard.md`
- `frontend-web/app/dashboard/view.jsx`
- `frontend-web/app/dashboard/lang.ko.js`
- `frontend-web/tests/dashboard.view.test.jsx`
- UNIT-007 / MOD-006 / QA/index doc links and status updates

## 2. Result

Frontend Go PASS:

- The dashboard now uses the **Lucid Command** dark desktop-first operator
  cockpit layout.
- Stored AI reports and AI conversation are separated into distinct UI surfaces.
- The AI conversation panel exposes a question textarea, submit affordance,
  read-only disclaimer, local Q&A/refusal rendering, and POST wiring to
  `/api/v1/hwistock/ai/conversation`.
- The UI keeps buy/sell/order execution controls out of the dashboard.
- User-facing mode text maps `paper_sandbox`/sandbox/mock-like runtime tokens to
  neutral operator-facing labels instead of exposing raw adapter tokens.

Backend follow-up:

- The backend AI conversation endpoint, grounded answer/refusal behavior, and
  local audit logging are completed in
  `docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`.
- Browser/tunnel Prove for the full frontend+backend conversation flow remains
  pending.

## 3. Worker / Acceptance Note

A `hwi-cursor-worker` run produced a `WORKER_RESULT: DONE` patch and reported:

- focused dashboard Vitest: 8/8 passed before local follow-up edits;
- `git diff --check`: clean.

The wrapper classification was **not accepted** because concurrent hwiStock
runtime services wrote ignored `data/` and `logs/` files during the worker run,
which the wrapper reported as out-of-scope environmental file changes. The
worker output was therefore treated as a quarantined draft and the final result
was owned by local Codex review, follow-up patching, and validation.

## 4. Local Validation

Commands run after local takeover:

- `python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn`
  - PASS, findings: error=0, warning=0, info=0
- `pnpm --dir frontend-web exec vitest run tests/dashboard.view.test.jsx`
  - PASS, 9 tests
- `pnpm --dir frontend-web exec eslint app/dashboard/view.jsx app/dashboard/lang.ko.js tests/dashboard.view.test.jsx`
  - PASS
- `git diff --check`
  - PASS
- `pnpm --dir frontend-web build`
  - PASS
  - Existing warning remains: Next.js `middleware` convention deprecation and
    Turbopack NFT trace warning from `next.config.mjs`/server config import
    path. No dashboard compile failure.

## 5. Remaining Risk

This evidence does not close UNIT-007 Prove by itself. It proves the dashboard
frontend/design half; the backend half is covered by
`docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`, and
browser/tunnel Prove remains pending.
