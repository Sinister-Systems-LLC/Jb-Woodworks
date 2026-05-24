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

# Mark first-boot done so the unit doesn't re-run
touch /var/lib/sinister/.first-boot-done
mkdir -p /var/lib/sinister
chmod 700 /var/lib/sinister

echo "[$(date --utc +%FT%TZ)] sinister-first-boot done"
