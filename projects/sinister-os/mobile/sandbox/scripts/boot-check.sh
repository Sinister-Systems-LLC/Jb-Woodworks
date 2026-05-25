#!/usr/bin/env bash
# boot-check.sh — smoke-test a booted cvd + record one row in seven-green log
# RKOJ-ELENO :: 2026-05-24

set -euo pipefail

WORKDIR="${SINISTER_CVD_HOME:-$HOME/sinister-cvd}"
LOG="$WORKDIR/seven-green/.seven-green-log.jsonl"
LAST_BUILD="$WORKDIR/builds/.last-build.json"
LOG_PREFIX="[boot-check]"

log()  { echo "${LOG_PREFIX} $*"; }
fail() { echo "${LOG_PREFIX} FAIL: $*" >&2; record "fail" "$*"; exit 1; }

record() {
  local result="$1" reason="${2:-}"
  local sha
  sha="$(jq -r .src_sha "$LAST_BUILD" 2>/dev/null || echo unknown)"
  mkdir -p "$(dirname "$LOG")"
  printf '{"ts_utc":"%s","src_sha":"%s","result":"%s","reason":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$sha" "$result" "${reason//\"/}" \
    >> "$LOG"
}

ADB="adb -s 0.0.0.0:6520"

# Checks (each is a hard gate; any fail records 'fail' + exits)
log "(1/5) adb reachability"
$ADB shell true >/dev/null 2>&1 || fail "adb unreachable"

log "(2/5) uname makes sense"
UNAME="$($ADB shell uname -a)"
[[ -n "$UNAME" ]] || fail "empty uname"
[[ "$UNAME" == *"Linux"* ]] || fail "uname doesn't look like Linux: $UNAME"

log "(3/5) /system mounted readonly"
MOUNT="$($ADB shell mount | grep ' /system ')"
[[ "$MOUNT" == *"ro,"* ]] || fail "/system not mounted ro: $MOUNT"

log "(4/5) Snapchat-relevant services present"
# Play Integrity attestation service + keystore daemon — Snapchat checks both
$ADB shell pgrep -f keystore2 >/dev/null || fail "keystore2 daemon missing"
$ADB shell pgrep -f android.hardware.gatekeeper >/dev/null || fail "gatekeeper HAL missing"

log "(5/5) kernel did NOT panic in last 30s"
DMESG_TAIL="$($ADB shell dmesg | tail -100)"
[[ "$DMESG_TAIL" != *"Kernel panic"* ]] || fail "kernel panic in dmesg tail"

record "pass" "all 5 checks green"
log "OK — 1 boot-check passed"

# Count consecutive passes
CONSEC="$(tac "$LOG" | python3 -c '
import json, sys
n = 0
for line in sys.stdin:
    try:
        if json.loads(line)["result"] == "pass": n += 1
        else: break
    except: break
print(n)
')"
log "consecutive passes: $CONSEC / 7"
[[ "$CONSEC" -ge 7 ]] && log "==> seven-green threshold REACHED. Run scripts/seven-green-gate.sh to confirm + unlock advisory."
