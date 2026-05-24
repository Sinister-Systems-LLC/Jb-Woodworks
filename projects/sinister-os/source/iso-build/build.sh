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

set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

IMAGE_TAG="sinister-os-builder:latest"
OUT_DIR="$(realpath ../../build)"
WORK_DIR_HOST="$(realpath ../../build/_work)"

mkdir -p "$OUT_DIR" "$WORK_DIR_HOST"

echo "==> Verifying Panel bundle is staged..."
if [ ! -f "airootfs/srv/sinister-panel/server.js" ]; then
  echo "!! Panel server.js not found at airootfs/srv/sinister-panel/."
  echo "   Run bake-panel.sh first."
  exit 1
fi

echo "==> Building Docker image $IMAGE_TAG..."
docker build -t "$IMAGE_TAG" .

echo "==> Running mkarchiso inside container..."
docker run --rm --privileged \
  -v "$PWD":/work:ro \
  -v "$WORK_DIR_HOST":/tmp/work \
  -v "$OUT_DIR":/out \
  "$IMAGE_TAG" \
  mkarchiso -v -w /tmp/work -o /out /work

echo "==> Done. ISO at:"
ls -lh "$OUT_DIR"/*.iso || true
