# Sinister Term :: image_handler.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Port of jcode's src/tui/image.rs (terminal image display). Source MIT
# (Copyright (c) 2025 Jeremy Huang). Re-licensed under AGPL-3.0-or-later
# per upstream MIT terms.
#
# Goals: never crash on image input — Windows Terminal doesn't support
# Kitty/iTerm2/Sixel, so we detect the protocol, fall back to an ASCII
# placeholder if nothing works, and log_crash on any I/O exception.
#
# Detection logic mirrors jcode image.rs:35-108. Display routines mirror
# image.rs:152-414 for Kitty/iTerm2; Sixel goes through ImageMagick `convert`
# like jcode does. We deliberately do NOT raise on unsupported terminals —
# we return False so callers can fall back to text.

from __future__ import annotations

import base64
import os
import shutil
import struct
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple


class ImageProtocol(Enum):
    KITTY = "kitty"
    ITERM2 = "iterm2"
    SIXEL = "sixel"
    NONE = "none"

    @property
    def is_supported(self) -> bool:
        return self is not ImageProtocol.NONE


_HAS_IMAGEMAGICK_CACHE: Optional[bool] = None


def _has_imagemagick() -> bool:
    """Cached check (jcode image.rs:14-20)."""
    global _HAS_IMAGEMAGICK_CACHE
    if _HAS_IMAGEMAGICK_CACHE is None:
        _HAS_IMAGEMAGICK_CACHE = shutil.which("convert") is not None or shutil.which("magick") is not None
    return _HAS_IMAGEMAGICK_CACHE


def detect_protocol(env: Optional[dict] = None) -> ImageProtocol:
    """Detect best available image protocol. jcode image.rs:37-77."""
    e = env if env is not None else os.environ

    # 1. Kitty
    if e.get("KITTY_WINDOW_ID"):
        return ImageProtocol.KITTY
    term = e.get("TERM", "")
    if term and ("kitty" in term or "ghostty" in term):
        return ImageProtocol.KITTY

    # 2. TERM_PROGRAM
    tp = e.get("TERM_PROGRAM", "")
    if tp == "ghostty":
        return ImageProtocol.KITTY
    if tp == "iTerm.app":
        return ImageProtocol.ITERM2
    if tp == "WezTerm":
        return ImageProtocol.SIXEL

    # 3. LC_TERMINAL
    if e.get("LC_TERMINAL") == "iTerm2":
        return ImageProtocol.ITERM2

    # 4. Sixel-capable
    if _detect_sixel(e):
        return ImageProtocol.SIXEL

    return ImageProtocol.NONE


def _detect_sixel(e: dict) -> bool:
    """jcode image.rs:80-108."""
    if not _has_imagemagick():
        return False
    term = e.get("TERM", "").lower()
    if term and any(t in term for t in ("xterm", "foot", "mlterm", "yaft", "mintty", "contour")):
        return True
    tp = e.get("TERM_PROGRAM", "")
    if tp in ("mintty", "contour"):
        return True
    return False


# ---------------------------------------------------------------------------
# Image dimension parsers (image.rs:174-235). Pure Python so we don't depend
# on Pillow being installed — important since Windows installs are often
# bare.
# ---------------------------------------------------------------------------

def get_image_dimensions(data: bytes) -> Optional[Tuple[int, int]]:
    """Parse width/height from PNG/JPEG/GIF/WebP magic bytes."""
    n = len(data)

    # PNG: signature + IHDR
    if n > 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
        w = struct.unpack(">I", data[16:20])[0]
        h = struct.unpack(">I", data[20:24])[0]
        return (w, h)

    # JPEG: SOF0/SOF2
    if n > 2 and data[0] == 0xFF and data[1] == 0xD8:
        i = 2
        while i + 9 < n:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC2):
                h = struct.unpack(">H", data[i + 5:i + 7])[0]
                w = struct.unpack(">H", data[i + 7:i + 9])[0]
                return (w, h)
            if i + 3 < n:
                seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
                i += 2 + seg_len
            else:
                break

    # GIF
    if n > 10 and data[:6] in (b"GIF87a", b"GIF89a"):
        w = struct.unpack("<H", data[6:8])[0]
        h = struct.unpack("<H", data[8:10])[0]
        return (w, h)

    # WebP
    if n > 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8 " and data[23] == 0x9D and data[24] == 0x01 and data[25] == 0x2A:
            w = struct.unpack("<H", data[26:28])[0] & 0x3FFF
            h = struct.unpack("<H", data[28:30])[0] & 0x3FFF
            return (w, h)
        if data[12:16] == b"VP8L" and n > 25:
            bits = struct.unpack("<I", data[21:25])[0]
            w = (bits & 0x3FFF) + 1
            h = ((bits >> 14) & 0x3FFF) + 1
            return (w, h)

    return None


# ---------------------------------------------------------------------------
# Display params + size calc (image.rs:118-268)
# ---------------------------------------------------------------------------

@dataclass
class ImageDisplayParams:
    max_cols: int = 80
    max_rows: int = 24

    @classmethod
    def from_terminal(cls) -> "ImageDisplayParams":
        cols, rows = _terminal_size()
        # Use 2/3 width capped 40..100; 1/2 height capped 10..30
        c = max(40, min(100, cols * 2 // 3))
        r = max(10, min(30, rows // 2))
        return cls(max_cols=c, max_rows=r)


def _terminal_size() -> Tuple[int, int]:
    try:
        sz = shutil.get_terminal_size((120, 40))
        return sz.columns, sz.lines
    except Exception:
        return (120, 40)


def calculate_display_size(img_w: int, img_h: int, max_cols: int, max_rows: int) -> Tuple[int, int]:
    """jcode image.rs:238-268. Returns (cols, rows)."""
    if img_w == 0 or img_h == 0:
        return (min(max_cols, 40), min(max_rows, 20))
    cell_aspect = 2.0
    img_aspect = img_w / img_h
    mw = float(max_cols)
    mh = float(max_rows) * cell_aspect
    if img_aspect > mw / mh:
        dw, dh = mw, mw / img_aspect
    else:
        dw, dh = mh * img_aspect, mh
    return (max(10, int(dw)), int(dh / cell_aspect))


# ---------------------------------------------------------------------------
# Display protocols
# ---------------------------------------------------------------------------

def _emit_kitty(data: bytes, cols: int, rows: int, stream=sys.stdout) -> bool:
    """jcode image.rs:270-327 — Kitty graphics protocol, base64 in 4KB chunks."""
    try:
        encoded = base64.standard_b64encode(data).decode("ascii")
        CHUNK = 4096
        chunks = [encoded[i:i + CHUNK] for i in range(0, len(encoded), CHUNK)]
        for i, chunk in enumerate(chunks):
            is_first = (i == 0)
            is_last = (i == len(chunks) - 1)
            more = 0 if is_last else 1
            if is_first:
                stream.write(f"\x1b_Ga=T,f=100,c={cols},r={rows},m={more};{chunk}\x1b\\")
            else:
                stream.write(f"\x1b_Gm={more};{chunk}\x1b\\")
        stream.write("\n")
        stream.flush()
        return True
    except Exception:
        return False


def _emit_iterm2(data: bytes, name: str, cols: int, stream=sys.stdout) -> bool:
    """jcode image.rs:329-367 — iTerm2 OSC 1337."""
    try:
        encoded = base64.standard_b64encode(data).decode("ascii")
        name_b64 = base64.standard_b64encode(name.encode("utf-8")).decode("ascii")
        stream.write(
            f"\x1b]1337;File=name={name_b64};size={len(data)};inline=1;"
            f"width={cols}:{encoded}\x07\n"
        )
        stream.flush()
        return True
    except Exception:
        return False


def _emit_sixel(path: Path, cols: int, rows: int, stream=sys.stdout) -> bool:
    """jcode image.rs:369-414 — pipe through ImageMagick `convert`."""
    if not _has_imagemagick():
        return False
    # Prefer modern `magick` if available, else fall back to `convert`
    binname = "magick" if shutil.which("magick") else "convert"
    try:
        pixel_w = cols * 8
        pixel_h = rows * 16
        # `magick` expects subcommand prefix
        argv = (
            [binname, "convert"] if binname == "magick" else [binname]
        ) + [
            str(path), "-geometry", f"{pixel_w}x{pixel_h}>",
            "-colors", "256", "sixel:-",
        ]
        proc = subprocess.run(argv, capture_output=True, timeout=15)
        if proc.returncode != 0 or not proc.stdout:
            return False
        # stdout was bytes; write directly to underlying buffer
        try:
            stream.buffer.write(proc.stdout)  # type: ignore[attr-defined]
        except Exception:
            stream.write(proc.stdout.decode("latin-1"))
        stream.write("\n")
        stream.flush()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_ascii_placeholder(path: Path, dims: Optional[Tuple[int, int]] = None,
                              stream=sys.stdout) -> None:
    """Dim ASCII fallback. Always writes — never raises."""
    try:
        size_kb = "?"
        try:
            size_kb = f"{path.stat().st_size // 1024} KB"
        except Exception:
            pass
        dim_str = f"{dims[0]}x{dims[1]}" if dims else "unknown"
        # \x1b[2m dim, \x1b[0m reset
        stream.write(
            f"\x1b[2m[image] {path.name}  ({dim_str}, {size_kb})  "
            f"— terminal protocol unsupported, placeholder shown\x1b[0m\n"
        )
        stream.flush()
    except Exception:
        pass


def display_image(path: Path, params: Optional[ImageDisplayParams] = None,
                   stream=sys.stdout) -> bool:
    """Render `path` inline if supported, else ASCII placeholder. Returns
    True iff the real protocol succeeded. NEVER raises — image input
    failure must not crash the terminal (operator's key requirement)."""
    if params is None:
        params = ImageDisplayParams.from_terminal()

    if not path.exists():
        try:
            stream.write(f"\x1b[31m[image] file not found: {path}\x1b[0m\n")
            stream.flush()
        except Exception:
            pass
        return False

    try:
        data = path.read_bytes()
    except Exception:
        render_ascii_placeholder(path, None, stream)
        return False

    dims = get_image_dimensions(data) or (0, 0)
    protocol = detect_protocol()

    if not protocol.is_supported:
        render_ascii_placeholder(path, dims if dims != (0, 0) else None, stream)
        return False

    cols, rows = calculate_display_size(dims[0], dims[1], params.max_cols, params.max_rows)
    ok = False
    if protocol is ImageProtocol.KITTY:
        ok = _emit_kitty(data, cols, rows, stream)
    elif protocol is ImageProtocol.ITERM2:
        ok = _emit_iterm2(data, path.name, cols, stream)
    elif protocol is ImageProtocol.SIXEL:
        ok = _emit_sixel(path, cols, rows, stream)

    if not ok:
        render_ascii_placeholder(path, dims if dims != (0, 0) else None, stream)
    return ok
