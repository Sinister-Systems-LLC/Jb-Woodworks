# Sinister Term :: keybindings.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# JSON-driven keybindings (handterm-style). Operator can rebind without
# recompile by editing automations/session-templates/term-keybindings.json.
#
# Action vocabulary:
#   "clear_screen"          - renderer.clear()
#   "submit:<text>"         - replace buffer with <text> and submit it
#   "insert:<text>"         - insert <text> at cursor (no submit)

from __future__ import annotations

import json
from pathlib import Path

from prompt_toolkit.key_binding import KeyBindings

from term.commands import SANCTUM_ROOT


# Term-owned config. Lives under projects/sinister-term/source/ so it
# stays in this lane and the operator can edit it without crossing
# lane lines. The .py file is at term/keybindings.py; the config sits
# one level up next to pyproject.toml.
CONFIG_PATH = Path(__file__).resolve().parent.parent / "term-keybindings.json"


DEFAULT_BINDINGS: dict[str, str] = {
    "c-l":     "clear_screen",
    "c-f":     "submit:/forge",
    "c-n":     "submit:/mind",
    "c-h":     "submit:/heartbeats",
    "c-i":     "submit:/inbox",
    "c-p":     "submit:/projects",
}


def load_bindings() -> dict[str, str]:
    """Merge defaults with user overrides from CONFIG_PATH."""
    out = dict(DEFAULT_BINDINGS)
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            user = data.get("bindings", {})
            if isinstance(user, dict):
                for k, v in user.items():
                    if v is None:
                        out.pop(str(k), None)
                    else:
                        out[str(k)] = str(v)
        except Exception:
            pass
    return out


def _apply_action(event, action: str) -> None:
    if action == "clear_screen":
        event.app.renderer.clear()
        return
    if action.startswith("submit:"):
        text = action[len("submit:"):]
        buf = event.app.current_buffer
        buf.text = text
        buf.validate_and_handle()
        return
    if action.startswith("insert:"):
        event.app.current_buffer.insert_text(action[len("insert:"):])
        return


def build_keybindings() -> KeyBindings:
    kb = KeyBindings()
    for key, action in load_bindings().items():
        # Bind with a default-arg closure to avoid late-binding gotcha
        def _handler(event, _action=action):
            _apply_action(event, _action)
        try:
            kb.add(key)(_handler)
        except Exception:
            # Unknown / malformed key spec - skip rather than crash
            pass
    return kb
