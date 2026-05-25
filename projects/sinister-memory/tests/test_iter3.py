# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: iter-3 tests (P7-P14: embed / prune / consolidate / batch-verify / contradiction-gate / export-graph).

Brain entries:
- jcode-memory-audit-and-cherry-picks-2026-05-25.md (iter-2)
- multi-harness-memory-audit-2026-05-25.md (iter-3, when aggregated)
- sinister-memory-architecture-2026-05-25.md (iter-3)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _seed_for_index(tmp_path: Path) -> Path:
    from sinister_memory import indexer

    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "PROGRESS").mkdir(parents=True, exist_ok=True)
    (sm / "knowledge" / "doctrine.md").write_text(
        "loop relentless pursue every shipped deliverable immediately start next iteration",
        encoding="utf-8",
    )
    (sm / "knowledge" / "memory.md").write_text(
        "supersede dedupe cascade graph edges typed kinds",
        encoding="utf-8",
    )
    (sm / "PROGRESS" / "Sinister Memory.md").write_text(
        "iter-3 shipped embeddings cosine similarity",
        encoding="utf-8",
    )
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)
    return db


def test_embed_cosine_identity_and_orthogonal() -> None:
    from sinister_memory import embed

    v = embed.embed_text("loop relentless pursue every shipped")
    assert len(v) == 256, "TF-IDF backend uses dim=256"
    assert embed.cosine(v, v) == pytest.approx(1.0, rel=1e-5)

    a = embed.embed_text("apples bananas cherries")
    b = embed.embed_text("zebras quokkas platypuses")
    assert embed.cosine(a, b) < 0.3, "unrelated texts should be near-orthogonal"

    # Empty / mismatched
    assert embed.cosine([], v) == 0.0
    assert embed.cosine([1.0, 2.0], [1.0]) == 0.0


def test_embed_store_and_recall_roundtrip(tmp_path: Path) -> None:
    from sinister_memory import embed

    _ = _seed_for_index(tmp_path)
    db = embed.default_embedding_db(tmp_path)

    stats = embed.build_embedding_index(root=tmp_path, db_path=db)
    assert stats["scanned"] >= 3, f"expected at least 3 rows, got {stats}"
    assert stats["written"] >= 3
    assert stats["backend"] in {"tfidf", "ruflo", "null"}

    # Re-run is idempotent
    stats2 = embed.build_embedding_index(root=tmp_path, db_path=db)
    assert stats2["written"] == 0, "second pass should skip everything"
    assert stats2["skipped"] >= 3

    # Recall something the corpus contains
    hits = embed.recall_by_vector("loop relentless shipped", db, limit=5, threshold=0.05)
    assert hits, "embedded corpus should match its own tokens"
    assert hits[0].score > 0.0
    assert hits[0].score <= 1.0001  # cosine bounds


def test_prune_dry_run_no_delete(tmp_path: Path) -> None:
    from sinister_memory import auto_save, indexer, prune

    # Save a low-confidence memory; can't easily make it 24h old in test, so we
    # validate dry-run path + that candidates list works on artificial backdating.
    p = auto_save.save_iter_close(
        slug="test-prune-agent",
        iter_num=1,
        summary="ephemeral low-confidence fact",
        root=tmp_path,
        category="inferred",
        confidence=0.05,
    )
    # Backdate the file's mtime to 48h ago so it crosses age threshold
    import os, time
    age_seconds = 48 * 3600
    os.utime(p, (time.time() - age_seconds, time.time() - age_seconds))

    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)

    dry = prune.prune_low_confidence(tmp_path, db, confidence_threshold=0.15, age_hours=24, dry_run=True)
    assert dry["dry_run"] is True
    assert dry["candidates"] >= 1, f"expected at least 1 candidate, got {dry}"
    assert dry["pruned_fts"] == 0  # dry run doesn't delete

    # Apply
    applied = prune.prune_low_confidence(tmp_path, db, confidence_threshold=0.15, age_hours=24, dry_run=False)
    assert applied["pruned_fts"] >= 1


def test_consolidate_orchestrates_all_steps(tmp_path: Path) -> None:
    from sinister_memory import consolidate, indexer

    _ = _seed_for_index(tmp_path)
    db = indexer.default_db_path(tmp_path)

    stats = consolidate.consolidate(root=tmp_path, db_path=db, dry_run=True)
    assert "index" in stats
    assert "dedupe" in stats
    assert "prune" in stats
    assert "embeddings" in stats
    assert "verify" in stats
    assert stats["dry_run"] is True

    # without embeddings opt-in -> stats says skipped sentinel
    assert stats["embeddings"] == {"skipped": True}, "default consolidate skips embeddings"

    # with embeddings opt-in -> actually runs (returns scanned/written/skipped/errors)
    stats2 = consolidate.consolidate(
        root=tmp_path, db_path=db, dry_run=True, with_embeddings=True
    )
    emb = stats2["embeddings"]
    assert "scanned" in emb and "written" in emb, "with_embeddings=True must return build stats"


def test_grade_batch_heuristic_returns_one_verdict_per_candidate() -> None:
    from sinister_memory import verify

    candidates = [
        ("mem-a", "loop relentless after every shipped deliverable start next"),
        ("mem-b", "totally unrelated text about cats and dogs"),
        ("mem-c", "loop relentless pursue immediately"),
    ]
    source = "loop relentless after every shipped deliverable immediately start next iteration"

    verdicts = verify.grade_batch(candidates, source, prefer="heuristic")
    assert len(verdicts) == 3
    assert verdicts[0].verdict in {"fresh", "stale"}
    assert verdicts[1].verdict == "stale", "unrelated text must be flagged stale"
    assert verdicts[2].verdict in {"fresh"}
    for v in verdicts:
        assert v.model == "heuristic-jaccard"
        assert v.cost_estimate_usd == 0.0


def test_check_contradiction_heuristic_negation_asymmetry() -> None:
    from sinister_memory import verify

    # Same topic, negation asymmetry -> contradicts
    contradicts, _r = verify.check_contradiction(
        new_text="we do NOT use bat files anymore stop using bat files everywhere",
        old_text="we use bat files for all installer scripts everywhere",
        prefer="heuristic",
    )
    assert contradicts is True

    # Same topic, no negation -> not contradicts
    not_c, _r2 = verify.check_contradiction(
        new_text="loop relentless after every shipped deliverable immediately start next",
        old_text="loop relentless pursue every shipped deliverable immediately start next iteration",
        prefer="heuristic",
    )
    assert not_c is False

    # Different topics -> not contradicts (jaccard too low)
    diff, _r3 = verify.check_contradiction(
        new_text="rust async tokio runtime futures",
        old_text="javascript dom manipulation jquery",
        prefer="heuristic",
    )
    assert diff is False


def test_mark_edge_contradiction_gate(tmp_path: Path) -> None:
    from sinister_memory import supersede

    db = tmp_path / "gated.db"

    # With check_contradiction=True and clear contradiction -> succeeds
    supersede.mark_edge(
        src_id="new-rule",
        dst_id="old-rule",
        kind="Supersedes",
        db_path=db,
        check_contradiction=True,
        new_text="we do NOT use bat files stop using bat files",
        old_text="we use bat files for all installer scripts",
        reason="operator-canonical 2026-05-25",
    )

    # With check_contradiction=True and NO contradiction -> rejected
    with pytest.raises(ValueError, match="contradiction-gate REJECTED"):
        supersede.mark_edge(
            src_id="new-2",
            dst_id="old-2",
            kind="Supersedes",
            db_path=db,
            check_contradiction=True,
            new_text="loop relentless shipped",
            old_text="loop relentless pursue immediately",
            reason="bogus",
        )

    # Without check_contradiction -> succeeds regardless
    supersede.mark_edge(
        src_id="new-3",
        dst_id="old-3",
        kind="Supersedes",
        db_path=db,
        reason="ungated",
    )


def test_export_graph_writes_d3_compatible_json(tmp_path: Path) -> None:
    from sinister_memory import export_graph, indexer, supersede

    db = _seed_for_index(tmp_path)
    # Add a couple of typed edges so the export has both nodes and edges
    supersede.mark_edge("memA", "memB", "RelatesTo", db, weight=0.7, reason="test")
    supersede.mark_edge("memC", "memD", "Supersedes", db, reason="newer")

    out = tmp_path / "graph.json"
    stats = export_graph.export_graph(root=tmp_path, db_path=db, out_path=out)
    assert out.exists()
    assert stats["nodes"] >= 1
    assert stats["edges"] >= 2

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "nodes" in payload and "edges" in payload and "meta" in payload
    assert payload["meta"]["node_count"] == stats["nodes"]
    assert payload["meta"]["edge_count"] == stats["edges"]
    # At least one edge is Supersedes
    kinds = {e["kind"] for e in payload["edges"]}
    assert "Supersedes" in kinds


def test_current_backend_returns_string() -> None:
    from sinister_memory import embed

    assert embed.current_backend() in {"ruflo", "tfidf", "null"}
