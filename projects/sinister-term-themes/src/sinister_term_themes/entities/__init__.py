# Author: RKOJ-ELENO :: 2026-05-25
"""Entity registry.

Each project has a named entity. P0 ships `sanctum`. P1 ships the other 4
(sinister_panel / sinister_os / snap_api_quantum / sinister_sleight).

Each entity module exposes a single function `definition()` that returns a
dict with keys: name, project_key, glyph (list[str]), idle_palette,
high_energy_palette, rule (str), personality (str).
"""

from __future__ import annotations

import importlib
from typing import Callable

# Project-key -> entity-module-name lookup
_REGISTRY: dict[str, str] = {
    "sanctum": "sinister_term_themes.entities.sanctum",
    # P1:
    # "sinister-panel": "sinister_term_themes.entities.sinister_panel",
    # "sinister-os": "sinister_term_themes.entities.sinister_os",
    # "sinister-snap-api-quantum": "sinister_term_themes.entities.snap_api_quantum",
    # "sinister-sleight": "sinister_term_themes.entities.sinister_sleight",
}


def list_keys() -> list[str]:
    """Return all registered project keys."""
    return sorted(_REGISTRY.keys())


def load(project_key: str) -> dict:
    """Load an entity definition by project key. Falls back to sanctum on miss."""
    mod_name = _REGISTRY.get(project_key, _REGISTRY["sanctum"])
    mod = importlib.import_module(mod_name)
    defn_fn: Callable[[], dict] = getattr(mod, "definition")
    return defn_fn()
