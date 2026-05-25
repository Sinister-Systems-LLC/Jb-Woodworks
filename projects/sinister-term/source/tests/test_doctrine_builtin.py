# Sinister Term :: tests/test_doctrine_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-64: /doctrine builtin lists Operator hard-canonical headings from
# Sanctum CLAUDE.md + project-lane CLAUDE.md.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


_SANCTUM_MD = """\
# CLAUDE.md — Sinister Sanctum

## Operator hard-canonical 2026-05-25 — NO GATE QUESTIONS — EXECUTE DIRECTLY

Operator (verbatim 2026-05-25): *"make everything we do autonomous"*

Body of the canonical here.

## Operator hard-canonical 2026-05-24 — SOMETHING ELSE

Operator: *"this is a different directive"*

## Operator hard-canonical 2026-05-23 — RKOJ-ELENO AUTHORSHIP

Operator (verbatim 2026-05-23): *"everything needs to be ours"*

## Some Other Heading (not a hard-canonical)

ignore me
"""

_PROJECT_MD = """\
# Sinister Term :: CLAUDE.md

## Operator hard-canonical 2026-05-25 — TERM-SPECIFIC RULE

Operator: *"this is a lane-level rule"*
"""


@pytest.fixture
def fake_claude_mds(tmp_path):
    sanctum = tmp_path / "sanctum"
    (sanctum / "projects" / "sinister-term").mkdir(parents=True)
    (sanctum / "CLAUDE.md").write_text(_SANCTUM_MD, encoding="utf-8")
    (sanctum / "projects" / "sinister-term" / "CLAUDE.md").write_text(
        _PROJECT_MD, encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "SANCTUM_ROOT", sanctum):
        yield sanctum


def test_doctrine_lists_all_canonicals(fake_claude_mds):
    from term.commands import cmd_doctrine
    res = cmd_doctrine([])
    assert res.handled is True
    # 3 from sanctum + 1 from lane = 4
    assert "4 doctrines" in res.output


def test_doctrine_extracts_title_and_quote(fake_claude_mds):
    from term.commands import cmd_doctrine
    res = cmd_doctrine([])
    assert "NO GATE QUESTIONS" in res.output
    assert "make everything we do autonomous" in res.output
    assert "RKOJ-ELENO AUTHORSHIP" in res.output
    assert "everything needs to be ours" in res.output


def test_doctrine_marks_source_sanctum_vs_lane(fake_claude_mds):
    from term.commands import cmd_doctrine
    res = cmd_doctrine([])
    assert "[sanctum]" in res.output
    assert "[lane   ]" in res.output


def test_doctrine_sanctum_only_filter(fake_claude_mds):
    from term.commands import cmd_doctrine
    res = cmd_doctrine(["--sanctum"])
    assert "3 doctrines" in res.output
    assert "TERM-SPECIFIC RULE" not in res.output


def test_doctrine_search_filter(fake_claude_mds):
    from term.commands import cmd_doctrine
    res = cmd_doctrine(["--search", "authorship"])
    assert "1 doctrine" in res.output
    assert "RKOJ-ELENO AUTHORSHIP" in res.output
    # Case-insensitive: query 'authorship' matches 'AUTHORSHIP'


def test_doctrine_search_no_match(fake_claude_mds):
    from term.commands import cmd_doctrine
    res = cmd_doctrine(["--search", "nonsense"])
    assert "no hard-canonicals" in res.output


def test_doctrine_no_canonicals_when_md_missing(tmp_path):
    """If neither CLAUDE.md file exists, returns clear message."""
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "SANCTUM_ROOT", tmp_path / "empty"):
        res = cmd_mod.cmd_doctrine([])
    assert "no hard-canonicals" in res.output


def test_doctrine_newest_first(fake_claude_mds):
    from term.commands import cmd_doctrine
    res = cmd_doctrine([])
    lines = res.output.splitlines()
    may25_idx = next(i for i, l in enumerate(lines) if "2026-05-25" in l and "NO GATE" in l)
    may23_idx = next(i for i, l in enumerate(lines) if "2026-05-23" in l)
    assert may25_idx < may23_idx


def test_doctrine_sanctum_before_lane_same_date(fake_claude_mds):
    """When same date, sanctum-level canonical appears before lane-level."""
    from term.commands import cmd_doctrine
    res = cmd_doctrine([])
    lines = res.output.splitlines()
    # Both 2026-05-25 entries
    gates = next(i for i, l in enumerate(lines) if "NO GATE" in l)
    term_rule = next(i for i, l in enumerate(lines) if "TERM-SPECIFIC" in l)
    assert gates < term_rule


def test_doctrine_unknown_arg(fake_claude_mds):
    from term.commands import cmd_doctrine
    res = cmd_doctrine(["--bogus"])
    assert "unknown arg" in res.output


def test_doctrine_dispatch_via_slash(fake_claude_mds):
    from term.commands import dispatch
    res = dispatch("/doctrine --sanctum")
    assert res.handled is True


def test_doctrine_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/doctrine" in res.output


def test_doctrine_handles_long_title(tmp_path):
    """Titles longer than 70 chars get truncated with ..."""
    sanctum = tmp_path / "s"
    sanctum.mkdir()
    long_title = "A" * 100
    (sanctum / "CLAUDE.md").write_text(
        f"## Operator hard-canonical 2026-05-25 — {long_title}\n\n"
        "*\"some quote\"*\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "SANCTUM_ROOT", sanctum):
        res = cmd_mod.cmd_doctrine([])
    assert "..." in res.output


def test_doctrine_skips_non_matching_headings(fake_claude_mds):
    """Plain `## Something` headings (not 'Operator hard-canonical') are ignored."""
    from term.commands import cmd_doctrine
    res = cmd_doctrine([])
    assert "Some Other Heading" not in res.output
