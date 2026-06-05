---
schema_version: hwi.run-evidence/v0
id: RUN-20260604-unit-003-go-check
stage: go-check
unit_id: HWISTOCK-UNIT-003
status: superseded_by_mywebtemplate_code_import
current_authority: false
superseded_by_rebaseline_ref: docs/evidence/RUN-20260604_ready-set-rebaseline-after-mywebtemplate-import.md
superseded_reason: MyWebTemplate backend/frontend-web import removed the validated UNIT-003 implementation files from the current tree.
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
unit_ref: docs/units/HWISTOCK-UNIT-003_market-intelligence-ingestion.md
module_refs:
  - docs/modules/HWISTOCK-MOD-002_market-intelligence-ingestion.md
qa_scenario_ref: docs/qa/QA-HWISTOCK-UNIT-003_market-intelligence-ingestion.md
source_registry_ref: docs/sources/HWISTOCK-SOURCE-REGISTRY.md
preflight_ref: docs/evidence/RUN-20260604_unit-003-go-preflight.md
created_at: 2026-06-04
environment: docs_only
route_class: implementation_worker
adapter: multi_agent_v1.worker
orchestration_gate_id: DG-HWISTOCK-UNIT-003-GO-20260604-001
post_check_remediation_gate_id: DG-HWISTOCK-UNIT-003-RULEGATE-FIX-20260604-001
worker_output_acceptance: local_takeover_after_quarantined_worker_outputs
final_fastapi_rule_gate_status: pass
final_db_rule_gate_status: pass
---

# UNIT-003 Go-Check Evidence

> Superseded notice: this evidence is historical after the 2026-06-04
> MyWebTemplate backend/frontend-web code import. It no longer proves the
> current tree because the referenced UNIT-003 implementation files are missing.

## 1. Verdict

PASS for the foundation-only Go implementation/check scope.

`HWISTOCK-UNIT-003` now has a stdlib-only, fixture/config-first market
intelligence ingestion skeleton. This is not Prove evidence and does not
authorize network source collection, broker/KIS calls, AI provider calls, order
placement, credential storage, runtime scheduler execution, or runtime artifact
writes.

## 2. Route

- Stage: Go for HWISTOCK-UNIT-003, producing Go evidence for orchestrator Check.
- Route class: implementation_worker
- Adapter: multi_agent_v1.worker
- Gate id: DG-HWISTOCK-UNIT-003-GO-20260604-001
- Supersession: the earlier preflight `no_delegation` line is superseded by the
  explicit implementation-worker contract used for this Go pass.

## 3. Implemented Scope

- `backend/lib/market_intelligence.py`
  - deterministic foundation source registry/config model;
  - normalized event dataclass and validation helpers;
  - required event fields for source ids, timestamps, symbol/corp code, market,
    title, URL, dedupe key, storage policy, hash, and candidate eligibility;
  - deterministic hash/id/dedupe helpers;
  - duplicate linking helpers;
  - blocked-source guard for conditional, deferred, forbidden, and unknown
    source ids.
- `backend/service/market_intelligence_ingestion.py`
  - in-memory fixture-row ingestion only;
  - returned events, summary, and health dictionaries only;
  - source counts, duplicate count, disabled network sources, blocked source ids,
    failures, backlog, last fetch timestamps, and retention notes.
- `backend/tests/test_market_intelligence_ingestion.py`
  - focused unittest smoke coverage for QA-001 through QA-011 where practical.

## 4. Boundary Evidence

- No implementation path reads environment variables or credential files.
- No implementation path imports network client modules.
- No implementation path imports broker, KIS, trading, or order-routing modules.
- Network OpenDART, Naver, KRX/KIND, KIS/broker, general HTML scraping, and
  unofficial API sources remain disabled in foundation mode.
- Approved first-Go sources are fixture-only; no network client exists.
- Ingestion writes no runtime artifacts under `data/`.

## 5. QA Row Coverage

| row_id | result | evidence |
| --- | --- | --- |
| QA-001 | pass | Source registry config entries expose status, method, credential policy, storage policy, rate, terms, and retention fields. |
| QA-002 | pass | Import smoke confirms no broker/order/trading routing imports. |
| QA-003 | pass | Source policy notes and rate/terms text are present in the implementation config. |
| QA-004 | pass | Duplicate disclosure fixtures link deterministically by dedupe key. |
| QA-005 | pass | Health output exposes source counts, duplicate count, failures, backlog, disabled network sources, blocked source ids, and last fetch timestamps. |
| QA-006 | pass | Summary dictionary exposes source counts, duplicate count, failures, disabled network sources, and retention notes without writing runtime evidence files. |
| QA-007 | pass | Market-data context fields include venue, interval, OHLCV, volume, and latency status while network sources remain conditional/deferred. |
| QA-008 | pass | General HTML scraping and unofficial finance APIs are blocked in foundation mode. |
| QA-009 | pass | KIS/broker market/realtime/news source remains deferred and cannot ingest. |
| QA-010 | pass | Normalized event schema includes all required UNIT-003 fields and validation catches missing fields. |
| QA-011 | pass | Foundation fixture smoke succeeds without credentials, network imports, or network source calls. |

## 6. Validation

Required validation:

```text
source ./env.sh >/dev/null 2>&1 || true; python -m unittest backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract
```

Result:

```text
Ran 16 tests in 0.013s
OK
```

Required compile validation:

```text
source ./env.sh >/dev/null 2>&1 || true; python -m py_compile $(find backend -name '*.py' -print)
```

Result:

```text
PASS
```

Original optional rule-gate:

```text
source ./env.sh >/dev/null 2>&1 || true; python3 "$CODEX_HOME/skills/hwi-rule-gate/scripts/rule_gate.py" /data/workspace/My/hwiStock --all --preset fastapi-backend-rule-preset --fail-on-warn
```

Result:

```text
BLOCKED: CODEX_HOME was unset in this worker runtime, so the exact command tried
to open /skills/hwi-rule-gate/scripts/rule_gate.py and failed.
```

Follow-up availability check with the default Codex home path found the script
but the adapter blocked before scanning files because it expected
`docs/hwi-work-profile.md`:

```text
Status: blocked
Profile: unknown-profile
Scanned files: 0
Blocked / Skipped: profile not found: /data/workspace/My/hwiStock/docs/hwi-work-profile.md
```

This optional gate is not counted as PASS.

Post-check remediation and final rule-gate:

The orchestrator later re-ran the profile-aware HWI rule-gate and found three
backend preset errors in `backend/service/market_intelligence_ingestion.py`:
two `FASTAPI-BE-006` helper-name findings and one `FASTAPI-BE-039` evasive local
name finding. The remediation was routed through
`DG-HWISTOCK-UNIT-003-RULEGATE-FIX-20260604-001` as a patch-only
`cursor-sdk-local` implementation worker. The worker changed only
`backend/service/market_intelligence_ingestion.py` and renamed helper/local
symbols without changing public schema keys or test expectations.

Worker acceptance note:

- Cursor worker route/model: `cursor-sdk-local` / `composer-2.5`.
- Cursor wrapper status: `incomplete_worker_result`, because assistant stream
  output contained prose before `WORKER_RESULT`.
- Codex multi-agent DeepSeek review fallback: not launch-verified in this
  ChatGPT-account session (`deepseek-v4-pro` unsupported).
- MoonBridge DeepSeek read-only review fallback: ran against a copied
  `/tmp/hwistock-review-bundle-*` file bundle and reported no P0/P1 findings,
  but its output also contained prose before the sentinel, so it is treated as
  advisory/quarantined rather than accepted worker output.
- Final acceptance path: documented orchestrator local takeover after alternate
  worker routes were attempted, using local diff review plus the validation
  below as the authoritative closure evidence.

Final validation after remediation:

```text
source ./env.sh && python -m unittest backend.tests.test_market_intelligence_ingestion backend.tests.test_storage_contract
```

```text
Ran 16 tests in 0.013s
OK
```

```text
source ./env.sh && python -m py_compile backend/service/market_intelligence_ingestion.py
```

```text
PASS
```

```text
source ./env.sh && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile /data/workspace/My/hwiStock/docs/profiles/PROFILE-HWISTOCK.md --preset fastapi-backend-rule-preset --all --fail-on-warn
```

```text
Status: pass
Findings: error=0 warning=0 info=0
```

```text
source ./env.sh && python3 /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile /data/workspace/My/hwiStock/docs/profiles/PROFILE-HWISTOCK.md --preset db-naming-rule-preset --all --fail-on-warn
```

```text
Status: pass
Findings: error=0 warning=0 info=0
```

## 7. Remaining Risks / Handoff Notes

- This is a skeleton foundation pass only. Operation source fetchers, schedulers,
  storage persistence, API routes, and Prove evidence remain future work.
- The earlier optional worker-side hwi-rule-gate blocker is superseded by the
  final profile-aware orchestrator rule-gate pass recorded above.
- No source registry policy was changed; the implementation mirrors the current
  source status contract.
