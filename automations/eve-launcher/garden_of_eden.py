#!/usr/bin/env python3
"""Garden of Eden v4 -- TOTAL REDO with Unicode blocks + ANSI background apples.

Author: RKOJ-ELENO :: 2026-05-25
Operator hard-canonical 2026-05-25T01:42Z verbatim:
  "the tree looks worse than it did completely redo ti"

V4 vs V3:
  - Apples now use ANSI BACKGROUND COLORS (solid filled blocks; impossible to miss)
  - Canopy uses Unicode shading blocks (.... and #### look messy; switching to
    half-blocks for soft round silhouette)
  - Compact 50x28 canvas (fits in operator's standard 80-col terminal)
  - Organic tree shape (lobed canopy clusters; not a perfect ellipse)
  - Trunk is solid █ chars
  - 7 apples placed in distinct visible spots
"""

from __future__ import annotations

import math
import os
import random
import sys
import time
from typing import List, Tuple, Set

CANVAS_W = 56
CANVAS_H = 28

# Canopy block chars (light -> dark)
CANOPY_DENSE = "█"   # full block
CANOPY_MID   = "▓"   # dark shade 75%
CANOPY_LIGHT = "▒"   # medium shade 50%
CANOPY_EDGE  = "░"   # light shade 25%

# Apple shape: 4-wide x 2-tall solid block (with bg color)
APPLE_W = 4
APPLE_H = 2

# 7 apple anchor positions (top-left of 4x2 block); spread around canopy
APPLE_POS: List[Tuple[int, int]] = [
    (3,  14),   # top-center-left
    (5,  32),   # top-center-right
    (7,   8),   # mid-far-left
    (9,  22),   # mid-center
    (11, 38),   # mid-right
    (13, 18),   # lower-center-left
    (15, 30),   # lower-center-right
]

# Per-cell color palette positions (cyberpunk hues 0..360)
_HUE_CANOPY = [275.0, 290.0, 305.0, 250.0, 320.0, 220.0]
_HUE_APPLE_FG = 60.0     # warm yellow highlight on apple
_HUE_APPLE_BG = 358.0    # deep red bg
_HUE_APPLE_RIM = 25.0    # orange rim
_HUE_LEAF = 110.0
_HUE_STEM = 35.0
_HUE_TRUNK = 285.0
_HUE_ROOT = 200.0

_FADE_FRAMES = 18
_TICK_INTERVAL = 0.06


def _hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
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


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _bg(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


RESET = "\033[0m"


def _build_canopy_mask() -> List[List[str]]:
    """Build canopy density mask. 5 lobed clusters + 1 main center ellipse."""
    grid = [[" "] * CANVAS_W for _ in range(CANVAS_H)]
    center_x = CANVAS_W // 2
    # Main canopy ellipse
    canopy_cy = 10
    canopy_rx = 22
    canopy_ry = 8
    for y in range(CANVAS_H):
        for x in range(CANVAS_W):
            dx = (x - center_x) / canopy_rx
            dy = (y - canopy_cy) / canopy_ry
            d = dx * dx + dy * dy
            if d <= 1.0:
                if d < 0.4:
                    grid[y][x] = CANOPY_DENSE
                elif d < 0.7:
                    grid[y][x] = CANOPY_MID
                elif d < 0.9:
                    grid[y][x] = CANOPY_LIGHT
                else:
                    grid[y][x] = CANOPY_EDGE
    # Lobes -- 4 smaller bumps for organic silhouette
    lobes = [
        (4, center_x - 18, 8, 4),   # left bump
        (4, center_x + 16, 8, 4),   # right bump
        (1, center_x - 8, 10, 4),   # top-left bump
        (1, center_x + 8, 10, 4),   # top-right bump
    ]
    for (lcy, lcx, lrx, lry) in lobes:
        for y in range(max(0, lcy - lry - 1), min(CANVAS_H, lcy + lry + 1)):
            for x in range(max(0, lcx - lrx - 1), min(CANVAS_W, lcx + lrx + 1)):
                dx = (x - lcx) / max(1, lrx)
                dy = (y - lcy) / max(1, lry)
                d = dx * dx + dy * dy
                if d <= 1.0:
                    cur = grid[y][x]
                    if cur == " " or cur == CANOPY_EDGE:
                        grid[y][x] = CANOPY_MID if d < 0.6 else CANOPY_LIGHT
    return grid


_CANOPY = _build_canopy_mask()


def _build_apple_cells() -> Set[Tuple[int, int]]:
    """Cells that should be rendered as apple (solid bg-colored block)."""
    cells = set()
    for (ay, ax) in APPLE_POS:
        for dy in range(APPLE_H):
            for dx in range(APPLE_W):
                cells.add((ay + dy, ax + dx))
    return cells


_APPLE_CELLS = _build_apple_cells()


def _build_apple_stem_leaf() -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    stems = set(); leaves = set()
    for (ay, ax) in APPLE_POS:
        sy = ay - 1
        sx = ax + APPLE_W // 2
        if 0 <= sy < CANVAS_H and 0 <= sx < CANVAS_W:
            stems.add((sy, sx))
        ly = ay - 1
        lx = sx + 1
        if 0 <= ly < CANVAS_H and 0 <= lx < CANVAS_W:
            leaves.add((ly, lx))
    return stems, leaves


_STEMS, _LEAVES = _build_apple_stem_leaf()


def _build_trunk_cells() -> Set[Tuple[int, int]]:
    cells = set()
    center_x = CANVAS_W // 2
    trunk_top = 18
    for y in range(trunk_top, CANVAS_H - 2):
        depth = y - trunk_top
        half_w = 2 + depth // 4
        for x in range(center_x - half_w, center_x + half_w + 1):
            if 0 <= x < CANVAS_W:
                cells.add((y, x))
    return cells


_TRUNK_CELLS = _build_trunk_cells()


def _build_root_cells() -> Set[Tuple[int, int]]:
    cells = set()
    center_x = CANVAS_W // 2
    root_y = CANVAS_H - 2
    # 1 row of ground with 5 spreading roots
    for dx in range(-20, 21):
        x = center_x + dx
        if 0 <= x < CANVAS_W:
            cells.add((root_y, x))
            if root_y + 1 < CANVAS_H and abs(dx) < 18:
                cells.add((root_y + 1, x))
    return cells


_ROOT_CELLS = _build_root_cells()


def _render_frame(tick: int) -> str:
    fade = min(1.0, tick / _FADE_FRAMES) if tick < _FADE_FRAMES else 1.0
    # Subtle wind sway: shift canopy 0/1/0/-1 chars over slow cycle
    sway = int(round(math.sin(tick / 90.0 * 2 * math.pi) * 1.5))
    # Lightning ~0.5%
    lightning = (random.random() < 0.005) and tick > _FADE_FRAMES
    # Apple pulse cycle
    apple_pulse = 0.85 + 0.15 * math.sin(tick / 8.0)

    out: List[str] = []
    for y in range(CANVAS_H):
        parts: List[str] = []
        last_seq = ""
        for x in range(CANVAS_W):
            # Determine cell type (canopy / apple / stem / leaf / trunk / root / empty)
            src_x = x - sway if y < 17 else x  # only canopy + apples sway
            if not (0 <= src_x < CANVAS_W):
                if last_seq: parts.append(RESET); last_seq = ""
                parts.append(" ")
                continue
            cell = (y, src_x)
            ch = _CANOPY[y][src_x] if y < len(_CANOPY) else " "

            # --- APPLES (background-colored solid; impossible to miss) ---
            if cell in _APPLE_CELLS:
                # Apple position within its 4x2 block (for shading)
                for (ay, ax) in APPLE_POS:
                    if 0 <= y - ay < APPLE_H and 0 <= src_x - ax < APPLE_W:
                        ry = y - ay; rx = src_x - ax
                        # Top row + leftmost col: rim hue
                        # Top-left cell: highlight
                        if ry == 0 and rx <= 1:
                            bg_hue = _HUE_APPLE_BG
                            fg_hue = _HUE_APPLE_FG
                            bg_v = apple_pulse * fade * 0.85
                            fg_v = fade * 0.95
                            glyph = "▀"  # upper half block (highlight)
                        elif ry == APPLE_H - 1:
                            bg_hue = _HUE_APPLE_BG
                            fg_hue = _HUE_APPLE_RIM
                            bg_v = apple_pulse * fade * 0.75
                            fg_v = fade * 0.6
                            glyph = "▄"  # lower half block (shadow)
                        else:
                            bg_hue = _HUE_APPLE_BG
                            fg_hue = _HUE_APPLE_RIM
                            bg_v = apple_pulse * fade * 0.9
                            fg_v = fade * 0.7
                            glyph = "█"  # full block
                        br, bg_, bb = _hsv_to_rgb(bg_hue, 1.0, bg_v)
                        fr, fg_, fb = _hsv_to_rgb(fg_hue, 0.95, fg_v)
                        seq = _bg(br, bg_, bb) + _fg(fr, fg_, fb)
                        if seq != last_seq: parts.append(seq); last_seq = seq
                        parts.append(glyph)
                        break
                continue

            if cell in _STEMS:
                if last_seq: parts.append(RESET); last_seq = ""
                r, g, b = _hsv_to_rgb(_HUE_STEM, 0.7, 0.55 * fade)
                seq = _fg(r, g, b)
                parts.append(seq + "│")  # vertical line
                last_seq = seq
                continue
            if cell in _LEAVES:
                if last_seq: parts.append(RESET); last_seq = ""
                r, g, b = _hsv_to_rgb(_HUE_LEAF, 0.95, 0.8 * fade)
                seq = _fg(r, g, b)
                parts.append(seq + "◀")  # left triangle (leaf)
                last_seq = seq
                continue

            # --- TRUNK ---
            if cell in _TRUNK_CELLS:
                if last_seq: parts.append(RESET); last_seq = ""
                trunk_hue = (_HUE_TRUNK + math.sin(tick / 14.0 + y) * 12.0) % 360.0
                v = (0.55 + 0.1 * math.sin(tick / 9.0 + x / 5.0)) * fade
                r, g, b = _hsv_to_rgb(trunk_hue, 0.6, v)
                seq = _fg(r, g, b)
                parts.append(seq + "█")
                last_seq = seq
                continue

            # --- ROOTS / GROUND ---
            if cell in _ROOT_CELLS:
                if last_seq: parts.append(RESET); last_seq = ""
                root_hue = (_HUE_ROOT + math.sin(tick / 14.0 + x / 5.0) * 25.0) % 360.0
                v = (0.4 + 0.12 * math.sin(tick / 11.0 + x / 4.0)) * fade
                r, g, b = _hsv_to_rgb(root_hue, 0.6, v)
                seq = _fg(r, g, b)
                parts.append(seq + ("▀" if (x + tick // 5) % 4 == 0 else "▄"))
                last_seq = seq
                continue

            # --- CANOPY ---
            if ch == " ":
                if last_seq: parts.append(RESET); last_seq = ""
                parts.append(" ")
                continue
            if lightning:
                seq = _fg(255, 255, 255)
                if seq != last_seq: parts.append(seq); last_seq = seq
                parts.append(ch)
                continue
            # HSV shimmer; hue drifts slowly + per-cell offset
            base_hue = _HUE_CANOPY[int((tick / 20.0)) % len(_HUE_CANOPY)]
            char_hue = (base_hue + (x * 0.8) + (y * 2.5) +
                        math.sin(tick / 11.0 + y + x / 6.0) * 28.0) % 360.0
            sat = 0.85 if ch in (CANOPY_DENSE, CANOPY_MID) else 0.75
            base_v = {CANOPY_DENSE: 0.78, CANOPY_MID: 0.62, CANOPY_LIGHT: 0.5, CANOPY_EDGE: 0.38}.get(ch, 0.5)
            val = (base_v + 0.12 * math.sin(tick / 9.0 + x / 3.0)) * fade
            r, g, b = _hsv_to_rgb(char_hue, sat, val)
            seq = _fg(r, g, b)
            if seq != last_seq: parts.append(seq); last_seq = seq
            parts.append(ch)
        if last_seq: parts.append(RESET)
        out.append("".join(parts))
    return "\n".join(out)


def _enable_vt_on_windows() -> None:
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


def main() -> int:
    _enable_vt_on_windows()
    if os.name == "nt":
        # Force UTF-8 for Unicode block chars
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    tick = 0
    try:
        sys.stdout.write("\033[2J\033[H\033[?25l")
        while True:
            frame = _render_frame(tick)
            sys.stdout.write("\033[H")
            title = "❦  G A R D E N   O F   E D E N  ❦"
            title_hue = (275.0 + math.sin(tick / 8.0) * 60.0) % 360.0
            tr, tg, tb = _hsv_to_rgb(title_hue, 0.95, 0.98)
            sys.stdout.write("\n" + _fg(tr, tg, tb) + title.center(CANVAS_W) + RESET + "\n\n")
            sys.stdout.write(frame)
            sys.stdout.write("\n")
            sys.stdout.write(_fg(140, 130, 200) + "  Sinister Sideprojects ∙ cyberpunk garden ∙ 7 apples ∙ Ctrl+C to exit" + RESET + "\n")
            sys.stdout.flush()
            tick += 1
            time.sleep(_TICK_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + "\033[?25h\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
