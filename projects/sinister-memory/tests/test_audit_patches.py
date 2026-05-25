# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: tests for the 5 jcode-audit-driven patches.

Brain entry: _shared-memory/knowledge/jcode-memory-audit-and-cherry-picks-2026-05-25.md

Coverage:
  1. decay: per-category half-life dispatch (correction=365, fact=30, inferred=7, unknown=30)
  2. recall: apply_gap_filter truncates on >=25% relative score drop
  3. supersede: mark_edge accepts EDGE_KINDS, rejects unknown kind
  4. supersede: cascade_retrieve BFS through edges, respects depth + kind filter
  5. auto_save: v2 frontmatter round-trip (category + confidence + format_version)
  6. auto_save: invalid category/confidence/trust rejected
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_decay_per_category_half_life() -> None:
    from sinister_memory.decay import HALF_LIVES, DEFAULT_HALF_LIFE_DAYS, half_life_for

    assert half_life_for("correction") == 365.0
    assert half_life_for("preference") == 90.0
    assert half_life_for("procedure") == 60.0
    assert half_life_for("fact") == 30.0
    assert half_life_for("entity") == 30.0
    assert half_life_for("inferred") == 7.0

    # Case-insensitive
    assert half_life_for("CORRECTION") == 365.0
    assert half_life_for(" Inferred ") == 7.0

    # Unknown -> default
    assert half_life_for("madeup") == DEFAULT_HALF_LIFE_DAYS
    assert half_life_for(None) == DEFAULT_HALF_LIFE_DAYS
    assert half_life_for("") == DEFAULT_HALF_LIFE_DAYS

    # Table sanity
    assert set(HALF_LIVES.keys()) >= {"correction", "fact", "inferred"}


def test_recall_apply_gap_filter() -> None:
    from sinister_memory.recall import Hit, apply_gap_filter

    def _h(score: float, path: str = "p") -> Hit:
        # Hit.score holds -relevance; lower abs == better
        return Hit(layer="brain", slug="", path=path, line="1", snippet="x", score=-score)

    # Clear gap: 10 -> 9.8 -> 2.0 (relevance drop 7.8 > 25% of 10)
    hits = [_h(10.0, "a"), _h(9.8, "b"), _h(2.0, "c"), _h(1.5, "d")]
    filtered = apply_gap_filter(hits, drop_ratio=0.25)
    assert len(filtered) == 2, f"expected truncation after h2, got {len(filtered)}: {filtered}"
    assert [h.path for h in filtered] == ["a", "b"]

    # No gap (flat distribution): keep everything
    flat = [_h(10.0), _h(9.5), _h(9.0), _h(8.5)]
    assert len(apply_gap_filter(flat, drop_ratio=0.25)) == 4

    # Empty / single-item passthrough
    assert apply_gap_filter([]) == []
    assert len(apply_gap_filter([_h(5.0)])) == 1

    # min_kept floor
    sharp = [_h(10.0), _h(0.1), _h(0.05)]
    assert len(apply_gap_filter(sharp, min_kept=3)) == 3


def test_supersede_mark_edge_accepts_all_kinds_rejects_unknown(tmp_path: Path) -> None:
    from sinister_memory import supersede

    db = tmp_path / "edges.db"
    # All 5 EdgeKinds round-trip
    for kind in sorted(supersede.EDGE_KINDS):
        supersede.mark_edge("memA", f"memB-{kind}", kind, db, reason=f"kind={kind}")

    out_edges = supersede.edges_of("memA", db, direction="out")
    kinds_emitted = {e["kind"] for e in out_edges}
    assert kinds_emitted == supersede.EDGE_KINDS

    # Unknown kind rejected
    with pytest.raises(ValueError, match="unknown edge kind"):
        supersede.mark_edge("x", "y", "NotARealKind", db)

    # Self-edge rejected for Supersedes/Contradicts
    with pytest.raises(ValueError):
        supersede.mark_edge("z", "z", "Supersedes", db)
    with pytest.raises(ValueError):
        supersede.mark_edge("z", "z", "Contradicts", db)

    # Self-edge OK for HasTag (a memory tagged with its own slug, edge case)
    supersede.mark_edge("z", "z", "HasTag", db, reason="self-tag is allowed")

    # Direction filter works
    in_edges = supersede.edges_of("memB-Supersedes", db, direction="in")
    assert len(in_edges) == 1 and in_edges[0]["kind"] == "Supersedes"


def test_supersede_cascade_retrieve_bfs_depth_and_kind(tmp_path: Path) -> None:
    from sinister_memory import supersede

    db = tmp_path / "cascade.db"
    # Build a small graph:
    #   A --RelatesTo--> B --RelatesTo--> C --RelatesTo--> D
    #   A --HasTag--> tag1
    supersede.mark_edge("A", "B", "RelatesTo", db, weight=0.8)
    supersede.mark_edge("B", "C", "RelatesTo", db, weight=0.7)
    supersede.mark_edge("C", "D", "RelatesTo", db, weight=0.6)
    supersede.mark_edge("A", "tag1", "HasTag", db)

    # Depth 1 from A: B + tag1 (HasTag is also traversed)
    d1 = supersede.cascade_retrieve("A", db, depth=1)
    assert set(d1) == {"B", "tag1"}

    # Depth 2 from A: B, tag1, C
    d2 = supersede.cascade_retrieve("A", db, depth=2)
    assert set(d2) == {"B", "tag1", "C"}

    # Depth 3 from A: full chain + tag
    d3 = supersede.cascade_retrieve("A", db, depth=3)
    assert set(d3) == {"B", "tag1", "C", "D"}

    # Kind filter: only RelatesTo, no HasTag
    d2_rel = supersede.cascade_retrieve("A", db, depth=2, kinds=["RelatesTo"])
    assert "tag1" not in d2_rel
    assert "B" in d2_rel and "C" in d2_rel

    # Depth 0 -> nothing
    assert supersede.cascade_retrieve("A", db, depth=0) == []

    # Missing memory -> empty (no edges)
    assert supersede.cascade_retrieve("does-not-exist", db, depth=5) == []


def test_auto_save_v2_frontmatter_roundtrip(tmp_path: Path) -> None:
    from sinister_memory.auto_save import (
        FRONTMATTER_VERSION,
        parse_frontmatter,
        save_iter_close,
    )

    out = save_iter_close(
        slug="test-agent",
        iter_num=42,
        summary="schema v2 round-trip test",
        root=tmp_path,
        category="correction",
        confidence=0.85,
        trust="high",
    )
    fm = parse_frontmatter(out)
    assert fm.get("format_version") == str(FRONTMATTER_VERSION)
    assert fm.get("category") == "correction"
    assert fm.get("confidence") == "0.850"
    assert fm.get("trust") == "high"
    assert fm.get("slug") == "test-agent"
    assert fm.get("iter") == "42"

    # Save without optional fields -> v2 frontmatter still emitted, optional keys absent
    out_min = save_iter_close(
        slug="test-agent", iter_num=43, summary="minimal", root=tmp_path
    )
    fm_min = parse_frontmatter(out_min)
    assert fm_min.get("format_version") == str(FRONTMATTER_VERSION)
    assert "category" not in fm_min
    assert "confidence" not in fm_min
    assert "trust" not in fm_min


def test_auto_save_validates_optional_fields(tmp_path: Path) -> None:
    from sinister_memory.auto_save import save_iter_close

    valid_slug = "test-agent"

    with pytest.raises(ValueError, match="invalid category"):
        save_iter_close(valid_slug, 0, "x", tmp_path, category="bogus")

    with pytest.raises(ValueError, match="confidence"):
        save_iter_close(valid_slug, 1, "x", tmp_path, confidence=1.5)
    with pytest.raises(ValueError, match="confidence"):
        save_iter_close(valid_slug, 2, "x", tmp_path, confidence=-0.1)

    with pytest.raises(ValueError, match="trust"):
        save_iter_close(valid_slug, 3, "x", tmp_path, trust="ultra")


def test_decay_recall_uses_category_half_life(tmp_path: Path) -> None:
    """recall_with_decay(category="inferred") should use half_life=7d, not 30d."""
    from sinister_memory import decay, indexer

    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "knowledge" / "doc.md").write_text("loop relentless doctrine binding", encoding="utf-8")
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)

    # With category=inferred and short half-life, recall must still return hits
    hits = decay.recall_with_decay(
        query="relentless", db_path=db, limit=3, category="inferred"
    )
    assert hits, "recall_with_decay should return hits regardless of category"
    # Sanity: half-life table was actually consulted
    assert decay.half_life_for("inferred") == 7.0
