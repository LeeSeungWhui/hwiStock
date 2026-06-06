# RUN-20260606 Docs-Code Demo Route Quarantine Go-Check

Date: 2026-06-06 KST
Stage: go-check
Profile: `docs/profiles/PROFILE-HWISTOCK.md`

## 1. Scope

This run followed up on the question of whether code still needed changes after
the current `docs/` authority cleanup.

The checked docs contract requires MyWebTemplate-derived sample, public, and
generic demo surfaces to be removed, quarantined, disabled, renamed, or
replaced before they can be treated as current hwiStock runtime surfaces.

## 2. Finding

Code inspection found that backend router loading still allowed local
configuration to re-enable the imported MyWebTemplate demo routers:

- `backend/router/SampleRouter.py`
- `backend/router/TransactionRouter.py`

The default branch of the server already skipped those routers, but the
configurable escape hatch was not aligned with the current hwiStock docs
contract. The old backend test `test_sample_public_api.py` also asserted that
sample CRUD APIs should be publicly available, which contradicted the
quarantine contract.

## 3. Changes

- `backend/server.py`
  - Removes the config-based demo-router re-enable path.
  - Always excludes `SampleRouter` and `TransactionRouter` from FastAPI router
    registration.
- `backend/tests/test_demo_route_quarantine.py`
  - Replaces the previous public sample CRUD test with a route-registration
    quarantine assertion.
- `backend/tests/conftest.py`
  - Removes the former sample public API test from PostgreSQL integration-only
    classification because the quarantine assertion does not require DB
    startup.
- `backend/tests/test_transaction.py`
  - Keeps transaction rollback coverage at the service/transaction layer.
  - Adds explicit assertions that the old transaction demo HTTP routes are not
    registered.
- `backend/tests/test_tx_logging.py`
  - Keeps transaction logging coverage by setting request context directly and
    exercising the transaction service without the demo HTTP route.

## 4. Validation

Commands were executed with `source ./env.sh` where Python/Node toolchains were
used.

| Check | Result | Evidence |
| --- | --- | --- |
| Backend focused pytest | PASS | `python3 -m pytest backend/tests/test_demo_route_quarantine.py backend/tests/test_transaction.py backend/tests/test_tx_logging.py backend/tests/test_hwistock_runner.py backend/tests/test_operational_go_check_pipeline.py -q` -> `56 passed` |
| Frontend focused vitest | PASS | `pnpm --dir frontend-web exec vitest run __tests__/middleware.test.jsx __tests__/tasksQueryState.test.jsx` -> `2 passed`, `28 passed` |
| Rule gate | PASS | `python /home/hwi/.codex/skills/hwi-rule-gate/scripts/rule_gate.py /data/workspace/My/hwiStock --profile docs/profiles/PROFILE-HWISTOCK.md --changed --fail-on-warn` -> `error=0 warning=0 info=0` |
| Whitespace diff check | PASS | `git diff --check` -> no output |
| Residual backend sample-public expectation scan | PASS | Search found only quarantine assertions for `/api/v1/sample` and `/api/v1/transaction/test/*` in backend tests. |

## 5. Boundaries

- No broker/KIS/AI provider network call was made.
- No service restart, deployment, browser side effect, or order submission was
  performed.
- Physical imported sample frontend route files still remain in the tree, but
  current frontend middleware tests verify that `/sample`, `/component`,
  `/portfolio`, `/signup`, and `/forgot-password` are quarantined away from the
  public/operator surface.
