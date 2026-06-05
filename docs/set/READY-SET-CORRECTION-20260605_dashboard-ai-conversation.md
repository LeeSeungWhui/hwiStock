---
schema_version: hwi.ready-set-correction/v0
id: READY-SET-CORRECTION-20260605-dashboard-ai-conversation
stage: ready-set
status: corrective_set_issued
project_root: /data/workspace/My/hwiStock
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-05
updated_at: 2026-06-05
unit_refs:
  - docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md
module_refs:
  - docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md
qa_refs:
  - docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md
supersedes_interpretation_refs:
  - docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md
---

# Ready-Set Correction — Dashboard AI Conversation

## 1. Owner Intent

The dashboard must support both:

- viewing stored AI reports such as DeepSeek Pro hourly analysis and DeepSeek
  Flash trade documents; and
- asking the AI questions from the dashboard about stored reports, current
  dashboard state, candidates, positions, market intelligence, and audit logs.

The second capability is an interactive conversation feature. A static report
thread or `aiThread` card list is not enough.

## 2. Correction Finding

The prior UNIT-007 browser re-Prove should be interpreted as a partial browser
rendering/report-viewer proof only. It proved that:

- the login surface and dashboard could render through the local tunnel;
- the dashboard no longer showed the prior API 500;
- static AI/report cards could be displayed read-only; and
- direct order controls were not visible.

It did not prove:

- a dashboard question input;
- a backend AI conversation endpoint;
- a grounded answer/refusal flow;
- unsafe request refusal behavior; or
- conversation audit logging.

Therefore `browser_prove_passed` / `prove_status: pass` is no longer a valid
status for the full AI conversation scope.

## 3. Corrected Ready-Set Scope

The next UNIT-007 Go scope must add or prove:

1. **AI report viewer**
   - Stored Pro/Flash reports remain readable as cards/list/detail.
   - Report viewing must not require starting a conversation turn.

2. **AI conversation UI**
   - Dashboard includes a question input and submit affordance.
   - The UI clearly communicates that answers are read-only explanations.
   - The UI must not resemble a command shell or order-entry control.

3. **AI conversation backend**
   - A backend endpoint accepts a sanitized operator question.
   - The backend builds context only from stored reports, candidate cards,
     sanitized operator snapshot/state, market intelligence, and audit summaries.
   - The frontend never calls AI providers directly.

4. **Safety/refusal**
   - Requests to place orders, cancel orders, change risk settings, reveal
     credentials, edit prompts/models, enable adapters, or control service
     lifecycle are refused with a visible explanation.
   - Missing provider availability must produce a safe refusal/fallback response,
     not a hidden pass.

5. **Auditability**
   - Conversation logs include request id, sanitized question metadata, context
     refs, answer/refusal result, route/model/provider metadata when available,
     latency, and no credentials/raw secret values.

## 4. Corrected QA Gate

`QA-HWISTOCK-UNIT-007` is corrected so that conversation unavailable, missing
input, missing backend endpoint, or report-only AI panel is `FAIL`/`BLOCKED`, not
`PASS`.

The previous phrase "refused or unavailable" is superseded. Unavailable is not
an acceptable PASS condition for the owner-required conversation feature.

## 5. Boundary

This correction is docs-only. It does not implement UI or backend code, does not
call AI providers, does not call broker/KIS endpoints, does not place orders,
does not restart services, and does not approve public/LAN exposure.
