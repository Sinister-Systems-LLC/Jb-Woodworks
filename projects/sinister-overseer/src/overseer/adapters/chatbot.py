# Author: RKOJ-ELENO :: 2026-05-24
"""ChatbotAdapter -- for the `sinister-chatbot` lane.

P0 SCAFFOLD per docs/04-per-project-adapters.md "ChatbotAdapter" section.
Real collect_signals + observation_check land in P2.
"""

from __future__ import annotations

from overseer.adapters import BaseAdapter, register


@register
class ChatbotAdapter(BaseAdapter):
    PROJECT_KEY = "sinister-chatbot"
    POLLING_INTERVAL_SECONDS = 300  # 5 min -- chat lane
    COST_CAP_USD = 5.0
    SIGNAL_SOURCES = [
        "log_tail",
        "metric_endpoint",
        "user_data",
        "config_smell",
        "cost_burn",
    ]
    FIX_TEMPLATES = {
        "route_provider_pin": {"risk": "low", "desc": "Pin OpenRouter provider for stability"},
        "route_model_swap": {"risk": "low", "desc": "Swap to backup model"},
        "retry_budget_bump": {"risk": "low", "desc": "Increase retry budget"},
        "prompt_template_tune": {"risk": "medium", "desc": "Refine system prompt"},
        "nsfw_route_guardrail_tighten": {"risk": "medium", "desc": "Tighten NSFW routing"},
        "per_fan_memory_policy_change": {"risk": "high", "desc": "Adjust per-fan memory policy"},
        "train_ml_feedback_replay": {"risk": "high", "desc": "Replay ML feedback for retrain"},
    }
    AUTO_APPLY_RULES = {
        "route_provider_pin": "low",
        "route_model_swap": "low",
        "retry_budget_bump": "low",
        "prompt_template_tune": "medium",
        "nsfw_route_guardrail_tighten": "medium",
        "per_fan_memory_policy_change": "high",
        "train_ml_feedback_replay": "high",
    }
    ESCALATION_INBOX = "_shared-memory/inbox/sinister-chatbot/"

    def collect_signals(self, since_utc: str) -> list[dict]:
        raise NotImplementedError("ChatbotAdapter.collect_signals is a P2 deliverable")

    def observation_check(self, fix_id: str) -> bool:
        raise NotImplementedError("ChatbotAdapter.observation_check is a P2 deliverable")
