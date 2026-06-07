#!/usr/bin/env bash
# Normalize hwiStock runtime mode for systemd-launched services.
#
# The canonical switch is HWISTOCK_INVESTMENT_MODE=paper|live.
# Paper/mock mode is always KRX-only and NXT-disabled; live mode still defaults
# to KRX-only until a future owner-approved Ready-Set enables NXT routing.

set -euo pipefail

_hwistock_normalize_investment_mode() {
  local raw="${1:-}"
  raw="${raw,,}"
  raw="${raw//-/_}"
  case "$raw" in
    live|real|real_investment|prod|production|cash)
      printf 'live'
      ;;
    *)
      printf 'paper'
      ;;
  esac
}

_mode_source="${HWISTOCK_INVESTMENT_MODE:-${HWISTOCK_KIS_INVESTMENT_MODE:-${HWISTOCK_TRADING_MODE:-paper}}}"
_investment_mode="$(_hwistock_normalize_investment_mode "$_mode_source")"

export HWISTOCK_INVESTMENT_MODE="$_investment_mode"
export HWISTOCK_MARKET_ANALYSIS_FEED_MODE="${HWISTOCK_MARKET_ANALYSIS_FEED_MODE:-integrated}"
export HWISTOCK_KIS_MARKET_ANALYSIS_FEED_MODE="${HWISTOCK_KIS_MARKET_ANALYSIS_FEED_MODE:-$HWISTOCK_MARKET_ANALYSIS_FEED_MODE}"

if [[ "$HWISTOCK_INVESTMENT_MODE" == "paper" ]]; then
  export HWISTOCK_KIS_INVESTMENT_MODE="paper"
  export HWISTOCK_EXECUTION_VENUE_MODE="krx_only"
  export HWISTOCK_KIS_EXECUTION_VENUE_MODE="krx_only"
  export HWISTOCK_NXT_ENABLED="false"
  export HWISTOCK_NXT_READY_SET_APPROVED="false"
else
  export HWISTOCK_KIS_INVESTMENT_MODE="${HWISTOCK_KIS_INVESTMENT_MODE:-live}"
  export HWISTOCK_EXECUTION_VENUE_MODE="${HWISTOCK_EXECUTION_VENUE_MODE:-krx_only}"
  export HWISTOCK_KIS_EXECUTION_VENUE_MODE="${HWISTOCK_KIS_EXECUTION_VENUE_MODE:-$HWISTOCK_EXECUTION_VENUE_MODE}"
  export HWISTOCK_NXT_ENABLED="${HWISTOCK_NXT_ENABLED:-false}"
  export HWISTOCK_NXT_READY_SET_APPROVED="${HWISTOCK_NXT_READY_SET_APPROVED:-false}"
fi
