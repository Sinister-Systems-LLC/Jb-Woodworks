# animations.py -- jcode-style TUI animations for EVE.exe main menu
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T21:51Z:
#   "WITH THE RANDOM MOVING SAME CODE FROM JCODE ANIMATIONS JUST LIKE THERE.
#    here is the code legit take it and have it the same its not that hard.
#    'C:/Users/Zonia/Desktop/jcode-0.12.4'"
# Operator hard-canonical 2026-05-24T22:21Z:
#   "phase 2 jcode animations and evrything else you need to do like adding
#    the fucking logo to the exe"
#
# Ported from C:/Users/Zonia/Desktop/jcode-0.12.4/src/tui/ui_animations.rs:1-50
# (HSV-to-RGB hue rotation, donut/orbit_rings 3D ASCII, ease-out-cubic 150ms ticks).
# Adapted to Python with:
#   - stdlib only (math, time, threading, random)
#   - 256-color ANSI escapes (matches existing eve.py palette)
#   - non-blocking via background thread + thread-safe frame buffer
#   - Sinister purple bias (--accent #c084fc) instead of full rainbow
#
# Phase 2 of EVE.exe main-menu redesign per the master plan at
# _shared-memory/plans/sanctum-eve-main-menu-redesign-2026-05-24T2152Z/plan.md
#
# Honors eve-exe-uniform-ui-infinite-accounts-2026-05-24 doctrine: banner region
# capped at 5 rows + 1 menu header = 6-line cap; single-line header per panel.

from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, field

# Sinister palette (matches eve.py 6-color contract)
_SINISTER_PURPLE_HSL = (270.0, 0.85, 0.55)   # base hue purple
_HUE_DRIFT_AMPLITUDE = 40.0                   # +/- degrees from purple (gives motion w/o rainbow)


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    """jcode ui_animations.rs:1-50 HSV->RGB port. h in [0,360), s/v in [0,1]."""
    h = h % 360.0
    c = v * s
    x = c * (1 - abs(((h / 60.0) % 2) - 1))
    m = v - c
    if h < 60:    r, g, b = c, x, 0.0
    elif h < 120: r, g, b = x, c, 0.0
    elif h < 180: r, g, b = 0.0, c, x
    elif h < 240: r, g, b = 0.0, x, c
    elif h < 300: r, g, b = x, 0.0, c
    else:         r, g, b = c, 0.0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def _ansi_fg_rgb(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


_ANSI_RESET = "\033[0m"


@dataclass
class _AnimState:
    """Thread-safe frame buffer + tick counter."""
    frame_lines: list[str] = field(default_factory=list)
    tick: int = 0
    stop: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


def _ease_out_cubic(t: float) -> float:
    """jcode crates/jcode-desktop/src/animation.rs:37-98 -- 150ms ease-out-cubic."""
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def _render_orbit_rings(width: int, rows: int, tick: int) -> list[str]:
    """jcode ui_animations.rs orbit_rings -- 3D ASCII rings with HSV hue rotation.
    Sinister-purple-biased: hue oscillates around 270deg +/- 40deg.
    """
    cx = width / 2.0
    cy = rows / 2.0
    # ease-out-cubic on a slow 60-tick cycle gives smooth ring motion
    phase = _ease_out_cubic((tick % 60) / 60.0)
    t_hue = math.sin(tick / 30.0) * _HUE_DRIFT_AMPLITUDE
    base_hue = (_SINISTER_PURPLE_HSL[0] + t_hue) % 360.0

    # 3 concentric rings at radii proportional to terminal size
    ring_chars = ['*', '+', 'o']
    out: list[list[str]] = [[' '] * width for _ in range(rows)]
    out_colors: list[list[str]] = [[''] * width for _ in range(rows)]

    for ring_idx in range(3):
        radius_x = (width / 2.0 - 2) * (0.4 + ring_idx * 0.25)
        radius_y = (rows / 2.0 - 1) * (0.4 + ring_idx * 0.25)
        # particles per ring
        n_particles = 12 + ring_idx * 4
        for i in range(n_particles):
            angle = (i / n_particles) * 2 * math.pi + phase * 2 * math.pi + (ring_idx * math.pi / 6)
            x = int(cx + radius_x * math.cos(angle))
            y = int(cy + radius_y * math.sin(angle) * 0.5)  # squash vertically for terminal aspect
            if 0 <= x < width and 0 <= y < rows:
                # HSV hue varies per particle for shimmer
                particle_hue = (base_hue + i * 8.0) % 360.0
                r, g, b = _hsv_to_rgb(particle_hue, 0.75, 0.6 + 0.4 * math.sin(tick / 20.0 + i))
                out[y][x] = ring_chars[ring_idx]
                out_colors[y][x] = _ansi_fg_rgb(r, g, b)

    # Compose final lines with embedded ANSI escapes
    lines = []
    for y in range(rows):
        line_parts = []
        last_color = ''
        for x in range(width):
            ch = out[y][x]
            color = out_colors[y][x]
            if ch == ' ':
                if last_color:
                    line_parts.append(_ANSI_RESET)
                    last_color = ''
                line_parts.append(' ')
            else:
                if color != last_color:
                    line_parts.append(color)
                    last_color = color
                line_parts.append(ch)
        if last_color:
            line_parts.append(_ANSI_RESET)
        lines.append(''.join(line_parts))
    return lines


def _logo_banner(width: int) -> list[str]:
    """Clean Sinister wordmark. Block-letter ASCII art (5 lines).
    Operator 22:21Z 'add the fucking logo' + 23:15Z 'sinister to look good'.
    The prior orbit_rings + janky wordmark version was scrapped.
    """
    # 5-row block-letter SINISTER using box-drawing characters
    logo = [
        " ████  ███  █   █  ███  ████  ████  ████  ████   ",
        " █     █    █▌  █  █    █     █     █     █     ",
        " ████  █    █▐  █  ███  ████  █     ████  ████   ",
        "    █  █    █ ▌ █    █     █  █     █     █     ",
        " ████  ███  █  ▐█  ███  ████  █     ████  ████   ",
    ]
    centered = []
    for ln in logo:
        pad = max(0, (width - len(ln)) // 2)
        centered.append(' ' * pad + ln)
    return centered


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_GLOBAL_STATE: _AnimState | None = None
_TICK_INTERVAL_SEC = 0.08   # 80ms == ~12 fps, matches jcode tick cadence


def start_background_animation(width: int = 80, rows: int = 5) -> None:
    """Start the jcode-style animation thread. Idempotent."""
    global _GLOBAL_STATE
    if _GLOBAL_STATE is not None and not _GLOBAL_STATE.stop:
        return
    _GLOBAL_STATE = _AnimState()
    state = _GLOBAL_STATE

    def _tick_loop() -> None:
        while not state.stop:
            try:
                frame = _render_orbit_rings(width, rows, state.tick)
                with state.lock:
                    state.frame_lines = frame
                    state.tick += 1
            except Exception:
                pass
            time.sleep(_TICK_INTERVAL_SEC)

    t = threading.Thread(target=_tick_loop, daemon=True, name='eve-animation')
    t.start()


def stop_background_animation() -> None:
    global _GLOBAL_STATE
    if _GLOBAL_STATE is not None:
        _GLOBAL_STATE.stop = True
        _GLOBAL_STATE = None


def render_banner(width: int = 80, rows: int = 5, with_logo: bool = True) -> list[str]:
    """Render the Sinister wordmark with subtle HSV hue shimmer per character.
    No orbit_rings particles (the prior overlay made the banner look junky per
    operator 23:15Z 'sinister to look good'). Pure logo + per-char color tick.

    Returns list of pre-formatted lines ready to print. Non-blocking.
    """
    # Keep the animation thread alive (drives the hue tick) but no longer use its
    # orbit_rings frame; we read the tick counter for color shimmer only.
    if _GLOBAL_STATE is None or _GLOBAL_STATE.stop:
        start_background_animation(width=width, rows=rows)
    state = _GLOBAL_STATE
    tick = state.tick if state is not None else 0

    if not with_logo:
        return []

    raw_logo = _logo_banner(width)
    # Per-character HSV hue rotation -- Sinister purple base, gentle drift +/-30deg
    base_hue = (_SINISTER_PURPLE_HSL[0] + math.sin(tick / 25.0) * 30.0) % 360.0
    sat = 0.78
    val = 0.85
    colored = []
    for row_idx, ln in enumerate(raw_logo):
        parts = []
        last_color = ''
        for col_idx, ch in enumerate(ln):
            if ch == ' ':
                if last_color:
                    parts.append(_ANSI_RESET)
                    last_color = ''
                parts.append(' ')
            else:
                # Per-character hue offset for shimmer; row-offset adds vertical
                # gradient so block letters aren't monochrome
                hue = (base_hue + (col_idx * 1.8) + (row_idx * 6.0)) % 360.0
                r, g, b = _hsv_to_rgb(hue, sat, val)
                color = _ansi_fg_rgb(r, g, b)
                if color != last_color:
                    parts.append(color)
                    last_color = color
                parts.append(ch)
        if last_color:
            parts.append(_ANSI_RESET)
        colored.append(''.join(parts))
    return colored


def render_static_logo(width: int = 80) -> list[str]:
    """Return just the static logo (no animation thread). For terminals without
    color or where animation would interfere with screen-reader / CI."""
    return _logo_banner(width)


# ---------------------------------------------------------------------------
# Self-test (run module directly to preview animation)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import sys
    cols = 80
    rows = 5
    try:
        cols, _ = os.get_terminal_size()
        if cols > 120:
            cols = 120
    except Exception:
        pass
    start_background_animation(width=cols, rows=rows)
    try:
        for _ in range(60):  # ~5 sec preview
            frame = render_banner(width=cols, rows=rows)
            # Clear + redraw
            sys.stdout.write("\033[H\033[J")
            for line in frame:
                sys.stdout.write(line + "\n")
            sys.stdout.flush()
            time.sleep(0.08)
    finally:
        stop_background_animation()
