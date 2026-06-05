---
schema_version: hwi.evidence/v0
id: RUN-20260605-owner-selected-naver-kis6-scope
type: evidence
name: Owner-selected NAVER plus KIS six-input runtime scope
stage: set
environment: local_docs_update
status: pass
owner: hwi
created_at: 2026-06-05
updated_at: 2026-06-05
current_authority: true
secret_values_shared: false
---

# Owner-Selected NAVER + KIS 6 Runtime Scope

## 1. Decision

After the post-review source/scope reduction prompt, the owner selected:

```text
네이버+KIS 6개
```

This means:

- NAVER Search News API is the selected first-runtime news source.
- OpenDART remains the selected disclosure source.
- Public RSS/news search is fallback-only and must not run in parallel with
  NAVER in the first runtime loop.
- UNIT-013 KIS adapter-read signal input scope is exactly six inputs:
  1. KRX realtime trade price WebSocket;
  2. KRX realtime orderbook WebSocket;
  3. REST volume rank;
  4. REST execution-strength / volume-power rank;
  5. REST fluctuation rank;
  6. REST program-trading aggregate status where adapter-supported.

## 2. Safety Interpretation

The decision does not authorize:

- KIS order/cancel/modify calls in UNIT-013;
- unapproved endpoints;
- raw secret/account logging;
- KIS signal endpoints outside the six-input allowlist;
- public RSS running in parallel with NAVER;
- Flash inventing ticker candidates outside deterministic `compiled_watch/v0`.

Missing NAVER config or missing KIS adapter-read proof produces safe-block evidence,
not an implicit fallback to another source.

## 3. Files Updated

- `docs/sources/HWISTOCK-SOURCE-REGISTRY.md`
- `docs/modules/HWISTOCK-MOD-009_operational-automated-trading-program.md`
- `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md`
- `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
- `docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md`
- `docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md`
- `docs/set/READY-SET-ROW-CLOSURE-20260605_operational-automated-trading-program_hwistock.md`
- `docs/evidence/RUN-20260605_owner-runtime-architecture-10m-trade-document-rebaseline.md`

## 4. Boundary

No KIS broker/API call, NAVER API call, OpenDART call, DeepSeek call, operation
endpoint call, order/cancel/modify call, or secret env/config read was performed
for this docs update.
