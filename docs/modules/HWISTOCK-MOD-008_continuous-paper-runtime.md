---
schema_version: hwi.module/v0
id: HWISTOCK-MOD-008
type: module
domain: backend_ops
name: Continuous KIS paper runtime
spec_status: set
build_status: go_check_passed_local_no_network
verification_status: go_check_passed_local_no_network
ready_set_rebaseline_status: go_check_passed_local_no_network
priority: P0
source_of_truth: user_intent
owner: hwi
updated_at: 2026-06-05
required_rules:
  - docs/profiles/PROFILE-HWISTOCK.md
links:
  - PROFILE-HWISTOCK
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-007
evidence_refs:
  - docs/evidence/RUN-20260605_ready-set-continuous-paper-runner.md
  - docs/evidence/RUN-20260605_unit-010-go-check.md
---

# Continuous KIS Paper Runtime

## 1. Purpose

This module owns the KIS paper runner foundation after the skeleton queue: a
24-hour continuous home-server runner that can use the approved KIS KRX
paper/mock-investment path under strict safety controls.

Current correction: this module is not the whole stock-trading program. The
actual operational paper-trading program integration is governed by
`HWISTOCK-MOD-009` and the 2026-06-05 UNIT-011 through UNIT-015 Ready-Set queue.

This is not a "7-day program." The service is continuous. The project owner
chooses the paper/sandbox observation window outside the program and may run it
for any desired duration. Code must not hardcode a seven-day lifetime, seven-day
pass condition, or automatic live-readiness verdict.

## 2. Product / Capability Contract

- The runtime is an independently restartable service, not a Codex session.
- The service may run 24 hours a day.
- The market-intelligence branch may run 24 hours for approved/conditional
  public sources.
- The trading/order branch is market-calendar and session aware. It stays idle
  outside approved Korea-market envelopes or when data/calendar/risk/kill-switch
  gates block.
- KIS use is limited to the paper/mock-investment KRX-supported path recorded in
  `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`.
- KIS paper NXT/SOR/integrated realtime/helper branches remain disabled or
  explicit-fallback-only until later support-confirmation evidence changes the
  profile.
- The runner must load KIS paper credentials only from the external local secret
  store and must never print, persist, or commit secrets.
- The paper account's broker-visible budget may be larger than the intended
  live cash baseline. Risk sizing must use the hwiStock policy overlay, not
  blindly consume the broker paper balance.
- The default live capital policy remains 2,000,000 KRW cash, cash-only, no
  leverage, no all-in deployment, maximum simultaneous holdings 5, and
  minimum cash reserve ratio 0.25.
- AI output cannot directly call broker adapters or place orders.
- The dashboard remains read-only and cannot expose buy/sell controls.
- Live order placement, real-money trading, live credentials, and public/LAN
  exposure remain denied.

## 3. Interfaces

Planned implementation surfaces:

- KIS paper adapter for KRX-supported paper/mock REST and WebSocket calls.
- KIS paper token/session manager with secret redaction and fail-closed domain
  checks.
- Continuous runner loop that coordinates calendar, source freshness, strategy,
  risk, order state, KIS paper adapter, reconciliation, alerts, and evidence.
- Operator observation-window manifest writer.
- Paper ledger and reconciliation service.
- Read-only runner status extension for dashboard/API.
- systemd user or service units for continuous runtime and health checks.

Candidate file paths for the Go implementation:

- `backend/service/kis_paper_adapter.py`
- `backend/service/kis_paper_continuous_runner.py`
- `backend/lib/paper_trading_ledger.py`
- `backend/service/HwiStockRunnerService.py`
- `backend/router/HwiStockRunnerRouter.py`
- `backend/tests/test_kis_paper_adapter.py`
- `backend/tests/test_kis_paper_continuous_runner.py`
- `ops/systemd/user/hwistock-kis-paper-runner.service`
- `ops/systemd/user/hwistock-kis-paper-runner.timer`

The exact file split may change during Go if the implementation preserves the
contract and reports the final paths in evidence.

## 4. State / Data Contract

The runtime must persist or emit redaction-safe records for:

- service health
- calendar state
- source freshness
- candidate id and source ids
- deterministic risk gate result
- order intent
- KIS paper request class without secrets
- KIS paper order id only if safe to store after masking policy review
- submitted/accepted/rejected/cancelled/fill events
- daily order/fill lookup reconciliation
- balance/buyable snapshots with account identifiers masked
- system-calculated cash, position, exposure, and PnL fields
- disabled/fallback branch records for paper-unsupported KIS capabilities
- operator observation-window start/end metadata
- critical alerts and operator acknowledgements

No fake broker fills, fake broker balances, fake broker PnL, or synthetic
"success" records may be represented as broker evidence.

## 5. Decisions

- Decision: the next Ready-Set target is a continuous paper runtime, not a fixed
  seven-day runner.
- Decision: observation duration is operator-controlled metadata.
- Decision: KIS paper/mock network calls and paper orders are allowed only
  inside `HWISTOCK-UNIT-010` Go/Prove scope and only after its preflight passes.
- Decision: KIS-facing broker proof is KRX-paper-only under the current
  capability matrix.
- Decision: live trading remains denied until a later explicit go/no-go approval.
