---
schema_version: hwi.source/v0
id: HWISTOCK-MARKET-CALENDAR-ALERT-PAPER-GATE
type: calendar_alert_paper_gate_policy
name: hwiStock market calendar, alert, and paper gate policy
status: set
owner: hwi
created_at: 2026-06-02
updated_at: 2026-06-02
unit_refs:
  - HWISTOCK-UNIT-002
  - HWISTOCK-UNIT-004
  - HWISTOCK-UNIT-006
module_refs:
  - HWISTOCK-MOD-001
  - HWISTOCK-MOD-003
  - HWISTOCK-MOD-005
---

# hwiStock Market Calendar, Alert, And Paper Gate Policy

## 1. Purpose

This policy closes the first Set contract for:

- trading-day and session calendar authority
- first-pass local alert channel
- one-week paper/sandbox pass criteria

It does not approve broker network calls, AI network calls, live trading, public
dashboard exposure, or profit claims.

## 2. Market Calendar Source Contract

### 2.1 Source Hierarchy

| priority | source | use | network boundary |
| --- | --- | --- | --- |
| 1 | KRX official trading-days/holidays page and KRX notices | Trading-day, holiday, year-end close, and exceptional market-management day authority | Public official source review or cached calendar only |
| 2 | NXT official site/session notices | NXT session availability and session-window reference | Public official source review or cached calendar only |
| 3 | KIS `국내휴장일조회[국내주식-040]` | Broker-side holiday/open-day cross-check after approval | Broker network call only inside a later approved KIS integration unit |
| 4 | Local cached calendar | Runtime scheduler input during dry-run/paper when broker calendar API is unavailable or paper-unsupported | No network call during ordinary scheduler evaluation |

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
- KIS holiday lookup is paper-unsupported in the local KIS capability matrix.
  It must not be called during no-order dry-run and must not be required for
  KIS KRX paper evidence unless a future approved broker-network unit enables
  it.
- If KIS holiday lookup is approved later, cache it at most once per KST day and
  treat `opnd_yn` as a cross-check input, not the only trading gate.

### 2.3 Session Routing

hwiStock's owner-selected routing policy remains:

- KRX: 09:00-15:00 KST
- NXT: 08:00-09:00 KST and 15:00-20:00 KST
- Idle: outside 08:00-20:00 KST or when the calendar says closed/stale

This is a project routing policy. It does not claim to model every exchange
auction, overlap, or broker-specific route detail.

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

## 4. One-Week Paper/Sandbox Pass Criteria

The one-week test is a safety, evidence, and operational-readiness gate. It is
not a profit target and does not prove expected future profit.

Minimum duration:

- at least 7 consecutive calendar days of runner evidence
- at least 5 valid Korean market open days
- if holidays or exceptional closures reduce open days below 5, extend the run
  until 5 valid open days are covered

Pass requires all P0 rows below:

| area | P0 pass criterion |
| --- | --- |
| service lifecycle | systemd services can start, stop, restart, and report health without a Codex session |
| safety boundary | no live orders, real-money orders, unapproved broker calls, or unapproved AI calls occur |
| broker boundary | before approved KIS paper, records stop at no-order dry-run; after approved KIS paper, only supported KRX paper paths may produce broker-backed evidence |
| calendar/session | trading/order loops are idle on closed/stale-calendar days and outside the configured KRX/NXT envelope |
| risk gates | every order intent passes or is rejected by cash reserve 0.25, max holdings 5, AI stop max -5, stale-data, and kill-switch checks |
| evidence completeness | every day has a paper-day evidence manifest, health summary, risk rejects, order-intent/order-state summary, and daily close report |
| PnL calculation | PnL fields are system-calculated from order/fill/position records; AI may interpret but not calculate the numbers |
| source policy | only approved/conditional-approved data sources run; blocked HTML scraping and unofficial APIs do not run |
| reconciliation | KIS KRX paper orders/fills/balances reconcile when KIS paper is approved; unsupported NXT/SOR branches are disabled or explicit-fallback-only |
| incident handling | any critical alert is acknowledged, explained, and either fixed or marked as a blocker before live-readiness discussion |

Automatic fail or extension triggers:

- any live order or real-money order
- any unapproved broker, AI, or external alert network call
- any credential leak into logs/docs/artifacts
- any fake broker fill, fake balance, or simulated PnL represented as broker
  evidence
- any order intent created while kill switch is active, data is stale, calendar
  is closed/stale, or risk gates reject
- any unexplained service outage that prevents daily evidence creation
- any unreconciled KIS paper order/fill/balance discrepancy after the daily
  close reconciliation window

After passing, live operation still requires an explicit user go/no-go approval.

## 5. Evidence Requirements

Each day of the paper/sandbox gate must link:

- `data/evidence/YYYY-MM-DD/paper-day.json`
- `data/reports/YYYY-MM-DD/morning-0700.md`
- `data/reports/YYYY-MM-DD/daily-close-2000.md`
- alert log path
- health/service status
- source collection summary
- candidate/order-intent/order-state summary
- risk reject summary
- PnL summary with `calculation_source: system`

The final one-week evidence report must list every day, market-open status,
runner uptime, P0 pass/fail rows, critical alerts, fixes, unresolved blockers,
and the explicit live-readiness recommendation.
