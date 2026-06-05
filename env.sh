#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "[env.sh] Source this script in the current shell."
  echo "[env.sh] Usage: source ./env.sh"
  exit 1
fi

SCRIPT_SOURCE="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd -L)"
SCRIPT_DIR_PHYSICAL="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd -P)"
CURRENT_DIR_PHYSICAL="$(pwd -P)"

declare -a CANDIDATE_BASES=()
add_candidate_base() {
  local candidate="$1"
  [ -n "$candidate" ] || return
  for base in "${CANDIDATE_BASES[@]}"; do
    [ "$base" = "$candidate" ] && return
  done
  CANDIDATE_BASES+=("$candidate")
}

if [ -n "$PWD" ] && [[ "$PWD" == *"/workspace/"* ]]; then
  add_candidate_base "${PWD%%/workspace/*}"
fi
if [ -n "$CURRENT_DIR_PHYSICAL" ] && [[ "$CURRENT_DIR_PHYSICAL" == *"/workspace/"* ]]; then
  add_candidate_base "${CURRENT_DIR_PHYSICAL%%/workspace/*}"
fi
if [ -n "$SCRIPT_DIR" ] && [[ "$SCRIPT_DIR" == *"/workspace/"* ]]; then
  add_candidate_base "${SCRIPT_DIR%%/workspace/*}"
fi
if [ -n "$SCRIPT_DIR_PHYSICAL" ] && [[ "$SCRIPT_DIR_PHYSICAL" == *"/workspace/"* ]]; then
  add_candidate_base "${SCRIPT_DIR_PHYSICAL%%/workspace/*}"
fi
add_candidate_base "/home/hwi/Project"
add_candidate_base "/data"

pick_tool_home() {
  local relative_path="$1"
  local candidate=""
  for candidate in "${CANDIDATE_BASES[@]}"; do
    if [ -d "$candidate/$relative_path" ]; then
      echo "$candidate/$relative_path"
      return 0
    fi
  done
  return 1
}

# JDK
if JAVA_HOME_PICKED="$(pick_tool_home "jdk-17.0.12")"; then
  export JAVA_HOME="$JAVA_HOME_PICKED"
  export PATH="$JAVA_HOME/bin:$PATH"
fi

# Node
if NODE_HOME_PICKED="$(pick_tool_home "node-v26.3.0")"; then
  export NODE_HOME="$NODE_HOME_PICKED"
  export PATH="$NODE_HOME/bin:$PATH"
fi

# Python
if PY_HOME_PICKED="$(pick_tool_home "Python3.14.5")"; then
  export PY_HOME="$PY_HOME_PICKED"
  export PATH="$PY_HOME/bin:$PATH"
fi

# Compatibility helpers.
if ! command -v python >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  python() {
    command python3 "$@"
  }
fi

if ! command -v pip >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    pip() {
      command python3 -m pip "$@"
    }
  elif command -v pip3 >/dev/null 2>&1; then
    pip() {
      command pip3 "$@"
    }
  fi
fi

# Activate a local virtualenv when present.
[ -d ".venv" ] && . ".venv/bin/activate"

# hwiStock project defaults.
export HWISTOCK_PROJECT_ROOT="$SCRIPT_DIR"
export HWISTOCK_ENV_DIR="${HWISTOCK_ENV_DIR:-$HOME/.config/hwistock}"
export HWISTOCK_DATA_DIR="${HWISTOCK_DATA_DIR:-$HWISTOCK_PROJECT_ROOT/data}"
export HWISTOCK_DOCS_DIR="${HWISTOCK_DOCS_DIR:-$HWISTOCK_PROJECT_ROOT/docs}"
export HWISTOCK_POSTGRES_DB="${HWISTOCK_POSTGRES_DB:-hwistock}"
export HWISTOCK_POSTGRES_SCHEMA="${HWISTOCK_POSTGRES_SCHEMA:-hwistock_core}"

load_hwistock_env_file() {
  local env_file="$1"
  [ -f "$env_file" ] || return 0

  local had_allexport=0
  case "$-" in
    *a*) had_allexport=1 ;;
  esac

  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  if [[ "$had_allexport" -eq 0 ]]; then
    set +a
  fi
}

# Project-local secret/config files. Values are never stored in this repository.
load_hwistock_env_file "$HWISTOCK_ENV_DIR/hwistock.env"
load_hwistock_env_file "$HWISTOCK_ENV_DIR/deepseek.env"
load_hwistock_env_file "$HOME/.config/deepseek.env"
load_hwistock_env_file "$HWISTOCK_ENV_DIR/source-apis.env"
load_hwistock_env_file "$HWISTOCK_ENV_DIR/hwistockApi.env"

unset -f load_hwistock_env_file

echo -e "\n[env.sh] hwiStock environment applied."
echo "[env.sh] PROJECT_ROOT=$HWISTOCK_PROJECT_ROOT"
echo "[env.sh] ENV_DIR=$HWISTOCK_ENV_DIR"
echo "[env.sh] DATA_DIR=$HWISTOCK_DATA_DIR"
echo "[env.sh] POSTGRES_DB=$HWISTOCK_POSTGRES_DB"
echo "[env.sh] POSTGRES_SCHEMA=$HWISTOCK_POSTGRES_SCHEMA"
echo -e "[env.sh] PATH:\n$(echo "$PATH" | tr ':' '\n')\n"
