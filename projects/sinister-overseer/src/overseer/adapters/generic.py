# Author: RKOJ-ELENO :: 2026-05-24
"""GenericAdapter -- fallback for any project key without a dedicated adapter.

P0 SCAFFOLD per docs/04-per-project-adapters.md "GenericAdapter" section.
Registered under the special key `__generic__` so adapters/__init__.get_adapter
can fall back to it for unknown project keys.

Conservative defaults: 60-min polling, no fixes auto-applied (operator review
required for ALL non-trivial proposals).
"""

from __future__ import annotations

from overseer.adapters import BaseAdapter, register


@register
class GenericAdapter(BaseAdapter):
    PROJECT_KEY = "__generic__"
    POLLING_INTERVAL_SECONDS = 3600  # 60 min -- generic fallback
    COST_CAP_USD = 5.0
    SIGNAL_SOURCES = [
        "heartbeat",
        "log_tail",
        "cost_burn",
        "config_smell",
    ]
    FIX_TEMPLATES = {
        "log_level_tune": {"risk": "low", "desc": "Adjust log verbosity"},
        "polling_self_throttle": {"risk": "low", "desc": "Self-throttle polling cadence"},
        "progress_row_archive": {"risk": "low", "desc": "Archive old PROGRESS rows"},
        "_no_action_default": {"risk": "high", "desc": "Default no-action; escalate to operator"},
    }
    AUTO_APPLY_RULES = {
        "log_level_tune": "low",
        "polling_self_throttle": "low",
        "progress_row_archive": "low",
        "_no_action_default": "high",  # default to operator review when in doubt
    }
    ESCALATION_INBOX = "_shared-memory/inbox/"  # generic; runtime fills <project-key>/

    def collect_signals(self, since_utc: str) -> list[dict]:
        raise NotImplementedError("GenericAdapter.collect_signals is a P2 deliverable")

    def observation_check(self, fix_id: str) -> bool:
        raise NotImplementedError("GenericAdapter.observation_check is a P2 deliverable")
