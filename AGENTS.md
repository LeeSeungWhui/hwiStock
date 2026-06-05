# AGENTS (hwiStock HWI Work Harness)

This file is a thin execution adapter for `hwiStock`. Global Codex rules,
memento behavior, delegation-guard policy, browser-use defaults, and generic
Hwi Work Harness lifecycle rules are inherited from the global instruction chain
and the `hwi-work-harness` skill. Project-specific paths, commands, rule
presets, approvals, and evidence policy live in `docs/profiles/PROFILE-HWISTOCK.md`,
which is this project's profile source of truth.

## Basic Paths

- Project root: `.`
- HWI project profile: `docs/profiles/PROFILE-HWISTOCK.md`
- Docs root: `docs/`
- Frontend code: `frontend-web/` present; currently MyWebTemplate-derived
  Next.js app skeleton and pending hwiStock Ready-Set rebaseline
- Backend/trading engine code: `backend/` present; currently MyWebTemplate-
  derived FastAPI/backend skeleton and pending hwiStock Ready-Set rebaseline
- Shared packages/libraries: none yet
- Design artifacts: none yet
- Automation scripts: `ops/systemd/` planned, not created yet
- Environment setup: `source ./env.sh`
- Primary local/dev URL: dashboard `http://127.0.0.1:5000`, backend/API
  `http://127.0.0.1:5001`; access from hwibuntu uses SSH local forwarding, not
  LAN/public bind
- Remote/dev server access: SSH tunnel or Chrome Remote Desktop only by default
- Version control: Git initialized on `main` as of
  `docs/evidence/RUN-20260604_git-init-ready-set-delta-sync.md`; do not assume
  remote origin, commits, tags, or deployment branches until recorded later.

## Verification / QA Accounts

- Broker/API accounts: KIS paper/mock credentials are configured only in the
  local secret store; live accounts are not approved for runtime use.
- Paper/sandbox accounts: KIS paper/mock account config exists in
  `/home/hwi/.config/hwistock/hwistockApi.env`; values must never be pasted,
  committed, or written into reports.
- Sensitive values must be referenced by fixture/env name rather than copied
  into reports.
- Project secrets/config values must live outside the repo under
  `/home/hwi/.config/hwistock/*.env`; do not paste or commit API keys.
- MyWebTemplate `config.ini` files under `backend/` and `frontend-web/` are
  local ignored template config only. Do not read, print, or commit their
  contents; migrate durable hwiStock secrets/config to
  `/home/hwi/.config/hwistock/*.env`.

## Harness Routing

- Default to `hwi-work-harness` for non-trivial planning, implementation, review,
  QA, documentation, evidence, rule-gate, migration, or artifact intake work.
- Use the global harness lifecycle unless `docs/profiles/PROFILE-HWISTOCK.md`
  defines a project-specific override.
- Tiny answers, one-line command output, and very small copy/constant edits may
  skip the harness.

## Project Overrides

- Source-of-truth order: user instruction > this AGENTS.md >
  `docs/profiles/PROFILE-HWISTOCK.md` > module/unit/QA docs > code/runtime
  evidence > prior memento/evidence.
- Ready-Set status note: the earlier 2026-06-02/2026-06-04
  `implementation_ready: true` queue is superseded by
  `docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md`
  until Ready-Set is reissued against the imported MyWebTemplate code baseline.
- Approval additions beyond global defaults: live brokerage login, order
  placement, real-money trading, production deployment, credential storage,
  strategy-risk parameter changes, and any network operation against a broker
  API require explicit user approval.
- Live operation requires at least one full week of paper/sandbox testing with
  named evidence and an explicit user go/no-go approval.
- Forbidden by default: live orders before the one-week test gate, credential
  commits, real account balances in logs, scraping that violates a provider's
  terms, and claims of expected profit.
- Capital policy: cash-only. Credit, margin, 미수, borrowed funds, or other
  leveraged capital are forbidden unless a future explicit profile/unit change
  reverses this policy.
- Starting capital: 2,000,000 KRW cash. All-in single-stock deployment is
  forbidden by default; strategy/risk parameter changes require explicit
  approval and must be reflected in the profile/module/unit docs.
- Baseline allocation policy: no fixed per-symbol maximum allocation; maximum
  simultaneous holdings is 5; every buy must preserve
  `minimum_cash_reserve_ratio = 0.25` of total capital unless a future explicit
  profile/unit change reverses this policy.
- Project-specific worker route: global delegation rules apply until the profile
  defines a narrower implementation worker route.

## Memento

- Follow the global memento instructions.
- For this project, use workspace `/data/workspace/My/hwiStock` and include
  `hwiStock` plus the feature/domain in topic and keywords.
- Store only project-specific confirmed settings, repeated QA procedures,
  deployment procedures, decisions, or resolved errors.

## Document Sources

- HWI profile: `docs/profiles/PROFILE-HWISTOCK.md`
- Docs index: `docs/index.md`
- Existing module/unit docs: `docs/modules/*.md`, `docs/units/*.md`
- New or normalized HWI outputs:
  - module: durable product/capability contract
  - unit: execution contract
  - QA scenario: full-run QA contract written at the end of Set
  - evidence: run/prove evidence summary
  - design artifact: docs-side index for Figma/PPT/PDF/screenshot/wireframe or
    existing-screen sources

## Rule Preset / Rule Gate

- Active common rule presets come from `docs/profiles/PROFILE-HWISTOCK.md`.
- Enabled presets: `fastapi-backend-rule-preset`,
  `next-frontend-rule-preset`, `db-naming-rule-preset`
- Project-specific overrides/exceptions: none
- Rule-gate command or adapter: `hwi-rule-gate` after code exists; manual
  checklist for docs-only Ready/Set
- Warning policy override: warnings block completion unless explicitly accepted
  in the unit/profile.

## Stage Routing

- `ready`: `hwi-work-harness`
- `set`: `hwi-work-harness`; use `chatgpt-collaboration-harness` for non-trivial
  strategy, risk, QA scenario, or architecture refinement when requested/available
- `go`: `hwi-work-harness` + `delegation-guard`
- `check`: `hwi-work-harness`; add external review for trading-risk or credential
  handling changes
- `prove`: `hwi-work-harness`
- Browser QA route override: none yet
- External collaboration/review route override: when requesting GPT Pro review
  for this project, provide the GitHub repository URL plus the exact folders
  and file paths that should be reviewed. Do not rely on an unscoped full-repo
  prompt.

## Design / Browser Evidence

- Prepared design sources: none
- Docs-side design index path: none until a UI/design source exists
- No-design fallback policy: implementation may proceed from product conventions
  and user-described intent for non-visual engine/docs work; UI work must record
  its no-design fallback in the unit and QA scenario.
- Evidence output roots: `docs/evidence/`

## Completion Criteria

- Report the active profile, unit/module/QA docs used, changed files, and
  project-specific verification/evidence locations.
- Use global completion/reporting rules for PASS/FAIL/BLOCKED, tests, smoke,
  QA, memento, and user-facing summaries.
