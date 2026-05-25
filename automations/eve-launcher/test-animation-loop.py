# Author: RKOJ-ELENO :: 2026-05-24
"""Smoke test for jcode_animation tick advancement.

Renders 40 frames at 10fps. If the shimmer band visibly drifts horizontally
frame-to-frame, the source primitives are correct and the integration issue
is in main_menu.py (blocking input prevents repaints between keystrokes)."""
import os
import sys
import time

sys.path.insert(0, r"D:/Sinister Sanctum/tools/eve-picker")
os.system("")  # enable VT-100 on Windows cmd

from jcode_animation import picker_tick_render  # noqa: E402

try:
    for tick in range(40):
        print("\033[H\033[2J", end="")  # clear + home
        picker_tick_render(
            tick,
            server="Sanctum",
            client="EVE",
            mcp_count=10,
            bot_count=7,
            live_agent_count=3,
        )
        sys.stdout.write(f"\n  [tick={tick}]")
        sys.stdout.flush()
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
print("\n[done]")
