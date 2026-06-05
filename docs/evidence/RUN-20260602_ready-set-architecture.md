---
schema_version: hwi.evidence/v0
id: RUN-20260602-ready-set-architecture
type: evidence
name: Ready-Set architecture pass
stage: ready-set
environment: docs_only
status: needs_input
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
implementation_ready: false
---

# Ready-Set Architecture Pass

## 1. Scope

This docs-only Ready-Set pass normalized the hwiStock operating skeleton after
brainstorming:

- 24h news/disclosure collection and hourly DeepSeek Pro analysis.
- 08:00-19:00 market-regime analysis add-on.
- 06:50 GPT Pro prompt generation from overnight analysis artifacts.
- 07:00 ChatGPT Pro morning review via browser automation, with DeepSeek-only
  fallback after cutoff.
- DeepSeek Flash intraday candidate/chart/risk labels.
- Deterministic condition compiler, trading engine, and order state machine.
- 20:00 daily close report using system-calculated PnL plus AI interpretation.
- Read-only dashboard/operator console, with `agy` + Gemini Pro design route.
- KIS direction, future official broker-adapter API verification, and
  10,000,000 KRW broker-adapter starting budget.
- Starting capital remains 2,000,000 KRW cash.
- Minimal first-pass risk policy: minimum cash reserve ratio 0.25, maximum
  simultaneous holdings 5, and AI-assisted per-entry stop price capped by
  deterministic maximum -5% loss rules.
- MyWebTemplate may be reused for code skeleton patterns only; its docs are not
  copied.

## 2. Updated / Added Documents

Updated:

- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/index.md`
- `docs/modules/HWISTOCK-MOD-001_trading-safety-core.md`
- `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`
- `docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md`
- `docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md`
- `docs/units/HWISTOCK-UNIT-002_home-server-adapter-runner.md`
- `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md`
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/units/HWISTOCK-UNIT-005_ai-orchestration-layer.md`
- `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md`
- `docs/qa/QA-HWISTOCK-UNIT-002_home-server-adapter-runner.md`
- `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md`
- `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md`
- `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md`
- `docs/evidence/RUN-20260602_unit-005-ai-orchestration-layer-set.md`
- `docs/evidence/RUN-20260602_unit-004-strategy-risk-rulebook-set.md`
- `docs/evidence/RUN-20260602_unit-002-home-server-adapter-runner-set.md`
- `docs/evidence/RUN-20260602_unit-007-dashboard-operator-console-set.md`
- `docs/evidence/RUN-20260602_project-bootstrap.md`

Added:

- `docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md`
- `docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md`
- `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md`
- `docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md`
- `docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md`
- `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md`
- `docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md`
- `docs/qa/QA-HWISTOCK-UNIT-009_kis-api-portal-verification.md`
- `docs/evidence/RUN-20260602_unit-006-trading-engine-order-state-set.md`
- `docs/evidence/RUN-20260602_unit-001-project-bootstrap-set.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`
- `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`

## 3. Ready-Set Status

`implementation_ready: false`

The local module/unit/QA inventory is complete, but Go must not start yet. The
current docs still need strategy decision-packet approval or exclusion,
dashboard design review execution or exclusion, row-closure blockers to close,
and current final external review before full implementation.

## 4. Proposed Go-Check Queue

This is a draft queue, not yet approved for Go. The authoritative current row
matrix is `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`:

| order | unit | status | reason |
| --- | --- | --- | --- |
| 1 | `HWISTOCK-UNIT-001_project-bootstrap` | set | docs-only bootstrap/profile safety contract closed |
| 2 | `HWISTOCK-UNIT-008_data-evidence-storage` | set | PostgreSQL storage, hwiStock DB/schema isolation, and artifact contract closed locally; final external review pending |
| 3 | `HWISTOCK-UNIT-003_market-intelligence-ingestion` | set | source allowlist closed for first Go; DART approved, Naver conditional, KRX/KIND conditional, KIS deferred, HTML scraping blocked; final external review pending |
| 4 | `HWISTOCK-UNIT-009_kis-api-portal-verification` | set | Official docs/samples and local `apiRefer` files confirm KIS endpoint families; no broker network call is allowed |
| 5 | `HWISTOCK-UNIT-004_strategy-risk-rulebook` | set/blocking | reserve-floor/holdings/AI stop and one-week pass criteria closed; first-pass strategy defaults are packaged for approval |
| 6 | `HWISTOCK-UNIT-006_trading-engine-order-state` | set | condition/order-state contract and calendar source closed locally; final review pending |
| 7 | `HWISTOCK-UNIT-005_ai-orchestration-layer` | set | AI job registry and schemas closed with AI network disabled; final external review pending |
| 8 | `HWISTOCK-UNIT-002_home-server-paper-runner` | set | systemd runner lifecycle, calendar source, local alert channel, and one-week pass criteria closed locally; final review pending |
| 9 | `HWISTOCK-UNIT-007_dashboard-operator-console` | set/blocking | dashboard contract closed; dashboard design review packet is prepared and `agy` Gemini Pro design review still blocks dashboard Go |

## 5. Set Questions To Close Next

1. Stack: closed by `docs/evidence/RUN-20260602_stack-rule-preset-set.md`.
   Selected stack is Python 3 + FastAPI backend/API/trading runner,
   TypeScript + Next.js/React read-only dashboard, PostgreSQL storage, and
   active HWI presets `fastapi-backend-rule-preset`,
   `next-frontend-rule-preset`, and `db-naming-rule-preset`.
2. Storage: closed after this pass by `HWISTOCK-UNIT-008` Set direction:
   PostgreSQL database `hwistock`, schema `hwistock_core`, plus
   date-partitioned artifacts. See
   `docs/evidence/RUN-20260602_unit-008-data-evidence-storage-set.md`.
3. KIS official portal pass: closed for docs-only Set by
   `docs/evidence/RUN-20260602_unit-009-kis-api-portal-verification-set.md`.
   KIS domestic order/account/realtime endpoint families, adapter-mode separation,
   and NXT/SOR routing fields are documented. Local `apiRefer` files add a KIS
   API capability matrix showing adapter-supported, adapter-constrained,
   adapter-unsupported, fallback, and runtime-verification behavior. Adapter balance
   and exact current limits remain future broker-network smoke items. NXT/SOR
   broker behavior cannot be adapter-proven by the current KIS references.
4. Minimal risk values: closed for the first docs pass. Maximum simultaneous
   holdings is 5. Position sizing has no fixed per-symbol cap; every order must
   preserve `minimum_cash_reserve_ratio = 0.25` of total capital. Stop policy is
   AI-assisted per entry, with deterministic validation capped at maximum -5%
   loss.
5. AI schedule/schema/cutoff/fallback: closed for first pass by
   `HWISTOCK-UNIT-005` Set. AI network remains disabled by default, with
   nonzero token/cost caps deferred to a future approved provider-pricing check.
6. Source allowlist: closed for first Go by
   `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`; DART approved, Naver news API
   conditional, KRX/KIND conditional, KIS broker data deferred, general HTML
   scraping blocked by default. Long-term retention remains a later storage
   policy question.
7. Condition schema and KIS broker-adapter reconciliation model: closed for first pass by
   `HWISTOCK-UNIT-006` Set. See
   `docs/evidence/RUN-20260602_unit-006-trading-engine-order-state-set.md`.
8. Dashboard access and first-screen sections: closed by
   `docs/evidence/RUN-20260602_unit-007-dashboard-operator-console-set.md`.
   Default access is local-only `127.0.0.1` through local browser, SSH tunnel, or
   Chrome Remote Desktop. Public/LAN exposure requires later authenticated Set
   approval. First screen is the operator console, not a landing page.
9. Home-server process manager: closed by
   `docs/evidence/RUN-20260602_unit-002-home-server-adapter-runner-set.md`.
   `systemd` is selected for the official one-week adapter-backed evidence
   runner; tmux/screen/manual shell is early-experiment-only.
10. Market calendar, alert channel, and one-week adapter-backed pass criteria:
    closed by
    `docs/evidence/RUN-20260602_calendar-alert-operation-gate-set.md`. Runtime uses
    local cached KRX/NXT calendar from official sources, first-pass alerts are
    local-only, and the operation gate is safety/evidence based with no profit
    threshold.

## 6. External Review Status

- ChatGPT Pro / GPT collaboration: not run in this pass.
- Gemini Pro dashboard design via `agy`: not run in this pass.
- Reason: current pass normalized local docs and did not yet share project
  context externally. External review should be requested once the Set question
  packet is ready and sharing scope is approved.

## 7. Verdict

Ready-Set skeleton: PASS

Implementation readiness: BLOCKED

Blocking condition: Ready-Set row-closure blockers remain and current final
external review has not run. No product code, broker network call, AI network
call, or dashboard implementation should start until the completion report marks
`implementation_ready: true`.
