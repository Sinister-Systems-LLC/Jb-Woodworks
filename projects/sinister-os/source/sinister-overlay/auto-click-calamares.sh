#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-24
# Auto-click Calamares Next button 7 times on Wayland via ydotool (uinput).
# Assumes ydotoold already running with socket at /tmp/.ydotool_socket.
set -uo pipefail
export YDOTOOL_SOCKET=/tmp/.ydotool_socket

# Linux input event codes (input-event-codes.h):
#   KEY_LEFTALT  = 56
#   KEY_N        = 49
#   KEY_ENTER    = 28
ALT=56
N=49
ENTER=28

# Confirm calamares still up
if ! pgrep -x calamares >/dev/null; then
  echo "ERR: calamares not running"
  exit 2
fi
echo "calamares-pid=$(pgrep -x calamares)"

# Page 1 Welcome -> Page 2 Location -> Page 3 Keyboard -> Page 4 Partitions
#   -> Page 5 Users -> Page 6 Summary -> click Install (page 6 Next becomes Install)
# Seven Alt+N taps:
#   1: Welcome -> Location
#   2: Location -> Keyboard
#   3: Keyboard -> Partitions
#   4: Partitions -> Users (may pop a confirm modal; handled below)
#   5: Users -> Summary
#   6: Summary -> Install (kicks install)
#   7: spare (if any modal interleaves)
for n in 1 2 3 4 5 6 7; do
  sleep 4
  echo "[$(date -Iseconds)] sending Alt+N #$n"
  ydotool key ${ALT}:1 ${N}:1 ${N}:0 ${ALT}:0
  rc=$?
  echo "  -> exit=$rc"
done

# In case the partition-wipe confirmation modal opened, press Enter to accept it.
sleep 3
echo "[$(date -Iseconds)] sending Enter to accept any open modal"
ydotool key ${ENTER}:1 ${ENTER}:0

sleep 2
echo "[$(date -Iseconds)] final pgrep:"
pgrep -a calamares
echo "DONE"
