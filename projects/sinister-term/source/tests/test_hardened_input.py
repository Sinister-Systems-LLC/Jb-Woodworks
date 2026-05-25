# Sinister Term :: tests/test_hardened_input.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later

from __future__ import annotations

import io
import time

import pytest

from term.hardened_input import (
    CtrlCTracker,
    InputLoopHardener,
    EXIT_WORDS,
    DOUBLE_CTRL_C_WINDOW_S,
    is_exit_line,
    is_tty,
    supports_ansi,
    safe_emit_ansi,
)


# ----- CtrlCTracker ------------------------------------------------------

class TestCtrlCTracker:
    def test_first_press_does_not_exit(self):
        t = CtrlCTracker()
        assert t.register_press() is False

    def test_two_quick_presses_exit(self):
        t = CtrlCTracker(window_s=5.0)
        assert t.register_press() is False
        assert t.register_press() is True

    def test_slow_second_press_does_not_exit(self):
        t = CtrlCTracker(window_s=0.05)
        t.register_press()
        time.sleep(0.1)
        assert t.register_press() is False

    def test_reset_clears_state(self):
        t = CtrlCTracker(window_s=5.0)
        t.register_press()
        t.reset()
        # After reset, the next press is again a "first" press
        assert t.register_press() is False

    def test_third_press_after_exit_starts_fresh(self):
        t = CtrlCTracker(window_s=5.0)
        t.register_press()
        assert t.register_press() is True  # exit
        # Now the tracker reset itself; next is first press again
        assert t.register_press() is False


# ----- is_exit_line ------------------------------------------------------

class TestIsExitLine:
    @pytest.mark.parametrize("word", sorted(EXIT_WORDS))
    def test_exit_words_recognised(self, word):
        assert is_exit_line(word) is True
        assert is_exit_line(word.upper()) is True
        assert is_exit_line(f"  {word}  ") is True

    def test_partial_exit_word_not_exit(self):
        assert is_exit_line("exit now") is False
        assert is_exit_line("quitter") is False
        assert is_exit_line("logoutsomething") is False

    def test_empty_and_none(self):
        assert is_exit_line("") is False
        assert is_exit_line(None) is False
        assert is_exit_line("   ") is False


# ----- TTY / ANSI gating -------------------------------------------------

class TestSupportsAnsi:
    def test_no_tty_means_no_ansi(self):
        s = io.StringIO()  # not a tty
        # safe_emit_ansi should NOT write
        safe_emit_ansi("\x1b[31mhi\x1b[0m", stream=s)
        assert s.getvalue() == ""

    def test_dumb_term_blocks_ansi(self, monkeypatch):
        monkeypatch.setenv("TERM", "dumb")
        # supports_ansi() reads sys.stdout; we just verify it returns False
        # when TERM=dumb AND stdout is a tty. Since stdout isn't a tty in
        # pytest, the function already short-circuits — but it must not raise.
        assert supports_ansi() is False

    def test_safe_emit_does_not_raise_on_broken_stream(self):
        class Broken:
            def isatty(self):
                return True
            def write(self, _):
                raise IOError("broken")
            def flush(self):
                raise IOError("broken")
        # No exception escapes
        safe_emit_ansi("hi", stream=Broken())


# ----- InputLoopHardener -------------------------------------------------

class TestInputLoopHardener:
    def test_first_ctrl_c_returns_false(self):
        h = InputLoopHardener()
        assert h.on_ctrl_c() is False

    def test_second_ctrl_c_returns_true(self):
        h = InputLoopHardener(window_s=5.0)
        h.on_ctrl_c()
        assert h.on_ctrl_c() is True

    def test_reset_after_command(self):
        h = InputLoopHardener(window_s=5.0)
        h.on_ctrl_c()
        h.reset_ctrl_c()
        # Next press is again a "first"
        assert h.on_ctrl_c() is False

    def test_is_exit_delegates(self):
        h = InputLoopHardener()
        assert h.is_exit("exit") is True
        assert h.is_exit("hello") is False
        assert h.is_exit(None) is False

    def test_emit_ansi_no_raise(self):
        h = InputLoopHardener()
        h.emit_ansi("\x1b[2mxx\x1b[0m", stream=io.StringIO())  # no exception
