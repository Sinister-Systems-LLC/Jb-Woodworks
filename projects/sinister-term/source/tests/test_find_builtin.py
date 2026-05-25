# Sinister Term :: tests/test_find_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-63: /find builtin recursive name search.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def fake_tree(tmp_path, monkeypatch):
    """Build a small file tree + chdir into it so /find searches it by default."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "alpha.py").write_text("# alpha\n", encoding="utf-8")
    (tmp_path / "src" / "beta.py").write_text("# beta\n", encoding="utf-8")
    (tmp_path / "src" / "alpha.md").write_text("# md\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("hi\n", encoding="utf-8")
    # Heavy dir that should be skipped
    (tmp_path / "node_modules" / "lib").mkdir(parents=True)
    (tmp_path / "node_modules" / "lib" / "noise.py").write_text("", encoding="utf-8")
    (tmp_path / ".git" / "objects").mkdir(parents=True)
    (tmp_path / ".git" / "objects" / "deadbeef.py").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_find_no_args(fake_tree):
    from term.commands import cmd_find
    res = cmd_find([])
    assert "usage:" in res.output.lower()


def test_find_python_files(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["*.py"])
    assert res.handled is True
    # 2 .py files in src/ (alpha + beta), node_modules + .git skipped
    assert "src/alpha.py" in res.output
    assert "src/beta.py" in res.output
    assert "node_modules" not in res.output
    assert ".git" not in res.output


def test_find_returns_2_matches(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["*.py"])
    assert "2 matches" in res.output


def test_find_one_match_singular(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["guide.md"])
    assert "1 match for" in res.output


def test_find_md_files(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["*.md"])
    assert "alpha.md" in res.output
    assert "guide.md" in res.output


def test_find_no_matches(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["*.rs"])
    assert "no matches" in res.output.lower()
    assert "*.rs" in res.output


def test_find_directories_only(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["src", "--type", "d"])
    # src directory matches
    assert "src" in res.output
    # Files DON'T match
    assert "src/alpha.py" not in res.output


def test_find_files_only_default(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["src"])
    # src is a directory; --type defaults to f so no match
    assert "no matches" in res.output


def test_find_explicit_files_filter(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["*.py", "--type", "f"])
    assert "src/alpha.py" in res.output


def test_find_invalid_type(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["x", "--type", "weird"])
    assert "--type must be f or d" in res.output


def test_find_limit(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["*.md", "1"])
    assert "1 match for" in res.output


def test_find_sanctum_flag_uses_sanctum_root(tmp_path, monkeypatch):
    """--sanctum flag searches under SANCTUM_ROOT, not cwd."""
    # Build sanctum with a known file
    sanctum = tmp_path / "sanctum"
    sanctum.mkdir()
    (sanctum / "marker.special").write_text("", encoding="utf-8")
    # cwd is elsewhere
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    from term import commands as cmd_mod
    with patch.object(cmd_mod, "SANCTUM_ROOT", sanctum):
        # Without --sanctum: no match (cwd is elsewhere/)
        res1 = cmd_mod.cmd_find(["marker.special"])
        assert "no matches" in res1.output
        # With --sanctum: finds it
        res2 = cmd_mod.cmd_find(["marker.special", "--sanctum"])
        assert "marker.special" in res2.output


def test_find_dispatch_via_slash(fake_tree):
    from term.commands import dispatch
    res = dispatch("/find *.py")
    assert res.handled is True


def test_find_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/find" in res.output


def test_find_skips_node_modules_and_git(fake_tree):
    """SKIP_DIRS should be honored."""
    from term.commands import cmd_find
    # Pattern that would match in node_modules + .git but should be skipped
    res = cmd_find(["noise.py"])
    assert "no matches" in res.output  # noise.py is in node_modules → skipped
    res2 = cmd_find(["deadbeef.py"])
    assert "no matches" in res2.output  # deadbeef.py is in .git → skipped


def test_find_long_path_truncation(tmp_path, monkeypatch):
    """Paths longer than 100 chars get truncated with leading ..."""
    deep = tmp_path
    for i in range(15):
        deep = deep / f"deeply-nested-dir-{i}"
    deep.mkdir(parents=True)
    target = deep / "leaf.py"
    target.write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    from term.commands import cmd_find
    res = cmd_find(["leaf.py"])
    # Filter to indented match rows (skip the header line)
    match_lines = [l for l in res.output.splitlines()
                   if l.startswith("  ") and "leaf.py" in l]
    assert match_lines
    # Each match row's content is capped at 100 chars + 2-space indent
    for l in match_lines:
        body = l.lstrip()
        assert "..." in body or len(body) <= 100


def test_find_unknown_arg(fake_tree):
    from term.commands import cmd_find
    res = cmd_find(["*.py", "--bogus"])
    assert "unknown arg" in res.output.lower()
