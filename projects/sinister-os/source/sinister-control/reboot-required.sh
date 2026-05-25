#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-25
# Sinister OS — reboot-required write-side
#
# Emits a structured record to /var/lib/sinister/reboot-required.json so the
# panel banner watcher (see reboot-banner-watch.sh) can surface it to the
# operator without needing to actually reboot until the operator chooses.
#
# Usage:
#   reboot-required.sh <reason> [--severity advisory|recommended|required] [--component <name>]
#
# Examples:
#   reboot-required.sh "kernel.upgrade 6.10.4 -> 6.10.7" --severity required --component kernel
#   reboot-required.sh "systemd-boot config change" --severity recommended --component bootloader
#
# Exit codes:
#   0  wrote/updated record
#   2  missing reason
#   3  write failed (permissions)

set -euo pipefail

STATE_DIR="/var/lib/sinister"
STATE_FILE="${STATE_DIR}/reboot-required.json"

reason="${1:-}"
shift || true

severity="recommended"
component="unknown"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --severity) severity="$2"; shift 2 ;;
    --component) component="$2"; shift 2 ;;
    *) echo "reboot-required: unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$reason" ]]; then
  echo "usage: reboot-required.sh <reason> [--severity advisory|recommended|required] [--component <name>]" >&2
  exit 2
fi

case "$severity" in advisory|recommended|required) ;; *) echo "bad severity: $severity" >&2; exit 2 ;; esac

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
host="$(hostname -s 2>/dev/null || echo unknown)"

mkdir -p "$STATE_DIR" || { echo "cannot mkdir $STATE_DIR" >&2; exit 3; }

tmp="$(mktemp)"
cat > "$tmp" <<JSON
{
  "schema": "sinister.reboot-required.v1",
  "host": "${host}",
  "ts_utc": "${ts}",
  "severity": "${severity}",
  "component": "${component}",
  "reason": "${reason}",
  "acked_by_operator": false
}
JSON

mv "$tmp" "$STATE_FILE" || { echo "cannot write $STATE_FILE" >&2; exit 3; }
chmod 0644 "$STATE_FILE"

echo "reboot-required: wrote ${STATE_FILE} (severity=${severity} component=${component})"
