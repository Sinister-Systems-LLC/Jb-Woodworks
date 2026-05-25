# Sinister Term :: tests/test_utterances_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-60: /utterances builtin tails operator-utterances.jsonl with
# optional filters.

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
def fake_utterances(tmp_path):
    """Build a fake operator-utterances.jsonl with a handful of rows."""
    jl = tmp_path / "operator-utterances.jsonl"
    rows = [
        {"ts_utc": "2026-05-25T10:00:00Z", "session_slug": "sinister-term",
         "preview": "first message from operator", "status": "resolved"},
        {"ts_utc": "2026-05-25T11:00:00Z", "session_slug": "sanctum",
         "preview": "sanctum-targeted directive", "status": "acknowledged"},
        {"ts_utc": "2026-05-25T12:00:00Z", "session_slug": "sinister-term",
         "preview": "looks like shit and laggy", "status": "new"},
        {"ts_utc": "2026-05-25T13:00:00Z", "session_slug": "eve-exe",
         "preview": "eve-exe ask about wizard", "status": "new"},
        {"ts_utc": "2026-05-25T14:00:00Z", "session_slug": "sinister-term",
         "preview": "make the x button popup", "status": "new"},
    ]
    jl.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_UTTERANCES_PATH", jl):
        yield jl


def test_utterances_default_last_10(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances([])
    assert res.handled is True
    # All 5 rows fit under the default 10 limit
    assert "5 of" in res.output
    assert "first message" in res.output
    assert "x button popup" in res.output


def test_utterances_limit_arg(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances(["2"])
    assert "2 of" in res.output
    # Only the last 2 rows (eve-exe + x button)
    assert "x button popup" in res.output
    assert "first message" not in res.output


def test_utterances_only_new(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances(["--new"])
    # 3 status=new rows (rows 3, 4, 5)
    assert "3 of" in res.output
    assert "x button popup" in res.output
    assert "first message" not in res.output  # resolved
    assert "sanctum-targeted" not in res.output  # acknowledged


def test_utterances_only_mine(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances(["--mine"])
    # 3 rows are session_slug=sinister-term
    assert "3 of" in res.output
    assert "first message" in res.output
    assert "x button popup" in res.output
    assert "sanctum-targeted" not in res.output
    assert "eve-exe" not in res.output


def test_utterances_combined_new_and_mine(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances(["--new", "--mine"])
    # Rows 3 + 5 (sterm + new)
    assert "2 of" in res.output
    assert "looks like shit" in res.output
    assert "x button popup" in res.output


def test_utterances_search(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances(["--search", "wizard"])
    assert "1 of" in res.output
    assert "wizard" in res.output


def test_utterances_search_case_insensitive(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances(["--search", "POPUP"])
    assert "popup" in res.output


def test_utterances_search_no_match(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances(["--search", "nonsensetoken"])
    assert "no utterances" in res.output


def test_utterances_missing_file(tmp_path):
    missing = tmp_path / "nonexistent.jsonl"
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_UTTERANCES_PATH", missing):
        res = cmd_mod.cmd_utterances([])
    assert "no operator-utterances.jsonl" in res.output


def test_utterances_skips_blank_and_bad_lines(tmp_path):
    jl = tmp_path / "u.jsonl"
    jl.write_text(
        json.dumps({"ts_utc": "2026-05-25T00:00:00Z",
                    "session_slug": "x", "preview": "good"}) + "\n"
        "\n"  # blank line
        "not valid json{{{\n"
        + json.dumps({"ts_utc": "2026-05-25T00:00:01Z",
                      "session_slug": "y", "preview": "also good"}) + "\n",
        encoding="utf-8",
    )
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_UTTERANCES_PATH", jl):
        res = cmd_mod.cmd_utterances([])
    assert "2 of" in res.output
    assert "good" in res.output
    assert "also good" in res.output


def test_utterances_renders_status_badges(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances([])
    assert "[NEW]" in res.output
    assert "[ack]" in res.output
    assert "[res]" in res.output


def test_utterances_unknown_arg_returns_error(fake_utterances):
    from term.commands import cmd_utterances
    res = cmd_utterances(["--garbage"])
    assert "unknown arg" in res.output.lower()


def test_utterances_alias_utt(fake_utterances):
    """Alias /utt routes to the same handler."""
    from term.commands import dispatch
    res = dispatch("/utt 3")
    assert res.handled is True
    assert "3 of" in res.output


def test_utterances_dispatch_via_slash(fake_utterances):
    from term.commands import dispatch
    res = dispatch("/utterances --mine")
    assert res.handled is True
    assert "sinister-term" in res.output


def test_utterances_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/utterances" in res.output


def test_utterances_caps_preview_at_80(tmp_path):
    """Long preview lines are truncated to 80 chars."""
    long_msg = "x" * 200
    jl = tmp_path / "u.jsonl"
    jl.write_text(json.dumps({
        "ts_utc": "2026-05-25T00:00:00Z", "session_slug": "x",
        "preview": long_msg,
    }) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_UTTERANCES_PATH", jl):
        res = cmd_mod.cmd_utterances([])
    # The 200-char string should NOT appear in full in the output
    assert long_msg not in res.output


def test_utterances_falls_back_to_message_full_when_no_preview(tmp_path):
    jl = tmp_path / "u.jsonl"
    jl.write_text(json.dumps({
        "ts_utc": "2026-05-25T00:00:00Z", "session_slug": "x",
        "message_full": "no preview field, only message_full",
    }) + "\n", encoding="utf-8")
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "_UTTERANCES_PATH", jl):
        res = cmd_mod.cmd_utterances([])
    assert "no preview field" in res.output
