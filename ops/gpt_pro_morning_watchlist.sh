#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${HWISTOCK_REPO_ROOT:-/data/workspace/My/hwiStock}"
cd "$REPO_ROOT"

umask 077
export TZ="${TZ:-Asia/Seoul}"

CODEX_BIN="${HWISTOCK_CODEX_BIN:-/home/hwi/.local/bin/codex}"
DATA_DIR="${HWISTOCK_DATA_DIR:-${REPO_ROOT}/data}"
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
PROMPT_SOURCE_EXPLICIT=false
if [[ -n "$PROMPT_SOURCE" ]]; then
  PROMPT_SOURCE_EXPLICIT=true
fi

START_EPOCH="$(date +%s)"
START_ISO="$(date --iso-8601=seconds)"

CODEX_PROMPT="${RUN_DIR}/codex-prompt.md"
RESPONSE="${RUN_DIR}/response.json"
RAW_RESPONSE="${RUN_DIR}/response.raw.txt"
SUMMARY="${RUN_DIR}/summary.json"
PUBLISH_OUT="${RUN_DIR}/publish.json"
PUBLISH_ERR="${RUN_DIR}/publish.err.log"
PROMPT_BUILD_OUT="${RUN_DIR}/prompt-build.json"
PROMPT_BUILD_ERR="${RUN_DIR}/prompt-build.err.log"
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
FAILURE_JSON="${RUN_DIR}/failure.json"
RESPONSE_VALIDATE_ERR="${RUN_DIR}/response-validate.err.log"

export RUN_ID RUN_DIR TARGET_TRADE_DATE PURPOSE PROMPT_SOURCE START_EPOCH START_ISO
export REPO_ROOT DATA_DIR DAY
export RESPONSE RAW_RESPONSE SUMMARY PUBLISH_OUT PUBLISH_ERR CODEX_EVENTS CODEX_LAST CODEX_STDERR
export PROMPT_BUILD_OUT PROMPT_BUILD_ERR
export PREFLIGHT_CODEX_EVENTS PREFLIGHT_CODEX_LAST PREFLIGHT_CODEX_STDERR
export PREFLIGHT_BROWSER_PROMPT PREFLIGHT_BROWSER_EVENTS PREFLIGHT_BROWSER_LAST PREFLIGHT_BROWSER_STDERR
export SECRET_SCAN_JSON FAILURE_JSON RESPONSE_VALIDATE_ERR

publish_safe_block() {
  local reason="$1"
  local safe_purpose="${PURPOSE}_${reason}"
  set +e
  source ./env.sh >/dev/null 2>&1
  export HWISTOCK_DATA_DIR="$DATA_DIR"
  python backend/service/ai_analysis_runner.py --once \
    --job publish-morning-watchlist \
    --target-trade-date "$TARGET_TRADE_DATE" \
    --purpose "$safe_purpose" \
    >"$PUBLISH_OUT" 2>"$PUBLISH_ERR"
  local code=$?
  set -e
  return "$code"
}

publish_safe_block_or_fail() {
  local reason="$1"
  set +e
  publish_safe_block "$reason"
  local code=$?
  set -e
  if [[ "$code" -ne 0 ]]; then
    write_summary "safe_block_publish_failed" "${reason}:${code}" "$code"
    exit "$code"
  fi
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
repo_root = Path(os.environ["REPO_ROOT"]).resolve()
data_dir = Path(os.environ["DATA_DIR"]).resolve()
default_data_dir = repo_root / "data"
target_trade_date = os.environ["TARGET_TRADE_DATE"]
run_day = os.environ["DAY"]

expected_canonical_paths = {
    "ai_latest": str(data_dir / "ai" / target_trade_date / "morning-watchlist-latest.json"),
    "morning-watchlist_latest": str(data_dir / "morning-watchlist" / target_trade_date / "morning-watchlist-latest.json"),
    "health": str(data_dir / "evidence" / run_day / "morning-watchlist-publish-health.json"),
}
artifact_paths = publish.get("artifact_paths") if isinstance(publish, dict) else None
if isinstance(artifact_paths, dict):
    canonical_paths = {
        key: str(artifact_paths.get(key) or expected_canonical_paths[key])
        for key in expected_canonical_paths
    }
else:
    canonical_paths = dict(expected_canonical_paths)
published_to_canonical_data = (
    isinstance(publish, dict)
    and publish.get("validation_status") in {"accepted", "safe_block"}
    and all(Path(path).is_file() for path in canonical_paths.values())
)
validation_status = publish.get("validation_status") if isinstance(publish, dict) else None
validation_errors = publish.get("validation_errors") if isinstance(publish, dict) else []
if not isinstance(validation_errors, list):
    validation_errors = [validation_errors] if validation_errors else []
publish_status = "accepted" if validation_status == "accepted" else ("safe_block" if validation_status == "safe_block" else "missing")
response_json_exists = Path(os.environ["RESPONSE"]).is_file()
response_raw_exists = Path(os.environ["RAW_RESPONSE"]).is_file()
parse_status = "parsed" if isinstance(response, dict) else ("missing" if not response_json_exists else "invalid_json")
watchlist_accepted = validation_status == "accepted"
watchlist_usable = (
    watchlist_accepted
    and isinstance(publish, dict)
    and isinstance(publish.get("items"), list)
    and len(publish.get("items") or []) > 0
)
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
    "data_dir": str(data_dir),
    "is_smoke_data_dir": data_dir != default_data_dir,
    "run_dir": os.environ["RUN_DIR"],
    "run_log_dir": os.environ["RUN_DIR"],
    "response_json": os.environ["RESPONSE"],
    "raw_response": os.environ["RAW_RESPONSE"],
    "failure_output": os.environ.get("FAILURE_JSON"),
    "response_validate_stderr": os.environ.get("RESPONSE_VALIDATE_ERR"),
    "publish_output": os.environ["PUBLISH_OUT"],
    "publish_stderr": os.environ["PUBLISH_ERR"],
    "prompt_build_output": os.environ["PROMPT_BUILD_OUT"],
    "prompt_build_stderr": os.environ["PROMPT_BUILD_ERR"],
    "codex_events": os.environ["CODEX_EVENTS"],
    "codex_last_message": os.environ["CODEX_LAST"],
    "codex_stderr": os.environ["CODEX_STDERR"],
    "preflight_codex_events": os.environ["PREFLIGHT_CODEX_EVENTS"],
    "preflight_browser_events": os.environ["PREFLIGHT_BROWSER_EVENTS"],
    "artifact_id": (
        publish.get("artifact_id") or publish.get("safe_block_id")
        if isinstance(publish, dict)
        else None
    ),
    "safe_block_id": publish.get("safe_block_id") if isinstance(publish, dict) else None,
    "validation_status": validation_status,
    "validation_errors": validation_errors,
    "artifact_paths": publish.get("artifact_paths") if isinstance(publish, dict) else None,
    "canonical_artifact_paths": canonical_paths,
    "published_to_canonical_data": published_to_canonical_data,
    "canonical_artifact_written": published_to_canonical_data,
    "watchlist_accepted": watchlist_accepted,
    "watchlist_usable": watchlist_usable,
    "response_json_exists": response_json_exists,
    "response_raw_exists": response_raw_exists,
    "parse_status": parse_status,
    "publish_status": publish_status,
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

build_prompt_if_missing() {
  if [[ "$PROMPT_SOURCE_EXPLICIT" == "true" ]]; then
    if [[ -n "$PROMPT_SOURCE" && -f "$PROMPT_SOURCE" ]]; then
      return 0
    fi
    printf 'explicit prompt source missing: %s\n' "$PROMPT_SOURCE" >"$PROMPT_BUILD_ERR"
    return 2
  fi

  set +e
  source ./env.sh >/dev/null 2>&1
  local env_source_code=$?
  if [[ "$env_source_code" -eq 0 ]]; then
    export HWISTOCK_DATA_DIR="$DATA_DIR"
    python backend/service/ai_analysis_runner.py --once \
      --job build-morning-prompt \
      --target-trade-date "$TARGET_TRADE_DATE" \
      --purpose "$PURPOSE" \
      >"$PROMPT_BUILD_OUT" 2>"$PROMPT_BUILD_ERR"
    local build_code=$?
  else
    local build_code="$env_source_code"
    printf 'env.sh source failed: %s\n' "$env_source_code" >"$PROMPT_BUILD_ERR"
  fi
  set -e
  if [[ "$build_code" -ne 0 ]]; then
    return "$build_code"
  fi

  PROMPT_SOURCE="$(
    python3 - <<'PY'
import json
import os
from pathlib import Path

payload = json.loads(Path(os.environ["PROMPT_BUILD_OUT"]).read_text(encoding="utf-8"))
paths = payload.get("prompt_paths") if isinstance(payload, dict) else {}
for key in ("ai_latest", "prompts_latest"):
    value = str((paths or {}).get(key) or "").strip()
    if value and Path(value).is_file():
        print(value)
        break
PY
  )"
  export PROMPT_SOURCE
  [[ -n "$PROMPT_SOURCE" && -f "$PROMPT_SOURCE" ]]
}

if [[ ! -x "$CODEX_BIN" ]]; then
  publish_safe_block_or_fail "codex_bin_missing"
  write_summary "safe_block" "codex_bin_missing:${CODEX_BIN}" 1
  exit 0
fi

set +e
build_prompt_if_missing
prompt_build_code=$?
set -e
if [[ "$prompt_build_code" -ne 0 ]]; then
  publish_safe_block_or_fail "prompt_build_failed"
  write_summary "safe_block" "prompt_build_failed:${prompt_build_code}" "$prompt_build_code"
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
    publish_safe_block_or_fail "codex_preflight_failed"
    write_summary "safe_block" "codex_preflight_failed:${preflight_codex_code}" "$preflight_codex_code"
    exit 0
  fi

  browser_preflight_ok="false"
  browser_preflight_reason="browser_preflight_no_backend"
  browser_preflight_detail="browser_preflight_no_backend"
  browser_attempts="${HWISTOCK_GPT_PREFLIGHT_BROWSER_ATTEMPTS:-3}"
  if ! [[ "$browser_attempts" =~ ^[0-9]+$ ]] || [[ "$browser_attempts" -lt 1 ]]; then
    browser_attempts=1
  fi

  for ((browser_attempt = 1; browser_attempt <= browser_attempts; browser_attempt++)); do
    PREFLIGHT_BROWSER_PROMPT="${RUN_DIR}/preflight-browser-prompt-attempt-${browser_attempt}.md"
    PREFLIGHT_BROWSER_EVENTS="${RUN_DIR}/preflight-browser-events-attempt-${browser_attempt}.jsonl"
    PREFLIGHT_BROWSER_LAST="${RUN_DIR}/preflight-browser-last-message-attempt-${browser_attempt}.md"
    PREFLIGHT_BROWSER_STDERR="${RUN_DIR}/preflight-browser-stderr-attempt-${browser_attempt}.log"
    export PREFLIGHT_BROWSER_PROMPT PREFLIGHT_BROWSER_EVENTS PREFLIGHT_BROWSER_LAST PREFLIGHT_BROWSER_STDERR

    cat >"$PREFLIGHT_BROWSER_PROMPT" <<'EOF'
Use the mcp__node_repl_http js tool exactly once with timeout_ms set to at least 30000.

In that tool, run JavaScript equivalent to this logic:
- import `file:///home/hwi/.codex/plugins/cache/openai-bundled/chrome/26.519.81530/scripts/browser-client.mjs`
- call `setupBrowserRuntime({ globals: globalThis })`
- run `agent.browsers.list()` with a 20000ms Promise.race timeout
- write only JSON text with `nodeRepl.write(JSON.stringify({ ok: true, browser_count: <number> }))` when at least the browser list call completes, or `{ "ok": false, "error": <string> }` on failure.

Do not open pages, do not browse, do not edit files.
After the tool call, answer with exactly DONE.
EOF
    set +e
    run_codex_exec "$PREFLIGHT_BROWSER_PROMPT" \
      "$PREFLIGHT_BROWSER_EVENTS" "$PREFLIGHT_BROWSER_LAST" "$PREFLIGHT_BROWSER_STDERR" \
      "${HWISTOCK_GPT_PREFLIGHT_BROWSER_TIMEOUT_SECONDS:-240}"
    preflight_browser_code=$?
    set -e
    if [[ "$preflight_browser_code" -ne 0 ]]; then
      browser_preflight_reason="browser_preflight_failed"
      browser_preflight_detail="browser_preflight_failed:${preflight_browser_code}:attempt_${browser_attempt}_of_${browser_attempts}"
      sleep "${HWISTOCK_GPT_PREFLIGHT_BROWSER_RETRY_SLEEP_SECONDS:-2}"
      continue
    fi

    set +e
    python3 - <<'PY'
import json
import os
import re
from pathlib import Path

events = Path(os.environ["PREFLIGHT_BROWSER_EVENTS"])
ok = False

def load_json_candidates(text: str):
    stripped = text.strip()
    if not stripped:
        return []
    candidates = [stripped]
    candidates.extend(match.group(1).strip() for match in re.finditer(r"```(?:json)?\s*(.*?)```", text, re.S | re.I))
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
        except Exception:
            continue
        yield payload
    for candidate in candidates:
        try:
            yield json.loads(candidate)
        except Exception:
            continue

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
        for payload in load_json_candidates(text):
            if isinstance(payload, dict) and payload.get("ok") is True and int(payload.get("browser_count") or 0) > 0:
                ok = True
if not ok:
    raise SystemExit("browser_preflight_no_backend")
PY
    browser_validate_code=$?
    set -e
    if [[ "$browser_validate_code" -eq 0 ]]; then
      browser_preflight_ok="true"
      browser_preflight_reason=""
      browser_preflight_detail=""
      break
    fi
    browser_preflight_reason="browser_preflight_no_backend"
    browser_preflight_detail="browser_preflight_no_backend:${browser_validate_code}:attempt_${browser_attempt}_of_${browser_attempts}"
    sleep "${HWISTOCK_GPT_PREFLIGHT_BROWSER_RETRY_SLEEP_SECONDS:-2}"
  done

  if [[ "$browser_preflight_ok" != "true" ]]; then
    publish_safe_block_or_fail "$browser_preflight_reason"
    write_summary "safe_block" "$browser_preflight_detail" 1
    exit 0
  fi
fi

if [[ "${HWISTOCK_GPT_SMOKE_ONLY:-false}" == "true" ]]; then
  write_summary "smoke_ok" "preflight_only" 0
  exit 0
fi

if [[ -z "$PROMPT_SOURCE" || ! -f "$PROMPT_SOURCE" ]]; then
  publish_safe_block_or_fail "prompt_missing"
  write_summary "safe_block" "prompt_missing" 0
  exit 0
fi

set +e
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
secret_scan_code=$?
set -e
if [[ "$secret_scan_code" -ne 0 ]]; then
  publish_safe_block_or_fail "prompt_secret_scan_failed"
  write_summary "safe_block" "prompt_secret_scan_failed:${secret_scan_code}" "$secret_scan_code"
  exit 0
fi

cat >"$CODEX_PROMPT" <<EOF
# hwiStock GPT Pro morning watchlist runner

You are a Codex CLI automation runner inside \`${REPO_ROOT}\`.

Objective: perform the GPT Pro leg only, using the user's local Chrome/browser-use route, then save a strict morning_watchlist/v1 JSON file. Do not edit repo files. Do not commit. Do not call broker APIs or order APIs.

Hard route rule:
- Use local Chrome/browser-use via the Chrome plugin/browser-client route available to Codex CLI.
- Do NOT use ssh-browser-use, SSH reverse socket routes, remote Chrome, CDP fallback, headless Playwright, or DeepSeek.
- If the selected route cannot reach ChatGPT Pro, write a JSON failure summary to \`${FAILURE_JSON}\` and stop.
- When using the node_repl_http js/browser-client route, set tool timeout_ms to at least 30000 and use explicit JS-side waits/timeouts for browser discovery/navigation. Do not rely on the default 10000ms tool timeout for browser operations.

Input prompt to send to ChatGPT Pro:
- Read \`${PROMPT_SOURCE}\`.
- Send its content to ChatGPT Pro.
- If ChatGPT Web turns the long prompt into a pasted-text/document card, add a short visible instruction: \`첨부된 pasted text 번들을 분석해서 morning_watchlist/v1 strict JSON object 하나만 반환해. Markdown 금지. top-level items 배열은 필수이고, top-level eligible_for_flash_review 키는 금지야. eligible_for_flash_review는 items[].stance 값으로만 써. 사람이 읽는 자연어 문자열 값은 한국어로 작성하고, schema key/enum/ticker/route 같은 기계값은 지정 형식 그대로 유지해. market_open_plan, first_flash_questions, opening_trigger_conditions, invalidation_conditions, source_refs/pro_refs를 반드시 포함해.\` and send.
- Wait until generation is complete. Do not press Stop or retry while it is still generating.
- If the first response is not strict JSON, ask once: \`같은 morning_watchlist/v1 객체를 strict valid minified JSON object 하나로만 다시 반환해. top-level items 배열 필수, top-level eligible_for_flash_review 키 금지, eligible_for_flash_review는 items[].stance 값으로만 사용. 인용/설명/Markdown 제거, 문자열 escape 처리. 사람이 읽는 자연어 문자열 값은 한국어로 유지하고 schema key/enum/ticker/route 같은 기계값은 그대로 둬.\`

Output requirements:
- Save the final strict JSON object only to \`${RESPONSE}\`.
- Save any raw assistant text to \`${RAW_RESPONSE}\`.
- The JSON must parse with Python \`json.loads\` and must contain:
  - \`schema_version = "morning_watchlist/v1"\`
  - \`reviewer = "chatgpt_pro"\`
  - \`route = "codex_cli_local_browser_use"\`
  - \`forbidden_actions_acknowledged = true\`
  - \`market_open_plan\` with \`opening_bias\`, \`why\`, \`must_wait_for_market_confirmation\`, and \`first_flash_questions\`
  - top-level \`items\` must be a JSON array, even when empty
  - top-level \`eligible_for_flash_review\` is forbidden; \`eligible_for_flash_review\` may appear only as an \`items[].stance\` value
  - each \`items[]\` object whose \`stance\` is \`eligible_for_flash_review\` must include ticker, thesis, opening_trigger_conditions, invalidation_conditions, source_refs or pro_refs, confidence
  - no executable order fields such as entry_price_limit, quantity, order_type
- Keep the ChatGPT tab open as handoff.
- Final answer should be brief and include whether the JSON file was saved and parse-valid.
EOF

gpt_codex_attempts="${HWISTOCK_GPT_CODEX_ATTEMPTS:-3}"
if ! [[ "$gpt_codex_attempts" =~ ^[0-9]+$ ]] || [[ "$gpt_codex_attempts" -lt 1 ]]; then
  gpt_codex_attempts=1
fi
gpt_response_ok="false"
gpt_failure_reason="gpt_response_validation_failed"
gpt_failure_detail="gpt_response_validation_failed"
CODEX_EXIT=0
CODEX_START=""
CODEX_END=""

for ((gpt_attempt = 1; gpt_attempt <= gpt_codex_attempts; gpt_attempt++)); do
  CODEX_EVENTS="${RUN_DIR}/codex-events-attempt-${gpt_attempt}.jsonl"
  CODEX_LAST="${RUN_DIR}/codex-last-message-attempt-${gpt_attempt}.md"
  CODEX_STDERR="${RUN_DIR}/codex-stderr-attempt-${gpt_attempt}.log"
  RESPONSE_VALIDATE_ERR="${RUN_DIR}/response-validate-attempt-${gpt_attempt}.err.log"
  export CODEX_EVENTS CODEX_LAST CODEX_STDERR RESPONSE_VALIDATE_ERR
  rm -f "$RESPONSE" "$RAW_RESPONSE" "$FAILURE_JSON" "$RESPONSE_VALIDATE_ERR"

  set +e
  CODEX_START="$(date +%s)"
  run_codex_exec "$CODEX_PROMPT" "$CODEX_EVENTS" "$CODEX_LAST" "$CODEX_STDERR" "${HWISTOCK_GPT_CODEX_TIMEOUT_SECONDS:-1800}"
  CODEX_EXIT=$?
  CODEX_END="$(date +%s)"
  set -e
  export CODEX_START CODEX_END CODEX_EXIT

  if [[ "$CODEX_EXIT" -ne 0 ]]; then
    gpt_failure_reason="codex_exec_failed"
    gpt_failure_detail="codex_exec_failed:${CODEX_EXIT}:attempt_${gpt_attempt}_of_${gpt_codex_attempts}"
    sleep "${HWISTOCK_GPT_CODEX_RETRY_SLEEP_SECONDS:-3}"
    continue
  fi

  set +e
  python3 - 2>"$RESPONSE_VALIDATE_ERR" <<'PY'
import json
import os
from pathlib import Path

p = Path(os.environ["RESPONSE"])
if not p.is_file():
    raise SystemExit("missing_response_json")
obj = json.loads(p.read_text(encoding="utf-8"))
assert obj.get("schema_version") == "morning_watchlist/v1", obj.get("schema_version")
assert obj.get("reviewer") == "chatgpt_pro", obj.get("reviewer")
assert obj.get("route") == "codex_cli_local_browser_use", obj.get("route")
assert obj.get("forbidden_actions_acknowledged") is True
assert isinstance(obj.get("market_open_plan"), dict)
if "eligible_for_flash_review" in obj:
    raise SystemExit("top_level_eligible_for_flash_review_forbidden")
items = obj.get("items")
if not isinstance(items, list):
    raise SystemExit("items_must_be_list")
for index, item in enumerate(items):
    if not isinstance(item, dict):
        raise SystemExit(f"items_{index}_must_be_object")
    if item.get("stance") != "eligible_for_flash_review":
        continue
    assert item.get("ticker"), index
    assert item.get("thesis"), index
    assert item.get("opening_trigger_conditions"), index
    assert item.get("invalidation_conditions"), index
    assert item.get("source_refs") or item.get("pro_refs"), index
    assert item.get("confidence") is not None, index
    for forbidden in ("entry_price_limit", "quantity", "order_type"):
        assert forbidden not in item, forbidden
PY
  response_validate_code=$?
  set -e
  if [[ "$response_validate_code" -eq 0 ]]; then
    gpt_response_ok="true"
    gpt_failure_reason=""
    gpt_failure_detail=""
    break
  fi
  gpt_failure_reason="gpt_response_validation_failed"
  gpt_failure_detail="gpt_response_validation_failed:${response_validate_code}:attempt_${gpt_attempt}_of_${gpt_codex_attempts}"
  sleep "${HWISTOCK_GPT_CODEX_RETRY_SLEEP_SECONDS:-3}"
done

if [[ "$gpt_response_ok" != "true" ]]; then
  publish_safe_block_or_fail "$gpt_failure_reason"
  write_summary "safe_block" "$gpt_failure_detail" 1
  exit 0
fi

set +e
source ./env.sh >/dev/null 2>&1
env_source_code=$?
if [[ "$env_source_code" -eq 0 ]]; then
  export HWISTOCK_DATA_DIR="$DATA_DIR"
  python backend/service/ai_analysis_runner.py --once \
    --job publish-morning-watchlist \
    --source-json "$RESPONSE" \
    --target-trade-date "$TARGET_TRADE_DATE" \
    --purpose "$PURPOSE" \
    >"$PUBLISH_OUT" 2>"$PUBLISH_ERR"
  publish_code=$?
else
  publish_code="$env_source_code"
  printf 'env.sh source failed: %s\n' "$env_source_code" >"$PUBLISH_ERR"
fi
set -e

if [[ "$publish_code" -ne 0 ]]; then
  write_summary "publish_failed" "publish_morning_watchlist_failed:${publish_code}" "$publish_code"
  exit "$publish_code"
fi

write_summary "ok" "" 0
