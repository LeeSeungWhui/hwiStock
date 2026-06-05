---
schema_version: hwi.evidence/v0
id: RUN-20260604-unit-009-go-preflight-rebaseline
stage: go-preflight
status: pass
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
current_authority: true
supersedes_preflight_ref: docs/evidence/RUN-20260604_unit-009-go-preflight.md
historical_go_check_ref: docs/evidence/RUN-20260604_unit-009-go-check.md
orchestration_gate_id: DG-HWISTOCK-UNIT-009-GO-GPT54-20260604-001
selected_unit_id: HWISTOCK-UNIT-009
selected_queue_scope: full_queue_skeleton_adapter_safe
completion_report_ref: docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md
row_closure_ref: docs/set/READY-SET-ROW-CLOSURE-20260604_rebaseline_hwistock.md
go_preflight_checklist_ref: docs/set/READY-SET-GO-PREFLIGHT-CHECKLIST-20260604_rebaseline_hwistock.md
unit_ref: docs/units/HWISTOCK-UNIT-009_kis-api-portal-verification.md
qa_ref: docs/qa/QA-HWISTOCK-UNIT-009_kis-api-portal-verification.md
capability_matrix_ref: docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md
kis_smoke_evidence_ref: docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md
rebaseline_evidence_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
ready_set_reissue_evidence_ref: docs/evidence/RUN-20260604_ready-set-reissue-after-mywebtemplate-owner-decision.md
work_class: docs_only
broker_network_calls_made: false
kis_token_calls_made: false
kis_order_calls_made: false
credential_values_printed: false
---

# UNIT-009 Go Preflight — Rebaseline

## 1. Selected Row Scope

| field | value |
| --- | --- |
| unit_id | `HWISTOCK-UNIT-009` |
| queue_order | 4 |
| observed_row_state_before_closure | `ready_for_go_check` |
| allowed_first_go_scope | current-authority local docs/capability-matrix refinement only |
| hard_exclusions | KIS token, account, balance, quote, realtime, order, modify/cancel, WebSocket, broker network, credential, or MyWebTemplate-generated reference-code action |
| module_refs | `HWISTOCK-MOD-001`, `HWISTOCK-MOD-005` |
| profile_ref | `PROFILE-HWISTOCK` |
| expected_evidence | `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md` |
| implementation_route | patch-only docs sync in current project root |

This preflight is the current-authority rebaseline replacement for
`docs/evidence/RUN-20260604_unit-009-go-preflight.md`. It authorizes only docs-only
updates to the UNIT-009 unit/QA docs, capability-matrix references, row-closure
status, and docs index links. It does not authorize new KIS/broker/API/network calls.

## 2. Ready-Set Preflight Table (PF-01..PF-14)

| check_id | requirement | result | notes |
| --- | --- | --- | --- |
| PF-01 | current completion report exists | pass | `docs/set/READY-SET-COMPLETION-20260604_rebaseline_hwistock.md` |
| PF-02 | `implementation_ready: true` for current rebaseline scope | pass | skeleton/adapter-safe rebaseline queue only; operational trading readiness remains false |
| PF-03 | `HWISTOCK-UNIT-009` appears in current Go queue | pass | row-closure matrix order 4 |
| PF-04 | current row state is `ready_for_go_check` before this closure | pass | observed in current row-closure matrix |
| PF-05 | unit, QA, module, and profile refs exist | pass | UNIT-009, QA-UNIT-009, MOD-001, MOD-005, PROFILE-HWISTOCK |
| PF-06 | local-only narrowed approval remains valid | pass | current action is docs-only and does not expand broker/KIS, AI, credential, dashboard, or operational scope |
| PF-07 | no open P0/P1 review blocker for this docs-only action | pass | historical review remains supporting context only; no new expansion boundary crossed |
| PF-08 | strategy row approval is not required for this docs-only row | pass | no broker-backed strategy/order behavior is introduced |
| PF-09 | dashboard design review is not required for this docs-only row | pass | no dashboard/public UI behavior is changed |
| PF-10 | broker/KIS/AI/order/credential approvals are explicit for selected action | pass | selected action is no-network/no-order/no-credential docs sync only |
| PF-11 | owner-decision-based rebaseline authority is recorded | pass | current rebaseline/reissue evidence and row-closure docs are present |
| PF-12 | narrowed foundation-only conditional row logic is not applicable | not_applicable | current queue is the full skeleton/adapter-safe rebaseline queue |
| PF-13 | VCS baseline was already resolved before this docs update | pass | current authority inherits the 2026-06-04 git-init delta-sync baseline through Ready-Set docs |
| PF-14 | MyWebTemplate quarantine requirement is preserved for the selected scope | pass | UNIT-009 closure stays docs-only and does not authorize generated template reference code or runtime behavior |

Overall preflight verdict: **PASS** for the current-authority UNIT-009 docs-only
rebaseline Go-Check sync.

## 3. Secret And Data Safety

| check | result |
| --- | --- |
| no `env.sh` content in evidence | pass |
| no `/home/hwi/.config/hwistock/*.env` content in evidence | pass |
| no broker secrets, tokens, account values, or raw responses copied into docs | pass |
| bounded KIS smoke is reused only as sanitized historical support | pass |

## 4. Network And Trading Boundary

| boundary | required_state | result |
| --- | --- | --- |
| new KIS token issuance | denied for this row | pass |
| KIS account/balance/quote/realtime/order/modify/cancel/WebSocket | denied for this row | pass |
| adapter or account-affecting order placement | denied for this row | pass |
| AI provider network | denied | pass |
| credential storage/commits | denied | pass |
| public/LAN dashboard exposure | denied | pass |
| fake broker fills/balances/PnL | denied | pass |
| expected-profit claims | denied | pass |

The bounded smoke in `docs/evidence/RUN-20260604_kis-broker-adapter-api-smoke.md`
remains historical supporting evidence for already-proven KRX adapter paths only. It does
not expand the selected UNIT-009 docs row into broker-network authorization.

## 5. Focused QA Mapping

| qa_row | focused_check | preflight_expectation |
| --- | --- | --- |
| QA-001 | official endpoint families remain enumerated | pass via existing set evidence and current unit text |
| QA-002 | adapter-mode separation and KRX adapter constraints remain documented | pass with partial boundary; historical bounded smoke may be cited only as sanitized support |
| QA-003 | KRX/NXT/SOR fields remain documented with NXT/SOR still `live_verify` | pass with partial boundary |
| QA-004 | no credential use or broker API call occurs in this rebaseline sync | pass |

## 6. Handoff

Proceed to `docs/evidence/RUN-20260604_unit-009-go-check-rebaseline.md` for the
current-authority docs-only Go-Check closure.
