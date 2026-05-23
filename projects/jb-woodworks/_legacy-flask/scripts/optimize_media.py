# Author: RKOJ-ELENO :: 2026-05-23
"""Transcode hero/portfolio MP4s to web-optimized H.264 + extract poster JPGs.

Source: D:\\Sinister\\old\\Coding Random\\JB Woodworks\\Jah Images\\
Output: ../static/media/<Category>/<basename>.mp4 + .jpg

Targets:
  - 1280px wide max, 30fps cap
  - H.264 main profile, CRF 23, faststart (moov at front)
  - No audio (hero videos play muted anyway)
  - Poster JPG extracted at 0.5s, q=4 (~85%)

Re-run when source files change. Idempotent: skips files where output
is newer than source.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(r"D:\Sinister\old\Coding Random\JB Woodworks\Jah Images")
OUT = Path(__file__).resolve().parent.parent / "static" / "media"

# Only transcode files referenced by hero_media.json / portfolio.json
TARGETS = [
    "Pergola/IMG_0047.mp4",
    "Pergola/IMG_0050.mp4",
    "Trex Deck/I like.mp4",
    "Deck/My Movie 2.mp4",
    # extras used in portfolio detail pages
    "Pergola/IMG_1866.mp4",
    "Trex Deck/IMG_2175.mp4",
    "Trex Deck/IMG_2183.mp4",
    "Boat Dock/IMG_1577.mp4",
    "Boat Dock/IMG_1605.mp4",
    "Custom Furniture/IMG_1133.mp4",
    "Custom Furniture/IMG_1134.mp4",
    "Deck/IMG_1558.mp4",
]


def needs_rebuild(src: Path, dst: Path) -> bool:
    return not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime


def transcode(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(src),
        "-c:v", "libx264",
        "-profile:v", "main",
        "-preset", "fast",
        "-crf", "24",
        "-maxrate", "1800k",
        "-bufsize", "3600k",
        "-vf", "scale='min(1280,iw)':-2,fps=30",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",  # no audio
        str(dst),
    ]
    print(f"  transcoding {src.name} -> {dst}")
    subprocess.run(cmd, check=True)


def extract_poster(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", "0.5", "-i", str(src),
        "-vframes", "1",
        "-vf", "scale='min(1280,iw)':-2",
        "-q:v", "4",
        str(dst),
    ]
    print(f"  poster   {src.name} -> {dst.name}")
    subprocess.run(cmd, check=True)


def main() -> None:
    if not shutil.which("ffmpeg"):
        print("ffmpeg not found on PATH. Install it first.")
        sys.exit(1)

    total = 0
    for rel in TARGETS:
        src = SRC / rel
        if not src.exists():
            print(f"  MISSING: {src}")
            continue
        # Sanitize folder/file names so URL paths are simple
        folder = rel.split("/", 1)[0]
        name = Path(rel).stem
        dst_mp4 = OUT / folder / f"{name}.mp4"
        dst_jpg = OUT / folder / f"{name}.jpg"

        if needs_rebuild(src, dst_mp4):
            transcode(src, dst_mp4)
            total += 1
        if needs_rebuild(src, dst_jpg):
            extract_poster(src, dst_jpg)
            total += 1

    # Bytes before / after report
    src_total = sum((SRC / r).stat().st_size for r in TARGETS if (SRC / r).exists())
    dst_total = sum(p.stat().st_size for p in OUT.rglob("*.mp4"))
    print(f"\nDone. {total} files rebuilt. Source MP4 total: {src_total / 1e6:.1f} MB. Optimized total: {dst_total / 1e6:.1f} MB.")


if __name__ == "__main__":
    main()
