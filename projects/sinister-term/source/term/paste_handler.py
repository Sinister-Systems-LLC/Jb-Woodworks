# Sinister Term :: paste_handler.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Port of jcode's paste handling: src/tui/app/input.rs:463-510 (handle_paste
# + handle_text_paste) plus src/tui/app/helpers.rs:625-663 (extract_image_url
# for bare image URLs / <img src=...> snippets). Source MIT (Copyright (c)
# 2025 Jeremy Huang). Re-licensed under AGPL-3.0-or-later per upstream MIT.
#
# Why we need this on top of prompt_toolkit's built-in bracketed-paste:
#   1. Big pastes (>= 5 lines) should NOT be expanded into the prompt — they
#      get stored in a "pasted_contents" buffer and the prompt shows a tiny
#      [pasted N lines] placeholder. Without this, multi-line code paste
#      garbles the prompt (one of the operator's exact complaints).
#   2. Pasted image URLs / <img src> snippets get sniffed so we can offer to
#      download them instead of pasting raw HTML.
#   3. A central handler means every entry point (keybinding Ctrl+V, OS
#      bracketed-paste, drag-drop) goes through the same robust path.

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple


# Threshold (matches jcode input.rs:498 — `if line_count < 5`)
LARGE_PASTE_LINE_THRESHOLD = 5

# jcode helpers.rs:651-660 — bare URL detection
_IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
_HTTP_RE = re.compile(r"^https?://", re.IGNORECASE)
_IMG_SRC_DQ_RE = re.compile(r'<img\b[^>]*?\bsrc\s*=\s*"([^"]+)"', re.IGNORECASE)
_IMG_SRC_SQ_RE = re.compile(r"<img\b[^>]*?\bsrc\s*=\s*'([^']+)'", re.IGNORECASE)


def extract_image_url(text: str) -> Optional[str]:
    """jcode helpers.rs:625-663 — return URL if `text` looks like an image.

    Recognises:
      - <img src="https://..."> (Discord/web copy)
      - <img src='https://...'>
      - bare 'https://x/y.png?optional=query'
    """
    if not text:
        return None
    trimmed = text.strip()

    # <img src="..."> double-quote first then single
    m = _IMG_SRC_DQ_RE.search(trimmed)
    if m and m.group(1).startswith("http"):
        return m.group(1)
    m = _IMG_SRC_SQ_RE.search(trimmed)
    if m and m.group(1).startswith("http"):
        return m.group(1)

    # Bare URL — must be an HTTP(s) URL and contain an image extension
    # somewhere (jcode .contains() is substring, so query params are ok).
    if _HTTP_RE.match(trimmed):
        lower = trimmed.lower()
        for ext in _IMG_EXTS:
            if ext in lower:
                return trimmed
    return None


# ---------------------------------------------------------------------------
# Pasted-content store + result type
# ---------------------------------------------------------------------------

@dataclass
class PasteResult:
    """Returned by handle_paste so the host shell knows what to display."""
    # The text to actually insert into the input buffer (placeholder for big
    # pastes, full text for short).
    insert_text: str
    # Original raw paste text. Always populated.
    raw_text: str
    # Number of lines in raw_text (always >= 1).
    line_count: int
    # True if we stored the paste in `pasted_contents` and inserted a
    # placeholder. False = the full text is in `insert_text`.
    is_placeholder: bool
    # If non-None, the raw_text looked like an image URL/snippet. Host can
    # decide to download instead of paste.
    image_url: Optional[str] = None


@dataclass
class PasteBuffer:
    """Mirror of jcode's `app.pasted_contents: Vec<String>`. Lets the host
    recover the full text for a placeholder."""
    contents: List[str] = field(default_factory=list)

    def push(self, text: str) -> int:
        """Append and return 1-based index (matches how jcode renders
        `[pasted N lines]` references)."""
        self.contents.append(text)
        return len(self.contents)

    def clear(self) -> None:
        self.contents.clear()

    def get(self, index_1based: int) -> Optional[str]:
        i = index_1based - 1
        if 0 <= i < len(self.contents):
            return self.contents[i]
        return None

    def __len__(self) -> int:
        return len(self.contents)


def _line_count(text: str) -> int:
    """Match Rust's `text.lines().count().max(1)`. Note: Rust's `.lines()`
    treats a trailing newline as ending the last line WITHOUT producing an
    empty one (different from str.split('\\n'))."""
    if not text:
        return 1
    # splitlines() drops a trailing newline + matches \r\n + \r + \n
    n = len(text.splitlines())
    return max(n, 1)


def _placeholder(line_count: int) -> str:
    suffix = "" if line_count == 1 else "s"
    return f"[pasted {line_count} line{suffix}]"


def handle_paste(text: str, buffer: PasteBuffer,
                 threshold: int = LARGE_PASTE_LINE_THRESHOLD) -> PasteResult:
    """Top-level paste entry. Port of input.rs:463-510.

    - If text contains an image URL/snippet, that takes precedence —
      caller can use result.image_url to download.
    - Else, short pastes (<threshold lines) get inserted verbatim.
    - Long pastes get appended to the buffer + placeholder text returned.
    """
    if text is None:
        text = ""
    image_url = extract_image_url(text)
    lc = _line_count(text)

    if lc < threshold:
        return PasteResult(
            insert_text=text,
            raw_text=text,
            line_count=lc,
            is_placeholder=False,
            image_url=image_url,
        )

    buffer.push(text)
    return PasteResult(
        insert_text=_placeholder(lc),
        raw_text=text,
        line_count=lc,
        is_placeholder=True,
        image_url=image_url,
    )


def expand_placeholders(line: str, buffer: PasteBuffer) -> str:
    """Inverse of handle_paste: replace `[pasted N lines]` markers in a
    submitted line with the full text from the buffer. We replace them in
    insertion order so the operator gets back exactly what they pasted.

    This is what runs at submit-time — the model/shell sees the FULL text,
    not the placeholder."""
    if not buffer.contents:
        return line
    # Greedy: replace each placeholder one at a time
    placeholder_re = re.compile(r"\[pasted (\d+) lines?\]")
    out_parts: List[str] = []
    last_end = 0
    idx = 0
    for m in placeholder_re.finditer(line):
        out_parts.append(line[last_end:m.start()])
        if idx < len(buffer.contents):
            out_parts.append(buffer.contents[idx])
        else:
            # Out-of-bounds placeholder — keep literal so we don't
            # silently drop characters
            out_parts.append(m.group(0))
        idx += 1
        last_end = m.end()
    out_parts.append(line[last_end:])
    return "".join(out_parts)


# ---------------------------------------------------------------------------
# prompt_toolkit integration helpers
# ---------------------------------------------------------------------------

def install_paste_handler(session, buffer: PasteBuffer,
                          on_placeholder: Optional[Callable[[PasteResult], None]] = None) -> None:
    """Wire bracketed paste into a prompt_toolkit PromptSession. The session
    already enables bracketed paste by default; we hook the Vt100 paste
    event so multi-line pastes get the placeholder treatment.

    `on_placeholder(result)` is called when a large paste is folded into a
    placeholder — host can log it / show a status notice.
    """
    # prompt_toolkit fires `event.app.current_buffer.insert_text(data)` for
    # bracketed paste internally. We override by binding `<bracketed-paste>`.
    try:
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.keys import Keys
    except Exception:
        return

    kb: KeyBindings = session.key_bindings  # may be None
    if kb is None:
        return

    @kb.add(Keys.BracketedPaste)
    def _on_paste(event) -> None:  # type: ignore[no-untyped-def]
        data = event.data or ""
        result = handle_paste(data, buffer)
        event.current_buffer.insert_text(result.insert_text)
        if result.is_placeholder and on_placeholder is not None:
            try:
                on_placeholder(result)
            except Exception:
                pass
