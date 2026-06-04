---
schema_version: hwi.ready-set-decision-packet/v0
stage: ready-set
status: needs_user_approval
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
unit_id: HWISTOCK-UNIT-004
module_id: HWISTOCK-MOD-003
created_at: 2026-06-02
---

# Strategy Decision Packet

## 1. Purpose

This packet turns the remaining `HWISTOCK-UNIT-004` strategy blockers into a
single approval-ready decision set. It is not a profit claim and not live-trading
approval. The values below are proposed only as first-pass paper/sandbox
parameters for implementation planning.

## 2. Already Closed Decisions

- Capital policy: cash-only.
- Live starting capital: 2,000,000 KRW.
- Paper/mock target budget: 10,000,000 KRW until broker evidence proves the
  actual paper balance.
- Maximum simultaneous holdings: 5.
- Fixed per-symbol maximum allocation: none.
- Minimum cash reserve floor: every buy must preserve
  `minimum_cash_reserve_ratio = 0.25` of total capital.
- AI stop policy: AI may recommend the per-entry stop price, but deterministic
  validation rejects missing, stale, unauditable, disabled, or wider-than--5%
  stop output.
- No first-pass fallback stop: if the accepted AI stop is unavailable or invalid,
  the entry is rejected.

## 3. Recommended First-Pass Strategy Defaults

These defaults are intended to make the first implementation measurable without
pretending that the strategy is proven.

| decision_area | recommended_default | reason | approval_effect |
| --- | --- | --- | --- |
| strategy family | catalyst-confirmed intraday momentum | Matches the project direction: news/disclosure context plus chart confirmation for 10-20 minute trades. | Closes the broad alpha-family question. |
| candidate source path | event-first from approved DART/news/disclosure sources, plus chart-first candidates labeled as chart-first | Keeps candidate generation separate from entry and avoids HTML/unofficial scraping. | Allows candidate schema implementation. |
| chart/realtime source | KIS domestic quote/realtime/minute-data path only after explicit broker-network approval; otherwise source-unconfigured idle/dry-run | Uses the selected broker direction while preserving the current no-network gate. | Closes source selection without authorizing network calls. |
| candle intervals | 1-minute primary, 5-minute confirmation, 15-minute context | Fits 10-20 minute trades while allowing broader trend context. | Closes candle interval selection for first tests. |
| chart confirmation rule | require all first-pass gates in Section 4: VWAP availability/pass, rolling breakout/reclaim, volume spike, reward/risk, stale-data pass | Avoids entry on catalyst alone and keeps risk gate central. | Closes chart confirmation as a measurable first-pass rule. |
| liquidity threshold | require all first-pass liquidity gates in Section 4: 5-minute traded value, spread, and data availability | Prevents thin-name entries and makes missing market data fail closed. | Closes the first-pass liquidity rule as a measurable config. |
| market-alert source | local KRX/NXT calendar cache first; KIS market/quote status only after approved broker-network smoke | Aligns with the selected calendar policy and avoids paper-unsupported KIS holiday dependency. | Closes market-alert source selection for implementation planning. |
| entry result | `would_enter` / `dry_run_recorded` before KIS paper approval; no fake broker fill or fake PnL | Preserves the broker boundary. | Allows order-intent logging without broker calls. |
| take-profit target | first paper default target is the lower of +1.5% price move or +2R, capped inside the 1-5% target band | Keeps the user's strategy hypothesis but prevents profit claims. | Adds a measurable target field for paper evidence. |
| time stop | review at 10 minutes, exit by 20 minutes if the trade has not reached +0.5R or kept the chart setup valid; hard maximum 30 minutes | Matches the intended tempo but does not force constant re-entry. | Adds a measurable hold/exit review condition. |

## 4. First-Pass Numeric Rule Defaults

These defaults are intentionally conservative paper/sandbox starting points.
They are configuration values, not claims that the strategy will be profitable.

### 4.1 Candle And Data Freshness

- Primary candle: 1-minute OHLCV.
- Confirmation candle: 5-minute OHLCV.
- Context candle: 15-minute OHLCV.
- Stale-data reject: no required quote/candle field may be older than 10 seconds
  in active trading mode.
- Missing VWAP, missing volume, missing spread, missing traded-value, or missing
  candle data rejects entry.

### 4.2 Liquidity Gates

Before an entry can become `would_enter`, all must pass:

- Latest 5-minute traded value is at least 100,000,000 KRW.
- Latest quoted spread is no wider than 1.0%.
- Same-symbol latest 1-minute volume is available.
- The system can compute the accepted stop, target, and reward/risk from current
  data.

### 4.3 Chart Confirmation Gates

For the first paper strategy, all must pass:

- Price is above VWAP, or a 1-minute close has reclaimed VWAP after the candidate
  event.
- A 1-minute close breaks the previous rolling 5-minute high, or a 5-minute
  candle closes above the previous rolling 15-minute high.
- Latest 1-minute volume is at least 2.0x the median of the prior 20 completed
  1-minute candles for the same symbol.
- Accepted stop distance is within the deterministic -5% maximum loss envelope.
- Expected reward/risk is at least 1.2R using the selected target and accepted
  stop.

### 4.4 Exit Defaults

- Hard stop: exit attempt when the accepted stop is hit.
- Initial target: lower of +1.5% price move or +2R, capped inside the 1-5% target
  band.
- Trailing: after +1R, move review state to protect break-even or better; exact
  trailing mechanics may be refined after paper evidence.
- Time review: at 10 minutes, mark `hold_review` unless the position reached at
  least +0.5R and the chart setup remains valid.
- Time exit: by 20 minutes if target/trailing condition has not justified hold.
- Hard maximum: by 30 minutes regardless of signal state, except forced earlier
  exit by stop, stale data, kill switch, or session/day-end flat policy.

## 5. Approval Choices

Recommended approval wording:

> Approve the first-pass strategy defaults in
> `docs/set/READY-SET-STRATEGY-DECISION-PACKET-20260602_hwistock.md` for
> paper/sandbox planning only. Keep broker and AI network calls disabled until
> later explicit approval.

If approved, update:

- `docs/modules/HWISTOCK-MOD-003_strategy-risk-rulebook.md`
- `docs/units/HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/qa/QA-HWISTOCK-UNIT-004_strategy-risk-rulebook.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260602_hwistock.md`
- `docs/set/READY-SET-COMPLETION-20260602_hwistock.md`

## 6. Non-Approval Path

If this packet is not approved, keep `HWISTOCK-UNIT-004` blocked and narrow the
first Go queue to storage, DART/source ingestion, KIS docs verification, and
other non-trading foundations only.

## 7. Safety Notes

- This packet does not approve live trading.
- This packet does not approve KIS/external broker network calls.
- This packet does not approve AI API network calls.
- This packet does not assert expected profit.
- Any later strategy/risk parameter change remains an explicit approval item.
