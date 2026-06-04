#!/usr/bin/env bash
# 파일명: backend/run.sh
# 작성자: LSH
# 설명: FastAPI 백엔드 prod/dev 실행/중지/상태 확인/재시작 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

CONFIG_FILE="$SCRIPT_DIR/config.ini"
PID_FILE_PROD="$LOG_DIR/backend.pid"
PID_FILE_DEV="$LOG_DIR/backend-dev.pid"
OUT_FILE_PROD="$LOG_DIR/backend.out"
ERR_FILE_PROD="$LOG_DIR/backend.err"
OUT_FILE_DEV="$LOG_DIR/backend-dev.out"
ERR_FILE_DEV="$LOG_DIR/backend-dev.err"

parse_port() {
  if [[ -f "$CONFIG_FILE" ]]; then
    # INI 파싱: [SERVER] 섹션의 port 값을 가져온다.
    # 섹션 이후 첫 port= 라인 추출
    awk -F '=' '
      BEGIN { in_server=0 }
      /^\[SERVER\]/ { in_server=1; next }
      /^\[/ { in_server=0 }
      in_server && tolower($1) ~ /^port[[:space:]]*$/ { gsub(/[[:space:]]/, "", $2); print $2; exit }
    ' "$CONFIG_FILE"
  fi
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
      echo "백엔드($mode) 시작 실패: 프로세스가 종료됨"
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

  echo "백엔드($mode) 시작 실패: 포트 $port 리슨 확인 불가"
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

SERVER_PORT_PROD="$(parse_port)"
SERVER_PORT_PROD="${SERVER_PORT_PROD:-5001}"
SERVER_PORT_DEV="${BACKEND_DEV_PORT:-5001}"
DEFAULT_BIND_HOST="127.0.0.1"
resolve_bind_host() {
  python3 - "$@" <<'PY'
import os
import sys

sys.path.insert(0, os.environ.get("HWISTOCK_BACKEND_DIR", "."))
from service.HwiStockRunnerService import resolve_bind_host

config_host = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
print(resolve_bind_host(config_host or None))
PY
}
BIND_HOST="$(HWISTOCK_BACKEND_DIR="$SCRIPT_DIR" resolve_bind_host "")"

start_mode() {
  local mode="${1:-prod}"
  local pid_file="$PID_FILE_PROD"
  local out_file="$OUT_FILE_PROD"
  local err_file="$ERR_FILE_PROD"
  local port="$SERVER_PORT_PROD"
  local extra_args=()

  if [[ "$mode" == "dev" ]]; then
    pid_file="$PID_FILE_DEV"
    out_file="$OUT_FILE_DEV"
    err_file="$ERR_FILE_DEV"
    port="$SERVER_PORT_DEV"
    extra_args+=(--reload)
  fi

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "백엔드($mode) 이미 실행 중 (PID $(cat "$pid_file"))"
    return
  fi
  echo "백엔드($mode) 시작... (port=$port)"
  (
    cd "$SCRIPT_DIR"
    nohup uvicorn server:app --host "$BIND_HOST" --port "$port" "${extra_args[@]}" \
      </dev/null \
      >>"$out_file" 2>>"$err_file" &
    echo $! >"$pid_file"
  )
  if wait_until_started "$mode" "$pid_file" "$port" "$err_file"; then
    echo "백엔드($mode) 시작됨 (PID $(cat "$pid_file"))"
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
      echo "백엔드($mode) 종료 (PID $pid)"
      kill "$pid"
    fi
    rm -f "$pid_file"
  else
    echo "백엔드($mode) 실행 기록 없음"
  fi
}

status_mode() {
  local mode="${1:-prod}"
  local pid_file="$PID_FILE_PROD"
  if [[ "$mode" == "dev" ]]; then
    pid_file="$PID_FILE_DEV"
  fi
  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "백엔드($mode) 실행 중 (PID $(cat "$pid_file"))"
  else
    echo "백엔드($mode) 정지"
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
