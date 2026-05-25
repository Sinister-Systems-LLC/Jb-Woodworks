"""make-claude-icon.py -- generate assets/claude-icon.ico for spawned claude mintty windows.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 (eve-exe lane iter-1): "i need claude icon working asap".

Generates a Sinister-themed Claude glyph (stylized "C") in multi-resolution .ico
on transparent background so spawned mintty windows running Claude Code show a
distinct, recognizable icon in the Windows taskbar (instead of the generic
mintty/cmd icon).

Design:
  - Round purple glyph badge (Sinister-canonical PURPLE #c084fc gradient over DARKP #6b21a8).
  - Bold stylized "C" cut-out in white over the gradient.
  - Transparent background (mintty's title-bar / taskbar shows it cleanly).
  - Emits 16/24/32/48/64/128/256 pixel sizes (Windows picks per-context).

Idempotent. Rerunning regenerates byte-identical output.

Usage:
  python make-claude-icon.py [--out PATH]

Default --out: <script-dir>/assets/claude-icon.ico
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEFAULT_OUT = Path(__file__).parent / "assets" / "claude-icon.ico"
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

PURPLE_BRIGHT = (216, 180, 254, 255)
PURPLE_MID    = (192, 132, 252, 255)
PURPLE_DARK   = (107, 33, 168, 255)
WHITE         = (250, 245, 255, 255)
TRANSPARENT   = (0, 0, 0, 0)


def _radial_gradient(size: int, inner: tuple[int, int, int, int], outer: tuple[int, int, int, int]) -> Image.Image:
    """Soft radial gradient inner -> outer, clipped to a circle."""
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    cx = cy = size / 2.0
    rmax = size / 2.0
    pixels = img.load()
    for y in range(size):
        for x in range(size):
            dx = (x + 0.5) - cx
            dy = (y + 0.5) - cy
            d = (dx * dx + dy * dy) ** 0.5
            if d > rmax:
                continue
            t = min(1.0, d / rmax)
            r = int(round(inner[0] * (1 - t) + outer[0] * t))
            g = int(round(inner[1] * (1 - t) + outer[1] * t))
            b = int(round(inner[2] * (1 - t) + outer[2] * t))
            a = int(round(inner[3] * (1 - t) + outer[3] * t))
            edge = 1.0 - max(0.0, (d - (rmax - 1.5)) / 1.5)
            a = int(round(a * max(0.0, min(1.0, edge))))
            pixels[x, y] = (r, g, b, a)
    return img


def _draw_c_glyph(canvas: Image.Image, size: int) -> None:
    """Bold stylized 'C' cut into the glyph badge."""
    draw = ImageDraw.Draw(canvas)
    pad = max(2, size // 6)
    outer_box = (pad, pad, size - pad, size - pad)
    stroke_w = max(2, size // 7)
    draw.arc(outer_box, start=35, end=325, fill=WHITE, width=stroke_w)
    tip_w = stroke_w // 2
    cx, cy = size / 2.0, size / 2.0
    rmid = (size - 2 * pad) / 2.0
    import math
    for angle_deg in (35, 325):
        a = math.radians(angle_deg)
        ex = cx + rmid * math.cos(a)
        ey = cy + rmid * math.sin(a)
        draw.ellipse(
            (ex - tip_w, ey - tip_w, ex + tip_w, ey + tip_w),
            fill=WHITE,
        )


def render_one(size: int) -> Image.Image:
    badge = _radial_gradient(size, PURPLE_BRIGHT, PURPLE_DARK)
    overlay = Image.new("RGBA", (size, size), TRANSPARENT)
    _draw_c_glyph(overlay, size)
    badge = Image.alpha_composite(badge, overlay)
    return badge


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    largest = render_one(256)
    extras = [render_one(s) for (s, _) in ICO_SIZES if s != 256]
    largest.save(args.out, format="ICO", sizes=ICO_SIZES, append_images=extras)
    print(f"[OK] wrote {args.out} ({args.out.stat().st_size} bytes, {len(ICO_SIZES)} sizes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
