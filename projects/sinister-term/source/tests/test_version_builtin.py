# Sinister Term :: tests/test_version_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-71: /version composite dashboard.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_version_returns_dashboard():
    from term.commands import cmd_version
    res = cmd_version([])
    assert res.handled is True
    for row in (
        "Version dashboard",
        "sinister-term:",
        "sinister-ascii:",
        "python:",
        "prompt_toolkit",
        "rich",
        "pytest",
        "git HEAD:",
        "term modules:",
        "builtins:",
    ):
        assert row in res.output, f"missing row: {row!r}"


def test_version_sinister_term_includes_a_version_string():
    from term.commands import cmd_version
    res = cmd_version([])
    # Find the sinister-term line
    line = next(l for l in res.output.splitlines() if "sinister-term:" in l)
    # Either a real version OR "? (...)"
    assert any(ch.isdigit() for ch in line) or "?" in line


def test_version_python_renders_three_components():
    from term.commands import cmd_version
    res = cmd_version([])
    import re
    # Look for the python line with format X.Y.Z
    line = next(l for l in res.output.splitlines() if "python:" in l)
    assert re.search(r"\d+\.\d+\.\d+", line)


def test_version_builtins_count_includes_version_itself():
    """The dispatch table includes /version (just added), so count > 0."""
    from term.commands import cmd_version
    res = cmd_version([])
    line = next(l for l in res.output.splitlines() if "builtins:" in l)
    import re
    match = re.search(r"(\d+) commands registered", line)
    assert match is not None
    count = int(match.group(1))
    # We've shipped 30+ builtins by iter-71
    assert count >= 30


def test_version_dispatch_via_slash():
    from term.commands import dispatch
    res = dispatch("/version")
    assert res.handled is True
    assert "Version dashboard" in res.output


def test_version_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/version" in res.output


def test_version_handles_missing_pkg_gracefully():
    """If __import__ raises, the row says '(not installed)'."""
    from term import commands as cmd_mod
    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
    def bad_import(name, *a, **kw):
        if name == "rich":
            raise ImportError("simulated missing rich")
        return real_import(name, *a, **kw)
    with patch("builtins.__import__", side_effect=bad_import):
        res = cmd_mod.cmd_version([])
    assert "rich" in res.output
    assert "(not installed)" in res.output


def test_version_git_head_short_sha_or_msg():
    from term.commands import cmd_version
    res = cmd_version([])
    line = next(l for l in res.output.splitlines() if "git HEAD:" in l)
    # Either a 7-char-ish sha or the not-in-repo message
    assert "not in a git repo" in line or len(line.split(":", 1)[1].strip()) >= 4


def test_version_term_modules_count_positive():
    from term.commands import cmd_version
    res = cmd_version([])
    line = next(l for l in res.output.splitlines() if "term modules:" in l)
    import re
    match = re.search(r"(\d+) files in", line)
    assert match is not None
    assert int(match.group(1)) >= 10  # we have many term/*.py modules


def test_version_sinister_ascii_shown():
    """sinister-ascii row is always present (importable or with err marker)."""
    from term.commands import cmd_version
    res = cmd_version([])
    assert "sinister-ascii:" in res.output


def test_version_resilient_to_one_broken_dep(monkeypatch):
    """Force pytest-import failure; other rows still render."""
    from term import commands as cmd_mod
    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
    def bad_import(name, *a, **kw):
        if name == "pytest":
            raise RuntimeError("boom")
        return real_import(name, *a, **kw)
    with patch("builtins.__import__", side_effect=bad_import):
        res = cmd_mod.cmd_version([])
    # pytest line shows '(not installed)' but rest render
    assert "Version dashboard" in res.output
    assert "python:" in res.output
    assert "prompt_toolkit" in res.output
