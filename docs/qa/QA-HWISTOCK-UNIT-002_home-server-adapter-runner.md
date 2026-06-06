---
schema_version: hwi.qa-scenario/v0
id: QA-HWISTOCK-UNIT-002
type: qa_scenario
name: Home-server broker-adapter runner QA
unit_refs:
  - HWISTOCK-UNIT-002
module_refs:
  - HWISTOCK-MOD-001
profile_refs:
  - PROFILE-HWISTOCK
status: set
ready_set_rebaseline_status: go_check_passed
implementation_status: go_check_passed
owner: hwi
updated_at: 2026-06-05
evidence_refs:
  - docs/evidence/RUN-20260602_unit-002-home-server-adapter-runner-set.md
  - docs/evidence/RUN-20260604_unit-002-go-preflight.md
  - docs/evidence/RUN-20260604_unit-002-go-check.md
  - docs/evidence/RUN-20260605_ready-set-continuous-adapter-runner.md
---

# Home-Server Broker-Adapter Runner QA

## 1. Purpose

Prove that the hwiStock runtime can operate as a 24-hour home-server program in
adapter-backed mode without depending on a Codex session and without enabling operation
orders. The runner must also distinguish 24-hour service uptime from Korea market
session activity, and separate 24-hour information ingestion from trading/order
routing. Trading venue routing is investment-mode aware: paper/mock mode is
KRX-only for new investment/order decisions from 09:00-15:00 KST and rejects
NXT broker branches; future live mode starts `krx_only`, and NXT venue routing
requires separate owner approval and Ready-Set.

## 2. Scope

In scope:

- service/process start, stop, restart
- adapter-backed mode config
- no-order dry-run behavior before KIS adapter approval
- future official KIS KRX broker-adapter API separation and budget mapping
- market-session scheduler behavior
- branch separation between information ingestion and trading
- off-hours idle/maintenance/reporting mode
- health output
- kill switch state
- audit logs
- daily evidence summary shape
- operator-selected observation-window metadata

Out of scope:

- brokerage order placement
- account-affecting trading
- broker credential handling
- KIS/external broker network calls
- broker-provided broker-adapter/demo/testbed/adapter API calls before approved KIS
  verification/integration
- final strategy profitability claims

## 3. Scenario Rows

| row_id | priority | mode | steps | expected_result | evidence |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P0 | service | Start runner, detach from Codex/shell where applicable | Runner continues independently | process/service status |
| QA-002 | P0 | config | Inspect default environment/config | Operation mode is disabled; adapter-backed mode is active | config/log |
| QA-003 | P0 | safety | Activate kill switch | Dry-run/order routing is blocked and logged | health/log |
| QA-004 | P1 | health | Query or inspect health state | Loop, data, risk gate, order gate, and kill switch states are visible | health output |
| QA-005 | P1 | logs | Inspect audit logs | signal, decision, risk reject, dry-run order-intent, and error events are distinguishable | log paths |
| QA-006 | P1 | evidence | Generate daily summary and observation-window manifest | Summary includes date, runtime duration, mode, failures, dry-run intents or KIS broker orders when approved, risk rejects, and operator-selected observation-window metadata | evidence file |
| QA-007 | P0 | calendar | Simulate or inspect out-of-envelope state | Service remains healthy but active trading/order loops are idle or disabled outside 08:00-20:00 KST | health/log |
| QA-008 | P0 | safety | Inspect branch boundaries | News/disclosure ingestion output cannot directly invoke order routing | config/log/code review |
| QA-009 | P0 | routing | Simulate paper/mock 08:30, 09:30, 15:00, and 15:30 KST plus future-live 08:30/15:30 when approved | Paper/mock: 08:30 idle/off-window, 09:30 KRX, 15:00 and 15:30 no new entry/order; future live may route NXT only after support proof and approval | route test output |
| QA-010 | P0 | dry-run | Submit approved order intent before KIS adapter approval | Intent is recorded as no-order dry-run only; no broker call, simulated fill, or fake balance is produced | adapter log |
| QA-011 | P0 | safety | Inspect config and outbound network attempts | KIS/external broker endpoints, broker broker-adapter/demo/testbed endpoints, credentials, tokens, and broker network calls are absent until approved | config/network log |
| QA-012 | P0 | config | Inspect adapter budget config/docs | Official broker-adapter budget candidate is 10,000,000 KRW and does not replace the 2,000,000 KRW operation-capital baseline | config/doc review |
| QA-013 | P0 | service | Inspect planned service config | `systemd` or an approved service manager is the official continuous-run evidence path; tmux/screen/manual shell is excluded from official evidence | service config/doc |
| QA-014 | P0 | config | Start or inspect runner with market-data source unset | Related trading loops report `source_unconfigured`/idle and cannot route orders | health/config log |
| QA-015 | P0 | security | Inspect bind/listen config | Health/API/dashboard surfaces bind `127.0.0.1` by default; LAN/public exposure requires later authenticated Set approval | config/network log |
| QA-016 | P0 | calendar | Inspect calendar config and simulate missing/stale cache | Runtime uses local cached KRX/NXT calendar; missing or stale cache makes trading/order loops idle | config/route log |
| QA-017 | P0 | alert | Trigger service, calendar, kill-switch, and daily-summary alert events | Alerts appear in systemd journal, `data/alerts`, dashboard audit panel when implemented, and daily close report; no external delivery occurs | journal/log/report |
| QA-018 | P0 | evidence | Inspect operation observation report template | Report uses operator-selected start/end/duration metadata, P0 safety/evidence criteria, and no profit threshold; it does not require a hardcoded runner duration | evidence contract |

## 4. PASS / FAIL / BLOCKED Rules

- PASS: runner operates independently in adapter-backed mode with visible health,
  `systemd` service lifecycle, kill switch, audit evidence, simple KRX/NXT
  routing, local-only health/API surfaces, and idle behavior outside the trading
  envelope.
- FAIL: runner requires Codex to stay alive, enables account-affecting orders by default, or
  cannot prove kill switch, branch separation, no-order dry-run boundary, or
  market-session gating behavior.
- BLOCKED: implementation cannot prove `systemd` lifecycle, local-only bind,
  source-unconfigured idle behavior, or no-order dry-run broker boundary.

## 5. Evidence Requirements

- process/service status
- config showing adapter-backed default
- kill switch log
- market calendar/routing state output
- health output
- audit log paths
- daily summary sample
- no-order dry-run order-intent sample, and KIS broker order/fill/balance/position
  sample only after approval
- outbound-network absence evidence for KIS/external broker and broker
  broker-adapter/demo/testbed endpoints
- local cached calendar coverage and stale-calendar idle evidence
- local alert event log and no-external-delivery evidence
- operator-selected operation observation evidence manifest
