---
schema_version: hwi.source/v0
id: HWISTOCK-MARKET-CALENDAR-ALERT-ADAPTER-GATE
type: calendar_alert_paper_gate_policy
name: hwiStock market calendar, alert, and operation observation policy
status: set
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-05
unit_refs:
  - HWISTOCK-UNIT-002
  - HWISTOCK-UNIT-004
  - HWISTOCK-UNIT-006
  - HWISTOCK-UNIT-010
module_refs:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-005
  - HWISTOCK-MOD-008
---

# hwiStock Market Calendar, Alert, And Adapter Observation Policy

## 1. Purpose

This policy closes the first Set contract for:

- trading-day and session calendar authority
- first-pass local alert channel
- operator-controlled adapter-backed observation criteria

It does not approve broker network calls, AI network calls, account-affecting operation, public
dashboard exposure, or profit claims.

Current correction: the runner is a 24-hour continuous home-server service. The
adapter-backed observation period is **not** hardcoded as seven days or any other
fixed duration in the program. The project owner/operator decides when an
observation window starts, when it stops, and whether the collected evidence is
enough for a later go/no-go discussion. Docs and code must model the period as
operator-supplied run metadata, not as a baked-in service lifetime.

## 2. Market Calendar Source Contract

### 2.1 Source Hierarchy

| priority | source | use | network boundary |
| --- | --- | --- | --- |
| 1 | KRX official trading-days/holidays page and KRX notices | Trading-day, holiday, year-end close, and exceptional market-management day authority | Public official source review or cached calendar only |
| 2 | NXT official site/session notices | NXT session availability and session-window reference | Public official source review or cached calendar only |
| 3 | KIS `국내휴장일조회[국내주식-040]` | Broker-side holiday/open-day cross-check in the KIS adapter runtime | Broker network call only inside approved KIS adapter read/execution paths |
| 4 | Local cached calendar | Runtime scheduler input and primary order gate even when provider holiday cross-check is available | No network call during ordinary scheduler evaluation |

Checked public references on 2026-06-02:

- KRX Global `Trading Days and Holidays`:
  `https://global.krx.co.kr/contents/GLB/06/0606/0606030101/GLB0606030101T3.jsp`
- NXT official site:
  `https://www.nextrade.co.kr/`

Local KIS reference:

- `apiRefer/국내휴장일조회[국내주식-040].xlsx`

### 2.2 First-Pass Runtime Rule

- Runtime trading-day decisions use a local cached calendar file generated from
  approved official sources.
- Planned cache path: `config/market-calendar/krx-nxt-trading-days.json`.
- If the cached calendar is missing, expired, or does not cover the current
  KST date, active trading/order loops must stay idle with
  `calendar_unconfigured` or `calendar_stale`.
- KIS holiday lookup is implemented as provider cross-check evidence. It must
  not replace the local cached calendar as the primary order gate.
- Cache KIS holiday lookup at most once per KST day where practical and treat
  `opnd_yn` as a cross-check input, not the only trading gate.

### 2.3 Session Context And Internal Adapter-Order Window

hwiStock keeps two separate concepts:

1. **exchange/session context** used by collectors, AI analysis, reports, and
   operator UI; and
2. **broker-facing adapter-order enablement** used by the executor.

KRX public regular-session context is treated as 09:00-15:30 KST unless a
future market-calendar source update records a special day. NXT context covers
the NXT-published session windows. KIS broker/order routing is then gated by the
active investment mode:

- paper/mock mode: KRX broker order routing only; integrated realtime/market
  operation inputs are market-data/account-truth helpers, not an integrated
  broker-order venue.
- real investment mode: KRX and NXT broker order routing where KIS capability
  flags allow it.
- SOR: disabled before transport until a future approved contract enables it.
- Idle: outside the active venue envelope or when the calendar says
  closed/stale.

## 3. Alert Channel Contract

First-pass alerting is local-only and does not send messages to a third-party
service.

Required channels:

- systemd journal entries for service lifecycle and failures
- `data/alerts/YYYY-MM-DD/alerts.jsonl`
- dashboard audit/error panel when the dashboard unit is implemented
- `data/reports/YYYY-MM-DD/daily-close-2000.md`

Required alert event fields:

- `alert_id`
- `created_at_kst`
- `severity`: `info`, `warning`, `critical`
- `category`: `service`, `calendar`, `source`, `risk`, `broker_boundary`,
  `kill_switch`, `daily_summary`
- `message`
- `related_artifact_ids`
- `requires_operator_action`
- `acknowledged_at_kst`

External alert delivery such as Telegram, email, Discord, SMS, or webhook is
deferred and requires a later Set approval because it creates new credentials,
privacy, delivery, and network-operation risks.

## 4. Operator-Controlled Adapter/Adapter Observation Criteria

The adapter-backed observation window is a safety, evidence, and operational
readiness gate. It is not a profit target and does not prove expected future
profit.

Duration policy:

- The runner is designed to run continuously, 24 hours a day, across operator
  observation windows.
- The observation window length is chosen by the operator outside the program.
- The service must not auto-stop, auto-pass, or auto-fail because a fixed day
  count was reached.
- Evidence reports must record `observation_window_started_at_kst`,
  `observation_window_ended_at_kst` when ended, elapsed runtime, covered market
  days, skipped/closed days, and any operator note.
- If a future operation-readiness policy sets a minimum duration, it belongs in the
  approval/evidence decision record, not as a runner loop hardcode.

Pass requires all P0 rows below:

| area | P0 pass criterion |
| --- | --- |
| service lifecycle | systemd services can start, stop, restart, and report health without a Codex session |
| safety boundary | no account-affecting orders, account-affecting orders, unapproved broker calls, or unapproved AI calls occur |
| broker boundary | before approved KIS adapter, records stop at no-order dry-run; after approved KIS adapter, only supported KRX adapter paths may produce broker-backed evidence |
| calendar/session | trading/order loops are idle on closed/stale-calendar days and outside the configured KRX/NXT envelope |
| risk gates | every order intent passes or is rejected by cash reserve 0.25, max holdings 5, AI stop max -5, stale-data, and kill-switch checks |
| evidence completeness | every observation day has a adapter-day evidence manifest, health summary, risk rejects, order-intent/order-state summary, and daily close report |
| PnL calculation | PnL fields are system-calculated from order/fill/position records; AI may interpret but not calculate the numbers |
| source policy | only approved/conditional-approved data sources run; blocked HTML scraping and unofficial APIs do not run |
| reconciliation | KIS KRX broker orders/fills/balances reconcile when KIS adapter is approved; unsupported NXT/SOR branches are disabled or explicit-fallback-only |
| incident handling | any critical alert is acknowledged, explained, and either fixed or marked as a blocker before operation-readiness discussion |

Automatic fail or extension triggers:

- any account-affecting order or account-affecting order
- any unapproved broker, AI, or external alert network call
- any credential leak into logs/docs/artifacts
- any fake broker fill, fake balance, or simulated PnL represented as broker
  evidence
- any order intent created while kill switch is active, data is stale, calendar
  is closed/stale, or risk gates reject
- any unexplained service outage that prevents daily evidence creation
- any unreconciled KIS broker order/fill/balance discrepancy after the daily
  close reconciliation window

After the operator accepts an observation window, account-affecting operation still requires
an explicit user go/no-go approval and a current profile/unit update.

## 5. Evidence Requirements

Each observation day must link:

- `data/evidence/YYYY-MM-DD/paper-day.json`
- `data/reports/YYYY-MM-DD/morning-0700.md`
- `data/reports/YYYY-MM-DD/daily-close-2000.md`
- alert log path
- health/service status
- source collection summary
- candidate/order-intent/order-state summary
- risk reject summary
- PnL summary with `calculation_source: system`

The final observation evidence report must list every covered day, market-open
status, runner uptime, P0 pass/fail rows, critical alerts, fixes, unresolved
blockers, operator-selected window start/end metadata, and the explicit
operation-readiness recommendation if one is requested.
