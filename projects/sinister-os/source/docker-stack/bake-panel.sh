#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-24
#
# bake-panel.sh — Scaffold a real Panel image bake.
#
# Intent:
#   The docker-compose.yml ships Panel as a `node:22-alpine` container that
#   runs an inline-generated placeholder server.js when no /app/server.js is
#   mounted. This script REPLACES that placeholder by building a real Docker
#   image from the operator's `sinister-panel` project source tree.
#
#   Honesty note (no-bullshit doctrine 2026-05-23):
#     This script SCAFFOLDS the bake. It does NOT guarantee a working Panel
#     image — that depends entirely on the state of $PANEL_SRC (must contain
#     a valid Dockerfile + buildable app). If the operator's sinister-panel
#     repo lacks a Dockerfile, this script reports the gap and exits.
#
# Invoke:
#   ./bake-panel.sh                # full bake (build the image)
#   ./bake-panel.sh --verify       # only check PANEL_SRC + Dockerfile exist
#   ./bake-panel.sh --dry-run      # print the planned build command, no build
#
# Env overrides:
#   SANCTUM_ROOT   default: /d/Sinister Sanctum
#   PANEL_SRC      default: $SANCTUM_ROOT/projects/sinister-panel
#   PANEL_TAG      default: sinister/panel:local-$(date +%Y%m%d)
#
# Composition with docker-compose:
#   After a successful bake, drop a `compose.panel-local.yml` overlay (this
#   script prints the suggested overlay snippet) and bring the stack up via:
#     docker compose -f docker-compose.yml -f compose.panel-local.yml up -d panel

set -euo pipefail

cd "$(dirname "$0")"

# -------- defaults / env --------
SANCTUM_ROOT="${SANCTUM_ROOT:-/d/Sinister Sanctum}"
PANEL_SRC="${PANEL_SRC:-$SANCTUM_ROOT/projects/sinister-panel}"
PANEL_TAG="${PANEL_TAG:-sinister/panel:local-$(date +%Y%m%d)}"

MODE="bake"
for arg in "$@"; do
  case "$arg" in
    --verify)   MODE="verify" ;;
    --dry-run)  MODE="dryrun" ;;
    -h|--help)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *)
      echo "bake-panel.sh: unknown flag: $arg" >&2
      echo "  usage: bake-panel.sh [--verify | --dry-run]" >&2
      exit 2
      ;;
  esac
done

echo "[bake-panel] SANCTUM_ROOT=$SANCTUM_ROOT"
echo "[bake-panel] PANEL_SRC   =$PANEL_SRC"
echo "[bake-panel] PANEL_TAG   =$PANEL_TAG"
echo "[bake-panel] MODE        =$MODE"

# -------- preflight --------
DOCKERFILE="$PANEL_SRC/Dockerfile"
PANEL_SRC_OK=0
DOCKERFILE_OK=0
[ -d "$PANEL_SRC" ] && PANEL_SRC_OK=1
[ -f "$DOCKERFILE" ] && DOCKERFILE_OK=1

if [ "$PANEL_SRC_OK" = "1" ]; then
  echo "[bake-panel] PANEL_SRC : present"
else
  echo "[bake-panel] PANEL_SRC : MISSING ($PANEL_SRC)"
fi

if [ "$DOCKERFILE_OK" = "1" ]; then
  echo "[bake-panel] Dockerfile: present ($DOCKERFILE)"
else
  echo "[bake-panel] Dockerfile: MISSING ($DOCKERFILE)"
fi

# --verify is a status-only reporter: always exits 0 after printing what it
# found. Use this mode to detect-without-failing-CI whether the operator's
# panel project is ready to bake.
if [ "$MODE" = "verify" ]; then
  echo "[bake-panel] --verify: reported status; exiting cleanly."
  exit 0
fi

# For dryrun + full bake, missing prerequisites are hard errors.
if [ "$PANEL_SRC_OK" = "0" ]; then
  echo "" >&2
  echo "[bake-panel] ERROR: PANEL_SRC does not exist: $PANEL_SRC" >&2
  echo "  Hint: clone the operator's sinister-panel repo into:" >&2
  echo "    $PANEL_SRC" >&2
  echo "  or override PANEL_SRC=/path/to/sinister-panel ./bake-panel.sh" >&2
  exit 1
fi

if [ "$DOCKERFILE_OK" = "0" ]; then
  echo "" >&2
  echo "[bake-panel] ERROR: no Dockerfile at: $DOCKERFILE" >&2
  echo "  The sinister-panel project must ship a Dockerfile at its root." >&2
  echo "  Until that lands, the placeholder Panel in docker-compose.yml stays." >&2
  exit 1
fi

echo "[bake-panel] preflight OK: PANEL_SRC + Dockerfile present"

# -------- planned command --------
BUILD_CMD=(docker build -t "$PANEL_TAG" "$PANEL_SRC")

echo "[bake-panel] planned build command:"
echo "  ${BUILD_CMD[*]}"

# -------- overlay snippet --------
OVERLAY_FILE="compose.panel-local.yml"
read -r -d '' OVERLAY_SNIPPET <<EOF || true
# $OVERLAY_FILE — overlay to consume the locally-baked Panel image.
# Drop this next to docker-compose.yml and bring up with:
#   docker compose -f docker-compose.yml -f $OVERLAY_FILE up -d panel
name: sinister-mesh
services:
  panel:
    image: $PANEL_TAG
    # The base compose.yml's inline placeholder command is overridden
    # by the image's own ENTRYPOINT/CMD when no command: is set here.
    command: []
    volumes: []
EOF

echo ""
echo "[bake-panel] suggested overlay (drop into $OVERLAY_FILE):"
echo "----------------------------------------"
echo "$OVERLAY_SNIPPET"
echo "----------------------------------------"

if [ "$MODE" = "dryrun" ]; then
  echo "[bake-panel] --dry-run: skipping build."
  exit 0
fi

# -------- the actual bake --------
if ! command -v docker >/dev/null 2>&1; then
  echo "[bake-panel] ERROR: docker not found on PATH" >&2
  exit 1
fi

echo "[bake-panel] running build..."
if "${BUILD_CMD[@]}"; then
  echo "[bake-panel] BAKED: $PANEL_TAG"
  echo "[bake-panel] next: write $OVERLAY_FILE (snippet above) and run:"
  echo "  docker compose -f docker-compose.yml -f $OVERLAY_FILE up -d panel"
  exit 0
else
  rc=$?
  echo "[bake-panel] ERROR: docker build failed (exit $rc)" >&2
  exit "$rc"
fi
