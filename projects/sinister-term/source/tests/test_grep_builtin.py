# Sinister Term :: tests/test_grep_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-66: /grep content search across files.

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
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "alpha.py").write_text(
        "def foo():\n    pass\ndef bar():\n    return 'TODO'\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "beta.py").write_text(
        "def foo():\n    return 1\nclass FooBar: pass\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text(
        "# Guide\nTODO: write it\n", encoding="utf-8"
    )
    # Skip-dir noise
    (tmp_path / "node_modules" / "lib").mkdir(parents=True)
    (tmp_path / "node_modules" / "lib" / "ignored.py").write_text(
        "TODO ignore me\n", encoding="utf-8"
    )
    # Binary file (NUL byte) -> skipped
    (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02 TODO inside binary")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_grep_no_args(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep([])
    assert "usage:" in res.output.lower()


def test_grep_finds_pattern(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["TODO"])
    # 2 hits: src/alpha.py + docs/guide.md (node_modules + binary skipped)
    assert "2 hits" in res.output
    assert "src/alpha.py" in res.output
    assert "docs/guide.md" in res.output
    assert "node_modules" not in res.output


def test_grep_skips_binary_files(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["TODO"])
    assert "binary.bin" not in res.output


def test_grep_no_matches(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["nonexistenttoken"])
    assert "no matches" in res.output
    assert "nonexistenttoken" in res.output


def test_grep_regex_pattern(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["^def "])
    # 3 def lines (foo in alpha + bar in alpha + foo in beta)
    assert "3 hits" in res.output


def test_grep_case_insensitive(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["todo", "-i"])
    # Case-insensitive: matches TODO
    assert "2 hits" in res.output
    res2 = cmd_grep(["todo"])  # case-sensitive
    assert "no matches" in res2.output


def test_grep_glob_filter(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["TODO", "--glob", "*.py"])
    # Only .py files: src/alpha.py
    assert "1 hit for" in res.output
    assert "src/alpha.py" in res.output
    assert "docs/guide.md" not in res.output  # md file excluded


def test_grep_limit_arg(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["def", "1"])
    assert "1 hit" in res.output


def test_grep_sub_path(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["foo", "src"])
    # Searches under src/ only — foo in alpha + foo in beta
    assert "2 hits" in res.output
    assert "guide.md" not in res.output


def test_grep_sub_path_missing(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["foo", "nonexistent-dir"])
    assert "does not exist" in res.output


def test_grep_bad_regex(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["[unclosed"])
    assert "bad regex" in res.output


def test_grep_unknown_flag(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["foo", "--bogus"])
    assert "unknown flag" in res.output


def test_grep_renders_filename_and_lineno(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["TODO"])
    import re
    # Format: path:lineno: content
    assert re.search(r"src/alpha\.py:\d+: ", res.output)


def test_grep_truncates_long_lines(tmp_path, monkeypatch):
    big = tmp_path / "big.txt"
    big.write_text("MATCH " + ("x" * 500) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    from term.commands import cmd_grep
    res = cmd_grep(["MATCH"])
    assert "..." in res.output
    # Full 500-char line not in output
    assert "x" * 500 not in res.output


def test_grep_dispatch_via_slash(fake_tree):
    from term.commands import dispatch
    res = dispatch("/grep TODO")
    assert res.handled is True


def test_grep_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/grep" in res.output


def test_grep_singular_grammar(fake_tree):
    from term.commands import cmd_grep
    res = cmd_grep(["FooBar"])
    assert "1 hit for" in res.output  # singular


def test_grep_handles_skip_dirs(fake_tree):
    """The 'TODO ignore me' in node_modules should never appear."""
    from term.commands import cmd_grep
    res = cmd_grep(["ignore"])
    assert "no matches" in res.output


def test_grep_two_positional_args_rejected(fake_tree):
    """Can't pass two sub-paths."""
    from term.commands import cmd_grep
    res = cmd_grep(["foo", "src", "docs"])
    # The 3rd positional is an unexpected arg
    assert "unexpected" in res.output.lower() or "no matches" in res.output.lower()
