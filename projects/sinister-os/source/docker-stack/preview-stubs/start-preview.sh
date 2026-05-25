#!/usr/bin/env bash
# start-preview.sh — Phase 1A entrypoint for sinister/os-preview container.
# Author: RKOJ-ELENO :: 2026-05-25
#
# Stack:
#   Xvfb :0     → virtual framebuffer (no real GPU needed)
#   i3          → tiling WM (Hyprland needs real Wayland; i3 is the preview shim)
#   x11vnc :5900 → exposes display 0 over VNC
#   noVNC 6080   → noVNC web client (websockify connects 6080 → 5900)

set -euo pipefail

export DISPLAY=:0
export USER="${USER:-eve}"
export HOME="${HOME:-/home/eve}"

mkdir -p /var/log/sinister /var/lib/sinister /run/sinister
chown -R eve:eve /var/log/sinister /var/lib/sinister /run/sinister 2>/dev/null || true

echo "[preview] starting Xvfb on :0"
Xvfb :0 -screen 0 1600x900x24 -nolisten tcp &
XVFB_PID=$!

# Wait for Xvfb to be ready
for i in $(seq 1 20); do
    if xdpyinfo -display :0 >/dev/null 2>&1; then
        break
    fi
    sleep 0.2
done

echo "[preview] starting xterm + i3 as eve user"
su - eve -c "DISPLAY=:0 xrdb -merge /home/eve/.Xresources" || true

# i3 needs to know about display; run it as eve in background
su - eve -c "DISPLAY=:0 i3 --shmlog-size=0" &
I3_PID=$!

# Give i3 a moment to come up
sleep 1

# Open one xterm so operator immediately sees something to type in
su - eve -c "DISPLAY=:0 xterm -fa 'Cascadia Code' -fs 11 -bg '#100820' -fg '#e8d6ff' -title 'Sinister OS Preview' -e 'cat /etc/sinister/banner.txt; exec bash'" &

echo "[preview] starting x11vnc on :5900"
x11vnc -display :0 -rfbport 5900 -nopw -forever -shared -bg -o /var/log/sinister/x11vnc.log

echo "[preview] starting noVNC websockify on :6080 → :5900"
websockify --web /usr/share/novnc/ 6080 localhost:5900 &
NOVNC_PID=$!

echo "[preview] all surfaces up"
echo "[preview]   noVNC:  http://<host>:6080/vnc.html?autoconnect=1&resize=remote"
echo "[preview]   VNC:    <host>:5900"

# Trap SIGTERM/SIGINT and forward to children
trap 'kill $XVFB_PID $I3_PID $NOVNC_PID 2>/dev/null || true; exit 0' SIGTERM SIGINT

# Wait on i3; if i3 dies the desktop is gone
wait $I3_PID
echo "[preview] i3 exited — preview shutting down"
kill $XVFB_PID $NOVNC_PID 2>/dev/null || true
