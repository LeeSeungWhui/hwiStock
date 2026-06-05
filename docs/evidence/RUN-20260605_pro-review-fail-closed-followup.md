---
schema_version: hwi.evidence/v0
id: RUN-20260605-pro-review-fail-closed-followup
type: evidence
stage: go-check
status: pass
project_root: /data/workspace/My/hwiStock
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-05
owner: codex
review_source: pasted Pro review after d3ed116 push
---

# Pro Review Fail-Closed Follow-up

## 1. Scope

This run addresses the remaining Pro review findings after the dashboard AI
conversation push.

Implemented remediation:

- Paper-order approval now rejects `HWISTOCK_ALLOW_WEEKDAY_CALENDAR_FALLBACK`
  when paper orders are requested.
- Paper-order approval requires an order-grade market-data source
  (`kis_paper_read` or `kis_market_six_input`) and a configured calendar file.
- Order-intent preflight now requires `paper_only = true` for every broker
  submit path, not only when a live adapter value appears.
- Order-intent preflight now requires the broker adapter enum to be
  `kis_paper`; missing, `kis_live`, unknown, or unexpected values fail closed.
- The JSONL queue loader is now named and reported as FIFO:
  `next_intent_queue_fifo`, while the existing file name remains
  `paper-order-intents-latest.jsonl` for artifact compatibility.
- AI conversation readiness truth now reflects inspected KIS paper runner
  service policy, including `systemd_order_enabled_contradicts_readiness`.
- AI conversation responses/audits now include
  `accessInvariant = loopback_or_frontend_bff_only`, and the router docstring
  records the loopback/BFF exposure invariant.

## 2. Validation

Commands:

- `source ./env.sh && python -m pytest backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_hwistock_ai_conversation.py -q`
  - PASS, 28 tests
- `source ./env.sh && python -m pytest backend/tests/test_operational_go_check_pipeline.py backend/tests/test_kis_paper_continuous_runner.py backend/tests/test_hwistock_ai_conversation.py -q`
  - PASS, 39 tests
- `source ./env.sh && python /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn`
  - PASS, changed scan files: 3, findings: error=0, warning=0, info=0
- `source ./env.sh && python -m py_compile backend/lib/kis_paper_continuous_runtime.py backend/lib/operator_console_runtime.py backend/router/HwiStockAiRouter.py`
  - PASS
- `git diff --check`
  - PASS

## 3. Boundary

- No KIS, broker, Naver, DART, or AI provider network call was made.
- No order was submitted.
- No secret file was read or printed.
- No service was restarted or deployed in this remediation run.
- This run improves fail-closed readiness for a future explicitly approved
  paper-order smoke; it does not declare operational trading readiness.
