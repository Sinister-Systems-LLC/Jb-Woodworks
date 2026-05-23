# Sinister Term :: test_alias.py
# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later
# RKOJ-ELENO :: 2026-05-23 :: covers /alias roundtrip + /mind probe on dead port

from __future__ import annotations

import json
from pathlib import Path


def test_alias_roundtrip(tmp_path, monkeypatch):
    """Define -> list -> expand -> remove, all hitting the persisted file."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    # Re-import to pick up the patched home
    import importlib
    from term import aliases as alias_mod
    importlib.reload(alias_mod)

    # define
    alias_mod.save_aliases({"ll": "ls -la", "g": "git"})
    persisted = json.loads((fake_home / ".sterm" / "aliases.json").read_text())
    assert persisted == {"ll": "ls -la", "g": "git"}

    # load
    loaded = alias_mod.load_aliases()
    assert loaded["ll"] == "ls -la"

    # expand: first-word substitution
    assert alias_mod.expand_line("ll /tmp", loaded) == "ls -la /tmp"
    assert alias_mod.expand_line("g status", loaded) == "git status"
    # non-alias passes through
    assert alias_mod.expand_line("echo hi", loaded) == "echo hi"
    # slash commands are not expanded
    assert alias_mod.expand_line("/help", loaded) == "/help"

    # remove
    del loaded["ll"]
    alias_mod.save_aliases(loaded)
    assert "ll" not in alias_mod.load_aliases()


def test_mind_probe_unreachable(monkeypatch):
    """/mind on a guaranteed-dead port returns a helpful message, no crash, no browser."""
    monkeypatch.setenv("SINISTER_MIND_HOST", "127.0.0.1")
    monkeypatch.setenv("SINISTER_MIND_PORT", "1")  # port 1 is reserved/unused
    opened: list[str] = []
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url) or True)

    from term import commands
    result = commands.cmd_mind([])
    assert result.handled is True
    assert "not reachable" in result.output
    assert opened == []  # browser must NOT be invoked when probe fails
