# Sinister Sanctum :: sinister-model :: persisted active-model state
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Persists the currently-selected model to ~/.config/sinister/model.json.

State file shape (schema v1):
    {
        "schema": "sinister.model.state.v1",
        "model_id": "claude-opus-4-7[1m]",
        "provider": "anthropic",
        "set_at": "2026-05-21T14:30:00Z"
    }

Environment override:
    SINISTER_MODEL_STATE_PATH=/custom/path/model.json  (used by tests)

No imports of registry — keep state.py provider-agnostic so registry
edits don't risk corrupting the persistence layer.
"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path

SCHEMA_VERSION = "sinister.model.state.v1"

# Honor XDG_CONFIG_HOME when set, else ~/.config (works on Windows too via
# Path.home()). Override via SINISTER_MODEL_STATE_PATH for tests / portable installs.
def _default_state_path() -> Path:
    override = os.environ.get("SINISTER_MODEL_STATE_PATH")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else (Path.home() / ".config")
    return base / "sinister" / "model.json"


STATE_PATH = _default_state_path()


def state_path() -> Path:
    """Resolve at call-time so env-var overrides take effect after import."""
    return _default_state_path()


def _now_utc_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_current() -> dict | None:
    """Read the persisted active model. Returns None if missing or corrupt."""
    p = state_path()
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if not data.get("model_id"):
        return None
    return data


def set_current(model_id: str, provider: str | None = None) -> dict:
    """Persist the active model. Returns the written state dict."""
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": SCHEMA_VERSION,
        "model_id": model_id,
        "provider": provider,
        "set_at": _now_utc_iso(),
    }
    p.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def clear_current() -> bool:
    """Remove the persisted state. Returns True if a file was removed."""
    p = state_path()
    if p.exists():
        try:
            p.unlink()
            return True
        except OSError:
            return False
    return False
