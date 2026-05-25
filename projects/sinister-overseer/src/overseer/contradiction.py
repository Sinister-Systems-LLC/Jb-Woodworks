"""contradiction.py -- adversarial self-test engine for Sinister Overseer.

Author: RKOJ-ELENO :: 2026-05-24

Composes with:
    docs/08-contradiction-engine.md  (full doctrine)
    docs/09-unified-improvement-engine.md  (pipeline placement)
    _shared-memory/knowledge/contradiction-engine-doctrine-2026-05-24.md

Purpose:
    Every Overseer-proposed fix is run through this module BEFORE it reaches
    the apply gate. The module asks 3 counter-argument questions, scores the
    answer 0-10 via a cheap-tier (Haiku-4.5) call, and rolls back any fix that
    crosses the threshold (default 6). Periodically the adversarial_cycle()
    function deliberately tries to BREAK already-applied past fixes to find
    regressions / gaps the live watch loop did not catch.

Composes with no-bullshit rule 8 (quality-degradation limits expansion):
    contradiction.py is the rule-8 enforcer at fix granularity -- if a fix's
    counter-argument score is high the fix is held / rolled back BEFORE
    we accumulate downstream technical debt from a wrong fix.

Status: P0 STUB. P2 implements the actual Haiku call + JSON parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data shapes (also referenced by sensors/analyzer.py + watch.py + gate.py).
# Defined here in the lowest-level pure module to avoid circular imports.
# ---------------------------------------------------------------------------

@dataclass
class FixProposal:
    """A fix the Overseer wants to apply.

    Fields:
        fix_id: stable id (e.g. ``fix-2026-05-24T23:55Z-abc123``)
        lane: target lane slug (e.g. ``sinister-chatbot``)
        kind: e.g. ``code-change`` | ``config-tweak`` | ``doctrine-row`` | ``schedule-adjust``
        risk: ``low`` | ``medium`` | ``high``
        diff_summary: human-readable 1-3 lines
        evidence: dict of sensor events that triggered the fix
        proposed_by_tier: ``cheap`` (Haiku) | ``medium`` (Sonnet) | ``high`` (Opus)
    """

    fix_id: str
    lane: str
    kind: str
    risk: str
    diff_summary: str
    evidence: dict[str, Any] = field(default_factory=dict)
    proposed_by_tier: str = "medium"


@dataclass
class Regression:
    """A past-fix gap surfaced by adversarial_cycle()."""

    fix_id: str
    lane: str
    found_at_utc: str
    severity: str  # low | medium | high
    description: str
    suggested_action: str  # rollback | re-reason | add-test | escalate


@dataclass
class Conflict:
    """A cross-project invariant collision."""

    fix_lane: str
    conflicting_lane: str
    invariant: str
    fix_id: str
    severity: str  # low | medium | high


@dataclass
class Lane:
    """Minimal lane reference -- full def lives in adapters/*."""

    slug: str
    invariants: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API (all stubs at P0; real impls land at P2).
# ---------------------------------------------------------------------------

def score_counter_argument(fix_proposal: FixProposal | dict) -> int:
    """Score a fix's counter-argument strength 0-10 (higher = more likely WRONG).

    Asks the cheap-tier model THREE questions:
        (a) What's the strongest argument THIS FIX IS WRONG?
        (b) What edge case does this fix miss?
        (c) What would a hostile reviewer say?

    The model returns a JSON object with ``score`` + ``arguments``. We return
    only the score (the arguments are persisted into the lessons store at the
    caller, NOT here -- keeps this function pure).

    Args:
        fix_proposal: a FixProposal dataclass OR a dict with the same shape.

    Returns:
        int in [0, 10]. 0 = no credible counter-argument; 10 = fix is almost
        certainly wrong. Threshold for rollback is governed by
        :func:`should_rollback`, default 6.

    TODO(P2): wire to cheap-tier client (Haiku-4.5 via OAuth-pooled session).
    """
    # P0 stub: always returns 0 (no counter-argument). Real impl will call Haiku.
    _ = fix_proposal
    return 0


def should_rollback(score: int, threshold: int = 6) -> bool:
    """Whether the counter-argument score warrants a rollback.

    Args:
        score: output of :func:`score_counter_argument`, 0-10.
        threshold: default 6. Tunable per-lane via improvement-recipe.json.

    Returns:
        True if score > threshold.
    """
    return score > threshold


def adversarial_cycle(past_fixes: list[FixProposal | dict]) -> list[Regression]:
    """Quarterly (or operator-triggered) adversarial scan of past fixes.

    For each past fix the Overseer applied successfully, ask the medium-tier
    model: "given the current state of the target lane, has this fix been
    eroded / contradicted by subsequent changes? Does any new evidence make
    this fix wrong in hindsight?" The function returns a list of
    :class:`Regression` rows for any fix flagged.

    Cadence: default quarterly (every 90 days). Also fires on operator
    explicit-go (``overseer adversarial-now``) or on >3 forever-improve
    DEGRADED scores in a single lane.

    Args:
        past_fixes: list of fixes from the lessons store (applied=True only).

    Returns:
        list[Regression]. Empty if no regression found.

    TODO(P2): wire to medium-tier client (Sonnet-4.6) + lessons store query.
    """
    _ = past_fixes
    return []


def cross_project_invariant_check(
    fix: FixProposal | dict, all_lanes: list[Lane]
) -> list[Conflict]:
    """Detect whether ``fix`` violates an invariant of any OTHER attached lane.

    Example: a fix that disables ``ANTHROPIC_API_KEY`` export across the spawn
    pipeline must NOT contradict ``oauth-pivot-max-quota-pooling`` (the api-key
    legacy path is preserved by design). If invariant overlap is detected the
    fix is held until the operator reviews via inbox.

    Args:
        fix: the proposed fix.
        all_lanes: every CURRENTLY-ATTACHED lane (read from
            ``config/attached-projects.json`` status=active rows).

    Returns:
        list[Conflict]. Empty if fix is invariant-safe.

    TODO(P2): implement invariant pattern-match -- each adapter declares its
    invariants in its module; this function aggregates and pattern-matches the
    diff summary + evidence against each invariant string.
    """
    _ = (fix, all_lanes)
    return []


# ---------------------------------------------------------------------------
# Convenience wrappers (used by gate.py + watch.py at P2).
# ---------------------------------------------------------------------------

def run_full_contradiction_check(
    fix: FixProposal | dict, all_lanes: list[Lane], threshold: int = 6
) -> dict[str, Any]:
    """One-shot helper that runs all three checks and returns a verdict dict.

    Returns shape::

        {
          "fix_id": str,
          "counter_arg_score": int,
          "rollback_recommended": bool,
          "cross_project_conflicts": list[Conflict],
          "verdict": "apply" | "hold" | "rollback" | "escalate",
        }

    Verdict precedence (most severe wins):
        1. cross_project_conflicts non-empty -> ``escalate``
        2. rollback_recommended -> ``rollback``
        3. counter_arg_score in 4..6 -> ``hold`` (re-reason at medium tier)
        4. otherwise -> ``apply``
    """
    fix_id = fix.fix_id if isinstance(fix, FixProposal) else fix.get("fix_id", "?")
    score = score_counter_argument(fix)
    rollback = should_rollback(score, threshold)
    conflicts = cross_project_invariant_check(fix, all_lanes)

    if conflicts:
        verdict = "escalate"
    elif rollback:
        verdict = "rollback"
    elif 4 <= score <= threshold:
        verdict = "hold"
    else:
        verdict = "apply"

    return {
        "fix_id": fix_id,
        "counter_arg_score": score,
        "rollback_recommended": rollback,
        "cross_project_conflicts": conflicts,
        "verdict": verdict,
    }
