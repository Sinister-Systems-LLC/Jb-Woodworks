# Sinister Term :: tests/test_crash_recovery.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import pytest

from term import crash_recovery as cr


# ----- restore_terminal --------------------------------------------------

class TestRestoreTerminal:
    def test_restore_idempotent(self, monkeypatch):
        cr._allow_resignal()
        calls = []

        class FakeTty:
            def isatty(self):
                return True
            def write(self, s):
                calls.append(s)
            def flush(self):
                pass

        fake = FakeTty()
        monkeypatch.setattr(sys, "stdout", fake)
        cr.restore_terminal()
        assert len(calls) == 1
        # Second call should be a no-op (already restored)
        calls.clear()
        cr.restore_terminal()
        assert calls == []

    def test_restore_no_raise_on_broken_stream(self, monkeypatch):
        cr._allow_resignal()
        class Bad:
            def isatty(self): return True
            def write(self, s): raise IOError("broken pipe")
            def flush(self): raise IOError("broken pipe")
        monkeypatch.setattr(sys, "stdout", Bad())
        monkeypatch.setattr(sys, "stderr", Bad())
        cr.restore_terminal()  # must not raise

    def test_restore_skips_non_tty(self, monkeypatch):
        cr._allow_resignal()
        calls = []
        class NonTty:
            def isatty(self): return False
            def write(self, s): calls.append(s)
            def flush(self): pass
        monkeypatch.setattr(sys, "stdout", NonTty())
        monkeypatch.setattr(sys, "stderr", NonTty())
        cr.restore_terminal()
        assert calls == []


# ----- log_crash ---------------------------------------------------------

class TestLogCrash:
    def test_writes_jsonl(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cr, "CRASH_LOG", tmp_path / "crashes.jsonl")
        try:
            raise ValueError("boom")
        except ValueError as e:
            cr.log_crash("ctx-x", e, extra={"slug": "test"})
        recs = (tmp_path / "crashes.jsonl").read_text(encoding="utf-8").strip().split("\n")
        assert len(recs) == 1
        rec = json.loads(recs[0])
        assert rec["type"] == "ValueError"
        assert rec["message"] == "boom"
        assert rec["context"] == "ctx-x"
        assert rec["slug"] == "test"
        assert "traceback" in rec

    def test_does_not_raise_on_unwritable_path(self, monkeypatch):
        # Point at a path inside a non-existent directory whose parent
        # creation will succeed but write will be… actually mkdir
        # parents=True so we test the inner write failure differently.
        # Use a path that exists as a directory:
        monkeypatch.setattr(cr, "CRASH_LOG", Path("/dev/null/nope/should_fail"))
        try:
            raise RuntimeError("x")
        except RuntimeError as e:
            # Must not propagate
            cr.log_crash("ctx", e)


# ----- safe_call ---------------------------------------------------------

class TestSafeCall:
    def test_returns_value(self):
        assert cr.safe_call(lambda x: x * 2, 21) == 42

    def test_swallows_exception(self):
        def boom():
            raise RuntimeError("nope")
        assert cr.safe_call(boom, ctx="t", default="fallback") == "fallback"

    def test_passes_through_keyboard_interrupt(self):
        def boom():
            raise KeyboardInterrupt
        with pytest.raises(KeyboardInterrupt):
            cr.safe_call(boom, ctx="t")

    def test_passes_through_system_exit(self):
        def boom():
            raise SystemExit(2)
        with pytest.raises(SystemExit):
            cr.safe_call(boom, ctx="t")


# ----- safe_loop ---------------------------------------------------------

class TestSafeLoop:
    def test_loop_runs_until_step_returns_false(self):
        counter = {"n": 0}
        def step():
            counter["n"] += 1
            return counter["n"] < 3
        cr.safe_loop(step, ctx="t")
        assert counter["n"] == 3

    def test_loop_gives_up_after_max_errors(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cr, "CRASH_LOG", tmp_path / "c.jsonl")
        attempts = {"n": 0}
        def step():
            attempts["n"] += 1
            raise RuntimeError("oops")
        cr.safe_loop(step, ctx="t", max_consecutive_errors=3, backoff_initial_s=0.0)
        assert attempts["n"] == 3

    def test_success_resets_error_counter(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cr, "CRASH_LOG", tmp_path / "c.jsonl")
        seq = [
            "ok", "err", "err", "ok", "err", "err", "stop",
        ]
        i = {"x": 0}
        def step():
            cur = seq[i["x"]]
            i["x"] += 1
            if cur == "err":
                raise ValueError("transient")
            if cur == "stop":
                return False
            return True
        # With 3-error cap, the 2-fail, 1-ok, 2-fail pattern must NOT
        # trigger giveup because the OK resets the count.
        cr.safe_loop(step, ctx="t", max_consecutive_errors=3, backoff_initial_s=0.0)
        assert i["x"] == len(seq)

    def test_keyboard_interrupt_escapes(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cr, "CRASH_LOG", tmp_path / "c.jsonl")
        def step():
            raise KeyboardInterrupt
        with pytest.raises(KeyboardInterrupt):
            cr.safe_loop(step, ctx="t", backoff_initial_s=0.0)


# ----- install_atexit_reset ---------------------------------------------

class TestAtexit:
    def test_install_no_raise(self):
        # Multiple installs should not raise (atexit dedups)
        cr.install_atexit_reset()
        cr.install_atexit_reset()
