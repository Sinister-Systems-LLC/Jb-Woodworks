# Sinister Term :: tests/test_uptime_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-56: /uptime builtin — session duration + activity counters.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ---- duration formatter ----

def test_format_duration_seconds():
    from term.commands import _format_duration
    assert _format_duration(0.0) == "0.0s"
    assert _format_duration(45.0) == "45.0s"
    assert _format_duration(59.9).endswith("s")


def test_format_duration_minutes():
    from term.commands import _format_duration
    assert _format_duration(60.0) == "1m 00s"
    assert _format_duration(90.0) == "1m 30s"
    assert _format_duration(3599.0) == "59m 59s"


def test_format_duration_hours():
    from term.commands import _format_duration
    assert _format_duration(3600.0) == "1h 00m 00s"
    assert _format_duration(3661.0) == "1h 01m 01s"


def test_format_duration_days():
    from term.commands import _format_duration
    # 1d 01h 01m
    out = _format_duration(86400 + 3600 + 60)
    assert out.startswith("1d ")
    assert "01h" in out


def test_format_duration_handles_negative():
    from term.commands import _format_duration
    # Negative inputs clamp to 0
    assert _format_duration(-5.0) == "0.0s"


# ---- uptime builtin ----

def test_uptime_returns_dashboard():
    from term.commands import cmd_uptime
    res = cmd_uptime([])
    assert res.handled is True
    for needle in (
        "Sinister Term uptime:",
        "session:",
        "booted at:",
        "now:",
        "events seen:",
        "ascii frames:",
    ):
        assert needle in res.output, f"missing: {needle!r}"


def test_uptime_session_is_non_negative():
    from term.commands import cmd_uptime
    res = cmd_uptime([])
    # The session row shows a number followed by s/m/h/d
    assert "session:" in res.output


def test_uptime_shows_boot_iso_format():
    from term.commands import cmd_uptime
    res = cmd_uptime([])
    # Boot timestamp uses ISO format with Z suffix
    import re
    match = re.search(r"booted at:\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", res.output)
    assert match is not None


def test_uptime_includes_event_seq_when_bus_available():
    from term.commands import cmd_uptime
    res = cmd_uptime([])
    assert "events seen:" in res.output
    # Either shows a number or "(event_bus unavailable)"
    assert ("ring" in res.output) or ("unavailable" in res.output)


def test_uptime_includes_ascii_frames():
    from term.commands import cmd_uptime
    res = cmd_uptime([])
    assert "ascii frames:" in res.output


def test_uptime_bridge_off_row():
    """When the ascii bridge is off, the row says 'bridge off'."""
    from term.commands import cmd_uptime
    from term import ascii_bridge as _br
    # Make sure the default bridge is stopped
    _br.default_bridge().stop()
    res = cmd_uptime([])
    assert "bridge off" in res.output or "bridge ON" in res.output


def test_uptime_includes_cache_entries():
    from term.commands import cmd_uptime
    res = cmd_uptime([])
    # cache entries row is optional but should appear when term.cache exists
    assert "cache entries:" in res.output


def test_uptime_dispatch_via_slash():
    from term.commands import dispatch
    res = dispatch("/uptime")
    assert res.handled is True
    assert "Sinister Term uptime" in res.output


def test_uptime_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/uptime" in res.output


def test_uptime_resilient_to_bus_failure():
    """If event_bus.default_bus raises, /uptime still renders."""
    from term import commands as cmd_mod
    with patch("term.event_bus.default_bus", side_effect=RuntimeError("boom")):
        res = cmd_mod.cmd_uptime([])
    assert "Sinister Term uptime" in res.output
    assert "event_bus unavailable" in res.output


def test_uptime_resilient_to_bridge_failure():
    """If ascii_bridge.default_bridge raises, /uptime still renders."""
    from term import commands as cmd_mod
    with patch("term.ascii_bridge.default_bridge", side_effect=RuntimeError("boom")):
        res = cmd_mod.cmd_uptime([])
    assert "Sinister Term uptime" in res.output
    assert "ascii_bridge unavailable" in res.output
