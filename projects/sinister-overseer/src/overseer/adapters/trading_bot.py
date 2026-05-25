# Author: RKOJ-ELENO :: 2026-05-24
"""TradingBotAdapter -- for the `sinister-sleight` lane.

P0 SCAFFOLD per docs/04-per-project-adapters.md "TradingBotAdapter" section.
Real collect_signals + observation_check land in P1 (first attached project).

NOTE: real-money fix templates (`real_money_enable`) are CRITICAL tier and
NEVER auto-apply -- operator-explicit-go + GO REAL-MONEY signature required
per sinister-sleight CLAUDE.md hard rule 1.
"""

from __future__ import annotations

from overseer.adapters import BaseAdapter, register


@register
class TradingBotAdapter(BaseAdapter):
    PROJECT_KEY = "sinister-sleight"
    POLLING_INTERVAL_SECONDS = 300  # 5 min -- financial surface; latency to detect matters
    COST_CAP_USD = 5.0
    SIGNAL_SOURCES = [
        "metric_endpoint",
        "drift",
        "heartbeat",
        "config_smell",
        "log_tail",
        "process",
        "cost_burn",
    ]
    FIX_TEMPLATES = {
        "polling_cadence_tune": {"risk": "low", "desc": "Adjust paper-trade poll cadence"},
        "risk_cap_re_assert": {"risk": "low", "desc": "Re-write known-good risk caps"},
        "model_retrain_schedule": {"risk": "medium", "desc": "Queue retrain job for drift"},
        "strategy_param_tune": {"risk": "medium", "desc": "Tune strategy parameter JSON"},
        "kill_switch_reassert_on": {"risk": "high", "desc": "Re-assert kill-switch ON (investigate first)"},
        "real_money_kill": {"risk": "high", "desc": "Flip real-money kill-switch ON"},
        "real_money_enable": {"risk": "critical", "desc": "Enable real-money trading (operator-explicit-go required)"},
    }
    AUTO_APPLY_RULES = {
        "polling_cadence_tune": "low",
        "risk_cap_re_assert": "low",
        "model_retrain_schedule": "medium",
        "strategy_param_tune": "medium",
        "kill_switch_reassert_on": "high",
        "real_money_kill": "high",
        "real_money_enable": "critical",
    }
    ESCALATION_INBOX = "_shared-memory/inbox/sinister-sleight/"

    def collect_signals(self, since_utc: str) -> list[dict]:
        raise NotImplementedError("TradingBotAdapter.collect_signals is a P1 deliverable")

    def observation_check(self, fix_id: str) -> bool:
        raise NotImplementedError("TradingBotAdapter.observation_check is a P1 deliverable")
