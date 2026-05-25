#!/usr/bin/env bash
# Sinister OS overlay uninstaller. Author: RKOJ-ELENO :: 2026-05-24
# Reverts install.sh: restores /etc/os-release.cachyos.bak, removes overlay files.
#
# Usage:
#   sudo bash uninstall.sh             # revert
#   sudo bash uninstall.sh --dry-run   # print actions only

set -euo pipefail

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

log()  { printf '\033[1;35m[sinister-overlay]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[sinister-overlay] WARN:\033[0m %s\n' "$*" >&2; }

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '\033[1;36m[dry-run]\033[0m %s\n' "$*"
  else
    eval "$@"
  fi
}

if [[ $EUID -ne 0 ]]; then
  echo "must run as root (sudo bash uninstall.sh)" >&2
  exit 1
fi

# ===== 1. os-release restore =====
if [[ -f /etc/os-release.cachyos.bak ]]; then
  log "restoring /etc/os-release from /etc/os-release.cachyos.bak"
  run "mv -f /etc/os-release.cachyos.bak /etc/os-release"
else
  warn "no /etc/os-release.cachyos.bak found — leaving current /etc/os-release in place"
fi

# ===== 2. wallpapers =====
log "removing /usr/share/backgrounds/sinister/"
run "rm -rf /usr/share/backgrounds/sinister"

# ===== 3. Hyprland config (only our copies — don't nuke user customizations) =====
log "removing Sinister Hyprland + Waybar files from /etc/skel + /root"
for f in /etc/skel/.config/hypr/hyprland.conf \
         /etc/skel/.config/waybar/config.jsonc \
         /etc/skel/.config/waybar/style.css \
         /root/.config/hypr/hyprland.conf \
         /root/.config/waybar/config.jsonc \
         /root/.config/waybar/style.css; do
  if [[ -f "$f" ]] && grep -q "Sinister OS" "$f" 2>/dev/null; then
    run "rm -f '$f'"
  fi
done

# ===== 4. GTK + Qt theme =====
log "removing /usr/share/themes/Sinister/"
run "rm -rf /usr/share/themes/Sinister"

# ===== 5. Plymouth =====
log "removing /usr/share/plymouth/themes/sinister/"
run "rm -rf /usr/share/plymouth/themes/sinister"
if command -v plymouth-set-default-theme >/dev/null 2>&1; then
  # Reset to distro default — caller can switch back to whatever they prefer.
  if plymouth-set-default-theme --list 2>/dev/null | grep -qx bgrt; then
    run "plymouth-set-default-theme -R bgrt"
  else
    warn "could not auto-pick replacement Plymouth theme; run: sudo plymouth-set-default-theme -R <name>"
  fi
fi

# ===== 6. hostname — only reset if still the sinister default =====
if [[ -f /etc/hostname ]] && [[ "$(cat /etc/hostname)" == "sinister-laptop" ]]; then
  log "resetting /etc/hostname (was the Sinister seed) -> cachyos"
  run "echo cachyos > /etc/hostname"
fi

# ===== 7. EVE sudoers =====
log "removing /etc/sudoers.d/eve"
run "rm -f /etc/sudoers.d/eve"

# ===== 8. EVE-OS integration (mirror of install.sh install_eve) =====
# Author: RKOJ-ELENO :: 2026-05-24
log "step 8 — EVE-OS integration removal"
uninstall_eve() {
  # Stop + disable systemd unit if present.
  if command -v systemctl >/dev/null 2>&1; then
    if systemctl list-unit-files 2>/dev/null | grep -q '^sinister-eve\.service'; then
      run "systemctl disable --now sinister-eve.service 2>/dev/null || true"
    fi
  fi

  # Files dropped by install_eve.
  run "rm -f /etc/systemd/system/sinister-eve.service"
  run "rm -f /usr/local/bin/sinister-eve"
  run "rm -rf /usr/lib/sinister-eve"
  # Config: keep eve.toml (operator-edited); only drop the example.
  run "rm -f /etc/sinister/eve.toml.example"
  # MCP drop-ins shipped by the overlay.
  run "rm -f /etc/sinister/mcp/eve-cli.json /etc/sinister/mcp/panel-control.json"
  # Empty /etc/sinister/mcp + /etc/sinister if nothing else remains.
  if [[ -d /etc/sinister/mcp ]] && [[ -z "$(ls -A /etc/sinister/mcp 2>/dev/null)" ]]; then
    run "rmdir /etc/sinister/mcp"
  fi
  if [[ -d /etc/sinister ]] && [[ -z "$(ls -A /etc/sinister 2>/dev/null)" ]]; then
    run "rmdir /etc/sinister"
  fi

  # NOTE: /var/lib/sinister/memory is the operator's brain — NEVER auto-delete.
  warn "preserved /var/lib/sinister/memory (operator brain). Delete manually if intended."

  # Group: remove only if no users still belong to it.
  if getent group sinister >/dev/null 2>&1; then
    local members
    members="$(getent group sinister | awk -F: '{print $4}')"
    if [[ -z "$members" ]]; then
      run "groupdel sinister 2>/dev/null || true"
    else
      warn "group 'sinister' has members ($members) — keeping group"
    fi
  fi

  if command -v systemctl >/dev/null 2>&1; then
    run "systemctl daemon-reload 2>/dev/null || true"
  fi
  log "  - EVE-OS integration removed"
}
uninstall_eve

log "uninstall complete. Reboot to drop the Plymouth + Hyprland changes from running sessions."
