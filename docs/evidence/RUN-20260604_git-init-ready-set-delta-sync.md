---
schema_version: hwi.evidence/v0
id: RUN-20260604-git-init-ready-set-delta-sync
stage: go-preflight
status: pass
project_root: /data/workspace/My/hwiStock
created_at: 2026-06-04
updated_at: 2026-06-04
environment: local_shell
selected_action: delta_sync_plus_git_init
owner_decision: Delta sync + Git init
git_initialized: true
git_branch: main
commit_created: false
env_files_gitignored: true
secret_values_printed: false
---

# Git Init And Ready-Set Delta Sync Evidence

## 1. Owner Decision

The owner selected `Delta sync + Git init (Recommended)` after the KIS
paper/mock REST and websocket smoke passed.

The owner also clarified that `.env` files must be ignored by Git.

## 2. Git Initialization

Observed result:

| check | result |
| --- | --- |
| `git rev-parse --is-inside-work-tree` | `true` |
| active branch | `main` |
| commit created | no |
| `.gitignore` created | yes |

This resolves the previous PF-13 pre-code-edit blocker by establishing a Git
working tree before product code edits.

## 3. Ignore Policy

The root `.gitignore` now ignores:

- `.env`
- `.env.*`
- `*.env`
- runtime/cache/output/log folders
- common Python/Node/tool caches

It explicitly allows `.env.example` and `*.env.example` so safe templates can be
versioned later without committing real secrets.

Verification used `git check-ignore` against representative paths:

| path | result |
| --- | --- |
| `.env` | ignored |
| `.env.local` | ignored |
| `secrets.env` | ignored |
| `cache/projects.json` | ignored |
| `data/runtime.json` | ignored |
| `logs/run.log` | ignored |

## 4. KIS Smoke Delta

The previous Ready-Set baseline denied all KIS/broker network activity by
default. That remains the default for ordinary Go implementation rows, but a
bounded owner-approved KIS paper/mock smoke was completed and documented in:

- `docs/evidence/RUN-20260604_kis-paper-mock-api-smoke.md`
- `docs/set/KIS-PAPER-MOCK-API-SMOKE-MATRIX-20260604_hwistock.md`

The completed smoke does not authorize live API calls, real accounts, future
unscoped broker adapter execution, production operation, or additional paper
orders outside an explicitly scoped future unit.

## 5. Safety Notes

- No secret values were printed or written to docs.
- No commit was created.
- `/home/hwi/.config/hwistock/*.env` remains outside the repository.
- Future commits must keep Korean commit messages unless the owner specifies
  otherwise.
