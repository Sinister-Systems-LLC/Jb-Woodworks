# Author: RKOJ-ELENO :: 2026-05-24
"""Watch-loop stub for Sinister Overseer.

P0 SCAFFOLD ONLY -- no real loop runs at P0; everything below documents the
contract that P1 will implement.

The real implementation (P1) will:
  1. Read config/attached-projects.json for the attachment.
  2. Look up the adapter from src/overseer/adapters/__init__.py REGISTRY.
  3. Spawn one long-running process per attachment (NOT spawn-per-event).
  4. Per cycle:
       - Check cost cap -> throttle at 80% / suspend at 100%
       - adapter.collect_signals(since=last_poll_utc)
       - Route each signal through detector -> triage -> proposer -> apply gate
       - Write heartbeat every 60s
  5. Respect mesh-coord locks before any shared-file edit.
  6. Honor model-tier routing per docs/02-token-efficiency.md.

See docs/03-watch-architecture.md for the full architecture.
"""

from __future__ import annotations


def run_watch_loop(attachment_key: str) -> int:
    """Placeholder. Returns 0 immediately at P0.

    P1+ will block in an infinite loop with cadence per the adapter.
    """
    raise NotImplementedError("watch-loop is a P1 deliverable; see docs/07-evolution-roadmap.md")
