# Author: RKOJ-ELENO :: 2026-05-24
"""Apply gate -- routes proposals to auto-apply vs operator-review.

P0 SCAFFOLD. Risk-tier classification (BINDING per docs/03-watch-architecture.md):

  TRIVIAL  -> auto-apply
  LOW      -> auto-apply after 5min observation
  MEDIUM   -> 4-hour operator-review window then auto-apply
  HIGH     -> operator inbox row REQUIRED, NEVER auto-applies
  CRITICAL -> operator inbox + "GO" signature REQUIRED

Every apply:
  1. Locks target file(s) via mesh-coord.
  2. Snapshots current state (reversibility plan).
  3. Writes diff.
  4. Releases lock.
  5. Triggers post-apply observation_check.
  6. On observation failure: AUTO-REVERT + write lessons row + fleet-update notice.
"""

from __future__ import annotations


def classify_risk(proposal: dict, attachment_key: str) -> str:
    """Return one of: trivial | low | medium | high | critical."""
    raise NotImplementedError("classify_risk() is a P1 deliverable")


def apply_if_allowed(proposal: dict, attachment_key: str) -> dict:
    """P0 stub. P1 implements lock + snapshot + diff + observe + revert-on-fail."""
    raise NotImplementedError("apply_if_allowed() is a P1 deliverable")
