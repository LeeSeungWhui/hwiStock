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
KIS paper/mock behavior. The UNIT-009 docs-only pass confirmed the official
endpoint families, paper/live separation, and NXT/SOR routing fields, but local
KIS references constrain paper/mock proof to the KRX path for several
order/realtime APIs. NXT/SOR remain venue/session parameters in the internal
engine and must use disabled/fallback behavior in KIS-facing paper runs until a
later approved real-account/support-confirmation gate. The actual paper balance
and exact current rate-limit numbers still require future account evidence. The
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
- `docs/set/READY-SET-EXTERNAL-REVIEW-PACKET-20260602_hwistock.md`: prepared
  safe sharing scope for the current final external review.
- `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`:
  prepared `agy` Gemini Pro dashboard design review packet.
- `docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md`: current
  requirement-by-requirement audit proving Ready-Set completion for the
  `full_queue_skeleton_sandbox_safe` queue.
- `docs/set/READY-SET-APPROVAL-ACTIONS-20260602_hwistock.md`: exact owner
  approval choices, receipt checklist, and current full expansion closure refs.
- `docs/set/READY-SET-FOUNDATION-QUEUE-PROPOSAL-20260602_hwistock.md`:
  inactive proposal for a narrower foundation-only Go queue.
- `docs/set/READY-SET-EXTERNAL-REVIEW-PROMPT-20260602_hwistock.md`: prepared
  safe prompt for the current final external review, not sent.
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
- `docs/set/READY-SET-GATE-EVIDENCE-MATRIX-20260603_hwistock.md`: prepared
  matrix mapping each Ready-Set completion-gate requirement to current full
  queue pass evidence.
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
  dashboard/operator console and AI conversation surface contract.
- `docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md`: date-based data,
  analysis artifact, PostgreSQL storage, trade log, and evidence storage
  contract.

## Units

- `docs/units/HWISTOCK-UNIT-001_project-bootstrap.md`: set project bootstrap
  and safety-first planning setup.
- `docs/units/HWISTOCK-UNIT-002_home-server-paper-runner.md`: set 24-hour
  home-server paper/sandbox runner contract.
- `docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md`: set
  24-hour market intelligence ingestion contract with DART-first source
  allowlist and blocked/deferred source policy.
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`: set strategy
  and minimal risk parameter contract for candidate selection, entries, exits,
  minimum cash reserve ratio 0.25, maximum simultaneous holdings 5, and
  AI-assisted stop policy capped by deterministic risk gates.
- `docs/units/HWISTOCK-UNIT-005_ai-orchestration-layer.md`: set AI
  orchestration schedule, schema, fallback, tool-boundary, and network-default
  contract.
- `docs/units/HWISTOCK-UNIT-006_trading-engine-order-state.md`: set trading
  engine, order state-machine, no-order dry-run, KIS paper adapter, and
  fallback contract.
- `docs/units/HWISTOCK-UNIT-007_dashboard-operator-console.md`: set
  dashboard/operator console contract.
- `docs/units/HWISTOCK-UNIT-008_data-evidence-storage.md`: set storage and
  evidence contract using PostgreSQL database `hwistock`, schema
  `hwistock_core`, and date-partitioned artifacts.
- `docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md`: set KIS API
  official portal verification contract before any broker network call.

## QA Scenarios

- `docs/qa/QA-HWISTOCK-UNIT-001_project-bootstrap.md`: set QA to prove that the bootstrap
  docs and safety gates are present before implementation begins.
- `docs/qa/QA-HWISTOCK-UNIT-002_home-server-paper-runner.md`: set QA for
  service lifecycle, health, logging, kill switch, and paper-only operation.
- `docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md`: set QA for
  allowed-source ingestion, blocked-source enforcement, deduplication, rate
  limiting, and evidence.
- `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`: set QA for
  strategy/risk rule completeness, cash-reserve/holdings caps, order blocking, and paper-run
  evidence.
- `docs/qa/QA-HWISTOCK-UNIT-005_ai-orchestration-layer.md`: set QA for AI
  output schema, citation/source grounding, no-direct-order behavior, and
  deterministic risk-gate enforcement.
- `docs/qa/QA-HWISTOCK-UNIT-006_trading-engine-order-state.md`: set QA for
  condition compiler, deterministic buy gate, explicit order states, and
  no-order dry-run / KIS paper adapter boundary.
- `docs/qa/QA-HWISTOCK-UNIT-007_dashboard-operator-console.md`: set QA for
  read-only dashboard behavior, sensitive-data masking, and design review route.
- `docs/qa/QA-HWISTOCK-UNIT-008_data-evidence-storage.md`: set QA for
  PostgreSQL isolation, storage separation, system-calculated PnL, and one-week
  evidence linkability.
- `docs/qa/QA-HWISTOCK-UNIT-009_kis-api-portal-verification.md`: set QA for
  official KIS API portal verification before any broker network call.

## Evidence

- Historical evidence files preserve earlier planning assumptions. If they
  conflict with the current profile/module/unit contracts or the latest
  Ready-Set evidence, treat the current contracts as authoritative.
- `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`: current Ready-Set
  completion gate. It is `implementation_ready: true` for the
  `full_queue_skeleton_sandbox_safe` queue.
- `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`: current row-closure
  matrix for the active full skeleton/sandbox-safe Go-Check queue.
- `docs/evidence/RUN-20260604_gpt-pro-full-ready-set-review.md`: external
  ChatGPT Pro review evidence and local interpretation for full queue closure
  with exclusions.
- `docs/evidence/RUN-20260604_dashboard-design-review.md`: `agy` Gemini Pro
  dashboard design review evidence.
- `docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md`:
  owner decision receipt and pre-send evidence for the full expansion review.
- `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke-approval-preflight.md`:
  owner approval and blocked environment preflight for KIS paper/mock API smoke
  including mock orders.
- `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md`: sanitized KIS
  paper/mock REST and websocket smoke evidence; token, quote, balance, buyable,
  mock buy order, cancel, daily order/fill, websocket fill-notice ACK, and token
  revoke passed.
- `docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md`: Git
  initialization, PF-13 resolution, `.env` ignore policy, and Ready-Set delta
  sync evidence.
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
- `docs/evidence/RUN-20260602_unit-007-dashboard-operator-console-set.md`: Set
  evidence for read-only dashboard scope, local-only access, no-design fallback,
  first-screen sections, and AI conversation boundary.
- `docs/evidence/RUN-20260602_calendar-alert-paper-gate-set.md`: Set evidence
  for KRX/NXT calendar source hierarchy, local-only alert channel, and one-week
  paper/sandbox pass criteria.
- `docs/evidence/RUN-20260602_ready-set-decision-review-packets.md`: Set
  evidence for preparing the strategy decision packet, final external review
  packet, and dashboard design review packet without sending external data.
- `docs/set/READY-SET-COMPLETION-AUDIT-20260602_hwistock.md`: current
  completion audit showing pass/open-blocking state for module inventory, unit
  inventory, QA inventory, row closure, external review, and residual gaps.
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
  current full review superseded this with an 85-file candidate bundle recorded
  in `docs/evidence/RUN-20260604_full-ready-set-owner-decisions-presend.md`.
- `docs/evidence/RUN-20260603_row-closure-activation-draft.md`: evidence for
  preparing the inactive row-closure activation draft without authorizing Go.
- `docs/evidence/RUN-20260603_review-findings-intake-template.md`: evidence for
  preparing the future review findings intake template, including pre-send
  candidate count/exact-match/secret-scan fields, without running reviews.
- `docs/evidence/RUN-20260603_rule-preset-applicability-matrix.md`: evidence for
  preparing the unit-by-unit rule preset applicability matrix without running Go.
- `docs/evidence/RUN-20260603_gate-evidence-matrix.md`: evidence for preparing
  the Ready-Set gate evidence matrix without authorizing Go.
- `docs/evidence/RUN-20260603_root-vcs-env-scan.md`: evidence for the current
  root baseline: no git/svn detected, `env.sh` and `apiRefer/` present, and
  planned source/runtime folders not created yet.
- `docs/evidence/RUN-20260603_ready-set-current-state-snapshot.md`: current
  historical local Ready-Set state snapshot after foundation-only ChatGPT Pro
  review, row closure, and completion rewrite.
- `docs/evidence/RUN-20260603_owner-decision-receipt-template.md`: evidence for
  preparing the future owner decision receipt template, including Action 3
  pre-send candidate checks, without recording any approval.
- `docs/evidence/RUN-20260602_unit-001-project-bootstrap-set.md`: Set evidence
  for closing the docs-only bootstrap/profile safety contract.
- `docs/evidence/RUN-20260602_project-bootstrap.md`: current bootstrap evidence.
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
  KIS paper balance evidence. UNIT-009 confirms paper/live endpoint separation
  and paper credentials/account fields, but not the actual paper balance. KIS
  paper proof is KRX-limited where the local API references mark NXT/SOR,
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
