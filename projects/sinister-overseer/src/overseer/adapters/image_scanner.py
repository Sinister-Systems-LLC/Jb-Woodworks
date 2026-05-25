# Author: RKOJ-ELENO :: 2026-05-24
"""ImageScannerAdapter -- for the `eve-compliance` lane.

P0 SCAFFOLD per docs/04-per-project-adapters.md "ImageScannerAdapter" section.
Real collect_signals + observation_check land in P2.
"""

from __future__ import annotations

from overseer.adapters import BaseAdapter, register


@register
class ImageScannerAdapter(BaseAdapter):
    PROJECT_KEY = "eve-compliance"
    POLLING_INTERVAL_SECONDS = 1800  # 30 min -- file-based lane
    COST_CAP_USD = 5.0
    SIGNAL_SOURCES = [
        "metric_endpoint",
        "user_data",
        "log_tail",
        "drift",
        "config_smell",
        "cost_burn",
    ]
    FIX_TEMPLATES = {
        "threshold_tune": {"risk": "low", "desc": "Adjust per-agency moderation threshold"},
        "prompt_template_tune": {"risk": "medium", "desc": "Tune vision-model prompt"},
        "agency_override_add": {"risk": "medium", "desc": "Add per-agency override rule"},
        "provider_swap_vision": {"risk": "high", "desc": "Swap vision provider (cost + accuracy impact)"},
        "ncmec_report_auto_draft_enable": {"risk": "critical", "desc": "Enable NCMEC auto-draft on CSAM (regulatory)"},
        "ncii_takedown_route_enable": {"risk": "critical", "desc": "Enable NCII takedown route (regulatory)"},
    }
    AUTO_APPLY_RULES = {
        "threshold_tune": "low",
        "prompt_template_tune": "medium",
        "agency_override_add": "medium",
        "provider_swap_vision": "high",
        "ncmec_report_auto_draft_enable": "critical",
        "ncii_takedown_route_enable": "critical",
    }
    ESCALATION_INBOX = "_shared-memory/inbox/eve-compliance/"

    def collect_signals(self, since_utc: str) -> list[dict]:
        raise NotImplementedError("ImageScannerAdapter.collect_signals is a P2 deliverable")

    def observation_check(self, fix_id: str) -> bool:
        raise NotImplementedError("ImageScannerAdapter.observation_check is a P2 deliverable")
