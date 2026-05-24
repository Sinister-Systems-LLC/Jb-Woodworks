#!/usr/bin/env bash
# build.sh — one-command Sinister OS ISO builder (Docker-driven)
# Author: RKOJ-ELENO :: 2026-05-24
#
# Pre-reqs (must be true before running):
#   - Docker Desktop is installed and running
#   - You are at: projects/sinister-os/source/iso-build/
#   - The Sinister Panel Next.js standalone build exists at
#     ../../source/iso-build/airootfs/srv/sinister-panel/server.js
#     (bake-panel.sh produces it; run that first if it isn't there yet)
#
# Output: ../../build/sinister-os-<version>-x86_64.iso
#
# Safety fix 2026-05-24 (RKOJ-ELENO): SLIM-WIRING — operator directive
# "make sure everything is fast efficient and only include the shit i need".
# By default this script feeds mkarchiso the LEAN list (packages.x86_64.slim,
# ~85 packages) instead of the legacy 109-package packages.x86_64. The 17
# deferred packages (discord, obs-studio, lutris, wine-staging, winetricks,
# vulkan-tools, openrgb, zen-browser-bin, etc.) install on first boot via
# sinister-first-boot-install-deferred.sh after network is up.
#
# Environment overrides:
#   SINISTER_PACKAGES=slim   (default) — feed packages.x86_64.slim (lean ~85)
#   SINISTER_PACKAGES=fat              — feed the legacy 109-line packages.x86_64
#   SINISTER_PACKAGES=auto             — prefer .slim if present, else fallback to packages.x86_64
#
# Implementation note: mkarchiso hard-reads the file named exactly
# "packages.x86_64" from the profile dir. We stage a writable build context
# under build/_stage so we can swap the file in without mutating the source
# tree. The original files (packages.x86_64, packages.x86_64.slim,
# packages.x86_64.removed) are NEVER touched.

set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

IMAGE_TAG="sinister-os-builder:latest"
OUT_DIR="$(realpath ../../build)"
WORK_DIR_HOST="$(realpath ../../build/_work)"
# Safety fix 2026-05-24 (RKOJ-ELENO): writable build-context staging dir so we
# can swap the package list without modifying the source tree.
STAGE_DIR="$(realpath ../../build)/_stage"

mkdir -p "$OUT_DIR" "$WORK_DIR_HOST" "$STAGE_DIR"

echo "==> Verifying Panel bundle is staged..."
if [ ! -f "airootfs/srv/sinister-panel/server.js" ]; then
  echo "!! Panel server.js not found at airootfs/srv/sinister-panel/."
  echo "   Run bake-panel.sh first."
  exit 1
fi

# Safety fix 2026-05-24 (RKOJ-ELENO): select the package list per
# SINISTER_PACKAGES env var (default = slim).
SINISTER_PACKAGES="${SINISTER_PACKAGES:-slim}"
case "$SINISTER_PACKAGES" in
  slim)
    if [ ! -f "packages.x86_64.slim" ]; then
      echo "!! SINISTER_PACKAGES=slim but packages.x86_64.slim not found. Aborting."
      exit 1
    fi
    PKG_SRC="packages.x86_64.slim"
    ;;
  fat)
    if [ ! -f "packages.x86_64" ]; then
      echo "!! SINISTER_PACKAGES=fat but packages.x86_64 not found. Aborting."
      exit 1
    fi
    PKG_SRC="packages.x86_64"
    ;;
  auto)
    if [ -f "packages.x86_64.slim" ]; then
      PKG_SRC="packages.x86_64.slim"
    elif [ -f "packages.x86_64" ]; then
      PKG_SRC="packages.x86_64"
    else
      echo "!! SINISTER_PACKAGES=auto and neither packages.x86_64.slim nor packages.x86_64 exists. Aborting."
      exit 1
    fi
    ;;
  *)
    echo "!! Unknown SINISTER_PACKAGES=$SINISTER_PACKAGES (expected: slim|fat|auto)."
    exit 1
    ;;
esac
echo "==> SINISTER_PACKAGES=$SINISTER_PACKAGES -> feeding mkarchiso: $PKG_SRC"

# Safety fix 2026-05-24 (RKOJ-ELENO): stage the build context. Copy the
# profile to STAGE_DIR, then drop the chosen list in as packages.x86_64.
# Using rsync-equivalent cp -a; excludes the build output and stage dirs
# in case they live underneath (defensive — they don't currently).
rm -rf "$STAGE_DIR"/*
cp -a ./. "$STAGE_DIR"/
# Remove any sibling lists from the stage so only the canonical name remains
rm -f "$STAGE_DIR/packages.x86_64" "$STAGE_DIR/packages.x86_64.slim" "$STAGE_DIR/packages.x86_64.removed"
cp -f "$PKG_SRC" "$STAGE_DIR/packages.x86_64"

echo "==> Building Docker image $IMAGE_TAG..."
docker build -t "$IMAGE_TAG" .

echo "==> Running mkarchiso inside container..."
docker run --rm --privileged \
  -v "$STAGE_DIR":/work:ro \
  -v "$WORK_DIR_HOST":/tmp/work \
  -v "$OUT_DIR":/out \
  "$IMAGE_TAG" \
  mkarchiso -v -w /tmp/work -o /out /work

echo "==> Done. ISO at:"
ls -lh "$OUT_DIR"/*.iso || true
