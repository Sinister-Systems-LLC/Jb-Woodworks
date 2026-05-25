# Sinister Term :: tests/test_event_bus_wiring.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-52: verify that /recall and /swarm builtins publish events to the
# cmux event_bus so downstream consumers (Feed panel, crash replay) see
# them. We capture published events via a test-local subscriber.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def captured_events():
    """Subscribe to the default bus; collect every published event."""
    from term.event_bus import default_bus
    bus = default_bus()
    seen: list = []
    unsub = bus.add_listener(lambda ev: seen.append(ev))
    yield seen
    unsub()


# ---- /recall ----

def test_recall_publishes_event_with_match_count(tmp_path, captured_events):
    sanctum = tmp_path / "s"
    k = sanctum / "_shared-memory" / "knowledge"
    k.mkdir(parents=True)
    (k / "alpha.md").write_text("# alpha\n\ntoken token\n", encoding="utf-8")
    (k / "beta.md").write_text("# beta\n\nunrelated\n", encoding="utf-8")
    from term import commands as cmd
    with patch.object(cmd, "SANCTUM_ROOT", sanctum):
        cmd.cmd_recall(["token"])
    recall_evts = [e for e in captured_events if e.name == "recall"]
    assert len(recall_evts) >= 1
    ev = recall_evts[-1]
    assert ev.category == "agent"
    assert ev.payload["match_count"] == 1
    assert ev.payload["terms"] == ["token"]
    assert isinstance(ev.payload.get("top_titles"), list)


def test_recall_publishes_event_even_on_no_match(tmp_path, captured_events):
    sanctum = tmp_path / "s2"
    (sanctum / "_shared-memory" / "knowledge").mkdir(parents=True)
    from term import commands as cmd
    with patch.object(cmd, "SANCTUM_ROOT", sanctum):
        cmd.cmd_recall(["nonsensetokenxyz"])
    recall_evts = [e for e in captured_events if e.name == "recall"]
    assert recall_evts[-1].payload["match_count"] == 0


# ---- /swarm ----

def test_swarm_list_publishes_event(captured_events):
    from term import commands as cmd
    with patch("term.swarm.list_agents", return_value=[{"agent": "a", "age_min": 1, "marker": "●", "cwd": "/x"}]):
        cmd.cmd_swarm(["list"])
    evts = [e for e in captured_events if e.name == "swarm_list"]
    assert len(evts) >= 1
    assert evts[-1].payload["agent_count"] == 1
    assert evts[-1].category == "agent"


def test_swarm_spawn_publishes_event_with_exit_code(captured_events):
    from term import commands as cmd
    with patch("term.swarm.spawn", return_value=0):
        cmd.cmd_swarm(["spawn", "sinister-mind"])
    evts = [e for e in captured_events if e.name == "swarm_spawn"]
    assert len(evts) >= 1
    assert evts[-1].payload["project_key"] == "sinister-mind"
    assert evts[-1].payload["exit_code"] == 0


def test_swarm_dm_publishes_event(captured_events):
    from term import commands as cmd
    fake_path = Path("_shared-memory/inbox/sinister-mind/x.json")
    with patch("term.swarm.dm", return_value=fake_path):
        cmd.cmd_swarm(["dm", "sinister-mind", "hello", "world"])
    evts = [e for e in captured_events if e.name == "swarm_dm"]
    assert len(evts) >= 1
    p = evts[-1].payload
    assert p["target"] == "sinister-mind"
    assert p["msg_len"] == len("hello world")
    assert p["delivered"] is True


def test_swarm_dm_publishes_event_on_unknown_target(captured_events):
    from term import commands as cmd
    with patch("term.swarm.dm", return_value=None):
        cmd.cmd_swarm(["dm", "nope", "hi"])
    evts = [e for e in captured_events if e.name == "swarm_dm"]
    assert evts[-1].payload["delivered"] is False


def test_swarm_broadcast_publishes_event(captured_events):
    from term import commands as cmd
    fake_path = Path("_shared-memory/cross-agent/bcast.md")
    with patch("term.swarm.broadcast", return_value=fake_path):
        cmd.cmd_swarm(["broadcast", "the", "fleet", "lives"])
    evts = [e for e in captured_events if e.name == "swarm_broadcast"]
    assert len(evts) >= 1
    p = evts[-1].payload
    assert p["msg_len"] == len("the fleet lives")
    assert "cross-agent/bcast.md" in p["path"] or "cross-agent" in p["path"]


def test_swarm_usage_does_not_publish(captured_events):
    """No subcommand → usage text only; should NOT publish a swarm event."""
    from term import commands as cmd
    before = sum(1 for e in captured_events if e.name.startswith("swarm_"))
    cmd.cmd_swarm([])
    after = sum(1 for e in captured_events if e.name.startswith("swarm_"))
    assert after == before
