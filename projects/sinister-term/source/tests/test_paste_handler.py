# Sinister Term :: tests/test_paste_handler.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later

from __future__ import annotations

import pytest

from term.paste_handler import (
    PasteBuffer,
    PasteResult,
    LARGE_PASTE_LINE_THRESHOLD,
    extract_image_url,
    handle_paste,
    expand_placeholders,
)


# ----- extract_image_url -------------------------------------------------

class TestExtractImageUrl:
    def test_empty_returns_none(self):
        assert extract_image_url("") is None
        assert extract_image_url(None) is None

    def test_bare_png_url(self):
        assert extract_image_url("https://example.com/x.png") == "https://example.com/x.png"

    def test_bare_jpg_with_query(self):
        u = "https://cdn.example.com/cat.jpg?w=400"
        assert extract_image_url(u) == u

    def test_bare_jpeg(self):
        assert extract_image_url("http://x.test/a.jpeg") == "http://x.test/a.jpeg"

    def test_bare_gif(self):
        assert extract_image_url("https://x.test/anim.gif") is not None

    def test_bare_webp(self):
        assert extract_image_url("https://x.test/pic.webp") is not None

    def test_bare_url_no_image_ext(self):
        assert extract_image_url("https://example.com/article") is None

    def test_non_http_image_ext(self):
        assert extract_image_url("file:///tmp/x.png") is None

    def test_img_tag_double_quote(self):
        s = '<img src="https://cdn.test/a.png" alt="x">'
        assert extract_image_url(s) == "https://cdn.test/a.png"

    def test_img_tag_single_quote(self):
        s = "<p>hi</p><img src='https://cdn.test/b.jpg'/>"
        assert extract_image_url(s) == "https://cdn.test/b.jpg"

    def test_img_tag_non_http_src_falls_through(self):
        # jcode requires src starts with http; relative srcs return None
        s = '<img src="/static/x.png">'
        assert extract_image_url(s) is None

    def test_text_with_leading_whitespace(self):
        assert extract_image_url("   https://x.test/cat.png  ") == "https://x.test/cat.png"


# ----- handle_paste ------------------------------------------------------

class TestHandlePaste:
    def test_short_single_line(self):
        buf = PasteBuffer()
        r = handle_paste("hello world", buf)
        assert r.insert_text == "hello world"
        assert r.is_placeholder is False
        assert r.line_count == 1
        assert len(buf) == 0

    def test_short_few_lines(self):
        buf = PasteBuffer()
        r = handle_paste("a\nb\nc", buf)
        assert r.is_placeholder is False
        assert r.insert_text == "a\nb\nc"
        assert r.line_count == 3

    def test_just_below_threshold(self):
        buf = PasteBuffer()
        # threshold default = 5; 4 lines stays inline
        r = handle_paste("a\nb\nc\nd", buf)
        assert r.is_placeholder is False
        assert r.line_count == 4
        assert len(buf) == 0

    def test_at_threshold_becomes_placeholder(self):
        buf = PasteBuffer()
        r = handle_paste("a\nb\nc\nd\ne", buf)
        assert r.line_count == 5
        assert r.is_placeholder is True
        assert r.insert_text == "[pasted 5 lines]"
        assert len(buf) == 1

    def test_large_paste_stores_full(self):
        buf = PasteBuffer()
        text = "\n".join(f"line {i}" for i in range(50))
        r = handle_paste(text, buf)
        assert r.is_placeholder
        assert r.insert_text == "[pasted 50 lines]"
        assert buf.contents[0] == text

    def test_empty_input(self):
        buf = PasteBuffer()
        r = handle_paste("", buf)
        assert r.insert_text == ""
        assert r.line_count == 1
        assert r.is_placeholder is False

    def test_none_input_treated_as_empty(self):
        buf = PasteBuffer()
        r = handle_paste(None, buf)
        assert r.insert_text == ""

    def test_image_url_detection_runs(self):
        buf = PasteBuffer()
        r = handle_paste("https://cdn.test/a.png", buf)
        assert r.image_url == "https://cdn.test/a.png"
        # short paste — still inserts text
        assert r.is_placeholder is False

    def test_image_url_in_long_paste_still_flagged(self):
        # jcode parity (helpers.rs:651-660): for a bare URL pattern, the
        # ENTIRE trimmed string is returned as the URL — there's no per-line
        # extraction. So with a multi-line paste where the first line is the
        # URL, .image_url comes back containing the whole blob; the host can
        # decide what to do. Test just verifies the URL is flagged.
        buf = PasteBuffer()
        text = "https://cdn.test/a.png\n" + "\n".join(str(i) for i in range(10))
        r = handle_paste(text, buf)
        assert r.is_placeholder is True
        assert r.image_url is not None
        assert "https://cdn.test/a.png" in r.image_url

    def test_crlf_counts_as_one_line_break(self):
        buf = PasteBuffer()
        # 5 lines via CRLF should still be detected as 5
        r = handle_paste("a\r\nb\r\nc\r\nd\r\ne", buf)
        assert r.line_count == 5
        assert r.is_placeholder is True

    def test_custom_threshold(self):
        buf = PasteBuffer()
        r = handle_paste("a\nb\nc", buf, threshold=2)
        assert r.is_placeholder is True
        assert r.insert_text == "[pasted 3 lines]"


# ----- PasteBuffer -------------------------------------------------------

class TestPasteBuffer:
    def test_push_returns_1based_index(self):
        b = PasteBuffer()
        assert b.push("x") == 1
        assert b.push("y") == 2

    def test_get_round_trip(self):
        b = PasteBuffer()
        b.push("first")
        b.push("second")
        assert b.get(1) == "first"
        assert b.get(2) == "second"
        assert b.get(3) is None
        assert b.get(0) is None

    def test_clear(self):
        b = PasteBuffer()
        b.push("x")
        b.clear()
        assert len(b) == 0


# ----- expand_placeholders ----------------------------------------------

class TestExpandPlaceholders:
    def test_no_placeholders_passthrough(self):
        b = PasteBuffer()
        b.push("ignored")
        assert expand_placeholders("just text", b) == "just text"

    def test_single_placeholder_expanded(self):
        b = PasteBuffer()
        b.push("FULL PASTE HERE")
        out = expand_placeholders("before [pasted 5 lines] after", b)
        assert out == "before FULL PASTE HERE after"

    def test_multiple_placeholders_in_order(self):
        b = PasteBuffer()
        b.push("AAA")
        b.push("BBB")
        out = expand_placeholders("[pasted 5 lines]\n---\n[pasted 9 lines]", b)
        assert out == "AAA\n---\nBBB"

    def test_more_placeholders_than_buffer_keeps_literal(self):
        b = PasteBuffer()
        b.push("only one")
        out = expand_placeholders("[pasted 5 lines] [pasted 6 lines]", b)
        assert "only one" in out
        assert "[pasted 6 lines]" in out

    def test_single_line_singular_form(self):
        # singular 'line' (no s) should also be recognised by the regex
        b = PasteBuffer()
        b.push("xyz")
        out = expand_placeholders("[pasted 1 line]", b)
        assert out == "xyz"

    def test_empty_buffer_passthrough(self):
        b = PasteBuffer()
        text = "no expansion [pasted 9 lines]"
        # buffer is empty so we just return as-is (no .contents)
        assert expand_placeholders(text, b) == text


# ----- prompt_toolkit install_paste_handler smoke -----------------------

class TestInstallPasteHandlerSmoke:
    def test_no_session_no_crash(self):
        # Calling with a bare object that has key_bindings=None must not raise
        from term.paste_handler import install_paste_handler

        class FakeSession:
            key_bindings = None

        install_paste_handler(FakeSession(), PasteBuffer())  # no exception
