#!/usr/bin/env bash
# 파일명: frontend-web/run.sh
# 작성자: LSH
# 설명: Next.js 프론트엔드 prod/dev 실행/중지/상태 확인/재시작 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

CONFIG_FILE="$SCRIPT_DIR/config.ini"
PID_FILE_PROD="$LOG_DIR/frontend.pid"
PID_FILE_DEV="$LOG_DIR/frontend-dev.pid"
OUT_FILE_PROD="$LOG_DIR/frontend.out"
ERR_FILE_PROD="$LOG_DIR/frontend.err"
OUT_FILE_DEV="$LOG_DIR/frontend-dev.out"
ERR_FILE_DEV="$LOG_DIR/frontend-dev.err"

parse_ini_value() {
  local section="${1:-}"
  local key="${2:-}"
  if [[ -z "$section" || -z "$key" ]]; then
    return 0
  fi
  awk -F '=' -v sec="$section" -v want="$key" '
    BEGIN { in_sec=0; want_l=tolower(want) }
    $0 ~ "^\\[" sec "\\]" { in_sec=1; next }
    $0 ~ "^\\[" { in_sec=0 }
    in_sec {
      k=$1
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", k)
      if (tolower(k) != want_l) next
      v=$2
      sub(/^[[:space:]]+/, "", v)
      sub(/[[:space:]]+$/, "", v)
      print v
      exit
    }
  ' "$CONFIG_FILE"
}

is_port_number() {
  [[ "${1:-}" =~ ^[0-9]+$ ]]
}

is_port_listening() {
  local port="${1:-}"
  if ! is_port_number "$port"; then
    return 1
  fi
  ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${port}$"
}

list_port_listener_pids() {
  local port="${1:-}"
  if ! is_port_number "$port"; then
    return 0
  fi
  ss -ltnp 2>/dev/null \
    | awk -v needle=":${port}" '$4 ~ needle"$" { print $0 }' \
    | grep -oE 'pid=[0-9]+' \
    | cut -d '=' -f2 \
    | sort -u || true
}

stop_existing_port_processes() {
  local mode="${1:-prod}"
  local port="${2:-}"
  local listener_pids
  listener_pids="$(list_port_listener_pids "$port" | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
  if [[ -z "$listener_pids" ]]; then
    return 0
  fi

  echo "프론트엔드($mode) 포트 $port 기존 프로세스 종료: $listener_pids"
  local pid
  for pid in $listener_pids; do
    kill "$pid" 2>/dev/null || true
  done
  sleep 1

  for pid in $listener_pids; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  done
  sleep 0.2

  if is_port_listening "$port"; then
    echo "프론트엔드($mode) 시작 실패: 포트 $port 점유 프로세스 종료 실패"
    return 1
  fi
}

extract_port_from_host() {
  local input="${1:-}"
  if [[ -z "$input" ]]; then
    return 0
  fi
  local hostport="$input"
  hostport="${hostport#*://}"
  hostport="${hostport%%/*}"

  # IPv6: http://[::1]:5000
  if [[ "$hostport" =~ ^\\[[^\\]]+\\]:(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi

  # IPv4/hostname: localhost:5000
  if [[ "$hostport" == *:* ]]; then
    echo "${hostport##*:}"
    return 0
  fi
}

parse_port() {
  if [[ -f "$CONFIG_FILE" ]]; then
    local port
    port="$(parse_ini_value "WEB" "port" || true)"
    if is_port_number "$port"; then
      echo "$port"
      return 0
    fi

    port="$(parse_ini_value "APP" "port" || true)"
    if is_port_number "$port"; then
      echo "$port"
      return 0
    fi

    local frontendHost
    frontendHost="$(parse_ini_value "APP" "frontendHost" || true)"
    port="$(extract_port_from_host "$frontendHost" || true)"
    if is_port_number "$port"; then
      echo "$port"
      return 0
    fi
  fi
}

PROD_PORT="$(parse_port)"
PROD_PORT="${PROD_PORT:-5000}"
DEV_PORT="${FRONTEND_DEV_PORT:-5000}"

resolve_next_bin() {
  local next_bin="$SCRIPT_DIR/node_modules/.bin/next"
  if [[ -x "$next_bin" ]]; then
    echo "$next_bin"
    return 0
  fi
  echo "next 실행 파일을 찾을 수 없습니다: $next_bin" >&2
  echo "먼저 frontend-web에서 pnpm install을 실행해 주세요." >&2
  return 1
}

ensure_build_for_prod() {
  local build_id_file="$SCRIPT_DIR/.next/BUILD_ID"
  local should_build=0
  local build_reason=""

  if [[ ! -f "$build_id_file" ]]; then
    should_build=1
    build_reason="빌드 없음"
  else
    local stale_file
    stale_file="$(
      find \
        "$SCRIPT_DIR/app" \
        "$SCRIPT_DIR/public" \
        "$SCRIPT_DIR/package.json" \
        "$SCRIPT_DIR/next.config.js" \
        "$SCRIPT_DIR/next.config.mjs" \
        "$SCRIPT_DIR/postcss.config.mjs" \
        "$SCRIPT_DIR/tailwind.config.js" \
        "$SCRIPT_DIR/middleware.js" \
        "$SCRIPT_DIR/config.ini" \
        "$SCRIPT_DIR/config_dev.ini" \
        "$SCRIPT_DIR/config_prod.ini" \
        -type f -newer "$build_id_file" -print -quit 2>/dev/null || true
    )"
    if [[ -n "$stale_file" ]]; then
      should_build=1
      build_reason="소스 변경 감지"
    fi
  fi

  if [[ "$should_build" -eq 1 ]]; then
    echo "프론트엔드(prod) ${build_reason}. pnpm build 실행..."
    (cd "$SCRIPT_DIR" && pnpm build)
  fi
}

wait_until_started() {
  local mode="${1:-prod}"
  local pid_file="${2:-}"
  local port="${3:-}"
  local err_file="${4:-}"
  local retries=20
  local delay_sec=0.5
  local i

  for ((i = 1; i <= retries; i++)); do
    if [[ ! -f "$pid_file" ]]; then
      break
    fi
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
      echo "프론트엔드($mode) 시작 실패: 프로세스가 종료됨"
      rm -f "$pid_file"
      if [[ -f "$err_file" ]]; then
        tail -n 40 "$err_file" || true
      fi
      return 1
    fi
    if is_port_listening "$port"; then
      return 0
    fi
    sleep "$delay_sec"
  done

  echo "프론트엔드($mode) 시작 실패: 포트 $port 리슨 확인 불가"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
    rm -f "$pid_file"
  fi
  if [[ -f "$err_file" ]]; then
    tail -n 40 "$err_file" || true
  fi
  return 1
}

start_mode() {
  local mode="${1:-prod}"
  local pid_file="$PID_FILE_PROD"
  local out_file="$OUT_FILE_PROD"
  local err_file="$ERR_FILE_PROD"
  local port="$PROD_PORT"
  local next_bin
  next_bin="$(resolve_next_bin)"
  local cmd=("$next_bin" "start" "--hostname" "127.0.0.1" "--port" "$port")

  if [[ "$mode" == "dev" ]]; then
    pid_file="$PID_FILE_DEV"
    out_file="$OUT_FILE_DEV"
    err_file="$ERR_FILE_DEV"
    port="$DEV_PORT"
    cmd=("$next_bin" "dev" "--turbopack" "--hostname" "127.0.0.1" "--port" "$port")
  else
    ensure_build_for_prod
  fi

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "프론트엔드($mode) 이미 실행 중 (PID $(cat "$pid_file"))"
    return
  fi

  stop_existing_port_processes "$mode" "$port"

  echo "프론트엔드($mode) 시작... (port=$port)"
  (
    cd "$SCRIPT_DIR"
    nohup "${cmd[@]}" </dev/null >>"$out_file" 2>>"$err_file" &
    echo $! >"$pid_file"
  )
  if wait_until_started "$mode" "$pid_file" "$port" "$err_file"; then
    echo "프론트엔드($mode) 시작됨 (PID $(cat "$pid_file"))"
    return 0
  fi
  return 1
}

stop_mode() {
  local mode="${1:-prod}"
  local pid_file="$PID_FILE_PROD"
  if [[ "$mode" == "dev" ]]; then
    pid_file="$PID_FILE_DEV"
  fi
  if [[ -f "$pid_file" ]]; then
    local pid
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
      echo "프론트엔드($mode) 종료 (PID $pid)"
      kill "$pid"
    fi
    rm -f "$pid_file"
  else
    echo "프론트엔드($mode) 실행 기록 없음"
  fi
}

status_mode() {
  local mode="${1:-prod}"
  local pid_file="$PID_FILE_PROD"
  if [[ "$mode" == "dev" ]]; then
    pid_file="$PID_FILE_DEV"
  fi
  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "프론트엔드($mode) 실행 중 (PID $(cat "$pid_file"))"
  else
    echo "프론트엔드($mode) 정지"
  fi
}

restart_mode() {
  local mode="${1:-prod}"
  stop_mode "$mode"
  start_mode "$mode"
}

case "${1:-}" in
  start) start_mode prod ;;
  stop) stop_mode prod ;;
  status) status_mode prod ;;
  restart) restart_mode prod ;;
  start-dev) start_mode dev ;;
  stop-dev) stop_mode dev ;;
  status-dev) status_mode dev ;;
  restart-dev) restart_mode dev ;;
  *)
    echo "사용법: $0 {start|stop|status|restart|start-dev|stop-dev|status-dev|restart-dev}"
    exit 1
    ;;
esac
