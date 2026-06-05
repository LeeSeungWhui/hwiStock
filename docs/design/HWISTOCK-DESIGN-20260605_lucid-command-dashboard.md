---
schema_version: hwi.design/v0
id: HWISTOCK-DESIGN-20260605
type: design
domain: frontend
name: Lucid Command operator cockpit
status: active
unit_refs:
  - HWISTOCK-UNIT-007
module_refs:
  - HWISTOCK-MOD-006
owner: hwi
updated_at: 2026-06-05
source: agy_gemini_pro_concept_lucid_command
---

# Lucid Command Dashboard Design

## 1. Concept

**Lucid Command** is the hwiStock read-only operator cockpit for a solo Korean
stock automation operator. It is a dark, desktop-first SaaS/fintech monitoring
surface — not a marketing landing page, not a trading terminal, and not a
command shell that implies order execution.

The operator opens the dashboard to answer one question: *"What is the system
doing right now, and is it safe to trust what I see?"*

## 2. Visual Language

| Element | Direction |
| --- | --- |
| Base palette | Slate 950/900 backgrounds, slate 700 borders |
| Text | Slate 100 primary, slate 400 secondary |
| Accents | Cyan/teal for informational state; amber for warnings; rose for errors |
| Avoid | Purple-blue hero gradients, neon terminal green, red/green trade buttons |
| Density | Desktop-first three-pane layout; mobile deferred |
| Typography | Korean labels; mono for identifiers and numeric values |

## 3. Layout Model

```
┌─────────────────────────────────────────────────────────────┐
│  Global header: title, data source badge, fallback warning  │
├─────────────────────────────────────────────────────────────┤
│  Readiness truth banner (loud, cannot be missed)            │
├─────────────────────────────────────────────────────────────┤
│  Status strip: mode · KST · venue · kill-switch · health   │
├──────────┬────────────────────────┬───────────────────────┤
│  LEFT    │  CENTER                │  RIGHT                │
│  Account │  Holdings table        │  AI 리포트 viewer     │
│  summary │  Candidates watchlist  │  AI 대화 panel        │
│          │  Market intelligence   │  Audit/error timeline │
└──────────┴────────────────────────┴───────────────────────┘
```

### In-page section anchors

Top-level menu concepts map to existing routes where possible:

- **운영 콘솔** — `/dashboard` (this view)
- **감시 로그** — `/dashboard/tasks`
- **운영 정책** — `/dashboard/settings`
- **AI 리포트** — in-page right-pane report viewer (stored Pro/Flash cards)
- **AI 대화** — in-page right-pane conversation panel (separate from report viewer)

## 4. Capability Guardrails

### Must show (operatorSnapshot contract)

- Readiness truth: headline, blockers, data/order/observation gates
- Account summary: masked identifiers, cash, reserve, PnL, positions, risk rejects
- Holdings, candidates, market-intelligence timeline
- KIS/data health, runner/order state via status strip
- Stored AI report viewer (`aiThread` cards)
- Audit/error timeline

### AI report vs AI conversation

| Surface | Purpose | Input |
| --- | --- | --- |
| AI 리포트 viewer | Read stored Pro/Flash/morning/close reports | None (read-only cards) |
| AI 대화 panel | Ask questions about reports and sanitized state | Question textarea + muted submit |

The conversation panel must:

- Show a visible read-only disclaimer (no orders, no config changes)
- Provide question input and submit affordance
- Style as report/mail Q&A thread, not terminal/CLI
- Never use primary trade-action button variants

### Forbidden

- Direct buy/sell/order execution buttons
- Credential or raw API/error JSON display
- Command-console styling for filters, refresh, or conversation controls
- Fake sample data or marketing hero sections

## 5. Component Conventions

- Reuse project `Card`, `Badge`, `Skeleton` with dark `className` overrides
- Use `MaskedValue` or placeholder maps for sensitive tokens
- Severity colors reserved for kill-switch, stale/fallback data, and errors
- Muted outline buttons for non-ordering actions (refresh hint, conversation submit)

## 6. Implementation Mapping

| Design area | Implementation |
| --- | --- |
| Dark shell | `frontend-web/app/dashboard/view.jsx` root `bg-slate-950` |
| Three panes | `xl:grid-cols-12` with 3/5/4 column split |
| Report viewer | `operator-ai-report` card, `snapshot.aiThread` |
| Conversation | `operator-ai-conversation` card, local Q&A state + backend POST |
| Labels | `frontend-web/app/dashboard/lang.ko.js` |
| Data contract | `frontend-web/app/dashboard/operatorData.js` (unchanged shape) |

## 7. Evidence Linkage

- Prior `agy` Gemini Pro review: `docs/evidence/RUN-20260604_dashboard-design-review.md`
- Findings intake: `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md`
- AI conversation correction: `docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md`

## 8. Open Follow-ups (out of this design artifact)

- Backend conversation endpoint prove and audit logging (QA-013 through QA-015)
- Browser/tunnel re-Prove with interactive conversation flow
- Mobile layout (deferred unless a future unit adds scope)
