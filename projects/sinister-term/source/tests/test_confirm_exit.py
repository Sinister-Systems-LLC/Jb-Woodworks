# Sinister Term :: tests/test_confirm_exit.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Covers the X-button popup (_confirm_exit) added 2026-05-25T14:15Z per
# operator: *"make the x button have a extra popup before just closing"*.

from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class _FakeConsole:
    def __init__(self) -> None:
        self.printed: list[str] = []

    def print(self, *args, **kwargs) -> None:
        self.printed.append(" ".join(str(a) for a in args))


@pytest.fixture
def console() -> _FakeConsole:
    return _FakeConsole()


@pytest.fixture
def clear_env():
    keys = ["SINISTER_TERM_FAST_EXIT"]
    saved = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_fast_exit_env_bypasses_popup(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    os.environ["SINISTER_TERM_FAST_EXIT"] = "1"
    assert _confirm_exit(console) is True
    # Popup should not have been printed
    assert not any("Exit Sinister Term" in p for p in console.printed)


def test_fast_exit_env_accepts_true_on(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    for val in ("true", "on", "True", "ON", "1"):
        os.environ["SINISTER_TERM_FAST_EXIT"] = val
        assert _confirm_exit(console) is True


def test_non_tty_stdin_confirms_exit(clear_env, console: _FakeConsole):
    """Piped/CI stdin (no TTY) must NOT hang — auto-confirm exit."""
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=False):
        assert _confirm_exit(console) is True


def test_y_confirms_exit(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", return_value="y"):
        assert _confirm_exit(console) is True


def test_yes_confirms_exit(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", return_value="yes"):
        assert _confirm_exit(console) is True


def test_uppercase_y_confirms(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", return_value="Y"):
        assert _confirm_exit(console) is True


def test_n_keeps_running(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", return_value="n"):
        assert _confirm_exit(console) is False


def test_empty_keeps_running(clear_env, console: _FakeConsole):
    """Default (just-Enter) is STAY — accidental Ctrl+D shouldn't kill the shell."""
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", return_value=""):
        assert _confirm_exit(console) is False


def test_arbitrary_text_keeps_running(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", return_value="lol no"):
        assert _confirm_exit(console) is False


def test_eof_at_confirmation_confirms(clear_env, console: _FakeConsole):
    """If they Ctrl+D again at the confirmation, they really mean it."""
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", side_effect=EOFError):
        assert _confirm_exit(console) is True


def test_keyboard_interrupt_at_confirmation_confirms(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", side_effect=KeyboardInterrupt):
        assert _confirm_exit(console) is True


def test_popup_printed_when_interactive(clear_env, console: _FakeConsole):
    from term.app import _confirm_exit
    with patch.object(sys.stdin, "isatty", return_value=True), \
         patch("builtins.input", return_value="n"):
        _confirm_exit(console)
    assert any("Exit Sinister Term" in p for p in console.printed)
