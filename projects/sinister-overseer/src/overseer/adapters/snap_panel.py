# Author: RKOJ-ELENO :: 2026-05-24
"""SnapPanelAdapter -- for the `sinister-panel` lane (NOT pre-attached at P0).

P0 SCAFFOLD per docs/04-per-project-adapters.md "SnapPanelAdapter" section.
This adapter is REGISTERED but the lane is NOT in config/attached-projects.json
at P0 -- operator must explicitly attach via EVE.exe Overseer menu.

The operator brief named this as a future example:
> "I can plug it into the chatbot ... for sinister snap panel that overseer
>  could detect when a phone has an issue or snap updates and auto solve the
>  issue push the fix or update."

Real implementation land in P2+ once core watch-loop is stable.
"""

from __future__ import annotations

from overseer.adapters import BaseAdapter, register


@register
class SnapPanelAdapter(BaseAdapter):
    PROJECT_KEY = "sinister-panel"
    POLLING_INTERVAL_SECONDS = 600  # 10 min -- panel + phone fleet
    COST_CAP_USD = 5.0
    SIGNAL_SOURCES = [
        "log_tail",
        "process",
        "metric_endpoint",
        "heartbeat",
        "drift",
    ]
    FIX_TEMPLATES = {
        "phone_adb_reverse_restart": {"risk": "low", "desc": "Restart adb-reverse subprocess"},
        "snap_version_selector_remap": {"risk": "medium", "desc": "Update Snap UI selectors after version bump"},
        "snap_apk_re_push": {"risk": "medium", "desc": "Re-install Snap APK on phone"},
        "auto_solve_snap_update": {"risk": "medium", "desc": "Auto-detect + auto-solve Snap update issue"},
        "phone_factory_reset_queue": {"risk": "high", "desc": "Queue factory-reset for operator action"},
    }
    AUTO_APPLY_RULES = {
        "phone_adb_reverse_restart": "low",
        "snap_version_selector_remap": "medium",
        "snap_apk_re_push": "medium",
        "auto_solve_snap_update": "medium",
        "phone_factory_reset_queue": "high",
    }
    ESCALATION_INBOX = "_shared-memory/inbox/sinister-panel/"

    def collect_signals(self, since_utc: str) -> list[dict]:
        raise NotImplementedError("SnapPanelAdapter.collect_signals is a P2+ deliverable")

    def observation_check(self, fix_id: str) -> bool:
        raise NotImplementedError("SnapPanelAdapter.observation_check is a P2+ deliverable")
