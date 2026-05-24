#!/usr/bin/env bash
# sinister-first-boot.sh — one-shot first-boot init for Sinister OS live ISO
# Author: RKOJ-ELENO :: 2026-05-24
#
# Triggered by sinister-first-boot.service on first boot. Brings up
# networking, starts the ollama daemon for local AI, sets greeter to
# auto-login the eve user, and primes the Panel server.

set -euo pipefail

LOG=/var/log/sinister/first-boot.log
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1

echo "[$(date --utc +%FT%TZ)] sinister-first-boot start"

# Enable networking
systemctl enable --now NetworkManager.service || true

# Start ollama (local LLM substrate) — pulls a small default model on demand
systemctl enable --now ollama.service || true

# Ensure log dir exists for kiosk
mkdir -p /var/log/sinister
chown -R eve:eve /var/log/sinister || true

# Safety fix 2026-05-24 (RKOJ-ELENO): reorder mkdir -> chmod -> touch so set -euo pipefail does not abort on missing parent dir
mkdir -p /var/lib/sinister
chmod 700 /var/lib/sinister
# Mark first-boot done so the unit doesn't re-run
touch /var/lib/sinister/.first-boot-done

# Safety fix 2026-05-24 (RKOJ-ELENO): BLOCKER #2 simpler-option — also place kiosk Hyprland config at /root/.config/hypr/ so live ISO (boots as root/liveuser) auto-launches kiosk. Long-term M2: switch to greetd auto-login of dedicated eve user from /etc/skel.
mkdir -p /root/.config/hypr
if [ -f /etc/skel/.config/hypr/hyprland.conf ]; then
    cp -f /etc/skel/.config/hypr/hyprland.conf /root/.config/hypr/hyprland.conf
fi

# Safety fix 2026-05-24 (RKOJ-ELENO): BLOCKER #3 — yay is whitelisted in /etc/sudoers.d/sinister but AUR-only. Bootstrap it from official Arch source on first boot (idempotent).
/usr/local/bin/sinister-first-boot-install-yay.sh || true

echo "[$(date --utc +%FT%TZ)] sinister-first-boot done"
