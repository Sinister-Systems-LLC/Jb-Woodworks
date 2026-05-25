# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# SA-PH4 :: renderer.py — ANSI 24-bit truecolor frame writer.
# Writes one frame as a single string (caller decides where to write it).
# Per-frame budget: <16ms (60 FPS); per-keystroke budget: <2ms.

from __future__ import annotations

import os
import shutil
import sys
import time
from dataclasses import dataclass

from sinister_ascii import palette
from sinister_ascii.entities._base import Entity
from sinister_ascii.motion import MotionFrame


ANSI_RESET = "\033[0m"
ANSI_HIDE_CURSOR = "\033[?25l"
ANSI_SHOW_CURSOR = "\033[?25h"
ANSI_CLEAR_SCREEN = "\033[2J"
ANSI_HOME = "\033[H"


@dataclass
class Viewport:
    cols: int
    rows: int

    @classmethod
    def from_terminal(cls, default_cols: int = 80, default_rows: int = 24) -> "Viewport":
        try:
            sz = shutil.get_terminal_size((default_cols, default_rows))
            return cls(cols=max(20, sz.columns), rows=max(8, sz.lines))
        except Exception:
            return cls(cols=default_cols, rows=default_rows)


def _norm_to_cell(x_norm: float, y_norm: float, vp: Viewport,
                  *, margin: int = 2) -> tuple[int, int]:
    """Map (x,y) in [-1,1] to (col,row) cells, leaving a margin from edges."""
    cx = vp.cols / 2.0
    cy = vp.rows / 2.0
    half_w = max(1.0, cx - margin)
    half_h = max(1.0, cy - margin)
    col = int(cx + x_norm * half_w)
    row = int(cy + y_norm * half_h * 0.85)
    return (
        max(0, min(vp.cols - 1, col)),
        max(0, min(vp.rows - 1, row)),
    )


def frame_string(entity: Entity, t_seconds: float, *,
                 activity_signal: float = 0.0,
                 viewport: Viewport | None = None,
                 trail_length: int = 5) -> str:
    """Render one frame as an ANSI string with a small motion trail."""
    vp = viewport or Viewport.from_terminal()
    parts: list[str] = [ANSI_HOME]

    if vp.cols >= 50 and vp.rows >= 14:
        parts.append(_starfield(vp, t_seconds, entity.palette))

    for i in range(trail_length, 0, -1):
        t_past = t_seconds - i * 0.08
        if t_past < 0:
            continue
        f = entity.frame(t_past, activity_signal=activity_signal)
        col, row = _norm_to_cell(f.x, f.y, vp)
        dim_factor = 1.0 - (i / (trail_length + 1)) * 0.7
        r, g, b = palette.color_at(entity.palette, t_past,
                                   mix=min(1.0, f.intensity * dim_factor))
        r = int(r * dim_factor)
        g = int(g * dim_factor)
        b = int(b * dim_factor)
        glyph = entity.pick_glyph(f.intensity * dim_factor)
        parts.append(_place(col, row, palette.rgb_to_ansi_truecolor(r, g, b) + glyph))

    f_now = entity.frame(t_seconds, activity_signal=activity_signal)
    col, row = _norm_to_cell(f_now.x, f_now.y, vp)
    r, g, b = palette.color_at(entity.palette, t_seconds, mix=f_now.intensity)
    glyph = entity.pick_glyph(f_now.intensity)
    parts.append(_place(col, row, palette.rgb_to_ansi_truecolor(r, g, b) + glyph))

    tag = f"  {entity.name}  ·  {entity.project_key}"
    if len(tag) > vp.cols - 2:
        tag = tag[: vp.cols - 5] + "..."
    dim_violet = palette.rgb_to_ansi_truecolor(96, 64, 140)
    parts.append(_place(0, vp.rows - 1, dim_violet + tag))

    parts.append(ANSI_RESET)
    return "".join(parts)


def _place(col: int, row: int, text: str) -> str:
    return f"\033[{row + 1};{col + 1}H{text}"


_STARFIELD_CACHE: dict[tuple[int, int], list[tuple[int, int]]] = {}


def _starfield(vp: Viewport, t_seconds: float, pal: palette.Palette) -> str:
    key = (vp.cols, vp.rows)
    stars = _STARFIELD_CACHE.get(key)
    if stars is None:
        density = max(8, (vp.cols * vp.rows) // 220)
        stars = []
        phi = (1.0 + 5 ** 0.5) / 2.0
        for i in range(density):
            x = (i * phi * 0.27) % 1.0
            y = (i * phi * 0.41) % 1.0
            stars.append((int(x * vp.cols), int(y * (vp.rows - 1))))
        _STARFIELD_CACHE[key] = stars

    out = []
    shimmer = (t_seconds % 25.0) / 25.0
    for i, (c, r) in enumerate(stars):
        if r >= vp.rows - 1:
            continue
        local = (shimmer + (i * 0.137)) % 1.0
        brightness = 0.10 + 0.15 * abs(local - 0.5)
        rr, gg, bb = palette.color_at(pal, t_seconds + i, mix=0.0)
        rr = int(rr * brightness)
        gg = int(gg * brightness)
        bb = int(bb * brightness)
        out.append(_place(c, r, palette.rgb_to_ansi_truecolor(rr, gg, bb) + "·"))
    return "".join(out)


def clear_screen() -> str:
    return ANSI_CLEAR_SCREEN + ANSI_HOME


def enable_alt_screen() -> str:
    return "\033[?1049h" + ANSI_HIDE_CURSOR + ANSI_CLEAR_SCREEN + ANSI_HOME


def disable_alt_screen() -> str:
    return ANSI_RESET + ANSI_SHOW_CURSOR + "\033[?1049l"
