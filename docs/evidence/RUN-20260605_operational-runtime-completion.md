# RUN-20260605 operational broker-adapter runtime completion

> Correction / supersession note (2026-06-05): after the post-Pro Ready-Set
> rebaseline, this evidence must be read as "runtime/artifact smoke completed",
> not as proof that the program is operation-ready. Current authority remains
> `docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md`,
> reinforced with explicit non-readiness and dashboard/runtime truth requirements.

Date: 2026-06-05 KST
Workspace: `/data/workspace/My/hwiStock`

## Scope

Implemented and smoke-checked the broker-adapter operational loop:

1. KIS broker adapter-read market collector
2. compiled-watch candidate generation
3. DeepSeek Pro hourly market analysis
4. DeepSeek Flash trade document generation
5. broker order intent generation
6. continuous KIS broker adapter runner consuming latest intent queue
7. user systemd timers/services with daily file logs

Unapproved brokerage domain and account-affecting orders remain disabled.

## Changed runtime behavior

- KIS market collector now performs the six approved adapter-read inputs when
  `HWISTOCK_KIS_MARKET_READ_NETWORK_ENABLED=true`.
- KIS market collector writes:
  - `data/kis-market/<YYYY-MM-DD>/kis-market-snapshot-latest.json`
  - `data/compiled-watch/<YYYY-MM-DD>/compiled-watch-latest.json`
- compiled-watch candidates are filtered to ordinary 6-digit numeric symbols,
  minimum 1,000 KRW price, and exclude obvious ETF/ETN/inverse/leverage/SPAC/bond
  names.
- Pro hourly runner calls DeepSeek when grounded news/KIS context exists and
  writes `data/ai/<YYYY-MM-DD>/pro-hourly-latest.json`.
- Flash runner calls DeepSeek, validates the deterministic bounded trade
  document, then writes:
  - `data/trade-documents/<YYYY-MM-DD>/flash-trade-document-latest.json`
  - `data/intents/<YYYY-MM-DD>/broker-order-intents-latest.jsonl`
- Broker-adapter runner now auto-loads the latest intent queue when no explicit intent
  file is supplied.
- Broker-adapter runner marks intents consumed only after a passed KIS broker adapter cash-order
  response.
- Broker-adapter runner blocks broker order submission outside KRX regular session even
  while the 24-hour service remains running.
- Shared KIS broker adapter token cache was added outside the repo at
  `/home/hwi/.config/hwistock/runtime/kis-paper-token-cache.json` to avoid
  tokenP/rate-limit churn. Token values are never printed in evidence.

## Systemd state

Installed updated user units:

- `/home/hwi/.config/systemd/user/hwistock-kis-market-data.service`
- `/home/hwi/.config/systemd/user/hwistock-kis-paper-runner.service`

Active timers observed:

- `hwistock-kis-market-data.timer`: active/waiting
- `hwistock-ai-analysis.timer`: active/waiting
- `hwistock-ai-flash.timer`: active/waiting
- `hwistock-kis-paper-runner.timer`: active/waiting
- `hwistock-runner-tick.timer`: active/waiting

Daily file logs are written under:

- `logs/systemd/2026-06-05/hwistock-kis-market-data.log`
- `logs/systemd/2026-06-05/hwistock-ai-analysis.log`
- `logs/systemd/2026-06-05/hwistock-ai-flash.log`
- `logs/systemd/2026-06-05/hwistock-kis-paper-runner.log`

## Ordered smoke result

Commands were run in this order with secrets loaded only through env files:

1. KIS market collector
2. Pro hourly analysis
3. Flash trade document
4. Broker-adapter runner

Sanitized result summary:

| Step | Result |
| --- | --- |
| KIS market collector | `status=ok`, `candidate_count=5`, token cache hit |
| Pro hourly | `validation_status=accepted`, `document_kind=MARKET_ANALYSIS`, `provider_status=ok`, `market_mode=RISK_OFF` |
| Flash 10m | `validation_status=accepted`, `document_kind=TRADE_ACTIONS`, `provider_status=ok`, `accepted_count=5` |
| Broker-adapter runner at 16:24 KST | intent loaded from the next FIFO queue, broker order not called, blocked by `kis_paper_order_requires_krx_regular_session` |

Runner after-hours block is expected: the service remains 24-hour, but KIS broker adapter
orders are allowed only during KRX regular session.

## Verification

Passed:

```text
python3 -m py_compile backend/lib/kis_paper_token_cache.py backend/lib/kis_market_data_runtime.py backend/lib/kis_paper_continuous_runtime.py
python3 -m pytest backend/tests/test_operational_go_check_pipeline.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_ai_orchestration_layer.py backend/tests/test_hwistock_runner.py
# 72 passed
python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --changed --fail-on-warn --profile docs/profiles/PROFILE-HWISTOCK.md
# Status: pass, error=0 warning=0
```

Known unrelated full backend suite result:

```text
python3 -m pytest backend/tests
# 200 passed, 12 failed
```

The 12 failures are in legacy MyWebTemplate auth/logout/refresh tests returning
403 and are outside the hwiStock broker-adapter runtime scope.

## Residual risk / next watch item

- During KRX regular session, the next broker-adapter runner tick should submit only if a
  fresh non-expired Flash intent exists and the risk overlay passes.
- If KIS returns `EGW00201`, treat it as a rate-limit signal and keep the shared
  token cache plus call-gap throttle enabled.
- Superseded wording: this evidence previously overstated the current system as
  ready for a broker-adapter operation test. The post-Pro Ready-Set rebaseline narrows
  that to runtime/artifact smoke only; the current system is not operation-ready
  or operational-trading-ready until the corrective queue and observation gate
  pass.
