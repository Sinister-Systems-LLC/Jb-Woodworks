#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-24
# Fill Calamares Users-page passwords via ydotool mouse + type, then advance to Install.
# Resolution: 800x600. Calamares fills full screen.
set -uo pipefail
export YDOTOOL_SOCKET=/tmp/.ydotool_socket

# Input event codes
ALT=56
N=49
ENTER=28

PASS="sinister"

# ydotool absolute mouse: `ydotool mousemove --absolute -x X -y Y`
# left click: `ydotool click 0xC0` (down+up of button 0)
# Per ydotool docs: click code: 0x00 LEFT-up, 0x40 LEFT-down, 0xC0 LEFT down+up.
# But ydotool 1.0.4 uses different syntax. Check available:

echo "[$(date -Iseconds)] ydotool version + help:"
ydotool --help 2>&1 | head -20
echo "---"
ydotool mousemove --help 2>&1 | head -10
echo "---"
ydotool click --help 2>&1 | head -10
echo "==="

# Coords (800x600 ref)
USER_PASS_X=208; USER_PASS_Y=258
USER_REPEAT_X=413; USER_REPEAT_Y=258
CHECKBOX_X=115; CHECKBOX_Y=293
NEXT_X=742; NEXT_Y=551

click_at() {
  local x=$1 y=$2
  ydotool mousemove --absolute -x $x -y $y
  sleep 0.3
  ydotool click 0xC0
  sleep 0.3
}

echo "[$(date -Iseconds)] click 'Use same password for admin' checkbox to disable separate admin password"
click_at $CHECKBOX_X $CHECKBOX_Y
sleep 1

echo "[$(date -Iseconds)] click User Password field and type"
click_at $USER_PASS_X $USER_PASS_Y
sleep 0.5
ydotool type --delay 30 "$PASS"
sleep 1

echo "[$(date -Iseconds)] click Repeat Password field and type"
click_at $USER_REPEAT_X $USER_REPEAT_Y
sleep 0.5
ydotool type --delay 30 "$PASS"
sleep 1

echo "[$(date -Iseconds)] Alt+N to advance from Users to Summary"
ydotool key ${ALT}:1 ${N}:1 ${N}:0 ${ALT}:0
sleep 4

echo "[$(date -Iseconds)] Alt+N to click Install on Summary page"
ydotool key ${ALT}:1 ${N}:1 ${N}:0 ${ALT}:0
sleep 3

echo "[$(date -Iseconds)] Enter for any confirmation modal"
ydotool key ${ENTER}:1 ${ENTER}:0
sleep 2

echo "[$(date -Iseconds)] final pgrep:"
pgrep -a calamares
echo "DONE"
