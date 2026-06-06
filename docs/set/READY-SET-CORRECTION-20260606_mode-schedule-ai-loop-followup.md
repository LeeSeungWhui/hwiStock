---
schema_version: hwi.ready-set-correction/v0
stage: ready-set
status: set_followup_required_before_full_ai_operation_claim
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
updated_at: 2026-06-06
current_authority_for:
  - investment_mode_schedule
  - integrated_market_analysis_feed_policy
  - krx_only_execution_authority
  - morning_watchlist_requirement
  - gpt_pro_local_browser_use_route
  - flash_10m_trade_document_requirement
  - daily_close_report_requirement
  - dynamic_exposure_cap_requirement
related_completion_ref: docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md
module_ref: docs/modules/HWISTOCK-MOD-009_operational-automated-trading-program.md
unit_refs:
  - docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md
  - docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md
  - docs/units/HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md
prompt_refs:
  - docs/set/READY-SET-GPT-PRO-MORNING-PROMPT-20260606_hwistock.md
---

# Ready-Set Correction — Investment Mode Schedule And AI Loop Follow-Up

## 1. Correction Summary

This docs-only Ready-Set correction folds the owner's latest operational review
into the existing operational automated-trading Ready-Set.

It does **not** create a parallel architecture and does **not** cancel the
current KIS paper/mock experiment target. It clarifies the follow-up scope that
must be closed before hwiStock claims the full owner-defined AI operation loop is
ready.

Critical correction:

- KRX public regular-session/market-data context may remain `09:00-15:30 KST`.
- KRX paper/mock **investment/order-decision** time is `09:00-15:00 KST`.
- The `15:00-15:30 KST` period is close/market-data/reconciliation context only
  for paper/mock mode. It must not unlock new KRX paper/mock entries or broker
  order submissions.

## 2. Required Investment Mode Split

The runtime must separate operation stage from investment mode:

| concern | value family | purpose |
| --- | --- | --- |
| operation stage | `paper_experiment`, `live_production`, future dry-run labels | says whether the current run is an experiment, live operation, or non-order validation |
| investment mode | `paper`, `live` | says which broker-market capability set and schedule apply |
| market-analysis feed mode | `integrated` | says which KIS feed family is the default input for AI/context/ranking |
| execution venue mode | `krx_only`, future `krx_nxt` | says which venue can authorize broker submit |

Canonical docs variable:

- `HWISTOCK_INVESTMENT_MODE=paper|live`
- `HWISTOCK_MARKET_ANALYSIS_FEED_MODE=integrated`
- `HWISTOCK_EXECUTION_VENUE_MODE=krx_only`
- `HWISTOCK_NXT_ENABLED=false`

Existing KIS-specific env/config names may temporarily map into this canonical
mode during implementation, but Ready-Set docs must reason in terms of
`HWISTOCK_INVESTMENT_MODE`.

Market-analysis feed policy:

- hwiStock uses KIS integrated realtime feeds as the default market-analysis
  input.
- Integrated feeds are used for market context, DeepSeek Pro hourly reports,
  Flash 10-minute trade documents, ranking/scoring, and watchlist updates.
- KRX quote/session/order-window evidence remains authoritative for executable
  order checks in paper/mock mode.
- Paper/mock mode never enables NXT broker submission and never uses NXT-only
  feeds as execution authority.
- Separate KRX/NXT feeds are diagnostic-only unless a future live-mode
  Ready-Set explicitly enables NXT venue routing.

## 3. Mode-Aware Schedule Contract

| branch/job | paper investment mode | live investment mode |
| --- | --- | --- |
| `news_disclosure_collector` | 24h | 24h |
| `deepseek_pro_hourly` | top of every hour, 24h | top of every hour, 24h |
| `gpt_morning_watchlist` | starts `07:15 KST`, hard cutoff before the first paper Flash bucket at `09:00 KST` | starts `07:15 KST`, hard cutoff before the first live Flash bucket at `08:00 KST` |
| `kis_intraday_market_collector` | KRX + integrated market-data context during `09:00-15:30 KST` where supported | KRX/NXT/integrated market-data context during `08:00-20:00 KST` where capability flags prove support |
| market-analysis feed authority | integrated feed by default | integrated feed by default |
| execution venue authority | KRX-only; NXT disabled | KRX-only by default; NXT disabled until future owner approval and Ready-Set |
| `deepseek_flash_decision_10m` | every 10 minutes during `09:00-15:00 KST`; first paper Flash must reference the morning watchlist or safe-block | every 10 minutes during `08:00-20:00 KST`; first live Flash must reference the morning watchlist or safe-block |
| `trade_document_executor` / broker order submit | KIS paper/mock KRX cash orders only during `09:00-15:00 KST` and only inside a valid `paper_experiment` session approval | venue/capability based KRX/NXT only after future live approval and proof |
| daily close / operation summary | after paper KRX market-data close, target `15:30 KST`; no new paper entries after `15:00 KST` | target `20:00 KST` |

## 4. Follow-Up Ready-Set Requirements

The next docs/code Go queue must close these items before claiming the full AI
operation scenario is ready:

1. Add the canonical investment-mode constant/config mapping:
   `HWISTOCK_INVESTMENT_MODE=paper|live`.
2. Centralize the mode-aware schedule in one runtime policy file or equivalent
   service contract.
3. Ensure `hwistock-intel-collector.service` / `.timer` is present and proves
   24-hour news/disclosure collection into normalized events.
4. Add `gpt_morning_watchlist` service/timer or an equivalent browser-review
   orchestration path that starts at `07:15 KST`, covers the prior close through
   the current morning, and writes `morning_watchlist/v0`. The approved GPT Pro
   route for this project is **Codex CLI on the local desktop/workstation using
   local browser-use**. SSH browser-use is explicitly forbidden for this morning
   review path.
5. Require the first Flash bucket in each investment mode to reference the
   latest valid morning watchlist or write `NO_TRADE`.
6. Keep Flash as a 10-minute decision document, not a per-minute order brain.
   Each action must carry symbol/name, action type, entry zone if relevant,
   take-profit, stop-loss, trailing-stop percent, cancel-if-not-filled window,
   size/cash cap, validity window, source refs, Pro refs, morning-watchlist ref
   when required, portfolio/order refs, and risk notes.
7. Add the daily close DeepSeek Pro job: paper summary after `15:30 KST`, live
   summary at `20:00 KST`.
8. Replace the static reserve-only sizing check with a dynamic exposure cap:
   `current_position_value_krw + pending_buy_notional_krw +
   new_order_notional_krw <= effective_total_deposit_krw * 0.75`, while still
   respecting the 2,000,000 KRW risk-overlay cap unless a future approved
   profile/unit change raises it.

## 4.1 GPT Pro Local Browser-Use Prompt Contract

The GPT Pro morning path is a bounded external-review sidecar, not part of the
broker executor and not an SSH browser task.

The GPT Pro route is optional/fallback-capable, but a
`morning_watchlist/v0` artifact or explicit `NO_TRADE` safe-block artifact is
mandatory before the first Flash bucket.

Required route:

```text
local Codex CLI -> local browser-use -> user's logged-in local Chrome -> ChatGPT Pro
```

Forbidden route:

```text
SSH Codex session -> SSH browser-use / reverse socket / remote Chrome bridge -> ChatGPT Pro
```

The Codex CLI prompt sent to GPT Pro must include only a sanitized
`morning_watchlist_input_bundle/v0` summary:

- trading date and investment mode;
- prior close through current-morning normalized news/disclosure summaries;
- DeepSeek Pro hourly artifact summaries and refs;
- sanitized KIS market-data summaries and refs;
- current portfolio/order-state summary only after redaction and only when
  needed for conflict/risk context;
- deterministic candidate universe refs;
- explicit forbidden actions: no broker calls, no credentials, no order
  placement, no risk-parameter changes, no profit guarantees.

The requested GPT Pro output format must be `morning_watchlist/v0` compatible:

- ranked watchlist items with ticker/name;
- thesis and source refs;
- invalidation conditions;
- risk notes;
- whether the item is `watch_only`, `eligible_for_flash_review`, or `reject`;
- missing-data notes;
- no executable broker-order fields.

If local Codex CLI or local browser-use is unavailable, the morning path must
write a named `NO_TRADE` safe-block artifact or a DeepSeek-derived
`morning_watchlist/v0` artifact. It must not silently switch to SSH browser-use.

Prompt template source:

- `docs/set/READY-SET-GPT-PRO-MORNING-PROMPT-20260606_hwistock.md`

## 5. Readiness Interpretation

- The current Monday KIS paper/mock experiment can still proceed if the existing
  `paper_experiment_ready` hard blockers pass.
- Missing morning watchlist, daily close Pro, centralized investment-mode
  schedule, or dynamic 75% exposure cap blocks the claim that the complete AI
  operation scenario is ready.
- Any implementation that treats `15:00-15:30 KST` as paper/mock KRX
  order-entry time is a P0 contract violation.
