# Author: RKOJ-ELENO :: 2026-05-25
"""Palette tables.

Canonical color rows per project family. Stdlib only; truecolor preferred,
256-color fallback path documented in docs/02-color-palettes.md.

Each palette is a dict with 5 roles: primary / secondary / tertiary /
highlight / dim_or_danger. Each role is a (hex, ansi_256) tuple.
"""

from __future__ import annotations

import colorsys

# (hex_without_hash, ansi_256_index)
PALETTES: dict[str, dict[str, tuple[str, int]]] = {
    # --- Sanctum (violet) ---
    "violet-core": {
        "primary": ("6366f1", 99),
        "secondary": ("a855f7", 135),
        "tertiary": ("c084fc", 177),
        "highlight": ("f5f3ff", 255),
        "dim": ("312e81", 54),
    },
    "violet-core-burning": {
        "primary": ("a855f7", 135),
        "secondary": ("ec4899", 199),
        "tertiary": ("f0abfc", 219),
        "highlight": ("ffffff", 231),
        "danger": ("fbbf24", 220),
    },
    # --- Sinister Panel (red) ---
    "red-control": {
        "primary": ("b91c1c", 124),
        "secondary": ("ef4444", 196),
        "tertiary": ("f97316", 208),
        "highlight": ("fef3c7", 230),
        "dim": ("450a0a", 52),
    },
    "red-burning": {
        "primary": ("dc2626", 160),
        "secondary": ("fbbf24", 220),
        "tertiary": ("fde047", 226),
        "highlight": ("ffffff", 231),
        "danger": ("fb923c", 215),
    },
    # --- Sinister OS (blue) ---
    "blue-deep": {
        "primary": ("1e3a8a", 18),
        "secondary": ("2563eb", 27),
        "tertiary": ("38bdf8", 75),
        "highlight": ("e0f2fe", 195),
        "dim": ("0c1e3a", 17),
    },
    "blue-storm": {
        "primary": ("06b6d4", 38),
        "secondary": ("818cf8", 105),
        "tertiary": ("f0f9ff", 230),
        "highlight": ("ffffff", 231),
        "danger": ("fef08a", 228),
    },
    # --- Sinister Snap-API-Quantum (indigo) ---
    "indigo-fringe": {
        "primary": ("4338ca", 56),
        "secondary": ("7c3aed", 92),
        "tertiary": ("cbd5e1", 252),
        "highlight": ("ddd6fe", 189),
        "dim": ("1e1b4b", 17),
    },
    "indigo-collapse": {
        "primary": ("8b5cf6", 99),
        "secondary": ("f0abfc", 219),
        "tertiary": ("d946ef", 200),
        "highlight": ("ffffff", 231),
        "danger": ("fbbf24", 220),
    },
    # --- Sinister Sleight (green) ---
    "green-growth": {
        "primary": ("16a34a", 34),
        "secondary": ("22c55e", 41),
        "tertiary": ("84cc16", 112),
        "highlight": ("fef3c7", 230),
        "dim": ("14532d", 22),
    },
    "green-electric": {
        "primary": ("4ade80", 121),
        "secondary": ("2dd4bf", 80),
        "tertiary": ("67e8f9", 117),
        "highlight": ("ffffff", 231),
        "danger": ("f59e0b", 214),
    },
}


def hex_to_rgb(hex6: str) -> tuple[int, int, int]:
    """Convert 6-char hex (no #) to (r, g, b) ints."""
    hex6 = hex6.lstrip("#")
    return (int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert (r, g, b) ints to 6-char hex (no #)."""
    return "".join(f"{c:02x}" for c in rgb)


def hsv_shift(hex6: str, hue_deg: float) -> str:
    """Rotate hue by hue_deg degrees, preserve s/v. Return new hex (no #)."""
    r, g, b = hex_to_rgb(hex6)
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h = (h + (hue_deg / 360.0)) % 1.0
    nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
    return rgb_to_hex((int(nr * 255), int(ng * 255), int(nb * 255)))


def ansi_fg_truecolor(hex6: str) -> str:
    """ANSI truecolor foreground escape for the given hex."""
    r, g, b = hex_to_rgb(hex6)
    return f"\033[38;2;{r};{g};{b}m"


def ansi_fg_256(idx: int) -> str:
    """ANSI 256-color foreground escape."""
    return f"\033[38;5;{idx}m"


RESET = "\033[0m"


def get_palette(name: str) -> dict[str, tuple[str, int]]:
    """Look up a palette by name. Falls back to violet-core on miss."""
    return PALETTES.get(name, PALETTES["violet-core"])
