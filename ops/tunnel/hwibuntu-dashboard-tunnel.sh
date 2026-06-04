#!/usr/bin/env bash
# hwiStock dashboard SSH tunnel helper.
# Run this on hwibuntu, not on the hwiServer service process.
# It keeps hwiStock bound to hwiServer loopback and exposes only local
# hwibuntu loopback ports for browser QA.

set -euo pipefail

REMOTE_HOST="${HWISTOCK_TUNNEL_HOST:-hwiServer}"
LOCAL_FRONTEND_PORT="${HWISTOCK_LOCAL_FRONTEND_PORT:-5000}"
REMOTE_FRONTEND_PORT="${HWISTOCK_REMOTE_FRONTEND_PORT:-5000}"
LOCAL_BACKEND_PORT="${HWISTOCK_LOCAL_BACKEND_PORT:-5001}"
REMOTE_BACKEND_PORT="${HWISTOCK_REMOTE_BACKEND_PORT:-5001}"

exec ssh -N \
  -L "${LOCAL_FRONTEND_PORT}:127.0.0.1:${REMOTE_FRONTEND_PORT}" \
  -L "${LOCAL_BACKEND_PORT}:127.0.0.1:${REMOTE_BACKEND_PORT}" \
  "${REMOTE_HOST}"
