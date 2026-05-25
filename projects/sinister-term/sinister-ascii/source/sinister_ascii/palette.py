# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# SA-PH1 :: palette.py — the 5 anchor color families + HSV rotation primitive.
# Operator vision: reds / blues / greens / indigos / violets — each project's
# entity picks one dominant + two accents from this 5-family table.
#
# All math is deterministic (pure functions of t); the engine drives `t` via a
# monotonic clock so animations stay smooth across pauses + restarts.

from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColorFamily:
    """One anchor family. The hue_range is in degrees [0, 360)."""
    name: str
    hue_start_deg: float
    hue_end_deg: float
    saturation: float = 0.85
    value: float = 0.95

    def hue_at(self, t: float) -> float:
        """Return the hue (degrees) for normalized t in [0, 1)."""
        # Handle the red wrap (335-25) by treating it as a continuous range
        if self.hue_start_deg > self.hue_end_deg:
            span = (360.0 - self.hue_start_deg) + self.hue_end_deg
            raw = self.hue_start_deg + (t % 1.0) * span
            return raw % 360.0
        span = self.hue_end_deg - self.hue_start_deg
        return self.hue_start_deg + (t % 1.0) * span


# The canonical 5 anchor families. Per the operator vision quote (2026-05-25):
# "reds, blues, greens indigos violets"
CRIMSON_RED   = ColorFamily("crimson",        335.0,  25.0,  0.90, 0.95)
COBALT_BLUE   = ColorFamily("cobalt",         215.0, 255.0,  0.85, 0.95)
VERDANT_GREEN = ColorFamily("verdant",         80.0, 155.0,  0.80, 0.92)
ROYAL_INDIGO  = ColorFamily("royal_indigo",   255.0, 280.0,  0.85, 0.90)
SINISTER_VIOLET = ColorFamily("sinister_violet", 270.0, 315.0, 0.80, 0.98)

ANCHORS: tuple[ColorFamily, ...] = (
    CRIMSON_RED, COBALT_BLUE, VERDANT_GREEN, ROYAL_INDIGO, SINISTER_VIOLET,
)


@dataclass(frozen=True)
class Palette:
    """A per-entity palette = one dominant family + two accents."""
    dominant: ColorFamily
    accent_a: ColorFamily
    accent_b: ColorFamily
    rotation_period_s: float = 11.0  # irrational-ish — avoids visible loop point


def hsv_to_rgb_bytes(h_deg: float, s: float, v: float) -> tuple[int, int, int]:
    """Standard HSV (h in degrees) -> 24-bit RGB tuple."""
    r, g, b = colorsys.hsv_to_rgb((h_deg % 360.0) / 360.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def rgb_to_ansi_truecolor(r: int, g: int, b: int, *, background: bool = False) -> str:
    """ANSI 24-bit truecolor escape — same format Windows Terminal / mintty
    understand. Foreground unless background=True."""
    code = 48 if background else 38
    return f"\033[{code};2;{r};{g};{b}m"


def color_at(palette: Palette, t_seconds: float, *, mix: float = 0.0) -> tuple[int, int, int]:
    """Return an (r, g, b) byte tuple for the palette at absolute time t.

    `mix` in [0, 1] lerps between the dominant (0) and a weighted accent blend (1).
    The hue rotation uses the operator-mined jcode pattern:
    `hue = (time_hue + t * 160.0) % 360.0`, ease-out-cubic on the mix value.
    """
    # Ease-out-cubic on mix (jcode ui_animations.rs:1-50 parity)
    e = 1.0 - (1.0 - max(0.0, min(1.0, mix))) ** 3

    period = palette.rotation_period_s
    if period <= 0:
        period = 11.0  # safety
    norm_t = (t_seconds / period) % 1.0

    h_dom = palette.dominant.hue_at(norm_t)
    # Two accents rotate at slightly offset phases so the blend feels alive
    h_a = palette.accent_a.hue_at((norm_t + 0.31) % 1.0)
    h_b = palette.accent_b.hue_at((norm_t + 0.67) % 1.0)

    # Accent_b weight grows as e approaches 1.0
    h_accent = h_a * (1.0 - e * 0.5) + h_b * (e * 0.5)
    h_final = h_dom * (1.0 - e) + h_accent * e

    s = palette.dominant.saturation
    v = palette.dominant.value
    return hsv_to_rgb_bytes(h_final, s, v)


def reset() -> str:
    """ANSI reset escape — restore default fg/bg."""
    return "\033[0m"


# Per-project palette presets — names match projects.json keys.
# Picks: dominant + two accents from ANCHORS, with rotation_period chosen to
# feel distinct per entity.
PROJECT_PALETTES: dict[str, Palette] = {
    "sinister-sanctum":   Palette(SINISTER_VIOLET, ROYAL_INDIGO, COBALT_BLUE, rotation_period_s=13.0),
    "sinister-term":      Palette(SINISTER_VIOLET, ROYAL_INDIGO, CRIMSON_RED, rotation_period_s=11.0),
    "sinister-forge":     Palette(CRIMSON_RED, SINISTER_VIOLET, COBALT_BLUE, rotation_period_s=9.5),
    "sinister-mind":      Palette(COBALT_BLUE, ROYAL_INDIGO, VERDANT_GREEN, rotation_period_s=14.0),
    "sinister-overseer":  Palette(VERDANT_GREEN, COBALT_BLUE, SINISTER_VIOLET, rotation_period_s=12.0),
    "sinister-chatbot":   Palette(CRIMSON_RED, COBALT_BLUE, VERDANT_GREEN, rotation_period_s=10.5),
    "sinister-vault":     Palette(ROYAL_INDIGO, SINISTER_VIOLET, VERDANT_GREEN, rotation_period_s=17.0),
    "sinister-memory":    Palette(ROYAL_INDIGO, COBALT_BLUE, SINISTER_VIOLET, rotation_period_s=15.5),
    "sinister-kernel-apk": Palette(COBALT_BLUE, ROYAL_INDIGO, CRIMSON_RED, rotation_period_s=8.5),
    "sinister-panel":     Palette(SINISTER_VIOLET, VERDANT_GREEN, COBALT_BLUE, rotation_period_s=11.5),
    "sinister-link":      Palette(VERDANT_GREEN, SINISTER_VIOLET, ROYAL_INDIGO, rotation_period_s=13.5),
    "sinister-os":        Palette(SINISTER_VIOLET, CRIMSON_RED, COBALT_BLUE, rotation_period_s=16.0),
    # SA-PH7 (iter-48) — fill remaining 13 project entities so picker
    # selections always resolve to a unique palette (no fallback collisions).
    "sinister-emulator":  Palette(CRIMSON_RED, COBALT_BLUE, SINISTER_VIOLET, rotation_period_s=10.0),
    "sinister-bus":       Palette(COBALT_BLUE, SINISTER_VIOLET, VERDANT_GREEN, rotation_period_s=13.7),
    "sinister-designer":  Palette(SINISTER_VIOLET, CRIMSON_RED, ROYAL_INDIGO, rotation_period_s=12.3),
    "sinister-sleight":   Palette(ROYAL_INDIGO, CRIMSON_RED, SINISTER_VIOLET, rotation_period_s=18.0),
    "sinister-snap-emu":  Palette(VERDANT_GREEN, ROYAL_INDIGO, COBALT_BLUE, rotation_period_s=14.3),
    "sinister-hieroglyphics": Palette(ROYAL_INDIGO, SINISTER_VIOLET, CRIMSON_RED, rotation_period_s=19.3),
    "sinister-watcher":   Palette(VERDANT_GREEN, SINISTER_VIOLET, CRIMSON_RED, rotation_period_s=15.0),
    "sinister-bumble":    Palette(VERDANT_GREEN, CRIMSON_RED, COBALT_BLUE, rotation_period_s=11.7),
    "eve-exe":            Palette(SINISTER_VIOLET, COBALT_BLUE, VERDANT_GREEN, rotation_period_s=12.7),
    "eve-compliance":     Palette(CRIMSON_RED, SINISTER_VIOLET, ROYAL_INDIGO, rotation_period_s=9.0),
    "letstext":           Palette(COBALT_BLUE, VERDANT_GREEN, CRIMSON_RED, rotation_period_s=10.7),
    "showmasters":        Palette(ROYAL_INDIGO, VERDANT_GREEN, COBALT_BLUE, rotation_period_s=16.3),
    "jb-woodworks":       Palette(CRIMSON_RED, VERDANT_GREEN, ROYAL_INDIGO, rotation_period_s=14.7),
}


def for_project(project_key: str | None) -> Palette:
    """Return the palette for a project key, falling back to Sanctum-master."""
    if not project_key:
        return PROJECT_PALETTES["sinister-sanctum"]
    return PROJECT_PALETTES.get(project_key, PROJECT_PALETTES["sinister-sanctum"])


def golden_ratio_phase(i: int, base: float = 0.0) -> float:
    """Deterministic anti-loop phase offset using the golden ratio conjugate
    (1/phi ≈ 0.6180339887). Use this to spread N entities across the hue wheel
    without ever lining up to the same period."""
    phi_conj = (math.sqrt(5.0) - 1.0) / 2.0
    return (base + i * phi_conj) % 1.0
