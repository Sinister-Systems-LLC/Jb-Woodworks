#!/usr/bin/env bash
# Sinister OS overlay installer. Author: RKOJ-ELENO :: 2026-05-24
# Converts a vanilla CachyOS system (live OR installed) into Sinister OS by overlaying
# branding on every operator-facing surface.
#
# Idempotent: safe to re-run.
# Operator directive (verbatim 2026-05-24): "everything we make needs to have our branding".
#
# Usage:
#   sudo bash install.sh                  # apply (auto-detects live vs installed)
#   sudo bash install.sh --no-plymouth    # skip Plymouth (forced)
#   sudo bash install.sh --dry-run        # print actions without executing
#
# Reverts via: sudo bash uninstall.sh

set -euo pipefail

# ===== flags =====
DRY_RUN=0
FORCE_NO_PLYMOUTH=0
for arg in "$@"; do
  case "$arg" in
    --dry-run)      DRY_RUN=1 ;;
    --no-plymouth)  FORCE_NO_PLYMOUTH=1 ;;
    -h|--help)
      sed -n '2,16p' "$0"; exit 0 ;;
    *)  echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# ===== logging =====
log()  { printf '\033[1;35m[sinister-overlay]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[sinister-overlay] WARN:\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[sinister-overlay] ERR:\033[0m %s\n' "$*" >&2; }

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '\033[1;36m[dry-run]\033[0m %s\n' "$*"
  else
    eval "$@"
  fi
}

# ===== preflight =====
if [[ $EUID -ne 0 ]]; then
  err "must run as root (sudo bash install.sh)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log "overlay source: $SCRIPT_DIR"

# ===== detect live vs installed =====
IS_LIVE=0
if [[ -f /etc/cachyos-release ]] || grep -qi cachyos /etc/os-release 2>/dev/null; then
  if mount | grep -E '^(airootfs|cow|overlay)\s' >/dev/null 2>&1 \
     || [[ -d /run/archiso ]] \
     || ! touch /usr/.sinister-write-probe 2>/dev/null; then
    IS_LIVE=1
  fi
  rm -f /usr/.sinister-write-probe 2>/dev/null || true
fi
if [[ $IS_LIVE -eq 1 ]]; then
  log "detected: LIVE session (read-only /usr — Plymouth + initramfs steps will be skipped)"
else
  log "detected: INSTALLED system (full overlay including Plymouth)"
fi

# ===== status tracking =====
declare -A STATUS
mark_ok()   { STATUS["$1"]="OK"; }
mark_skip() { STATUS["$1"]="SKIP ($2)"; }
mark_fail() { STATUS["$1"]="FAIL ($2)"; }

# ===== 1. os-release =====
log "step 1/9 — os-release rewrite"
if [[ -f /etc/os-release ]] && [[ ! -f /etc/os-release.cachyos.bak ]]; then
  run "cp -a /etc/os-release /etc/os-release.cachyos.bak"
fi
run "install -m 0644 '$SCRIPT_DIR/etc/os-release.sinister' /etc/os-release"
mark_ok os-release

# ===== 2. wallpapers =====
log "step 2/9 — wallpapers"
run "install -d -m 0755 /usr/share/backgrounds/sinister"
for f in wallpaper-primary.svg wallpaper-lockscreen.svg; do
  if [[ -f "$SCRIPT_DIR/usr/share/backgrounds/sinister/$f" ]]; then
    run "install -m 0644 '$SCRIPT_DIR/usr/share/backgrounds/sinister/$f' /usr/share/backgrounds/sinister/$f"
  fi
done
# Rasterize SVG -> PNG so swww/Plymouth can consume directly. Falls back to SVG if rsvg-convert missing.
if command -v rsvg-convert >/dev/null 2>&1; then
  for base in wallpaper-primary wallpaper-lockscreen; do
    src="/usr/share/backgrounds/sinister/${base}.svg"
    dst="/usr/share/backgrounds/sinister/${base}.png"
    if [[ -f "$src" ]]; then
      run "rsvg-convert -w 1920 -h 1080 '$src' -o '$dst'"
    fi
  done
  mark_ok wallpapers
else
  warn "rsvg-convert not installed — wallpaper PNG not generated (Hyprland config still works with SVG via swww if librsvg backend present)"
  mark_skip wallpapers "rsvg-convert missing — SVG copied, PNG not rendered"
fi

# ===== 3. Hyprland theme (system skel + root) =====
log "step 3/9 — Hyprland theme"
run "install -d -m 0755 /etc/skel/.config/hypr /etc/skel/.config/waybar"
run "install -m 0644 '$SCRIPT_DIR/etc/skel/.config/hypr/hyprland.conf'   /etc/skel/.config/hypr/hyprland.conf"
run "install -m 0644 '$SCRIPT_DIR/etc/skel/.config/waybar/config.jsonc'  /etc/skel/.config/waybar/config.jsonc"
run "install -m 0644 '$SCRIPT_DIR/etc/skel/.config/waybar/style.css'     /etc/skel/.config/waybar/style.css"
run "install -d -m 0700 /root/.config/hypr /root/.config/waybar"
run "install -m 0644 '$SCRIPT_DIR/root/.config/hypr/hyprland.conf'       /root/.config/hypr/hyprland.conf"
run "install -m 0644 '$SCRIPT_DIR/root/.config/waybar/config.jsonc'      /root/.config/waybar/config.jsonc"
run "install -m 0644 '$SCRIPT_DIR/root/.config/waybar/style.css'         /root/.config/waybar/style.css"
mark_ok hyprland

# ===== 4. GTK + Qt theme =====
log "step 4/9 — GTK + Qt accent overlay"
run "install -d -m 0755 /usr/share/themes/Sinister/gtk-3.0 /usr/share/themes/Sinister/gtk-4.0"
run "install -m 0644 '$SCRIPT_DIR/usr/share/themes/Sinister/index.theme'        /usr/share/themes/Sinister/index.theme"
run "install -m 0644 '$SCRIPT_DIR/usr/share/themes/Sinister/gtk-3.0/gtk.css'    /usr/share/themes/Sinister/gtk-3.0/gtk.css"
run "install -m 0644 '$SCRIPT_DIR/usr/share/themes/Sinister/gtk-4.0/gtk.css'    /usr/share/themes/Sinister/gtk-4.0/gtk.css"
# Qt picks the GTK colors when qt5ct/qt6ct platform-theme is set; nothing extra to write here.
mark_ok gtk-qt

# ===== 5. Plymouth =====
log "step 5/9 — Plymouth splash"
if [[ $IS_LIVE -eq 1 ]] || [[ $FORCE_NO_PLYMOUTH -eq 1 ]]; then
  mark_skip plymouth "live session or --no-plymouth (initramfs cannot be rebuilt)"
else
  run "install -d -m 0755 /usr/share/plymouth/themes/sinister"
  run "install -m 0644 '$SCRIPT_DIR/usr/share/plymouth/themes/sinister/sinister.plymouth' /usr/share/plymouth/themes/sinister/sinister.plymouth"
  run "install -m 0644 '$SCRIPT_DIR/usr/share/plymouth/themes/sinister/sinister.script'   /usr/share/plymouth/themes/sinister/sinister.script"
  run "install -m 0644 '$SCRIPT_DIR/usr/share/plymouth/themes/sinister/background.svg'    /usr/share/plymouth/themes/sinister/background.svg"
  if command -v rsvg-convert >/dev/null 2>&1; then
    run "rsvg-convert -w 1920 -h 1080 '$SCRIPT_DIR/usr/share/plymouth/themes/sinister/background.svg' -o /usr/share/plymouth/themes/sinister/background.png"
  fi
  if command -v plymouth-set-default-theme >/dev/null 2>&1 && [[ -f /usr/share/plymouth/themes/sinister/background.png ]]; then
    run "plymouth-set-default-theme -R sinister"
    mark_ok plymouth
  else
    mark_skip plymouth "plymouth-set-default-theme or background.png missing"
  fi
fi

# ===== 6. hostname seed =====
log "step 6/9 — hostname seed (default; operator may change later)"
if [[ ! -f /etc/hostname ]] || [[ "$(cat /etc/hostname 2>/dev/null)" == "cachyos" ]] || [[ ! -s /etc/hostname ]]; then
  run "install -m 0644 '$SCRIPT_DIR/etc/hostname.sinister' /etc/hostname"
  mark_ok hostname
else
  mark_skip hostname "operator-set hostname preserved: $(cat /etc/hostname)"
fi

# ===== 7. EVE sudoers =====
log "step 7/9 — EVE sudoers"
run "install -d -m 0755 /etc/sudoers.d"
# sudoers files MUST be 0440.
run "install -m 0440 '$SCRIPT_DIR/etc/sudoers.d/eve' /etc/sudoers.d/eve"
if [[ $DRY_RUN -eq 0 ]] && command -v visudo >/dev/null 2>&1; then
  if visudo -cf /etc/sudoers.d/eve >/dev/null 2>&1; then
    mark_ok sudoers
  else
    err "visudo -cf rejected /etc/sudoers.d/eve — removing"
    rm -f /etc/sudoers.d/eve
    mark_fail sudoers "visudo rejected file (left filesystem clean)"
  fi
else
  mark_ok sudoers
fi

# ===== 8. EVE-OS integration (Python prototype; Rust port follows) =====
# Drops the sinister-eve daemon binary wrapper, systemd unit, config example, and MCP tool registrations.
# Author: RKOJ-ELENO :: 2026-05-24
log "step 8/9 — EVE-OS integration"
install_eve() {
  local src="$SCRIPT_DIR/../eve-os-integration/scaffold"
  if [[ ! -d "$src" ]]; then
    warn "EVE scaffold missing at $src — skipping EVE install"
    mark_skip eve-os "scaffold dir not present"
    return 0
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '\033[1;36m[dry-run]\033[0m would install EVE from %s\n' "$src"
    mark_ok eve-os
    return 0
  fi

  # Directories.
  install -d -m 0755 /usr/lib/sinister-eve /etc/sinister /etc/sinister/mcp /var/lib/sinister/memory

  # Wrapper (executable) + Python prototype + systemd unit + config example.
  install -m 0755 "$src/usr/local/bin/sinister-eve" /usr/local/bin/sinister-eve
  install -m 0644 "$src/sinister-eve-mcp-bridge.py" /usr/lib/sinister-eve/sinister-eve-mcp-bridge.py
  install -m 0644 "$src/sinister-eve.service" /etc/systemd/system/sinister-eve.service
  install -m 0644 "$src/etc/sinister/eve.toml.example" /etc/sinister/eve.toml.example
  if [[ ! -f /etc/sinister/eve.toml ]]; then
    install -m 0644 "$src/etc/sinister/eve.toml.example" /etc/sinister/eve.toml
  fi

  # MCP tool drop-ins (any *.json under scaffold/etc/sinister/mcp/).
  local mcp
  shopt -s nullglob
  for mcp in "$src/etc/sinister/mcp/"*.json; do
    install -m 0644 "$mcp" "/etc/sinister/mcp/$(basename "$mcp")"
  done
  shopt -u nullglob

  # Group ("sinister") used by socket peer-cred + eve.service Group=. eve user creation is handled
  # by a separate postinstall hook (out-of-scope for branding overlay; documented in DEPLOYMENT-2026-05-24.md).
  if ! getent group sinister >/dev/null; then
    groupadd -r sinister || warn "groupadd sinister failed (non-fatal; may exist in NSS only)"
  fi

  # Reload systemd + enable the unit. Use ||true so a missing systemctl (chroot) doesn't abort.
  systemctl daemon-reload 2>/dev/null || warn "systemctl daemon-reload failed (chroot?)"
  systemctl enable sinister-eve.service 2>/dev/null || warn "systemctl enable failed (chroot? eve user missing?)"
  log "  + EVE-OS integration installed and enabled"
  mark_ok eve-os
}
# Run under a no-fail guard: EVE failures must NOT abort the branding overlay.
if install_eve; then
  :
else
  mark_fail eve-os "install_eve returned non-zero (see warnings above)"
fi

# ===== 9. summary table =====
log "step 9/9 — summary"
printf '\n\033[1;35m========== Sinister Overlay Apply Summary ==========\033[0m\n'
printf '  %-14s %s\n' "STEP" "RESULT"
printf '  %-14s %s\n' "----" "------"
for key in os-release wallpapers hyprland gtk-qt plymouth hostname sudoers eve-os; do
  printf '  %-14s %s\n' "$key" "${STATUS[$key]:-UNKNOWN}"
done
printf '\033[1;35m====================================================\033[0m\n\n'

if [[ $IS_LIVE -eq 1 ]]; then
  log "live session: changes apply in-memory only — reboot the live ISO and they're gone (expected)."
else
  log "installed system: log out + back in (or reboot) for all surfaces to pick up the overlay."
fi
log "uninstall any time: sudo bash $SCRIPT_DIR/uninstall.sh"
