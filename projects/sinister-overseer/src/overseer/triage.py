# Author: RKOJ-ELENO :: 2026-05-24
"""Triage stage -- MEDIUM TIER (Sonnet-4.6).

P0 SCAFFOLD. Fires only when detector emits classification >= alert OR
recommended_action in {"triage", "escalate"}.

Contract: produce a structured triage note containing
  - root_cause_hypothesis
  - candidate_fixes (1-3)
  - risk_ranking
  - reversibility_plan

Queries the lessons store BEFORE generating; surfaces prior failures in
context (cached prefix slot).

HARD RULE per docs/02-token-efficiency.md: medium tier, NEVER Opus.
"""

from __future__ import annotations


def triage(signal: dict, classification: dict) -> dict:
    """P0 stub."""
    raise NotImplementedError("triage() is a P1 deliverable")
