# Author: RKOJ-ELENO :: 2026-05-24
"""Adapter registry for Sinister Overseer.

P0 SCAFFOLD -- BaseAdapter declared + per-project stubs registered. Real
implementations (collect_signals + observation_check) ship phase-by-phase
per docs/07-evolution-roadmap.md.

Per-project adapter specs live in docs/04-per-project-adapters.md.

REGISTRY pattern: each adapter module imports `register` from here and applies
the decorator to its class. Adapter modules are imported in REGISTRY_MODULES
below so the decorator fires at import time.
"""

from __future__ import annotations


class BaseAdapter:
    """Base contract every adapter must satisfy.

    Subclasses MUST set:
      - PROJECT_KEY: matches projects.json key
      - SIGNAL_SOURCES: list[str] of source-type names from docs/03-watch-architecture.md
      - FIX_TEMPLATES: dict[str, dict] of pre-canonical fix shapes
      - AUTO_APPLY_RULES: dict[fix_template_id, risk_tier]
      - ESCALATION_INBOX: path string under _shared-memory/inbox/

    Subclasses MAY override:
      - POLLING_INTERVAL_SECONDS (default 1800)
      - COST_CAP_USD (default 5.0)
      - SCHEMA_VERSION (default 1)
    """

    PROJECT_KEY: str = ""
    SCHEMA_VERSION: int = 1
    POLLING_INTERVAL_SECONDS: int = 1800
    COST_CAP_USD: float = 5.0
    SIGNAL_SOURCES: list[str] = []
    FIX_TEMPLATES: dict[str, dict] = {}
    AUTO_APPLY_RULES: dict[str, str] = {}
    ESCALATION_INBOX: str = ""

    def collect_signals(self, since_utc: str) -> list[dict]:
        raise NotImplementedError

    def observation_check(self, fix_id: str) -> bool:
        raise NotImplementedError


REGISTRY: dict[str, type[BaseAdapter]] = {}


def register(cls: type[BaseAdapter]) -> type[BaseAdapter]:
    """Decorator -- registers an adapter class by its PROJECT_KEY."""
    if not cls.PROJECT_KEY:
        raise ValueError(f"Adapter {cls.__name__} missing PROJECT_KEY class attribute")
    REGISTRY[cls.PROJECT_KEY] = cls
    return cls


# Import adapter modules so their @register decorators fire.
# Keep alphabetical for grep stability.
from overseer.adapters import chatbot  # noqa: E402,F401
from overseer.adapters import generic  # noqa: E402,F401
from overseer.adapters import image_scanner  # noqa: E402,F401
from overseer.adapters import snap_panel  # noqa: E402,F401
from overseer.adapters import trading_bot  # noqa: E402,F401


def get_adapter(project_key: str) -> type[BaseAdapter]:
    """Return adapter class for project_key, falling back to GenericAdapter."""
    if project_key in REGISTRY:
        return REGISTRY[project_key]
    return REGISTRY["__generic__"]
