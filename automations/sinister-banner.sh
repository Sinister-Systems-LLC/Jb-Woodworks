#!/bin/bash
# Author: RKOJ-ELENO :: 2026-05-23
# sinister-banner.sh - animated jcode-style ASCII C banner for spawn windows.
#
# Operator 2026-05-23 evening (image #3): "make sure we have the jcode animation
# ascii thing on the start of the prompt as well or in teh bat file somewhere.
# yopu can just pick the coolest one and use that for now."
#
# Renders an animated stylized "C" with a shifting color gradient, then restores
# the terminal and exits. Usage:
#   bash /d/Sinister\ Sanctum/automations/sinister-banner.sh [frames] [delay]
# defaults: 8 frames, 0.07s per frame (~0.55s total).
#
# Tested in mintty + Git Bash. Uses 256-color ANSI; degrades to plain text if
# TERM doesn't advertise color support.

FRAMES="${1:-8}"
DELAY="${2:-0.07}"

# Lines transcribed 1:1 from image #3 (jcode launch logo). Glyph proportions
# preserved; only quote-escape adjustments for bash literals.
LOGO_LINES=(
    "        =,,@@@@#,=="
    "     ,@@@@@@@@@@@@-"
    "   .@@@@@@@@@@@##@@@@@-"
    "   .@@@@@@@.    -@@@@@-"
    "   |@@@@@@@      @@@@@|"
    "   .@@@@@@@%     @@@@@|"
    "   @@@@@@@@@     @@@@@@-"
    "   .@@@@@@@@@@,,@@@@@@@-"
    "   -@@@@@@@@@@@@@@@@@@@-"
    "    *@@@@@@@@@@@@@@@@@@@%"
    "      ^@@@@@@@@@@@@@@@@%"
    "         ^=@@@@@@@-"
)

# 256-color palette tuned to match the jcode screenshot: red→orange→pink→
# magenta→purple→indigo. Cycles smoothly when offset shifts per frame.
COLORS=(196 202 208 209 210 211 212 213 207 201 200 199 198 197 165 129 93 99)

# Detect color support; fall back to monochrome if unavailable.
USE_COLOR=1
case "${TERM:-}" in
    dumb|"") USE_COLOR=0 ;;
esac
if [ -z "${COLORTERM:-}" ] && [ "${TERM:-}" != "xterm-256color" ] && [ "${TERM:-}" != "screen-256color" ] && [ "${TERM:-}" != "mintty" ]; then
    # Most terminals these days handle 256-color; only opt out if explicitly dumb.
    :
fi

render_frame() {
    local offset="$1"
    # Reposition to logo origin; printed top-down. Caller has already reserved
    # vertical space + moved cursor to the right starting row.
    printf '\033[%dA' "${#LOGO_LINES[@]}" 2>/dev/null
    local i=0
    for line in "${LOGO_LINES[@]}"; do
        if [ "$USE_COLOR" = "1" ]; then
            local cidx=$(( (i + offset) % ${#COLORS[@]} ))
            printf '\033[2K\033[38;5;%dm%s\033[0m\n' "${COLORS[$cidx]}" "$line"
        else
            printf '\033[2K%s\n' "$line"
        fi
        i=$((i + 1))
    done
}

# Hide cursor + reserve vertical space (print empty lines, then animate in place).
if [ "$USE_COLOR" = "1" ]; then printf '\033[?25l'; fi
for _ in "${LOGO_LINES[@]}"; do printf '\n'; done

frame=0
while [ "$frame" -lt "$FRAMES" ]; do
    render_frame "$frame"
    sleep "$DELAY" 2>/dev/null || sleep 1
    frame=$((frame + 1))
done

# Restore cursor.
if [ "$USE_COLOR" = "1" ]; then printf '\033[?25h'; fi
