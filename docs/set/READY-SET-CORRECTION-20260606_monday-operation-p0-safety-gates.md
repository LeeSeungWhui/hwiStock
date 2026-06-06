# READY-SET CORRECTION — Monday Operation P0 Safety Gates

- Date: 2026-06-06
- Status: set-corrected
- Scope: Monday 2026-06-08 operation-readiness hardening for the existing
  operational automated-trading program.
- Supersedes: none. This reinforces the current 2026-06-05 operational
  Ready-Set instead of creating a parallel design.

## Problem

The current runtime was service-visible, but several P0 checks were still too
weak for unattended operation:

1. A future `validUntil` calendar cache could make a Saturday or missing KST day
   look usable.
2. Order preflight could still trust AI/intent cash and holdings fields instead
   of the latest KIS read evidence.
3. The operator console checked repository service files, but not the effective
   live user-systemd unit/timer policy.
4. Realtime exit intents were not guaranteed to be selected ahead of new entry
   intents from the same queue.
5. Dashboard readiness did not surface stale/missing runtime artifacts clearly
   enough.

## Correction Contract

### Calendar

- A tradeable state requires a date-specific KST row in the local KRX/NXT
  calendar cache.
- `validUntil` only proves cache freshness. It does not prove the requested KST
  date is a trading day.
- Missing day row => `calendar_day_missing`.
- Non-trading day row => `calendar_non_trading_day`.
- Any non-ready calendar state blocks route and order gate.
- KRX order execution additionally requires `krxOrderSessionOpen=true`.
- The default local cache now includes the Monday 2026-06-08 row and is short
  valid-through only to 2026-06-10. Future dates must be extended from official
  source review before use.

### Account Truth

- Executable order preflight must use the latest adapter read steps as account
  truth.
- Intent-provided cash/holdings are never sufficient for order preflight.
- Buy preflight requires:
  - balance read status `pass`,
  - buyable-cash read status `pass`,
  - account truth present,
  - reserve floor preserved.
- Sell/exit preflight keeps the account-truth requirement but does not require a
  positive planned buy cash amount.

### Intent Queue Priority

- Exit/realtime sell intents are selected before new entry intents.
- Within the same priority rank, FIFO order remains preserved.

### Operator Console

- Readiness must distinguish:
  - repository service-file policy,
  - live/effective user-systemd policy,
  - runtime artifact freshness.
- If live/effective order policy is enabled under `paper_experiment` session
  approval, the dashboard must not treat that as a live/final-readiness
  contradiction. `systemd_order_enabled_contradicts_readiness` is retained only
  for unscoped order enablement outside the paper experiment contract.
- Required artifacts have TTLs and can become evidence gaps even when files
  exist. Only paper-experiment hard blockers may block the Monday KIS paper/mock
  run.

### Frontend

- The dashboard must show a runtime freshness strip with:
  - snapshot time,
  - stale/missing artifact counts,
  - effective order policy,
  - live unit/timer state.

## Verification Reference

- Go-Check evidence:
  `docs/evidence/RUN-20260606_monday-operation-p0-safety-gates-go-check.md`
- Local calendar cache:
  `config/market-calendar/krx-nxt-trading-days.json`
