# hwiStock Docs Index

`hwiStock` is a stock day-trading automation project. The initial project
contract prioritizes safety, observability, paper/sandbox validation, and clear
approval gates before any live brokerage integration or real-money order flow.
Before actual live operation, the project must pass at least one full week of
paper/sandbox testing with named evidence and an explicit user go/no-go approval.
The intended runtime target is a 24-hour home-server program/service, not a
Codex session. Codex is used for planning, implementation, review, and evidence
work; the trading runner must be an independently restartable service.
The first market scope is Korea domestic stocks (`국장`). The runtime has two
separate branches:

- Market intelligence branch: runs 24 hours for news, articles, disclosures, and
  other permitted public information ingestion.
- Trading branch: uses simple venue routing inside 08:00-20:00 KST. Route
  09:00-15:00 KST to KRX, and route the remaining trading envelope
  08:00-09:00 / 15:00-20:00 KST to NXT. Do not split this into additional
  session modes unless a future unit explicitly changes this policy.

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
an approved KIS paper/mock-investment KRX path. A bounded owner-approved KIS
paper/mock REST and websocket smoke passed on 2026-06-04, but ordinary Go rows
still run no-order dry-run validation unless a selected unit explicitly scopes
KIS paper/mock behavior. Current-authority UNIT-009 rebaseline Go-Check passed
on 2026-06-04 as docs-only capability verification: the official endpoint
families, paper/live separation, and NXT/SOR routing fields are documented in
the capability matrix, with sanitized bounded KIS paper/mock smoke
cross-referenced for proven KRX paper paths only. Local KIS references still
constrain paper/mock proof to the KRX path for several order/realtime APIs.
NXT/SOR remain venue/session parameters in the internal engine and must use
disabled/fallback behavior in KIS-facing paper runs until a later approved
real-account/support-confirmation gate. The actual paper balance and exact
current rate-limit numbers still require future account evidence. This closure
does not authorize new KIS/broker/network calls. The
paper/mock investment target budget is 10,000,000 KRW until the paper account
balance proves the actual value, and it is separate from the intended live
starting capital of 2,000,000 KRW cash.

AI orchestration direction is selected at the operating-skeleton level:
DeepSeek Pro runs hourly news/disclosure analysis across 24 hours, adds market
regime/session analysis during 08:00-19:00 KST, DeepSeek Flash handles intraday
candidate/chart/risk labels, and ChatGPT Pro is used as a 07:00 external morning
reviewer when browser automation succeeds before cutoff. The orchestrator, not
the models, moves data between these systems. AI outputs create candidate cards,
explanations, and review artifacts only; deterministic strategy/risk/order
state machines own order decisions.

## Current Rebaseline Status

The current code baseline changed on 2026-06-04 when MyWebTemplate-derived
`backend/` and `frontend-web/` code was imported. Earlier Ready-Set closure and
Go-Check evidence are now historical, not current Go authorization.

- Current rebaseline evidence:
  `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`
- Current Ready-Set reissue evidence:
  `docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md`
- Current Ready-Set state: `implementation_ready: true` for the
  `skeleton_sandbox_safe_rebaseline_queue` only; this is **not** operational
  trading readiness.
- Current Ready-Set docs:
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
- Current browser UI Prove evidence:
  - `docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`
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
are first-row requirements for Go-Check, not optional cleanup. All nine units
are in the `skeleton_sandbox_safe_rebaseline_queue`; all nine units
(`HWISTOCK-UNIT-001` through `HWISTOCK-UNIT-009`) have current Go-Check PASS
evidence, including `HWISTOCK-UNIT-007`
(`docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md`). Current local
dashboard/API defaults are dashboard/frontend `127.0.0.1:5000` and backend/API
`127.0.0.1:5001`; hwibuntu access uses SSH local forwarding, recorded in
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
login/API 500 fix re-Prove passed: Chrome confirmed a hwiStock-branded public
login surface without template/demo residue, authenticated dashboard rendering,
masked account-like values, and no visible API 500
(`docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md`).
Commit-prep scope audit confirmed `git add -A --dry-run` candidates exclude
local config/env/log/cache paths after `.gitignore` cleanup, and no staging or
commit has been performed
(`docs/evidence/RUN-20260605_commit-prep-scope-audit.md`).
Historical GPT/design reviews are supporting constraints only and were not
re-run after the import. No operational trading, live brokerage, AI provider
network use, or public dashboard exposure is authorized.

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
- `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`: KIS API paper/live
  capability, fallback, and live-verification matrix for local `apiRefer`
  spreadsheets.
- `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`: KRX/NXT calendar
  source, local alert channel, and one-week paper/sandbox pass criteria.
- `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`: prepared
  user-approval packet for first-pass strategy defaults.
- `docs/set/READY-SET-EXTERNAL-REVIEW-PACKET-20260602_hwistock.md`: historical
  safe sharing scope for the pre-import final external review.
- `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`:
  prepared `agy` Gemini Pro dashboard design review packet.
- `docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md`: historical
  pre-import requirement-by-requirement audit. The current post-import authority
  is the 2026-06-04 rebaseline completion, row closure, and Go preflight set.
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
- `docs/set/KIS-PAPER-MOCK-API-SMOKE-MATRIX-20260604_hwistock.md`: approved
  but currently blocked KIS paper/mock API smoke matrix, including mock order,
  modify, and cancel calls for the KRX paper path.
- `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260603_foundation.md`:
  historical normalized ChatGPT Pro external review findings for the narrowed
  foundation-only queue.
- `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_dashboard-design.md`:
  normalized `agy` dashboard design findings for `HWISTOCK-UNIT-007`.
- `docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260604_full.md`: normalized
  ChatGPT Pro external review findings for full queue closure with exclusions.

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
  dashboard/operator console and AI conversation surface contract;
  `go_check_passed`
  (`docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md`).
- `docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md`: date-based data,
  analysis artifact, PostgreSQL storage, trade log, and evidence storage
  contract.

## Units

- `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md`:
  set project bootstrap and safety-first planning setup;
  `go_check_passed` for docs-only rebaseline verification
  (`docs/evidence/RUN-20260604_unit-001-go-check-rebaseline.md`). MyWebTemplate
  quarantine guardrails are recorded as first-row blockers for affected future
  rows; product-code removal remains out of UNIT-001 scope.
- `docs/units/HWISTOCK-UNIT-002_home-server-paper-runner.md`:
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
  paper capability flags
  (`docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md`).
- `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md`:
  `go_check_passed` read-only dashboard/operator console with tasks/settings
  subroutes, root/public/sample quarantine, masked/sanitized values, and
  local-only/public exposure boundary. Current local ports are
  dashboard/frontend `5000` and backend/API `5001`, with hwibuntu access through
  SSH local forwarding
  (`docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md`;
  `docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md`).
- `docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md`:
  `go_check_passed` storage and evidence skeleton using PostgreSQL database
  `hwistock`, schema `hwistock_core`, date-partitioned artifacts, hwiStock DB
  isolation, typed artifact contracts, and focused tests.
- `docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md`:
  `go_check_passed` for current-authority rebaseline KIS API official portal
  and capability-matrix verification with sanitized KRX paper smoke
  cross-reference and preserved partial-boundary follow-ups
  (`docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`).

## QA Scenarios

- `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md`:
  set QA to prove that the bootstrap docs, safety gates, and rebaseline
  quarantine guardrails are present before implementation begins.
- `docs/qa/QA-HWISTOCK-UNIT-002_home-server-paper-runner.md`:
  `go_check_passed` QA for service lifecycle skeleton, health, logging, kill
  switch, local-only bind, and paper/no-order operation.
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
  order states, dry-run-only boundary, KIS paper capability flags, and
  fixture-only broker-evidence representation
  (`docs/evidence/RUN-20260604_unit-006-go-check-rebaseline.md`).
- `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md`:
  `go_check_passed` QA for read-only dashboard behavior, sensitive-data masking,
  design review route, MyWebTemplate branding/sample/public route quarantine,
  local-only access boundary, and dashboard/API `5000`/`5001` port defaults
  with SSH local forwarding
  (`docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md`;
  `docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md`).
- `docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md`:
  `go_check_passed` QA for PostgreSQL isolation, storage separation,
  system-calculated PnL, hwiStock DB isolation, and one-week evidence
  linkability.
- `docs/qa/QA-HWISTOCK-UNIT-009_kis-api-portal-verification.md`:
  `go_check_passed` QA for current-authority rebaseline KIS API portal
  verification with partial-boundary items preserved and no new KIS/broker
  authorization (`docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md`).

## Evidence

- Historical evidence files preserve earlier planning assumptions. If they
  conflict with the current profile/module/unit contracts or the latest
  Ready-Set evidence, treat the current contracts as authoritative.
- `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`:
  current rebaseline evidence explaining why the prior queue was superseded by
  the MyWebTemplate code import.
- `docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md`:
  current Ready-Set reissue evidence after the owner selected MyWebTemplate
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
- `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke-approval-preflight.md`:
  owner approval and blocked environment preflight for KIS paper/mock API smoke
  including mock orders.
- `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md`: sanitized KIS
  paper/mock REST and websocket smoke evidence; token, quote, balance, buyable,
  mock buy order, cancel, daily order/fill, websocket fill-notice ACK, and token
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
  transitions, KIS paper capability flags, fixture-only evidence
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
  transitions, no-order dry-run records, KIS paper capability flags, focused
  tests, and rule-gates without broker-backed paper authorization; invalidated
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
  sanitized KRX paper smoke cross-reference, historical worker/fallback
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
  Ready-Set architecture evidence after the AI, dashboard, paper/mock budget,
  KIS verification, and minimal risk-policy brainstorming pass.
- `docs/evidence/RUN-20260602_unit-008-data-evidence-storage-set.md`: Set
  evidence for choosing PostgreSQL storage with hwiStock-specific
  database/schema isolation.
- `docs/evidence/RUN-20260602_unit-003-market-intelligence-set.md`: Set
  evidence for DART-first market-intelligence ingestion, conditional Naver news
  API use, and deferred/blocked source handling.
- `docs/evidence/RUN-20260602_unit-009-kis-api-portal-verification-set.md`: Set
  evidence for KIS official endpoint-family verification, paper/live separation,
  paper-constrained API behavior, fallback needs, and remaining broker-smoke
  items.
- `docs/evidence/RUN-20260602_unit-006-trading-engine-order-state-set.md`: Set
  evidence for condition schema, order state machine, no-order dry-run, KIS KRX
  paper adapter capability, and reconciliation/fallback behavior.
- `docs/evidence/RUN-20260602_unit-005-ai-orchestration-layer-set.md`: Set
  evidence for AI job registry, schemas, GPT cutoff, tool-use disabled policy,
  AI network disabled defaults, and fallback behavior.
- `docs/evidence/RUN-20260602_stack-rule-preset-set.md`: Set evidence for
  selecting Python/FastAPI backend, TypeScript/Next.js dashboard, PostgreSQL,
  Alembic migrations, and HWI FastAPI/Next/DB rule presets.
- `docs/evidence/RUN-20260602_unit-004-strategy-risk-rulebook-set.md`: Set
  evidence for reserve-floor sizing, maximum simultaneous holdings 5, and
  AI-assisted stop policy capped by deterministic maximum -5% loss.
- `docs/evidence/RUN-20260602_unit-002-home-server-paper-runner-set.md`: Set
  evidence for systemd runner lifecycle, source-unconfigured idle behavior, and
  local-only health/API surfaces.
- `docs/evidence/RUN-20260604_unit-002-go-preflight.md`: Go preflight evidence
  for the bounded UNIT-002 runner/systemd skeleton row.
- `docs/evidence/RUN-20260604_unit-002-go-check.md`: Go-Check evidence for
  the UNIT-002 local-only paper runner skeleton, no-order status API,
  loopback-only bind, `--once` runner entrypoint, and worker/review closure.
- `docs/evidence/RUN-20260602_unit-007-dashboard-operator-console-set.md`: Set
  evidence for read-only dashboard scope, local-only access, no-design fallback,
  first-screen sections, and AI conversation boundary.
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
  browser UI re-Prove PASS evidence after login public-surface quarantine and
  dashboard Decimal JSON-safe response conversion. Captures the hwibuntu
  tunnel/Chrome Extension route, focused backend/frontend tests, BFF login and
  dashboard API smoke, and login/dashboard screenshots.
- `docs/evidence/RUN-20260605_commit-prep-scope-audit.md`: current commit-prep
  scope audit. It records the read-only Cursor worker audit, `.gitignore`
  cleanup for local config/test-config/log artifacts, `git add -A --dry-run`
  candidate count, excluded path classes, and Korean commit-message suggestion.
- `docs/evidence/RUN-20260602_calendar-alert-paper-gate-set.md`: Set evidence
  for KRX/NXT calendar source hierarchy, local-only alert channel, and one-week
  paper/sandbox pass criteria.
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
  execution is KIS KRX paper/mock only after KIS API portal verification and an
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
- Official paper/mock-investment target budget: 10,000,000 KRW, pending future
  KIS paper balance evidence. UNIT-009 Go-Check confirms paper/live endpoint
  separation and documents KRX-bounded paper proof via the capability matrix and
  sanitized smoke cross-reference, but not the actual paper balance. KIS paper
  proof is KRX-limited where the local API references mark NXT/SOR,
  integrated realtime, holiday, sellable quantity, or helper lookup APIs as
  paper-unsupported.
- UI/dashboard scope is selected as read-only status, reports, logs, AI
  conversation, and operator visibility. Direct buy/sell controls are excluded.
  Default access is local-only `127.0.0.1` through local browser, SSH tunnel, or
  Chrome Remote Desktop. Public/LAN exposure needs later authenticated Set
  approval.
- Dashboard design route: no-design fallback plus Antigravity CLI `agy` with
  Gemini Pro design review before dashboard Go. The review packet is prepared
  at `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`.
- Home-server process manager is selected as `systemd` for the official
  one-week paper/sandbox evidence runner. Docker Compose is deferred; tmux/screen
  is early-experiment-only.
- Market calendar source, holiday handling, and exceptional-session handling are
  selected by `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`: KRX
  official trading-days/holidays and notices, NXT official session references,
  local cached runtime calendar, and later KIS `국내휴장일조회` cross-check only
  after approved broker-network integration.
- Alert channel and one-week paper/sandbox pass criteria are selected by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`: local-only
  alerts through systemd journal, `data/alerts`, dashboard audit panel when
  implemented, and daily close reports; one-week gate is 7 calendar days,
  at least 5 valid market-open days, P0 safety/evidence criteria, and no profit
  threshold.
- Market intelligence sources, crawler permissions, disclosure sources, chart
  data source, realtime quote source, and retention policy are partially
  selected. First Go source registry approves DART Open API, conditionally
  allows Naver Search API news after key/query/rate approval, defers KIND/KRX
  automation until terms/access checks, defers KIS broker data, and blocks
  general HTML scraping/unofficial APIs by default.
- AI provider/model direction is selected for planning: DeepSeek Pro, DeepSeek
  Flash, and ChatGPT Pro morning review. UNIT-005 closes first-pass schedules,
  `*/v0` schemas, normalized-bundle-only inputs, GPT Pro 07:20 cutoff, and
  network disabled / cost cap 0 defaults. Nonzero live AI API cost/token caps
  remain a future approval item.
