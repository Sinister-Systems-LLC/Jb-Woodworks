# Sinister Term :: tests/test_touch_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-58: /touch builtin manually pulses the sinister-term heartbeat.

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def fake_heartbeat(tmp_path):
    """Point _HEARTBEAT_PATH at a tmp file for this test."""
    hb = tmp_path / "sinister-term.json"
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_HEARTBEAT_PATH", hb):
        yield hb


def test_touch_creates_heartbeat(fake_heartbeat):
    from term.commands import cmd_touch
    res = cmd_touch([])
    assert res.handled is True
    assert fake_heartbeat.exists()
    data = json.loads(fake_heartbeat.read_text(encoding="utf-8"))
    assert data["agent"] == "sinister-term"
    assert data["alive"] is True
    assert data["via"] == "sterm /touch"
    assert "ts_utc" in data
    assert "cwd" in data


def test_touch_with_status_note(fake_heartbeat):
    from term.commands import cmd_touch
    res = cmd_touch(["paused", "waiting", "for", "review"])
    data = json.loads(fake_heartbeat.read_text(encoding="utf-8"))
    assert data["status_note"] == "paused waiting for review"
    assert "status:" in res.output
    assert "paused waiting for review" in res.output


def test_touch_no_note_doesnt_set_status_note(fake_heartbeat):
    from term.commands import cmd_touch
    cmd_touch([])
    data = json.loads(fake_heartbeat.read_text(encoding="utf-8"))
    assert "status_note" not in data


def test_touch_caps_long_note(fake_heartbeat):
    from term.commands import cmd_touch
    big = "x" * 500
    cmd_touch([big])
    data = json.loads(fake_heartbeat.read_text(encoding="utf-8"))
    # Capped at 280 chars
    assert len(data["status_note"]) == 280


def test_touch_preserves_existing_fields(fake_heartbeat):
    """If heartbeat already has mode/branch_intent/etc, /touch keeps them."""
    fake_heartbeat.write_text(json.dumps({
        "agent": "sinister-term",
        "ts_utc": "2026-05-25T00:00:00Z",  # old
        "mode": "loop-dynamic-relentless",
        "branch_intent": "agent/sinister-term/sa-ph4-shipped-2026-05-25",
        "last_shipped": "earlier iter",
    }), encoding="utf-8")
    from term.commands import cmd_touch
    cmd_touch(["pulse"])
    data = json.loads(fake_heartbeat.read_text(encoding="utf-8"))
    # New fields
    assert data["status_note"] == "pulse"
    assert data["ts_utc"] > "2026-05-25T00:00:00Z"
    assert data["via"] == "sterm /touch"
    # Preserved fields
    assert data["mode"] == "loop-dynamic-relentless"
    assert data["branch_intent"] == "agent/sinister-term/sa-ph4-shipped-2026-05-25"
    assert data["last_shipped"] == "earlier iter"


def test_touch_overwrites_corrupt_json(fake_heartbeat):
    """If existing heartbeat is corrupted JSON, /touch writes fresh."""
    fake_heartbeat.write_text("not json at all{{{", encoding="utf-8")
    from term.commands import cmd_touch
    res = cmd_touch([])
    data = json.loads(fake_heartbeat.read_text(encoding="utf-8"))
    assert data["agent"] == "sinister-term"
    # Old garbage gone
    assert "not json" not in fake_heartbeat.read_text(encoding="utf-8")


def test_touch_creates_parent_dir(tmp_path):
    """If the heartbeats dir doesn't exist, /touch creates it."""
    hb = tmp_path / "deep" / "nested" / "dir" / "sinister-term.json"
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_HEARTBEAT_PATH", hb):
        from term.commands import cmd_touch
        cmd_touch([])
    assert hb.exists()


def test_touch_returns_human_readable_output(fake_heartbeat):
    from term.commands import cmd_touch
    res = cmd_touch([])
    assert "heartbeat pulsed:" in res.output
    assert "sinister-term.json" in res.output
    assert "ts_utc:" in res.output
    assert "cwd:" in res.output


def test_touch_dispatch_via_slash(fake_heartbeat):
    from term.commands import dispatch
    res = dispatch("/touch hello world")
    assert res.handled is True
    data = json.loads(fake_heartbeat.read_text(encoding="utf-8"))
    assert data["status_note"] == "hello world"


def test_touch_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/touch" in res.output


def test_touch_failure_returns_friendly_error(tmp_path):
    """If the write fails (e.g. permission denied), return CommandResult with msg."""
    hb = tmp_path / "ro" / "sinister-term.json"
    hb.parent.mkdir()
    # Patch the path + simulate write failure via patch on write_text
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_HEARTBEAT_PATH", hb), \
         patch.object(Path, "write_text", side_effect=OSError("disk full")):
        from term.commands import cmd_touch
        res = cmd_touch([])
    assert "/touch failed:" in res.output
    assert "disk full" in res.output
