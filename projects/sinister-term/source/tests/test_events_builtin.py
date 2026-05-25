# Sinister Term :: tests/test_events_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-53: /events builtin reads the cmux event_bus. We need to use a
# fresh test-only EventBus instance (the default singleton is process-wide
# and may have stale events from other tests).

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def fresh_bus(tmp_path):
    """Build a clean EventBus + patch default_bus() to return it for this test."""
    from term.event_bus import EventBus
    bus = EventBus(tmp_path / "events.jsonl",
                   ring_capacity=64, rotation_threshold=4096)
    with patch("term.event_bus.default_bus", return_value=bus):
        yield bus


def test_events_empty(fresh_bus):
    from term.commands import cmd_events
    res = cmd_events([])
    assert res.handled is True
    assert "no events" in res.output.lower()


def test_events_lists_published(fresh_bus):
    from term.commands import cmd_events
    fresh_bus.publish("alpha", "lifecycle", {"k": 1})
    fresh_bus.publish("beta", "agent", {"k": 2})
    res = cmd_events([])
    assert "alpha" in res.output
    assert "beta" in res.output
    assert "lifecycle" in res.output
    assert "agent" in res.output


def test_events_limit_arg(fresh_bus):
    from term.commands import cmd_events
    for i in range(30):
        fresh_bus.publish(f"e{i}", "lifecycle", {"i": i})
    res = cmd_events(["5"])
    # 1 header + 5 rows
    assert res.output.count("\n") == 5


def test_events_filter_by_cat(fresh_bus):
    from term.commands import cmd_events
    fresh_bus.publish("a", "lifecycle")
    fresh_bus.publish("b", "agent")
    fresh_bus.publish("c", "agent")
    res = cmd_events(["--cat", "agent"])
    assert "a" not in res.output.split("\n")[1:]  # 'a' not in row data
    # 'b' and 'c' should appear
    assert "b " in res.output or "b\n" in res.output
    assert "c " in res.output or "c\n" in res.output
    # lifecycle event should be filtered out
    assert "lifecycle" not in res.output


def test_events_filter_by_name(fresh_bus):
    from term.commands import cmd_events
    fresh_bus.publish("alpha", "agent")
    fresh_bus.publish("beta", "agent")
    res = cmd_events(["--name", "alpha"])
    assert "alpha" in res.output
    assert "beta" not in res.output


def test_events_header_includes_boot_id(fresh_bus):
    from term.commands import cmd_events
    fresh_bus.publish("x", "lifecycle")
    res = cmd_events([])
    # First 8 chars of boot_id appear in header
    assert fresh_bus.boot_id[:8] in res.output


def test_events_unknown_flag_returns_error(fresh_bus):
    from term.commands import cmd_events
    res = cmd_events(["--invalid"])
    assert "unknown arg" in res.output.lower()


def test_events_disk_reads_jsonl(fresh_bus):
    from term.commands import cmd_events
    fresh_bus.publish("disk_a", "lifecycle")
    fresh_bus.publish("disk_b", "lifecycle")
    res = cmd_events(["--disk"])
    assert "disk_a" in res.output
    assert "disk_b" in res.output
    assert "disk" in res.output  # source label


def test_events_appears_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/events" in res.output


def test_events_dispatch_via_slash(fresh_bus):
    from term.commands import dispatch
    fresh_bus.publish("slash_test", "lifecycle")
    res = dispatch("/events")
    assert "slash_test" in res.output


def test_events_renders_payload_keys(fresh_bus):
    from term.commands import cmd_events
    fresh_bus.publish("hello", "agent", {"target": "foo", "msg_len": 11})
    res = cmd_events([])
    assert "target=foo" in res.output
    assert "msg_len=11" in res.output


def test_events_truncates_long_payload_value(fresh_bus):
    from term.commands import cmd_events
    fresh_bus.publish("long", "agent", {"path": "x" * 200})
    res = cmd_events([])
    # Should NOT contain the full 200x — truncated with ...
    assert "x" * 200 not in res.output
    assert "..." in res.output


def test_events_caps_payload_at_4_keys_shown(fresh_bus):
    from term.commands import cmd_events
    fresh_bus.publish("big", "agent",
                      {"k1": 1, "k2": 2, "k3": 3, "k4": 4, "k5": 5, "k6": 6})
    res = cmd_events([])
    assert "k1=1" in res.output
    assert "k4=4" in res.output
    assert "+2" in res.output  # 6 total minus 4 shown = +2
