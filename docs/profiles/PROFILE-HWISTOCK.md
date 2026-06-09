---
schema_version: hwi.profile/v0
id: PROFILE-HWISTOCK
type: profile
name: hwiStock project profile
project_root: /data/workspace/My/hwiStock
docs_base: docs
status: active
owner: hwi
updated_at: 2026-06-06
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
  - account_affecting_order_placement
  - credential_storage
  - account_affecting_trading
  - strategy_risk_parameter_change
  - ai_api_provider_selection
  - ai_api_network_operation
  - ai_prompt_or_model_change
---

# hwiStock Project Profile

## 1. Purpose

This profile configures Hwi Work Harness for `hwiStock`, a stock day-trading
automation project. The profile is intentionally safety-first: no code path,
test, worker, or QA run may place real orders or access brokerage account records
until the required approvals, adapter evidence, and risk controls are documented.
Actual account-affecting operation also requires an operator-selected adapter-backed
observation window with named evidence and an explicit user go/no-go approval.
The runner itself must not hardcode seven days, one week, or any other fixed
test duration; observation windows are operator/runtime metadata.
The intended runtime is a 24-hour home-server program/service. Codex sessions are
not the runtime; they are used for development, review, and verification.
The first market scope is Korea domestic stocks (`국장`). The runtime has two
branches:

- `market_intelligence`: 24-hour ingestion of permitted public news, articles,
  disclosures, chart/market-data context, and related signals.
- `trading`: simple session-aware strategy/risk/order loop. KIS mode is explicit:
  paper/mock mode uses integrated market-data/account-truth helpers for analysis
  and KRX-only broker execution; NXT broker branches are rejected. Future live
  mode also starts `krx_only`; NXT requires separate owner approval and
  Ready-Set before routing can be enabled. SOR remains disabled until a future
  approved contract proves it.

This project is tooling and automation work, not investment advice. Strategy
documentation must distinguish hypotheses, backtest results, automated-trading
results, and account-affecting operation evidence.

Strategy direction is short-term day trading (`단타`) with a fast intraday
scalping/momentum hypothesis: approved-signal entries, typical 10-20 minute
holding window, per-trade candidate 1-5% price-move target band, and quick exit
on invalidated signals or predefined risk triggers. This target band is not a
daily account return target. The later real-investment `08:00-20:00 KST`
envelope is an observation/opportunity window, not permission to trade
continuously. The current paper/mock KRX investment/order-decision window is
`09:00-15:00 KST`; `15:00-15:30 KST` may be market-data/close/reconciliation
context only and must not unlock new paper/mock KRX entries or order submits.
Capital policy is cash-only. Credit, margin, 미수, borrowed funds, or other
leveraged capital are forbidden by default. Initial starting capital is
2,000,000 KRW cash.
AI API orchestration may be used for candidate synthesis, ranking, explanation,
and operation review, but AI outputs cannot directly place orders or override
deterministic risk controls.
Broker/API provider direction is selected as Korea Investment & Securities Open
API (`KIS`, 한국투자증권). KB Securities (`KB증권`) is treated as not usable for this
personal-account automation project unless a future official confirmation proves
otherwise. hwiStock will not use an internal fake broker adapter as the first
execution path. The first broker-backed execution path is an approved KIS
broker-adapter KRX path. Outside a valid `paper_experiment` session approval,
the engine may run only no-order dry-run validation that records candidate,
risk, and order-intent decisions without simulating broker fills. Inside a valid
`paper_experiment` session approval, KIS paper/mock KRX orders are allowed
without per-order human approval, subject to deterministic caps, account truth,
KRX session preflight, duplicate locks, submit-result recording, and
evidence-write checks.
UNIT-009 confirms, from official docs/samples, KIS domestic
order/account/realtime endpoint families, adapter-mode separation,
personal-account eligibility, and NXT/SOR order-routing fields. Local KIS
reference files constrain the official broker-adapter path to KRX for several
order/realtime flows, so KIS broker adapter evidence must not be treated as proof of
NXT/SOR broker behavior. NXT/SOR are engine-level venue/session parameters over
the same state machine, with KIS-specific NXT/SOR branches disabled or
explicit-fallback-only during KIS broker adapter runs until a later approved
broker-account/support-confirmation gate. Actual KIS adapter balance and exact
current rate limits still require a future explicitly approved broker-network
smoke.
Broker-adapter account balance is observed broker evidence only. Risk sizing uses
authoritative account-truth totals for the current paper experiment's dynamic
75% exposure calculation, but the effective exposure base must not exceed the
hwiStock risk-overlay capital of 2,000,000 KRW unless a future approved
profile/unit change records a higher cap.

Current operational correction: the continuous KIS broker adapter runner foundation
(`HWISTOCK-UNIT-010`) is not the complete trading program. Actual operation
readiness now requires the 2026-06-05 operational queue
(`HWISTOCK-UNIT-011` through `HWISTOCK-UNIT-015`) covering service supervision,
24-hour news/disclosure collection, KIS intraday market-data collection,
DeepSeek Pro/Flash runtime analysis, source-grounded trade-document to order
intent generation, KIS KRX broker order execution/reconciliation, and read-only
operator observation Prove.

Latest KIS paper/mock runtime correction: as of
`docs/evidence/RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix.md`,
the KIS paper/mock runner must use the token cache on the current adapter
transport shape, retry once after invalid token evidence, skip provider-unsupported
sellable/cancelable/realized-PnL/holiday helper TRs as
`skipped_provider_unsupported`, and preserve unsupported sellable truth as
unknown instead of converting it to zero. This hotfix is evidence for safer
runtime/account-truth handling, not by itself order-submit readiness.

Owner paper-experiment correction (2026-06-06): Monday-start readiness is
evaluated as `paper_experiment_ready`, not as final live-money or production
readiness. `live_money_trading_ready` is `not_applicable` for this experiment.
`production_quality_ready` is `partial_non_blocking`. The true paper blockers
are disabled paper network/order loop, paper token failure,
account/balance/buyable failure, KRX session/calendar failure, broken duplicate
lock, evidence-write failure, missing submit-result recording, and process
crash. In `paper_experiment` mode, a valid session approval plus caps enables
the KIS paper/mock order loop; no per-order human approval is required inside
that approved session.

Current owner-defined runtime architecture is file-driven. The canonical
investment-mode docs variable is `HWISTOCK_INVESTMENT_MODE=paper|live`; existing
KIS-specific env/config names may map into that canonical mode during migration,
but Ready-Set reasoning must separate investment mode from
`HWISTOCK_OPERATION_MODE` such as `paper_experiment`.
The installed user-systemd runtime reads this canonical switch from
`/home/hwi/.config/hwistock/runtime-mode.env` and normalizes it through
`ops/systemd/load_runtime_mode_env.sh`; service units must not reintroduce
per-service hardcoded `HWISTOCK_INVESTMENT_MODE=paper` exports. In paper/mock
mode the loader forcibly pins executable routing to `krx_only` and NXT disabled.

1. `news_disclosure_collector` runs 24 hours and collects only permitted/free
   public sources. Initial recommended sources are OpenDART disclosures, NAVER
   Search News API when keys are configured, and public RSS/news-search metadata
   as a no-key fallback. KRX KIND or other portal scraping remains deferred
   until terms/access are explicitly recorded.
2. `kis_intraday_market_collector` runs continuously during the approved
   intraday window and collects mode-aware KIS broker adapter-supported market
   data: integrated WebSocket realtime trade/orderbook/market-operation inputs
   are the default market-analysis authority, plus REST ranking/analysis
   snapshots every 1-3 minutes such as volume rank, fluctuation, volume power,
   and program-trading aggregate status where supported. KRX quote/session
   evidence remains execution authority. NXT inputs are disabled in paper/mock
   and future live mode until a separate owner approval and Ready-Set. Paper/mock
   market-data context may run through the KRX public
   regular-session close at `15:30 KST`, but paper/mock investment/order
   decisions stop at `15:00 KST`. SOR KIS broker-facing collection remains
   disabled or fallback-only until later support confirmation.
3. `deepseek_pro_hourly` runs on the top of every hour. It reads the accumulated
   news/disclosure and KIS market-data files. During market hours it includes
   market-regime/session analysis in the same hourly Pro artifact, not as a
   detached side design.
3a. `gpt_morning_watchlist` starts at `07:15 KST` when scoped. It is executed by
   **Codex CLI on the local desktop/workstation using local browser-use** against
   the user's logged-in local Chrome ChatGPT Pro session. SSH browser-use,
   reverse-socket Chrome bridges, remote Chrome, and hwiServer-side browser
   automation are forbidden for this path. The prompt reads the prior close
   through current-morning Pro/news/disclosure artifacts and writes a
   `morning_watchlist/v0` artifact or a named safe-block. For paper/mock mode,
   the first `09:00 KST` Flash bucket must reference that artifact or safe-block;
   for future live mode, the first `08:00 KST` Flash bucket has the same
   requirement.
4. `deepseek_flash_decision_10m` runs every 10 minutes during market hours. It
   reads the latest Pro artifact, the recent 10-minute news/disclosure window,
   KIS REST ranking changes, current KIS market snapshots, and realtime
   price/orderbook data. It must also read either the previous trade document
   chain or the current portfolio/order-state snapshot, and preferably both, so
   new actions do not conflict with current holdings, pending orders, exits,
   stops, cooldowns, or still-valid earlier trade decisions. It then writes at
   most one trade document for that 10-minute decision bucket. The document
   contains at most five symbol actions. Each action must include ticker/name,
   action type (`WAIT_BUY`, `BUY_NOW`, `HOLD`, `SELL`, or `NO_TRADE`), entry
   zone if relevant, take-profit, stop-loss, trailing-stop percent,
   cancel-if-not-filled window, size/cash cap, validity window, source refs, and
   risk notes. Paper/mock Flash decision buckets that can create new entry
   intents are limited to `09:00-15:00 KST`; `15:00-15:30 KST` may produce
   close/reconciliation/watch records only.
5. `trade_document_executor` watches newly written trade documents, validates
   them through deterministic strategy/risk gates plus current holdings,
   pending-order, and open-exit checks, and submits only approved KIS KRX
   broker-adapter cash orders. AI artifacts never call broker APIs directly and
   never hold credentials.
6. `daily_close_report` uses DeepSeek Pro for an operation summary after the
   relevant close. Paper/mock mode targets the post-KRX-close summary after
   `15:30 KST`; future live mode targets `20:00 KST`. Daily reports explain
   system-calculated results and must not calculate PnL in AI prose.

ChatGPT Pro remains optional external review through local Codex CLI
browser-use when available; it is not required for the runtime loop to stay
running. The approved hwiStock GPT Pro route is local Codex CLI -> local
browser-use -> user's logged-in local Chrome. SSH browser-use must not be used
for morning watchlist or runtime-review prompts. When GPT Pro review is used for
this project, the review packet must include the GitHub repository URL and the
exact folders and file paths to review, instead of only an unscoped architecture
summary or whole-project prompt.

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
  - `/home/hwi/.config/hwistock/hwistockApi.env`: optional KIS broker-adapter secrets
- Generated output folders: not created yet
- Runtime target: home server, 24-hour service/process managed by `systemd`
  or an approved service manager for continuous adapter-backed evidence.
  Observation window duration is chosen by the operator, not hardcoded by the
  runner.
- Market scope: Korea domestic stocks (`국장`) first
- Trading venues/session context: KRX + integrated + NXT
- KRX session truth: KRX public regular-session context is 09:00-15:30 KST
- Paper/mock KRX investment/order-decision truth: 09:00-15:00 KST; 15:00-15:30
  KST is close/market-data/reconciliation context only
- Current KIS investment-mode policy: paper/mock mode uses KIS integrated
  realtime feeds as the default market-analysis authority and KRX-only
  quote/session/order checks as the executable-order authority. Future live mode
  also defaults to `execution_venue_mode = krx_only`; NXT venue routing remains
  disabled until a separate owner approval and Ready-Set explicitly enable it.
- SOR broker route policy: disabled/fallback before KIS transport unless future
  approved proof changes this
- Broker/API direction: Korea Investment & Securities Open API (`KIS`)
- Blocked broker candidate: KB Securities personal use is blocked unless later
  official confirmation proves otherwise
- First broker-backed execution adapter: KIS KRX broker-adapter-investment path;
  the first bounded broker-adapter smoke is complete, but adapter integration and
  future broker calls still require explicit unit scope
- Internal fake broker adapter: not used by project direction; no legacy fake
  broker execution path
- Pre-approval execution behavior: no-order dry-run only, recording candidate,
  risk, and order-intent decisions without broker fill simulation
- Paper experiment execution behavior: with `HWISTOCK_OPERATION_MODE =
  paper_experiment`, `HWISTOCK_KIS_PAPER_ORDER_ENABLED = true`, and a valid
  approval file for the KST date/caps/source/calendar, the KIS paper/mock KRX
  order loop may submit approved paper orders without per-order human approval.
  The runner must still fail closed on token/account/balance/buyable,
  KRX-session, duplicate-lock, evidence-write, submit-result, or crash blockers.
- Daily paper approval rollover: systemd-launched paper runner ticks execute
  `ops/systemd/ensure_paper_order_approval.py` before the runner. The helper
  reuses only an existing paper-experiment approval with the same operator run
  id and writes a date-stamped `valid_for_date_kst` file, so stale prior-day
  approval paths do not block the next trading day while live-money scope stays
  forbidden.
- Broker-provided adapter API mode: KIS KRX-adapter path only
  under explicit unit/smoke or `paper_experiment` session approval; NXT/SOR stay
  disabled or explicit-fallback-only until later broker-account/support-confirmation
- Broker-adapter account balance: observed broker evidence only; it does not expand
  the 2,000,000 KRW risk-overlay sizing capital
- KIS API mode: the first bounded broker-adapter REST and websocket smoke passed in
  `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`; ordinary Go rows
  still must not call KIS/broker APIs unless the selected unit explicitly scopes
  that behavior
- KIS broker adapter validation boundary: current local KIS references prove only the KRX
  adapter route for the relevant order/realtime flows. NXT/SOR are not adapter-proven
  and must stay disabled or explicit-fallback-only in KIS broker adapter runs.
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
  per-trade 1-5% price-move target band, evidence required before account-affecting use
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
- Continuous KIS broker adapter runtime source:
  `docs/modules/HWISTOCK-MOD-008_continuous-adapter-runtime.md`
- Operational automated-trading program source:
  `docs/modules/HWISTOCK-MOD-009_operational-automated-trading-program.md`
- Current operational Ready-Set queue:
  `docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md`
- Current operational Go-Check row closure:
  `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-automated-trading-program_hwistock.md`
- Current operational Go preflight:
  `docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-automated-trading-program_hwistock.md`
- Current KIS paper/mock runtime hotfix evidence:
  `docs/evidence/RUN-20260606_kis-paper-token-cache-and-mock-unsupported-tr-hotfix.md`
- Current KIS paper/mock experiment readiness split evidence:
  `docs/evidence/RUN-20260606_paper-experiment-readiness-split-go-check.md`
- Current investment-mode schedule / AI-loop follow-up Ready-Set correction:
  `docs/set/READY-SET-CORRECTION-20260606_mode-schedule-ai-loop-followup.md`
- Current GPT Pro morning prompt contract:
  `docs/set/READY-SET-GPT-PRO-MORNING-PROMPT-20260606_hwistock.md`
- Current operational implementation / contract units:
  - `docs/units/HWISTOCK-UNIT-011_operational-runtime-supervisor.md`
  - `docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md`
  - `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md`
  - `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
  - `docs/units/HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md`
  - `docs/units/HWISTOCK-UNIT-015_operator-console-observation-prove.md`
- Storage backend: PostgreSQL with hwiStock isolation
  - database: `hwistock`
  - schema: `hwistock_core`
  - env var: `HWISTOCK_DATABASE_URL`
  - do not share MyWebTemplate database/schema/migrations/tables
- KIS API verification source:
  `docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md`
- KIS API capability matrix:
  `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`
- Market calendar, alert, and operation observation policy:
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`
- 24-hour branch: market intelligence ingestion, not order execution
- Market calendar: selected source hierarchy is KRX official trading-days/
  holidays and notices, NXT official session notices, approved local cached
  calendar, and later KIS `국내휴장일조회` as broker-side cross-check only after
  explicit broker-network approval.
- Selected technology stack: Python 3 + FastAPI for the backend API, trading
  runner, schedulers, adapters, AI orchestration, and storage services;
  TypeScript + Next.js/React for the read-only dashboard/operator console; and
  PostgreSQL for durable application storage.
- Post-Pro readiness correction: the imported `frontend-web/` implementation is
  currently JS-only (`.js`/`.jsx`) even though the selected target stack says
  TypeScript. Do not cite the current dashboard as TypeScript-compliant until a
  future corrective reinforcement either migrates the implementation or
  explicitly changes this profile policy.
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

The 2026-06-05 operational automated-trading Ready-Set is now
`implementation_ready: true` only for the contract-hardened Go-Check queue after
`HWISTOCK-UNIT-016` closed runtime data/execution contracts. This does not mean
operation-ready or operationally complete. UNIT-012 through UNIT-015 have local
no-network Go-Check evidence, but provider network, KIS adapter-read/order
transport, browser/tunnel Prove, and operator observation-window side-effect
evidence remain blocked until explicitly scoped.

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
  placement, unapproved adapter operation, or risk-control changes.
- `prove`: `hwi-work-harness`

Project-specific GPT Pro review packet policy:

- Execute hwiStock GPT Pro review/morning prompts from Codex CLI with local
  browser-use only. Do not use SSH browser-use for this project path.
- Include the current GitHub repository URL, not only local paths.
- Include the exact folders and file paths that GPT Pro should review.
- Keep secret-bearing local config, ignored env files, broker credentials,
  raw account identifiers, and local-only runtime data out of the review packet.
- If the intended review scope changes, regenerate the path list before sending
  the prompt.

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

- no account-affecting order placement by default
- no credential leakage
- clear adapter mode separation
- broker adapter separation: no internal fake broker execution path; KIS/external
  broker network adapters disabled until approved; broker-provided broker-adapter
  APIs allowed only after UNIT-009 docs verification plus explicit
  broker-network smoke approval
- KIS broker adapter capability must expose explicit authority separation:
  integrated realtime feeds are analysis authority, KRX is paper/mock execution
  authority, NXT is disabled in paper/mock and future-only, and SOR remains
  disabled unless separately proved and approved.
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
- operator-selected adapter-backed observation evidence before account-affecting operation;
  the program must not hardcode the observation duration
- overtrading controls for the later real-investment 08:00-20:00 envelope are
  not part of the first minimal risk policy unless a future Set decision adds
  them; the current paper/mock KRX investment/order-decision window remains
  09:00-15:00 KST, and signal-quality/stale-data gates still apply
- audit logging for signals, decisions, orders, and failures
- reproducible evidence for backtest and automated-trading claims
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
- Runtime language policy status: target policy, not current implementation
  truth. The current imported dashboard code is JS-only (`.js`/`.jsx`). The
  operational Ready-Set's post-Pro reinforcement must resolve this by migration
  or an explicit profile update before claiming frontend stack compliance.
- Runtime extensions target: `.ts`, `.tsx`, plus framework/config files as
  required by the selected Next toolchain. Current implementation exceptions
  must remain visible in Ready-Set/Check evidence.
- Scope: read-only dashboard/operator console, status views, reports, logs,
  health, candidate visibility, and AI conversation surface.
- Forbidden scope: direct buy/sell controls, order placement buttons, broker
  credential entry, raw account-number display, or account-affecting operation approval UI.
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
  kill switch behavior, and adapter-mode separation.
- `credential-safety-check`: verify credentials are referenced through env/secret
  stores and not committed.
- `storage-contract-check`: verify PostgreSQL database/schema isolation,
  `HWISTOCK_DATABASE_URL`, hwiStock migrations, artifact paths, hashes, and
  system-calculated PnL contracts.
- `automated-trading-smoke`: initial approved KIS KRX broker-adapter REST and websocket
  smoke passed in `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`;
  future expanded smoke gates cover longer order/fill, position, reject, and
  adapter-budget behavior.
- `no-order-dry-run-smoke`: future smoke gate proving candidate, risk, and
  order-intent decisions are recorded without unscoped broker calls or simulated
  fills during ordinary Go implementation rows.
- `service-lifecycle-smoke`: future smoke gate for start, stop, restart, health,
  and log output of the home-server runner.
- `market-calendar-smoke`: future smoke gate for KRX/integrated/NXT session
  context, investment-mode venue gating, out-of-envelope idle behavior,
  closed/stale-calendar idle behavior, and local cached-calendar coverage.
- `intel-ingestion-smoke`: future smoke gate for source allowlist, robots/terms
  compliance notes, deduplication, rate limiting, and disclosure/news evidence.
- `ai-orchestration-smoke`: future smoke gate for structured AI output,
  source-id grounding, prompt/model audit logs, and no direct order interface.
- `ai-policy-gate-smoke`: future smoke gate proving AI recommendations cannot
  bypass deterministic position-risk, capital, stale-data, or kill-switch rules.
- `kis-api-contract-check`: future docs/code gate for KIS endpoint mode,
  credentials, call limits, KRX/NXT support, personal-account eligibility, and
  no accidental adapter-order path.
- `official-adapter-api-smoke`: initial approved KIS KRX broker-adapter API smoke
  passed for token, quote, balance, buyable, one minimal broker buy, cancel,
  daily order/fill lookup, websocket fill-notice ACK, and token revoke. Future
  expanded adapter API smoke still needs longer position/reject/adapter-budget
  evidence. This gate does not prove NXT/SOR broker behavior under the current
  KIS broker adapter constraints.
- `continuous-adapter-runner-go-check`: foundation Go gate for
  `HWISTOCK-UNIT-010`. It proves the KIS broker adapter runner boundary and local
  no-network implementation, but it is not the complete operational
  stock-trading program.
- `operational-trading-program-go-check`: current Go queue for
  `HWISTOCK-UNIT-011` through `HWISTOCK-UNIT-015`. It must prove service
  supervision, current DeepSeek Pro/Flash analysis runtime,
  source-grounded signal-to-intent generation, KIS KRX broker order
  execution/reconciliation, read-only operator observation, and no fake/unapproved-adapter
  behavior.
- `operation-observation-window-prove`: future Prove gate for an operator-selected
  observation window. The window length is chosen by the project owner/operator
  and recorded in evidence; the runner must not auto-pass, auto-fail, or
  auto-stop because a fixed duration was reached.
- `dashboard-readonly-access-smoke`: future smoke gate proving the dashboard
  exposes no direct order controls, masks sensitive values, binds local-only by
  default, and rejects public/LAN exposure unless a later Set contract approves
  authenticated access.
- `post-pro-readiness-truth-smoke`: corrective smoke gate proving the dashboard,
  operator API, docs, and evidence all show false readiness loudly when
  `brokerNetworkEnabled`, `brokerOrdersSubmitted`, `operationObservationAccepted`, or
  `operationalReadiness` are false. This gate must prevent service/timer
  activity from being misreported as operation readiness.
- `runtime-entrypoint-no-reload-smoke`: corrective smoke gate proving
  service-managed backend runtime uses a non-reload entrypoint or documents the
  dev-only entrypoint split before systemd evidence can count toward
  operational readiness.

## 7. Approval Policy

Explicit approval is required before:

- changing the selected broker API provider
- enabling, integrating, or running any KIS or external broker API adapter
- storing or loading credentials
- any broker network call
- any KIS or external broker network call unless a Set-approved broker-adapter unit explicitly scopes it
- any broker account login
- any order placement, even adapter-backed, unless the unit explicitly scopes it;
  for KIS paper/mock experiments this approval may be session-level and
  date/cap-scoped rather than per-order
- treating the system as operation-ready before an operator-selected adapter-backed
  observation window has been completed, reviewed, and explicitly accepted
- account-affecting trading outside the current KIS paper/mock experiment scope
- production deployment or remote operation
- selecting an AI API provider/model or sending project data to an AI API
- changing AI prompt, output schema, model, tool permissions, or fallback policy
- changing capital allocation, stop-loss, max simultaneous holdings, or kill
  switch policy
- enabling credit, margin, 미수, borrowed funds, or any leveraged-capital mode
- enabling all-in or single-stock full-capital deployment

## 8. Evidence Policy

Evidence summaries are stored under `docs/evidence/`.

For trading-related work, evidence must label the environment:

- `docs_only`
- `backtest`
- `adapter`
- `broker_readonly`
- `broker_order`

`broker_order` evidence requires explicit approval in a Set contract.
For the current KIS paper/mock experiment, the explicit approval unit is the
date/cap-scoped `paper_experiment` session approval file consumed by the runner.
It must include `mode` or `operation_mode = paper_experiment`,
`allow_paper_orders = true`, `valid_for_date_kst`, optional `valid_until_kst`,
`max_daily_orders`, `max_notional_krw`, and
`live_money_scope = not_applicable`. This approval enables the paper order loop
only for the approved session and caps; it does not approve live-money
operation.
The earliest operation approval must link operator-selected adapter-backed
observation evidence, including dates, test environment, scenario coverage,
broker order/reconciliation results where approved, failures, fixes, observation
window metadata, and final go/no-go verdict.

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
- First broker-backed execution adapter: KIS KRX broker-adapter-investment path after
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
  `minimum_cash_reserve_ratio = 0.25` of effective total-deposit exposure, using
  authoritative account truth and still capped by the 2,000,000 KRW risk-overlay
  capital unless a later approved profile/unit change raises it; AI may
  recommend a per-entry stop price, but deterministic risk gates cap accepted
  stops at a maximum -5% loss envelope.
- Operation observation acceptance criteria: selected by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`. The runner is a
  continuous 24-hour service; observation-window start, end, and duration are
  chosen by the operator and recorded as evidence metadata. P0
  safety/evidence/reconciliation criteria and no-profit-threshold policy remain
  required.
- Broker adapter provider: KIS broker-adapter API use is limited to the KRX-supported
  path unless later official evidence changes this. NXT/SOR remain
  venue/session parameters in the engine, but KIS-facing NXT/SOR branches stay
  disabled or explicit-fallback-only and require later
  broker-account/support-confirmation evidence before account-affecting routing.
  Internal fake broker simulation is not used. Broker adapter balance is
  observed account-truth evidence for the dynamic 75% exposure gate, but it must
  not expand hwiStock's 2,000,000 KRW risk-overlay capital without a later
  approved profile/unit cap change.
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
  Nonzero paid AI API cost/token caps remain a future approved pricing item.
- MyWebTemplate reuse: reuse suitable `frontend-web`/`backend` code skeleton and
  tooling patterns only. Do not copy MyWebTemplate `docs/` or template-product
  PST content into hwiStock.
- Home-server process manager: selected as `systemd` or an approved service
  manager for the continuous adapter-backed runner evidence path. Docker Compose
  is deferred; tmux/screen is allowed only for early manual experiments, not
  official evidence.
- Service health/alerting channel: selected as local-only first pass:
  systemd journal, `data/alerts/YYYY-MM-DD/alerts.jsonl`, dashboard audit/error
  panel when implemented, and daily close report. External alert delivery is
  deferred and requires later approval.
- Market calendar source and holiday/exceptional-session rules: selected by
  `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`. Missing or stale
  cached calendar forces trading/order loops idle.
- Market-intelligence source registry:
  `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`
  - approved first Go: OPENDART / DART Open API and no-key public RSS news
    metadata search
  - conditional after key approval: NAVER Search API news
  - conditional after terms/access check: KRX KIND, KRX Data Marketplace delayed
    context data
  - deferred: KIS/broker market/news/realtime APIs
  - forbidden by default: general media HTML scraping and unofficial finance APIs
- KIS broker API adapter-mode capability matrix:
  `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`
- Chart/realtime quote data source, candle intervals, and first-pass source
  behavior are packaged for user approval in
  `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`; broker
  network calls remain disabled for ordinary Go rows unless a selected unit
  explicitly scopes KIS broker-adapter behavior.
- Crawling/rate-limit policy: first Go uses API/RSS/official-source first and
  blocks general HTML crawling by default; long-term retention remains
  unresolved beyond the operator-selected operation observation evidence gate.

## 11. Ready / Set Questions

These must be answered before implementation-ready Go:

1. KIS broker adapter schema and no-order dry-run record schema: closed by
   `HWISTOCK-UNIT-006` Set for the first condition/order-state pass. Future
   implementation may refine field names without changing the safety boundary.
2. Official/broker calendar source: closed by
   `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`. Use KRX
   official trading-days/holidays and notices, NXT official session references,
   local cached calendar for runtime, and KIS `국내휴장일조회` only after approved
   broker-network integration.
3. Which sources are allowed for 24-hour market intelligence ingestion: closed
   for first Go by `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`; DART and no-key
   public RSS news metadata search are approved, Naver Search API news is
   conditional after key/query/rate approval, KRX/KIND are conditional after
   terms/access check, KIS broker data is deferred, and general HTML scraping is
   blocked by default.
4. What collection policy is allowed for crawlers: closed for first Go as
   API/RSS/official-source first; no general HTML crawling unless a later
   source-specific Set approval records terms, rate limits, and storage policy.
5. Chart/realtime market-data source for the first strategy implementation:
   packaged for user approval in
   `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.
6. Candle intervals for the 10-20 minute strategy: packaged for user approval
   in `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md`.
7. AI job registry, first-pass `*/v0` schemas, structured actions, normalized
   bundle input policy, and fallback behavior: initially closed by
   `HWISTOCK-UNIT-005` Set; the current operational Ready-Set follow-up changes
   the morning review contract to a `07:15 KST` start with hard cutoff before
   the first Flash bucket for the active investment mode.
8. AI token/cost caps for provider network calls: defaults are
   `AI_NETWORK_ENABLED=false` and `AI_DAILY_COST_CAP_KRW=0`; nonzero caps require
   a future approved provider-pricing check.
9. AI tool use: closed for first pass as disabled; models receive only
   normalized source bundles prepared by hwiStock.
10. AI prompt file paths: implementation detail, but must use the job ids and
    schema names from `HWISTOCK-UNIT-005`.
11. Is the first implementation target a research/backtest engine, automated-trading
   engine, read-only broker-adapter monitor, or UI dashboard?
12. Preferred stack: closed as Python 3 + FastAPI backend/API/trading runner,
    TypeScript + Next.js/React read-only dashboard, and PostgreSQL storage.
13. Minimal risk policy: closed for the first docs pass and corrected by the
    current operational Ready-Set follow-up. Maximum simultaneous holdings is 5.
    Position sizing has no fixed per-symbol cap, but every order must preserve
    `minimum_cash_reserve_ratio = 0.25` of authoritative effective
    total-deposit exposure, capped by the 2,000,000 KRW risk-overlay capital
    unless a later approved profile/unit change raises it. Stop policy is
    AI-assisted per entry, but deterministic risk gates cap accepted stops at a
    maximum -5% loss envelope.
14. Should any account-level risk controls such as daily loss halt, max trades,
   or cooldown remain excluded for the first test, or should they be added later
   after adapter evidence?
15. Operation observation criteria: closed by
    `docs/sources/HWISTOCK-MARKET-CALENDAR-ALERT-OPERATION-GATE.md`. The runner is
    continuous; the operator chooses the observation period. Evidence must
    record start/end/duration metadata, covered market days, P0
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
18. 24-hour runner process manager: closed as `systemd` or approved service
   manager for continuous adapter-backed evidence. Docker Compose deferred;
   tmux/screen only for early manual experiments.
19. Alert channel: closed for first pass as local-only systemd journal,
    `data/alerts/YYYY-MM-DD/alerts.jsonl`, dashboard audit/error panel when
    implemented, and daily close report. External delivery is deferred.
20. KIS broker adapter integration scope: `HWISTOCK-UNIT-010` is the foundation runner
    boundary; actual operational KIS broker order execution and reconciliation
    belongs to `HWISTOCK-UNIT-014`. Bounded KIS KRX broker-adapter network calls and
    broker orders may be implemented only inside the selected unit after
    preflight; unapproved, NXT/SOR broker routing, secret printing, and fake broker
    state remain outside the current scope.
21. KIS broker-adapter API use for continuous testing: current operational use is
    governed by the 2026-06-05 operational Ready-Set queue. The official
    broker-adapter investment API can be used for operator-selected observation
    windows in the KRX-supported adapter path. Broker-visible adapter balance is
    observed context for account-truth and dynamic exposure checks; hwiStock
    risk sizing must not exceed the 2,000,000 KRW risk-overlay capital unless a
    future explicit profile/unit change says otherwise.
