# Author: RKOJ-ELENO :: 2026-05-25
"""Recall quality benchmark (iter-25 contradict-followup).

Iter-22 contradict-list item #1: "RRF+IDF improves recall quality" was only
manually verified on 1 query. This test ships a 10-query gold set + asserts
RRF >= BM25 on >=70% of queries by a structural relevance check:

  For each (query, expected_path_substring) pair, both BM25-only and RRF
  return the top-K hits. A query "passes" for a mode if any of the top-K
  hits contains the expected substring in its path. RRF must pass at least
  as often as BM25.

This is a smoke-level benchmark (10 queries, not 1000). Real quality
evaluation needs human-labeled relevance judgments. But it's enough to
catch regressions where RRF starts performing WORSE than BM25.

Tested against the live Sanctum FTS5 corpus -- skipped if not present.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# Gold set: (query, expected_substring_in_top_K_hit_path)
# All queries should have at least one expected hit in the live Sanctum corpus.
GOLD = [
    ("loop relentless pursuit", "loop-relentless-pursuit-doctrine"),
    ("memory restore path bug", "sinister-memory-path-bug-and-restore"),
    # iter-26 fix: real PROGRESS file is "Sinister Kernel APK.md" (spaces + CamelCase),
    # not "kernel-apk". iter-25 gold set had this wrong -- test was buggy not recall.
    ("kernel apk frida", "Kernel APK"),
    ("snap-emu pure-api", "snap-emu"),
    ("contradiction gate", "sinister-memory"),  # iter-3 P11/P12 lives in sinister-memory
    ("audit systemic gaps", "sinister-memory-audit-systemic-gaps"),
    ("save adoption doctrine", "save-adoption"),
    ("sanctum scope discipline", "sanctum-scope-discipline"),
    ("no gate questions", "no-gate-questions"),
    ("automate everything operator", "automate-everything-no-operator-admin"),
]

K = 5  # top-K to consider for "found"


def _query_passes(hits: list, expected_substring: str) -> bool:
    """A query passes if ANY of the top-K hit paths OR slugs contains the
    expected substring. Iter-26 fix: also check slug -- otherwise a path like
    'Sinister Kernel APK.md' (CamelCase + spaces) wouldn't match the test
    fixture 'kernel-apk' even though the slug field has 'sinister-kernel-apk'.
    """
    expected_lower = expected_substring.lower()
    for h in hits[:K]:
        path_lower = (h.path or "").lower()
        slug_lower = (h.slug or "").lower()
        if expected_lower in path_lower or expected_lower in slug_lower:
            return True
    return False


def _live_index_available() -> bool:
    return Path(r"D:\Sinister Sanctum\_shared-memory\sinister-memory\index.db").exists()


@pytest.mark.skipif(not _live_index_available(), reason="live Sanctum index not present")
def test_rrf_beats_or_ties_bm25_on_majority_of_gold_queries() -> None:
    """Iter-22 contradict #1: ship the quantitative benchmark.

    Assert RRF >= BM25 in 'passes' count across the 10-query gold set.
    """
    from sinister_memory import recall
    db = Path(r"D:\Sinister Sanctum\_shared-memory\sinister-memory\index.db")

    bm25_passes = 0
    rrf_passes = 0
    per_query: list[tuple[str, bool, bool]] = []  # (query, bm25_pass, rrf_pass)

    for query, expected in GOLD:
        recall.cache_clear()
        bm25_hits = recall.recall(query, db, limit=K, rrf=False)
        recall.cache_clear()
        rrf_hits = recall.recall(query, db, limit=K, rrf=True)
        bm25_pass = _query_passes(bm25_hits, expected)
        rrf_pass = _query_passes(rrf_hits, expected)
        if bm25_pass:
            bm25_passes += 1
        if rrf_pass:
            rrf_passes += 1
        per_query.append((query, bm25_pass, rrf_pass))

    # Print per-query results for visibility (pytest -s shows it)
    print("\n=== recall@K=5 gold-set comparison ===")
    print(f"{'query':<40} {'bm25':>5} {'rrf':>5}")
    for q, b, r in per_query:
        print(f"{q:<40} {'PASS' if b else 'fail':>5} {'PASS' if r else 'fail':>5}")
    print(f"TOTAL passes: bm25={bm25_passes}/{len(GOLD)}  rrf={rrf_passes}/{len(GOLD)}")

    assert rrf_passes >= bm25_passes, (
        f"REGRESSION: RRF passed {rrf_passes} queries vs BM25 {bm25_passes}; "
        f"RRF must be >= BM25 (RRF is a strict superset by design)"
    )
    # Soft assertion: at least 70% of gold queries should pass under either mode
    # (catches a degraded index / wrong slug naming / etc)
    coverage_ratio = max(bm25_passes, rrf_passes) / len(GOLD)
    assert coverage_ratio >= 0.7, (
        f"Gold-set coverage too low: best mode passed {coverage_ratio:.0%} "
        f"of {len(GOLD)} queries (need >=70%); index may need rebuild"
    )
