# hwiStock Docs Index

`hwiStock` is a stock day-trading automation project. The initial project
contract prioritizes safety, observability, adapter-backed validation, and clear
approval gates before any broker adapter integration and account-affecting order flow.
Before account-affecting operation, the project must pass an operator-selected
adapter-backed observation window with named evidence and an explicit user
go/no-go approval. The runtime must not hardcode seven days, one week, or any
other fixed test duration; the operator decides the observation period.
The intended runtime target is a 24-hour home-server program/service, not a
Codex session. Codex is used for planning, implementation, review, and evidence
work; the trading runner must be an independently restartable service.
The first market scope is Korea domestic stocks (`국장`). The runtime has two
separate branches:

- Market intelligence branch: runs 24 hours for news, articles, disclosures, and
  other permitted public information ingestion.
- Trading branch: uses simple session context inside 08:00-20:00 KST with an
  explicit KIS investment-mode gate. Paper/mock mode enables KRX plus integrated
  market-data/account-truth helpers and rejects NXT broker branches; real
  investment mode enables KRX and NXT where KIS capability flags allow it. SOR
  remains disabled until a future approved contract proves it.

Strategy direction is short-term day trading (`단타`) with a fast intraday
scalping/momentum hypothesis: enter only on approved signals, hold roughly
10-20 minutes when the signal remains valid, aim for a per-position candidate
1-5% price move, and exit quickly when the risk plan triggers. The 08:00-20:00
trading envelope is an observation/opportunity window, not permission to trade
continuously. The 1-5% target band means an individual position's
price-move/take-profit candidate; it is not a daily account return target.
Signal design should combine news/disclosure context with chart/market-data
confirmation. News or disclosure alone can create a watchlist candidate, but it
must not directly place an order. Chart movement alone can create a momentum
candidate, but the system should still look for disclosure/news context before
entry whenever possible. AI API orchestration is allowed as a planned research
direction, but only as an analysis/orchestration layer. AI output cannot directly
place orders, override risk limits, or bypass deterministic policy gates.
Capital policy is cash-only: no credit, margin, 미수, borrowed funds, or
leveraged capital by default. Initial starting capital is 2,000,000 KRW cash.
All-in single-stock deployment is forbidden by default.
Broker/API provider direction is now Korea Investment & Securities Open API
(`KIS`, 한국투자증권). KB Securities (`KB증권`) was checked and is treated as not
usable for this personal-account automation project unless a future official
confirmation proves otherwise. hwiStock will not use an internal fake broker
adapter as the first execution path. The first broker-backed execution path is
an approved KIS broker-adapter-investment KRX path. A bounded owner-approved KIS
broker-adapter REST and websocket smoke passed on 2026-06-04, but ordinary Go rows
still run no-order dry-run validation unless a selected unit explicitly scopes
KIS broker-adapter behavior. A 2026-06-05 runtime recheck confirmed current KIS
broker-adapter REST and WebSocket connectivity; the broker order endpoint was called
again but rejected with the adapter-mode market-not-started class because the run
occurred before market open
(`docs/evidence/RUN-20260605_kis-broker-adapter-api-runtime-recheck.md`).
Current-authority UNIT-009 rebaseline Go-Check passed
on 2026-06-04 as docs-only capability verification: the official endpoint
families, adapter-mode separation, and NXT/SOR routing fields are documented in
the capability matrix, with sanitized bounded KIS broker-adapter smoke
cross-referenced for proven KRX adapter paths only. Local KIS references still
constrain broker-adapter proof to the KRX path for several order/realtime APIs.
NXT/SOR remain venue/session parameters in the internal engine and must use
disabled/fallback behavior in KIS-facing operation runs until a later approved
broker-account/support-confirmation gate. The actual adapter balance and exact
current rate-limit numbers still require future account evidence. This closure
does not authorize new KIS/broker/network calls. The
broker-adapter account balance is observed broker evidence only. Risk sizing uses
the hwiStock risk-overlay capital of 2,000,000 KRW unless a future approved
profile/unit change records a different value.

AI orchestration direction is selected at the operating-skeleton planning level,
but the owner-defined runtime target is now precise and file-driven:

1. 24-hour news/disclosure collection from permitted/free public sources.
2. Continuous KIS intraday market-data collection during the approved intraday
   window: current price/quote context, ranking/analysis data, and KRX realtime
   price/orderbook feeds where adapter-supported.
3. DeepSeek Pro runs on the top of every hour, reads accumulated news,
   disclosures, and KIS market-data files, and writes the hourly analysis file.
   During market hours the market-regime/session analysis is part of this Pro
   artifact, not a separate detached subsystem.
4. DeepSeek Flash runs every 10 minutes during market hours, reads the latest
   Pro artifact, the recent 10-minute news/disclosure window, KIS REST ranking
   changes, and current KIS price/orderbook data. It also reads the previous
   trade-document chain and/or current portfolio/order-state snapshot so the new
   document does not conflict with existing holdings, pending orders, active
   exits, cooldowns, or previous still-valid decisions. It writes at most one
   trade document for that 10-minute decision bucket. The document contains at
   most five symbol actions. Each action must include `WAIT_BUY`, `BUY_NOW`,
   `HOLD`, `SELL`, or `NO_TRADE`, entry/take-profit/stop-loss/trailing/cancel
   windows where relevant, sizing cap, source refs, portfolio-conflict status,
   and risk notes.
5. The auto-trading runner watches newly written trade documents and executes
   only deterministic-risk-approved, portfolio-state-compatible KIS KRX
   broker-adapter cash orders.

The orchestrator, not the models, moves data between these systems. AI outputs
create analysis and trade-document artifacts only; deterministic
strategy/risk/order state machines own executable broker-order decisions.

## CURRENT-READINESS — 2026-06-06 KST

| Gate | Status | Meaning | Canonical evidence |
| --- | --- | --- | --- |
| Documentation authority | 🟢 CURRENT | The current operational authority is the 2026-06-05 operational automated-trading Ready-Set. The 2026-06-04 rebaseline files are historical and must not be cited as current operational authority. | `docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md`; `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-automated-trading-program_hwistock.md`; `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-automated-trading-program_hwistock.md` |
| Service observability | 🟡 OBSERVABLE | API, frontend, timers, and runtime artifacts may be active on loopback/systemd, but service activity is not automated-trading readiness. | `docs/evidence/RUN-20260605_unit-011-runtime-start-go.md`; `docs/evidence/RUN-20260606_monday-operation-p0-safety-gates-go-check.md` |
| Data/AI artifact pipeline | 🟡 PARTIAL | Local Go-Check evidence exists for Pro/Flash artifacts, source grounding, KIS mode-aware market data, and fail-closed behavior; provider/network observation still needs scoped evidence. | `docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`; `docs/evidence/RUN-20260606_monday-operation-p0-safety-gates-go-check.md` |
| KIS paper/mock account truth | 🟡 PARTIAL | Supported KIS paper/mock read steps pass in the latest sanitized smoke; provider-unsupported helper TRs are skipped as `skipped_provider_unsupported` and unknown sellable truth is not converted to zero. | `docs/evidence/RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix.md`; `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md` |
| Order submission readiness | ❌ FALSE | Account-affecting order submission is not a current readiness claim. It still requires explicit unit scope, market/session preflight, account truth, adapter guard, idempotency/reconciliation evidence, and operator approval. | `docs/units/HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md`; `docs/evidence/RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix.md` |
| Observation acceptance | ❌ FALSE | No operator-selected market-hours observation window has been accepted as final operational proof. | `docs/units/HWISTOCK-UNIT-015_operator-console-observation-prove.md`; `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md` |

Terminology for the current docs:

- `operational-automated-trading-program` is the canonical current program
  wording. It means file-driven automation and deterministic order-state
  control; it does not imply order-submit readiness.
- `broker-adapter` is the order submission/reconciliation abstraction.
- `KIS paper/mock` is the currently configured KIS investment environment.
  Paper/mock enables KRX plus integrated market-data/account-truth helpers, but
  it does not make unsupported KIS helper TRs available.
- `real investment mode` is a later mode-gated branch for KRX/NXT where KIS
  capability flags and separate proof allow it. SOR remains disabled unless a
  future contract proves it.

## Current Rebaseline Status

Current 2026-06-05 operational automated-trading authority:

- Operational Ready-Set:
  `docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md`
- Operational row closure:
  `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-automated-trading-program_hwistock.md`
- Operational Go preflight:
  `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-automated-trading-program_hwistock.md`
- Operational module:
  `docs/modules/HWISTOCK-MOD-009_operational-automated-trading-program.md`
- Operational unit queue:
  - `docs/units/HWISTOCK-UNIT-011_operational-runtime-supervisor.md`
  - `docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md`
  - `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md`
  - `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
  - `docs/units/HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md`
  - `docs/units/HWISTOCK-UNIT-015_operator-console-observation-prove.md`
- Operational QA scenarios:
  - `docs/qa/QA-HWISTOCK-UNIT-011_operational-runtime-supervisor.md`
  - `docs/qa/QA-HWISTOCK-UNIT-016_runtime-contract-hardening.md`
  - `docs/qa/QA-HWISTOCK-UNIT-012_ai-analysis-runtime.md`
  - `docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
  - `docs/qa/QA-HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md`
  - `docs/qa/QA-HWISTOCK-UNIT-015_operator-console-observation-prove.md`
- Operational Ready-Set evidence:
  `docs/evidence/RUN-20260605_ready-set-operational-automated-trading-program.md`
- UNIT-011 runtime start Go evidence:
  `docs/evidence/RUN-20260605_unit-011-runtime-start-go.md`
- Owner architecture rebaseline evidence:
  `docs/evidence/RUN-20260605_owner-runtime-architecture-10m-trade-document-rebaseline.md`
- GPT Pro external Ready-Set review:
  `docs/evidence/RUN-20260605_gpt-pro-operational-ready-set-review.md`
- UNIT-016 runtime contract Set evidence:
  `docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md`
- Runtime contract documents:
  - `docs/contracts/HWISTOCK-RUNTIME-DATA-EXECUTION-CONTRACTS.md`
  - `docs/contracts/hwistock-runtime-contracts.schema.json`
- Operational UNIT-012 through UNIT-015 local Go-Check evidence:
  `docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`
- Post-Pro corrective UNIT-011/015 Go-Check evidence:
  `docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md`
- Pro runtime safety remediation evidence:
  `docs/evidence/RUN-20260605_pro-runtime-safety-remediation.md`
- Monday operation P0 safety-gate correction:
  `docs/set/READY-SET-CORRECTION-20260606_monday-operation-p0-safety-gates.md`
- Monday operation P0 safety-gate Go-Check evidence:
  `docs/evidence/RUN-20260606_monday-operation-p0-safety-gates-go-check.md`
- KIS mode-gated account-truth Go-Check evidence:
  `docs/evidence/RUN-20260606_kis-mode-gated-account-truth-go-check.md`
- KIS paper token-cache and mock-unsupported TR hotfix evidence:
  `docs/evidence/RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix.md`
- Monday operation local calendar cache:
  `config/market-calendar/krx-nxt-trading-days.json`

Post-Pro reinforcement: this existing operational Ready-Set remains the current
authority; it is not replaced by a parallel Ready-Set. The Pro critique is
folded into the current completion, row closure, preflight, module, unit, and
profile docs as additional readiness-truth requirements.

Current truth after the Pro critique:

- `implementation_ready: true` only for the
  `operational_contract_hardened_go_check_queue`;
- `broker_run_ready: false`;
- `continuous_runner_ready: false`;
- `operational_readiness: false`;
- `broker_runner_ready: false`.

The runtime can be observed through local services, timers, artifacts, the
dashboard, and the operator snapshot API. That is not the same as a validated
automated-trading observation run. Earlier post-Pro operator snapshots reported
`brokerNetworkEnabled: false`, `brokerOrdersSubmitted: false`,
`operationObservationAccepted: false`, `operationalReadiness: false`, and a
blocked `orderGate`. The 2026-06-06 Monday P0 safety gate now separately records
implemented order-gate behavior: date-specific KST calendar rows are required,
Saturday/non-trading days are blocked as `blocked_calendar_non_trading_day`, and
KRX order submission additionally requires `krxOrderSessionOpen=true`.

Corrective reinforcements now attached to the existing queue:

1. `HWISTOCK-UNIT-011`: runtime entrypoint/systemd hardening — local
   Go-Check passed in
   `docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md`.
2. `HWISTOCK-UNIT-015`: dashboard/API readiness truth surface — local
   Go-Check passed in
   `docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md`.
3. `HWISTOCK-UNIT-012`: DeepSeek Pro/Flash timer and artifact truth.
4. `HWISTOCK-UNIT-013`: source/calendar/KIS mode-aware market-data readiness
   without order submission.
5. `HWISTOCK-UNIT-014`: bounded KRX broker order/reconciliation smoke only after
   explicit approval and market/session preflight.

Latest operational Go-Check update: UNIT-012 through UNIT-015 passed local
no-network Go-Check for the owner-selected NAVER/OpenDART + KIS mode-aware
market-data scope. Provider network smoke, KIS broker adapter-read transport, KIS KRX adapter
order/reconciliation smoke, browser/tunnel Prove, and final operator
observation-window acceptance remain blocked until explicitly scoped. Therefore
`broker_run_ready: false`, `continuous_runner_ready: false`, and
`operational_readiness: false` remain current.

Correction: `HWISTOCK-UNIT-010` is a KIS broker adapter runner foundation and local
no-network implementation proof, not the whole stock-trading program. The
current operational architecture queue for an actually runnable automated trading
program is UNIT-011, UNIT-016, and UNIT-012 through UNIT-015. UNIT-016 has now
closed the blocking contract-hardening Set gate with schema catalog, fixtures,
and validator evidence. UNIT-012/013 are responsible for the Pro-hourly,
Flash-10-minute, KIS-market-data, and trade-document bridge. Current status is
`go_check_passed_local_no_network_with_side_effect_rows_blocked` only for the
contract-hardened Go-Check queue. Until the side-effect rows pass Go/Check/Prove,
`broker_run_ready: false`, `continuous_runner_ready: false`, and
`operational_readiness: false` remain the correct status.

Prior GPT Pro review correction: the 2026-06-05 external review classified the
architecture as solid in intent but not implementation-ready until runtime
contracts existed. UNIT-016 now provides those Set-level contracts:
machine-checkable schemas, deterministic ids, atomic artifact publication,
`NO_TRADE` sentinel behavior, executor locks, reservation accounting, order
state machine, freshness TTLs, ambiguous-submit reconciliation, adapter-only
guard, fixtures, and local validation.

Post-Pro correction: after a later Pro critique of the current repository state,
the project reinforced the existing operational Ready-Set instead of replacing
it. Service/timer activity, local tests, and visible dashboards cannot be cited
as operation readiness until the existing operational queue's side-effect rows
and observation gate are proved.

Runtime start update: on 2026-06-05 UNIT-011 Go started the user systemd runtime
bundle. API and frontend are running on loopback ports 5001 and 5000. Five
hwiStock timers are active/waiting: market intelligence, DeepSeek analysis,
runner evidence, KIS broker adapter health, and KIS broker adapter continuous runner. DeepSeek Pro
analysis and KIS broker adapter read/reconciliation ticks produced successful sanitized
evidence. DeepSeek timer activity means the local analysis job/timer is installed
and produces sanitized runtime evidence when provider/config prerequisites are
available; it does not imply order readiness. KIS broker adapter cash order
submission remains disabled by the default user systemd runner and additionally
requires an operator approval file plus matching approved order run id before
the runner can submit any cash order. The order gate remains blocked by missing
calendar/source configuration.

Follow-up Pro review fail-closed remediation on 2026-06-05 tightened
paper-order approval/calendar/source requirements, required `paper_only` and the
`kis_paper` broker adapter for submit-path intents, clarified the FIFO intent
queue as `next_intent_queue_fifo`, propagated service-policy contradictions into
AI conversation readiness, and recorded the loopback/frontend-BFF AI access
invariant. Evidence:
`docs/evidence/RUN-20260605_pro-review-fail-closed-followup.md`.

Superseded narrow UNIT-010 correction set:

- Narrow Ready-Set target:
  `docs/set/READY-SET-COMPLETION-20260605_continuous-adapter-runner_hwistock.md`
- Narrow row closure:
  `docs/set/READY-SET-ROW-CLOSURE-20260605_continuous-adapter-runner_hwistock.md`
- Narrow Go preflight:
  `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_continuous-adapter-runner_hwistock.md`
- Narrow module/unit/QA:
  - `docs/modules/HWISTOCK-MOD-008_continuous-adapter-runtime.md`
  - `docs/units/HWISTOCK-UNIT-010_kis-adapter-continuous-runner.md`
  - `docs/qa/QA-HWISTOCK-UNIT-010_kis-adapter-continuous-runner.md`
- Narrow evidence:
  `docs/evidence/RUN-20260605_ready-set-continuous-adapter-runner.md`
- Narrow correction: the next runner foundation was a **24-hour continuous KIS
  broker-adapter runner**, not a fixed seven-day program. The project owner/operator
  chooses the adapter-backed observation window. The program must not auto-stop,
  auto-pass, or auto-fail based on a hardcoded duration. Whole-program
  operational readiness is now governed by the UNIT-011, UNIT-016, and
  UNIT-012 through UNIT-015 queue above.
- Narrow UNIT-010 readiness: `HWISTOCK-UNIT-010` local no-network Go-Check has passed.
  The continuous KIS broker adapter runner code exists and later UNIT-011 evidence shows
  service-managed runtime startup, but `broker_run_ready: false`,
  `continuous_runner_ready: false`, and `operational_readiness: false`
  remain for the operational program because order-producing Go rows, broker
  order evidence, and operator observation-window Prove have not closed.

The current code baseline changed on 2026-06-04 when MyWebTemplate-derived
`backend/` and `frontend-web/` code was imported. Earlier Ready-Set closure and
Go-Check evidence are now historical, not current Go authorization.

- Historical 2026-06-04 MyWebTemplate rebaseline evidence:
  `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`
- Historical 2026-06-04 MyWebTemplate reissue evidence:
  `docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md`
- Historical 2026-06-04 Ready-Set state marked the
  `skeleton_adapter_safe_rebaseline_queue` as implementation-ready only; this
  is **not** current operational trading readiness.
- Historical 2026-06-04 MyWebTemplate rebaseline docs, still useful for
  quarantine/replacement history:
  - `docs/set/READY-SET-OWNER-DECISION-20260604_rebaseline_hwistock.md`
  - `docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md`
  - `docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md`
  - `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md`
- Superseded historical docs:
  - `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`
  - `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`
  - `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md`
- Current UNIT-001 rebaseline Go evidence:
  - `docs/evidence/RUN-20260604_unit-001-go-preflight-rebaseline.md`
  - `docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md`
- Current UNIT-002 Go evidence:
  - `docs/evidence/RUN-20260604_unit-002-go-check.md`
- Current UNIT-008 rebaseline Go evidence:
  - `docs/evidence/RUN-20260604_unit-008-go-preflight-rebaseline.md`
  - `docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md`
- Current UNIT-003 rebaseline Go evidence:
  - `docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md`
  - `docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md`
- Current UNIT-003 source collector hotfix evidence:
  - `docs/evidence/RUN-20260605_unit-003-source-collector-hotfix.md`
- Current UNIT-004 rebaseline Go evidence:
  - `docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md`
  - `docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md`
- Current UNIT-006 rebaseline Go evidence:
  - `docs/evidence/RUN-20260604_unit-006-go-preflight-rebaseline.md`
  - `docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md`
- Current UNIT-005 rebaseline Go evidence:
  - `docs/evidence/RUN-20260605_unit-005-go-preflight-rebaseline.md`
  - `docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md`
- Current UNIT-009 rebaseline Go evidence:
  - `docs/evidence/RUN-20260604_unit-009-go-preflight-rebaseline.md`
  - `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`
- Current UNIT-007 rebaseline Go evidence:
  - `docs/evidence/RUN-20260605_unit-007-go-preflight-rebaseline.md`
  - `docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md`
- Current dashboard/API port and tunnel evidence:
  - `docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md`
- Current local server smoke evidence:
  - `docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md`
- Current hwibuntu tunnel smoke evidence:
  - `docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md`
- Current browser UI Prove evidence, now partial for static dashboard/report
  rendering only:
  - `docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`
- Current dashboard AI conversation correction:
  - `docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md`
- Current UNIT-007 Lucid Command dashboard Go evidence:
  - `docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md`
- Current UNIT-007 Gemini screenshot follow-up dark-shell Go-Check evidence:
  - `docs/evidence/RUN-20260606_unit-007-dashboard-dark-shell-go-check.md`
- Current UNIT-007 AI conversation backend Go-Check evidence:
  - `docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`
- Current Pro review fail-closed follow-up evidence:
  - `docs/evidence/RUN-20260605_pro-review-fail-closed-followup.md`
- Current UNIT-010 local Go-Check evidence:
  - `docs/evidence/RUN-20260605_unit-010-go-check.md`
- Current commit-prep scope audit:
  - `docs/evidence/RUN-20260605_commit-prep-scope-audit.md`
- Historical or invalidated prior Go-Check evidence:
  - `docs/evidence/RUN-20260604_unit-001-go-preflight.md`
  - `docs/evidence/RUN-20260604_unit-001-go-check.md`
  - `docs/evidence/RUN-20260604_unit-003-go-check.md`
  - `docs/evidence/RUN-20260604_unit-004-go-check.md`
  - `docs/evidence/RUN-20260604_unit-006-go-check.md`
  - `docs/evidence/RUN-20260604_unit-008-go-check.md`
  - `docs/evidence/RUN-20260604_unit-009-go-preflight.md`
  - `docs/evidence/RUN-20260604_unit-009-go-check.md`

Ready-Set has been reissued against the imported MyWebTemplate code baseline.
MyWebTemplate sample/public quarantine and local-only bind/access enforcement
are first-row requirements for Go-Check, not optional cleanup. The original
nine-unit `skeleton_adapter_safe_rebaseline_queue` is preserved as history, but
`HWISTOCK-UNIT-007` has a current 2026-06-05 correction: static dashboard/report
thread proof was partial only. The Lucid Command frontend now proves separate
AI report and AI conversation UI plus POST wiring, and the backend follow-up
proves the conversation endpoint, grounded local answer/refusal, and local audit
logging. Browser/tunnel Prove remains pending
(`docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md`;
`docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`;
`docs/evidence/RUN-20260606_unit-007-dashboard-dark-shell-go-check.md`;
`docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md`).
Current local dashboard/API defaults are dashboard/frontend `127.0.0.1:5000`
and backend/API `127.0.0.1:5001`; hwibuntu access uses SSH local forwarding, recorded in
`docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md`. Local server smoke
confirmed both loopback ports can serve the runtime after local ignored config
override cleanup, and frontend BFF now reaches the same 5001 backend as direct
backend smoke
(`docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md`). hwibuntu tunnel
smoke confirmed the SSH local-forwarded 5000/5001 path over hwibuntu loopback
with matching BFF/backend `startedAt` and no-order/no-broker runner safety
flags
(`docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md`).
Browser UI Prove through the same hwibuntu tunnel initially failed on
2026-06-05 because `/login` still exposed MyWebTemplate sample/demo copy and
the authenticated dashboard showed `HTTP_500_INTERNAL` due to backend Decimal
JSON serialization failures
(`docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md`). The follow-up
login/API 500 fix re-Prove passed for static rendering only: Chrome confirmed a hwiStock-branded public
login surface without template/demo residue, authenticated dashboard rendering,
masked account-like values, and no visible API 500
(`docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`). It did not
prove a dashboard question input or backend AI conversation endpoint; the
frontend input/POST wiring was later covered by
`docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md`, while
grounded backend answer/refusal flow and audit logging were later covered by
`docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`.
Commit-prep scope audit confirmed `git add -A --dry-run` candidates exclude
local config/env/log/cache paths after `.gitignore` cleanup, and no staging or
commit has been performed
(`docs/evidence/RUN-20260605_commit-prep-scope-audit.md`).
Historical GPT/design reviews are supporting constraints only and were not
re-run after the import. No operational trading, brokerage, AI provider
network use, or public dashboard exposure is authorized.

The all-nine-unit skeleton queue is not operation readiness. It proves local
foundation/skeleton behavior only. `HWISTOCK-UNIT-010` is also not the complete
program: it is a local no-network KIS broker adapter runner foundation. The current
operational target is the UNIT-011, UNIT-016, and UNIT-012 through UNIT-015
queue recorded in the 2026-06-05 operational Ready-Set. UNIT-016 blocks
order-producing Go rows until runtime contracts are hardened. Operational
operation Prove has not started.

UNIT-003 correction note: the 2026-06-04 UNIT-003 Go-Check PASS was only a
fixture/config-first skeleton and did not mean a 24-hour news/disclosure
collector was already running. On 2026-06-05 a source collector entrypoint and
user systemd timer were added and enabled. The timer currently runs every 10
minutes. A no-key `public_news_rss_search` source now collects public RSS news
metadata: the 2026-06-05 runtime proof recorded 150 normalized news events, 150
unique event ids, and 0 duplicate JSONL rows. OpenDART/Naver API rows still
skip until `DART_API_KEY` and/or Naver API credentials are added to the local
secret store. Historical UNIT-003 hotfix evidence did not start DeepSeek, but a
later UNIT-011/DeepSeek timer pass did install the hwiStock DeepSeek Pro
top-of-hour job/timer. Treat those as separate evidence rows: UNIT-003 proves
collector correction only; UNIT-011/DeepSeek timer evidence proves analysis
timer installation, while operational readiness remains false.

## Source Of Truth

1. User instruction in the current task.
2. Root `AGENTS.md`.
3. Project profile: `docs/profiles/PROFILE-HWISTOCK.md`.
4. Module, unit, and QA scenario docs under `docs/`.
5. Code and runtime evidence once implementation starts.
6. Broker/API official documentation for the selected provider.
7. Prior evidence and memento memories.

## Current Profile

- `docs/profiles/PROFILE-HWISTOCK.md`: active HWI Work Harness project profile.
- `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`: market intelligence source
  allowlist and source-status contract.
- `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`: KIS API adapter-mode
  capability, fallback, and runtime-verification matrix for local `apiRefer`
  spreadsheets.
- `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`: KRX/NXT calendar
  source, local alert channel, and operator-controlled adapter-backed observation
  criteria.
- `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`: prepared
  user-approval packet for first-pass strategy defaults.
- `docs/set/READY-SET-EXTERNAL-REVIEW-PACKET-20260602_hwistock.md`: historical
  safe sharing scope for the pre-import final external review.
- `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`:
  prepared `agy` Gemini Pro dashboard design review packet.
- `docs/design/HWISTOCK-DESIGN-20260605_lucid-command-dashboard.md`: Lucid
  Command dark desktop-first operator cockpit design artifact for UNIT-007.
- `docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md`: historical
  pre-import requirement-by-requirement audit. For operational claims, use the
  2026-06-05 operational automated-trading Ready-Set; the 2026-06-04 rebaseline
  completion, row closure, and Go preflight are historical MyWebTemplate-import
  records.
- `docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md`: historical owner
  approval choices, receipt checklist, and pre-import full expansion closure
  refs.
- `docs/set/READY-SET-FOUNDATION-QUEUE-PROPOSAL-20260602_hwistock.md`:
  inactive proposal for a narrower foundation-only Go queue.
- `docs/set/READY-SET-EXTERNAL-REVIEW-PROMPT-20260602_hwistock.md`: prepared
  safe prompt for historical external review workflows, not current
  post-import authority.
- `docs/set/READY-SET-EXTERNAL-REVIEW-SHARE-MANIFEST-20260602_hwistock.md`:
  prepared include/exclude manifest for sanitized external review sharing.
- `docs/set/READY-SET-LOCAL-DOC-CONSISTENCY-AUDIT-20260602_hwistock.md`:
  local findings-first consistency audit for Ready-Set docs and share scope.
- `docs/set/READY-SET-DOC-REFERENCE-LEDGER-20260602_hwistock.md`: local
  reference ledger for current docs inventory and template exceptions.
- `docs/set/READY-SET-OWNER-DECISION-BRIEF-20260602_hwistock.md`: owner-facing
  decision brief for closing the remaining Ready-Set approval/review blockers.
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md`: final
  local preflight checklist that must pass before any Go implementation attempt.
- `docs/set/READY-SET-OWNER-DECISION-RECEIPT-TEMPLATE-20260603_hwistock.md`:
  prepared template for classifying future owner messages before any
  approval-driven row closure or completion rewrite.
- `docs/set/READY-SET-ROW-CLOSURE-ACTIVATION-DRAFT-20260603_hwistock.md`:
  inactive draft describing how full or foundation-only row closure could be
  rewritten after explicit owner approval and required review evidence.
- `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-TEMPLATE-20260603_hwistock.md`:
  prepared template for normalizing future external/design review findings
  before any row closure or completion-status rewrite.
- `docs/set/READY-SET-RULE-PRESET-APPLICABILITY-MATRIX-20260603_hwistock.md`:
  prepared matrix mapping active FastAPI, Next frontend, DB naming, and manual
  safety rules to each unit before Go.
- `docs/set/READY-SET-GATE-EVIDENCE-MATRIX-20260603_hwistock.md`: historical
  matrix mapping pre-import Ready-Set completion-gate requirements to full queue
  pass evidence.
- `docs/set/KIS-BROKER-ADAPTER-API-SMOKE-MATRIX-20260604_hwistock.md`: approved
  but currently blocked KIS broker-adapter API smoke matrix, including broker order,
  modify, and cancel calls for the KRX adapter path.
- `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260603_foundation.md`:
  historical normalized ChatGPT Pro external review findings for the narrowed
  foundation-only queue.
- `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md`:
  normalized `agy` dashboard design findings for `HWISTOCK-UNIT-007`.
- `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_full.md`: normalized
  ChatGPT Pro external review findings for full queue closure with exclusions.
- `docs/set/READY-SET-COMPLETION-20260605_continuous-adapter-runner_hwistock.md`:
  superseded/narrow Ready-Set completion for `HWISTOCK-UNIT-010` continuous KIS
  broker-adapter runner Go-Check only. It is not operational program readiness.
- `docs/set/READY-SET-ROW-CLOSURE-20260605_continuous-adapter-runner_hwistock.md`:
  superseded/narrow row closure for the continuous KIS broker adapter runner row.
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_continuous-adapter-runner_hwistock.md`:
  superseded/narrow preflight for implementing the continuous KIS broker adapter runner.
- `docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md`:
  current Ready-Set completion for the actual operational automated-trading program;
  currently contract-hardened and implementation-ready only for the next
  Go-Check queue, not operation-ready.
- `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-automated-trading-program_hwistock.md`:
  current row closure for UNIT-011, UNIT-016, and UNIT-012 through UNIT-015.
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-automated-trading-program_hwistock.md`:
  current preflight for implementing the actual operational automated-trading
  program.

## Modules

- `docs/modules/HWISTOCK-MOD-001_trading-safety-core.md`: trading automation
  safety, risk, order-gating, and observability contract.
- `docs/modules/HWISTOCK-MOD-002_market-intelligence-ingestion.md`: 24-hour
  news/article/disclosure ingestion contract.
- `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`: stock-selection,
  position-sizing, all-in prohibition, exit, and kill-switch rulebook.
- `docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md`: AI API
  orchestration contract for candidate synthesis, structured recommendations,
  and safety gating.
- `docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md`: trading engine,
  condition compiler, order state, and broker adapter contract.
- `docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md`: read-only
  dashboard/operator console, stored AI report viewer, and interactive AI
  conversation surface contract; Lucid Command frontend report/conversation UI
  is validated, Gemini screenshot follow-up dark-shell Go-Check has local
  browser proof, backend conversation answer/refusal/audit is focused-tested,
  and browser/tunnel Prove remains pending
  (`docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md`;
  `docs/evidence/RUN-20260606_unit-007-dashboard-dark-shell-go-check.md`;
  `docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`;
  `docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md`).
- `docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md`: date-based data,
  analysis artifact, PostgreSQL storage, trade log, and evidence storage
  contract.
- `docs/modules/HWISTOCK-MOD-008_continuous-adapter-runtime.md`: 24-hour
  continuous KIS broker adapter runtime contract. This is the runner foundation and
  explicitly forbids hardcoded seven-day/fixed-duration runner logic.
- `docs/modules/HWISTOCK-MOD-009_operational-automated-trading-program.md`: current
  authority for the actual automated-trading program integration across service
  supervision, AI analysis, signal-to-intent, KIS broker adapter execution,
  reconciliation, and operator observation Prove.

## Units

- `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md`:
  set project bootstrap and safety-first planning setup;
  `go_check_passed` for docs-only rebaseline verification
  (`docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md`). MyWebTemplate
  quarantine guardrails are recorded as first-row blockers for affected future
  rows; product-code removal remains out of UNIT-001 scope.
- `docs/units/HWISTOCK-UNIT-002_home-server-adapter-runner.md`:
  `go_check_passed` for the bounded local runner/systemd skeleton
  (`docs/evidence/RUN-20260604_unit-002-go-check.md`): loopback-only bind,
  read-only runner status API, no-order intent metadata, calendar/source idle
  behavior, local audit/alert metadata, and systemd templates.
- `docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md`:
  `go_check_passed` 24-hour market intelligence ingestion skeleton with a
  DART-first source allowlist, blocked/deferred source policy, fixture/config-
  first ingestion, KST timestamp/body-policy enforcement, and no sample/demo
  backend surface requirement
  (`docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md`).
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`:
  `go_check_passed` strategy and minimal risk parameter contract with a
  stdlib-only local config/validation/no-order dry-run skeleton for candidate
  selection, entries, exits, minimum cash reserve ratio 0.25, maximum
  simultaneous holdings 5, stale-data and re-entry blocking, and AI-assisted
  stop policy capped by deterministic risk gates
  (`docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md`).
- `docs/units/HWISTOCK-UNIT-005_ai-orchestration-layer.md`:
  `go_check_passed` current-authority AI orchestration foundation with
  disabled-by-default AI network/provider/cost config, six-role job registry,
  `ai_recommendation/v0` validation, source grounding, sensitive-payload review,
  deterministic policy-gate handoff, no-order dry-run records, audit/fallback
  reports, tool-use-disabled behavior, and no sample/demo backend surface
  contract (`docs/evidence/RUN-20260605_unit-005-go-check-rebaseline.md`).
- `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md`:
  `go_check_passed` current-authority rebaseline trading engine/order-state
  foundation skeleton with `condition_card/v0` validation, deterministic
  compiler, UNIT-004 risk-gate delegation, SOR/AUTO_SESSION route
  normalization-or-blocking, pre-approval order-state transitions through
  `dry_run_recorded`, no-order dry-run records, venue-route metadata, and KIS
  adapter capability flags
  (`docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md`).
- `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md`:
  `go_check_passed_pending_browser_tunnel_prove` for read-only dashboard/operator console with
  tasks/settings subroutes, root/public/sample quarantine, masked/sanitized
  values, local-only/public exposure boundary, stored AI report viewer, and
  frontend AI conversation input/POST wiring plus backend answer/refusal/audit
  focused tests. Current
  local ports are dashboard/frontend `5000` and backend/API `5001`, with
  hwibuntu access through SSH local forwarding
  (`docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md`;
  `docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md`;
  `docs/evidence/RUN-20260606_unit-007-dashboard-dark-shell-go-check.md`;
  `docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`;
  `docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md`;
  `docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md`).
- `docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md`:
  `go_check_passed` storage and evidence skeleton using PostgreSQL database
  `hwistock`, schema `hwistock_core`, date-partitioned artifacts, hwiStock DB
  isolation, typed artifact contracts, and focused tests.
- `docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md`:
  `go_check_passed` for current-authority rebaseline KIS API official portal
  and capability-matrix verification with sanitized KRX adapter smoke
  cross-reference and preserved partial-boundary follow-ups
  (`docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`).
- `docs/units/HWISTOCK-UNIT-010_kis-adapter-continuous-runner.md`:
  local no-network Go-Check foundation for a continuous 24-hour KIS KRX
  broker-adapter runner. It is an input to the operational queue, not the complete
  trading program.
- `docs/units/HWISTOCK-UNIT-011_operational-runtime-supervisor.md`:
  `go_started_check_pending` for installable user systemd supervision,
  local-only service startup, timer health, and runtime evidence
  (`docs/evidence/RUN-20260605_unit-011-runtime-start-go.md`).
- `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md`:
  local no-network Go-Check passed for current DeepSeek Pro/Flash scheduled
  analysis runtime with no-order AI boundaries; provider smoke remains blocked
  (`docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`).
- `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`:
  local no-network Go-Check passed for NAVER/OpenDART source-grounded
  candidates, the KIS mode-gated market-data collector boundary, deterministic risk gates,
  and `paper_order_intent/v0` queue generation; KIS broker adapter-read transport smoke
  remains blocked (`docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`).
- `docs/units/HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md`:
  local no-network Go-Check passed for preflight/idempotency/realtime-exit
  behavior; KIS KRX broker order/reconciliation smoke remains blocked
  (`docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`).
- `docs/units/HWISTOCK-UNIT-015_operator-console-observation-prove.md`:
  local API/frontend Go-Check passed for read-only operator dashboard/API
  status and observation-window reports; browser/tunnel Prove remains blocked
  (`docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`).

## QA Scenarios

- `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md`:
  set QA to prove that the bootstrap docs, safety gates, and rebaseline
  quarantine guardrails are present before implementation begins.
- `docs/qa/QA-HWISTOCK-UNIT-002_home-server-adapter-runner.md`:
  `go_check_passed` QA for service lifecycle skeleton, health, logging, kill
  switch, local-only bind, and adapter/no-order operation.
- `docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md`:
  `go_check_passed` QA for allowed-source ingestion, blocked-source
  enforcement, deduplication, rate limiting, event schema, KST timestamp/body-
  policy enforcement, evidence, and no sample/demo backend exposure.
- `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`:
  `go_check_passed` QA for strategy/risk rule completeness, cash-reserve/
  holdings caps, stale-data and re-entry blocking, and no-order dry-run
  boundary (`docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md`).
- `docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md`:
  set QA for AI output schema, citation/source grounding, no-direct-order
  behavior, deterministic risk-gate enforcement, and provider-network disabled
  defaults.
- `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md`:
  `go_check_passed` QA for condition compiler, deterministic buy gate, explicit
  order states, dry-run-only boundary, KIS broker adapter capability flags, and
  fixture-only broker-evidence representation
  (`docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md`).
- `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md`:
  `go_check_passed_pending_browser_tunnel_prove` QA for read-only dashboard behavior,
  sensitive-data masking, stored AI report viewer, frontend AI conversation
  input/POST wiring, backend answer/refusal/audit focused tests, design review
  route, MyWebTemplate
  branding/sample/public route quarantine, local-only access boundary, and
  dashboard/API `5000`/`5001` port defaults with SSH local forwarding
  (`docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md`;
  `docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md`;
  `docs/evidence/RUN-20260606_unit-007-dashboard-dark-shell-go-check.md`;
  `docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`;
  `docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md`;
  `docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md`).
- `docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md`:
  `go_check_passed` QA for PostgreSQL isolation, storage separation,
  system-calculated PnL, hwiStock DB isolation, and operator-selected operation
  observation evidence linkability.
- `docs/qa/QA-HWISTOCK-UNIT-009_kis-api-portal-verification.md`:
  `go_check_passed` QA for current-authority rebaseline KIS API portal
  verification with partial-boundary items preserved and no new KIS/broker
  authorization (`docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`).
- `docs/qa/QA-HWISTOCK-UNIT-010_kis-adapter-continuous-runner.md`:
  set QA for continuous KIS broker adapter runner behavior, operator-controlled
  observation windows, KIS broker adapter/unapproved domain separation,
  mode-gated KRX/integrated/NXT capability, risk overlay, no fake broker state, service lifecycle, and
  read-only/local-only status surfaces.
- `docs/qa/QA-HWISTOCK-UNIT-011_operational-runtime-supervisor.md`:
  set QA for user systemd install/start/restart/local-only supervision.
- `docs/qa/QA-HWISTOCK-UNIT-012_ai-analysis-runtime.md`:
  local no-network Go-Check QA passed for DeepSeek Pro/Flash model config,
  schedule, schema validation, redaction, and no-order boundaries; provider
  smoke remains blocked.
- `docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`:
  local no-network Go-Check QA passed for source-grounded candidate generation,
  KIS mode-gated market-data boundary, and deterministic
  `paper_order_intent/v0` gating; KIS adapter-read transport smoke remains
  blocked.
- `docs/qa/QA-HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md`:
  local no-network Go-Check QA passed for KIS adapter domain guard, preflight,
  restart idempotency, realtime exit checks, and no-fake-broker behavior; order
  smoke remains blocked.
- `docs/qa/QA-HWISTOCK-UNIT-015_operator-console-observation-prove.md`:
  local API/frontend Go-Check QA passed for read-only operator status, masking,
  readiness separation, and observation-window reporting; browser/tunnel Prove
  remains blocked.

## Evidence

- Historical evidence files preserve earlier planning assumptions. If they
  conflict with the current profile/module/unit contracts or the latest
  Ready-Set evidence, treat the current contracts as authoritative.
- `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`:
  historical rebaseline evidence explaining why the prior queue was superseded by
  the MyWebTemplate code import.
- `docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md`:
  historical Ready-Set reissue evidence after the owner selected MyWebTemplate
  sample/public quarantine and hwiStock replacement.
- `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`: historical Ready-Set
  completion gate, now `implementation_ready: false` and
  `current_authority: false`.
- `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`: historical row-closure
  matrix; row states must be reissued against the imported code baseline.
- `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260602_hwistock.md`: historical
  Go preflight checklist; do not use as current Go authorization.
- `docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md`: external
  ChatGPT Pro review evidence and local interpretation for the pre-import full
  queue closure with exclusions; supporting context only after the
  MyWebTemplate import.
- `docs/evidence/RUN-20260604_dashboard-design-review.md`: `agy` Gemini Pro
  dashboard design review evidence from before the MyWebTemplate import;
  supporting design constraints only until a current dashboard Check/review runs.
- `docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md`:
  owner decision receipt and pre-send evidence for the full expansion review.
- `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke-approval-preflight.md`:
  owner approval and blocked environment preflight for KIS broker-adapter API smoke
  including broker orders.
- `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`: sanitized KIS
  broker-adapter REST and websocket smoke evidence; token, quote, balance, buyable,
  broker buy order, cancel, daily order/fill, websocket fill-notice ACK, and token
  revoke passed.
- `docs/evidence/RUN-20260604_unit-003-go-preflight-rebaseline.md`:
  current UNIT-003 rebaseline Go preflight evidence after the MyWebTemplate
  import.
- `docs/evidence/RUN-20260604_unit-003-go-check-rebaseline.md`:
  current UNIT-003 rebaseline Go-Check evidence for the fixture/config-first
  market-intelligence ingestion skeleton.
- `docs/evidence/RUN-20260604_unit-004-go-preflight-rebaseline.md`:
  current UNIT-004 rebaseline Go preflight evidence for the stdlib-only
  strategy/risk rulebook skeleton.
- `docs/evidence/RUN-20260604_unit-004-go-check-rebaseline.md`:
  current UNIT-004 rebaseline Go-Check evidence for reserve-floor sizing,
  holdings caps, AI-stop validation, no-order dry-run records, and focused
  unittest coverage.
- `docs/evidence/RUN-20260604_unit-006-go-preflight-rebaseline.md`:
  current UNIT-006 rebaseline Go preflight evidence for the imported backend
  tree and foundation-only trading-engine skeleton scope.
- `docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md`:
  current UNIT-006 rebaseline Go-Check evidence for `condition_card/v0`
  validation, deterministic compiler, UNIT-004 risk-gate delegation,
  SOR/AUTO_SESSION route normalization-or-blocking, dry-run-only order-state
  transitions, KIS broker adapter capability flags, fixture-only evidence
  representation, and focused unittest coverage.
- `docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md`: Git
  initialization, PF-13 resolution, `.env` ignore policy, and Ready-Set delta
  sync evidence.
- `docs/evidence/RUN-20260604_unit-001-go-preflight-rebaseline.md`: UNIT-001
  current rebaseline Go preflight evidence (docs-only bootstrap).
- `docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md`: UNIT-001
  current rebaseline Go-Check evidence (docs-only bootstrap; Kimi worker
  attempt quarantined, Cursor audit closure accepted).
- `docs/evidence/RUN-20260604_unit-001-go-preflight.md`: UNIT-001 historical
  selected-row Go preflight evidence from before the rebaseline reissue; not
  current Go authorization.
- `docs/evidence/RUN-20260604_unit-001-go-check.md`: UNIT-001 docs-only
  historical Go-Check evidence; useful support, not current Go
  authorization.
- `docs/evidence/RUN-20260604_unit-006-go-preflight.md`: UNIT-006 historical
  selected-row Go preflight evidence superseded by the rebaseline queue; not
  current authority.
- `docs/evidence/RUN-20260604_unit-006-go-check.md`: UNIT-006 Go-Check evidence
  for condition_card/v0 validation, compiler skeleton, pre-approval order-state
  transitions, no-order dry-run records, KIS broker adapter capability flags, focused
  tests, and rule-gates without broker-backed broker-adapter authorization; invalidated
  as current implementation evidence by the MyWebTemplate import.
- `docs/evidence/RUN-20260604_unit-004-go-preflight.md`: UNIT-004 historical
  selected-row Go preflight evidence superseded by the rebaseline queue.
- `docs/evidence/RUN-20260604_unit-004-go-check.md`: UNIT-004 Go-Check evidence
  for approved config constants, entry-intent validators, no-order dry-run
  records, focused tests, and rule-gates without broker/AI/order authorization;
  invalidated as current implementation evidence by the MyWebTemplate import.
- `docs/evidence/RUN-20260604_unit-008-go-preflight.md`: UNIT-008 historical
  selected-row Go preflight evidence superseded by the rebaseline queue.
- `docs/evidence/RUN-20260604_unit-008-go-check.md`: UNIT-008 Go-Check
  evidence for typed storage schemas, Alembic `hwistock_core` migration
  skeleton, request payload helper profile compatibility, tests, and rule-gates;
  invalidated as current implementation evidence by the MyWebTemplate import.
- `docs/evidence/RUN-20260604_unit-008-go-preflight-rebaseline.md`: current
  UNIT-008 rebaseline Go preflight evidence.
- `docs/evidence/RUN-20260604_unit-008-go-check-rebaseline.md`: current
  UNIT-008 Go-Check evidence for typed storage schemas, canonical artifact
  paths, Alembic `hwistock_core` migration skeleton, request payload helpers,
  focused tests, scoped rule-gate results, and accepted read-only Check review.
- `docs/evidence/RUN-20260604_unit-003-go-preflight.md`: UNIT-003 historical
  selected-row Go preflight evidence. Its original no_delegation note is
  superseded by the explicit implementation-worker route recorded in the
  historical Go-Check evidence.
- `docs/evidence/RUN-20260604_unit-003-go-check.md`: UNIT-003 Go-Check evidence
  for the stdlib-only source registry/config model, fixture ingestion,
  normalized event shaping, deterministic dedupe, health/summary output,
  blocked-source guards, no network/credential/order imports, tests, and
  optional rule-gate status; invalidated as current implementation evidence by
  the MyWebTemplate import.
- `docs/evidence/RUN-20260604_unit-009-go-preflight-rebaseline.md`: UNIT-009
  current-authority rebaseline selected-row Go preflight evidence for docs-only
  capability-matrix refinement and broker/KIS-network denial preservation.
- `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`: UNIT-009
  current-authority rebaseline Go-Check evidence with docs-only PASS verdict,
  sanitized KRX adapter smoke cross-reference, historical worker/fallback
  context, and preserved partial boundaries.
- `docs/evidence/RUN-20260604_unit-009-go-preflight.md`: UNIT-009 historical
  selected-row Go preflight evidence for docs-only KIS capability matrix scope;
  not current Go authorization after the rebaseline reissue.
- `docs/evidence/RUN-20260604_unit-009-go-check.md`: UNIT-009 Go-Check evidence
  with PASS verdict for docs-only/local-reference KIS capability verification,
  sanitized smoke cross-reference, and partial-boundary preservation; supporting
  context only for the current reissued row.
- `docs/evidence/RUN-20260603_gpt-pro-foundation-ready-set-review.md`:
  historical external ChatGPT Pro review evidence for the narrowed
  foundation-only queue.
- `docs/evidence/RUN-20260602_ready-set-architecture.md`: latest docs-only
  Ready-Set architecture evidence after the AI, dashboard, broker-adapter budget,
  KIS verification, and minimal risk-policy brainstorming pass.
- `docs/evidence/RUN-20260602_unit-008-data-evidence-storage-set.md`: Set
  evidence for choosing PostgreSQL storage with hwiStock-specific
  database/schema isolation.
- `docs/evidence/RUN-20260602_unit-003-market-intelligence-set.md`: Set
  evidence for DART-first market-intelligence ingestion, conditional Naver news
  API use, and deferred/blocked source handling.
- `docs/evidence/RUN-20260602_unit-009-kis-api-portal-verification-set.md`: Set
  evidence for KIS official endpoint-family verification, adapter-mode separation,
  adapter-constrained API behavior, fallback needs, and remaining broker-smoke
  items.
- `docs/evidence/RUN-20260602_unit-006-trading-engine-order-state-set.md`: Set
  evidence for condition schema, order state machine, no-order dry-run, KIS KRX
  broker adapter capability, and reconciliation/fallback behavior.
- `docs/evidence/RUN-20260602_unit-005-ai-orchestration-layer-set.md`: Set
  evidence for AI job registry, schemas, GPT cutoff, tool-use disabled policy,
  AI network disabled defaults, and fallback behavior.
- `docs/evidence/RUN-20260602_stack-rule-preset-set.md`: Set evidence for
  selecting Python/FastAPI backend, TypeScript/Next.js dashboard, PostgreSQL,
  Alembic migrations, and HWI FastAPI/Next/DB rule presets.
- `docs/evidence/RUN-20260602_unit-004-strategy-risk-rulebook-set.md`: Set
  evidence for reserve-floor sizing, maximum simultaneous holdings 5, and
  AI-assisted stop policy capped by deterministic maximum -5% loss.
- `docs/evidence/RUN-20260602_unit-002-home-server-adapter-runner-set.md`: Set
  evidence for systemd runner lifecycle, source-unconfigured idle behavior, and
  local-only health/API surfaces.
- `docs/evidence/RUN-20260604_unit-002-go-preflight.md`: Go preflight evidence
  for the bounded UNIT-002 runner/systemd skeleton row.
- `docs/evidence/RUN-20260604_unit-002-go-check.md`: Go-Check evidence for
  the UNIT-002 local-only broker-adapter runner skeleton, no-order status API,
  loopback-only bind, `--once` runner entrypoint, and worker/review closure.
- `docs/evidence/RUN-20260602_unit-007-dashboard-operator-console-set.md`: Set
  evidence for read-only dashboard scope, local-only access, no-design fallback,
  first-screen sections, and AI conversation boundary.
- `docs/set/READY-SET-CORRECTION-20260605_dashboard-ai-conversation.md`:
  corrective Ready-Set source that separates stored AI report viewing from
  interactive AI conversation and makes missing backend endpoint/refusal/audit
  flow a blocker after the Lucid Command frontend input follow-up.
- `docs/evidence/RUN-20260605_unit-007-lucid-command-dashboard-go.md`: current
  UNIT-007 Lucid Command dashboard Go evidence for frontend report/conversation
  split, AI conversation input and POST wiring, focused tests, rule-gate, lint,
  diff check, and production build.
- `docs/evidence/RUN-20260606_unit-007-dashboard-dark-shell-go-check.md`:
  current UNIT-007 Gemini screenshot follow-up Go-Check evidence for the dark
  high-trust dashboard shell, readiness banner visual priority, dense cockpit
  spacing, shared Card dark override, focused tests, rule-gate, production
  build, and local production-style browser screenshot proof.
- `docs/evidence/RUN-20260605_unit-007-ai-conversation-backend-go-check.md`:
  current UNIT-007 backend Go-Check evidence for
  `POST /api/v1/hwistock/ai/conversation`, grounded local answer/refusal,
  JSONL audit, secret-preview redaction, and no broker/order/service/AI-provider
  side-effect flags.
- `docs/evidence/RUN-20260605_pro-review-fail-closed-followup.md`: current
  follow-up Go-Check evidence for Pro review fail-closed remediation across
  paper-order calendar/source approval, `paper_only`/broker-adapter intent
  preflight, FIFO queue reporting, AI readiness service-policy contradictions,
  and AI conversation access invariant.
- `docs/evidence/RUN-20260606_monday-operation-p0-safety-gates-go-check.md`:
  current Go-Check evidence for Monday operation P0 hardening: date-specific KST
  calendar rows, KRX order-session requirement, KIS read-step account truth,
  exit-before-entry queue priority, live/effective user-systemd policy, runtime
  artifact freshness, focused tests, rule-gate, and no-order runner smoke.
- `docs/evidence/RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix.md`:
  current KIS paper/mock hotfix evidence for token-cache recognition, invalid
  token retry, provider-unsupported sellable/cancelable/realized-PnL/holiday TR
  skipping as `skipped_provider_unsupported`, unknown sellable truth preservation,
  90 backend tests plus 11 subtests, rule-gate pass, and sanitized runtime smoke.
  This evidence does not claim order-submit readiness.
- `docs/evidence/RUN-20260605_unit-007-go-preflight-rebaseline.md`: current
  UNIT-007 rebaseline Go preflight evidence for read-only dashboard operator
  console doc-sync closure.
- `docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md`: current UNIT-007
  rebaseline Go-Check evidence for read-only operator console, tasks/settings
  subroutes, public/sample quarantine, masked values, focused frontend
  tests/eslint, scoped rule-gate zero findings, preserved worker history, and
  remaining limitations.
- `docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md`: current
  local-only dashboard/API port and hwibuntu SSH tunnel evidence for
  dashboard/frontend `127.0.0.1:5000`, backend/API `127.0.0.1:5001`, helper
  tunnel script, focused tests/lint, runner tests, syntax checks, and explicit
  no-server/no-browser/no-network limitations.
- `docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md`: local runtime
  smoke evidence after local ignored config override cleanup. Direct backend
  5001 and frontend 5000 checks passed, BFF `healthz` matched the direct
  backend `startedAt`, and BFF hwiStock runner status returned no-order,
  no-broker-call safety flags.
- `docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md`: hwibuntu SSH
  tunnel smoke evidence. The tunnel forwarded hwibuntu `127.0.0.1:5000/5001`
  to hwiServer loopback, direct/BFF backend checks passed, and runner status
  confirmed no-order/no-broker safety flags over the tunnel.
- `docs/evidence/RUN-20260605_browser-ui-prove-5000-5001.md`: superseded
  browser UI Prove failure evidence for the earlier login sample/demo residue
  and dashboard Decimal JSON serialization 500.
- `docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`: current
  browser UI re-Prove evidence after login public-surface quarantine and
  dashboard Decimal JSON-safe response conversion. After the 2026-06-05 AI
  conversation correction, treat it as static dashboard/report rendering proof
  only, not interactive AI conversation proof. Captures the hwibuntu tunnel/
  Chrome Extension route, focused backend/frontend tests, BFF login and
  dashboard API smoke, and login/dashboard screenshots.
- `docs/evidence/RUN-20260605_commit-prep-scope-audit.md`: current commit-prep
  scope audit. It records the read-only Cursor worker audit, `.gitignore`
  cleanup for local config/test-config/log artifacts, `git add -A --dry-run`
  candidate count, excluded path classes, and Korean commit-message suggestion.
- `docs/evidence/RUN-20260605_ready-set-continuous-adapter-runner.md`:
  superseded/narrow docs-only evidence for correcting the runner foundation to
  a continuous KIS broker adapter runner with operator-selected observation windows and
  no hardcoded fixed-duration program behavior.
- `docs/evidence/RUN-20260605_ready-set-operational-automated-trading-program.md`:
  current Ready-Set evidence for the actual operational automated-trading program
  queue: service supervision, AI runtime, signal-to-intent, KIS broker adapter
  execution/reconciliation, and operator observation Prove.
- `docs/evidence/RUN-20260605_unit-011-runtime-start-go.md`: current Go evidence
  that the user systemd runtime bundle was installed/enabled/started, API and
  frontend run on loopback, DeepSeek Pro analysis produced evidence, KIS broker adapter
  read/reconciliation ticks produced evidence, and broker cash order submission
  remains disabled.
- `docs/evidence/RUN-20260605_unit-010-go-check.md`: current local no-network
  Go-Check evidence for the continuous KIS broker adapter runner implementation,
  including adapter, ledger, runner CLI, read-only status API, systemd user
  templates, focused tests, and explicit no-KIS-call/no-secret/no-order
  boundaries.
- `docs/evidence/RUN-20260602_calendar-alert-operation-gate-set.md`: historical Set
  evidence for KRX/NXT calendar source hierarchy, local-only alert channel, and
  earlier adapter-backed criteria. Current active policy is updated in
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`.
- `docs/evidence/RUN-20260602_ready-set-decision-review-packets.md`: Set
  evidence for preparing the strategy decision packet, final external review
  packet, and dashboard design review packet without sending external data.
- `docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md`: historical
  pre-import completion audit showing pass/open-blocking state for module
  inventory, unit inventory, QA inventory, row closure, external review, and
  residual gaps.
- `docs/set/READY-SET-FOUNDATION-QUEUE-PROPOSAL-20260602_hwistock.md`: inactive
  queue proposal that can be activated only by explicit owner approval plus
  completion/row-closure rewrite.
- `docs/evidence/RUN-20260602_external-review-share-manifest.md`: Set evidence
  for preparing the external-review share manifest without sending external
  data.
- `docs/set/READY-SET-LOCAL-DOC-CONSISTENCY-AUDIT-20260602_hwistock.md`: local
  doc consistency audit showing no P0/P1 doc-consistency findings and expected
  remaining approval/review blockers.
- `docs/evidence/RUN-20260602_doc-reference-ledger.md`: evidence for local docs
  reference integrity, with template placeholder exceptions.
- `docs/evidence/RUN-20260602_owner-decision-go-preflight.md`: evidence for
  preparing the owner decision brief and Go preflight checklist without
  authorizing Go.
- `docs/evidence/RUN-20260602_external-review-presend-dry-run.md`: local
  dry-run file list for the sanitized external review bundle, including the
  80-file candidate count, exact-match candidate comparison, and fail-closed
  candidate secret scan result, prepared without sending external data. The
  pre-import full review superseded this with an 85-file candidate bundle
  recorded in `docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md`.
- `docs/evidence/RUN-20260603_row-closure-activation-draft.md`: evidence for
  preparing the inactive row-closure activation draft without authorizing Go.
- `docs/evidence/RUN-20260603_review-findings-intake-template.md`: evidence for
  preparing the future review findings intake template, including pre-send
  candidate count/exact-match/secret-scan fields, without running reviews.
- `docs/evidence/RUN-20260603_rule-preset-applicability-matrix.md`: evidence for
  preparing the unit-by-unit rule preset applicability matrix without running Go.
- `docs/evidence/RUN-20260603_gate-evidence-matrix.md`: evidence for preparing
  the Ready-Set gate evidence matrix without authorizing Go.
- `docs/evidence/RUN-20260603_root-vcs-env-scan.md`: historical root-baseline
  evidence from before Git initialization and MyWebTemplate code import.
- `docs/evidence/RUN-20260603_ready-set-current-state-snapshot.md`: current
  historical local Ready-Set state snapshot after foundation-only ChatGPT Pro
  review, row closure, and completion rewrite.
- `docs/evidence/RUN-20260603_owner-decision-receipt-template.md`: evidence for
  preparing the future owner decision receipt template, including Action 3
  pre-send candidate checks, without recording any approval.
- `docs/evidence/RUN-20260602_unit-001-project-bootstrap-set.md`: Set evidence
  for closing the docs-only bootstrap/profile safety contract.
- `docs/evidence/RUN-20260602_project-bootstrap.md`: historical/supporting
  bootstrap evidence from before the MyWebTemplate rebaseline.
- `docs/evidence/RUN-20260602_market-session-source-check.md`: KRX/NXT session
  source check for the current planning envelope.
- `docs/evidence/RUN-20260602_strategy-risk-rulebook.md`: docs-only evidence
  for the initial 2,000,000 KRW cash risk framework.
- `docs/evidence/RUN-20260602_ai-orchestration-layer.md`: docs-only evidence for
  the AI orchestration safety contract.
- `docs/evidence/RUN-20260602_broker-selection-kis.md`: docs-only evidence for
  selecting KIS as the current broker integration direction.
- `docs/evidence/RUN-20260602_broker-candidate-kb-blocked.md`: docs-only
  evidence for blocking KB Securities as a personal API candidate.

## Open Decisions

- Broker/API provider direction is selected as KIS. KB Securities is blocked as
  a practical personal API candidate unless future official confirmation proves
  otherwise. Internal fake broker execution is not used. First broker-backed
  execution is KIS KRX broker-adapter only after KIS API portal verification and an
  explicitly approved broker-network smoke; before that, only no-order dry-run
  validation is allowed.
- Market scope: Korea domestic stocks (`국장`) first.
- Technology stack is selected: Python 3 + FastAPI for backend API, trading
  runner, schedulers, adapters, AI orchestration, and storage services;
  TypeScript + Next.js/React for the read-only dashboard/operator console; and
  PostgreSQL for durable application storage. MyWebTemplate code skeletons and
  tooling patterns may be reused where suitable, but MyWebTemplate docs,
  product PST content, database names, schemas, migrations, tables, seed data,
  and app-specific behavior are excluded.
- Storage backend is selected: PostgreSQL plus date-partitioned runtime
  artifacts. Use database `hwistock`, schema `hwistock_core`, and
  `HWISTOCK_DATABASE_URL`; do not share MyWebTemplate database/schema,
  migrations, tables, or seed data.
- Strategy family: short-term intraday scalping/momentum (`단타`), using a
  10-20 minute holding hypothesis and per-trade candidate 1-5% price-move target
  band; signal design combines news/disclosure context with chart confirmation.
  The first-pass alpha/source/candle/liquidity/market-alert defaults are
  packaged for user approval in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.
- Capital policy: cash-only with 2,000,000 KRW starting capital; baseline
  minimal allocation/risk policy is minimum cash reserve ratio 0.25, maximum
  simultaneous holdings 5, and AI-assisted per-entry stop price capped by
  deterministic maximum -5% loss rules. Broad daily/account-level loss
  management is intentionally not selected for the first pass.
- Broker-visible broker-adapter balance is observed evidence only and does not
  expand hwiStock's 2,000,000 KRW risk-overlay capital. UNIT-009 Go-Check
  confirms adapter/unapproved endpoint separation and documents mode-gated KIS
  proof via the capability matrix and sanitized smoke cross-reference, but not a
  sizing-budget change. Current KIS capability is paper/mock KRX plus integrated
  market-data/account-truth helpers, with NXT enabled only in real investment
  mode and SOR still disabled.
- UI/dashboard scope is selected as read-only status, stored AI reports, logs,
  interactive AI conversation, and operator visibility. Direct buy/sell controls
  are excluded. A report-only AI panel without question input and backend answer
  flow does not satisfy the conversation scope.
  Default access is local-only `127.0.0.1` through local browser, SSH tunnel, or
  Chrome Remote Desktop. Public/LAN exposure needs later authenticated Set
  approval.
- Dashboard design route: no-design fallback plus Antigravity CLI `agy` with
  Gemini Pro design review before dashboard Go. The review packet is prepared
  at `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`.
- Home-server process manager is selected as `systemd` or an approved service
  manager for the official continuous adapter-backed evidence runner. Docker
  Compose is deferred; tmux/screen is early-experiment-only.
- Market calendar source, holiday handling, and exceptional-session handling are
  selected by `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`: KRX
  official trading-days/holidays and notices, NXT official session references,
  local cached runtime calendar, and later KIS `국내휴장일조회` cross-check only
  after approved broker-network integration.
- Alert channel and adapter-backed observation criteria are selected by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`: local-only
  alerts through systemd journal, `data/alerts`, dashboard audit panel when
  implemented, and daily close reports. The observation window is chosen by the
  operator and recorded as evidence metadata; P0 safety/evidence criteria and
  no-profit-threshold policy remain required.
- Market intelligence sources, crawler permissions, disclosure sources, chart
  data source, realtime quote source, and retention policy are partially
  selected. First Go source registry approves DART Open API, conditionally
  allows Naver Search API news after key/query/rate approval, defers KIND/KRX
  automation until terms/access checks, defers KIS broker data, and blocks
  general HTML scraping/unofficial APIs by default.
- AI provider/model direction is selected for planning: DeepSeek Pro, DeepSeek
  Flash, and ChatGPT Pro morning review. UNIT-005 closes first-pass schedules,
  `*/v0` schemas, normalized-bundle-only inputs, GPT Pro 07:20 cutoff, and
  network disabled / cost cap 0 defaults. Nonzero paid AI API cost/token caps
  remain a future approval item.
