# Sinister Term :: tests/test_me_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-69: /me shows sinister-term's own heartbeat in detail.

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
def fake_hb(tmp_path):
    hb = tmp_path / "sinister-term.json"
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_HEARTBEAT_PATH", hb):
        yield hb


def test_me_missing_heartbeat(fake_hb):
    from term.commands import cmd_me
    res = cmd_me([])
    assert res.handled is True
    assert "no heartbeat for sinister-term yet" in res.output
    assert "/touch" in res.output  # hint


def test_me_renders_all_known_fields(fake_hb):
    fake_hb.write_text(json.dumps({
        "agent": "sinister-term",
        "ts_utc": "2026-05-25T20:00:00Z",
        "alive": True,
        "mode": "loop-dynamic-relentless",
        "branch_intent": "agent/sinister-term/sa-ph4-shipped-2026-05-25",
        "status_note": "shipping iter-69",
        "last_shipped": "iter-68: /incidents",
        "cwd": "D:/Sinister Sanctum/projects/sinister-term",
        "via": "sterm /touch",
    }), encoding="utf-8")
    from term.commands import cmd_me
    res = cmd_me([])
    for needle in (
        "My heartbeat",
        "agent           : sinister-term",
        "ts_utc          : 2026-05-25T20:00:00Z",
        "alive           : True",
        "mode            : loop-dynamic-relentless",
        "status_note     : shipping iter-69",
    ):
        assert needle in res.output, f"missing: {needle!r}"


def test_me_preferred_field_order(fake_hb):
    """Known fields render in PREFERRED_KEYS order."""
    fake_hb.write_text(json.dumps({
        "cwd": "x",  # later in preferred order
        "agent": "sinister-term",  # first
        "ts_utc": "2026-05-25T00:00:00Z",  # second
    }), encoding="utf-8")
    from term.commands import cmd_me
    res = cmd_me([])
    lines = [l for l in res.output.splitlines() if ":" in l and l.startswith("  ")]
    agent_idx = next(i for i, l in enumerate(lines) if "agent" in l)
    ts_idx = next(i for i, l in enumerate(lines) if "ts_utc" in l)
    cwd_idx = next(i for i, l in enumerate(lines) if "cwd" in l)
    assert agent_idx < ts_idx < cwd_idx


def test_me_includes_unknown_fields(fake_hb):
    """Forward-compat: new fields not in PREFERRED_KEYS still render."""
    fake_hb.write_text(json.dumps({
        "agent": "sinister-term",
        "future_field_xyz": "value-here",
    }), encoding="utf-8")
    from term.commands import cmd_me
    res = cmd_me([])
    assert "future_field_xyz" in res.output


def test_me_renders_age(fake_hb):
    fake_hb.write_text(json.dumps({"agent": "sinister-term"}), encoding="utf-8")
    # Set mtime to 90 seconds ago
    past = time.time() - 90
    os.utime(fake_hb, (past, past))
    from term.commands import cmd_me
    res = cmd_me([])
    # age 90s renders as "1m 30s"
    assert "age" in res.output
    assert "1m 30s" in res.output


def test_me_corrupt_json(fake_hb):
    fake_hb.write_text("not json{{{", encoding="utf-8")
    from term.commands import cmd_me
    res = cmd_me([])
    assert "heartbeat JSON corrupt" in res.output


def test_me_truncates_long_field_values(fake_hb):
    big = "x" * 500
    fake_hb.write_text(json.dumps({
        "agent": "sinister-term", "last_shipped": big,
    }), encoding="utf-8")
    from term.commands import cmd_me
    res = cmd_me([])
    assert big not in res.output
    assert "..." in res.output


def test_me_handles_non_dict_json(fake_hb):
    """If heartbeat JSON is a list / scalar, /me wraps it as raw."""
    fake_hb.write_text(json.dumps(["unexpected", "list"]), encoding="utf-8")
    from term.commands import cmd_me
    res = cmd_me([])
    assert "raw" in res.output


def test_me_dispatch_via_slash(fake_hb):
    fake_hb.write_text(json.dumps({"agent": "sinister-term"}), encoding="utf-8")
    from term.commands import dispatch
    res = dispatch("/me")
    assert res.handled is True
    assert "My heartbeat" in res.output


def test_me_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/me" in res.output


def test_me_composes_with_touch(fake_hb):
    """End-to-end: /touch writes, /me reads it back."""
    from term import commands as cmd_mod
    cmd_mod.cmd_touch(["composing", "with", "touch"])
    res = cmd_mod.cmd_me([])
    assert "composing with touch" in res.output
    assert "sinister-term" in res.output


def test_me_renders_relative_path_header(fake_hb):
    """Header shows the relative path under SANCTUM_ROOT when applicable."""
    fake_hb.write_text(json.dumps({"agent": "sinister-term"}), encoding="utf-8")
    from term.commands import cmd_me
    res = cmd_me([])
    first_line = res.output.splitlines()[0]
    assert "My heartbeat" in first_line
    assert "age" in first_line
