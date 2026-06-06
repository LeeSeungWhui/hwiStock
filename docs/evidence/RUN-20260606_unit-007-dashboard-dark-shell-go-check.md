---
schema_version: hwi.evidence/v0
id: RUN-20260606-unit-007-dashboard-dark-shell-go-check
type: evidence
unit_refs:
  - HWISTOCK-UNIT-007
module_refs:
  - HWISTOCK-MOD-006
stage: go-check
status: pass_local_browser_proof
created_at: 2026-06-06
owner: codex
---

# UNIT-007 Dashboard Dark Shell Go-Check Evidence

## 1. Scope

This run followed the Gemini Pro dashboard screenshot critique and folded the
correction into the existing UNIT-007 dashboard authority instead of replacing
the prior Lucid Command implementation.

Corrected scope:

- `docs/set/READY-SET-CORRECTION-20260605_dashboard-dark-console-shell.md`
- `docs/design/HWISTOCK-DESIGN-20260605_lucid-command-dashboard.md`
- `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md`
- `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md`
- `frontend-web/app/dashboard/DashboardLayoutClient.jsx`
- `frontend-web/app/dashboard/view.jsx`
- `frontend-web/tests/dashboard.view.test.jsx`

No backend, trading runner, broker adapter, provider API, credential, deploy,
or order-execution scope was changed.

## 2. Result

PASS for local Go-Check:

- The `/dashboard` route family now uses a coherent dark high-trust operator
  shell across dashboard header, sidebar, main body, and footer.
- The readiness truth banner is visually louder and keeps the not-ready state
  prominent above lower-priority metrics.
- The operator console is denser and more cockpit-like while keeping readable
  account, holdings, candidate, AI report, AI conversation, and audit sections.
- The dashboard card surfaces now override the imported shared `Card` component's
  white default background, preventing the mixed light/dark screen that the
  screenshot review flagged.
- Badge/pill treatment is flatter and less toy-like.
- The dashboard still exposes no order execution controls.

## 3. Worker / Acceptance Note

A delegated implementation worker completed the initial patch:

- route: `codex multi-agent`
- adapter: `multi_agent_v1`
- declared model: `gpt-5.4`
- reasoning: high
- worker result: `WORKER_RESULT: DONE`
- scope written by worker:
  - `frontend-web/app/dashboard/DashboardLayoutClient.jsx`
  - `frontend-web/app/dashboard/view.jsx`
  - `frontend-web/tests/dashboard.view.test.jsx`

Codex accepted the worker output after checking the sentinel, scope, model
declaration, and forbidden-action report. Local Codex then fixed two Check-time
issues:

1. `EasyObj` was removed from React effect dependency arrays without using
   `useState`; a `useRef` bridge keeps the rule-gate and ESLint hook rule
   aligned.
2. Dashboard cards received important dark overrides because the shared `Card`
   component has `bg-white` / `border-gray-200` defaults that otherwise survived
   in the production screenshot.

## 4. Validation

Commands run with `source ./env.sh`:

- `pnpm --dir frontend-web exec vitest run tests/dashboard.view.test.jsx`
  - PASS, 9 tests
- `pnpm --dir frontend-web exec eslint app/dashboard/DashboardLayoutClient.jsx app/dashboard/view.jsx tests/dashboard.view.test.jsx`
  - PASS, no warnings
- `python /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn`
  - PASS, findings: error=0, warning=0, info=0
- `git diff --check`
  - PASS
- `pnpm --dir frontend-web build`
  - PASS
  - Existing build warnings remain unrelated to this dashboard patch:
    Next.js middleware/proxy deprecation and Turbopack NFT trace warning from
    `next.config.mjs` / server config import path.

## 5. Browser Evidence

Local production-style browser proof used a temporary `next start` instance on
`127.0.0.1:5010` after a successful build. The currently deployed `5000`
service was not restarted by this evidence run.

Screenshots:

- Viewport:
  `/tmp/hwistock-dashboard-design-review/dashboard-20260606-dark-shell-v2-viewport.png`
- Full page:
  `/tmp/hwistock-dashboard-design-review/dashboard-20260606-dark-shell-v2-full.png`

Manual screenshot verdict:

- PASS: the mixed white-card failure from the first local screenshot was removed.
- PASS: the whole visible dashboard now reads as one dark operator console.
- PASS: readiness truth remains first-order and visually dominant.
- PASS: account/holdings/candidates/AI/audit surfaces are readable.
- PASS: no visible order-execution control was introduced.

## 6. Remaining Risk

This Go-Check proves the local production-built dashboard UI correction only. It
does not redeploy the running `5000` frontend, does not re-run external Gemini
review, and does not change operational trading readiness.

