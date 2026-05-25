# Sinister Term :: tests/test_swarm_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# P2-3 (iter-51): /swarm builtin in commands.py routes to term.swarm.
# Mock the underlying swarm module so we don't actually spawn processes /
# write to real Sanctum dirs.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_swarm_no_args_shows_usage():
    from term.commands import cmd_swarm
    res = cmd_swarm([])
    assert res.handled is True
    assert "usage:" in res.output.lower()
    assert "spawn" in res.output
    assert "list" in res.output
    assert "dm" in res.output
    assert "broadcast" in res.output


def test_swarm_list_empty():
    from term.commands import cmd_swarm
    with patch("term.swarm.list_agents", return_value=[]):
        res = cmd_swarm(["list"])
    assert res.handled is True
    assert "no live agents" in res.output.lower()


def test_swarm_list_renders_agents():
    from term.commands import cmd_swarm
    fake_rows = [
        {"agent": "sinister-sanctum", "age_min": 2, "marker": "●", "cwd": "/x"},
        {"agent": "sinister-term", "age_min": 0, "marker": "●", "cwd": "/y"},
        {"agent": "sinister-mind", "age_min": 99, "marker": "○", "cwd": "/z"},
    ]
    with patch("term.swarm.list_agents", return_value=fake_rows):
        res = cmd_swarm(["list"])
    assert res.handled is True
    assert "3 agents" in res.output
    assert "sinister-sanctum" in res.output
    assert "sinister-term" in res.output
    assert "sinister-mind" in res.output


def test_swarm_spawn_usage_when_no_target():
    from term.commands import cmd_swarm
    res = cmd_swarm(["spawn"])
    assert "usage:" in res.output.lower()


def test_swarm_spawn_success():
    from term.commands import cmd_swarm
    with patch("term.swarm.spawn", return_value=0) as m:
        res = cmd_swarm(["spawn", "sinister-forge"])
    m.assert_called_once_with("sinister-forge")
    assert "spawned:" in res.output


def test_swarm_spawn_failure_shows_exit_code():
    from term.commands import cmd_swarm
    with patch("term.swarm.spawn", return_value=1):
        res = cmd_swarm(["spawn", "bogus"])
    assert "exit 1" in res.output


def test_swarm_dm_usage_when_short_args():
    from term.commands import cmd_swarm
    res = cmd_swarm(["dm", "only-agent"])
    assert "usage:" in res.output.lower()


def test_swarm_dm_routes_to_swarm_module():
    from term.commands import cmd_swarm
    with patch("term.swarm.dm", return_value=Path("_shared-memory/inbox/foo/bar.json")) as m:
        res = cmd_swarm(["dm", "foo", "hello", "there"])
    m.assert_called_once_with("foo", "hello there")
    assert "[DM]" in res.output
    assert "bar.json" in res.output


def test_swarm_dm_unknown_agent():
    from term.commands import cmd_swarm
    with patch("term.swarm.dm", return_value=None):
        res = cmd_swarm(["dm", "nonexistent-agent", "msg"])
    assert "unknown agent inbox" in res.output


def test_swarm_broadcast_usage_when_empty():
    from term.commands import cmd_swarm
    res = cmd_swarm(["broadcast"])
    assert "usage:" in res.output.lower()


def test_swarm_broadcast_routes():
    from term.commands import cmd_swarm
    fake_path = Path("_shared-memory/cross-agent/bcast.md")
    with patch("term.swarm.broadcast", return_value=fake_path) as m:
        res = cmd_swarm(["broadcast", "hello", "fleet"])
    m.assert_called_once_with("hello fleet")
    assert "[BROADCAST]" in res.output
    assert "bcast.md" in res.output


def test_swarm_unknown_subcommand():
    from term.commands import cmd_swarm
    res = cmd_swarm(["nonsense"])
    assert "unknown swarm subcommand" in res.output


def test_swarm_dispatch_via_slash():
    """Dispatch routes /swarm <args> to cmd_swarm."""
    from term.commands import dispatch
    with patch("term.swarm.list_agents", return_value=[]):
        res = dispatch("/swarm list")
    assert res.handled is True
    assert "no live agents" in res.output.lower()


def test_swarm_appears_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/swarm" in res.output
