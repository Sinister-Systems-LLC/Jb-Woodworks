#!/usr/bin/env bash
# post-install-smoke.sh — verify sinister-eve is alive on a freshly-installed Sinister OS.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Run inside the installed Sinister OS (NOT the live ISO) after first boot:
#     bash /usr/lib/sinister-eve/post-install-smoke.sh
# or from the overlay source tree during development:
#     bash projects/sinister-os/source/eve-os-integration/scaffold/post-install-smoke.sh
#
# Exit codes:
#   0  all checks PASS
#   1  systemd unit not active
#   2  HTTP /health did not respond
#   3  HTTP /health responded but JSON missing expected keys
#   4  required tools (curl, systemctl) missing

set -uo pipefail

# Colors — quiet on dumb terminals.
if [[ -t 1 ]] && [[ "${TERM:-dumb}" != "dumb" ]]; then
  C_OK='\033[1;32m'; C_ERR='\033[1;31m'; C_INFO='\033[1;35m'; C_OFF='\033[0m'
else
  C_OK=''; C_ERR=''; C_INFO=''; C_OFF=''
fi
ok()   { printf '%b[ OK ]%b %s\n' "$C_OK"   "$C_OFF" "$*"; }
fail() { printf '%b[FAIL]%b %s\n' "$C_ERR"  "$C_OFF" "$*" >&2; }
info() { printf '%b[ -- ]%b %s\n' "$C_INFO" "$C_OFF" "$*"; }

# --- prereqs ---
for bin in systemctl curl; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    fail "$bin not on PATH — cannot run smoke test"
    exit 4
  fi
done

# --- 1. systemctl status ---
info "1/3 — systemctl status sinister-eve --no-pager"
systemctl status sinister-eve --no-pager || true
if ! systemctl is-active --quiet sinister-eve.service; then
  fail "sinister-eve.service is NOT active"
  info "    journalctl -u sinister-eve --no-pager | tail -30"
  journalctl -u sinister-eve --no-pager 2>/dev/null | tail -30 || true
  exit 1
fi
ok "sinister-eve.service is active"

# --- 2. HTTP /health ---
info "2/3 — curl http://127.0.0.1:7331/health"
HEALTH_BODY="$(curl --silent --show-error --max-time 5 http://127.0.0.1:7331/health 2>&1)"
HEALTH_RC=$?
if [[ $HEALTH_RC -ne 0 ]] || [[ -z "$HEALTH_BODY" ]]; then
  fail "/health did not respond (curl exit $HEALTH_RC)"
  printf '%s\n' "$HEALTH_BODY"
  exit 2
fi
printf '  %s\n' "$HEALTH_BODY"
ok "/health responded"

# --- 3. shape-check the JSON (ok / tools / memory keys expected) ---
info "3/3 — minimal JSON shape check"
for key in '"ok"' '"tools"' '"memory"'; do
  if ! grep -q "$key" <<<"$HEALTH_BODY"; then
    fail "/health JSON missing key $key"
    exit 3
  fi
done
ok "/health JSON contains ok + tools + memory"

printf '\n%bPASS%b — sinister-eve is alive on this Sinister OS install.\n' "$C_OK" "$C_OFF"
exit 0
