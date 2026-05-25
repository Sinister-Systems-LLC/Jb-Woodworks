# Sinister Term :: tests/test_crashlog_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-65: /crashlog reads eve-crash-log.jsonl.

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def fake_crashlog(tmp_path):
    jl = tmp_path / "eve-crash-log.jsonl"
    rows = [
        {"ts_utc": "2026-05-25T10:00:00Z", "module": "term.app",
         "agent": "sinister-term", "error": "KeyboardInterrupt at prompt"},
        {"ts_utc": "2026-05-25T11:00:00Z", "module": "sanctum.launcher",
         "agent": "sanctum", "error": "FileNotFoundError: missing eve.exe"},
        {"ts_utc": "2026-05-25T12:00:00Z", "module": "term.jcode_popup",
         "agent": "sinister-term", "error": "RuntimeError: bad ANSI"},
        {"ts_utc": "2026-05-25T13:00:00Z", "module": "eve_compliance.daemon",
         "agent": "eve-compliance", "error": "ConnectionRefusedError"},
        {"ts_utc": "2026-05-25T14:00:00Z", "module": "term.crash_recovery",
         "agent": "sinister-term", "error": "ValueError: x"},
    ]
    jl.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_CRASH_LOG_PATH", jl):
        yield jl


def test_crashlog_default_tail(fake_crashlog):
    from term.commands import cmd_crashlog
    res = cmd_crashlog([])
    assert res.handled is True
    assert "5 of 5" in res.output
    # Last row appears
    assert "term.crash_recovery" in res.output


def test_crashlog_limit_arg(fake_crashlog):
    from term.commands import cmd_crashlog
    res = cmd_crashlog(["2"])
    assert "2 of 5" in res.output
    # Last 2: eve_compliance + term.crash_recovery
    assert "term.crash_recovery" in res.output
    assert "term.app" not in res.output  # 10:00 row not in last 2


def test_crashlog_only_mine(fake_crashlog):
    from term.commands import cmd_crashlog
    res = cmd_crashlog(["--mine"])
    # 3 term.* rows + agent=sinister-term
    assert "3 of 3" in res.output
    assert "term.app" in res.output
    assert "term.jcode_popup" in res.output
    assert "term.crash_recovery" in res.output
    assert "sanctum.launcher" not in res.output
    assert "eve_compliance" not in res.output


def test_crashlog_module_filter(fake_crashlog):
    from term.commands import cmd_crashlog
    res = cmd_crashlog(["--module", "term"])
    # All term.* rows
    assert "3 of 3" in res.output


def test_crashlog_module_filter_substring(fake_crashlog):
    from term.commands import cmd_crashlog
    res = cmd_crashlog(["--module", "jcode"])
    assert "1 of 1" in res.output
    assert "term.jcode_popup" in res.output


def test_crashlog_no_matches(fake_crashlog):
    from term.commands import cmd_crashlog
    res = cmd_crashlog(["--module", "nonexistent"])
    assert "no crashes" in res.output


def test_crashlog_missing_file(tmp_path):
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_CRASH_LOG_PATH", tmp_path / "nope.jsonl"):
        res = cmd_mod.cmd_crashlog([])
    assert "no crash log" in res.output


def test_crashlog_skips_blank_and_corrupt_lines(tmp_path):
    jl = tmp_path / "crashes.jsonl"
    jl.write_text(
        json.dumps({"ts_utc": "2026-05-25T00:00:00Z",
                    "module": "term.x", "error": "boom"}) + "\n"
        "\n"
        "not json{{{\n"
        + json.dumps({"ts_utc": "2026-05-25T00:00:01Z",
                      "module": "term.y", "error": "kaboom"}) + "\n",
        encoding="utf-8",
    )
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_CRASH_LOG_PATH", jl):
        res = cmd_mod.cmd_crashlog([])
    assert "2 of 2" in res.output


def test_crashlog_unknown_arg(fake_crashlog):
    from term.commands import cmd_crashlog
    res = cmd_crashlog(["--bogus"])
    assert "unknown arg" in res.output


def test_crashlog_combined_filters(fake_crashlog):
    """--mine + --module compose."""
    from term.commands import cmd_crashlog
    res = cmd_crashlog(["--mine", "--module", "jcode"])
    # 1 row: term.jcode_popup + agent=sinister-term
    assert "1 of 1" in res.output


def test_crashlog_truncates_long_error(tmp_path):
    jl = tmp_path / "x.jsonl"
    big_err = "x" * 300
    jl.write_text(json.dumps({
        "ts_utc": "2026-05-25T00:00:00Z", "module": "m", "error": big_err,
    }) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_CRASH_LOG_PATH", jl):
        res = cmd_mod.cmd_crashlog([])
    assert big_err not in res.output  # not full
    assert "..." in res.output


def test_crashlog_dispatch_via_slash(fake_crashlog):
    from term.commands import dispatch
    res = dispatch("/crashlog")
    assert res.handled is True


def test_crashlog_alias_crashes(fake_crashlog):
    from term.commands import dispatch
    res = dispatch("/crashes 2")
    assert res.handled is True
    assert "2 of 5" in res.output


def test_crashlog_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/crashlog" in res.output


def test_crashlog_renders_iso_ts(fake_crashlog):
    from term.commands import cmd_crashlog
    res = cmd_crashlog([])
    # ISO timestamps with Z suffix
    assert "2026-05-25T14:00:00Z" in res.output


def test_crashlog_accepts_err_alias(tmp_path):
    """Crash rows that use 'err' instead of 'error' still render."""
    jl = tmp_path / "x.jsonl"
    jl.write_text(json.dumps({
        "ts_utc": "2026-05-25T00:00:00Z", "module": "m", "err": "alt key",
    }) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_CRASH_LOG_PATH", jl):
        res = cmd_mod.cmd_crashlog([])
    assert "alt key" in res.output
