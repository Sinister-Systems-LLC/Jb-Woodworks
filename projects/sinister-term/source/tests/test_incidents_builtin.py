# Sinister Term :: tests/test_incidents_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-68: /incidents reads eve-incidents.jsonl.

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
def fake_incidents(tmp_path):
    jl = tmp_path / "eve-incidents.jsonl"
    rows = [
        {"ts_utc": "2026-05-25T10:00:00Z", "severity": "high",
         "kind": "oauth-slot-empty", "agent": "sanctum",
         "message": "claude-accounts.json empty"},
        {"ts_utc": "2026-05-25T11:00:00Z", "severity": "normal",
         "kind": "watchdog-tripped", "agent": "loop-watchdog",
         "message": "loop stalled >30 min"},
        {"ts_utc": "2026-05-25T12:00:00Z", "severity": "low",
         "kind": "stale-heartbeat", "agent": "sinister-mind",
         "message": "heartbeat 90m stale"},
        # Alias keys: level/type/source/detail
        {"ts_utc": "2026-05-25T13:00:00Z", "level": "critical",
         "type": "spawn-failure", "source": "eve-exe",
         "detail": "mintty failed to launch"},
        {"ts_utc": "2026-05-25T14:00:00Z", "severity": "high",
         "kind": "oauth-slot-empty", "agent": "sanctum",
         "message": "second occurrence"},
    ]
    jl.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_INCIDENTS_PATH", jl):
        yield jl


def test_incidents_default(fake_incidents):
    from term.commands import cmd_incidents
    res = cmd_incidents([])
    assert res.handled is True
    assert "5 of 5" in res.output


def test_incidents_limit(fake_incidents):
    from term.commands import cmd_incidents
    res = cmd_incidents(["2"])
    assert "2 of 5" in res.output


def test_incidents_severity_filter(fake_incidents):
    from term.commands import cmd_incidents
    res = cmd_incidents(["--severity", "high"])
    # 2 high-severity rows
    assert "2 of 2" in res.output
    assert "claude-accounts.json empty" in res.output
    assert "second occurrence" in res.output


def test_incidents_kind_filter(fake_incidents):
    from term.commands import cmd_incidents
    res = cmd_incidents(["--kind", "oauth"])
    # 2 oauth-slot-empty rows
    assert "2 of 2" in res.output


def test_incidents_agent_filter(fake_incidents):
    from term.commands import cmd_incidents
    res = cmd_incidents(["--agent", "sanctum"])
    assert "2 of 2" in res.output
    assert "sinister-mind" not in res.output


def test_incidents_alias_keys(fake_incidents):
    """level/type/source/detail keys are accepted as aliases."""
    from term.commands import cmd_incidents
    res = cmd_incidents(["--severity", "critical"])
    assert "1 of 1" in res.output
    assert "mintty failed" in res.output


def test_incidents_no_match(fake_incidents):
    from term.commands import cmd_incidents
    res = cmd_incidents(["--severity", "nonsense"])
    assert "no incidents" in res.output


def test_incidents_missing_file(tmp_path):
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_INCIDENTS_PATH", tmp_path / "nope.jsonl"):
        res = cmd_mod.cmd_incidents([])
    assert "no incidents log" in res.output


def test_incidents_skips_blank_and_corrupt(tmp_path):
    jl = tmp_path / "x.jsonl"
    jl.write_text(
        json.dumps({"ts_utc": "2026-05-25T00:00:00Z",
                    "severity": "high", "kind": "k", "message": "good"}) + "\n"
        "\n"
        "not json{{{\n"
        + json.dumps({"ts_utc": "2026-05-25T00:00:01Z",
                      "severity": "low", "kind": "k", "message": "also good"}) + "\n",
        encoding="utf-8",
    )
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_INCIDENTS_PATH", jl):
        res = cmd_mod.cmd_incidents([])
    assert "2 of 2" in res.output


def test_incidents_unknown_arg(fake_incidents):
    from term.commands import cmd_incidents
    res = cmd_incidents(["--garbage"])
    assert "unknown arg" in res.output


def test_incidents_severity_badges(fake_incidents):
    from term.commands import cmd_incidents
    res = cmd_incidents([])
    assert "[HI]" in res.output  # high or critical
    assert "[no]" in res.output  # normal
    assert "[lo]" in res.output  # low


def test_incidents_combined_filters(fake_incidents):
    """--severity + --kind compose."""
    from term.commands import cmd_incidents
    res = cmd_incidents(["--severity", "high", "--kind", "oauth"])
    assert "2 of 2" in res.output


def test_incidents_dispatch_via_slash(fake_incidents):
    from term.commands import dispatch
    res = dispatch("/incidents")
    assert res.handled is True


def test_incidents_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/incidents" in res.output


def test_incidents_truncates_long_message(tmp_path):
    jl = tmp_path / "x.jsonl"
    big = "x" * 200
    jl.write_text(json.dumps({
        "ts_utc": "2026-05-25T00:00:00Z", "severity": "high",
        "kind": "k", "message": big,
    }) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_INCIDENTS_PATH", jl):
        res = cmd_mod.cmd_incidents([])
    assert big not in res.output
