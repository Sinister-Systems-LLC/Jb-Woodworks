#!/usr/bin/env bash
# /root/.automated_script.sh — runs at archiso live login
# Author: RKOJ-ELENO :: 2026-05-24
#
# archiso convention: this script runs once the live root user logs in on
# tty1. We use it to enable services and start Hyprland for the live
# kiosk experience.

systemctl enable --now NetworkManager.service 2>/dev/null || true
systemctl enable --now ollama.service 2>/dev/null || true
systemctl enable --now sinister-first-boot.service 2>/dev/null || true

# Auto-launch Hyprland on tty1 (the kiosk path)
if [ -z "$WAYLAND_DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec Hyprland
fi
