---
schema_version: hwi.ready-set-share-manifest/v0
stage: ready-set
status: sent_completed_for_foundation_only
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
created_at: 2026-06-02
updated_at: 2026-06-03
external_review_evidence_ref: docs/evidence/RUN-20260603_gpt-pro-foundation-ready-set-review.md
review_findings_intake_ref: docs/set/READY-SET-REVIEW-FINDINGS-INTAKE-20260603_foundation.md
---

# External Review Share Manifest

## 1. Purpose

This manifest defines the sanitized document set that was shared with the
current final external reviewer after explicit user approval.

It does not authorize any future send. Future external review sends require a
fresh candidate rebuild, exact-match check, and secret scan.

## 2. Include List

Share only these project planning artifacts:

- `AGENTS.md`
- `docs/index.md`
- `docs/profiles/PROFILE-HWISTOCK.md`
- `docs/modules/*.md`
- `docs/units/*.md`
- `docs/qa/*.md`
- `docs/sources/*.md`
- `docs/set/*.md`
- `docs/evidence/*.md`

## 3. Exclude List

Do not share:

- `env.sh`
- `/home/hwi/.config/hwistock/*`
- any `.env`, `*.env`, or shell file containing secrets
- `apiRefer/*.xlsx`
- broker app keys, app secrets, account ids, tokens, approval keys, or access
  tokens
- DeepSeek/OpenAI/AI provider API keys
- real balances, real account identifiers, or unredacted private records
- full copyrighted article bodies
- generated runtime data under future `data/` directories
- implementation code, if later created, unless a future review scope explicitly
  includes it

## 4. Current Local Safety Check

Local checks performed for this manifest:

- Current docs are Markdown planning/evidence artifacts.
- No broker or AI network call was made.
- External review was sent only for the sanitized 80-file Markdown planning
  bundle after checks passed.
- Secret-pattern checks are required immediately before any actual send.

## 5. Required Pre-Send Checklist

Before sending any external review bundle:

1. Rebuild the outgoing file list from the include list.
2. Compare the rebuilt outgoing list against the current pre-send dry-run file
   list and require exact match: no missing or extra Markdown planning/evidence
   files.
3. Confirm the exclude list is absent from the outgoing bundle.
4. Run a fresh secret-pattern scan over the outgoing bundle.
5. Verify the completion report still names this manifest.
6. Verify the outgoing bundle includes the latest completion report, row closure
   matrix, completion audit, gate evidence matrix, rule preset applicability
   matrix, strategy packet, dashboard design packet, foundation queue proposal,
   approval actions and owner decision receipt checklist, owner decision brief,
   owner decision receipt template, review findings intake template, Go
   preflight checklist, root/VCS/env scan evidence, external review pre-send
   dry-run evidence, current Ready-Set state snapshot, and external review
   prompt.
7. Record pre-send evidence under `docs/evidence/`. Current dry-run evidence:
   `docs/evidence/RUN-20260602_external-review-presend-dry-run.md`.

Suggested local secret scan command:

```bash
(printf '%s\n' AGENTS.md docs/index.md docs/profiles/PROFILE-HWISTOCK.md; find docs/modules docs/units docs/qa docs/sources docs/set docs/evidence -maxdepth 1 -name '*.md' | sort) | sort > /tmp/hwistock-actual-candidates.txt
matches=$(xargs -a /tmp/hwistock-actual-candidates.txt rg -n '(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|Bearer[[:space:]]+[A-Za-z0-9._~+/=-]{20,}|DEEPSEEK_API_KEY[[:space:]]*=|OPENAI_API_KEY[[:space:]]*=|APP_KEY[[:space:]]*=|APP_SECRET[[:space:]]*=|KIS_APP_KEY[[:space:]]*=|KIS_APP_SECRET[[:space:]]*=|appkey[[:space:]]*=|appsecret[[:space:]]*=|approval_key[[:space:]]*[:=]|access_token[[:space:]]*[:=]|CANO[[:space:]]*=|ACNT_PRDT_CD[[:space:]]*=' || true)
if [ -z "$matches" ]; then echo "candidate-secret-scan: no_matches"; else printf '%s\n' "$matches"; exit 1; fi
```

Do not write known secret literal prefixes into this manifest. If a local
deny-list of leaked or project-specific markers is needed, pass it from a
temporary file or environment variable immediately before the actual send.

## 6. Review Scope Reminder

The external reviewer should review readiness and risks only. They should not
request or receive credentials, env files, live account data, or broker network
evidence.
