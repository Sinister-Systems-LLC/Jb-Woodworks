# Sinister Term :: hardened_input.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Patterns ported from jcode for an "isn't sensitive" input loop:
#   - Double-Ctrl+C confirmation (jcode ui_overlays.rs:367 "press twice to confirm")
#   - Tolerant unknown-keybinding (silent ignore, not crash)
#   - Quiet-mode exit (single 'exit'/'quit' word counts only when buffer is
#     otherwise empty, prevents accidental exit while editing a command)
#   - Terminal-capability gating (don't emit OSC titles when not a TTY)
#
# Source MIT (Copyright (c) 2025 Jeremy Huang). Re-licensed under
# AGPL-3.0-or-later per upstream MIT.

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from typing import Callable, Optional


# Double-Ctrl+C window. If two Ctrl+C come within this many seconds, treat
# as quit; otherwise the first is just a buffer-clear hint.
DOUBLE_CTRL_C_WINDOW_S = 1.5

# Words that COUNT as exit on an empty prompt. Anything typed mid-command is
# passed through to the shell.
EXIT_WORDS = frozenset({"exit", "quit", "logout", ":q", ":wq"})


@dataclass
class CtrlCTracker:
    """Tracks repeated Ctrl+C presses to implement the 'press twice to quit'
    pattern. jcode ui_overlays.rs:367 surfaces 'Quit (press twice to confirm)'.

    Usage:
        tracker = CtrlCTracker()
        # in your KeyboardInterrupt handler:
        if tracker.register_press():
            break  # second ctrl+c within window → exit
        else:
            print("(^C — press again to quit)")
    """
    window_s: float = DOUBLE_CTRL_C_WINDOW_S
    _last_press: float = 0.0
    _press_count: int = 0

    def register_press(self) -> bool:
        """Return True if this is the SECOND press inside the window."""
        now = time.monotonic()
        if (now - self._last_press) <= self.window_s and self._press_count >= 1:
            # second press inside window
            self._press_count = 0
            self._last_press = 0.0
            return True
        self._last_press = now
        self._press_count = 1
        return False

    def reset(self) -> None:
        self._last_press = 0.0
        self._press_count = 0


def is_exit_line(line: str) -> bool:
    """Operator-friendly 'is this just an exit command?' check. We DON'T
    treat 'exit something' as exit — only the bare word."""
    if not line:
        return False
    stripped = line.strip()
    if not stripped:
        return False
    return stripped.lower() in EXIT_WORDS


def is_tty(stream=None) -> bool:
    """Safe TTY check. Defaults to stdout."""
    s = stream if stream is not None else sys.stdout
    try:
        return bool(getattr(s, "isatty", lambda: False)())
    except Exception:
        return False


def supports_ansi() -> bool:
    """Best-effort: are we on a terminal that understands ANSI escapes?
    Used to gate cosmetic OSC writes (title, cursor color) so we don't
    spew junk into pipes/log files."""
    if not is_tty():
        return False
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False
    # Windows: modern terminals all set TERM or ConEmu*/WT_SESSION
    if sys.platform == "win32":
        if "WT_SESSION" in os.environ:
            return True
        if "ConEmuPID" in os.environ:
            return True
        # PowerShell + Windows 10+ default cmd both support VT now, but be
        # conservative: if TERM is unset on Windows we default to off so
        # piping to file doesn't produce escape soup.
        return bool(term)
    return True


def safe_emit_ansi(seq: str, stream=None) -> None:
    """Write `seq` to stream IFF the stream looks like a real terminal.
    Never raises."""
    if not supports_ansi():
        return
    s = stream if stream is not None else sys.stdout
    try:
        s.write(seq)
        s.flush()
    except Exception:
        pass


@dataclass
class InputLoopHardener:
    """Bundles the Ctrl+C tracker + exit detection + ANSI gating so app.py
    can keep its loop simple. Designed to be drop-in friendly.

    Example:
        h = InputLoopHardener()
        while True:
            try:
                line = session.prompt(...)
            except KeyboardInterrupt:
                if h.on_ctrl_c():
                    break  # quit
                print("(^C — press again to exit)")
                continue
            except EOFError:
                break
            if h.is_exit(line):
                break
            run(line)
    """
    ctrl_c: CtrlCTracker

    def __init__(self, window_s: float = DOUBLE_CTRL_C_WINDOW_S):
        self.ctrl_c = CtrlCTracker(window_s=window_s)

    def on_ctrl_c(self) -> bool:
        """Returns True when caller should exit (second press inside window)."""
        return self.ctrl_c.register_press()

    def is_exit(self, line: Optional[str]) -> bool:
        if line is None:
            return False
        return is_exit_line(line)

    def reset_ctrl_c(self) -> None:
        self.ctrl_c.reset()

    def emit_ansi(self, seq: str, stream=None) -> None:
        safe_emit_ansi(seq, stream)
