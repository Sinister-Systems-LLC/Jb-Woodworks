#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-23
"""Convert HEIC -> JPG (full resolution), extract MOV poster frames, then
emit a categorization-helper contact sheet at scripts/_2026_inventory.html
listing every converted asset with its source filename + a small preview.

Usage:
    python scripts/sort_2026_imagery.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

SRC = Path(r"C:\Users\Zonia\Desktop\2026 JBWW")
OUT = Path(__file__).resolve().parent.parent / "public" / "img" / "_sorted_2026"
OUT.mkdir(parents=True, exist_ok=True)

JPG_QUALITY = 92
MAX_DIM = 4000  # cap any super-huge images to 4000px on the long edge

manifest: list[dict] = []


def convert_image(src: Path) -> Path:
    """HEIC/JPG -> high-quality JPG with EXIF orientation applied."""
    out = OUT / (src.stem + ".jpg")
    if out.exists() and out.stat().st_size > 0:
        return out
    img = Image.open(src)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Cap long edge
    w, h = img.size
    if max(w, h) > MAX_DIM:
        scale = MAX_DIM / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img.save(out, "JPEG", quality=JPG_QUALITY, optimize=True, progressive=True)
    return out


def extract_poster(src: Path) -> Path | None:
    """MOV -> .jpg poster at t=0.5s via ffmpeg if available."""
    out = OUT / (src.stem + ".jpg")
    if out.exists() and out.stat().st_size > 0:
        return out
    if not shutil.which("ffmpeg"):
        return None
    try:
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", "0.5", "-i", str(src),
                "-vframes", "1", "-q:v", "3", str(out)
            ],
            check=True, timeout=30
        )
        return out
    except Exception as exc:  # noqa: BLE001
        print(f"  poster failed for {src.name}: {exc}")
        return None


def copy_video(src: Path) -> Path:
    """MOV -> .mp4 transcode (h264) if ffmpeg available; else raw copy."""
    out_mp4 = OUT / (src.stem + ".mp4")
    if out_mp4.exists() and out_mp4.stat().st_size > 0:
        return out_mp4
    if not shutil.which("ffmpeg"):
        # raw copy with .mov extension
        out_mov = OUT / src.name
        if not out_mov.exists():
            shutil.copy2(src, out_mov)
        return out_mov
    try:
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-i", str(src),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "128k",
                str(out_mp4)
            ],
            check=True, timeout=600
        )
        return out_mp4
    except Exception as exc:  # noqa: BLE001
        print(f"  transcode failed for {src.name}: {exc}; falling back to raw copy")
        out_mov = OUT / src.name
        if not out_mov.exists():
            shutil.copy2(src, out_mov)
        return out_mov


def main() -> None:
    files = sorted(SRC.iterdir())
    print(f"Found {len(files)} source files in {SRC}")

    for src in files:
        if not src.is_file():
            continue
        ext = src.suffix.lower()
        try:
            if ext in (".heic", ".heif", ".jpg", ".jpeg", ".png"):
                out = convert_image(src)
                manifest.append({
                    "source": src.name,
                    "output": out.name,
                    "kind": "image",
                    "size_bytes": out.stat().st_size,
                    "width_height": Image.open(out).size
                })
                print(f"  [img] {src.name} -> {out.name} ({out.stat().st_size // 1024} KB)")
            elif ext in (".mov", ".mp4"):
                video_out = copy_video(src)
                poster = extract_poster(src)
                manifest.append({
                    "source": src.name,
                    "output": video_out.name,
                    "poster": poster.name if poster else None,
                    "kind": "video",
                    "size_bytes": video_out.stat().st_size
                })
                print(f"  [vid] {src.name} -> {video_out.name} ({video_out.stat().st_size // 1024} KB)")
        except Exception as exc:  # noqa: BLE001
            print(f"  [ERR] {src.name}: {exc}")

    manifest_path = OUT / "_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest at {manifest_path}")
    print(f"All outputs in {OUT}")


if __name__ == "__main__":
    main()
