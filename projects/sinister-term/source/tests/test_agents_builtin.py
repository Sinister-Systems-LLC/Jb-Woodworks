# Sinister Term :: tests/test_agents_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-62: /agents richer heartbeats view (mode + branch_intent + status_note).

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
def fake_heartbeats(tmp_path):
    """Build a tmp heartbeats dir with several agents at varied freshness."""
    d = tmp_path / "heartbeats"
    d.mkdir()
    rows = [
        ("sinister-sanctum",
         {"agent": "sinister-sanctum", "mode": "loop-dynamic-relentless",
          "branch_intent": "agent/sinister-sanctum/iter-77",
          "status_note": "doctrine sweep"},
         0),  # fresh
        ("sinister-term",
         {"agent": "sinister-term", "mode": "loop-dynamic-relentless",
          "branch_intent": "agent/sinister-term/sa-ph4-shipped-2026-05-25",
          "status_note": "shipping iter-62"},
         5),  # fresh
        ("sinister-forge",
         {"agent": "sinister-forge", "mode": "active",
          "branch_intent": "agent/sinister-forge/r3"},
         45),  # stale (>30m)
        ("sinister-mind",
         {"agent": "sinister-mind", "mode": "paused"},
         60),  # stale
        ("eve-exe",
         {"agent": "eve-exe", "branch_intent": "agent/eve-exe/wizard"},
         1),  # fresh
    ]
    now = time.time()
    for stem, payload, age_min in rows:
        p = d / f"{stem}.json"
        p.write_text(json.dumps(payload), encoding="utf-8")
        past = now - (age_min * 60)
        os.utime(p, (past, past))
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", d):
        yield d


def test_agents_default_lists_all(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents([])
    assert res.handled is True
    assert "Agents: 5 of 5" in res.output
    assert "fresh<30m=3" in res.output
    assert "stale=2" in res.output


def test_agents_newest_first(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents([])
    lines = [l for l in res.output.splitlines() if l.strip().startswith(("●", "○"))]
    # sinister-sanctum (0m) appears before sinister-mind (60m)
    sanctum_idx = next(i for i, l in enumerate(lines) if "sinister-sanctum" in l)
    mind_idx = next(i for i, l in enumerate(lines) if "sinister-mind" in l)
    assert sanctum_idx < mind_idx


def test_agents_fresh_marker(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents([])
    # Fresh agents marked ●, stale ○
    sanctum_line = next(l for l in res.output.splitlines() if "sinister-sanctum" in l)
    forge_line = next(l for l in res.output.splitlines() if "sinister-forge" in l)
    assert "●" in sanctum_line
    assert "○" in forge_line


def test_agents_fresh_filter(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents(["--fresh"])
    # 3 fresh
    assert "3 of 3" in res.output
    assert "sinister-forge" not in res.output
    assert "sinister-mind" not in res.output


def test_agents_stale_filter(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents(["--stale"])
    # 2 stale
    assert "2 of 2" in res.output
    assert "sinister-forge" in res.output
    assert "sinister-mind" in res.output
    assert "sinister-sanctum" not in res.output


def test_agents_slug_filter(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents(["--slug", "sinister"])
    # All except eve-exe
    assert "4 of 4" in res.output
    assert "eve-exe" not in res.output


def test_agents_limit(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents(["2"])
    assert "2 of 5" in res.output


def test_agents_shows_mode_field(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents([])
    assert "loop-dynamic-relen" in res.output  # truncated to 18 chars
    assert "paused" in res.output


def test_agents_shows_branch_short(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents([])
    # branch_intent uses tail-after-last-/
    assert "sa-ph4-shipped-2026-05-25" in res.output
    assert "iter-77" in res.output


def test_agents_shows_status_note(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents([])
    assert "doctrine sweep" in res.output
    assert "shipping iter-62" in res.output


def test_agents_missing_dir(tmp_path):
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", tmp_path / "nope"):
        res = cmd_mod.cmd_agents([])
    assert "no heartbeats dir" in res.output


def test_agents_handles_corrupt_json(tmp_path):
    d = tmp_path / "hb"
    d.mkdir()
    (d / "bad.json").write_text("garbage{{{", encoding="utf-8")
    (d / "good.json").write_text(json.dumps({"agent": "good"}), encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "HEARTBEATS_DIR", d):
        res = cmd_mod.cmd_agents([])
    assert "2 of 2" in res.output  # both render
    assert "good" in res.output
    assert "bad" in res.output  # falls back to stem name


def test_agents_no_matches_after_filter(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents(["--slug", "nonexistentslug"])
    assert "no agents" in res.output


def test_agents_unknown_arg(fake_heartbeats):
    from term.commands import cmd_agents
    res = cmd_agents(["--garbage"])
    assert "unknown arg" in res.output.lower()


def test_agents_dispatch_via_slash(fake_heartbeats):
    from term.commands import dispatch
    res = dispatch("/agents --fresh")
    assert res.handled is True
    assert "fresh" in res.output.lower()


def test_agents_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/agents" in res.output


def test_agents_combined_filters(fake_heartbeats):
    """--fresh + --slug compose."""
    from term.commands import cmd_agents
    res = cmd_agents(["--fresh", "--slug", "sinister"])
    # 2 fresh sinister-* (sanctum + term); eve-exe is fresh but doesn't match slug
    assert "2 of 2" in res.output
