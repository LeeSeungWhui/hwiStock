---
schema_version: hwi.ready-set-row-closure/v0
stage: ready-set
status: go_check_local_passed_with_side_effect_rows_blocked
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
updated_at: 2026-06-05
current_authority: true
implementation_ready: true
implementation_ready_scope: operational_contract_hardened_go_check_queue
go_check_evidence_ref: docs/evidence/RUN-20260605_operational-go-check-units-012-015.md
completion_report_ref: docs/set/READY-SET-COMPLETION-20260605_operational-automated-trading-program_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260605_operational-automated-trading-program_hwistock.md
module_ref: docs/modules/HWISTOCK-MOD-009_operational-automated-trading-program.md
owner_rebaseline_evidence_ref: docs/evidence/RUN-20260605_owner-runtime-architecture-10m-trade-document-rebaseline.md
contract_hardening_unit_ref: docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md
contract_hardening_evidence_ref: docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md
post_pro_corrective_go_check_evidence_ref: docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md
followup_correction_refs:
  - docs/set/READY-SET-CORRECTION-20260606_mode-schedule-ai-loop-followup.md
---

# Ready-Set Row Closure Matrix — Operational Automated Trading Program

## 1. Queue Rows

| order | unit_id | unit_ref | qa_ref | row_state | allowed_first_go_scope | hard_exclusions |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | HWISTOCK-UNIT-011 | `docs/units/HWISTOCK-UNIT-011_operational-runtime-supervisor.md` | `docs/qa/QA-HWISTOCK-UNIT-011_operational-runtime-supervisor.md` | go_check_passed_post_pro_runtime_entrypoint | User systemd install/sync, local-only service startup, runtime timer health, restart/status evidence, and no-reload entrypoint hardening. Evidence: `docs/evidence/RUN-20260605_unit-011-runtime-start-go.md`, `docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md`. | KIS broker adapter cash order submission, unapproved endpoints, public bind, secret printing. |
| 2 | HWISTOCK-UNIT-016 | `docs/units/HWISTOCK-UNIT-016_runtime-contract-hardening.md` | `docs/qa/QA-HWISTOCK-UNIT-016_runtime-contract-hardening.md` | set_complete | Runtime data/execution contracts, schema catalog, valid/invalid fixtures, and validator are defined and pass local validation. Evidence: `docs/evidence/RUN-20260605_unit-016-runtime-contract-hardening-set.md`. | Broker calls, AI provider calls, unapproved endpoints, credential reads/prints, strategy-risk parameter changes. |
| 3 | HWISTOCK-UNIT-012 | `docs/units/HWISTOCK-UNIT-012_ai-analysis-runtime.md` | `docs/qa/QA-HWISTOCK-UNIT-012_ai-analysis-runtime.md` | go_check_passed_local_no_network_provider_smoke_blocked | DeepSeek Pro hourly aggregate/market-regime artifact, `07:15 KST` morning watchlist requirement via local Codex CLI browser-use, DeepSeek Flash 10-minute `flash_trade_document/v0`, deterministic candidate-universe consumption, action schema/redaction/no-order validation, and paper/mock `09:00-15:00 KST` decision-window enforcement. Evidence: `docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`. | Broker calls, AI direct orders, unapproved cost caps, invented off-universe tickers, credentials in prompts, SSH browser-use, ChatGPT browser side effects unless separately scoped, paper/mock new entries after `15:00 KST`; provider network smoke remains blocked. |
| 4 | HWISTOCK-UNIT-013 | `docs/units/HWISTOCK-UNIT-013_signal-to-intent-pipeline.md` | `docs/qa/QA-HWISTOCK-UNIT-013_signal-to-intent-pipeline.md` | go_check_passed_local_no_network_kis_paper_read_blocked | NAVER/OpenDART source grounding, mode-gated KIS market-data collector, Flash trade-document action consumption, morning-watchlist refs, source/KIS-market/portfolio/order refs, freshness/session confirmation, dynamic 75% exposure cap, and deterministic risk-gated `paper_order_intent/v0` queue. Evidence: `docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`. | KIS order calls, KIS signal endpoints outside the mode-enabled allowlist, paper/mock entry intents at or after `15:00 KST`, news-only orders, AI-only orders, fake broker state, unapproved scraping, SOR broker-facing collection; KIS broker adapter-read network smoke remains blocked. |
| 5 | HWISTOCK-UNIT-014 | `docs/units/HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md` | `docs/qa/QA-HWISTOCK-UNIT-014_kis-broker-order-execution-reconciliation.md` | go_check_passed_local_no_network_order_smoke_blocked | KIS KRX broker order preflight, paper/mock `09:00-15:00 KST` broker-submit window, dynamic 75% exposure cap, superseded WAIT_BUY cancellation planning, realtime stop/take-profit/trailing exits, idempotency, ambiguous-submit guard, no-fake-broker evidence. Evidence: `docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`. | Unapproved endpoints, paper/mock broker submit at or after `15:00 KST`, NXT/SOR broker-adapter routing, raw secrets, duplicate orders, fake PnL; order/reconciliation side-effect smoke remains blocked. |
| 6 | HWISTOCK-UNIT-015 | `docs/units/HWISTOCK-UNIT-015_operator-console-observation-prove.md` | `docs/qa/QA-HWISTOCK-UNIT-015_operator-console-observation-prove.md` | go_check_passed_readiness_truth_tunnel_smoke_browser_visual_prove_blocked | Read-only dashboard/API status, operator-window observation reports, frontend normalization tests, readiness flag separation, and prominent false-readiness truth surface. Evidence: `docs/evidence/RUN-20260605_operational-go-check-units-012-015.md`, `docs/evidence/RUN-20260605_post-pro-corrective-go-check-unit-011-015.md`. | Buy/sell controls, adapter toggle, public bind, secret/raw-account display, false operation readiness; browser visual Prove remains blocked. |

## 1.1 Post-Pro Reinforcement Rows

The same queue remains current. The following corrective gaps must be folded
into the listed rows before any future operation readiness claim:

| unit_id | reinforcement |
| --- | --- |
| HWISTOCK-UNIT-011 | Done in `RUN-20260605_post-pro-corrective-go-check-unit-011-015`: `backend/run.py` defaults to no reload and service template tests assert no reload flag. |
| HWISTOCK-UNIT-015 | Done in `RUN-20260605_post-pro-corrective-go-check-unit-011-015`: operator API emits `readinessTruth` and dashboard renders a large not-ready banner. |
| HWISTOCK-UNIT-012 | Reconcile actual Pro/Flash timers, `07:15 KST` local Codex CLI browser-use morning watchlist dependency, paper/mock `09:00-15:00 KST` decision window, and provider-backed versus safe-block artifacts before citing AI runtime readiness. SSH browser-use is forbidden. |
| HWISTOCK-UNIT-013 | Prove source/calendar/KIS mode-gated market-data freshness, morning-watchlist refs, paper/mock `15:00 KST` entry-intent cutoff, and dynamic 75% exposure cap without order submission before treating intents as broker-order eligible. |
| HWISTOCK-UNIT-014 | Run KRX broker order/reconciliation only under explicit approval, paper/mock `09:00-15:00 KST` order window, adapter-only guard, dynamic 75% exposure cap, and idempotency/reconciliation evidence. |

## 2. Scope Result

Selected queue scope: `operational_contract_hardened_go_check_queue`.

The narrower UNIT-010 Ready-Set remains useful as a local no-network foundation
but is not enough to prove an actually running stock-trading program.

The clarified operational architecture and UNIT-016 runtime contracts are
accepted for Go-Check entry. UNIT-012 through UNIT-015 now have local
no-network Go-Check evidence. This row closure still does not prove operation
readiness because provider, KIS broker adapter-read/order, browser/tunnel, and operator
observation-window side-effect rows remain blocked until explicitly scoped.

## 3. Row Closure Rule

Rows may move from `ready_for_go_check` only after Go writes fresh evidence and
Check reviews it. A row with only docs, only code, only local unit tests, or only
trace sync is not closed.
