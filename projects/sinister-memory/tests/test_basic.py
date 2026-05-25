# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: P0 basic tests.

5 tests, all sandboxed under tmp_path. NEVER touches the real `_shared-memory/`.

Coverage:
  1. indexer.build creates FTS5 schema + indexes a synthetic brain entry
  2. recall.recall returns ranked hits and respects --limit
  3. auto_save.save_iter_close writes per-agent/<slug>/iter-NNNN.md w/ frontmatter
  4. spawn_inject.inject_for_spawn emits markdown chunk with the saved iter visible
  5. cli.main smoke -- recall against empty-but-built index exits 0 + no traceback
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow running pytest without installing the package
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _seed_sanctum(root: Path) -> None:
    """Create the minimum _shared-memory/ layout the indexer expects."""
    sm = root / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "PROGRESS").mkdir(parents=True, exist_ok=True)
    (sm / "heartbeats").mkdir(parents=True, exist_ok=True)
    (sm / "knowledge" / "loop-relentless-pursuit-doctrine-2026-05-25.md").write_text(
        "# Loop Relentless\n\nAfter every shipped deliverable, immediately start the next iteration.\n",
        encoding="utf-8",
    )
    (sm / "PROGRESS" / "Sinister Sanctum.md").write_text(
        "# Sinister Sanctum :: progress\n\n## 2026-05-25\n- Shipped sinister-memory P0 scaffold (5/5 tests).\n",
        encoding="utf-8",
    )
    (sm / "heartbeats" / "sanctum.json").write_text(
        '{"slug":"sanctum","status":"alive","note":"writing memory tests"}',
        encoding="utf-8",
    )


def test_indexer_build_creates_index(tmp_path: Path) -> None:
    from sinister_memory import indexer

    _seed_sanctum(tmp_path)
    db = indexer.default_db_path(tmp_path)
    stats = indexer.build(tmp_path, db)

    assert db.exists(), "index.db must be created"
    assert stats["indexed"] >= 3, f"expected >=3 files indexed, got {stats}"
    # Second call: everything cached
    stats2 = indexer.build(tmp_path, db)
    assert stats2["indexed"] == 0, "re-run with unchanged mtimes must skip all"
    assert stats2["skipped"] >= 3


def test_recall_returns_ranked_hits_and_respects_limit(tmp_path: Path) -> None:
    from sinister_memory import indexer, recall

    _seed_sanctum(tmp_path)
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)

    hits = recall.recall("relentless", db, limit=5)
    assert len(hits) >= 1, "must find the brain entry mentioning 'relentless'"
    assert hits[0].layer in {"brain", "progress", "heartbeat", "per-agent"}

    # Limit respected
    many = recall.recall("relentless", db, limit=1)
    assert len(many) <= 1

    # Empty / malformed query -> []
    assert recall.recall("", db) == []
    assert recall.recall('"""(((', db) == []

    # Missing db -> []
    assert recall.recall("x", tmp_path / "does-not-exist.db") == []


def test_auto_save_writes_iter_file_with_frontmatter(tmp_path: Path) -> None:
    from sinister_memory import auto_save

    out = auto_save.save_iter_close(
        slug="sinister-memory-test",
        iter_num=23,
        summary="Shipped P0 scaffold; 5/5 pytest PASS; SQLite FTS5 + BM25.",
        root=tmp_path,
        do_reindex=False,
    )
    assert out.exists()
    assert out.name == "iter-0023.md"
    body = out.read_text(encoding="utf-8")
    assert body.startswith("---\n"), "must include frontmatter"
    assert "slug: sinister-memory-test" in body
    assert "iter: 23" in body
    assert "Shipped P0 scaffold" in body

    # list_iters returns newest-first
    out2 = auto_save.save_iter_close(
        slug="sinister-memory-test", iter_num=24, summary="iter 24", root=tmp_path
    )
    listed = auto_save.list_iters("sinister-memory-test", tmp_path)
    assert listed[0] == out2, "newest iter must be first"

    # Bad slug rejected
    with pytest.raises(ValueError):
        auto_save.save_iter_close("BAD SLUG WITH SPACES", 0, "x", tmp_path)


def test_spawn_inject_emits_markdown_chunk_with_saved_iter(tmp_path: Path) -> None:
    from sinister_memory import auto_save, spawn_inject

    # No memories -> stub
    chunk0 = spawn_inject.inject_for_spawn("nonexistent-slug", tmp_path)
    assert "no prior memories" in chunk0

    # After save -> chunk references the iter
    auto_save.save_iter_close(
        slug="sinister-overseer",
        iter_num=7,
        summary="learned token-tier routing pays for itself within 2 days",
        root=tmp_path,
    )
    chunk = spawn_inject.inject_for_spawn("sinister-overseer", tmp_path, limit=3)
    assert "## Last memories (sinister-memory)" in chunk
    assert "iter-0007" in chunk
    assert "token-tier routing" in chunk
    # PS-safe: no terminating heredoc collision token
    assert "'@" not in chunk
    assert "`" not in chunk


def test_cli_recall_smoke_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    from sinister_memory import cli, indexer

    _seed_sanctum(tmp_path)
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)

    # version
    assert cli.main(["version"]) == 0

    # recall against built index
    rc = cli.main(["--root", str(tmp_path), "recall", "relentless", "--limit", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out  # non-empty (either hits or the "no memories matched" stub)

    # recall with empty query string -> stub, exit 0
    rc2 = cli.main(["--root", str(tmp_path), "recall", " ", "--limit", "1"])
    assert rc2 == 0

    # --help short-circuits via argparse SystemExit(0)
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
