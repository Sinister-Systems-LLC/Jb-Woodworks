# Sinister Term :: tests/test_ascii_bridge.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# SA-PH6: bridge sinister-ascii into the running sterm via a daemon thread.
# Coverage: env gating, lifecycle idempotence, thread-safety, status.

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Also ensure sinister-ascii is importable for the bridge under test
_ASCII = Path(__file__).resolve().parents[2] / "sinister-ascii" / "source"
if _ASCII.exists() and str(_ASCII) not in sys.path:
    sys.path.insert(0, str(_ASCII))


@pytest.fixture
def clear_env():
    saved = os.environ.get("SINISTER_ASCII")
    os.environ.pop("SINISTER_ASCII", None)
    yield
    if saved is None:
        os.environ.pop("SINISTER_ASCII", None)
    else:
        os.environ["SINISTER_ASCII"] = saved


def test_is_enabled_default_off(clear_env):
    from term.ascii_bridge import is_enabled
    assert is_enabled() is False


def test_is_enabled_accepts_canonical_values(clear_env):
    from term.ascii_bridge import is_enabled
    for v in ("on", "1", "true", "yes", "full", "ON", "True"):
        os.environ["SINISTER_ASCII"] = v
        assert is_enabled() is True, f"{v} should enable"


def test_is_enabled_rejects_non_canonical(clear_env):
    from term.ascii_bridge import is_enabled
    for v in ("off", "0", "false", "no", "", "minimal"):
        os.environ["SINISTER_ASCII"] = v
        assert is_enabled() is False, f"{v} should NOT enable"


def test_start_if_enabled_no_op_when_disabled(clear_env):
    from term.ascii_bridge import start_if_enabled, default_bridge
    assert start_if_enabled() is False
    assert default_bridge().status().running is False


def test_bridge_start_stop_lifecycle(clear_env):
    from term.ascii_bridge import AsciiBridge
    b = AsciiBridge(project_key="sinister-term", refresh_seconds=0.25)
    try:
        ok = b.start()
        assert ok is True
        assert b.status().running is True
        # Idempotent: second start returns True + thread unchanged
        assert b.start() is True
        time.sleep(0.4)
        assert b.status().frames_rendered >= 1
    finally:
        b.stop()
    assert b.status().running is False


def test_bridge_stop_when_not_started_is_safe():
    from term.ascii_bridge import AsciiBridge
    b = AsciiBridge()
    b.stop()  # must not raise
    assert b.status().running is False


def test_bridge_status_fields():
    from term.ascii_bridge import AsciiBridge, BridgeStatus
    b = AsciiBridge(project_key="sinister-mind", refresh_seconds=2.0, corner="bl")
    s = b.status()
    assert isinstance(s, BridgeStatus)
    assert s.project_key == "sinister-mind"
    assert s.refresh_seconds == 2.0
    assert s.running is False
    assert s.frames_rendered == 0


def test_bridge_renders_without_writing_to_real_stdout():
    """Render path must use stdout.write — we capture via patch."""
    from term.ascii_bridge import AsciiBridge
    captured: list[str] = []

    class _FakeStdout:
        def write(self, s):
            captured.append(s)
        def flush(self):
            pass

    b = AsciiBridge(project_key="sinister-term", refresh_seconds=0.2)
    with patch("sys.stdout", _FakeStdout()):
        try:
            b.start()
            # Wait for at least one frame
            deadline = time.monotonic() + 2.0
            while b.status().frames_rendered == 0 and time.monotonic() < deadline:
                time.sleep(0.05)
        finally:
            b.stop()
    assert b.status().frames_rendered >= 1
    # Captured output should contain ANSI cursor save + truecolor + reset
    full = "".join(captured)
    assert "\x1b[s" in full
    assert "\x1b[38;2;" in full
    assert "\x1b[0m" in full
    assert "\x1b[u" in full


def test_default_bridge_singleton():
    from term.ascii_bridge import default_bridge
    a = default_bridge()
    b = default_bridge()
    assert a is b


def test_project_for_current_dir_returns_str():
    from term.ascii_bridge import project_for_current_dir
    key = project_for_current_dir()
    assert isinstance(key, str)
    assert len(key) > 0


def test_corner_validation_falls_back_to_tr():
    """Invalid corner string falls back to top-right."""
    from term.ascii_bridge import AsciiBridge
    b = AsciiBridge(corner="invalid")
    assert b._corner == "tr"


def test_refresh_seconds_floor():
    """refresh_seconds <0.25 is clamped to 0.25 (sanity floor)."""
    from term.ascii_bridge import AsciiBridge
    b = AsciiBridge(refresh_seconds=0.01)
    assert b._refresh == 0.25
