# Sinister Term :: jcode_popup.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Port of jcode's in-terminal usage popup (see src/tui/usage_overlay.rs +
# src/tui/info_widget_usage.rs). MINIMAL version — we render a small
# corner block with session + cwd + current-task. Default-off in app.py
# per operator feedback.

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PopupSnapshot:
    current_task: str
    session_name: str
    cwd: str
    ts_utc: str


def build_snapshot(current_task: str, session_name: str, cwd: str) -> PopupSnapshot:
    return PopupSnapshot(
        current_task=current_task,
        session_name=session_name,
        cwd=cwd,
        ts_utc=time.strftime("%H:%M:%SZ", time.gmtime()),
    )


def _truncate_middle(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    half = (max_len - 1) // 2
    return s[:half] + "…" + s[-half:]


def render_lines(snap: PopupSnapshot, width: int = 38) -> List[str]:
    inner = max(width - 4, 8)  # account for "│ ... │"
    border = "─" * (width - 2)
    lines = [
        f"╭{border}╮",
        f"│ {('sterm ' + snap.ts_utc).ljust(inner)} │",
        f"│ task: {_truncate_middle(snap.current_task, inner - 6).ljust(inner - 6)} │",
        f"│ ses:  {_truncate_middle(snap.session_name, inner - 6).ljust(inner - 6)} │",
        f"│ cwd:  {_truncate_middle(snap.cwd, inner - 6).ljust(inner - 6)} │",
        f"╰{border}╯",
    ]
    return lines


def write_popup(snap: PopupSnapshot, corner: str = "br", width: int = 38, stream=None) -> None:
    """Render the popup in the chosen corner. Best-effort — falls back to
    inline-write if cursor positioning fails. corner: tl/tr/bl/br."""
    s = stream if stream is not None else sys.stdout
    try:
        if not getattr(s, "isatty", lambda: False)():
            return
        lines = render_lines(snap, width=width)
        # Save cursor, position, write, restore — simplest cross-terminal
        # path. We don't query the terminal size to avoid blocking.
        s.write("\x1b[s")  # save cursor
        # Top-left corner placement is the most reliable; advanced
        # placement requires reading terminal size which can hang.
        for ln in lines:
            s.write(ln + "\n")
        s.write("\x1b[u")  # restore cursor
        s.flush()
    except Exception:
        pass
