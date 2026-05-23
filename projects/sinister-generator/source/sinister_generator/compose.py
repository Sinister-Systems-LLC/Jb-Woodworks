"""Local PIL compositing helpers — pixel-perfect, no LLM call."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFilter


PathLike = Union[str, Path]


@dataclass
class ComposeResult:
    status: str
    output_path: Optional[str] = None
    meta_path: Optional[str] = None
    canvas_size: Optional[Tuple[int, int]] = None
    paste_at: Optional[Tuple[int, int]] = None
    error: Optional[str] = None


def left_aligned_banner(
    source: PathLike,
    output: PathLike,
    canvas_size: Tuple[int, int] = (1620, 648),
    canvas_color: Tuple[int, int, int] = (0x1A, 0x17, 0x29),
    crop_box: Optional[Tuple[int, int, int, int]] = None,
    paste_x: int = 30,
    margin: int = 20,
    feather_right: int = 140,
    feather_left: int = 40,
    feather_topbottom: int = 30,
    canvas_gradient_top_lift: Tuple[int, int, int] = (6, 4, 18),
    write_meta: bool = True,
) -> ComposeResult:
    """Composite a source image (e.g. a square-ish brand banner) onto the LEFT
    of a wider canvas, with feathered edges so the seam between source and
    canvas-color is invisible. The right portion stays plain canvas-color.

    Used to reshape something like JKOR's v6 banner (1536x672) into the
    ART/banner.png layout (1620x648 wide, character on left, empty field on right)
    without re-prompting the LLM. Pixel-perfect brand preservation.
    """
    src_path = Path(source)
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        src = Image.open(src_path).convert("RGBA")
    except Exception as e:
        return ComposeResult(status="error", error=f"failed to open source: {e}")

    if crop_box:
        src = src.crop(crop_box)
    cw, ch = src.size

    target_W, target_H = canvas_size
    scale = (target_H - 2 * margin) / ch
    new_w = int(cw * scale)
    new_h = int(ch * scale)
    scaled = src.resize((new_w, new_h), Image.LANCZOS)

    mask = Image.new("L", (new_w, new_h), 255)
    md = ImageDraw.Draw(mask)
    for x in range(feather_right):
        alpha = int(255 * (1 - (x / feather_right)) ** 2)
        md.line([(new_w - 1 - x, 0), (new_w - 1 - x, new_h - 1)], fill=alpha)
    for x in range(feather_left):
        alpha = int(255 * (x / feather_left))
        md.line([(x, 0), (x, new_h - 1)], fill=alpha)
    for y in range(feather_topbottom):
        alpha = int(255 * (y / feather_topbottom))
        for x in range(new_w):
            existing = mask.getpixel((x, y))
            mask.putpixel((x, y), min(existing, alpha))
            existing2 = mask.getpixel((x, new_h - 1 - y))
            mask.putpixel((x, new_h - 1 - y), min(existing2, alpha))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=2))

    canvas = Image.new("RGB", (target_W, target_H), canvas_color)
    draw = ImageDraw.Draw(canvas)
    lr, lg, lb = canvas_gradient_top_lift
    for y in range(target_H):
        t = y / target_H
        r = int(canvas_color[0] + (1 - t) * lr)
        g = int(canvas_color[1] + (1 - t) * lg)
        b = int(canvas_color[2] + (1 - t) * lb)
        draw.line([(0, y), (target_W, y)], fill=(r, g, b))

    paste_y = (target_H - new_h) // 2
    canvas.paste(scaled.convert("RGB"), (paste_x, paste_y), mask)
    canvas.save(out_path, "PNG", compress_level=6)

    meta_path = out_path.with_suffix(out_path.suffix + ".meta.json")
    if write_meta:
        meta = {
            "operation": "left_aligned_banner",
            "source": str(src_path),
            "model": "PIL/local (no LLM)",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "crop_box": list(crop_box) if crop_box else None,
            "scaled_size": [new_w, new_h],
            "canvas_size": [target_W, target_H],
            "canvas_color": list(canvas_color),
            "paste_at": [paste_x, paste_y],
            "feather": {"right": feather_right, "left": feather_left, "topbottom": feather_topbottom},
        }
        meta_path.write_text(json.dumps(meta, indent=2))

    return ComposeResult(
        status="ok",
        output_path=str(out_path),
        meta_path=str(meta_path) if write_meta else None,
        canvas_size=(target_W, target_H),
        paste_at=(paste_x, paste_y),
    )


def erase_region(
    source: PathLike,
    output: PathLike,
    region: Tuple[int, int, int, int],
    sample_at: Optional[Tuple[int, int]] = None,
) -> ComposeResult:
    """Erase a rectangular region by flooding with a sampled background color.
    Use for UI artifact removal (download icons, captions, watermarks).
    """
    src_path = Path(source)
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src_path).convert("RGB")
    x1, y1, x2, y2 = region
    sx, sy = sample_at or (max(0, x1 - 10), max(0, y1 - 10))
    bg = im.getpixel((sx, sy))
    draw = ImageDraw.Draw(im)
    draw.rectangle([x1, y1, x2 - 1, y2 - 1], fill=bg)
    im.save(out_path, "PNG", compress_level=6)
    return ComposeResult(
        status="ok",
        output_path=str(out_path),
        canvas_size=im.size,
    )
