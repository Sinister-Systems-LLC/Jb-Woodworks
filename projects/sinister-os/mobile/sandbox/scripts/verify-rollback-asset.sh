#!/usr/bin/env bash
# verify-rollback-asset.sh — Gate 4 (anti-brick): rollback asset present + hash valid
# RKOJ-ELENO :: 2026-05-24
set -euo pipefail

WORKDIR="${SINISTER_CVD_HOME:-$HOME/sinister-cvd}"
ROLLBACK_DIR="$WORKDIR/rollback"
ASSET="$ROLLBACK_DIR/bluejay-stock-boot.img"
HASHFILE="${ASSET}.sha256"

if [[ ! -f "$ASSET" ]]; then
  echo "FAIL: $ASSET missing — operator must drop the stock boot.img here (see $ROLLBACK_DIR/README-operator-fetch.md)" >&2
  exit 1
fi
if [[ ! -f "$HASHFILE" ]]; then
  echo "FAIL: $HASHFILE missing — operator must run 'sha256sum bluejay-stock-boot.img > bluejay-stock-boot.img.sha256' inside $ROLLBACK_DIR" >&2
  exit 1
fi

(cd "$ROLLBACK_DIR" && sha256sum -c "$(basename "$HASHFILE")") \
  || { echo "FAIL: rollback asset hash mismatch — re-download stock boot.img" >&2; exit 2; }

echo "OK: rollback asset present + hash verified ($(stat -c%s "$ASSET") bytes)"
