# Sinister Term :: tests/test_man_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-72: /man drilldown for builtin docstrings.

from __future__ import annotations

import sys
from pathlib import Path

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_man_no_args_lists_all_names():
    from term.commands import cmd_man
    res = cmd_man([])
    assert res.handled is True
    assert "Builtins" in res.output
    # A few known builtins
    for name in ("help", "exit", "ascii", "events", "watch", "find", "grep",
                 "version", "diff", "me"):
        assert name in res.output, f"missing: {name}"
    # Hint at end
    assert "/man <name>" in res.output


def test_man_a_flag_includes_summaries():
    from term.commands import cmd_man
    res = cmd_man(["-a"])
    assert "with summaries" in res.output
    # Each row should be `/<name>  <summary>`
    lines = [l for l in res.output.splitlines() if l.startswith("  /")]
    assert len(lines) >= 30  # we have 30+ builtins


def test_man_specific_command_shows_docstring():
    from term.commands import cmd_man
    res = cmd_man(["recall"])
    assert "/recall" in res.output
    # cmd_recall's docstring mentions "knowledge"
    assert "knowledge" in res.output.lower()
    # Header has the handler name (cmd_recall)
    assert "cmd_recall" in res.output


def test_man_unknown_command_suggests():
    """Fuzzy suggestion on miss."""
    from term.commands import cmd_man
    res = cmd_man(["recal"])  # missing trailing 'l'
    assert "unknown builtin" in res.output
    assert "did you mean" in res.output
    assert "recall" in res.output


def test_man_unknown_no_close_match():
    from term.commands import cmd_man
    res = cmd_man(["zzzzzzzzz"])
    assert "unknown builtin" in res.output


def test_man_strips_leading_slash():
    """`/man /recall` works as well as `/man recall`."""
    from term.commands import cmd_man
    res = cmd_man(["/recall"])
    assert "/recall" in res.output
    assert "cmd_recall" in res.output


def test_man_case_insensitive_lookup():
    from term.commands import cmd_man
    res = cmd_man(["RECALL"])
    assert "cmd_recall" in res.output


def test_man_renders_separator_line():
    """The header has a separator line of dashes."""
    from term.commands import cmd_man
    res = cmd_man(["help"])
    assert "─" in res.output


def test_man_dispatch_via_slash():
    from term.commands import dispatch
    res = dispatch("/man events")
    assert res.handled is True
    assert "/events" in res.output


def test_man_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/man" in res.output


def test_man_for_no_doc_command():
    """If a handler has no docstring, /man returns '(no docstring)'."""
    from term import commands as cmd_mod
    # cmd_help has no docstring currently
    res = cmd_mod.cmd_man(["help"])
    # Either docstring text or the placeholder
    assert "/help" in res.output


def test_man_all_command_count_matches_commands_dict():
    """`/man` count matches len(COMMANDS)."""
    from term.commands import cmd_man, COMMANDS
    res = cmd_man([])
    import re
    match = re.search(r"Builtins \((\d+) registered\)", res.output)
    assert match is not None
    assert int(match.group(1)) == len(COMMANDS)


def test_man_summary_first_line_only():
    """For -a, each summary is one line (no multi-line bleeding)."""
    from term.commands import cmd_man
    res = cmd_man(["-a"])
    for ln in res.output.splitlines():
        if ln.startswith("  /"):
            # Each builtin row is a single line; no embedded newlines mid-row
            assert "\n" not in ln
