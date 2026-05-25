# Author: RKOJ-ELENO :: 2026-05-24
"""Fix proposer -- MEDIUM TIER default; HIGH TIER (Opus-4.7) rate-limited.

P0 SCAFFOLD. Generates a concrete fix proposal from a triage note.

Escalation to Opus-4.7 ONLY IF:
  - multi-file (3+ files)
  - architectural (new abstraction or schema)
  - cross-project transferable pattern
  - daily Opus budget remaining for this attachment

HARD RULE per docs/02-token-efficiency.md: rate-limited to 5 Opus calls/day/attachment.
"""

from __future__ import annotations


def propose(triage_note: dict, attachment_key: str) -> dict:
    """P0 stub."""
    raise NotImplementedError("propose() is a P1 deliverable")
