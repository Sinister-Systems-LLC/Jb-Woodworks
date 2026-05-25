# Author: RKOJ-ELENO :: 2026-05-25
"""Ancestral Remotion render engine.

P0 scope:
- Render a single entity glyph
- Apply shimmer rule (hue rotation per frame)
- Render a pulsing energy bar
- No real stdin tap yet (energy is passed in)

P1+ adds: full rule vocabulary, palette HSV-lerp, real EnergyTap, sidecar.
"""

from __future__ import annotations

import math
import os
import sys

from . import palettes
from . import entities


def supports_truecolor() -> bool:
    """Check if the terminal advertises truecolor support."""
    if os.environ.get("ANCESTRAL_NO_TRUECOLOR") == "1":
        return False
    return os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")


def _color_for_hex(hex6: str, ansi_256: int) -> str:
    """Return the appropriate ANSI prefix for a (hex, 256-idx) pair."""
    if supports_truecolor():
        return palettes.ansi_fg_truecolor(hex6)
    return palettes.ansi_fg_256(ansi_256)


def render_frame(
    entity: dict,
    frame: int,
    energy: float,
    width: int = 60,
) -> str:
    """Render a single frame of an entity at given frame counter + energy.

    Args:
        entity: entity definition dict (from entities.load())
        frame: monotonic frame counter (drives animation phase)
        energy: 0.0 (idle) to 1.0 (high energy)
        width: terminal width in columns (for bar sizing)

    Returns:
        A multi-line string containing ANSI-escaped output for the frame.
        Does NOT include cursor positioning — caller decides placement.
    """
    energy = max(0.0, min(1.0, energy))
    is_hot = energy >= 0.7

    palette_name = (
        entity["high_energy_palette"] if is_hot else entity["idle_palette"]
    )
    pal = palettes.get_palette(palette_name)

    # Pick role cycling for visual interest per row
    role_order = ["primary", "secondary", "tertiary", "highlight"]
    # Add danger/dim depending on which palette
    if "danger" in pal:
        role_order.append("danger")
    if "dim" in pal:
        role_order.append("dim")

    lines: list[str] = []

    # Top header
    header_hex, header_256 = pal["highlight"]
    title = f"--- ANCESTRAL REMOTION :: {entity['name']} ---"
    lines.append(_color_for_hex(header_hex, header_256) + title.center(width) + palettes.RESET)

    # Glyph with per-row palette cycling + shimmer
    for i, row in enumerate(entity["glyph"]):
        role = role_order[(i + frame) % len(role_order)]
        hex6, ansi_256 = pal[role]
        # Shimmer = hue rotation when hot
        if is_hot:
            hex6 = palettes.hsv_shift(hex6, (frame * 12) % 360)
        # Pad/clip row to width
        padded_row = row[:width].ljust(width)
        lines.append(_color_for_hex(hex6, ansi_256) + padded_row + palettes.RESET)

    # Energy bar
    bar_width = max(10, width - 20)
    filled = int(round(energy * bar_width))
    bar = "[" + "#" * filled + "_" * (bar_width - filled) + "]"
    # Pulse: when hot, append a flicker dot 1 frame in 8
    pulse_dot = " *" if (is_hot and frame % 8 == 0) else "  "
    pct = int(round(energy * 100))
    bar_hex, bar_256 = pal["primary"]
    energy_line = f" ENERGY: {bar} {pct:3d}%{pulse_dot}"
    lines.append(_color_for_hex(bar_hex, bar_256) + energy_line.ljust(width) + palettes.RESET)

    # Footer
    footer_hex, footer_256 = pal.get("dim", pal["primary"])
    personality = entity["personality"]
    if len(personality) > width - 4:
        personality = personality[: width - 7] + "..."
    footer = "  " + personality
    lines.append(_color_for_hex(footer_hex, footer_256) + footer.ljust(width) + palettes.RESET)

    return "\n".join(lines)


def demo_render(
    project_key: str = "sanctum",
    frames: int = 30,
    out=None,
) -> int:
    """Run a demo: render N frames of the given project's entity to stdout.

    Energy ramps from 0.0 to 1.0 over the run so the operator sees
    idle -> mid -> hot palette + animation.

    Returns: exit code (0 success).
    """
    if out is None:
        out = sys.stdout

    try:
        entity = entities.load(project_key)
    except Exception as e:
        print(f"[ERROR] entity load failed for {project_key!r}: {e}", file=sys.stderr)
        return 2

    # Try to get terminal width; fall back to 60
    try:
        size = os.get_terminal_size()
        width = max(40, min(80, size.columns))
    except OSError:
        width = 60

    for f in range(frames):
        # Sigmoid ramp 0..1 over `frames`, then back down (breathing)
        if frames <= 1:
            energy = 0.5
        else:
            phase = f / max(1, frames - 1)
            # Use sin so we breathe in + out
            energy = (math.sin(phase * math.pi) ** 2)
        frame_str = render_frame(entity, frame=f, energy=energy, width=width)
        # Separator line so multi-frame output is visually parseable
        out.write(f"--- frame {f + 1}/{frames}  energy={energy:.2f} ---\n")
        out.write(frame_str + "\n")
        out.write(palettes.RESET + "\n")
    out.flush()
    return 0
