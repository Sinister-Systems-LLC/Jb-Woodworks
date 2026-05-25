# Sinister Term :: tests/test_fleet_updates_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-67: /fu (alias /fleet-updates) reads fleet-updates.jsonl.

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
def fake_fu(tmp_path):
    jl = tmp_path / "fleet-updates.jsonl"
    rows = [
        {"id": "fu-001", "ts_utc": "2026-05-25T10:00:00Z",
         "priority": "high", "kind": "delegate",
         "message": "EVE.exe X-button popup",
         "target_slugs": {"eve-exe": True},
         "pushed_by": "sinister-term",
         "acks": ["eve-exe"]},
        {"id": "fu-002", "ts_utc": "2026-05-25T11:00:00Z",
         "priority": "normal", "kind": "doctrine_update",
         "message": "BRAIN new: cmux integration audit",
         "target_slugs": {},
         "pushed_by": "sanctum",
         "acks": []},
        {"id": "fu-003", "ts_utc": "2026-05-25T12:00:00Z",
         "priority": "low", "kind": "status",
         "message": "iter-15 shipped",
         "target_slugs": ["sinister-term", "sanctum"],
         "pushed_by": "sinister-forge",
         "acks": ["sinister-term"]},
        {"id": "fu-004", "ts_utc": "2026-05-25T13:00:00Z",
         "priority": "high", "kind": "delegate",
         "message": "audit cycle started",
         "target_slugs": "sinister-term,sanctum",  # string form
         "pushed_by": "overseer",
         "acks": []},
        {"id": "fu-005", "ts_utc": "2026-05-25T14:00:00Z",
         "priority": "normal", "kind": "doctrine_update",
         "message": "BRAIN: another update",
         "target_slugs": {},
         "pushed_by": "sanctum",
         "acks": []},
    ]
    jl.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_FLEET_UPDATES_PATH", jl):
        yield jl


def test_fu_default_lists_all(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates([])
    assert res.handled is True
    assert "5 of 5" in res.output
    # Last row appears
    assert "BRAIN: another update" in res.output


def test_fu_alias_dispatch(fake_fu):
    from term.commands import dispatch
    res = dispatch("/fu 2")
    assert res.handled is True
    assert "2 of 5" in res.output


def test_fu_full_name_dispatch(fake_fu):
    from term.commands import dispatch
    res = dispatch("/fleet-updates")
    assert res.handled is True


def test_fu_priority_filter(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["--priority", "high"])
    assert "2 of 2" in res.output  # fu-001 + fu-004
    assert "X-button popup" in res.output
    assert "audit cycle" in res.output


def test_fu_kind_filter(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["--kind", "doctrine"])
    # fu-002 + fu-005
    assert "2 of 2" in res.output


def test_fu_mine_filter_via_pushed_by(fake_fu):
    """pushed_by=sinister-term should match --mine."""
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["--mine"])
    # fu-001 (pushed_by=sinister-term) + fu-003 (target list contains sinister-term)
    # + fu-004 (target string contains sinister-term)
    assert "3 of 3" in res.output
    assert "X-button popup" in res.output  # fu-001
    assert "iter-15 shipped" in res.output  # fu-003
    assert "audit cycle" in res.output  # fu-004


def test_fu_unacked_filter(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["--unacked"])
    # Rows where sinister-term NOT in acks: 1, 2, 4, 5 (only 3 has sinister-term in acks)
    assert "4 of 4" in res.output


def test_fu_combined_filters(fake_fu):
    """--priority high AND --unacked compose."""
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["--priority", "high", "--unacked"])
    # fu-001 has acks=[eve-exe], fu-004 has acks=[]
    # both unacked from sterm's POV (sinister-term not in acks)
    assert "2 of 2" in res.output


def test_fu_no_match_message(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["--kind", "nonsense"])
    assert "no fleet-updates" in res.output


def test_fu_missing_file(tmp_path):
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_FLEET_UPDATES_PATH", tmp_path / "nope.jsonl"):
        res = cmd_mod.cmd_fleet_updates([])
    assert "no fleet-updates at" in res.output


def test_fu_skips_blank_and_corrupt_lines(tmp_path):
    jl = tmp_path / "x.jsonl"
    jl.write_text(
        json.dumps({"id": "a", "ts_utc": "2026-05-25T00:00:00Z",
                    "priority": "normal", "kind": "k",
                    "message": "good", "pushed_by": "x"}) + "\n"
        "\n"
        "not json{{{\n"
        + json.dumps({"id": "b", "ts_utc": "2026-05-25T00:00:01Z",
                      "priority": "high", "kind": "k",
                      "message": "also good", "pushed_by": "x"}) + "\n",
        encoding="utf-8",
    )
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_FLEET_UPDATES_PATH", jl):
        res = cmd_mod.cmd_fleet_updates([])
    assert "2 of 2" in res.output


def test_fu_unknown_arg(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["--garbage"])
    assert "unknown arg" in res.output


def test_fu_renders_priority_badges(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates([])
    assert "[HI]" in res.output  # high
    assert "[no]" in res.output  # normal
    assert "[lo]" in res.output  # low


def test_fu_renders_ack_count(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates([])
    assert "(1 ack)" in res.output  # fu-001 has 1 ack


def test_fu_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/fu" in res.output


def test_fu_limit_arg(fake_fu):
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["2"])
    assert "2 of 5" in res.output


def test_fu_truncates_long_message(tmp_path):
    jl = tmp_path / "x.jsonl"
    long_msg = "x" * 200
    jl.write_text(json.dumps({
        "id": "a", "ts_utc": "2026-05-25T00:00:00Z",
        "priority": "normal", "kind": "k",
        "message": long_msg, "pushed_by": "x",
    }) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_FLEET_UPDATES_PATH", jl):
        res = cmd_mod.cmd_fleet_updates([])
    assert long_msg not in res.output  # truncated


def test_fu_target_slugs_dict_match(fake_fu):
    """When target_slugs is a dict, match by key."""
    # fu-001 has target_slugs={"eve-exe": True} — NOT mine
    # But pushed_by=sinister-term so it IS mine
    from term.commands import cmd_fleet_updates
    res = cmd_fleet_updates(["--mine"])
    assert "X-button popup" in res.output  # via pushed_by
