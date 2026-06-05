---
schema_version: hwi.run-evidence/v0
id: RUN-20260605-commit-prep-scope-audit
stage: commit-prep
status: pass_with_caveats
current_authority: true
project_root: /data/workspace/My/hwiStock
profile_ref: docs/profiles/PROFILE-HWISTOCK.md
supporting_refs:
  - docs/evidence/RUN-20260605_browser-ui-reprove-login-api500.md
  - docs/evidence/RUN-20260605_unit-007-go-check-rebaseline.md
  - docs/evidence/RUN-20260605_port-tunnel-5000-5001-sync.md
  - docs/evidence/RUN-20260605_local-server-smoke-5000-5001.md
  - docs/evidence/RUN-20260605_hwibuntu-tunnel-smoke-5000-5001.md
created_at: 2026-06-05
environment: hwiServer
route_class: evidence_analyst_worker_then_local_audit
worker_route: cursor-sdk-local
worker_model: composer-2.5
staged: false
committed: false
---

# Commit Prep Scope Audit

## 1. Verdict

PASS with caveats for commit preparation.

The working tree is structurally ready to stage after the local ignore cleanup
below. No staging or commit was performed in this run.

## 2. Delegation / Worker Audit

The commit-prep audit used a read-only Cursor SDK worker, then local
orchestrator verification.

Worker route:

```text
route_class: evidence_analyst_worker
adapter: cursor-sdk-local
model: composer-2.5
reasoning: medium
workspace: /data/workspace/My/hwiStock direct project cwd
```

Worker attempt history:

| attempt | result | note |
| --- | --- | --- |
| dry-run #1 | quarantined | `MODE: READ_ONLY_AUDIT` is not accepted by the wrapper; no product output used |
| dry-run #2 | accepted | wrapper-compatible `MODE: SCOPED_IMPL` with `ALLOWED_WRITES: none` |
| real run #1 | accepted | `WORKER_RESULT: DONE`, no changed files |

Worker transcript:

```text
/tmp/hwi-worker-hwistock-commit-prep-audit/transcript.log
```

## 3. Cleanup Applied

`.gitignore` was tightened before commit prep:

- added `backend/config.test.ini`;
- added `**/logs/*.err`;
- added `**/logs/*.out`.

Runtime dev log artifacts were removed from the working tree:

- `backend/logs/backend-dev.err`
- `backend/logs/backend-dev.out`
- `frontend-web/logs/frontend-dev.err`
- `frontend-web/logs/frontend-dev.out`

The local `backend/config.test.ini` file still exists on disk but is ignored.
Its contents were not read or printed.

## 4. Local Validation

| check | result |
| --- | --- |
| `git diff --check` | PASS |
| `git add -A --dry-run` | 442 candidate paths |
| suspicious-path scan over dry-run output | PASS; no `config.ini`, `.env`, `.err`, `.out`, `.log`, `node_modules`, `.next`, `__pycache__`, `.pytest_cache`, or `apiRefer` candidate |
| tracked secret-ish path scan | PASS; no tracked `.env`, `config.ini`, `config.test.ini`, `kis-paper.env`, or `apiRefer/` path |
| `git check-ignore -v backend/config.test.ini` | PASS; ignored by root `.gitignore` |
| hwiServer 5000/5001 listeners | none |
| hwibuntu 5000/5001 listeners | none |

Focused application tests were not rerun in this commit-prep step because the
only post-reprove product change was `.gitignore` cleanup and evidence/index
documentation. The current supporting validation remains the UNIT-007 re-Prove
evidence.

## 5. Commit Candidate Bundles

Recommended split if the user wants smaller commits:

1. **Toolchain / local guardrails**
   - `.gitignore`
   - `env.sh`
2. **Imported application baseline**
   - `backend/`
   - `frontend-web/`
   - `ops/`
3. **Ready-Set / Go-Check governance docs**
   - `AGENTS.md`
   - `docs/index.md`
   - `docs/modules/*.md`
   - `docs/units/*.md`
   - `docs/qa/*.md`
   - `docs/profiles/PROFILE-HWISTOCK.md`
   - `docs/sources/HWISTOCK-KIS-API-CAPABILITY-MATRIX.md`
   - updated 2026-06-02 Ready-Set docs demoted from current authority
   - new 2026-06-04 rebaseline Ready-Set docs
4. **Evidence bundle**
   - current rebaseline/go-check/smoke/browser evidence under `docs/evidence/`
   - browser screenshots and JSON summaries under `docs/evidence/assets/`

Recommended practical path for the first baseline commit: a single commit is
acceptable because the repo is still establishing the imported MyWebTemplate
baseline and the docs/evidence are tightly coupled to that baseline. If split,
use the order above.

## 6. Exclude / Do Not Stage

These paths must remain untracked/ignored:

- `.env`, `.env.*`, `*.env`
- `backend/config.ini`
- `frontend-web/config.ini`
- `backend/config.test.ini`
- `/home/hwi/.config/hwistock/*.env`
- `apiRefer/`
- `backend/logs/*.log`
- `**/logs/*.err`
- `**/logs/*.out`
- `frontend-web/node_modules/`
- `frontend-web/.next/`
- Python cache directories such as `__pycache__/` and `.pytest_cache/`

The `git add -A --dry-run` output did not include these excluded path classes
after the cleanup.

## 7. Suggested Korean Commit Message

Single baseline commit:

```text
hwiStock 레디셋 리베이스라인과 UNIT-007 브라우저 검증 반영
```

Suggested body:

```text
- MyWebTemplate 기반 backend/frontend-web/ops 베이스라인을 반영한다.
- Ready-Set rebaseline, Go-Check, smoke, browser re-Prove 증거를 동기화한다.
- UNIT-007 로그인 공개면 잔재와 대시보드 Decimal JSON 500을 수정한다.
- 로컬 config/env/log 파일이 커밋되지 않도록 ignore 범위를 보강한다.
```

## 8. Boundary

This run did not perform:

- git stage;
- git commit;
- git push;
- KIS/broker/API calls;
- order placement;
- account-affecting operation;
- deployment;
- browser/server rerun.
