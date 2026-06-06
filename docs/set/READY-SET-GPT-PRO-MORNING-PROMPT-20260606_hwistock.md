---
schema_version: hwi.prompt-contract/v0
stage: ready-set
status: set
project_root: /data/workspace/My/hwiStock
docs_base: docs
profile_id: PROFILE-HWISTOCK
prompt_id: gpt_pro_morning_watchlist_0715
approved_route: codex_cli_local_browser_use
forbidden_routes:
  - ssh_browser_use
  - reverse_socket_chrome_bridge
  - remote_chrome
  - hwiServer_side_browser_automation
output_schema: morning_watchlist/v0
updated_at: 2026-06-06
---

# GPT Pro Morning Watchlist Prompt Contract

## 1. Route

This prompt is sent only by:

```text
local Codex CLI -> local browser-use -> user's logged-in local Chrome -> ChatGPT Pro
```

Do not send this prompt through SSH browser-use, hwiServer-side browser
automation, reverse Unix socket Chrome bridges, remote Chrome, or headless
browser automation.

If local Codex CLI or local browser-use is unavailable, the job must write a
named safe-block or use the DeepSeek-only fallback. It must not silently switch
routes.

## 2. Prompt Template

```text
You are an external morning reviewer for hwiStock, a Korea domestic stock
paper/mock trading experiment. You are advisory only.

Task:
Review the attached/supplied sanitized morning input bundle and produce a
morning_watchlist/v0-compatible response for the first Flash decision bucket.

Hard constraints:
- Do not request or infer broker credentials, account numbers, tokens, secrets,
  raw private account data, or unredacted local paths.
- Do not place orders, call broker APIs, change risk settings, or claim profit.
- Do not produce executable broker-order instructions.
- Use only the supplied source refs, Pro refs, market-data refs, and candidate
  universe refs.
- If evidence is weak or missing, mark the item watch_only or reject.
- If the bundle is insufficient for ranking, return a NO_TRADE-style safe-block
  with missing_data reasons.

Investment mode:
- mode: {{investment_mode}}
- trading_date_kst: {{trading_date_kst}}
- first_flash_bucket_kst: {{first_flash_bucket_kst}}
- paper/mock KRX new-entry decision window: 09:00-15:00 KST
- 15:00-15:30 KST is close/market-data/reconciliation context only.

Input bundle summary:
{{morning_watchlist_input_bundle_summary}}

Required output:
Return one JSON object only. No Markdown prose outside JSON.

Schema:
{
  "schema_version": "morning_watchlist/v0",
  "artifact_type": "morning_watchlist",
  "trading_date": "{{trading_date_kst}}",
  "investment_mode": "{{investment_mode}}",
  "reviewer": "chatgpt_pro",
  "route": "codex_cli_local_browser_use",
  "valid_for_first_flash_bucket_kst": "{{first_flash_bucket_kst}}",
  "source_refs": [],
  "pro_refs": [],
  "market_data_refs": [],
  "candidate_universe_refs": [],
  "items": [
    {
      "rank": 1,
      "ticker": "000000",
      "name": "string",
      "stance": "watch_only | eligible_for_flash_review | reject",
      "thesis": "string",
      "source_refs": [],
      "pro_refs": [],
      "market_data_refs": [],
      "invalidation_conditions": [],
      "risk_notes": [],
      "missing_data": []
    }
  ],
  "global_risk_notes": [],
  "no_trade_reasons": [],
  "forbidden_actions_acknowledged": true
}

Ranking rules:
- Prefer source-grounded, fresh, liquid, and KIS-market-confirmed candidates.
- Penalize candidates with missing source refs, stale market refs, ambiguous
  ticker mapping, existing portfolio/order conflicts, or weak evidence.
- Max items: {{max_items}}.
- If no candidate is suitable, use an empty items array and fill no_trade_reasons.
```

## 3. Required Local Validation

Before storing GPT Pro output as `morning_watchlist/v0`, the Codex CLI wrapper
or downstream validator must check:

- JSON parse succeeds;
- `route = codex_cli_local_browser_use`;
- `forbidden_actions_acknowledged = true`;
- no credential/account/raw secret text is present;
- every item has source refs or is marked `watch_only` / `reject`;
- no executable order fields are present;
- max item count is respected;
- output is finalized before the first Flash bucket or becomes invalid for that
  bucket.
