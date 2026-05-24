#!/usr/bin/env bash
# kernel-build.sh — custom kernel build pipeline (cuttlefish-target first, bluejay second)
# RKOJ-ELENO :: 2026-05-24 :: GPL-3.0-or-later
#
# Build the Sinister OS Mobile custom kernel. Two targets, gated:
#   - vsoc_x86_64  (cuttlefish virtual device — always-allowed; the sandbox target)
#   - bluejay      (Pixel 6a — gated by --target=bluejay flag AND 7-green cvd record)
#
# Inputs:
#   $SINISTER_CVD_HOME/builds/sinister-kernel-src/  (kernel src checkout; created on first run via 'repo')
#   $SINISTER_CVD_HOME/builds/patches/              (Sinister patch series; empty in P0/P1, populated at P4)
#
# Outputs:
#   $SINISTER_CVD_HOME/builds/out-<target>/<artifacts>
#   $SINISTER_CVD_HOME/builds/.last-build.json      (target, sha, ts, size, kbuild_warnings)
#
# Anti-brick: this script produces artifacts but DOES NOT flash anything. The cvd
# boot path (boot-cuttlefish.sh) consumes the vsoc_x86_64 artifact. The bluejay
# artifact is operator-pickup-only.

set -euo pipefail

WORKDIR="${SINISTER_CVD_HOME:-$HOME/sinister-cvd}"
SRC_DIR="$WORKDIR/builds/sinister-kernel-src"
PATCH_DIR="$WORKDIR/builds/patches"
OUT_BASE="$WORKDIR/builds"
LAST_BUILD="$OUT_BASE/.last-build.json"

TARGET="${1:-vsoc_x86_64}"     # default sandbox target
DRY_RUN="${DRY_RUN:-0}"
LOG_PREFIX="[kernel-build]"

log()  { echo "${LOG_PREFIX} $*"; }
fail() { echo "${LOG_PREFIX} FAIL: $*" >&2; exit 1; }

case "$TARGET" in
  vsoc_x86_64) ARCH=x86_64; KERNEL_BRANCH="common-android14-6.1"; CONFIG="cuttlefish_defconfig" ;;
  bluejay)     ARCH=arm64;  KERNEL_BRANCH="android-gs-bluejay-5.10"; CONFIG="bluejay_defconfig"
               [[ "${ALLOW_BLUEJAY:-0}" == "1" ]] || fail "bluejay target gated — set ALLOW_BLUEJAY=1 only after 7-green-gate.sh passes on vsoc_x86_64" ;;
  *) fail "unknown target: $TARGET (allowed: vsoc_x86_64, bluejay)" ;;
esac

mkdir -p "$OUT_BASE" "$SRC_DIR" "$PATCH_DIR"
OUT_DIR="$OUT_BASE/out-$TARGET"
mkdir -p "$OUT_DIR"

# ----- Fetch sources -----------------------------------------------------------

if [[ ! -d "$SRC_DIR/.repo" ]]; then
  log "first run for $TARGET — initialising kernel manifest ($KERNEL_BRANCH)"
  if [[ "$DRY_RUN" == "1" ]]; then
    log "DRY_RUN=1 — skipping 'repo init' (would init https://android.googlesource.com/kernel/manifest -b $KERNEL_BRANCH)"
  else
    command -v repo >/dev/null || fail "'repo' tool not found — install per https://source.android.com/docs/setup/download#installing-repo"
    (cd "$SRC_DIR" && repo init --depth=1 -u https://android.googlesource.com/kernel/manifest -b "$KERNEL_BRANCH")
    (cd "$SRC_DIR" && repo sync -j"$(nproc 2>/dev/null || echo 4)")
  fi
else
  log "kernel src already initialised at $SRC_DIR"
fi

# ----- Apply Sinister patches -------------------------------------------------

if compgen -G "$PATCH_DIR/*.patch" >/dev/null; then
  log "applying Sinister patches from $PATCH_DIR"
  if [[ "$DRY_RUN" == "1" ]]; then
    log "DRY_RUN=1 — would apply: $(ls "$PATCH_DIR"/*.patch | wc -l) patches"
  else
    for p in "$PATCH_DIR"/*.patch; do
      log "  applying $(basename "$p")"
      (cd "$SRC_DIR" && git apply --check "$p") || fail "patch $p does not apply cleanly"
      (cd "$SRC_DIR" && git apply "$p")
    done
  fi
else
  log "no Sinister patches yet ($PATCH_DIR is empty) — building vanilla GKI (P0/P1 baseline)"
fi

# ----- Build ------------------------------------------------------------------

log "building target=$TARGET arch=$ARCH config=$CONFIG"
if [[ "$DRY_RUN" == "1" ]]; then
  log "DRY_RUN=1 — would invoke: BUILD_CONFIG=common/build.config.gki.${ARCH} build/build.sh"
  echo "{ \"target\": \"$TARGET\", \"sha\": \"DRY_RUN\", \"ts\": \"$(date -u +%Y-%m-%dT%H%MZ)\", \"size\": 0, \"warnings\": 0 }" > "$LAST_BUILD"
  log "dry-run complete; wrote $LAST_BUILD"
  exit 0
fi

START_SHA="$(cd "$SRC_DIR" && git rev-parse --short HEAD 2>/dev/null || echo unknown)"
BUILD_LOG="$OUT_DIR/build-$(date -u +%Y%m%dT%H%MZ).log"

(
  cd "$SRC_DIR"
  BUILD_CONFIG="common/build.config.gki.${ARCH}" \
  OUT_DIR="$OUT_DIR" \
  build/build.sh 2>&1 | tee "$BUILD_LOG"
) || fail "build failed; see $BUILD_LOG"

# ----- Collect artifacts -------------------------------------------------------

if [[ -f "$OUT_DIR/dist/Image" ]]; then
  IMG="$OUT_DIR/dist/Image"
elif [[ -f "$OUT_DIR/dist/bzImage" ]]; then
  IMG="$OUT_DIR/dist/bzImage"
else
  fail "no kernel image found in $OUT_DIR/dist/"
fi

SIZE="$(stat -c%s "$IMG")"
WARNINGS="$(grep -c "warning:" "$BUILD_LOG" 2>/dev/null || echo 0)"
END_TS="$(date -u +%Y-%m-%dT%H%MZ)"

cat > "$LAST_BUILD" <<EOF
{
  "target": "$TARGET",
  "arch": "$ARCH",
  "config": "$CONFIG",
  "kernel_branch": "$KERNEL_BRANCH",
  "src_sha": "$START_SHA",
  "image": "$IMG",
  "size_bytes": $SIZE,
  "build_log": "$BUILD_LOG",
  "kbuild_warnings": $WARNINGS,
  "built_at": "$END_TS"
}
EOF

log "build OK"
log "  image: $IMG ($SIZE bytes)"
log "  warnings: $WARNINGS"
log "  metadata: $LAST_BUILD"
log ""
log "next:"
log "  bash scripts/boot-cuttlefish.sh   # boots vsoc with this kernel"
log "  bash scripts/boot-check.sh        # smoke-tests + records 1/7"
