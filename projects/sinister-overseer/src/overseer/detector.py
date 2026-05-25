# Author: RKOJ-ELENO :: 2026-05-24
"""Weak-spot detector -- CHEAP TIER (Haiku-4.5).

P0 SCAFFOLD. P1 implements the real Anthropic SDK call with cached prefix.

Contract:
  classify(signal: dict) -> dict
    Input shape (see docs/03-watch-architecture.md):
      {
        "attachment": "<project-key>",
        "signal_type": "<regression|anomaly|stall|drift|smell|cost-burn|doctrine-violation|user-data-signal>",
        "signal_diff": "<text under 2KB>",
        "context_pointer": "<path-or-url>"
      }
    Output shape:
      {
        "classification": "<noise|info|warn|alert|critical>",
        "severity_score": <0-100>,
        "evidence_summary": "<text under 200 chars>",
        "recommended_action": "<ignore|log|triage|escalate>"
      }

  HARD RULE per docs/02-token-efficiency.md: this function MUST use Haiku-4.5
  and ship only the signal_diff in the variable section. The system prompt
  (adapter type, risk-tier table, top-5 lessons) goes in the CACHED prefix.
"""

from __future__ import annotations


def classify(signal: dict) -> dict:
    """P0 stub. Returns a static noise classification for smoke tests."""
    raise NotImplementedError("detector classify() is a P1 deliverable")
