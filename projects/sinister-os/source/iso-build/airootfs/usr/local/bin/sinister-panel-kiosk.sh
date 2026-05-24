#!/usr/bin/env bash
# sinister-panel-kiosk.sh — launch the Sinister Panel as a Wayland kiosk
# Author: RKOJ-ELENO :: 2026-05-24
#
# Started by Hyprland autostart on first boot. The Panel Next.js standalone
# build is bundled into the live ISO at /srv/sinister-panel/. We start it on
# 127.0.0.1:3080 and launch Chromium in --kiosk mode against it.

set -euo pipefail

PANEL_ROOT="/srv/sinister-panel"
PANEL_PORT="3080"
PANEL_LOG="/var/log/sinister/panel.log"

mkdir -p "$(dirname "$PANEL_LOG")"

# Start panel server if not already up
if ! curl -fsS -o /dev/null "http://127.0.0.1:${PANEL_PORT}/api/health" 2>/dev/null; then
  pushd "$PANEL_ROOT" >/dev/null
  PORT="$PANEL_PORT" HOSTNAME="127.0.0.1" nohup node server.js >>"$PANEL_LOG" 2>&1 &
  popd >/dev/null

  # Wait up to 30 s for it to come up
  for i in $(seq 1 30); do
    if curl -fsS -o /dev/null "http://127.0.0.1:${PANEL_PORT}/"; then
      break
    fi
    sleep 1
  done
fi

# Kiosk the Panel
exec chromium \
  --kiosk \
  --no-first-run \
  --noerrdialogs \
  --disable-translate \
  --disable-features=TranslateUI \
  --disable-infobars \
  --check-for-update-interval=31536000 \
  --autoplay-policy=no-user-gesture-required \
  --enable-features=UseOzonePlatform \
  --ozone-platform=wayland \
  "http://127.0.0.1:${PANEL_PORT}/"
