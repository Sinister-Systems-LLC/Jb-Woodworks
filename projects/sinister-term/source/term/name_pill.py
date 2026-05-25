# Sinister Term :: name_pill.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Minimal name-pill renderer. Writes a single ANSI line showing the
# project + mode + loop/swarm flags. Default-off in app.py per operator
# feedback (2026-05-25T12:02:58Z "this looks like shit and its super laggy");
# only emitted when SINISTER_TERM_OVERLAY=on.

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional


# Project key → accent color (matches Sanctum theme tokens)
ACCENT_BY_KEY = {
    "sinister-sanctum":     "#A06EFF",
    "sinister-term":        "#A06EFF",
    "sinister-forge":       "#FF6E6E",
    "sinister-mind":        "#6EFF9A",
    "sinister-overseer":    "#FFC86E",
    "sinister-chatbot":     "#6ED1FF",
    "sinister-vault":       "#FFD86E",
    "sinister-memory":      "#D86EFF",
    "sinister-kernel-apk":  "#FF9A6E",
    "sinister-panel":       "#9AFF6E",
    "sinister-link":        "#6E9AFF",
    "sinister-os":          "#FF6EC8",
    "eve-exe":              "#FFFFFF",
}


@dataclass
class PillStyle:
    project_key: str
    label: str
    mode: str = "active"
    loop: bool = False
    swarm: bool = False
    status: str = "alive"
    accent: str = "#A06EFF"


def default_style(project_key: str, mode: str = "active", loop: bool = False,
                  swarm: bool = False, status: str = "alive") -> PillStyle:
    accent = ACCENT_BY_KEY.get(project_key, "#A06EFF")
    label = project_key.replace("sinister-", "").upper()
    return PillStyle(
        project_key=project_key, label=label, mode=mode,
        loop=loop, swarm=swarm, status=status, accent=accent,
    )


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) != 6:
        return (160, 110, 255)
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception:
        return (160, 110, 255)


def render(style: PillStyle) -> str:
    """Return the ANSI string for the pill. No newline."""
    r, g, b = _hex_to_rgb(style.accent)
    bg = f"\x1b[48;2;{r};{g};{b}m"
    fg = "\x1b[38;2;0;0;0m"
    reset = "\x1b[0m"
    flags = []
    if style.loop:
        flags.append("L")
    if style.swarm:
        flags.append("S")
    flag_str = "/" + "".join(flags) if flags else ""
    return f"{bg}{fg} ◈ {style.label} {style.mode}{flag_str} {reset}"


def write_pill(style: PillStyle, stream=None) -> None:
    s = stream if stream is not None else sys.stdout
    try:
        if not getattr(s, "isatty", lambda: False)():
            return
        s.write(render(style) + "\n")
        s.flush()
    except Exception:
        pass
