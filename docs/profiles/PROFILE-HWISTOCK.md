---
schema_version: hwi.profile/v0
id: PROFILE-HWISTOCK
type: profile
name: hwiStock project profile
project_root: /data/workspace/My/hwiStock
docs_base: docs
status: active
owner: hwi
updated_at: 2026-06-04
vcs_adapter: git
frameworks:
  - python
  - fastapi
  - typescript
  - nextjs
  - react
  - postgresql
rule_presets:
  - fastapi-backend-rule-preset
  - next-frontend-rule-preset
  - db-naming-rule-preset
default_stage_routes:
  ready:
    - hwi-work-harness
  set:
    - hwi-work-harness
  go:
    - hwi-work-harness
    - delegation-guard
  check:
    - hwi-work-harness
  prove:
    - hwi-work-harness
approval_required_for:
  - module_contract_change
  - rule_exception
  - worker_implementation
  - side_effect_qa
  - production_operation
  - broker_network_operation
  - external_broker_api_network_operation
  - live_order_placement
  - credential_storage
  - real_money_trading
  - strategy_risk_parameter_change
  - ai_api_provider_selection
  - ai_api_network_operation
  - ai_prompt_or_model_change
---

# hwiStock Project Profile

## 1. Purpose

This profile configures Hwi Work Harness for `hwiStock`, a stock day-trading
automation project. The profile is intentionally safety-first: no code path,
test, worker, or QA run may place real orders or access real brokerage accounts
until the required approvals, sandbox evidence, and risk controls are documented.
Actual live operation also requires at least one full week of paper/sandbox
testing with named evidence and an explicit user go/no-go approval.
The intended runtime is a 24-hour home-server program/service. Codex sessions are
not the runtime; they are used for development, review, and verification.
The first market scope is Korea domestic stocks (`국장`). The runtime has two
branches:

- `market_intelligence`: 24-hour ingestion of permitted public news, articles,
  disclosures, chart/market-data context, and related signals.
- `trading`: simple venue-routed strategy/risk/order loop. Use KRX from
  09:00-15:00 KST and NXT for 08:00-09:00 / 15:00-20:00 KST. Do not model
  additional session modes unless a future unit explicitly changes this policy.

This project is tooling and automation work, not investment advice. Strategy
documentation must distinguish hypotheses, backtest results, paper-trading
results, and live-trading evidence.

Strategy direction is short-term day trading (`단타`) with a fast intraday
scalping/momentum hypothesis: approved-signal entries, typical 10-20 minute
holding window, per-trade candidate 1-5% price-move target band, and quick exit
on invalidated signals or predefined risk triggers. This target band is not a
daily account return target. The 08:00-20:00 trading envelope is an
observation/opportunity window, not permission to trade continuously. Capital
policy is cash-only. Credit, margin, 미수, borrowed funds, or other leveraged
capital are forbidden by default. Initial starting capital is 2,000,000 KRW cash.
AI API orchestration may be used for candidate synthesis, ranking, explanation,
and paper-run review, but AI outputs cannot directly place orders or override
deterministic risk controls.
Broker/API provider direction is selected as Korea Investment & Securities Open
API (`KIS`, 한국투자증권). KB Securities (`KB증권`) is treated as not usable for this
personal-account automation project unless a future official confirmation proves
otherwise. hwiStock will not use an internal fake broker adapter as the first
execution path. The first broker-backed execution path is an approved KIS
paper/mock-investment KRX path. Before that explicit broker-network approval,
the engine may run only no-order dry-run validation that records candidate,
risk, and order-intent decisions without simulating broker fills.
UNIT-009 confirms, from official docs/samples, KIS domestic
order/account/realtime endpoint families, paper/live separation,
personal-account eligibility, and NXT/SOR order-routing fields. Local KIS
reference files constrain the official paper/mock path to KRX for several
order/realtime flows, so KIS paper evidence must not be treated as proof of
NXT/SOR broker behavior. NXT/SOR are engine-level venue/session parameters over
the same state machine, with KIS-specific NXT/SOR branches disabled or
explicit-fallback-only during KIS paper runs until a later approved
real-account/support-confirmation gate. Actual KIS paper balance and exact
current rate limits still require a future explicitly approved broker-network
smoke.
Paper/mock investment target budget is 10,000,000 KRW until paper balance
evidence proves the actual value. This paper target is separate from the
intended live starting capital of 2,000,000 KRW cash.

AI orchestration direction is selected for planning: DeepSeek Pro handles
hourly news/disclosure analysis across 24 hours, with market-regime/session
analysis added during 08:00-19:00 KST; DeepSeek Flash handles intraday
lightweight candidate, chart, and risk-label analysis; ChatGPT Pro is used as a
07:00 external morning reviewer through browser automation when available. AI
never places orders. The hwiStock orchestrator submits prompts and stores
answers; DeepSeek, Flash, and GPT Pro do not hold broker credentials or order
permissions.

## 2. Project Layout

- Project root: `/data/workspace/My/hwiStock`
- Root AGENTS: `AGENTS.md`
- Docs root: `docs/`
- Profile: `docs/profiles/PROFILE-HWISTOCK.md`
- Modules: `docs/modules/`
- Units: `docs/units/`
- QA scenarios: `docs/qa/`
- Evidence: `docs/evidence/`
- Archive/backlog: `docs/archive/`
- Source code: present after MyWebTemplate backend/frontend-web import; current
  code baseline requires Ready-Set rebaseline before Go resumes
- Backend/API/trading runtime source: `backend/` (present; MyWebTemplate-derived
  FastAPI/backend skeleton)
- Backend entrypoint: `backend/server.py` (present; imported template entrypoint)
- Backend layers: `backend/router/`, `backend/service/`, `backend/query/`,
  `backend/lib/`, and `backend/tests/` (present as imported template layers;
  hwiStock domain files must be re-ported or re-implemented)
- Backend migrations: `backend/migrations/` using Alembic (present for the
  UNIT-008 storage skeleton; future domain migrations must keep
  hwiStock-specific schema isolation)
- Frontend dashboard source: `frontend-web/` (present; MyWebTemplate-derived
  Next.js app skeleton)
- Frontend app root: `frontend-web/app/` (present)
- Frontend component/library roots: `frontend-web/components/` and
  `frontend-web/lib/` (verify exact imported structure during rebaseline)
- Frontend tests: `frontend-web/tests/` and `frontend-web/__tests__/` (present
  as imported template tests)
- Ops/deployment config: `ops/systemd/` (planned)
- Environment setup: `source ./env.sh`
- Local dev ports: dashboard/frontend `127.0.0.1:5000`, backend/API
  `127.0.0.1:5001`
- hwibuntu dashboard access: use SSH local forwarding from hwibuntu to
  hwiServer, for example `ssh -N -L 5000:127.0.0.1:5000 -L
  5001:127.0.0.1:5001 hwiServer`; do not bind hwiStock services to LAN/public
  addresses for this access path.
- Environment files:
  - `env.sh`: project toolchain/default env loader, adapted from
    MyWebTemplate's env layout
  - `/home/hwi/.config/hwistock/hwistock.env`: optional project-local config
  - `/home/hwi/.config/hwistock/deepseek.env`: optional AI provider secrets
  - `/home/hwi/.config/hwistock/source-apis.env`: optional DART/Naver/source API
    secrets
  - `/home/hwi/.config/hwistock/kis-paper.env`: optional KIS paper/mock secrets
- Generated output folders: not created yet
- Runtime target: home server, 24-hour service/process managed by `systemd`
  for the one-week paper/sandbox evidence run
- Market scope: Korea domestic stocks (`국장`) first
- Trading venues: KRX + NXT
- Trading routing policy: 09:00-15:00 KST -> KRX; 08:00-09:00 and 15:00-20:00
  KST -> NXT
- Broker/API direction: Korea Investment & Securities Open API (`KIS`)
- Blocked broker candidate: KB Securities personal use is blocked unless later
  official confirmation proves otherwise
- First broker-backed execution adapter: KIS KRX paper/mock-investment path;
  the first bounded paper/mock smoke is complete, but adapter integration and
  future broker calls still require explicit unit scope
- Internal fake broker adapter: not used by project direction; no
  `mock_broker_api` execution path
- Pre-approval execution behavior: no-order dry-run only, recording candidate,
  risk, and order-intent decisions without broker fill simulation
- Broker-provided mock/demo/testbed/sandbox API mode: KIS KRX-paper path only
  under explicit unit/smoke approval; NXT/SOR stay disabled or
  explicit-fallback-only until later real-account/support-confirmation
- Paper/mock-investment target budget: 10,000,000 KRW, pending KIS paper balance
  evidence
- KIS API mode: the first bounded paper/mock REST and websocket smoke passed in
  `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md`; ordinary Go rows
  still must not call KIS/broker APIs unless the selected unit explicitly scopes
  that behavior
- KIS paper validation boundary: current local KIS references prove only the KRX
  paper route for the relevant order/realtime flows. NXT/SOR are not paper-proven
  and must stay disabled or explicit-fallback-only in KIS paper runs.
- Current root baseline as of 2026-06-04:
  - Git working tree: initialized from `/data/workspace/My/hwiStock`.
  - Active branch: `main`.
  - SVN working copy: not detected from `/data/workspace/My/hwiStock`.
  - `env.sh`: present; existence checked only, contents not read in the root
    scan.
  - `.gitignore`: present; `.env`, `.env.*`, and `*.env` are ignored while
    `.env.example` templates remain allowed.
  - `apiRefer/`: present with local KIS reference spreadsheets; excluded from
    external review sharing by default.
  - `backend/`: present with MyWebTemplate-derived FastAPI/backend skeleton.
  - `frontend-web/`: present with MyWebTemplate-derived Next.js app skeleton.
  - `backend/config.ini`, `frontend-web/config.ini`: local ignored template
    config; do not read, print, or commit contents.
  - `ops/systemd/`: not created yet.
  - `data/`: project data directory policy exists; current runtime contents are
    not Ready-Set completion evidence.
  - Root baseline evidence:
    `docs/evidence/RUN-20260603_root-vcs-env-scan.md`
  - Git initialization evidence:
    `docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md`
- Strategy direction: short-term day trading (`단타`)
- Strategy tempo: fast intraday scalping/momentum, candidate 10-20 minute hold,
  per-trade 1-5% price-move target band, evidence required before live use
- Capital policy: cash-only; no credit, margin, 미수, borrowed funds, or leveraged
  capital by default
- Starting capital: 2,000,000 KRW cash
- All-in policy: forbidden by default
- Baseline risk parameter source:
  `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`
- AI orchestration source:
  `docs/modules/HWISTOCK-MOD-004_ai-orchestration-layer.md`
- Trading engine/order state source:
  `docs/modules/HWISTOCK-MOD-005_trading-engine-order-state.md`
- Dashboard/operator console source:
  `docs/modules/HWISTOCK-MOD-006_dashboard-operator-console.md`
- Data/evidence storage source:
  `docs/modules/HWISTOCK-MOD-007_data-evidence-storage.md`
- Storage backend: PostgreSQL with hwiStock isolation
  - database: `hwistock`
  - schema: `hwistock_core`
  - env var: `HWISTOCK_DATABASE_URL`
  - do not share MyWebTemplate database/schema/migrations/tables
- KIS API verification source:
  `docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md`
- KIS API capability matrix:
  `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`
- Market calendar, alert, and one-week paper gate policy:
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`
- 24-hour branch: market intelligence ingestion, not order execution
- Market calendar: selected source hierarchy is KRX official trading-days/
  holidays and notices, NXT official session notices, approved local cached
  calendar, and later KIS `국내휴장일조회` as broker-side cross-check only after
  explicit broker-network approval.
- Selected technology stack: Python 3 + FastAPI for the backend API, trading
  runner, schedulers, adapters, AI orchestration, and storage services;
  TypeScript + Next.js/React for the read-only dashboard/operator console; and
  PostgreSQL for durable application storage.
- Dashboard is frontend-web only. No mobile/frontend-app scope exists unless a
  future unit explicitly adds it.
- Dashboard/API bind policy: default local-only bind to `127.0.0.1`. Operator
  access uses local browser, Chrome Remote Desktop, or SSH tunnel. The current
  local dev ports are dashboard/frontend `5000` and backend/API `5001`; hwibuntu
  access should forward local `127.0.0.1:5000`/`5001` to hwiServer
  `127.0.0.1:5000`/`5001` through SSH. LAN/public IP exposure requires a later
  explicit Set approval with authentication and allowlist/VPN/reverse-proxy
  controls; "unknown URL" secrecy is not an accepted access-control mechanism.
- MyWebTemplate `backend/` and `frontend-web/` code is now physically imported
  and is the current skeleton baseline. Its app-specific routes, branding,
  database/config assumptions, sample data, public routes, and bind behavior are
  not automatically accepted as hwiStock product behavior; they must be kept,
  renamed, quarantined, or removed during Ready-Set rebaseline and subsequent
  Go-Check.

## 2.1 Current Rebaseline Notice

The earlier full Ready-Set closure and Go-Check queue are superseded by
`docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`.
Do not treat prior `implementation_ready: true`, `ready_for_go_check`, or
`go_check_passed` labels as current until the Ready-Set bundle is reissued
against the imported MyWebTemplate code baseline.

## 3. Source Of Truth Order

1. User instruction in the current task.
2. Root `AGENTS.md`.
3. This profile.
4. Module, unit, and QA scenario docs.
5. Code/runtime evidence after implementation starts.
6. Broker/API official documentation when a provider is selected.
7. Prior evidence and memento memories.

Design source policy: no UI design source exists yet. For non-visual engine and
docs work, no-design fallback is acceptable. UI/dashboard work must record its
visual basis in the unit and QA scenario before Go.

## 4. Default Stage Routing

- `ready`: `hwi-work-harness`
- `set`: `hwi-work-harness`; use external collaboration for non-trivial strategy,
  risk, architecture, or QA scenario refinement when the user asks for it.
- `go`: `hwi-work-harness` + `delegation-guard`
- `check`: `hwi-work-harness`; add external review for broker credentials, order
  placement, live trading, or risk-control changes.
- `prove`: `hwi-work-harness`

## 5. Rule Presets

Active common rule presets:

- `fastapi-backend-rule-preset`: applies to `backend/`, including the FastAPI
  API surface, trading runner services, AI orchestration services, KIS adapter
  boundaries, storage services, and tests.
- `next-frontend-rule-preset`: applies to `frontend-web/`, limited to the
  read-only dashboard/operator console.
- `db-naming-rule-preset`: applies to PostgreSQL schemas, migrations, queries,
  table/view/column names, and database evidence.

Rule-gate adapter:

- Use `hwi-rule-gate` after implementation code exists. Default command shape:
  `python3 "$CODEX_HOME/skills/hwi-rule-gate/scripts/rule_gate.py" /data/workspace/My/hwiStock --changed --fail-on-warn`.
- Docs-only Ready/Set work uses the manual checklist below plus contract review.
- Warnings block completion unless a unit/profile records an explicit accepted
  exception.

Manual checklist review always includes:

- no live order placement by default
- no credential leakage
- clear paper/sandbox/live environment separation
- broker adapter separation: no internal fake broker execution path; KIS/external
  broker network adapters disabled until approved; broker-provided paper/mock
  APIs allowed only after UNIT-009 docs verification plus explicit
  broker-network smoke approval
- KIS paper adapter capability must expose KRX-only support where the local KIS
  references mark NXT/SOR or integrated realtime feeds paper-unsupported
- market-session-aware scheduler for Korea domestic trading days, holidays, and
  exceptional sessions
- branch separation between 24-hour information ingestion and market-session
  trading/order routing
- permitted-source policy for news/article/disclosure collection
- approved chart/market-data source policy before chart signals are enabled
- AI API output must be structured, source-grounded, audited, and unable to
  invoke broker/order interfaces directly
- explicit minimal position-risk controls before any order path: minimum cash
  reserve floor, maximum simultaneous holdings, and stop-loss trigger
- cash-only capital policy before any order path
- all-in single-stock deployment blocked by default
- at least one full week of paper/sandbox testing before live operation
- overtrading controls for the 08:00-20:00 envelope are not part of the first
  minimal risk policy unless a future Set decision adds them; signal-quality and
  stale-data gates still apply
- audit logging for signals, decisions, orders, and failures
- reproducible evidence for backtest and paper-trading claims
- PostgreSQL storage isolation: hwiStock must use a separate database/schema
  from MyWebTemplate and must not share migrations, tables, or seed data

### 5.1 FastAPI Backend Profile

- Backend root: `backend/`
- App entrypoint: `backend/server.py`
- Router root: `backend/router/`
- Service root: `backend/service/`
- Query root: `backend/query/`
- Shared library root: `backend/lib/`
- Test root: `backend/tests/`
- Migration root: `backend/migrations/`
- API version prefix: `/api/v1`
- Response envelope: `{ status, message, result, count?, code?, requestId }`
- Response helpers: `successResponse`, `errorResponse`, and `ServiceError`
  unless a future unit records a profile exception.
- Request payload reader/helper names: `readRequestPayload` and
  `validateRequestPayload` unless a future unit records a profile exception.
- Layer pattern: `router / service / query`.
- Runtime naming: Hwi-FastAPI preset defaults apply, including camelCase
  variables/functions/methods, PascalCase classes/types, and UPPER_SNAKE_CASE
  constants.
- DB migration tool: Alembic.
- DB naming preset: `db-naming-rule-preset`.
- Persistence mode: PostgreSQL database `hwistock`, schema `hwistock_core`,
  env var `HWISTOCK_DATABASE_URL`.
- Healthcheck path: `/api/v1/health`.
- Auth/session mode: unresolved for dashboard access; no route may expose
  broker credentials, raw account identifiers, or order placement without a
  later Set-approved unit.
- Product truthfulness: no fake save/load/send success, no fake broker fills,
  no fake broker balances, and no internal fake broker execution path.
- Warning policy: warnings block unless explicitly accepted in the unit/profile.
- Explicit exceptions: none approved.

### 5.2 Next Frontend Profile

- Frontend root: `frontend-web/`
- App root: `frontend-web/app/`
- Route root: `frontend-web/app/`
- Component roots: `frontend-web/app/lib/component`, `frontend-web/app/dashboard/components`
- Shared utility root: `frontend-web/app/lib/`
- Test root: `frontend-web/tests/`
- Runtime language policy: TypeScript.
- Runtime extensions: `.ts`, `.tsx`, plus framework/config files as required by
  the selected Next toolchain.
- Scope: read-only dashboard/operator console, status views, reports, logs,
  health, candidate visibility, and AI conversation surface.
- Forbidden scope: direct buy/sell controls, order placement buttons, broker
  credential entry, raw account-number display, or live operation approval UI.
- Styling/design basis: no prepared design source yet. UNIT-007 must record the
  no-design fallback or a prepared design source and may route design review to
  Antigravity CLI `agy` with Gemini Pro before Go.
- API boundary: dashboard reads backend API data only; frontend must not call
  broker or AI provider APIs directly.
- Warning policy: warnings block unless explicitly accepted in the unit/profile.
- Explicit exceptions: none approved.

## 6. Commands / Gates

Project environment command:

- `source ./env.sh`: apply MyWebTemplate-style local toolchain paths and load
  hwiStock config/secrets from `/home/hwi/.config/hwistock/*.env` without
  storing secrets in the repository.

Planned gate ids:

- `docs-bootstrap-check`: verify required AGENTS/profile/module/unit/QA/evidence
  docs exist.
- `risk-contract-check`: verify units touching trading logic include risk limits,
  kill switch behavior, and paper/live separation.
- `credential-safety-check`: verify credentials are referenced through env/secret
  stores and not committed.
- `storage-contract-check`: verify PostgreSQL database/schema isolation,
  `HWISTOCK_DATABASE_URL`, hwiStock migrations, artifact paths, hashes, and
  system-calculated PnL contracts.
- `paper-trading-smoke`: initial approved KIS KRX paper/mock REST and websocket
  smoke passed in `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md`;
  future expanded smoke gates cover longer order/fill, position, reject, and
  paper-budget behavior.
- `no-order-dry-run-smoke`: future smoke gate proving candidate, risk, and
  order-intent decisions are recorded without unscoped broker calls or simulated
  fills during ordinary Go implementation rows.
- `service-lifecycle-smoke`: future smoke gate for start, stop, restart, health,
  and log output of the home-server runner.
- `market-calendar-smoke`: future smoke gate for 09:00-15:00 KRX routing,
  08:00-09:00 / 15:00-20:00 NXT routing, out-of-envelope idle behavior,
  closed/stale-calendar idle behavior, and local cached-calendar coverage.
- `intel-ingestion-smoke`: future smoke gate for source allowlist, robots/terms
  compliance notes, deduplication, rate limiting, and disclosure/news evidence.
- `ai-orchestration-smoke`: future smoke gate for structured AI output,
  source-id grounding, prompt/model audit logs, and no direct order interface.
- `ai-policy-gate-smoke`: future smoke gate proving AI recommendations cannot
  bypass deterministic position-risk, capital, stale-data, or kill-switch rules.
- `kis-api-contract-check`: future docs/code gate for KIS endpoint mode,
  credentials, call limits, KRX/NXT support, personal-account eligibility, and
  no accidental live-order path.
- `official-paper-api-smoke`: initial approved KIS KRX paper/mock API smoke
  passed for token, quote, balance, buyable, one minimal paper buy, cancel,
  daily order/fill lookup, websocket fill-notice ACK, and token revoke. Future
  expanded paper API smoke still needs longer position/reject/paper-budget
  evidence. This gate does not prove NXT/SOR broker behavior under the current
  KIS paper constraints.
- `dashboard-readonly-access-smoke`: future smoke gate proving the dashboard
  exposes no direct order controls, masks sensitive values, binds local-only by
  default, and rejects public/LAN exposure unless a later Set contract approves
  authenticated access.

## 7. Approval Policy

Explicit approval is required before:

- changing the selected broker API provider
- enabling, integrating, or running any KIS or external broker API adapter
- storing or loading credentials
- any broker network call
- any KIS or external broker live, partner, demo, testbed, mock, paper, or
  sandbox network call unless a Set-approved KIS paper/mock unit explicitly
  scopes it
- any live account login
- any order placement, even paper/sandbox, unless the unit explicitly scopes it
- treating the system as live-ready before at least one full week of
  paper/sandbox testing has been completed and reviewed
- real-money trading
- production deployment or remote operation
- selecting an AI API provider/model or sending project data to an AI API
- changing AI prompt, output schema, model, tool permissions, or fallback policy
- changing capital allocation, stop-loss, max simultaneous holdings, or kill
  switch policy
- enabling credit, margin, 미수, borrowed funds, or any leveraged-capital mode
- enabling all-in or single-stock full-capital deployment

## 8. Evidence Policy

Evidence summaries live under `docs/evidence/`.

For trading-related work, evidence must label the environment:

- `docs_only`
- `backtest`
- `paper`
- `sandbox`
- `live_readonly`
- `live_order`

`live_order` evidence is forbidden until explicitly approved in a Set contract.
The earliest live-operation approval must link one full week of paper/sandbox
testing evidence, including dates, test environment, scenario coverage, order
simulation results, failures, fixes, and final go/no-go verdict.

## 9. Document Paths

- Profile: `docs/profiles/PROFILE-HWISTOCK.md`
- Module: `docs/modules/HWISTOCK-MOD-*_name.md`
- Unit: `docs/units/HWISTOCK-UNIT-*_name.md`
- QA scenario: `docs/qa/QA-HWISTOCK-UNIT-*_name.md`
- Evidence: `docs/evidence/RUN-YYYYMMDD_name.md`
- Archive/backlog: `docs/archive/YYYY-MM-DD_note.md`

## 10. Exceptions / Open Profile Questions

- Broker/API provider: selected as KIS.
- KB Securities (`KB증권`): blocked as a practical personal API candidate unless
  future official confirmation proves otherwise.
- First broker-backed execution adapter: KIS KRX paper/mock-investment path after
  explicit broker-network smoke approval. Internal fake broker execution is not
  used.
- Market scope: Korea domestic stocks first.
- Technology stack: selected as Python 3 + FastAPI backend/API/trading runner,
  TypeScript + Next.js/React read-only dashboard, and PostgreSQL storage.
- Strategy scope: short-term intraday scalping/momentum (`단타`) with draft
  10-20 minute hold and per-trade 1-5% price-move target band, but exact
  first-pass alpha/source/candle/liquidity/market-alert defaults require user
  approval of
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.
- Capital policy: cash-only with 2,000,000 KRW starting capital.
- Baseline capital allocation, all-in prohibition, risk limits, and kill switch
  policy are drafted in `HWISTOCK-MOD-003`. Current Set decisions: maximum
  simultaneous holdings is 5; order sizing must preserve
  `minimum_cash_reserve_ratio = 0.25` of total capital; AI may recommend a
  per-entry stop price, but deterministic risk gates cap accepted stops at a
  maximum -5% loss envelope.
- One-week paper/sandbox test acceptance criteria: selected by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`. The gate is at
  least 7 consecutive calendar days and at least 5 valid Korean market open
  days, with P0 safety/evidence/reconciliation criteria and no profit threshold.
- Paper/sandbox provider: KIS paper/mock API use is limited to the KRX-supported
  path unless later official evidence changes this. NXT/SOR remain
  venue/session parameters in the engine, but KIS-facing NXT/SOR branches stay
  disabled or explicit-fallback-only and require later
  real-account/support-confirmation evidence before live routing. Internal fake
  broker simulation is not used. Official paper/mock investment mode appears
  potentially usable and has a planned starting budget of 10,000,000 KRW.
- Dashboard/UI need: selected as read-only status/conversation dashboard. Direct
  buy/sell controls are excluded. Default access is local-only
  `127.0.0.1`/SSH-tunnel/Chrome-Remote-Desktop. Design route is no-design
  fallback plus Antigravity CLI `agy` with Gemini Pro as front-end design
  collaborator/reviewer before Go.
- Data/evidence storage: selected as PostgreSQL plus date-partitioned local
  artifacts. Use database `hwistock`, schema `hwistock_core`, and
  `HWISTOCK_DATABASE_URL`; do not overlap with MyWebTemplate database/schema,
  migrations, tables, or seed data.
- Data source and historical data licensing: unresolved.
- AI API provider/model direction: DeepSeek Pro, DeepSeek Flash, and ChatGPT Pro
  morning review are selected for planning; first-pass schedules, schemas,
  tool-boundaries, and disabled-network defaults are closed by UNIT-005.
  Nonzero live AI API cost/token caps remain a future approved pricing item.
- MyWebTemplate reuse: reuse suitable `frontend-web`/`backend` code skeleton and
  tooling patterns only. Do not copy MyWebTemplate `docs/` or template-product
  PST content into hwiStock.
- Home-server process manager: selected as `systemd` for the one-week
  paper/sandbox runner evidence path. Docker Compose is deferred; tmux/screen is
  allowed only for early manual experiments, not official evidence.
- Service health/alerting channel: selected as local-only first pass:
  systemd journal, `data/alerts/YYYY-MM-DD/alerts.jsonl`, dashboard audit/error
  panel when implemented, and daily close report. External alert delivery is
  deferred and requires later approval.
- Market calendar source and holiday/exceptional-session rules: selected by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`. Missing or stale
  cached calendar forces trading/order loops idle.
- Market-intelligence source registry:
  `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`
  - approved first Go: OPENDART / DART Open API
  - conditional after key approval: NAVER Search API news
  - conditional after terms/access check: KRX KIND, KRX Data Marketplace delayed
    context data
  - deferred: KIS/broker market/news/realtime APIs
  - forbidden by default: general media HTML scraping and unofficial finance APIs
- KIS broker API paper/live capability matrix:
  `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`
- Chart/realtime quote data source, candle intervals, and first-pass source
  behavior are packaged for user approval in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`; broker
  network calls remain disabled for ordinary Go rows unless a selected unit
  explicitly scopes KIS paper/mock behavior.
- Crawling/rate-limit policy: first Go uses API/RSS/official-source first and
  blocks general HTML crawling by default; long-term retention remains
  unresolved beyond the one-week evidence gate.

## 11. Ready / Set Questions

These must be answered before implementation-ready Go:

1. KIS paper adapter schema and no-order dry-run record schema: closed by
   `HWISTOCK-UNIT-006` Set for the first condition/order-state pass. Future
   implementation may refine field names without changing the safety boundary.
2. Official/broker calendar source: closed by
   `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`. Use KRX
   official trading-days/holidays and notices, NXT official session references,
   local cached calendar for runtime, and KIS `국내휴장일조회` only after approved
   broker-network integration.
3. Which sources are allowed for 24-hour market intelligence ingestion: closed
   for first Go by `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`; DART is approved,
   Naver Search API news is conditional after key/query/rate approval, KRX/KIND
   are conditional after terms/access check, KIS broker data is deferred, and
   general HTML scraping is blocked by default.
4. What collection policy is allowed for crawlers: closed for first Go as
   API/RSS/official-source first; no general HTML crawling unless a later
   source-specific Set approval records terms, rate limits, and storage policy.
5. Chart/realtime market-data source for the first strategy implementation:
   packaged for user approval in
   `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.
6. Candle intervals for the 10-20 minute strategy: packaged for user approval
   in `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.
7. AI job registry, first-pass `*/v0` schemas, structured actions, normalized
   bundle input policy, GPT Pro 07:20 cutoff, and fallback behavior: closed by
   `HWISTOCK-UNIT-005` Set.
8. AI token/cost caps for real network calls: defaults are
   `AI_NETWORK_ENABLED=false` and `AI_DAILY_COST_CAP_KRW=0`; nonzero caps require
   a future approved provider-pricing check.
9. AI tool use: closed for first pass as disabled; models receive only
   normalized source bundles prepared by hwiStock.
10. AI prompt file paths: implementation detail, but must use the job ids and
    schema names from `HWISTOCK-UNIT-005`.
11. Is the first implementation target a research/backtest engine, paper-trading
   engine, live-readonly monitor, or UI dashboard?
12. Preferred stack: closed as Python 3 + FastAPI backend/API/trading runner,
    TypeScript + Next.js/React read-only dashboard, and PostgreSQL storage.
13. Minimal risk policy: closed for the first docs pass. Maximum simultaneous
    holdings is 5. Position sizing has no fixed per-symbol cap, but every order
    must preserve `minimum_cash_reserve_ratio = 0.25` of total capital. Stop
    policy is AI-assisted per entry, but deterministic risk gates cap accepted
    stops at a maximum -5% loss envelope.
14. Should any account-level risk controls such as daily loss halt, max trades,
   or cooldown remain excluded for the first test, or should they be added later
   after paper evidence?
15. One-week paper/sandbox pass criteria: closed by
    `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE.md`. Minimum 7
    consecutive calendar days, at least 5 valid Korean market open days, P0
    safety/evidence/reconciliation criteria, and no profit threshold.
16. What data source is permitted for historical and realtime quotes? First-pass
    recommendation is packaged in
    `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`; any KIS
    data call still needs later broker-network approval.
17. Is there any prepared design source for a dashboard, or should UI work use a
    no-design fallback plus `agy` Gemini Pro design review? Closed: no prepared
    design source exists; use no-design fallback and require `agy` Gemini Pro
    design review before dashboard Go. Review packet:
    `docs/set/READY-SET-DASHBOARD-DESIGN-REVIEW-PACKET-20260602_hwistock.md`.
18. 24-hour runner process manager: closed as `systemd` for the one-week
   paper/sandbox evidence path. Docker Compose deferred; tmux/screen only for
   early manual experiments.
19. Alert channel: closed for first pass as local-only systemd journal,
    `data/alerts/YYYY-MM-DD/alerts.jsonl`, dashboard audit/error panel when
    implemented, and daily close report. External delivery is deferred.
20. For a later KIS integration unit, which personal-account eligibility,
    endpoint mode, credential flow, account type, rate limits, KRX paper
    symbol/venue fields, and order APIs must be verified from current official
    KIS docs before any network call?
21. Can the official KIS paper/mock-investment API be used for the one-week test,
    and how should its 10,000,000 KRW paper budget be mapped down to the intended
    2,000,000 KRW live starting-capital policy, given that NXT/SOR broker
    behavior cannot be paper-proven by the current KIS references?
