# Sinister Term :: tests/test_branch_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-57: /branch builtin — current branch + upstream + ahead/behind + dirty.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_branch_returns_dashboard_when_in_repo():
    """Real-repo path: this test runs inside the Sanctum repo so we should
    see actual branch info."""
    from term.commands import cmd_branch
    res = cmd_branch([])
    assert res.handled is True
    assert "Branch:" in res.output


def test_branch_not_in_repo(tmp_path, monkeypatch):
    """When cwd is not a git repo, returns a clear message."""
    monkeypatch.chdir(tmp_path)
    from term.commands import cmd_branch
    res = cmd_branch([])
    assert "not in a git repo" in res.output.lower()


def test_branch_with_mocked_git_output():
    """Mock _git_one so we exercise each branch of the renderer."""
    from term import commands as cmd_mod
    seq = [
        "agent/sinister-term/sa-ph4-shipped-2026-05-25",  # rev-parse HEAD
        "origin/agent/sinister-term/sa-ph4-shipped-2026-05-25",  # upstream
        "2\t0",  # ahead/behind
        "M term/app.py\n?? new.py",  # status --porcelain
        "deadbee shipped iter-57",  # HEAD log
    ]
    with patch.object(cmd_mod, "_git_one", side_effect=seq):
        res = cmd_mod.cmd_branch([])
    out = res.output
    assert "agent/sinister-term/sa-ph4-shipped-2026-05-25" in out
    assert "upstream:" in out
    assert "+2 / -0" in out
    assert "2 changes" in out
    assert "staged=1" in out  # 'M ' = staged
    assert "untracked=1" in out
    assert "deadbee shipped iter-57" in out


def test_branch_clean_tree():
    from term import commands as cmd_mod
    seq = ["main", "origin/main", "0\t0", "", "abc commit msg"]
    with patch.object(cmd_mod, "_git_one", side_effect=seq):
        res = cmd_mod.cmd_branch([])
    assert "working tree:   clean" in res.output


def test_branch_no_upstream():
    from term import commands as cmd_mod
    # First call: branch name; second: upstream returns None
    def fake_git(args, **kwargs):
        if args[0] == "rev-parse" and "--abbrev-ref" in args and "@{u}" in args:
            return None
        if args[0] == "rev-parse":
            return "feat/local-only"
        if args[0] == "status":
            return ""
        if args[0] == "log":
            return "abc1234 some commit"
        return None
    with patch.object(cmd_mod, "_git_one", side_effect=fake_git):
        res = cmd_mod.cmd_branch([])
    assert "no upstream tracking" in res.output


def test_branch_ahead_behind_format():
    from term import commands as cmd_mod
    seq = ["main", "origin/main", "5\t3", "", "abc msg"]
    with patch.object(cmd_mod, "_git_one", side_effect=seq):
        res = cmd_mod.cmd_branch([])
    assert "+5 / -3" in res.output


def test_branch_status_failed_renders_message():
    from term import commands as cmd_mod
    seq = ["main", "origin/main", "0\t0", None, None]
    with patch.object(cmd_mod, "_git_one", side_effect=seq):
        res = cmd_mod.cmd_branch([])
    assert "status failed" in res.output


def test_branch_head_truncation():
    from term import commands as cmd_mod
    long_msg = "abc1234 " + ("x" * 200)
    seq = ["main", "origin/main", "0\t0", "", long_msg]
    with patch.object(cmd_mod, "_git_one", side_effect=seq):
        res = cmd_mod.cmd_branch([])
    # HEAD line truncated to 80 chars with "..."
    head_line = [l for l in res.output.splitlines() if l.strip().startswith("HEAD:")][0]
    assert "..." in head_line


def test_git_one_returns_none_on_failure(tmp_path, monkeypatch):
    """_git_one returns None when git fails (not in a repo)."""
    monkeypatch.chdir(tmp_path)
    from term.commands import _git_one
    assert _git_one(["rev-parse", "--abbrev-ref", "HEAD"]) is None


def test_git_one_timeout_returns_none():
    """If git hangs, _git_one returns None (doesn't propagate)."""
    from term.commands import _git_one
    # 0.0 timeout effectively kills subprocess immediately on most systems
    out = _git_one(["fsck"], timeout_s=0.001)
    # Either None (timeout) or a real result; never raises
    assert out is None or isinstance(out, str)


def test_branch_dispatch_via_slash():
    from term.commands import dispatch
    res = dispatch("/branch")
    assert res.handled is True


def test_branch_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/branch" in res.output


def test_branch_renamed_file_classification():
    """Git status 'R  old -> new' is a staged rename."""
    from term import commands as cmd_mod
    seq = ["main", "origin/main", "0\t0", "R  old.py -> new.py", "abc msg"]
    with patch.object(cmd_mod, "_git_one", side_effect=seq):
        res = cmd_mod.cmd_branch([])
    assert "1 change" in res.output  # singular for 1
    assert "staged=1" in res.output


def test_branch_change_count_singular_vs_plural():
    from term import commands as cmd_mod
    # Singular
    seq1 = ["main", "origin/main", "0\t0", "M a", "abc"]
    with patch.object(cmd_mod, "_git_one", side_effect=seq1):
        res = cmd_mod.cmd_branch([])
    assert "1 change " in res.output  # singular
    # Plural
    seq2 = ["main", "origin/main", "0\t0", "M a\nM b\nM c", "abc"]
    with patch.object(cmd_mod, "_git_one", side_effect=seq2):
        res = cmd_mod.cmd_branch([])
    assert "3 changes" in res.output  # plural
