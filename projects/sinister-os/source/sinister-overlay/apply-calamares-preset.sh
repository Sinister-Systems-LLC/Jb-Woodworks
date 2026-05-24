#!/usr/bin/env bash
# Sinister OS — Calamares preset applier.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Copies our /etc/calamares/ overrides onto the live ISO BEFORE Calamares is
# launched. Designed to run from the live-ISO root (cwd = sinister-overlay/).
#
# Honors kernel cmdline parameter `sinister.skip-auto=1` — if present in
# /proc/cmdline, the preset is NOT applied and Calamares falls back to its
# interactive defaults. This is the operator's escape hatch when they want to
# do a custom install (multi-disk, dual-boot, LUKS, etc.).
#
# Usage (from inside the live ISO):
#   sudo bash apply-calamares-preset.sh
#
# Idempotent: safe to re-run.

set -euo pipefail

# ===== logging =====
log()  { printf '\033[1;35m[calamares-preset]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[calamares-preset] WARN:\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[calamares-preset] ERR:\033[0m %s\n' "$*" >&2; }

# ===== preflight =====
if [[ $EUID -ne 0 ]]; then
  err "must run as root (sudo bash apply-calamares-preset.sh)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/etc/calamares"
DST_DIR="/etc/calamares"

if [[ ! -d "$SRC_DIR" ]]; then
  err "preset source missing: $SRC_DIR"
  exit 1
fi

# ===== kernel cmdline override =====
if grep -qE '(^| )sinister\.skip-auto=1( |$)' /proc/cmdline 2>/dev/null; then
  warn "kernel cmdline contains sinister.skip-auto=1 — preset NOT applied"
  warn "Calamares will launch with its stock interactive config"
  exit 0
fi

# ===== copy =====
log "source: $SRC_DIR"
log "target: $DST_DIR"

install -d -m 0755 "$DST_DIR"
install -d -m 0755 "$DST_DIR/modules"
install -d -m 0755 "$DST_DIR/branding"
install -d -m 0755 "$DST_DIR/branding/sinister"

# Top-level settings.conf.
install -m 0644 "$SRC_DIR/settings.conf" "$DST_DIR/settings.conf"
log "  + settings.conf"

# Module configs (each module reads /etc/calamares/modules/<name>.conf).
for f in "$SRC_DIR"/modules/*.conf; do
  base="$(basename "$f")"
  install -m 0644 "$f" "$DST_DIR/modules/$base"
  log "  + modules/$base"
done

# Branding descriptor + assets.
install -m 0644 "$SRC_DIR/branding/sinister/branding.desc" "$DST_DIR/branding/sinister/branding.desc"
log "  + branding/sinister/branding.desc"

# show.svg lives in the overlay's usr/share/calamares/branding/sinister/ tree.
# Calamares looks for branding assets relative to branding.desc, so we copy
# show.svg next to it in the destination.
SHOW_SVG="$SCRIPT_DIR/usr/share/calamares/branding/sinister/show.svg"
if [[ -f "$SHOW_SVG" ]]; then
  install -m 0644 "$SHOW_SVG" "$DST_DIR/branding/sinister/show.svg"
  log "  + branding/sinister/show.svg"
else
  warn "show.svg missing at $SHOW_SVG — branding will fall back to text-only"
fi

# Drop the operator doc into /etc/calamares so it ships on the installed system
# too (useful when operator is debugging post-install).
if [[ -f "$SCRIPT_DIR/CALAMARES-AUTOMATION.md" ]]; then
  install -m 0644 "$SCRIPT_DIR/CALAMARES-AUTOMATION.md" "$DST_DIR/CALAMARES-AUTOMATION.md"
  log "  + CALAMARES-AUTOMATION.md"
fi

log "preset applied. launch Calamares with:  sudo calamares"
log "override per-install:                   add  sinister.skip-auto=1  to kernel cmdline"
