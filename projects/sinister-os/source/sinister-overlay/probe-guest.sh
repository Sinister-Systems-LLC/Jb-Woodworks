#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-24
echo "===TOOLS==="
command -v xdotool && xdotool --version 2>&1 | head -1
command -v wlrctl
command -v ydotool
command -v wtype
echo "===PROCS==="
pgrep -a calamares
echo "===RUN1000==="
ls /run/user/1000/ 2>/dev/null
echo "===SESSION==="
loginctl list-sessions --no-legend 2>/dev/null
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
echo "===WINDOWS==="
if command -v xdotool >/dev/null; then
  DISPLAY=:0 xdotool search --name "." 2>&1 | head -5
fi
echo "===CALAMARES_LOG_TAIL==="
tail -20 /var/log/Calamares.log 2>/dev/null || tail -20 /root/.cache/Calamares/Calamares.log 2>/dev/null || find / -name "Calamares.log" 2>/dev/null | head -3
