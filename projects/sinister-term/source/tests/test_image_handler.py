# Sinister Term :: tests/test_image_handler.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later

from __future__ import annotations

import io
import struct
from pathlib import Path

import pytest

from term.image_handler import (
    ImageProtocol,
    ImageDisplayParams,
    detect_protocol,
    get_image_dimensions,
    calculate_display_size,
    render_ascii_placeholder,
    display_image,
)


# ----- detect_protocol ---------------------------------------------------

class TestDetectProtocol:
    def test_kitty_via_window_id(self):
        env = {"KITTY_WINDOW_ID": "1"}
        assert detect_protocol(env) is ImageProtocol.KITTY

    def test_kitty_via_term(self):
        env = {"TERM": "xterm-kitty"}
        assert detect_protocol(env) is ImageProtocol.KITTY

    def test_ghostty_via_term(self):
        env = {"TERM": "ghostty"}
        assert detect_protocol(env) is ImageProtocol.KITTY

    def test_iterm_via_term_program(self):
        env = {"TERM_PROGRAM": "iTerm.app"}
        assert detect_protocol(env) is ImageProtocol.ITERM2

    def test_iterm_via_lc_terminal(self):
        env = {"LC_TERMINAL": "iTerm2"}
        assert detect_protocol(env) is ImageProtocol.ITERM2

    def test_wezterm_is_sixel(self):
        env = {"TERM_PROGRAM": "WezTerm"}
        assert detect_protocol(env) is ImageProtocol.SIXEL

    def test_unknown_env_returns_none(self):
        env = {"TERM": "dumb"}
        # detect_sixel will refuse if no ImageMagick — either way NONE
        result = detect_protocol(env)
        assert result in (ImageProtocol.NONE, ImageProtocol.SIXEL)

    def test_empty_env_returns_none_or_sixel(self):
        result = detect_protocol({})
        assert result in (ImageProtocol.NONE, ImageProtocol.SIXEL)

    def test_is_supported_property(self):
        assert ImageProtocol.KITTY.is_supported is True
        assert ImageProtocol.ITERM2.is_supported is True
        assert ImageProtocol.SIXEL.is_supported is True
        assert ImageProtocol.NONE.is_supported is False


# ----- get_image_dimensions ---------------------------------------------

class TestGetImageDimensions:
    def test_png_dimensions(self):
        # Minimal valid PNG: signature + IHDR
        sig = b"\x89PNG\r\n\x1a\n"
        # IHDR chunk: length(4) + 'IHDR' + width(4) + height(4) + …
        ihdr = struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 100, 50) + b"\x08\x06\x00\x00\x00"
        data = sig + ihdr + b"\x00" * 100  # pad
        assert get_image_dimensions(data) == (100, 50)

    def test_gif_dimensions(self):
        data = b"GIF89a" + struct.pack("<HH", 200, 150) + b"\x00" * 100
        assert get_image_dimensions(data) == (200, 150)

    def test_jpeg_dimensions(self):
        # Build a fake JPEG with a SOF0 marker
        data = bytearray()
        data += b"\xFF\xD8"  # SOI
        # Some filler marker (APP0)
        data += b"\xFF\xE0"
        data += struct.pack(">H", 16)  # segment length
        data += b"\x00" * 14
        # SOF0
        data += b"\xFF\xC0"
        data += struct.pack(">H", 17)  # segment length
        data += b"\x08"  # precision
        data += struct.pack(">HH", 300, 400)  # height=300 width=400
        data += b"\x00" * 100
        # jcode returns (width, height)
        assert get_image_dimensions(bytes(data)) == (400, 300)

    def test_unknown_format(self):
        assert get_image_dimensions(b"not an image at all") is None

    def test_too_short(self):
        assert get_image_dimensions(b"\x89PNG") is None


# ----- calculate_display_size -------------------------------------------

class TestCalculateDisplaySize:
    def test_zero_dims_fallback(self):
        cols, rows = calculate_display_size(0, 0, 80, 24)
        assert cols == min(80, 40)
        assert rows == min(24, 20)

    def test_wide_image(self):
        # Square image, square-ish space
        cols, rows = calculate_display_size(100, 100, 80, 24)
        assert cols > 0
        assert rows > 0
        assert cols <= 80
        assert rows <= 24

    def test_minimum_10_cols(self):
        cols, _ = calculate_display_size(1, 1000, 80, 24)
        assert cols >= 10


# ----- ImageDisplayParams -----------------------------------------------

class TestImageDisplayParams:
    def test_default(self):
        p = ImageDisplayParams()
        assert p.max_cols == 80
        assert p.max_rows == 24

    def test_from_terminal_clamps(self):
        p = ImageDisplayParams.from_terminal()
        assert 40 <= p.max_cols <= 100
        assert 10 <= p.max_rows <= 30


# ----- render_ascii_placeholder + display_image safety ------------------

class TestPlaceholder:
    def test_placeholder_never_raises(self, tmp_path: Path):
        p = tmp_path / "fake.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        out = io.StringIO()
        render_ascii_placeholder(p, (100, 50), out)
        assert "fake.png" in out.getvalue()
        assert "100x50" in out.getvalue()

    def test_placeholder_no_dims(self, tmp_path: Path):
        p = tmp_path / "x.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n")
        out = io.StringIO()
        render_ascii_placeholder(p, None, out)
        assert "x.png" in out.getvalue()


class TestDisplayImage:
    def test_missing_file_returns_false(self, tmp_path: Path):
        out = io.StringIO()
        # We need an isatty-faking stream; the placeholder gate checks isatty
        # so use a stream that pretends to be a tty:
        class FakeTty(io.StringIO):
            def isatty(self):
                return True
        out_tty = FakeTty()
        result = display_image(tmp_path / "missing.png", stream=out_tty)
        assert result is False

    def test_unsupported_terminal_falls_back(self, tmp_path: Path, monkeypatch):
        # Force unsupported env
        for k in ("KITTY_WINDOW_ID", "TERM_PROGRAM", "LC_TERMINAL", "TERM"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("TERM", "dumb")
        p = tmp_path / "img.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        class FakeTty(io.StringIO):
            def isatty(self):
                return True
        out = FakeTty()
        result = display_image(p, stream=out)
        # Either False (placeholder) or True (if sixel detected w/ magick) —
        # the important thing is it MUST NOT raise.
        assert isinstance(result, bool)

    def test_corrupt_file_does_not_raise(self, tmp_path: Path):
        p = tmp_path / "bad.png"
        p.write_bytes(b"not even close to a valid png")

        class FakeTty(io.StringIO):
            def isatty(self):
                return True
        out = FakeTty()
        # Must return bool, not raise
        result = display_image(p, stream=out)
        assert isinstance(result, bool)
