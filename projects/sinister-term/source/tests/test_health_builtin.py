# Sinister Term :: tests/test_health_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-55: /health builtin renders a single-screen dashboard composed
# from existing helpers. Each row is independently try/except'd so a
# single broken source doesn't take down the whole panel.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_health_returns_dashboard():
    from term.commands import cmd_health
    res = cmd_health([])
    assert res.handled is True
    out = res.output
    # All 7 dashboard rows present
    for row in (
        "Sinister Term health:",
        "version:",
        "git branch:",
        "fleet agents:",
        "inbox:",
        "ascii bridge:",
        "event_bus:",
        "PROGRESS log:",
    ):
        assert row in out, f"missing row: {row!r}"


def test_health_version_includes_sinister_term():
    from term.commands import cmd_health
    res = cmd_health([])
    assert "sinister-term" in res.output


def test_health_handles_missing_heartbeats_dir(tmp_path):
    """If HEARTBEATS_DIR doesn't exist, panel still renders cleanly."""
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", tmp_path / "nonexistent"):
        res = cmd_mod.cmd_health([])
    assert "no heartbeats dir" in res.output


def test_health_counts_heartbeats(tmp_path):
    """Heartbeat rows render fresh/stale split."""
    import time
    hb_dir = tmp_path / "heartbeats"
    hb_dir.mkdir()
    (hb_dir / "fresh-agent.json").write_text("{}", encoding="utf-8")
    # Stale: set mtime to 1 hour ago
    stale = hb_dir / "stale-agent.json"
    stale.write_text("{}", encoding="utf-8")
    old = time.time() - 3600
    import os
    os.utime(stale, (old, old))

    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", hb_dir):
        res = cmd_mod.cmd_health([])
    assert "2 total" in res.output
    assert "1 fresh" in res.output
    assert "1 stale" in res.output


def test_health_counts_inbox(tmp_path):
    """Inbox row shows N unread."""
    inbox = tmp_path / "inbox" / "sinister-term"
    inbox.mkdir(parents=True)
    for i in range(3):
        (inbox / f"msg-{i}.json").write_text("{}", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "INBOX_DIR", tmp_path / "inbox"):
        res = cmd_mod.cmd_health([])
    assert "3 unread" in res.output


def test_health_inbox_zero_when_dir_missing(tmp_path):
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "INBOX_DIR", tmp_path / "nonexistent"):
        res = cmd_mod.cmd_health([])
    assert "0 unread" in res.output


def test_health_ascii_row_renders():
    from term.commands import cmd_health
    res = cmd_health([])
    # ascii row exists regardless of bridge state
    assert "ascii bridge:" in res.output
    assert "project=" in res.output


def test_health_event_bus_seq_renders():
    from term.commands import cmd_health
    res = cmd_health([])
    assert "event_bus:" in res.output
    assert "seq=" in res.output
    assert "ring=" in res.output
    assert "boot=" in res.output


def test_health_progress_row_when_present(tmp_path):
    progress = tmp_path / "Sinister Term.md"
    progress.write_text("# hello\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "PROGRESS_FILE", progress):
        res = cmd_mod.cmd_health([])
    assert "Sinister Term.md" in res.output
    assert "KiB" in res.output


def test_health_progress_row_when_missing(tmp_path):
    missing = tmp_path / "nope.md"
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "PROGRESS_FILE", missing):
        res = cmd_mod.cmd_health([])
    assert "(none" in res.output
    assert "nope.md" in res.output


def test_health_dispatch_via_slash():
    from term.commands import dispatch
    res = dispatch("/health")
    assert res.handled is True
    assert "Sinister Term health" in res.output


def test_health_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/health" in res.output


def test_health_single_broken_source_does_not_break_panel():
    """If one helper raises, only that row shows '?'; others render fine."""
    from term import commands as cmd_mod
    with patch("term.status.git_branch", side_effect=RuntimeError("boom")):
        res = cmd_mod.cmd_health([])
    assert "git branch:     ? (boom)" in res.output
    # Other rows still render
    assert "fleet agents:" in res.output
    assert "event_bus:" in res.output
