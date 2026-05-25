# Sinister Term :: tests/test_locks_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-59: /locks builtin reads mesh-coordinator lock state.

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
def fake_locks_dir(tmp_path):
    d = tmp_path / "mesh-locks"
    d.mkdir()
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_MESH_LOCKS_DIR", d):
        yield d


def test_locks_empty_dir(fake_locks_dir):
    from term.commands import cmd_locks
    res = cmd_locks([])
    assert res.handled is True
    assert "no active mesh-coordinator locks" in res.output


def test_locks_missing_dir(tmp_path):
    """If the locks dir doesn't exist, return a clear message."""
    missing = tmp_path / "nonexistent-mesh-locks"
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_MESH_LOCKS_DIR", missing):
        res = cmd_mod.cmd_locks([])
    assert "no mesh-locks dir" in res.output


def test_locks_one_lock(fake_locks_dir):
    (fake_locks_dir / "term-app.json").write_text(json.dumps({
        "owner": "sinister-term",
        "path": "projects/sinister-term/source/term/app.py",
        "ttl_seconds": 600,
        "acquired_at_utc": "2026-05-25T20:00:00Z",
    }), encoding="utf-8")
    from term.commands import cmd_locks
    res = cmd_locks([])
    assert "1 active" in res.output
    assert "sinister-term" in res.output
    assert "term/app.py" in res.output
    assert "ttl=600s" in res.output


def test_locks_multiple_sorted_newest_first(fake_locks_dir):
    """Multiple locks should render newest-first."""
    old = fake_locks_dir / "old.json"
    old.write_text(json.dumps({"owner": "old-agent", "path": "x.py"}), encoding="utf-8")
    past = time.time() - 3600
    os.utime(old, (past, past))

    (fake_locks_dir / "new.json").write_text(
        json.dumps({"owner": "new-agent", "path": "y.py"}), encoding="utf-8"
    )

    from term.commands import cmd_locks
    res = cmd_locks([])
    lines = res.output.splitlines()
    # Find owner positions
    new_idx = next(i for i, l in enumerate(lines) if "new-agent" in l)
    old_idx = next(i for i, l in enumerate(lines) if "old-agent" in l)
    assert new_idx < old_idx  # newer first


def test_locks_stale_marker(fake_locks_dir):
    """A lock older than its ttl gets a (stale) tag."""
    stale = fake_locks_dir / "stale.json"
    stale.write_text(json.dumps({
        "owner": "test-agent", "path": "f.py", "ttl_seconds": 10,
    }), encoding="utf-8")
    past = time.time() - 60  # 60s ago, ttl=10s
    os.utime(stale, (past, past))

    from term.commands import cmd_locks
    res = cmd_locks([])
    assert "(stale)" in res.output


def test_locks_fresh_no_stale_marker(fake_locks_dir):
    """A lock within ttl should NOT have (stale)."""
    (fake_locks_dir / "fresh.json").write_text(json.dumps({
        "owner": "test-agent", "path": "f.py", "ttl_seconds": 3600,
    }), encoding="utf-8")
    from term.commands import cmd_locks
    res = cmd_locks([])
    assert "(stale)" not in res.output


def test_locks_handles_corrupt_json(fake_locks_dir):
    """A corrupt JSON file shouldn't crash the listing."""
    (fake_locks_dir / "bad.json").write_text("not json{{{", encoding="utf-8")
    (fake_locks_dir / "good.json").write_text(
        json.dumps({"owner": "good", "path": "g.py"}), encoding="utf-8"
    )
    from term.commands import cmd_locks
    res = cmd_locks([])
    assert "2 active" in res.output
    assert "good" in res.output
    # The bad lock shows ? for owner since data dict is empty
    assert "?" in res.output


def test_locks_accepts_focus_alias(fake_locks_dir):
    """mesh-coordinator might write 'focus' instead of 'path'."""
    (fake_locks_dir / "x.json").write_text(json.dumps({
        "agent": "test", "focus": "projects/sinister-term/CLAUDE.md",
    }), encoding="utf-8")
    from term.commands import cmd_locks
    res = cmd_locks([])
    assert "CLAUDE.md" in res.output
    assert "test" in res.output


def test_locks_truncates_long_paths(fake_locks_dir):
    long_path = "x/" * 100 + "end.py"
    (fake_locks_dir / "x.json").write_text(json.dumps({
        "owner": "a", "path": long_path,
    }), encoding="utf-8")
    from term.commands import cmd_locks
    res = cmd_locks([])
    # Path is truncated with ellipsis at 47 chars
    assert "..." in res.output
    assert long_path not in res.output


def test_locks_age_format_uses_format_duration(fake_locks_dir):
    """Lock file age renders via _format_duration (so we get nicely formatted units)."""
    (fake_locks_dir / "x.json").write_text(json.dumps({
        "owner": "test", "path": "f.py",
    }), encoding="utf-8")
    from term.commands import cmd_locks
    res = cmd_locks([])
    # Output should contain "age=" followed by a duration string
    assert "age=" in res.output


def test_locks_no_ttl_renders_ttl_unknown(fake_locks_dir):
    (fake_locks_dir / "x.json").write_text(json.dumps({
        "owner": "test", "path": "f.py",
        # no ttl_seconds
    }), encoding="utf-8")
    from term.commands import cmd_locks
    res = cmd_locks([])
    assert "ttl=?" in res.output


def test_locks_dispatch_via_slash(fake_locks_dir):
    from term.commands import dispatch
    res = dispatch("/locks")
    assert res.handled is True


def test_locks_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/locks" in res.output
