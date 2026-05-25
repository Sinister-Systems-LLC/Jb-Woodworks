# Sinister Term :: tests/test_keybindings.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# PH14 (restored 2026-05-25): pytest coverage for term.keybindings — JSON-driven
# rebinding (handterm-philosophy: operator rebinds without recompile).

from __future__ import annotations

import json
from pathlib import Path


def test_default_bindings_canonical():
    """Default table contains the canonical 6 sinister shortcuts."""
    from term.keybindings import DEFAULT_BINDINGS
    for k in ("c-l", "c-f", "c-n", "c-h", "c-i", "c-p"):
        assert k in DEFAULT_BINDINGS, f"missing default binding {k}"
    assert DEFAULT_BINDINGS["c-l"] == "clear_screen"
    assert DEFAULT_BINDINGS["c-f"] == "submit:/forge"
    assert DEFAULT_BINDINGS["c-n"] == "submit:/mind"


def test_load_bindings_no_config_returns_defaults(tmp_path, monkeypatch):
    """When term-keybindings.json is absent, load returns defaults verbatim."""
    from term import keybindings as kb
    monkeypatch.setattr(kb, "CONFIG_PATH", tmp_path / "nope.json")
    out = kb.load_bindings()
    assert out == kb.DEFAULT_BINDINGS


def test_load_bindings_user_override_merges(tmp_path, monkeypatch):
    """User bindings override defaults; new keys are added."""
    from term import keybindings as kb
    cfg = tmp_path / "term-keybindings.json"
    cfg.write_text(json.dumps({
        "bindings": {
            "c-f": "submit:/forge --status",   # override
            "c-x": "submit:/inbox 1",           # new
        }
    }), encoding="utf-8")
    monkeypatch.setattr(kb, "CONFIG_PATH", cfg)
    out = kb.load_bindings()
    assert out["c-f"] == "submit:/forge --status"
    assert out["c-x"] == "submit:/inbox 1"
    # Other defaults still present
    assert out["c-l"] == "clear_screen"


def test_load_bindings_null_value_removes_default(tmp_path, monkeypatch):
    """Setting a default key to null in the user config DELETES that binding."""
    from term import keybindings as kb
    cfg = tmp_path / "term-keybindings.json"
    cfg.write_text(json.dumps({"bindings": {"c-l": None}}), encoding="utf-8")
    monkeypatch.setattr(kb, "CONFIG_PATH", cfg)
    out = kb.load_bindings()
    assert "c-l" not in out


def test_load_bindings_invalid_json_returns_defaults(tmp_path, monkeypatch):
    """Malformed JSON falls back to defaults (must NOT crash)."""
    from term import keybindings as kb
    cfg = tmp_path / "term-keybindings.json"
    cfg.write_text("not json {{{", encoding="utf-8")
    monkeypatch.setattr(kb, "CONFIG_PATH", cfg)
    out = kb.load_bindings()
    assert out == kb.DEFAULT_BINDINGS


def test_load_bindings_non_dict_user_payload_ignored(tmp_path, monkeypatch):
    """If user payload bindings field is not a dict, ignore it (defaults stand)."""
    from term import keybindings as kb
    cfg = tmp_path / "term-keybindings.json"
    cfg.write_text(json.dumps({"bindings": ["c-f", "c-l"]}), encoding="utf-8")
    monkeypatch.setattr(kb, "CONFIG_PATH", cfg)
    out = kb.load_bindings()
    assert out == kb.DEFAULT_BINDINGS


def test_build_keybindings_returns_keybindings_instance():
    """build_keybindings() returns a prompt_toolkit KeyBindings instance."""
    from prompt_toolkit.key_binding import KeyBindings
    from term.keybindings import build_keybindings
    kb = build_keybindings()
    assert isinstance(kb, KeyBindings)


def test_build_keybindings_handles_bad_key_spec(tmp_path, monkeypatch):
    """A malformed key spec is skipped (try/except wraps kb.add) — must not raise."""
    from term import keybindings as kb
    cfg = tmp_path / "term-keybindings.json"
    cfg.write_text(json.dumps({
        "bindings": {"this-is-not-a-real-key": "submit:/help"}
    }), encoding="utf-8")
    monkeypatch.setattr(kb, "CONFIG_PATH", cfg)
    # Must not raise
    out = kb.build_keybindings()
    # And still produces a KeyBindings instance
    from prompt_toolkit.key_binding import KeyBindings
    assert isinstance(out, KeyBindings)
