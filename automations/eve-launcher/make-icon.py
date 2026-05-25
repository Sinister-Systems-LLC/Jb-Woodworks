"""make-icon.py — regenerate assets/eve-icon.ico from a source PNG.

Author: RKOJ-ELENO :: 2026-05-24

Operator hard-canonical 2026-05-24T23:35Z (reinforcement of 18:51Z):
  "put the fucking logo here with no background as the fucking exe logo
   C:\\Users\\Zonia\\Desktop\\2026-05-23T133146Z-banner-hero-statement.png"

The source PNG is RGB (no alpha) with a dark purple/black background
(~RGB 24-54 luminance). We chroma-key out the dark background by brightness
threshold so the logo sits on transparent pixels in the .ico.

Pipeline:
  1. Open the source PNG, convert RGB -> RGBA.
  2. Walk every pixel: if max(R,G,B) < ALPHA_CUTOFF, set alpha=0.
     Between ALPHA_CUTOFF and ALPHA_FULL, ramp alpha smoothly (anti-alias).
  3. Crop to the logo's bounding box (trim transparent border).
  4. Fit-into-square with transparent padding (preserves aspect).
  5. Emit a multi-size .ico (16/24/32/48/64/128/256) at assets/eve-icon.ico.

Idempotent: rerunning with the same source produces an identical .ico.

Usage:
  python make-icon.py [--source PATH] [--out PATH] [--cutoff N] [--full N]

Defaults:
  --source  C:/Users/Zonia/Desktop/2026-05-23T133146Z-banner-hero-statement.png
  --out     <script-dir>/assets/eve-icon.ico
  --cutoff  80   (max(R,G,B) below this -> alpha 0)
  --full    140  (max(R,G,B) above this -> alpha 255; ramp between)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image


DEFAULT_SOURCE = Path(r"C:\Users\Zonia\Desktop\2026-05-23T133146Z-banner-hero-statement.png")
DEFAULT_OUT = Path(__file__).parent / "assets" / "eve-icon.ico"
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def chroma_key_dark_bg(img: Image.Image, cutoff: int, full: int) -> Image.Image:
    """Convert dark background to transparent by brightness ramp.

    max(R,G,B) < cutoff      -> alpha = 0   (fully transparent)
    max(R,G,B) > full        -> alpha = 255 (fully opaque)
    cutoff <= bright <= full -> linear ramp (anti-alias edges)
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    span = max(1, full - cutoff)
    for y in range(h):
        for x in range(w):
            r, g, b, _a = pixels[x, y]
            bright = max(r, g, b)
            if bright < cutoff:
                pixels[x, y] = (r, g, b, 0)
            elif bright > full:
                pixels[x, y] = (r, g, b, 255)
            else:
                alpha = int(round(((bright - cutoff) / span) * 255))
                pixels[x, y] = (r, g, b, alpha)
    return img


def fit_into_square(img: Image.Image, size: int) -> Image.Image:
    img = img.convert("RGBA")
    # Trim transparent border before fitting (gets logo as large as possible)
    bbox = img.getbbox()
    if bbox is not None:
        img = img.crop(bbox)
    w, h = img.size
    scale = min(size / w, size / h)
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
    return canvas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--cutoff", type=int, default=80)
    ap.add_argument("--full", type=int, default=140)
    args = ap.parse_args()

    if not args.source.exists():
        print(f"[FAIL] source not found: {args.source}", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    src = Image.open(args.source)
    keyed = chroma_key_dark_bg(src, args.cutoff, args.full)

    largest = fit_into_square(keyed, 256)
    largest.save(args.out, format="ICO", sizes=ICO_SIZES)
    print(f"[OK] wrote {args.out} ({args.out.stat().st_size} bytes, {len(ICO_SIZES)} sizes)")
    print(f"     chroma-key cutoff={args.cutoff} full={args.full}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
