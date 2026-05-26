# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: doctor.

Picks ONE concrete remediation from the health snapshot and emits the exact
shell command to fix it. Operator-facing: "what should I run right now?".

Algorithm:
  1. Run health() to get sub-scores.
  2. Find the lowest-scoring sub-score (weighted by its weight -- a 50/15 is
     worse than a 70/25 in absolute lost points, so we sort by lost_points).
  3. Return the fix recipe for that sub-score.

Each sub-score has a hand-written fix recipe in _FIXES below.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


# Iter-27 fix: recipes use {root} placeholder; doctor() substitutes the actual
# root path at runtime so doctor works correctly when SINISTER_SANCTUM_ROOT
# points elsewhere (was previously hardcoded to D:\Sinister Sanctum).
_FIXES: dict[str, tuple[str, str]] = {
    # sub_score_name -> (one-line diagnosis, multi-line fix recipe with {root} placeholder)
    "index_present": (
        "FTS5 index DB is missing or empty.",
        'sinister-memory --root "{root}" index',
    ),
    "embeddings_present": (
        "Embeddings DB is missing, empty, or IDF table not built.",
        'sinister-memory --root "{root}" embed-index',
    ),
    "layer_coverage": (
        "Embeddings DB is missing rows for some FTS5 layers.",
        '# wipe embeddings and rebuild\n'
        'sqlite3 "{root}/_shared-memory/sinister-memory/embeddings.db" "DELETE FROM embeddings"\n'
        'sinister-memory --root "{root}" embed-index',
    ),
    "recall_works": (
        "Test query returned 0 hits. Index may be stale or BM25 sanitizer broken.",
        'sinister-memory --root "{root}" index\n'
        'sinister-memory --root "{root}" recall "loop relentless pursuit" --limit 1',
    ),
    "vector_works": (
        "Vector recall returned 0 hits. Embeddings may be missing or mis-dimensioned.",
        'sinister-memory --root "{root}" embed-index\n'
        'sinister-memory --root "{root}" vector-recall "loop relentless" --limit 1 --threshold 0.05',
    ),
    "rotation_healthy": (
        "PROGRESS or fleet-updates file is oversized.",
        'python projects/sinister-memory/scripts/rotate_progress.py --keep-kb 80\n'
        'python projects/sinister-memory/scripts/rotate_fleet_updates.py --keep 1000 --max-mb 100',
    ),
    "adoption": (
        "Few or no lanes are calling `sinister-memory save` at iter-close.",
        '# delegated to sanctum (spawn-phrase fixture); manual seed for one lane:\n'
        'sinister-memory --root "{root}" save "iter-<N>" "<summary>" --agent <slug> --category preference --confidence 0.9\n'
        '# or read the doctrine + inbox\n'
        'cat "{root}/_shared-memory/knowledge/sinister-memory-save-adoption-doctrine-2026-05-25.md"',
    ),
}


def doctor(root: Path) -> dict:
    """Run health(), pick worst-leverage sub-score, return diagnosis + fix recipe.

    Returns: {
        score, grade, worst_sub, diagnosis, recipe,
        all_sub_scores (full health report for reference)
    }
    """
    from . import health as _h
    report = _h.health(root)
    grade = _h.health_grade(report["score"])
    if report["score"] >= 95:
        return {
            "score": report["score"],
            "grade": grade,
            "worst_sub": None,
            "diagnosis": "Health is excellent. No actionable items above the 95-point threshold.",
            "recipe": "",
            "all_sub_scores": report["sub_scores"],
        }

    # Worst = highest "lost points" = (100 - score) * weight / 100
    worst_name: Optional[str] = None
    worst_lost = -1.0
    for name, sub in report["sub_scores"].items():
        lost = (100.0 - sub["score"]) * sub["weight"] / 100.0
        if lost > worst_lost:
            worst_lost = lost
            worst_name = name

    if worst_name is None:
        return {
            "score": report["score"],
            "grade": grade,
            "worst_sub": None,
            "diagnosis": "No sub-score was identifiable.",
            "recipe": "",
            "all_sub_scores": report["sub_scores"],
        }

    diagnosis, recipe_template = _FIXES.get(worst_name, ("Unknown sub-score.", ""))
    # Iter-27: substitute {root} placeholder so recipe points to the actual
    # Sanctum root (works when SINISTER_SANCTUM_ROOT != D:\Sinister Sanctum).
    recipe = recipe_template.format(root=str(Path(root))) if recipe_template else ""
    return {
        "score": report["score"],
        "grade": grade,
        "worst_sub": worst_name,
        "worst_sub_score": report["sub_scores"][worst_name]["score"],
        "worst_sub_weight": report["sub_scores"][worst_name]["weight"],
        "lost_points": round(worst_lost, 2),
        "diagnosis": diagnosis,
        "recipe": recipe,
        "all_sub_scores": report["sub_scores"],
    }
