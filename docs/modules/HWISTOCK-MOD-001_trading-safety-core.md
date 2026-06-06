---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-001
type: module
domain: fullstack
name: Trading safety core
spec_status: set
build_status: pending_implementation
verification_status: go_check_passed
ready_set_rebaseline_status: go_check_passed
priority: P0
source_of_truth: user_intent
legacy_ids: []
source_coverage:
  inventory_ref: docs/index.md
  ledger_ref: none
  preservation_status: not_applicable
  coverage_ref: none
completeness:
  status: sufficient
  audit_ref: docs/units/HWISTOCK-UNIT-001_project-bootstrap.md
owner: hwi
updated_at: 2026-06-05
last_verified_at: 2026-06-04
source_inputs:
  - kind: user_prompt
    path_or_url: "주식자동매매단타프로젝트"
    confidence: medium
  - kind: user_prompt
    path_or_url: "프로그램은 24시간 계속 돌리고 테스트 기간은 운영자가 정한다"
    confidence: high
  - kind: user_prompt
    path_or_url: "현금으로 한다 / 총자금은 200만원"
    confidence: high
  - kind: user_prompt
    path_or_url: "KIS로 간다 / 어댑터투자 초기예산 1000만원"
    confidence: high
  - kind: url
    path_or_url: "https://global.krx.co.kr/contents/GLB/06/0606/0606030101/GLB0606030101T3.jsp"
    confidence: high
  - kind: url
    path_or_url: "https://www.nextrade.co.kr/"
    confidence: medium
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
design_refs: []
code_paths:
  - backend/
  - frontend-web/ (planned)
  - ops/systemd/
entrypoints:
  - backend/server.py
  - /api/v1/hwistock/runner/status
  - backend/service/HwiStockRunnerService.py --once
  - ops/systemd/
interfaces: []
links:
  - PROFILE-HWISTOCK
---

# Trading Safety Core

## 1. Purpose

This module owns the durable safety contract for `hwiStock`: no account-affecting
automation, brokerage access, or order placement is allowed until the
project has explicit approval gates, adapter-backed evidence, credential safety,
risk limits, auditability, and an operator-selected adapter-backed observation
window with named evidence.
The trading direction is short-term day trading (`단타`) with cash-only capital.
Initial starting capital is 2,000,000 KRW cash, and all-in single-stock
deployment is forbidden by default.

## 2. User Value / Representative Scenarios

- As the project owner, I can explore automated day-trading ideas without
  accidentally placing real orders.
- As the project owner, I can distinguish research, backtest, adapter-backed, and
  operation environments.
- As a reviewer, I can inspect why a signal would or would not become an order.
- As an operator, I can stop automation through a documented kill switch before
  risk escalates.
- As the project owner, I can run the program continuously on a home server while
  keeping Codex out of the runtime loop.
- As the project owner, I can run market-intelligence ingestion 24 hours while
  keeping trading/order loops restricted to KRX/NXT market sessions.

## 3. Scope

### Included

- Environment separation: docs/backtest/adapter-backed/read-only broker-adapter/operation-order.
- Minimal risk-control contract: minimum cash reserve floor, maximum
  simultaneous holdings, entry-price-based stop-loss, and kill switch.
- Cash-only capital contract: no credit, margin, 미수, borrowed funds, or
  leveraged capital by default.
- Starting capital and allocation contract: initial capital is 2,000,000 KRW
  cash; all-in single-stock deployment is blocked by default.
- Credential-safety contract.
- Auditability for signals, decisions, orders, rejects, and failures.
- Evidence requirements before implementation and before account-affecting operation.
- Operator-selected adapter-backed observation gate before actual account-affecting operation.
  The runner is continuous; the observation period is not hardcoded into the
  program.
- 24-hour home-server runtime safety expectations: restartability, health
  checks, audit logging, and kill switch.
- Market-session gating for Korea domestic stocks is investment-mode aware.
  Paper/mock mode routes new KRX investment/order decisions only during
  09:00-15:00 KST and rejects NXT broker branches. Future live mode may use the
  08:00-20:00 KST KRX/NXT envelope only where KIS capability flags and a later
  approved unit prove support.
- Branch separation: 24-hour information ingestion must not directly place
  orders; it can only publish normalized signals/events for later strategy/risk
  evaluation.
- AI orchestration separation: AI API outputs must not directly place orders,
  call broker interfaces, or override deterministic risk/capital/kill-switch
  controls.
- Broker/API provider direction is Korea Investment & Securities Open API
  (`KIS`, 한국투자증권). KB Securities (`KB증권`) is treated as not usable for this
  personal-account automation project unless a future official confirmation
  proves otherwise. Internal fake broker execution is not used. The first
  broker-backed execution path is KIS KRX broker-adapter. The first
  bounded KIS broker-adapter REST and WebSocket smoke was owner-approved and passed
  on 2026-06-04; ordinary Go rows still require an explicitly scoped approval
  before any additional broker/KIS network call or broker order.

### Excluded

- Specific signal rules and exact timeframe.
- Credit, margin, 미수, borrowed funds, or leveraged-capital trading.
- Broker/API implementation.
- Additional KIS/external broker network calls outside an explicitly scoped
  approved unit. Official KIS broker-adapter APIs are the first
  broker-backed path, not an internal fake broker replacement; the completed
  bounded smoke does not authorize unscoped future calls or broker orders.
- UI/dashboard implementation.
- Account-affecting trading.
- Skipping the operator-selected adapter-backed observation and explicit
  go/no-go approval.
- Profit expectation or financial recommendation.

## 4. Product / Capability Contract

- Default mode is no brokerage operation.
- Default capital mode is cash-only. Any credit, margin, 미수, borrowed-fund, or
  leveraged-capital path is forbidden unless a future approved unit explicitly
  changes the profile.
- Default starting capital is 2,000,000 KRW cash. Any strategy/risk engine must
  enforce the allocation and loss limits in `HWISTOCK-MOD-003` before it can
  emit an order decision.
- All-in single-stock deployment is forbidden by default.
- Any order-placement path must be disabled unless the active unit explicitly
  approves the environment and evidence requirement.
- Default Go behavior remains no-order dry-run validation: it may record
  candidate, risk, and order-intent decisions, but it must not simulate broker
  fills or balances. The first broker-backed order path is KIS KRX broker-adapter
  investment, and the owner-approved 2026-06-04 smoke proved only a bounded
  token/quote/balance/buyable/adapter-order/cancel/daily-order/WebSocket ACK path.
  Any additional KIS token/account/balance/quote/realtime/order/modify/cancel/
  WebSocket call, broker order, or adapter integration still requires the active
  unit to explicitly approve scope, credentials handling, endpoint separation,
  personal-account eligibility, KRX/NXT/SOR support boundaries, and adapter safety
  gates. The official broker-adapter starting budget is 10,000,000 KRW
  and must not change the intended 2,000,000 KRW operation starting-capital policy.
- Account-affecting operation must remain disabled until the operator-selected
  adapter-backed observation window has named evidence and an explicit user
  go/no-go approval.
- The trading runner must be an independently restartable home-server service or
  process. Codex sessions must not be required for the program to keep running.
- The runner must separate service uptime, 24-hour information ingestion, and
  trading-session activity. A running service outside the configured KRX/NXT
  trading session must not attempt order routing.
- Strategy outputs must be treated as hypotheses until proven by named evidence.
- AI outputs are recommendations or explanations only. They must pass through
  deterministic policy gates before any order decision can exist.
- Credentials must not be committed, printed, or stored in docs.
- Every future trading decision path must expose enough audit data to reconstruct
  input signal, risk decision, order decision, and outcome.

## 4-1. Contract Surface Map

| surface | names / paths / ids | behavior owned | out of scope | evidence needed |
| --- | --- | --- | --- | --- |
| profile | `docs/profiles/PROFILE-HWISTOCK.md` | approval and evidence policy | unapproved provider change | doc review |
| module | `HWISTOCK-MOD-001` | safety and risk contract | strategy tuning | doc review |
| capital | cash-only | no leverage by default | credit/margin/미수 | config + order review |
| unit | `HWISTOCK-UNIT-001` | bootstrap readiness | code implementation | file list + doc review |
| environment | docs/backtest/adapter-backed/operation | environment labels and gates | account-affecting order execution | QA scenario |
| test gate | operator-selected adapter-backed observation window | operation-readiness prerequisite; not runner duration | shortcut approval or hardcoded period | evidence summary |
| runtime | home-server runner | 24h service health/restart/kill switch | Codex-as-runtime | service smoke evidence |
| scheduler | Korea market routing calendar | paper/mock 09:00-15:00 KRX-only order window; future live starts `krx_only`; NXT requires separate approval/Ready-Set | extra session-mode split | calendar smoke evidence |
| information branch | news/disclosure ingestion | 24h collection and normalization | direct order placement | source/evidence logs |
| strategy/risk rulebook | `HWISTOCK-MOD-003` | stock filters, cash-reserve and holdings checks, exits, minimal stop policy | profit promises and broad account-level loss automation by default | adapter/backtest evidence |
| AI orchestration | `HWISTOCK-MOD-004` | candidate synthesis and structured recommendations | direct broker/order control | schema + policy-gate evidence |
| broker direction | `KIS`, no-order dry-run, KIS adapter API | KIS selected; KB blocked for personal use; internal fake broker execution is not used; first broker-backed execution is approved KIS KRX broker-adapter under scoped evidence | unscoped KIS/external broker or broker-provided broker-adapter/operation network calls outside an approved unit | broker-selection evidence + dry-run smoke + KIS portal verification + KIS broker-adapter smoke |

## 5. Interfaces

No code interfaces exist yet.

Future interfaces may include:

- broker adapter
- no-order dry-run decision recorder
- KIS official broker-adapter adapter
- future KIS operation adapter
- market data adapter
- strategy engine
- risk engine
- order router
- audit log
- dashboard
- strategy/risk rulebook config
- AI orchestration adapter

## 6. State / Data / Permission Rules

- Operation credentials and account data are out of scope until approved.
- Future runtime state must distinguish no-order dry-run intents, approved KIS
  broker orders, and future account-affecting orders.
- Pre-approval dry-run state must distinguish draft order intents, risk-approved
  intents, rejected intents, and kill-switch blocks without broker order ids,
  fills, positions, balances, or simulated PnL.
- KIS adapter credentials may exist only in the local external secret file
  `/home/hwi/.config/hwistock/hwistockApi.env` for approved broker-adapter work and
  must not be committed, printed, or copied into docs. Operation credentials, account
  data, tokens, partner endpoints, and any broker-provided operation mode remain out
  of scope until a later approved integration unit.
- Future audit data must avoid leaking credentials or private account details.
- AI API calls must avoid credentials, account identifiers, private account
  details, and unapproved raw article bodies.

## 7. Existing Assets / Reuse Points

- Hwi Work Harness templates and lifecycle.
- Imported MyWebTemplate backend/frontend skeletons are present and must remain
  quarantined/replaced per unit scope.
- UNIT-002 now provides the first hwiStock-specific safety runtime skeleton:
  local-only bind helper, read-only runner status API, no-order intent metadata,
  audit/alert metadata, `--once` runner tick, focused tests, and systemd
  templates.

## 8. Module-Level Verification

- Bootstrap docs exist.
- Profile requires approval for broker operations.
- QA scenario checks that no implementation claims operation readiness.

## 9. Included Units

- `HWISTOCK-UNIT-001`: project bootstrap and safety-first planning setup.
- `HWISTOCK-UNIT-002`: 24-hour home-server adapter-backed runner skeleton,
  local-only status API, no-order metadata, and systemd templates.
- `HWISTOCK-UNIT-003`: 24-hour market intelligence ingestion planning.
- `HWISTOCK-UNIT-004`: strategy/risk rulebook planning for stock selection,
  position sizing, exits, and kill switch.
- `HWISTOCK-UNIT-005`: AI orchestration planning for structured recommendations
  and no-direct-order safety gates.
- `HWISTOCK-UNIT-006`: trading engine, condition compiler, order state,
  no-order dry-run, and KIS broker adapter boundary planning.
- `HWISTOCK-UNIT-007`: read-only dashboard/operator console planning.
- `HWISTOCK-UNIT-008`: data/evidence storage and report artifact planning.
- `HWISTOCK-UNIT-009`: KIS official API portal verification planning.
- `HWISTOCK-UNIT-010`: continuous KIS broker-adapter runner planning.
- `HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE`: calendar, alert, and
  operator-controlled adapter-backed observation criteria policy.

## 10. Decisions / Open Contract Questions

- Decision: start safety-first; no account-affecting orders by default.
- Decision: actual account-affecting operation requires an operator-selected adapter-backed
  observation window with named evidence before user go/no-go approval. The
  runner must not hardcode that duration.
- Decision: the 24-hour runtime target is a home-server program/service, not a
  Codex session.
- Decision: Korea domestic stocks are the first market scope, and 24-hour service
  uptime must be separated from market-session trading activity.
- Decision: runtime has two branches: 24-hour market intelligence ingestion and
  investment-mode-aware trading/order routing. Paper/mock mode is KRX-only
  09:00-15:00 KST for new investment/order decisions; future live mode starts
  `krx_only`; NXT venue routing requires separate owner approval and Ready-Set.
- Decision: strategy direction is short-term day trading (`단타`).
- Decision: capital policy is cash-only; credit, margin, 미수, borrowed funds, and
  leveraged capital are forbidden by default.
- Decision: starting capital is 2,000,000 KRW cash.
- Decision: all-in single-stock deployment is forbidden by default.
- Decision: AI API orchestration may be explored only as an analysis layer; AI
  cannot directly place orders or bypass deterministic risk gates.
- Decision: Korea Investment & Securities Open API (`KIS`) is the selected
  broker/API direction.
- Decision: KB Securities (`KB증권`) is blocked as a practical personal API
  candidate unless future official confirmation proves otherwise.
- Decision: internal fake broker execution is not used. Default Go behavior is
  still no-order dry-run validation unless the active unit explicitly approves
  a bounded KIS broker-adapter action.
- Decision: broker-provided broker-adapter/demo/testbed/adapter APIs are deferred by
  default, not generally forbidden. The first bounded KIS KRX broker-adapter REST
  and WebSocket smoke was approved and passed on 2026-06-04; future integration
  or additional calls remain scoped-approval work.
- Decision: official broker-adapter initial budget is 10,000,000 KRW;
  intended starting capital remains 2,000,000 KRW cash.
- Decision: first-pass market calendar source hierarchy is KRX official
  trading-days/holidays and notices, NXT official session references, local
  cached calendar for runtime, and later KIS `국내휴장일조회` only after approved
  broker-network integration.
- Decision: first-pass alerting is local-only through systemd journal,
  `data/alerts/YYYY-MM-DD/alerts.jsonl`, dashboard audit/error panel when
  implemented, and daily close report.
- Decision: adapter-backed observation criteria are operator-controlled. Evidence
  must record observation-window start/end/duration metadata, covered market
  days, P0 safety/evidence criteria, and no profit threshold.
- Rebaseline Ready-Set completion is closed for the
  `skeleton_sandbox_safe_rebaseline_queue`; remaining restrictions are
  operational, not Ready-Set blockers: no unscoped KIS/broker/AI calls, no adapter
  orders outside approved scope, no account-affecting orders, no credential storage, no
  public/LAN dashboard exposure, no fake broker fills/balances/PnL, no
  MyWebTemplate sample/public exposure without quarantine/replacement, and no
  expected-profit claims.
- Remaining strategy follow-up: the first-pass alpha/chart/source/candle/
  liquidity/market-alert defaults are packaged in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`. They must
  not be inferred during Go before approval or row exclusion.
- Remaining provider follow-up: exact nonzero AI API cost/latency caps and any
  AI network enablement require a future approved provider-pricing check.
- Remaining source follow-up: long-term data retention, backup, and conditional
  source promotion remain future Set items. First Go source allowlist is closed
  by `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`.

## 10-1. Completeness Audit

| coverage_area | status | notes | blocks_unit_set |
| --- | --- | --- | --- |
| source inventory | sufficient | user prompt only, greenfield | no |
| actors and roles | sufficient | owner/operator/reviewer and service branches defined | no |
| entrypoints | sufficient | planned backend health and systemd surfaces listed; no code yet | no |
| behavior contract | sufficient | unapproved-adapter order guard, no-order dry-run, KIS adapter boundary, branch separation, and risk invariants defined | no |
| state and data | sufficient | dry-run, KIS adapter, future operation states and audit boundaries defined | no |
| permissions | sufficient | approval-required operations and credential/broker boundaries defined | no |
| design basis | minimal_exception | no UI yet | no |
| invariants | sufficient | cash-only, no internal fake broker, operator-controlled operation observation gate, AI no-direct-order, and local-only dashboard invariants defined | no |
| verification families | sufficient | docs bootstrap QA plus named future smoke families and operation observation evidence gate defined | no |

## 11. Evidence References

- `docs/evidence/RUN-20260602_project-bootstrap.md`
- `docs/evidence/RUN-20260602_market-session-source-check.md`
- `docs/evidence/RUN-20260602_ai-orchestration-layer.md`
- `docs/evidence/RUN-20260602_broker-selection-kis.md`
- `docs/evidence/RUN-20260602_broker-candidate-kb-blocked.md`
- `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`
- `docs/evidence/RUN-20260604_unit-001-go-preflight.md`
- `docs/evidence/RUN-20260604_unit-001-go-check.md`
- `docs/evidence/RUN-20260604_unit-001-go-preflight-rebaseline.md`
- `docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md`
- `docs/evidence/RUN-20260605_ready-set-continuous-adapter-runner.md`
- `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`

## 12. Design References

- None.
