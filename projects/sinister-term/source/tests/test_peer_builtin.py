# Sinister Term :: tests/test_peer_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-73: /peer reads a peer agent's heartbeat in detail.

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
def fake_hbs(tmp_path):
    d = tmp_path / "heartbeats"
    d.mkdir()
    (d / "sinister-term.json").write_text(json.dumps({
        "agent": "sinister-term", "ts_utc": "2026-05-25T20:00:00Z",
    }), encoding="utf-8")
    (d / "sinister-sanctum.json").write_text(json.dumps({
        "agent": "sinister-sanctum", "ts_utc": "2026-05-25T21:00:00Z",
        "mode": "loop-dynamic-relentless",
        "branch_intent": "agent/sinister-sanctum/iter-77",
        "status_note": "doctrine sweep",
    }), encoding="utf-8")
    (d / "sinister-forge.json").write_text(json.dumps({
        "agent": "sinister-forge", "ts_utc": "2026-05-25T19:00:00Z",
    }), encoding="utf-8")
    (d / "eve-exe.json").write_text(json.dumps({
        "agent": "eve-exe", "ts_utc": "2026-05-25T22:00:00Z",
    }), encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", d):
        yield d


def test_peer_no_args_lists_peers(fake_hbs):
    from term.commands import cmd_peer
    res = cmd_peer([])
    assert res.handled is True
    # 3 peers (excluding self = sinister-term)
    assert "3 other agents" in res.output
    assert "sinister-sanctum" in res.output
    assert "sinister-forge" in res.output
    assert "eve-exe" in res.output
    # Self should NOT appear in the peer list
    lines = [l for l in res.output.splitlines() if not l.startswith("Peers") and not l.startswith("Try")]
    grid_text = " ".join(lines)
    assert "sinister-term" not in grid_text


def test_peer_exact_slug_match(fake_hbs):
    from term.commands import cmd_peer
    res = cmd_peer(["sinister-sanctum"])
    assert "Peer: sinister-sanctum" in res.output
    assert "doctrine sweep" in res.output
    assert "agent/sinister-sanctum/iter-77" in res.output


def test_peer_substring_match_unique(fake_hbs):
    """A substring that matches exactly one peer drills in."""
    from term.commands import cmd_peer
    res = cmd_peer(["sanctum"])
    assert "Peer: sinister-sanctum" in res.output


def test_peer_substring_match_ambiguous(fake_hbs):
    """A substring matching multiple peers returns the candidates list."""
    from term.commands import cmd_peer
    res = cmd_peer(["sinister"])
    # 3 sinister-* heartbeats match
    assert "ambiguous" in res.output
    assert "candidates:" in res.output


def test_peer_no_match(fake_hbs):
    from term.commands import cmd_peer
    res = cmd_peer(["totally-nonexistent"])
    assert "no peer matching" in res.output
    assert "available:" in res.output


def test_peer_missing_dir(tmp_path):
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", tmp_path / "nope"):
        res = cmd_mod.cmd_peer([])
    assert "no heartbeats dir" in res.output


def test_peer_empty_dir(tmp_path):
    d = tmp_path / "hb"
    d.mkdir()
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", d):
        res = cmd_mod.cmd_peer([])
    assert "no peer heartbeats found" in res.output


def test_peer_renders_age(fake_hbs):
    """Header includes age."""
    target = fake_hbs / "sinister-sanctum.json"
    past = time.time() - 90
    os.utime(target, (past, past))
    from term.commands import cmd_peer
    res = cmd_peer(["sinister-sanctum"])
    assert "age" in res.output
    assert "1m 30s" in res.output


def test_peer_renders_preferred_order(fake_hbs):
    from term.commands import cmd_peer
    res = cmd_peer(["sinister-sanctum"])
    lines = [l for l in res.output.splitlines() if ":" in l and l.startswith("  ")]
    agent_idx = next(i for i, l in enumerate(lines) if l.strip().startswith("agent"))
    ts_idx = next(i for i, l in enumerate(lines) if l.strip().startswith("ts_utc"))
    assert agent_idx < ts_idx


def test_peer_corrupt_json(tmp_path):
    d = tmp_path / "hb"
    d.mkdir()
    (d / "bad.json").write_text("not json{{{", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", d):
        res = cmd_mod.cmd_peer(["bad"])
    assert "heartbeat JSON corrupt" in res.output


def test_peer_truncates_long_values(tmp_path):
    d = tmp_path / "hb"
    d.mkdir()
    big = "x" * 500
    (d / "big-agent.json").write_text(json.dumps({
        "agent": "big-agent", "last_shipped": big,
    }), encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", d):
        res = cmd_mod.cmd_peer(["big-agent"])
    assert big not in res.output
    assert "..." in res.output


def test_peer_case_insensitive(fake_hbs):
    from term.commands import cmd_peer
    res = cmd_peer(["SANCTUM"])
    assert "sinister-sanctum" in res.output


def test_peer_dispatch_via_slash(fake_hbs):
    from term.commands import dispatch
    res = dispatch("/peer sinister-sanctum")
    assert res.handled is True
    assert "Peer:" in res.output


def test_peer_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/peer" in res.output


def test_peer_self_listed_only_when_self_alone():
    """If sinister-term is the ONLY heartbeat, the peer list says 0."""
    from term import commands as cmd_mod
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "hb"
        d.mkdir()
        (d / "sinister-term.json").write_text(json.dumps({"agent": "sinister-term"}), encoding="utf-8")
        with patch.object(cmd_mod, "HEARTBEATS_DIR", d):
            res = cmd_mod.cmd_peer([])
    assert "0 other agents" in res.output
