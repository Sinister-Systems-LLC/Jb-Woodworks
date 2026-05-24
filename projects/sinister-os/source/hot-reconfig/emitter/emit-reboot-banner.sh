#!/usr/bin/env bash
# emit-reboot-banner.sh — atomic update of /var/lib/sinister/reboot-required.json.
# Author: RKOJ-ELENO :: 2026-05-24
# Status: SCAFFOLDED. Parse-clean; not installed.
#
# Usage:
#   emit-reboot-banner.sh add <trigger> <reason>   # appends a reason, sets required=true
#   emit-reboot-banner.sh clear                    # resets to empty state (operator-run after reboot)
#   emit-reboot-banner.sh snooze <hours>           # writes snooze_until = now + N hours
#   emit-reboot-banner.sh status                   # prints current JSON to stdout

set -euo pipefail

readonly STATE_FILE="${SINISTER_BANNER_STATE:-/var/lib/sinister/reboot-required.json}"
readonly LOCK_FILE="${STATE_FILE}.lock"

ensure_state() {
    if [ ! -f "${STATE_FILE}" ]; then
        mkdir -p "$(dirname "${STATE_FILE}")"
        cat > "${STATE_FILE}" <<'EMPTY'
{"required": false, "severity": "info", "reasons": [], "kexec_capable": false, "snooze_until": null}
EMPTY
    fi
}

with_lock() {
    # flock holds an exclusive lock for the duration of the subcommand.
    exec 9>"${LOCK_FILE}"
    flock 9
    "$@"
}

cmd_add() {
    local trigger="$1"
    local reason="$2"
    local now
    now="$(date -uIs)"
    local tmp="${STATE_FILE}.tmp"
    jq --arg t "${trigger}" --arg r "${reason}" --arg n "${now}" \
       '.required = true | .reasons += [{trigger:$t, reason:$r, since_utc:$n}]' \
       "${STATE_FILE}" > "${tmp}"
    mv -f "${tmp}" "${STATE_FILE}"
    # Best-effort journal hint; survives if not running under systemd-notify.
    command -v systemd-notify >/dev/null 2>&1 && systemd-notify --status="reboot pending: ${reason}" || true
}

cmd_clear() {
    local tmp="${STATE_FILE}.tmp"
    cat > "${tmp}" <<'EMPTY'
{"required": false, "severity": "info", "reasons": [], "kexec_capable": false, "snooze_until": null}
EMPTY
    mv -f "${tmp}" "${STATE_FILE}"
}

cmd_snooze() {
    local hours="$1"
    local until_iso
    until_iso="$(date -uIs -d "+${hours} hours" 2>/dev/null || date -uIs)"
    local tmp="${STATE_FILE}.tmp"
    jq --arg u "${until_iso}" '.snooze_until = $u' "${STATE_FILE}" > "${tmp}"
    mv -f "${tmp}" "${STATE_FILE}"
}

cmd_status() {
    cat "${STATE_FILE}"
}

main() {
    ensure_state
    local sub="${1:-status}"; shift || true
    case "${sub}" in
        add)     [ "$#" -ge 2 ] || { echo "usage: $0 add <trigger> <reason>" >&2; exit 2; }
                 with_lock cmd_add "$@" ;;
        clear)   with_lock cmd_clear ;;
        snooze)  [ "$#" -ge 1 ] || { echo "usage: $0 snooze <hours>" >&2; exit 2; }
                 with_lock cmd_snooze "$@" ;;
        status)  cmd_status ;;
        *)       echo "usage: $0 {add|clear|snooze|status}" >&2; exit 2 ;;
    esac
}

main "$@"
