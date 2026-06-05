---
schema_version: hwi.ready-set-row-closure/v0
stage: ready-set
status: active
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
updated_at: 2026-06-05
current_authority: true
implementation_ready: true
implementation_ready_scope: operational_contract_hardened_go_check_queue
completion_report_ref: docs/set/READY-SET-COMPLETION-20260605_operational-paper-trading-program_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-paper-trading-program_hwistock.md
module_ref: docs/modules/HWISTOCK-MOD-009_operational-paper-trading-program.md
owner_rebaseline_evidence_ref: docs/evidence/RUN-20260605_owner-runtime-architecture-10m-trade-document-rebaseline.md
contract_hardening_unit_ref: docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md
contract_hardening_evidence_ref: docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md
---

# Ready-Set Row Closure Matrix — Operational Paper Trading Program

## 1. Queue Rows

| order | unit_id | unit_ref | qa_ref | row_state | allowed_first_go_scope | hard_exclusions |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-011 | `docs/units/HWISTOCK-UNIT-011_operational-runtime-supervisor.md` | `docs/qa/QA-HWISTOCK-UNIT-011_operational-runtime-supervisor.md` | go_started_check_pending | User systemd install/sync, local-only service startup, runtime timer health, restart/status evidence. Evidence: `docs/evidence/RUN-20260605_unit-011-runtime-start-go.md`. | KIS paper cash order submission, live endpoints, public bind, secret printing. |
| 2 | HWISTOCK-UNIT-016 | `docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md` | `docs/qa/QA-HWISTOCK-UNIT-016_runtime-contract-hardening.md` | set_complete | Runtime data/execution contracts, schema catalog, valid/invalid fixtures, and validator are defined and pass local validation. Evidence: `docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md`. | Broker calls, AI provider calls, live endpoints, credential reads/prints, strategy-risk parameter changes. |
| 3 | HWISTOCK-UNIT-012 | `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md` | `docs/qa/QA-HWISTOCK-UNIT-012_ai-analysis-runtime.md` | ready_for_go_check | DeepSeek Pro hourly aggregate/market-regime artifact, DeepSeek Flash 10-minute `flash_trade_document/v0`, action schema/redaction/no-order validation. | Broker calls, AI direct orders, unapproved cost caps, credentials in prompts, ChatGPT browser side effects unless separately scoped. |
| 4 | HWISTOCK-UNIT-013 | `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md` | `docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md` | ready_for_go_check | KIS WebSocket realtime and 1-3-minute REST ranking collector, Flash trade-document action consumption, source refs, freshness/session confirmation, deterministic risk-gated `paper_order_intent/v0` queue. | KIS order calls, news-only orders, AI-only orders, fake broker state, unapproved scraping, NXT/SOR broker-facing collection. |
| 5 | HWISTOCK-UNIT-014 | `docs/units/HWISTOCK-UNIT-014_kis-paper-order-execution-reconciliation.md` | `docs/qa/QA-HWISTOCK-UNIT-014_kis-paper-order-execution-reconciliation.md` | ready_for_go_check | KIS KRX paper order execution, superseded WAIT_BUY cancellation, realtime stop/take-profit/trailing exits, cancel/fill lookup, balance/buyable reconciliation, idempotency, ambiguous-submit recovery, no-fake-broker evidence. | Live endpoints, NXT/SOR paper broker routing, raw secrets, duplicate orders, fake PnL. |
| 6 | HWISTOCK-UNIT-015 | `docs/units/HWISTOCK-UNIT-015_operator-console-observation-prove.md` | `docs/qa/QA-HWISTOCK-UNIT-015_operator-console-observation-prove.md` | ready_for_go_check | Read-only dashboard/API status, observation-window reports, browser/tunnel Prove, readiness flag separation. | Buy/sell controls, live toggle, public bind, secret/raw-account display, false live readiness. |

## 2. Scope Result

Selected queue scope: `operational_contract_hardened_go_check_queue`.

The narrower UNIT-010 Ready-Set remains useful as a local no-network foundation
but is not enough to prove an actually running stock-trading program.

The clarified operational architecture and UNIT-016 runtime contracts are
accepted for Go-Check entry. This row closure still does not prove paper-run
readiness; each ready row needs fresh Go, Check, QA disposition, and evidence.

## 3. Row Closure Rule

Rows may move from `ready_for_go_check` only after Go writes fresh evidence and
Check reviews it. A row with only docs, only code, only local unit tests, or only
trace sync is not closed.
