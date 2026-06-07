#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${HWISTOCK_REPO_ROOT:-/data/workspace/My/hwiStock}"
cd "$REPO_ROOT"

umask 077
export TZ="${TZ:-Asia/Seoul}"

CODEX_BIN="${HWISTOCK_CODEX_BIN:-/home/hwi/.local/bin/codex}"
LOG_ROOT="${HWISTOCK_GPT_LOG_ROOT:-logs/gpt-pro-morning}"
RUN_STAMP="${HWISTOCK_GPT_RUN_STAMP:-$(date +%Y%m%d-%H%M%S)}"
RUN_ID="${HWISTOCK_GPT_RUN_ID:-hwistock-gpt-pro-morning-${RUN_STAMP}}"
DAY="$(date +%F)"
RUN_DIR="${HWISTOCK_GPT_RUN_DIR:-${LOG_ROOT}/${DAY}/${RUN_ID}}"
mkdir -p "$RUN_DIR"
chmod 700 "$RUN_DIR" 2>/dev/null || true

TARGET_TRADE_DATE="${HWISTOCK_GPT_TARGET_TRADE_DATE:-}"
if [[ -z "$TARGET_TRADE_DATE" ]]; then
  TARGET_TRADE_DATE="$(
    python3 - <<'PY'
from datetime import datetime, timedelta, timezone

kst = timezone(timedelta(hours=9))
now = datetime.now(kst)
# The scheduled 07:15 run targets the same KST trading date. Late ad-hoc
# rehearsals default to the following KST date unless the caller overrides it.
target = now.date() if now.hour < 12 else (now + timedelta(days=1)).date()
print(target.isoformat())
PY
  )"
fi

PURPOSE="${HWISTOCK_GPT_PURPOSE:-morning_watchlist_0715_local_browser_use}"
PROMPT_SOURCE="${HWISTOCK_GPT_PROMPT_PATH:-}"
if [[ -z "$PROMPT_SOURCE" ]]; then
  for candidate in \
    "data/ai/${TARGET_TRADE_DATE}/gpt-morning-prompt-latest.txt" \
    "data/prompts/${TARGET_TRADE_DATE}/gpt-morning-watchlist-latest.txt"
  do
    if [[ -f "$candidate" ]]; then
      PROMPT_SOURCE="$candidate"
      break
    fi
  done
fi

START_EPOCH="$(date +%s)"
START_ISO="$(date --iso-8601=seconds)"

CODEX_PROMPT="${RUN_DIR}/codex-prompt.md"
RESPONSE="${RUN_DIR}/response.json"
RAW_RESPONSE="${RUN_DIR}/response.raw.txt"
SUMMARY="${RUN_DIR}/summary.json"
PUBLISH_OUT="${RUN_DIR}/publish.json"
PUBLISH_ERR="${RUN_DIR}/publish.err.log"
CODEX_EVENTS="${RUN_DIR}/codex-events.jsonl"
CODEX_LAST="${RUN_DIR}/codex-last-message.md"
CODEX_STDERR="${RUN_DIR}/codex-stderr.log"
PREFLIGHT_CODEX_EVENTS="${RUN_DIR}/preflight-codex-events.jsonl"
PREFLIGHT_CODEX_LAST="${RUN_DIR}/preflight-codex-last-message.md"
PREFLIGHT_CODEX_STDERR="${RUN_DIR}/preflight-codex-stderr.log"
PREFLIGHT_BROWSER_PROMPT="${RUN_DIR}/preflight-browser-prompt.md"
PREFLIGHT_BROWSER_EVENTS="${RUN_DIR}/preflight-browser-events.jsonl"
PREFLIGHT_BROWSER_LAST="${RUN_DIR}/preflight-browser-last-message.md"
PREFLIGHT_BROWSER_STDERR="${RUN_DIR}/preflight-browser-stderr.log"
SECRET_SCAN_JSON="${RUN_DIR}/prompt-secret-scan.json"

export RUN_ID RUN_DIR TARGET_TRADE_DATE PURPOSE PROMPT_SOURCE START_EPOCH START_ISO
export RESPONSE RAW_RESPONSE SUMMARY PUBLISH_OUT PUBLISH_ERR CODEX_EVENTS CODEX_LAST CODEX_STDERR
export PREFLIGHT_CODEX_EVENTS PREFLIGHT_CODEX_LAST PREFLIGHT_CODEX_STDERR
export PREFLIGHT_BROWSER_PROMPT PREFLIGHT_BROWSER_EVENTS PREFLIGHT_BROWSER_LAST PREFLIGHT_BROWSER_STDERR
export SECRET_SCAN_JSON

publish_safe_block() {
  local reason="$1"
  local safe_purpose="${PURPOSE}_${reason}"
  set +e
  source ./env.sh >/dev/null 2>&1
  python backend/service/ai_analysis_runner.py --once \
    --job publish-morning-watchlist \
    --target-trade-date "$TARGET_TRADE_DATE" \
    --purpose "$safe_purpose" \
    >"$PUBLISH_OUT" 2>"$PUBLISH_ERR"
  local code=$?
  set -e
  return "$code"
}

write_summary() {
  local status="$1"
  local reason="${2:-}"
  local exit_code="${3:-0}"
  local end_epoch
  end_epoch="$(date +%s)"
  export HWISTOCK_GPT_SUMMARY_STATUS="$status"
  export HWISTOCK_GPT_SUMMARY_REASON="$reason"
  export HWISTOCK_GPT_SUMMARY_EXIT_CODE="$exit_code"
  export END_EPOCH="$end_epoch"
  python3 - <<'PY'
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

kst = timezone(timedelta(hours=9))

def maybe_json(path: str):
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

publish = maybe_json(os.environ.get("PUBLISH_OUT", ""))
response = maybe_json(os.environ.get("RESPONSE", ""))
summary = {
    "run_id": os.environ["RUN_ID"],
    "status": os.environ["HWISTOCK_GPT_SUMMARY_STATUS"],
    "reason": os.environ.get("HWISTOCK_GPT_SUMMARY_REASON") or "",
    "exit_code": int(os.environ.get("HWISTOCK_GPT_SUMMARY_EXIT_CODE") or "0"),
    "started_at": os.environ["START_ISO"],
    "ended_at": datetime.now(kst).replace(microsecond=0).isoformat(),
    "elapsed_seconds": int(os.environ["END_EPOCH"]) - int(os.environ["START_EPOCH"]),
    "target_trade_date_kst": os.environ["TARGET_TRADE_DATE"],
    "purpose": os.environ["PURPOSE"],
    "prompt_source": os.environ.get("PROMPT_SOURCE") or "",
    "run_dir": os.environ["RUN_DIR"],
    "response_json": os.environ["RESPONSE"],
    "raw_response": os.environ["RAW_RESPONSE"],
    "publish_output": os.environ["PUBLISH_OUT"],
    "publish_stderr": os.environ["PUBLISH_ERR"],
    "codex_events": os.environ["CODEX_EVENTS"],
    "codex_last_message": os.environ["CODEX_LAST"],
    "codex_stderr": os.environ["CODEX_STDERR"],
    "preflight_codex_events": os.environ["PREFLIGHT_CODEX_EVENTS"],
    "preflight_browser_events": os.environ["PREFLIGHT_BROWSER_EVENTS"],
    "artifact_id": publish.get("artifact_id") if isinstance(publish, dict) else None,
    "validation_status": publish.get("validation_status") if isinstance(publish, dict) else None,
    "artifact_paths": publish.get("artifact_paths") if isinstance(publish, dict) else None,
    "route": (response or publish or {}).get("route") if isinstance((response or publish or {}), dict) else None,
    "reviewer": (response or publish or {}).get("reviewer") if isinstance((response or publish or {}), dict) else None,
    "items_count": len((response or {}).get("items") or []) if isinstance(response, dict) else 0,
    "no_trade_reasons_count": len((response or {}).get("no_trade_reasons") or []) if isinstance(response, dict) else 0,
}
Path(os.environ["SUMMARY"]).write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
PY
}

run_codex_exec() {
  local prompt_path="$1"
  local events_path="$2"
  local last_path="$3"
  local stderr_path="$4"
  local timeout_seconds="$5"
  timeout "$timeout_seconds" "$CODEX_BIN" exec --json \
    --dangerously-bypass-approvals-and-sandbox \
    -C "$REPO_ROOT" \
    -o "$last_path" \
    - <"$prompt_path" >"$events_path" 2>"$stderr_path"
}

if [[ ! -x "$CODEX_BIN" ]]; then
  publish_safe_block "codex_bin_missing" || true
  write_summary "safe_block" "codex_bin_missing:${CODEX_BIN}" 1
  exit 0
fi

if [[ "${HWISTOCK_GPT_SKIP_PREFLIGHT:-false}" != "true" ]]; then
  printf 'Reply with exactly OK. Do not use tools.\n' >"${RUN_DIR}/preflight-codex-prompt.md"
  set +e
  run_codex_exec "${RUN_DIR}/preflight-codex-prompt.md" \
    "$PREFLIGHT_CODEX_EVENTS" "$PREFLIGHT_CODEX_LAST" "$PREFLIGHT_CODEX_STDERR" \
    "${HWISTOCK_GPT_PREFLIGHT_CODEX_TIMEOUT_SECONDS:-120}"
  preflight_codex_code=$?
  set -e
  if [[ "$preflight_codex_code" -ne 0 ]]; then
    publish_safe_block "codex_preflight_failed" || true
    write_summary "safe_block" "codex_preflight_failed:${preflight_codex_code}" "$preflight_codex_code"
    exit 0
  fi

  cat >"$PREFLIGHT_BROWSER_PROMPT" <<'EOF'
Use the mcp__node_repl_http js tool exactly once. In that tool, import `/home/hwi/.codex/plugins/cache/openai-bundled/chrome/26.519.81530/scripts/browser-client.mjs`, call `setupBrowserRuntime({ globals: globalThis })`, then run `agent.browsers.list()`. Return only JSON with `{ "ok": true, "browser_count": <number> }` if it works, or `{ "ok": false, "error": <string> }` if it fails. Do not open pages, do not browse, do not edit files. Then answer with exactly DONE.
EOF
  set +e
  run_codex_exec "$PREFLIGHT_BROWSER_PROMPT" \
    "$PREFLIGHT_BROWSER_EVENTS" "$PREFLIGHT_BROWSER_LAST" "$PREFLIGHT_BROWSER_STDERR" \
    "${HWISTOCK_GPT_PREFLIGHT_BROWSER_TIMEOUT_SECONDS:-180}"
  preflight_browser_code=$?
  set -e
  if [[ "$preflight_browser_code" -ne 0 ]]; then
    publish_safe_block "browser_preflight_failed" || true
    write_summary "safe_block" "browser_preflight_failed:${preflight_browser_code}" "$preflight_browser_code"
    exit 0
  fi
  python3 - <<'PY'
import json
import os
from pathlib import Path

events = Path(os.environ["PREFLIGHT_BROWSER_EVENTS"])
ok = False
for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
    try:
        item = (json.loads(line).get("item") or {})
    except Exception:
        continue
    if item.get("type") != "mcp_tool_call":
        continue
    result = item.get("result") or {}
    for content in result.get("content") or []:
        text = content.get("text") if isinstance(content, dict) else None
        if not text:
            continue
        try:
            payload = json.loads(text)
        except Exception:
            continue
        if payload.get("ok") is True and int(payload.get("browser_count") or 0) > 0:
            ok = True
if not ok:
    raise SystemExit("browser_preflight_no_backend")
PY
fi

if [[ "${HWISTOCK_GPT_SMOKE_ONLY:-false}" == "true" ]]; then
  write_summary "smoke_ok" "preflight_only" 0
  exit 0
fi

if [[ -z "$PROMPT_SOURCE" || ! -f "$PROMPT_SOURCE" ]]; then
  publish_safe_block "prompt_missing" || true
  write_summary "safe_block" "prompt_missing" 0
  exit 0
fi

python3 - <<'PY'
import json
import os
import re
from pathlib import Path

prompt = Path(os.environ["PROMPT_SOURCE"]).read_text(encoding="utf-8", errors="replace")
patterns = [
    re.compile(r"(?i)(api[_-]?key|appsecret|password|passwd|access[_-]?token|refresh[_-]?token|authorization|account[_-]?no)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=:-]{12,}"),
]
hits = sum(1 for pattern in patterns for _ in pattern.finditer(prompt))
Path(os.environ["SECRET_SCAN_JSON"]).write_text(json.dumps({"suspicious_assignment_count": hits}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if hits:
    raise SystemExit("prompt_secret_scan_failed")
PY

cat >"$CODEX_PROMPT" <<EOF
# hwiStock GPT Pro morning watchlist runner

You are a Codex CLI automation runner inside \`${REPO_ROOT}\`.

Objective: perform the GPT Pro leg only, using the user's local Chrome/browser-use route, then save a strict JSON file. Do not edit repo files. Do not commit. Do not call broker APIs or order APIs.

Hard route rule:
- Use local Chrome/browser-use via the Chrome plugin/browser-client route available to Codex CLI.
- Do NOT use ssh-browser-use, SSH reverse socket routes, remote Chrome, CDP fallback, headless Playwright, or DeepSeek.
- If the selected route cannot reach ChatGPT Pro, write a JSON failure summary to \`${RUN_DIR}/failure.json\` and stop.

Input prompt to send to ChatGPT Pro:
- Read \`${PROMPT_SOURCE}\`.
- Send its content to ChatGPT Pro.
- If ChatGPT Web turns the long prompt into a pasted-text/document card, add a short visible instruction: \`첨부된 pasted text 번들을 분석해서 strict JSON object 하나만 반환해. Markdown 금지. 사람이 읽는 자연어 문자열 값은 한국어로 작성하고, schema key/enum/ticker/route 같은 기계값은 지정 형식 그대로 유지해.\` and send.
- Wait until generation is complete. Do not press Stop or retry while it is still generating.
- If the first response is not strict JSON, ask once: \`같은 객체를 strict valid minified JSON object 하나로만 다시 반환해. 인용/설명/Markdown 제거, 문자열 escape 처리. 사람이 읽는 자연어 문자열 값은 한국어로 유지하고 schema key/enum/ticker/route 같은 기계값은 그대로 둬.\`

Output requirements:
- Save the final strict JSON object only to \`${RESPONSE}\`.
- Save any raw assistant text to \`${RAW_RESPONSE}\`.
- The JSON must parse with Python \`json.loads\` and must contain:
  - \`schema_version = "morning_watchlist/v0"\`
  - \`reviewer = "chatgpt_pro"\`
  - \`route = "codex_cli_local_browser_use"\`
  - \`forbidden_actions_acknowledged = true\`
- Keep the ChatGPT tab open as handoff.
- Final answer should be brief and include whether the JSON file was saved and parse-valid.
EOF

set +e
CODEX_START="$(date +%s)"
run_codex_exec "$CODEX_PROMPT" "$CODEX_EVENTS" "$CODEX_LAST" "$CODEX_STDERR" "${HWISTOCK_GPT_CODEX_TIMEOUT_SECONDS:-1800}"
CODEX_EXIT=$?
CODEX_END="$(date +%s)"
set -e
export CODEX_START CODEX_END CODEX_EXIT

if [[ "$CODEX_EXIT" -ne 0 ]]; then
  publish_safe_block "codex_exec_failed" || true
  write_summary "safe_block" "codex_exec_failed:${CODEX_EXIT}" "$CODEX_EXIT"
  exit 0
fi

python3 - <<'PY'
import json
import os
from pathlib import Path

p = Path(os.environ["RESPONSE"])
if not p.is_file():
    raise SystemExit("missing_response_json")
obj = json.loads(p.read_text(encoding="utf-8"))
assert obj.get("schema_version") == "morning_watchlist/v0", obj.get("schema_version")
assert obj.get("reviewer") == "chatgpt_pro", obj.get("reviewer")
assert obj.get("route") == "codex_cli_local_browser_use", obj.get("route")
assert obj.get("forbidden_actions_acknowledged") is True
PY

source ./env.sh >/dev/null 2>&1
python backend/service/ai_analysis_runner.py --once \
  --job publish-morning-watchlist \
  --source-json "$RESPONSE" \
  --target-trade-date "$TARGET_TRADE_DATE" \
  --purpose "$PURPOSE" \
  >"$PUBLISH_OUT" 2>"$PUBLISH_ERR"

write_summary "ok" "" 0
