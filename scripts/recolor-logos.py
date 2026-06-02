"""
Author: RKOJ-ELENO :: 2026-05-24

Recolor JB Woodworks owner-supplied logos from dark grey on white to
brand gold (#c9a84c) on transparent. Produces named output assets in
public/img/branding/ + favicon variants in public/img/.

Inputs (from operator desktop, copied alongside this script for the run):
  - jbw-monogram-src.png        (standalone hexagon JBW icon)
  - jbw-horizontal-src.png      (icon + "J.B. WOODWORKS / Construction & Fabrication")
  - jbw-stacked-src.png         (stacked layout w/ small-scale variant below)

Outputs into public/img/branding/:
  - jbw-monogram.png            (gold/transparent, 1024px square)
  - jbw-wordmark-horizontal.png (gold/transparent, tight crop)
  - jbw-wordmark-stacked.png    (gold/transparent, tight crop)
  - jbw-monogram-on-ink.png     (gold mark on #080808 with padding, social use)

Outputs into public/img/ (favicons, replacing existing dark-color glyphs):
  - favicon-16.png, favicon-32.png, favicon-48.png, favicon-180.png,
    favicon-192.png, favicon-512.png, favicon.ico
"""
from pathlib import Path
from PIL import Image

GOLD = (201, 168, 76)        # #c9a84c
INK  = (8, 8, 8)             # #080808
WHITE_THRESHOLD = 215        # treat >=215 in all channels as background
BBOX_ALPHA_FLOOR = 32        # alpha threshold for bbox detection (ignore halo)

ROOT = Path(__file__).resolve().parent.parent           # projects/jb-woodworks
BRAND_DIR = ROOT / "public" / "img" / "branding"
IMG_DIR   = ROOT / "public" / "img"
SRC_DIR   = Path(__file__).resolve().parent / "_logo-src"


def recolor_to_gold_transparent(src_path: Path) -> Image.Image:
    """Replace any near-white pixel with transparent. Replace any darker pixel
    with brand gold, preserving original alpha as luminance-derived alpha so
    the antialiased edges stay smooth."""
    im = Image.open(src_path).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD:
                px[x, y] = (0, 0, 0, 0)
            else:
                # luminance 0 (black) -> alpha 255, white -> alpha 0
                lum = (r + g + b) / 3.0
                new_a = int(round((1.0 - lum / 255.0) * a))
                px[x, y] = (GOLD[0], GOLD[1], GOLD[2], new_a)
    return im


def trim_alpha(im: Image.Image, pad: int = 0, alpha_floor: int = BBOX_ALPHA_FLOOR) -> Image.Image:
    """Find bbox using a stricter alpha threshold so subtle anti-aliasing
    halos don't keep the canvas oversized."""
    alpha = im.split()[-1]
    # Replace every pixel below the alpha floor with 0 so getbbox ignores halos
    cleaned = alpha.point(lambda v: 255 if v >= alpha_floor else 0)
    bbox = cleaned.getbbox()
    if not bbox:
        return im
    cropped = im.crop(bbox)
    if pad <= 0:
        return cropped
    w, h = cropped.size
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    out.paste(cropped, (pad, pad))
    return out


def crop_to_mark_only(im: Image.Image) -> Image.Image:
    """For the stacked source: top tiny "JBW STACKED WORDMARK" label,
    main stacked wordmark (icon + name + tagline), bottom small favicon
    variant. Find contiguous content runs, drop the smallest top + bottom
    runs (header label + tiny favicon), keep the rest as one block."""
    alpha = im.split()[-1]
    w, h = alpha.size
    px = alpha.load()
    rows = []
    for y in range(h):
        total = 0
        for x in range(w):
            if px[x, y] >= BBOX_ALPHA_FLOOR:
                total += 1
        rows.append(total)
    floor_w = max(int(w * 0.03), 8)
    runs = []
    in_run = False
    start = 0
    for y, c in enumerate(rows):
        if c > floor_w and not in_run:
            in_run = True
            start = y
        elif c <= floor_w and in_run:
            in_run = False
            runs.append((start, y, sum(rows[start:y])))
    if in_run:
        runs.append((start, h, sum(rows[start:h])))
    if not runs:
        return im
    # Sort by weight; drop the tiny header label (smallest) + tiny favicon
    # (also small). Keep middle runs as one contiguous block from the
    # top-most kept run to the bottom-most kept run.
    sorted_runs = sorted(runs, key=lambda r: r[2])
    drop = set()
    if len(runs) >= 3:
        # smallest two are the header label + the bottom favicon variant
        drop.add(id(sorted_runs[0]))
        drop.add(id(sorted_runs[1]))
    kept = [r for r in runs if id(r) not in drop]
    if not kept:
        kept = runs
    top = min(r[0] for r in kept)
    bot = max(r[1] for r in kept)
    return im.crop((0, top, w, bot))


def square_canvas(im: Image.Image, bg=(0, 0, 0, 0)) -> Image.Image:
    w, h = im.size
    side = max(w, h)
    out = Image.new("RGBA", (side, side), bg)
    out.paste(im, ((side - w) // 2, (side - h) // 2), im)
    return out


def on_ink_padded(mark: Image.Image, side: int = 1024, pad_ratio: float = 0.16) -> Image.Image:
    out = Image.new("RGBA", (side, side), (INK[0], INK[1], INK[2], 255))
    target = int(side * (1.0 - pad_ratio * 2.0))
    mw, mh = mark.size
    scale = min(target / mw, target / mh)
    nw, nh = int(mw * scale), int(mh * scale)
    resized = mark.resize((nw, nh), Image.LANCZOS)
    out.paste(resized, ((side - nw) // 2, (side - nh) // 2), resized)
    return out


def write_resized_png(im: Image.Image, path: Path, side: int) -> None:
    sq = square_canvas(im)
    sq = sq.resize((side, side), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    sq.save(path, "PNG", optimize=True)


def write_ico(im: Image.Image, path: Path) -> None:
    sq = square_canvas(im)
    sq.save(path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])


def main() -> None:
    BRAND_DIR.mkdir(parents=True, exist_ok=True)

    monogram_src = SRC_DIR / "jbw-monogram-src.png"
    horizontal_src = SRC_DIR / "jbw-horizontal-src.png"
    stacked_src = SRC_DIR / "jbw-stacked-src.png"

    print(f"[recolor] monogram <- {monogram_src}")
    mono = trim_alpha(recolor_to_gold_transparent(monogram_src), pad=24)
    mono.save(BRAND_DIR / "jbw-monogram.png")

    print(f"[recolor] horizontal wordmark <- {horizontal_src}")
    horiz = trim_alpha(recolor_to_gold_transparent(horizontal_src), pad=12)
    horiz.save(BRAND_DIR / "jbw-wordmark-horizontal.png")

    print(f"[recolor] stacked wordmark <- {stacked_src}")
    # The "stacked" source layout (1195x1316):
    #   header label + rules        (~0-7%)
    #   main wordmark icon + name   (~10-66%)
    #   divider rule                (~70%)
    #   small variant label + icon  (~75-100%)
    # Hard-crop the main section, then trim alpha for safety.
    stack_raw = recolor_to_gold_transparent(stacked_src)
    w, h = stack_raw.size
    main_only = stack_raw.crop((0, int(h * 0.08), w, int(h * 0.68)))
    stacked = trim_alpha(main_only, pad=20)
    stacked.save(BRAND_DIR / "jbw-wordmark-stacked.png")

    print(f"[gen] on-ink social/og variant")
    on_ink = on_ink_padded(mono, side=1024, pad_ratio=0.16)
    on_ink.save(BRAND_DIR / "jbw-monogram-on-ink.png", "PNG", optimize=True)

    print(f"[gen] favicon variants (from monogram)")
    for size in (16, 32, 48, 180, 192, 512):
        out = IMG_DIR / f"favicon-{size}.png"
        write_resized_png(mono, out, size)
        print(f"   {out.name}")

    print(f"[gen] favicon.ico (16/32/48/64)")
    write_ico(mono, IMG_DIR / "favicon.ico")

    print("[ok] done")


if __name__ == "__main__":
    main()
