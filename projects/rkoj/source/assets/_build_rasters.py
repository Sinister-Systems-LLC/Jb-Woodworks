"""Author: RKOJ-ELENO :: 2026-05-21

One-shot raster builder for the RKOJ Sanctum brand kit.

Generates:
  - icon-32.png, icon-64.png, icon-128.png, icon-256.png, icon-512.png
    (devil mascot with Sanctum purple gradient, transparent bg)
  - splash-1290x2796.png (iOS splash: gradient bg + mascot + RKOJ wordmark + subtitle)

Strategy: we render the mascot directly in Pillow (not via cairosvg) so the
build degrades gracefully on systems without cairosvg. The geometry mirrors
the SVG paths in mascot.svg, scaled into each target raster.

Requires: Pillow (graceful-degraded if missing — see assets/README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.stderr.write("Pillow missing. Run: pip install Pillow\n")
    sys.exit(1)


ASSETS_DIR = Path(__file__).resolve().parent

# Sanctum palette
PURPLE_HALO = (195, 157, 255, 255)   # #C39DFF
PURPLE_ACCENT = (160, 110, 255, 255) # #A06EFF
PURPLE_DEEP = (122, 61, 212, 255)    # #7A3DD4
LIGHT_PURPLE = (232, 214, 255, 255)  # #E8D6FF
BG = (14, 10, 20, 255)               # #0E0A14
BG_GLOW = (42, 31, 61, 255)          # #2A1F3D


def lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def gradient_color(y_norm: float) -> tuple:
    """Vertical gradient: halo (top) -> accent (mid) -> deep (bottom)."""
    if y_norm < 0.5:
        return lerp(PURPLE_HALO, PURPLE_ACCENT, y_norm * 2.0)
    return lerp(PURPLE_ACCENT, PURPLE_DEEP, (y_norm - 0.5) * 2.0)


def draw_mascot(size: int) -> Image.Image:
    """Render the devil mascot at `size`x`size` with transparent bg."""
    # Work at 4x for anti-aliased downscale
    scale = 4
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Source-SVG coords are 0..100. We render into an s-pixel canvas centered.
    def p(x: float, y: float) -> tuple[float, float]:
        return (x / 100.0 * s, y / 100.0 * s)

    # We don't have per-pixel gradient stroke in Pillow easily; instead pick
    # a stroke color per shape based on its centroid Y.
    def color_for_y(y_pct: float) -> tuple:
        return gradient_color(max(0.0, min(1.0, y_pct / 100.0)))

    stroke_w = max(1, int(2.4 / 100 * s))

    # Horns (filled triangles)
    horn_color = color_for_y(16)
    draw.polygon([p(22, 10), p(18, 22), p(26, 22)], fill=horn_color)
    draw.polygon([p(78, 10), p(82, 22), p(74, 22)], fill=horn_color)

    # Cranium outline (rounded blob — approximate the SVG cubic with an ellipse + lower jaw rect)
    cranium_color = color_for_y(48)
    # Upper head: ellipse from (18,16) to (82,70)
    draw.ellipse([p(18, 16), p(82, 70)], outline=cranium_color, width=stroke_w)
    # Lower jaw / chin: two rects + connector
    # 28,70 -> 28,80 -> 40,80 -> 40,86 -> 60,86 -> 60,80 -> 72,80 -> 72,70
    jaw_pts = [p(28, 70), p(28, 80), p(40, 80), p(40, 86),
               p(60, 86), p(60, 80), p(72, 80), p(72, 70)]
    draw.line(jaw_pts, fill=cranium_color, width=stroke_w, joint="curve")

    # Eyes (filled circles)
    eye_color = color_for_y(48)
    for cx in (38, 62):
        draw.ellipse([p(cx - 6, 42), p(cx + 6, 54)], fill=eye_color)

    # Nose (filled diamond-ish)
    nose_color = color_for_y(62)
    draw.polygon([p(50, 56), p(46, 66), p(50, 68), p(54, 66)], fill=nose_color)

    # Teeth (horizontal line + 3 vertical ticks)
    teeth_color = color_for_y(75)
    draw.line([p(36, 72), p(64, 72)], fill=teeth_color, width=stroke_w)
    for tx in (42, 50, 58):
        draw.line([p(tx, 72), p(tx, 78)], fill=teeth_color, width=stroke_w)

    # Slight glow: blur a copy and composite under the line work
    glow = img.filter(ImageFilter.GaussianBlur(radius=s / 80))
    combined = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    combined = Image.alpha_composite(combined, glow)
    combined = Image.alpha_composite(combined, img)

    # Downscale to target with high-quality filter
    return combined.resize((size, size), Image.LANCZOS)


def build_icons() -> list[Path]:
    written: list[Path] = []
    for sz in (32, 64, 128, 256, 512):
        out = ASSETS_DIR / f"icon-{sz}.png"
        draw_mascot(sz).save(out, "PNG", optimize=True)
        written.append(out)
        print(f"  wrote {out.name} ({out.stat().st_size:,} bytes)")
    return written


def find_font(size: int) -> ImageFont.FreeTypeFont:
    """Try common Windows/macOS/Linux faces, fall back to default bitmap."""
    candidates = [
        "segoeuib.ttf", "segoeui.ttf",
        "arialbd.ttf", "arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def build_splash() -> Path:
    W, H = 1290, 2796
    img = Image.new("RGBA", (W, H), BG)
    px = img.load()

    # Vertical purple-radial gradient: dark bg at edges, BG_GLOW pulsing through center vertical band
    cx, cy = W // 2, int(H * 0.40)
    max_r = ((W // 2) ** 2 + (H // 2) ** 2) ** 0.5
    for y in range(H):
        for x in range(W):
            dx, dy = x - cx, y - cy
            d = (dx * dx + dy * dy) ** 0.5
            t = min(1.0, d / max_r)
            # near-center -> BG_GLOW, far -> BG
            color = lerp(BG_GLOW, BG, t * 1.2)
            px[x, y] = color
    # Soft halo
    img = img.filter(ImageFilter.GaussianBlur(radius=8))

    draw = ImageDraw.Draw(img)

    # Mascot at top (~25% from top, 360px square)
    mascot_size = 360
    mascot = draw_mascot(mascot_size)
    mx = (W - mascot_size) // 2
    my = int(H * 0.20)
    img.alpha_composite(mascot, (mx, my))

    # RKOJ wordmark (center, large)
    word_font = find_font(220)
    word = "RKOJ"
    wbbox = draw.textbbox((0, 0), word, font=word_font)
    ww = wbbox[2] - wbbox[0]
    wh = wbbox[3] - wbbox[1]
    wx = (W - ww) // 2
    wy = int(H * 0.45)
    # subtle drop shadow
    draw.text((wx + 6, wy + 6), word, font=word_font, fill=(0, 0, 0, 160))
    draw.text((wx, wy), word, font=word_font, fill=LIGHT_PURPLE)

    # Subtitle
    sub_font = find_font(64)
    subtitle = "Sinister Sanctum"
    sbbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sw = sbbox[2] - sbbox[0]
    sx = (W - sw) // 2
    sy = wy + wh + 64
    draw.text((sx, sy), subtitle, font=sub_font, fill=PURPLE_HALO)

    # EVE accent line
    eve_font = find_font(40)
    eve = "EVE • RKOJ-ELENO"
    ebbox = draw.textbbox((0, 0), eve, font=eve_font)
    ew = ebbox[2] - ebbox[0]
    ex = (W - ew) // 2
    ey = int(H * 0.88)
    draw.text((ex, ey), eve, font=eve_font, fill=PURPLE_ACCENT)

    out = ASSETS_DIR / "splash-1290x2796.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"  wrote {out.name} ({out.stat().st_size:,} bytes)")
    return out


def main() -> int:
    print("Building Sanctum brand-kit rasters...")
    print(f"Output dir: {ASSETS_DIR}")
    print("Icons:")
    build_icons()
    print("Splash:")
    build_splash()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
