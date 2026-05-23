# Author: RKOJ-ELENO :: 2026-05-23
"""Generate the JB Woodworks favicon set as PNG.

Run once when the brand mark changes:
    python scripts/make_favicons.py

Writes into ../static/img/:
    favicon-16.png
    favicon-32.png
    favicon-48.png
    favicon-180.png  (apple-touch-icon)
    favicon-192.png  (Android / PWA)
    favicon-512.png  (high-DPI / PWA splash)
    favicon.ico      (multi-resolution legacy)

Pure Pillow - no SVG renderer required.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BLACK = (8, 8, 8, 255)
WHITE = (255, 255, 255, 255)
GOLD = (201, 168, 76, 255)

OUT = Path(__file__).resolve().parent.parent / "static" / "img"
OUT.mkdir(parents=True, exist_ok=True)


def _font(size: int) -> ImageFont.FreeTypeFont:
    """Try a few Windows-bundled fonts that look right for JB Inter-Black-ish."""
    for path in (
        r"C:\Windows\Fonts\arialbd.ttf",   # Arial Bold - widely available
        r"C:\Windows\Fonts\arialbi.ttf",
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\seguibl.ttf",   # Segoe UI Black if present
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render(size: int, *, with_underline: bool = True) -> Image.Image:
    img = Image.new("RGBA", (size, size), BLACK)
    draw = ImageDraw.Draw(img)

    # Rounded-corner background hint - draw on top with anti-aliased mask
    corner = max(2, size // 6)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), corner, fill=255)
    img.putalpha(mask)

    # Pick font size so "JB" fills ~62% of the canvas width
    font_size = int(size * 0.62)
    font = _font(font_size)

    # Measure
    bbox = draw.textbbox((0, 0), "JB", font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (size - text_w) // 2 - bbox[0]
    y = (size - text_h) // 2 - bbox[1]
    # Nudge up so underline can sit beneath
    if with_underline and size >= 32:
        y -= int(size * 0.05)

    draw.text((x, y), "JB", font=font, fill=WHITE)

    # Gold underline only on icons big enough to read it
    if with_underline and size >= 32:
        bar_w = int(size * 0.55)
        bar_h = max(2, int(size * 0.05))
        bar_x = (size - bar_w) // 2
        bar_y = int(size * 0.78)
        draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), fill=GOLD)

    return img


def main() -> None:
    sizes = [16, 32, 48, 180, 192, 512]
    for s in sizes:
        img = render(s, with_underline=(s >= 32))
        out = OUT / f"favicon-{s}.png"
        img.save(out, "PNG")
        print(f"  wrote {out}")

    # Multi-res .ico for legacy support
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    base = render(48, with_underline=True)
    base.save(OUT / "favicon.ico", format="ICO", sizes=ico_sizes)
    print(f"  wrote {OUT / 'favicon.ico'}")


if __name__ == "__main__":
    main()
