# Sinister Term :: tests/test_sysinfo_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-74: /sysinfo builtin.

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def clear_env():
    """Snapshot + clear all SINISTER_* + STERM_* + secret env vars so tests
    don't leak between cases."""
    keys = list(os.environ.keys())
    saved = {}
    for k in keys:
        if k.startswith(("SINISTER_", "STERM_")) or k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            saved[k] = os.environ.pop(k)
    yield
    for k, v in saved.items():
        os.environ[k] = v


def test_sysinfo_renders_all_required_rows():
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    assert res.handled is True
    for needle in (
        "sysinfo:",
        "os:",
        "python:",
        "python_exe:",
        "cwd:",
        "sanctum_root:",
        "TERM:",
        "TERM_PROGRAM:",
    ):
        assert needle in res.output, f"missing: {needle!r}"


def test_sysinfo_dispatch_via_slash():
    from term.commands import dispatch
    res = dispatch("/sysinfo")
    assert res.handled is True
    assert "sysinfo:" in res.output


def test_sysinfo_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/sysinfo" in res.output


def test_sysinfo_python_version_renders():
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    line = next(l for l in res.output.splitlines() if "python:" in l)
    # Contains digits + dots
    import re
    assert re.search(r"\d+\.\d+\.\d+", line)


def test_sysinfo_sanctum_root_marker(clear_env):
    """sanctum_root row shows EXISTS or MISSING."""
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    line = next(l for l in res.output.splitlines() if "sanctum_root:" in l)
    assert "EXISTS" in line or "MISSING" in line


def test_sysinfo_unset_env_section_when_no_sinister_vars(clear_env):
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    assert "no SINISTER_* / STERM_* env vars set" in res.output


def test_sysinfo_lists_set_sinister_vars(clear_env):
    os.environ["SINISTER_ASCII"] = "on"
    os.environ["SINISTER_TERM_OVERLAY"] = "on"
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    assert "sterm env (2 set)" in res.output
    assert "SINISTER_ASCII" in res.output
    assert "SINISTER_TERM_OVERLAY" in res.output


def test_sysinfo_truncates_long_env_value(clear_env):
    big = "x" * 200
    os.environ["SINISTER_DEMO_PROJECT"] = big
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    assert big not in res.output
    assert "..." in res.output


def test_sysinfo_secret_present_marker(clear_env):
    os.environ["ANTHROPIC_API_KEY"] = "sk-secret-token-here-NEVER-SHOWN"
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    line = next(l for l in res.output.splitlines() if "ANTHROPIC_API_KEY" in l)
    assert "[present]" in line
    # The actual secret VALUE must NEVER appear in output
    assert "sk-secret-token-here-NEVER-SHOWN" not in res.output


def test_sysinfo_secret_unset_marker(clear_env):
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    line = next(l for l in res.output.splitlines() if "ANTHROPIC_API_KEY" in l)
    assert "[unset]" in line


def test_sysinfo_disk_row_when_sanctum_exists():
    """Real Sanctum exists → disk row appears."""
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    # disk row may not appear if SANCTUM_ROOT doesn't exist; check conditionally
    if "EXISTS" in next(l for l in res.output.splitlines() if "sanctum_root:" in l):
        assert "disk:" in res.output
        # Should show GiB
        assert "GiB" in res.output


def test_sysinfo_term_env_shown(clear_env):
    os.environ["TERM"] = "xterm-256color"
    os.environ["TERM_PROGRAM"] = "WindowsTerminal"
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    assert "xterm-256color" in res.output
    assert "WindowsTerminal" in res.output


def test_sysinfo_term_unset_shown(clear_env):
    # No TERM set
    if "TERM" in os.environ:
        del os.environ["TERM"]
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    line = next(l for l in res.output.splitlines() if "TERM:" in l)
    assert "(unset)" in line


def test_sysinfo_os_row_has_platform(clear_env):
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    line = next(l for l in res.output.splitlines() if l.strip().startswith("os:"))
    # OS row should have either "Windows", "Linux", or "Darwin"
    assert any(name in line for name in ("Windows", "Linux", "Darwin"))


def test_sysinfo_cwd_row_is_absolute(clear_env):
    from term.commands import cmd_sysinfo
    res = cmd_sysinfo([])
    line = next(l for l in res.output.splitlines() if "cwd:" in l)
    # Absolute path = starts with / on unix or X:\ on windows
    cwd_str = line.split("cwd:", 1)[1].strip()
    assert cwd_str  # non-empty
    p = Path(cwd_str)
    assert p.is_absolute()
