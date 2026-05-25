#!/usr/bin/env bash
# sinister-tailscale-firstboot.sh
# Author: RKOJ-ELENO :: 2026-05-24
#
# Auto-authenticates this host to the operator's tailnet on first successful
# start of tailscaled. Invoked as ExecStartPost from the sinister.conf drop-in
# at /etc/systemd/system/tailscaled.service.d/sinister.conf.
#
# Contract:
#   - No-op if the authkey file is absent or contains only whitespace.
#   - Reads optional TS_EXTRA_ARGS from /etc/sinister/eve.toml (sed/awk only;
#     no TOML parser dep). The expected line shape is:
#         ts_extra_args = "--advertise-exit-node --advertise-tags=tag:server"
#   - Runs `tailscale up --authkey=<key> --hostname=$(hostname) $TS_EXTRA_ARGS`.
#   - On success (`tailscale status` exit 0), self-deletes the authkey file so
#     the secret does not linger on disk.
#   - Logs to journald via `logger`. journalctl -u tailscaled shows it.
#   - Idempotent: if the node is already up, exits 0 without re-running.

set -euo pipefail

AUTHKEY_FILE=/etc/sinister/tailscale-authkey
EVE_TOML=/etc/sinister/eve.toml
LOG_TAG=sinister-tailscale-firstboot

log() {
    logger -t "$LOG_TAG" -- "$*" || true
    # also echo for journalctl -u tailscaled visibility when run via ExecStartPost
    echo "$LOG_TAG: $*" >&2
}

# --- 0. Bail early if already authenticated ------------------------------
if /usr/bin/tailscale status --peers=false >/dev/null 2>&1; then
    log "already authenticated to tailnet; nothing to do"
    # Defensive: if a stale authkey file is sitting around, remove it.
    if [ -s "$AUTHKEY_FILE" ]; then
        rm -f "$AUTHKEY_FILE" || true
        log "removed stale authkey file post-auth"
    fi
    exit 0
fi

# --- 1. No-op if the authkey file is empty / absent ----------------------
if [ ! -s "$AUTHKEY_FILE" ]; then
    log "no authkey at $AUTHKEY_FILE (or empty); skipping auto-join"
    exit 0
fi

AUTHKEY="$(tr -d '[:space:]' < "$AUTHKEY_FILE")"
if [ -z "$AUTHKEY" ]; then
    log "authkey file present but whitespace-only; skipping auto-join"
    exit 0
fi

# --- 2. Optional TS_EXTRA_ARGS from /etc/sinister/eve.toml ---------------
TS_EXTRA_ARGS=""
if [ -r "$EVE_TOML" ]; then
    # Extract: ts_extra_args = "..." (handles single/double quotes, leading whitespace)
    # Take the first match only.
    TS_EXTRA_ARGS="$(
        sed -n -E 's/^[[:space:]]*ts_extra_args[[:space:]]*=[[:space:]]*"([^"]*)".*/\1/p; s/^[[:space:]]*ts_extra_args[[:space:]]*=[[:space:]]*'\''([^'\'']*)'\''.*/\1/p' "$EVE_TOML" | head -n 1
    )"
fi

HOSTNAME_VAL="$(hostname)"

log "joining tailnet as host=$HOSTNAME_VAL extra_args=[$TS_EXTRA_ARGS]"

# --- 3. Bring up the node ------------------------------------------------
# `tailscale up` is itself idempotent — re-running with the same args is safe.
# shellcheck disable=SC2086  # we WANT word-splitting on TS_EXTRA_ARGS
if /usr/bin/tailscale up \
        --authkey="$AUTHKEY" \
        --hostname="$HOSTNAME_VAL" \
        ${TS_EXTRA_ARGS}; then
    log "tailscale up returned 0"
else
    rc=$?
    log "tailscale up failed rc=$rc; leaving authkey in place for retry"
    exit $rc
fi

# --- 4. Confirm + self-delete the authkey --------------------------------
if /usr/bin/tailscale status --peers=false >/dev/null 2>&1; then
    rm -f "$AUTHKEY_FILE" || true
    log "tailnet join confirmed; authkey file removed"
    exit 0
else
    log "tailscale up returned 0 but status check failed; authkey retained for retry"
    exit 1
fi
