# Sinister Term :: tests/test_ascii_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-54: /ascii builtin controls the SA-PH6 ascii_bridge from inside
# sterm. Tests mock the default bridge so they don't spawn real daemon
# threads or write OSC sequences to real stdout.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# sinister-ascii on path too (the /ascii list path needs it for live registry)
_ASCII = Path(__file__).resolve().parents[2] / "sinister-ascii" / "source"
if _ASCII.exists() and str(_ASCII) not in sys.path:
    sys.path.insert(0, str(_ASCII))


def _fake_status(*, running=False, project_key="sinister-term",
                 refresh_seconds=1.0, frames_rendered=0,
                 last_intensity=0.0, started_at=None, error=None):
    """Build a fake BridgeStatus-shaped object."""
    from term.ascii_bridge import BridgeStatus
    return BridgeStatus(
        running=running, project_key=project_key,
        refresh_seconds=refresh_seconds, frames_rendered=frames_rendered,
        last_intensity=last_intensity, started_at=started_at, error=error,
    )


@pytest.fixture
def fake_bridge():
    """Mock default_bridge() so tests don't touch real daemon threads."""
    b = MagicMock()
    b.status.return_value = _fake_status()
    with patch("term.ascii_bridge.default_bridge", return_value=b):
        yield b


# ---- no-args ----

def test_ascii_no_args_shows_summary(fake_bridge):
    from term.commands import cmd_ascii
    fake_bridge.status.return_value = _fake_status(running=False)
    res = cmd_ascii([])
    assert res.handled is True
    assert "ascii:" in res.output
    assert "off" in res.output.lower()
    assert "sinister-term" in res.output


def test_ascii_no_args_running(fake_bridge):
    from term.commands import cmd_ascii
    fake_bridge.status.return_value = _fake_status(running=True, frames_rendered=42, last_intensity=0.55)
    res = cmd_ascii([])
    assert "ON" in res.output
    assert "frames=42" in res.output
    assert "0.55" in res.output


# ---- on / off ----

def test_ascii_on_starts_bridge(fake_bridge):
    from term.commands import cmd_ascii
    fake_bridge.start.return_value = True
    fake_bridge.status.return_value = _fake_status(running=True, refresh_seconds=1.0)
    res = cmd_ascii(["on"])
    fake_bridge.start.assert_called_once()
    assert "ON" in res.output
    assert "refresh=1.0s" in res.output


def test_ascii_on_failure_shows_error(fake_bridge):
    from term.commands import cmd_ascii
    fake_bridge.start.return_value = False
    fake_bridge.status.return_value = _fake_status(running=False, error="not importable")
    res = cmd_ascii(["on"])
    assert "failed to start" in res.output
    assert "not importable" in res.output


def test_ascii_off_stops_bridge(fake_bridge):
    from term.commands import cmd_ascii
    res = cmd_ascii(["off"])
    fake_bridge.stop.assert_called_once()
    assert res.output.strip() == "ascii: off"


# ---- status ----

def test_ascii_status_full_dump(fake_bridge):
    from term.commands import cmd_ascii
    fake_bridge.status.return_value = _fake_status(
        running=True, project_key="sinister-mind",
        refresh_seconds=0.5, frames_rendered=99,
        last_intensity=0.123, started_at=1234.0, error=None,
    )
    res = cmd_ascii(["status"])
    for needle in (
        "ascii bridge status",
        "running:        True",
        "project_key:    sinister-mind",
        "refresh_secs:   0.5",
        "frames_rendered:99",
        "last_intensity: 0.123",
        "started_at:     1234.0",
        "error:          (none)",
    ):
        assert needle in res.output, f"missing: {needle!r}"


def test_ascii_status_shows_error_when_present(fake_bridge):
    from term.commands import cmd_ascii
    fake_bridge.status.return_value = _fake_status(
        running=False, error="render failed"
    )
    res = cmd_ascii(["status"])
    assert "error:          render failed" in res.output


# ---- project swap ----

def test_ascii_project_swap_requires_arg(fake_bridge):
    from term.commands import cmd_ascii
    res = cmd_ascii(["project"])
    assert "usage:" in res.output.lower()


def test_ascii_project_swap_success(fake_bridge):
    from term.commands import cmd_ascii
    fake_bridge.set_project.return_value = True
    fake_bridge.status.return_value = _fake_status(
        running=True, project_key="sinister-forge"
    )
    res = cmd_ascii(["project", "sinister-forge"])
    fake_bridge.set_project.assert_called_once_with("sinister-forge")
    assert "project=sinister-forge" in res.output
    assert "running=True" in res.output


def test_ascii_project_swap_failure(fake_bridge):
    from term.commands import cmd_ascii
    fake_bridge.set_project.return_value = False
    fake_bridge.status.return_value = _fake_status(error="bad project key")
    res = cmd_ascii(["project", "bogus"])
    assert "failed to swap" in res.output
    assert "bad project key" in res.output


# ---- list ----

def test_ascii_list_renders_entity_registry(fake_bridge):
    from term.commands import cmd_ascii
    res = cmd_ascii(["list"])
    assert res.handled is True
    # At least the master + sinister-term entries should show
    assert "sinister-sanctum" in res.output
    assert "sinister-term" in res.output
    # Each row mentions a motion kind
    assert "motion=" in res.output


# ---- unknown ----

def test_ascii_unknown_subcommand(fake_bridge):
    from term.commands import cmd_ascii
    res = cmd_ascii(["wat"])
    assert "unknown ascii subcommand" in res.output


# ---- integration ----

def test_ascii_dispatch_via_slash(fake_bridge):
    from term.commands import dispatch
    fake_bridge.status.return_value = _fake_status(running=False)
    res = dispatch("/ascii")
    assert res.handled is True
    assert "ascii:" in res.output


def test_ascii_appears_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/ascii" in res.output


# ---- set_project on the real bridge ----

def test_real_set_project_when_not_running():
    """AsciiBridge.set_project on a stopped bridge updates the key cleanly."""
    from term.ascii_bridge import AsciiBridge
    b = AsciiBridge(project_key="sinister-term")
    assert b.set_project("sinister-mind") is True
    assert b.status().project_key == "sinister-mind"
    assert b.status().running is False


def test_real_set_project_rejects_empty():
    from term.ascii_bridge import AsciiBridge
    b = AsciiBridge(project_key="sinister-term")
    assert b.set_project("") is False
    assert b.set_project(None) is False  # type: ignore[arg-type]
