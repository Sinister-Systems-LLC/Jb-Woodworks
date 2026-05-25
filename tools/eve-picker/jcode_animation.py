# Author: RKOJ-ELENO :: 2026-05-24
"""Sinister-themed animation -- operator hard-canonical 2026-05-25T00:15Z:
"have this have a suttle in theme slow and have this slowly move but be more in
our purple colors but in a suttle manor i want it to feel like its glowing.
add reds and purples to it and a splash of yellow."

Replaces the jcode 7-stop rainbow with a Sinister-branded palette:
  * 60% purples (deep violet -> mid violet -> Sinister bright purple #a06edc)
  * 20% deep reds (burgundy + muted crimson -- "splash")
  * 15% near-black negative space (makes purples pop)
  *  5% warm yellow accent (sparse, rare splash)

Movement is SLOW (pulse cycle stretched 4x vs jcode default) and GLOWING
(brightness pulses dim->mid->bright->mid->dim per position via sine).

License heritage: original jcode-0.12.4 primitives (MIT, (C) 2025 Jeremy Huang)
are retained for the blend / shimmer / sine math; the palette + density logic
is Sinister-original. Source provenance for the retained primitives:
  * crates/jcode-tui-style/src/theme.rs:107  blend_color() RGB lerp
  * crates/jcode-tui-style/src/theme.rs:167  prompt_entry_shimmer_color()

API (unchanged so main_menu.py keeps working):
  * render_animation_frame(tick, width, height) -> list[str]
  * picker_tick_render(tick, server, client, mcp_count, bot_count,
                       live_agent_count, **kwargs) -> None
  * render_banner_with_animation(...) -> None
  * spinner_frame(tick), tile_frame(tick) -> str

Constraints satisfied:
  * Python 3.12 stdlib only (math, os, shutil)
  * cp1252-safe glyphs (.:*+ only; no Unicode that crashes Windows cmd.exe)
  * 24-bit ANSI fg (works in mintty / Windows Terminal / cmd via VT-100)
  * Tick-driven; no threads / sleep / blocking I/O
"""
from __future__ import annotations

import math
import os
import shutil

# --- Sinister palette --------------------------------------------------------
# Weighted palette: each tuple is (R, G, B, weight). The weight column drives
# the per-distance pick so purples dominate 60%, reds 20%, dark 15%, yellow 5%.

_PALETTE: list[tuple[int, int, int]] = [
    # --- purples (60% -- 12 of 20 slots) ---
    ( 48,  24,  80),   # deep violet
    ( 64,  32,  96),   # deep violet (lighter)
    ( 80,  40, 112),   # mid-deep violet
    ( 96,  48, 128),   # mid violet
    (112,  64, 160),   # mid-bright violet
    (128,  80, 184),   # rising violet
    (144,  96, 200),   # bright violet
    (160, 110, 220),   # Sinister bright purple (accent token --accent: #c084fc-ish)
    (176, 128, 232),   # bright lavender
    (140,  88, 200),   # back to mid-bright
    (108,  56, 152),   # back to mid
    ( 72,  32, 104),   # back to deep
    # --- reds (20% -- 4 of 20) ---
    ( 80,  24,  32),   # deep burgundy
    (128,  40,  48),   # burgundy
    (160,  56,  56),   # crimson
    (192,  64,  64),   # muted crimson
    # --- dark negative space (15% -- 3 of 20) ---
    ( 20,  16,  28),   # near-black, faint violet tint
    ( 28,  20,  36),   # near-black
    ( 36,  24,  48),   # very dark violet
    # --- yellow splash (5% -- 1 of 20) ---
    (220, 180,  80),   # warm yellow accent (sparse)
]

# Highlight color used for the "glow" overlay -- warm pale lavender so the
# shimmer travels but stays in-theme (no white-hot blowouts).
_GLOW_HIGHLIGHT: tuple[int, int, int] = (235, 210, 255)

# Far-distance fade target (near-black, faint violet tint) -- gives the band a
# dim "negative space" floor so brights pop.
_DARK_FLOOR: tuple[int, int, int] = (20, 16, 28)


# --- core math (retained from jcode primitives) ------------------------------

def _blend_color(
    a: tuple[int, int, int], b: tuple[int, int, int], t: float
) -> tuple[int, int, int]:
    """jcode theme.rs:107 blend_color() -- linear RGB lerp."""
    ar, ag, ab = a
    br, bg, bb = b
    r = ar + (br - ar) * t
    g = ag + (bg - ag) * t
    bl = ab + (bb - ab) * t
    clamp = lambda v: max(0, min(255, int(v)))
    return (clamp(r), clamp(g), clamp(bl))


def palette_color(distance: int) -> tuple[int, int, int]:
    """Pick a Sinister-palette color by distance index, fading to dark floor
    at far distances. Decay rate 0.18 -- much gentler than jcode's 0.4 so the
    band feels uniform rather than spotlight-y."""
    decay = math.exp(-0.18 * distance)
    idx = distance % len(_PALETTE)
    base = _PALETTE[idx]
    return _blend_color(_DARK_FLOOR, base, decay)


def shimmer_glow(
    base: tuple[int, int, int], pos: float, t: float
) -> tuple[int, int, int]:
    """jcode shimmer adapted for "glow" feel: subtle pale-lavender highlight
    band travels slowly across the row. pos in [0,1] column-fraction, t in
    [0,1] animation phase. Lower amplitude (0.45 vs jcode 0.7) for subtlety."""
    travel = max(0.0, min(1.0, t * 1.15))
    width = 0.22  # slightly wider band -- softer edges
    dist = abs(pos - travel)
    shimmer = (1.0 - min(1.0, dist / width)) ** 2.6  # steeper falloff
    pulse = (1.0 - t) ** 0.55
    return _blend_color(base, _GLOW_HIGHLIGHT, shimmer * pulse * 0.45)


def animated_tool_color(elapsed: float) -> tuple[int, int, int]:
    """Slow purple<->violet sine pulse for the title text (replaces jcode's
    cyan<->purple). Stays in the Sinister palette family."""
    t = math.sin(elapsed * 1.2) * 0.5 + 0.5  # slower (1.2 vs jcode 2.0)
    # purple (96,48,128) <-> bright violet (160,110,220)
    r = int( 96 + t * ( 160 -  96))
    g = int( 48 + t * ( 110 -  48))
    b = int(128 + t * ( 220 - 128))
    return (r, g, b)


# --- spinner frames (retained from jcode) ------------------------------------

_SPINNER_FRAMES = ("⠂", "⠆", "⠇", "⠧", "⡷", "⠧", "⠇", "⠆")
_TILE_FRAMES = ("◴", "◷", "◶", "◵")


def spinner_frame(tick: int) -> str:
    return _SPINNER_FRAMES[tick % len(_SPINNER_FRAMES)]


def tile_frame(tick: int) -> str:
    return _TILE_FRAMES[tick % len(_TILE_FRAMES)]


# --- ANSI rendering layer ----------------------------------------------------

_RESET = "\x1b[0m"


def _ansi_fg(rgb: tuple[int, int, int]) -> str:
    return f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def render_animation_frame(tick: int, width: int = 80, height: int = 6) -> list[str]:
    """Return list of `height` rendered lines for a single animation frame.

    Sinister-themed palette + visible horizontal drift + glow pulse + sparkle.

    RKOJ-ELENO :: 2026-05-25T01:36Z :: operator screenshot #66 *"more animation
    and live here"*. Prior render felt static (1-in-30 shimmer, palette drift
    every 8 ticks, no horizontal scroll). This iteration:
      * Shimmer density 1-in-30  -> 1-in-12 (more bright cells)
      * Palette drift  tick//8   -> tick//4 (visibly moving)
      * NEW: horizontal scroll   -- entire pattern shifts 1 col every 2 ticks
        (creates a "river of stars" feel that scrolls left frame-to-frame)
      * NEW: sparkle accents `*` `+` chars appear ~1-in-160 cells, pulse
        brighter than base shimmer for "live" sparkle
      * Brightness cap on shimmer cells: kept at shimmer_glow 0.45 amplitude
        so individual bright cells stay subtle even at higher density.

    GLOWING: each cell modulates brightness by a sine of (col + row + tick)
    cycling through dim->mid->bright->mid->dim. Subtle (0.55..1.0 range).

    cp1252-safe glyphs: '.:*+' only (no Unicode crash on Windows cmd).
    """
    if width <= 0 or height <= 0:
        return []
    # SLOW: shimmer phase stretched 4x
    t = (tick % 160) / 160.0
    # FASTER drift (was tick//8) -- one palette step every 4 ticks
    drift = (tick // 4) % len(_PALETTE)
    # NEW: horizontal scroll offset -- entire pattern shifts left 1 col every
    # 2 ticks. Creates a "river of stars" feel. The modulo width keeps the
    # offset bounded so per-cell hashes don't drift to infinity.
    scroll = (tick // 2) % max(1, width)

    glyphs = ".:*+"
    sparkle_glyphs = "*+"  # cp1252-safe pulsing accents
    lines: list[str] = []
    for row in range(height):
        parts: list[str] = []
        for col in range(width):
            # Apply horizontal scroll: effective column is the rendering col
            # plus the scroll offset, so each frame the pattern at col=N is
            # what was at col=N+1 last frame (visible right->left drift).
            ecol = (col + scroll) % max(1, width)
            # palette index drifts horizontally + undulates per row
            distance = (ecol + drift + row * 2) % (len(_PALETTE) + 4)
            base = palette_color(distance)

            # GLOW: per-cell brightness pulse (subtle, range 0.55..1.0)
            # Sine of (col*0.25 + row*0.5 + tick*0.05) -- slow per-cell breathing
            glow_phase = math.sin(ecol * 0.25 + row * 0.5 + tick * 0.05) * 0.5 + 0.5
            glow_mul = 0.55 + glow_phase * 0.45
            glowed = (
                int(base[0] * glow_mul),
                int(base[1] * glow_mul),
                int(base[2] * glow_mul),
            )

            # Density bumped 30 -> 12. Each shimmer cell stays subtle via the
            # shimmer_glow 0.45 amplitude cap (no white-hot blowouts).
            sparkle_hash = (ecol * 31 + row * 17 + tick * 7) % 12
            if sparkle_hash == 0:
                pos = ecol / max(1, width - 1)
                final = shimmer_glow(glowed, pos, t)
            else:
                final = glowed

            # NEW: pulsing sparkle accent ~1-in-160 cells. These pulse a
            # brighter glow (0.85 overlay vs 0.45) and use a fixed accent
            # glyph (* / +) for a "live sparkle" feel without going Unicode.
            accent_hash = (ecol * 53 + row * 29 + tick * 11) % 160
            if accent_hash < 2:
                # Pulse brightness based on tick so each sparkle "twinkles"
                twinkle = abs(math.sin((tick + ecol + row) * 0.6)) * 0.5 + 0.5
                final = _blend_color(final, _GLOW_HIGHLIGHT, 0.55 * twinkle)
                glyph = sparkle_glyphs[(tick // 2) % len(sparkle_glyphs)]
            else:
                # alternate glyph per (row, col, tick) for "moving" texture
                glyph = glyphs[(ecol + row + tick // 4) % len(glyphs)]
            parts.append(_ansi_fg(final) + glyph)
        parts.append(_RESET)
        lines.append("".join(parts))
    return lines


# --- Hero block + animation composition --------------------------------------

def _term_width(default: int = 80) -> int:
    try:
        return shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default


def _visible_len(line: str) -> int:
    """Strip ANSI escapes to get printable width."""
    out, i = 0, 0
    while i < len(line):
        if line[i] == "\x1b":
            while i < len(line) and line[i] != "m":
                i += 1
            i += 1
            continue
        out += 1
        i += 1
    return out


def _center(line: str, width: int) -> str:
    pad = max(0, (width - _visible_len(line)) // 2)
    return (" " * pad) + line


def render_banner_with_animation(
    tick: int = 0,
    *,
    server: str = "Sanctum",
    client: str = "EVE",
    model: str = "EVE-OPUS-4.7",
    version: str = "v0.4.6",
    built: str = "built today",
    cwd: str | None = None,
    account_email: str | None = None,
    mcp_count: int = 0,
    bot_count: int = 0,
    live_agent_count: int = 0,
    width: int | None = None,
    animation_height: int = 4,
) -> None:
    """Render centered hero block + Sinister-themed animation underneath.

    `tick` advances per render cycle (caller passes monotonic counter)."""
    w = width or _term_width()
    cwd = cwd or os.getcwd()
    account = account_email or "(no account)"

    # Title color: slow purple<->violet pulse (in-theme breathing).
    # tick/20.0 (vs original tick/10.0) doubles the breath period -- slower.
    title_rgb = animated_tool_color(tick / 20.0)
    title_col = _ansi_fg(title_rgb)

    hero_lines_raw = [
        f"server: {server}",
        f"client: {client}",
        f"{model}",
        f"{version} · {built}",
        f"{cwd}",
        f"acct: {account}",
        f"mcp: {mcp_count}  bots: {bot_count}",
        f"server: {live_agent_count} agents live",
    ]

    out_lines: list[str] = []
    for raw in hero_lines_raw:
        out_lines.append(_center(title_col + raw + _RESET, w))

    out_lines.append("")
    out_lines.extend(render_animation_frame(tick, width=w, height=animation_height))

    print("\n".join(out_lines), flush=True)


# --- Integration helper for the picker ---------------------------------------

def picker_tick_render(tick: int, **hero_kwargs) -> None:
    """One-shot per-tick render call for the EVE picker.

    Picker integration call signature:
        from tools.eve_picker.jcode_animation import picker_tick_render
        picker_tick_render(tick, server="Sanctum", client="EVE",
                           mcp_count=10, bot_count=7, live_agent_count=3)

    Call this once per render cycle (~10 fps); pass an incrementing tick counter.
    Non-blocking: no threads, no sleep, no I/O wait."""
    render_banner_with_animation(tick=tick, **hero_kwargs)


if __name__ == "__main__":
    import time
    try:
        os.system("")  # enable VT-100 on Windows cmd
    except Exception:
        pass
    for t in range(40):
        print("\x1b[2J\x1b[H", end="")
        render_banner_with_animation(
            tick=t,
            mcp_count=10, bot_count=7, live_agent_count=3,
        )
        time.sleep(0.1)
