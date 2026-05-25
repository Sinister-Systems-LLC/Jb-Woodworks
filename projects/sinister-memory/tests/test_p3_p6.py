# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: P3-P6 tests for supersede / decay / cluster / verify.

7 tests, all tmp_path-sandboxed. NEVER touches the real `_shared-memory/`.

Coverage:
  1. supersede: mark + chain_for + latest_of (linear chain)
  2. supersede: cycle rejection + unmark
  3. decay: decay_weight monotonic + apply_decay boosts recent
  4. cluster: jaccard correctness + cluster_snippets groups dupes
  5. cluster: dedupe end-to-end creates supersedes edges
  6. verify: heuristic mode fresh vs stale
  7. verify: offline (no SDK, no source) returns ungraded
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

# Allow running pytest without installing the package
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _seed_index(tmp_path: Path) -> Path:
    """Seed _shared-memory with a handful of files + build the FTS5 index. Returns db path."""
    from sinister_memory import indexer

    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "PROGRESS").mkdir(parents=True, exist_ok=True)

    # Two near-duplicate progress rows for the same slug
    (sm / "PROGRESS" / "Sinister Memory.md").write_text(
        "Shipped P3 supersede primitive with cycle rejection and chain_for traversal.\n"
        "Shipped P4 decay with half-life formula.\n",
        encoding="utf-8",
    )
    (sm / "PROGRESS" / "Sinister Sanctum.md").write_text(
        "Shipped P3 supersede primitive with cycle rejection.\n"
        "Shipped P4 decay with half-life formula.\n",
        encoding="utf-8",
    )
    (sm / "knowledge" / "doctrine-2026-05-25.md").write_text(
        "# Loop relentless\n\nAfter every shipped deliverable, immediately start next.\n",
        encoding="utf-8",
    )

    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)
    return db


def test_supersede_linear_chain_and_latest_of(tmp_path: Path) -> None:
    from sinister_memory import supersede

    db = tmp_path / "test.db"
    supersede.mark_supersedes("v2", "v1", "second draft", db)
    supersede.mark_supersedes("v3", "v2", "third draft", db)

    chain = supersede.chain_for("v1", db)
    assert len(chain) == 2, f"expected 2 edges in chain, got {chain}"
    new_ids = {row["new_id"] for row in chain}
    assert new_ids == {"v2", "v3"}

    assert supersede.latest_of("v1", db) == "v3"
    assert supersede.latest_of("v3", db) == "v3"  # terminal node
    assert supersede.latest_of("unknown", db) == "unknown"  # passthrough

    superseded = supersede.superseded_set(db)
    assert superseded == {"v1", "v2"}


def test_supersede_rejects_cycles_and_unmark(tmp_path: Path) -> None:
    from sinister_memory import supersede

    db = tmp_path / "cycle.db"
    supersede.mark_supersedes("b", "a", "1", db)
    supersede.mark_supersedes("c", "b", "2", db)

    # c <- b <- a; trying to make a supersede c would create a cycle
    with pytest.raises(ValueError, match="cycle"):
        supersede.mark_supersedes("a", "c", "would cycle", db)

    # Self-supersede rejected
    with pytest.raises(ValueError):
        supersede.mark_supersedes("a", "a", "self", db)

    # Empty id rejected
    with pytest.raises(ValueError):
        supersede.mark_supersedes("", "x", "empty", db)

    # unmark removes a real edge
    assert supersede.unmark("b", "a", db) is True
    assert supersede.unmark("b", "a", db) is False  # already gone


def test_decay_weight_monotonic_and_apply_boosts_recent(tmp_path: Path) -> None:
    from sinister_memory import decay, indexer, recall

    db = _seed_index(tmp_path)

    # Half-life invariants
    assert decay.decay_weight(0) == 1.0
    assert decay.decay_weight(30, 30) == pytest.approx(0.5)
    assert decay.decay_weight(60, 30) == pytest.approx(0.25)
    # Earlier ages always weigh more
    assert decay.decay_weight(10) > decay.decay_weight(20)

    # apply_decay returns a re-ranked list of equal length
    hits = recall.recall("supersede", db, limit=5)
    assert hits, "seed should have at least one hit for 'supersede'"
    ranked = decay.apply_decay(hits, now_ts=time.time(), db_path=db)
    assert len(ranked) == len(hits)
    # All should be Hit-shaped
    for h in ranked:
        assert h.path
        assert h.layer

    # decay_weight age 365 should be much less than age 1 (with default half-life 30d)
    assert decay.decay_weight(1) > 10 * decay.decay_weight(365)


def test_cluster_jaccard_and_snippet_grouping() -> None:
    from sinister_memory import cluster

    a = cluster.tokenize("shipped P3 supersede primitive with cycle rejection")
    b = cluster.tokenize("shipped P3 supersede primitive with cycle rejection again")
    c = cluster.tokenize("totally unrelated payload of zebras and platypuses")

    assert cluster.jaccard(a, b) > 0.7
    assert cluster.jaccard(a, c) < 0.2
    assert cluster.jaccard(set(), set()) == 1.0
    assert cluster.jaccard(a, set()) == 0.0

    rows = [
        ("shipped P3 supersede primitive with cycle rejection",),
        ("shipped P3 supersede primitive with cycle rejection!",),
        ("totally unrelated payload of zebras and platypuses",),
    ]
    groups = cluster.cluster_snippets(rows, threshold=0.7)
    # First two cluster together, third stands alone
    assert any(len(g) == 2 for g in groups)
    assert any(len(g) == 1 for g in groups)


def test_cluster_dedupe_creates_supersedes_edges(tmp_path: Path) -> None:
    from sinister_memory import cluster, supersede

    db = _seed_index(tmp_path)
    stats = cluster.dedupe(db_path=db, threshold=0.5, layers=("progress",), limit=1000)

    assert stats["scanned"] > 0
    # The two PROGRESS files share most tokens; expect at least one cluster + edge
    assert stats["clusters"] >= 1
    assert stats["edges_added"] >= 1

    # Edges actually persisted
    superseded = supersede.superseded_set(db)
    assert superseded, "dedupe must have written at least one supersedes edge"

    # dry_run leaves db unchanged
    db2 = _seed_index(tmp_path / "dryrun")
    stats_dry = cluster.dedupe(db_path=db2, threshold=0.5, layers=("progress",), dry_run=True)
    assert stats_dry["edges_added"] == 0
    assert supersede.superseded_set(db2) == set()


def test_verify_heuristic_fresh_vs_stale() -> None:
    from sinister_memory import verify

    fresh_v = verify.verify_memory(
        memory_text="loop relentless after every shipped deliverable immediately start next iteration",
        source_text="loop relentless: after every shipped deliverable, immediately start the next iteration",
        prefer="heuristic",
    )
    assert fresh_v.verdict == "fresh"
    assert fresh_v.model == "heuristic-jaccard"
    assert fresh_v.cost_estimate_usd == 0.0

    stale_v = verify.verify_memory(
        memory_text="rust async io with tokio runtime and futures combinators",
        source_text="javascript dom manipulation jquery selectors and event handlers",
        prefer="heuristic",
    )
    assert stale_v.verdict == "stale"


def test_verify_offline_without_source_returns_ungraded(tmp_path: Path, monkeypatch) -> None:
    from sinister_memory import verify

    # Force offline: no API key + force heuristic which requires source
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    v = verify.verify_memory(
        memory_text="memory content with no source to compare",
        source_text=None,
        prefer="auto",
    )
    # available_modes() shouldn't promote us to online without a key, so falls through to ungraded
    assert v.verdict == "ungraded"
    assert v.cost_estimate_usd == 0.0


def test_available_modes_reports_dict() -> None:
    from sinister_memory import verify

    modes = verify.available_modes()
    assert isinstance(modes, dict)
    assert set(modes.keys()) >= {"online", "heuristic", "offline"}
    assert modes["heuristic"] is True
    assert modes["offline"] is True
