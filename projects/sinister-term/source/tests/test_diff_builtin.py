# Sinister Term :: tests/test_diff_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-70: /diff builtin — git diff --stat.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_diff_not_in_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from term.commands import cmd_diff
    res = cmd_diff([])
    assert res.handled is True
    assert "not in a git repo" in res.output


def test_diff_no_changes_in_real_repo():
    """When the tree is clean for the path, returns '(no changes)'."""
    from term import commands as cmd_mod
    # Mock _git_one to: branch exists, but both diff calls return empty
    def fake_git(args, **kwargs):
        if "rev-parse" in args:
            return "main"
        return ""
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        res = cmd_mod.cmd_diff([])
    assert "no changes" in res.output


def test_diff_renders_unstaged_and_staged_sections():
    from term import commands as cmd_mod
    seq = {
        ("rev-parse",): "main",
        ("diff_no_staged",): "  src/a.py | 5 +++++\n 1 file changed",
        ("diff_staged",): "  src/b.py | 3 ---",
    }
    def fake_git(args, **kwargs):
        if "rev-parse" in args:
            return seq[("rev-parse",)]
        if "--staged" in args:
            return seq[("diff_staged",)]
        return seq[("diff_no_staged",)]
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        res = cmd_mod.cmd_diff([])
    assert "Diff (branch=main)" in res.output
    assert "[unstaged]" in res.output
    assert "[staged]" in res.output
    assert "src/a.py" in res.output
    assert "src/b.py" in res.output


def test_diff_staged_only():
    from term import commands as cmd_mod
    def fake_git(args, **kwargs):
        if "rev-parse" in args:
            return "main"
        if "--staged" in args:
            return "  src/x.py | 2 ++"
        return "  src/y.py | 1 +"  # should not appear
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        res = cmd_mod.cmd_diff(["--staged"])
    assert "[staged]" in res.output
    assert "[unstaged]" not in res.output
    assert "src/x.py" in res.output
    assert "src/y.py" not in res.output


def test_diff_unstaged_only():
    from term import commands as cmd_mod
    def fake_git(args, **kwargs):
        if "rev-parse" in args:
            return "main"
        if "--staged" in args:
            return "  src/should-skip.py | 1 +"
        return "  src/keep.py | 1 +"
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        res = cmd_mod.cmd_diff(["--unstaged"])
    assert "[unstaged]" in res.output
    assert "[staged]" not in res.output
    assert "src/keep.py" in res.output
    assert "src/should-skip.py" not in res.output


def test_diff_name_only_uses_different_git_args():
    from term import commands as cmd_mod
    captured: list[list[str]] = []
    def fake_git(args, **kwargs):
        captured.append(list(args))
        if "rev-parse" in args:
            return "main"
        return "src/a.py\nsrc/b.py"
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        cmd_mod.cmd_diff(["--name-only"])
    # Verify at least one git invocation used --name-only
    assert any("--name-only" in c for c in captured)


def test_diff_with_path_arg():
    from term import commands as cmd_mod
    captured: list[list[str]] = []
    def fake_git(args, **kwargs):
        captured.append(list(args))
        if "rev-parse" in args:
            return "main"
        return ""
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        cmd_mod.cmd_diff(["projects/sinister-term"])
    diff_calls = [c for c in captured if "rev-parse" not in c]
    # Each diff invocation should include `--` and the path
    assert all(("--" in c and "projects/sinister-term" in c) for c in diff_calls)


def test_diff_unknown_flag():
    from term.commands import cmd_diff
    res = cmd_diff(["--bogus"])
    assert "unknown flag" in res.output


def test_diff_two_positional_args_rejected():
    from term.commands import cmd_diff
    res = cmd_diff(["path1", "path2"])
    assert "unexpected" in res.output.lower()


def test_diff_truncates_huge_diff():
    """A diff with >40 file lines gets capped + shows the overflow count."""
    from term import commands as cmd_mod
    big_diff = "\n".join(f" file{i}.py | 1 +" for i in range(100))
    def fake_git(args, **kwargs):
        if "rev-parse" in args:
            return "main"
        if "--staged" in args:
            return ""
        return big_diff
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        res = cmd_mod.cmd_diff([])
    assert "more)" in res.output
    # Specifically: 100 - 40 = 60 more
    assert "60 more" in res.output


def test_diff_truncates_long_single_lines():
    from term import commands as cmd_mod
    long_line = "  src/" + ("x" * 200) + ".py | 1 +"
    def fake_git(args, **kwargs):
        if "rev-parse" in args:
            return "main"
        if "--staged" in args:
            return ""
        return long_line
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        res = cmd_mod.cmd_diff([])
    # 200-char filename body should be truncated with "..."
    assert "..." in res.output
    assert "x" * 200 not in res.output


def test_diff_dispatch_via_slash():
    from term import commands as cmd_mod
    def fake_git(args, **kwargs):
        if "rev-parse" in args:
            return "main"
        return ""
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        from term.commands import dispatch
        res = dispatch("/diff")
    assert res.handled is True


def test_diff_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/diff" in res.output
