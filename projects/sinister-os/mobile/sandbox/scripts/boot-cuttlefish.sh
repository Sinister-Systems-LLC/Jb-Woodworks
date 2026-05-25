#!/usr/bin/env bash
# boot-cuttlefish.sh — start a fresh cvd instance using the most-recently-built kernel
# RKOJ-ELENO :: 2026-05-24
#
# Reads $WORKDIR/builds/.last-build.json to find the kernel image, then starts
# cvd with --kernel_path=<image>. Each invocation gets its own cvd instance
# (cvd handles parallel instances natively).
#
# Anti-brick: cvd is a userspace VM. The worst a bad kernel can do here is
# refuse to boot the VM. Physical hardware never touched.

set -euo pipefail

WORKDIR="${SINISTER_CVD_HOME:-$HOME/sinister-cvd}"
LAST_BUILD="$WORKDIR/builds/.last-build.json"
LOG_PREFIX="[boot-cuttlefish]"

log()  { echo "${LOG_PREFIX} $*"; }
fail() { echo "${LOG_PREFIX} FAIL: $*" >&2; exit 1; }

[[ -f "$LAST_BUILD" ]] || fail "no last-build metadata at $LAST_BUILD — run scripts/kernel-build.sh first"
command -v jq >/dev/null || fail "jq not on PATH — apt install jq"
command -v cvd >/dev/null || fail "cvd not on PATH — re-run cuttlefish-setup.sh + relogin"

TARGET="$(jq -r .target "$LAST_BUILD")"
IMAGE="$(jq -r .image "$LAST_BUILD")"
SHA="$(jq -r .src_sha "$LAST_BUILD")"

[[ "$TARGET" == "vsoc_x86_64" ]] || fail "last build target is '$TARGET' — only vsoc_x86_64 boots in cvd; rebuild with: kernel-build.sh vsoc_x86_64"
[[ -f "$IMAGE" ]] || fail "kernel image missing: $IMAGE"

log "booting cvd with kernel: $IMAGE (src_sha=$SHA)"

# cvd flags chosen for fast boot + headless + EVE-controllable:
#   --kernel_path=<img>       : use our custom kernel instead of cvd default
#   --num_instances=1         : single instance per invocation
#   --report_anonymous_usage_stats=n : no telemetry
#   --console=true            : pipe kernel console to a file for boot-check
cvd start \
  --kernel_path="$IMAGE" \
  --num_instances=1 \
  --report_anonymous_usage_stats=n \
  --console=true \
  --daemon

CVD_RUNTIME="$HOME/cuttlefish/instances/cvd-1"
log "cvd start issued; waiting up to 90s for adb"

for i in $(seq 1 90); do
  if adb -s 0.0.0.0:6520 shell true 2>/dev/null; then
    log "adb up on 0.0.0.0:6520 after ${i}s"
    break
  fi
  sleep 1
done

adb -s 0.0.0.0:6520 shell true 2>/dev/null \
  || fail "adb never came up — check $CVD_RUNTIME/logs/kernel.log"

UNAME="$(adb -s 0.0.0.0:6520 shell uname -a)"
log "boot OK"
log "  uname -a: $UNAME"
log ""
log "next:"
log "  bash scripts/boot-check.sh    # records pass/fail to seven-green log"
