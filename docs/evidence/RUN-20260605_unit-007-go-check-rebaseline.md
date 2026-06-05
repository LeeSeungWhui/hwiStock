---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-unit-007-go-check-rebaseline
stage: go-check
unit_id: HWISTOCK-UNIT-007
status: pass
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md
module_refs:
  - docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md
preflight_ref: docs/evidence/RUN-20260605_unit-007-go-preflight-rebaseline.md
created_at: 2026-06-05
environment: local_only
route_class: implementation_worker
route: cursor-sdk-local
adapter: cursor-sdk-local
model: composer-2.5
reasoning: medium
orchestration_gate_ids:
  - DG-HWISTOCK-UNIT-007-DOC-SYNC-20260605-001
---

# UNIT-007 Go-Check Evidence — Rebaseline

## 1. Verdict

PASS. `HWISTOCK-UNIT-007` now has current-authority local read-only dashboard
operator console foundation in the imported `frontend-web` tree.

Validated scope includes read-only operator console surfaces, dashboard
tasks/settings subroutes, root/public/sample quarantine, masked/sanitized value
display, and local-only/public exposure boundary enforcement.

This closure does **not** authorize buy/sell controls, broker/KIS/API calls,
AI-provider runtime calls, browser/screenshot/server smoke, public/LAN dashboard
exposure, operational trading readiness, or one-week adapter-backed proof.

## 2. Worker / Failure History

| worker | transcript | result | note |
| --- | --- | --- | --- |
| initial first-screen Cursor SDK | `/tmp/hwistock-unit007-cursor/run.jsonl` | quarantined | Wrapper `scope_violation` due allowed-writes glob parsing and command drift; output not directly accepted. |
| follow-up audit worker | `/tmp/hwistock-unit007-cursor-followup/run.jsonl` | accepted | Audit closure accepted by orchestrator. |
| dashboard subroute worker | `/tmp/hwistock-unit007-dashboard-subroutes/run.jsonl` | accepted | Tasks/settings subroutes implemented. |
| rule-gate fix dry-run | n/a | blocked | `MODE: SCOPED_IMPL/PATCH_ONLY` was invalid in contract. |
| rule-gate fix actual run | `/tmp/hwistock-unit007-dashboard-rulegate-fix/run.jsonl` | quarantined | Wrapper `scope_violation` due semicolon `ALLOWED_WRITES` parsing; output not directly accepted. |
| rule-gate acceptance worker | `/tmp/hwistock-unit007-dashboard-rulegate-acceptance/run.jsonl` | accepted | UNIT-007 scoped rule-gate acceptance recorded. |
| public-surface quarantine worker | `/tmp/hwistock-unit007-public-surface-quarantine/run.jsonl` | accepted | Root/public/sample quarantine and `publicRoutes` boundary recorded. |
| doc-sync worker (this record) | `/tmp/hwistock-unit007-doc-sync/run.jsonl` | accepted | Docs/evidence synchronization only; no product code edits. |

Local direct exceptions recorded outside primary worker transcripts:

- profile label-only patch in `docs/profiles/PROFILE-HWISTOCK.md` for rule-gate
  Route root/Component roots;
- comment-only local patches in dashboard tasks/settings page files;
- final copy/comment cleanup for lingering `/component` footer link and
  template-name comments.

No Codex multi-agent, DeepSeek/Kimi multi-agent, MoonBridge, browser, KIS,
broker, server, DB, deploy, package install, or git mutation route was used for
this doc-sync closure.

## 3. Implemented Scope (Prior Workers)

Bounded frontend surfaces validated for Go-Check:

- read-only operator dashboard (`frontend-web/app/dashboard/`)
- dashboard tasks and settings subroutes
- `MaskedValue` and sanitized error rendering
- middleware quarantine for `/sample`, `/component`, `/portfolio`, `/signup`,
  `/forgot-password`
- `publicRoutes` limited to `["/login"]`
- root redirect to dashboard operator console, not a public landing page

## 4. QA Row Coverage

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | No direct buy/sell or order-placement UI in dashboard views/tests. |
| QA-002 | pass | Masked/sanitized sensitive values; no raw credential/account exposure in reviewed surfaces. |
| QA-003 | pass | Operator console shows holdings, PnL, candidates, AI reports, logs, and health panels. |
| QA-004 | pass | Historical `agy` Gemini Pro design review preserved; supporting constraint only post-import. |
| QA-005 | pass | Local-only/public boundary enforced via `publicRoutes` and middleware quarantine. |
| QA-006 | pass | AI conversation surface remains read-only over stored reports/sanitized state. |
| QA-007 | pass | First screen is operator console, not landing page. |
| QA-008 | pass | Read-only styling; no execution-primary affordances on filters/tabs/refresh. |
| QA-009 | pass | `MaskedValue` primitive and sanitized error paths for sensitive payloads. |
| QA-010 | pass | Desktop-first three-pane operator layout in dashboard view/tests. |
| QA-011 | pass | AI panel styled as report/explanation thread, not command shell. |

## 5. Validation

Frontend tests:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1 && pnpm --dir frontend-web test -- __tests__/middleware.test.jsx tests/dashboard.view.test.jsx __tests__/dashboardDataStrategy.test.jsx __tests__/dashboardLayoutMeta.test.jsx __tests__/tasksQueryState.test.jsx __tests__/settingsTabQuery.test.jsx
=> 27 files passed, 131 tests passed
=> Node DEP0205 warning only
```

ESLint:

```text
source ./env.sh >/tmp/hwistock-env-source.log 2>&1 && pnpm --dir frontend-web exec eslint middleware.js app/common/config/publicRoutes.js app/page.jsx app/dashboard/lang.ko.js app/dashboard/view.jsx app/dashboard/operatorData.js app/dashboard/components/MaskedValue.jsx app/dashboard/tasks/view.jsx app/dashboard/settings/view.jsx __tests__/middleware.test.jsx tests/dashboard.view.test.jsx __tests__/dashboardDataStrategy.test.jsx __tests__/dashboardLayoutMeta.test.jsx __tests__/tasksQueryState.test.jsx __tests__/settingsTabQuery.test.jsx
=> exit 0
```

Rule-gate (skill script, `next-frontend-rule-preset`):

```text
hwi-rule-gate --all --preset next-frontend-rule-preset --fail-on-warn --json
=> overall status: fail (205 broader imported-baseline findings)
=> UNIT-007 scoped files findings: 0
   - frontend-web/app/dashboard/
   - frontend-web/app/common/config/publicRoutes.js
   - frontend-web/app/page.jsx
```

Public route static scan:

```text
publicRoutes exports only ["/login"]
/sample, /component, /portfolio, /signup, /forgot-password
=> middleware quarantine targets/tests only, not public routes
```

Template/product surface scan:

```text
no user-facing dashboard route to /component
remaining /app/lib/component hits => shared component-library imports, not public component page links
```

Secret marker scan:

```text
no real KIS credential markers
only middleware auth-cookie names access_token/refresh_token
and fake negative-test payload apiKey":"secret-key" / fake account-like string
```

Conflict marker scan:

```text
exact conflict-marker scan => no matches
```

## 6. Remaining Boundaries / Follow-Up

- Broader imported frontend rule-gate baseline still has unrelated findings
  outside UNIT-007 scoped files (205 total in preset run).
- Route files for sample/signup/etc. may physically remain in the tree but are
  quarantined and not public surfaces.
- No browser/screenshot/server smoke was run for this closure.
- No broker/KIS/API/AI-provider call was run for this closure.
- Public/LAN exposure, operational trading readiness, and one-week
  adapter-backed proof remain future approval scopes.
