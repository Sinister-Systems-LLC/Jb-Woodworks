# Author: RKOJ-ELENO :: 2026-05-24
"""Smoke test for jcode rainbow shimmer.

Renders 10 ticks of render_animation_frame to the terminal at 100ms intervals.
If the band visibly moves frame-to-frame and you see rainbow colors (not a
static red pumpkin or a blank gray block) -> animation is wired correctly.

Usage:
    PYTHONIOENCODING=utf-8 python smoke-animation.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "eve-picker"))

# Force VT-100 on Windows cmd
os.system("")

from jcode_animation import render_animation_frame  # noqa: E402

for tick in range(0, 40, 4):
    # ANSI clear-screen + home
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.write(f"  [smoke] tick={tick}\n\n")
    lines = render_animation_frame(tick, width=72, height=4)
    for line in lines:
        sys.stdout.write("  " + line + "\n")
    sys.stdout.flush()
    time.sleep(0.1)

sys.stdout.write("\n  [smoke] PASS if you saw the rainbow shimmer move frame-to-frame.\n")
