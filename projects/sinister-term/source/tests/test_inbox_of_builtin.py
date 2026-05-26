# Sinister Term :: tests/test_inbox_of_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-75: /inbox-of (alias /io) peeks at another agent's inbox.

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def fake_inboxes(tmp_path):
    base = tmp_path / "inbox"
    base.mkdir()

    for slug, msgs in [
        ("sanctum", [
            ("a.json", {"subject": "alpha message", "from": "x"}),
            ("b.json", {"subject": "beta", "from": "y"}),
            ("c.md", "# title-c-md\n\nbody\n"),
        ]),
        ("sinister-mind", []),
        ("eve-exe", [
            ("d.json", {"title": "title-key-d", "from": "z"}),
        ]),
    ]:
        d = base / slug
        d.mkdir()
        for name, content in msgs:
            p = d / name
            if isinstance(content, dict):
                p.write_text(json.dumps(content), encoding="utf-8")
            else:
                p.write_text(content, encoding="utf-8")

    from term import commands as cmd_mod
    with patch.object(cmd_mod, "INBOX_DIR", base):
        yield base


def test_inbox_of_no_args_lists_all_with_counts(fake_inboxes):
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of([])
    assert res.handled is True
    assert "3 agents" in res.output
    assert "sanctum" in res.output and "3 msg" in res.output
    assert "sinister-mind" in res.output and "0 msg" in res.output
    assert "eve-exe" in res.output and "1 msg" in res.output


def test_inbox_of_exact_slug(fake_inboxes):
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["sanctum"])
    assert "Inbox-of sanctum: 3 of 3" in res.output
    assert "alpha message" in res.output
    assert "title-c-md" in res.output


def test_inbox_of_substring_unique(fake_inboxes):
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["mind"])
    # sinister-mind is the only match
    assert "Inbox-of sinister-mind" in res.output or "empty" in res.output


def test_inbox_of_substring_ambiguous(fake_inboxes):
    """Substring that matches multiple slugs returns the candidates list."""
    # Add a second 'sinister-*' inbox so 'sinister' matches multiple
    extra = fake_inboxes / "sinister-forge"
    extra.mkdir()
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["sinister"])
    assert "ambiguous" in res.output


def test_inbox_of_no_match(fake_inboxes):
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["totally-nonexistent"])
    assert "no inbox matching" in res.output
    assert "available:" in res.output


def test_inbox_of_empty_inbox(fake_inboxes):
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["sinister-mind"])
    assert "empty" in res.output


def test_inbox_of_renders_age_newest_first(fake_inboxes):
    """Newest message comes first; oldest comes last."""
    # Set varied mtimes
    sanctum = fake_inboxes / "sanctum"
    now = time.time()
    os.utime(sanctum / "a.json", (now - 3600, now - 3600))  # 1h old
    os.utime(sanctum / "b.json", (now - 60, now - 60))       # 1m old
    os.utime(sanctum / "c.md", (now - 5, now - 5))           # 5s old
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["sanctum"])
    lines = [l for l in res.output.splitlines() if l.startswith("  ")]
    # c.md (5s) appears first
    assert "c.md" in lines[0]
    assert "a.json" in lines[-1]


def test_inbox_of_limit_arg(fake_inboxes):
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["sanctum", "2"])
    assert "2 of 3" in res.output


def test_inbox_of_invalid_limit_returns_error(fake_inboxes):
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["sanctum", "not-a-number"])
    assert "must be an integer" in res.output


def test_inbox_of_missing_dir(tmp_path):
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "INBOX_DIR", tmp_path / "nope"):
        res = cmd_mod.cmd_inbox_of([])
    assert "no inbox dir" in res.output


def test_inbox_of_md_title_extracted(fake_inboxes):
    """Markdown files use first heading as snippet."""
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["sanctum"])
    # c.md has "# title-c-md" heading
    assert "title-c-md" in res.output


def test_inbox_of_json_title_alias(fake_inboxes):
    """JSON files can use 'title' instead of 'subject'."""
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["eve-exe"])
    assert "title-key-d" in res.output


def test_inbox_of_alias_io_dispatch(fake_inboxes):
    from term.commands import dispatch
    res = dispatch("/io sanctum 1")
    assert res.handled is True
    assert "1 of 3" in res.output


def test_inbox_of_dispatch_via_slash(fake_inboxes):
    from term.commands import dispatch
    res = dispatch("/inbox-of")
    assert res.handled is True
    assert "3 agents" in res.output


def test_inbox_of_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/inbox-of" in res.output


def test_inbox_of_case_insensitive(fake_inboxes):
    from term.commands import cmd_inbox_of
    res = cmd_inbox_of(["SANCTUM"])
    assert "Inbox-of sanctum" in res.output
