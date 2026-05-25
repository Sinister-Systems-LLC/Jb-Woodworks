#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-25
# Sinister OS — reboot-banner watcher
#
# Watches /var/lib/sinister/reboot-required.json with inotify and republishes
# to the mesh vault-api KV at mesh/banner/reboot-required so the Sinister
# Panel banner component picks it up live. Designed to run as a sinister-eve
# systemd unit (Restart=always).
#
# Deps: inotify-tools, curl
# Vault endpoint defaults to UNIX socket; override via SINISTER_VAULT_URL.
#
# Usage:
#   reboot-banner-watch.sh                # foreground watch
#   reboot-banner-watch.sh --once         # one-shot publish current state

set -euo pipefail

STATE_DIR="/var/lib/sinister"
STATE_FILE="${STATE_DIR}/reboot-required.json"
VAULT_URL="${SINISTER_VAULT_URL:-http://127.0.0.1:5078}"
KV_KEY="mesh/banner/reboot-required"

publish() {
  if [[ ! -f "$STATE_FILE" ]]; then
    curl -fsS -X DELETE "${VAULT_URL}/kv/${KV_KEY}" >/dev/null 2>&1 || true
    echo "banner-watch: cleared ${KV_KEY}"
    return 0
  fi
  payload="$(cat "$STATE_FILE")"
  if ! curl -fsS -X PUT "${VAULT_URL}/kv/${KV_KEY}" \
        -H 'content-type: application/json' \
        --data-binary "$payload" >/dev/null; then
    echo "banner-watch: publish failed (vault unreachable: ${VAULT_URL})" >&2
    return 1
  fi
  echo "banner-watch: published ${KV_KEY} (bytes=${#payload})"
}

if [[ "${1:-}" == "--once" ]]; then
  publish
  exit $?
fi

mkdir -p "$STATE_DIR"
publish || true

if ! command -v inotifywait >/dev/null 2>&1; then
  echo "banner-watch: inotify-tools missing; falling back to 30s poll loop" >&2
  while true; do sleep 30; publish || true; done
fi

inotifywait -m -e close_write,delete,move "$STATE_DIR" --format '%e %f' 2>/dev/null \
  | while read -r ev name; do
      if [[ "$name" == "$(basename "$STATE_FILE")" ]]; then
        publish || true
      fi
    done
