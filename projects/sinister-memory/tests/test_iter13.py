# Author: RKOJ-ELENO :: 2026-05-25
"""Iter-13 (health composite score) tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _seed_minimal(tmp_path: Path) -> None:
    """Seed a minimal Sanctum-like tree so health() doesn't bottom out."""
    from sinister_memory import indexer, embed
    import json
    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "PROGRESS").mkdir(parents=True, exist_ok=True)
    (sm / "knowledge" / "doctrine.md").write_text(
        "loop relentless pursuit doctrine -- the keep-going rule", encoding="utf-8",
    )
    (sm / "PROGRESS" / "test-lane.md").write_text(
        "iter-1 shipped feature loop relentless", encoding="utf-8",
    )
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)
    embed.build_embedding_index(root=tmp_path, db_path=embed.default_embedding_db(tmp_path), backend="tfidf")
    # projects.json + per-agent dir so adoption sub-score can score
    pj = tmp_path / "automations" / "session-templates"
    pj.mkdir(parents=True, exist_ok=True)
    (pj / "projects.json").write_text(json.dumps({
        "projects": [{"key": "test-lane", "display": "Test Lane"}]
    }), encoding="utf-8")


def test_health_full_shape(tmp_path: Path) -> None:
    from sinister_memory import health
    _seed_minimal(tmp_path)
    report = health.health(tmp_path)
    assert "score" in report
    assert "sub_scores" in report
    assert "ts_utc" in report
    expected_keys = {
        "index_present", "embeddings_present", "layer_coverage",
        "recall_works", "vector_works", "rotation_healthy", "adoption",
    }
    assert set(report["sub_scores"].keys()) == expected_keys
    assert 0 <= report["score"] <= 100
    # All weights must sum to 100
    total_w = sum(s["weight"] for s in report["sub_scores"].values())
    assert total_w == 100


def test_health_score_when_index_missing(tmp_path: Path) -> None:
    from sinister_memory import health
    # No seeding -- empty tree
    report = health.health(tmp_path)
    # With nothing seeded the index/embed/recall sub-scores must be 0
    assert report["sub_scores"]["index_present"]["score"] == 0.0
    assert report["sub_scores"]["embeddings_present"]["score"] == 0.0
    assert report["sub_scores"]["recall_works"]["score"] == 0.0
    # Composite must be low (under 30) when no infrastructure exists
    assert report["score"] < 30


def test_health_grade_letters() -> None:
    from sinister_memory import health
    assert health.health_grade(95) == "A"
    assert health.health_grade(80) == "B"
    assert health.health_grade(65) == "C"
    assert health.health_grade(50) == "D"
    assert health.health_grade(20) == "F"


def test_health_minimal_seed_scores_above_50(tmp_path: Path) -> None:
    """Even a tiny corpus should score above the 'broken' threshold."""
    from sinister_memory import health
    _seed_minimal(tmp_path)
    report = health.health(tmp_path)
    assert report["score"] >= 50, f"minimal-seeded health should be C+, got {report['score']} :: {report['sub_scores']}"
