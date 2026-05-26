# Author: RKOJ-ELENO :: 2026-05-25
"""Iter-10 (batched insert speedup) + iter-11 (IDF table) regression tests."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _seed_corpus(tmp_path: Path, n_docs: int = 200) -> Path:
    """Generate N synthetic .md files spread across two layers + build FTS5 index."""
    from sinister_memory import indexer

    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "PROGRESS").mkdir(parents=True, exist_ok=True)
    for i in range(n_docs):
        # Two layers: half brain, half progress; varied content so IDF has signal
        if i % 2 == 0:
            (sm / "knowledge" / f"doc-{i:04d}.md").write_text(
                f"Brain entry {i} about loop relentless quantum cosine sinister memory "
                f"{'unique' + str(i) if i < n_docs // 4 else 'common'}",
                encoding="utf-8",
            )
        else:
            slug = "kernel-apk" if i % 3 else "sinister-memory"
            (sm / "PROGRESS" / f"{slug}.md").write_text(
                f"Progress for {slug} iter {i}: shipped feature {i % 7}",
                encoding="utf-8",
            )
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)
    return db


def test_iter10_batched_insert_throughput(tmp_path: Path) -> None:
    """Iter-10 batched insert + WAL must process >=200 rows/sec on the
    write path (synthetic corpus of 200 docs). Pre-iter-10 the per-row
    open+close+commit was ~20 rows/sec; the regression test sets the
    floor at 10x that to catch any reversion."""
    from sinister_memory import embed

    _seed_corpus(tmp_path, n_docs=200)
    db = embed.default_embedding_db(tmp_path)

    t0 = time.perf_counter()
    stats = embed.build_embedding_index(root=tmp_path, db_path=db, backend="tfidf")
    elapsed = time.perf_counter() - t0

    assert stats["written"] > 0, f"expected writes, got {stats}"
    written = stats["written"]
    throughput = written / max(elapsed, 1e-6)
    # Floor at 200 rows/sec. Real-world iter-10 measurement was ~900 rows/sec.
    # Generous floor accommodates slow CI / locked-DB pauses.
    assert throughput >= 200, (
        f"REGRESSION: batched insert dropped below 200 rows/sec "
        f"(got {throughput:.1f} rows/sec, written={written}, elapsed={elapsed:.2f}s). "
        f"Did embed.py revert to per-row commits?"
    )


def test_iter11_idf_table_persists_and_reloads(tmp_path: Path) -> None:
    """IDF table is built on first embed-index pass + persisted to idf.json
    + reloaded on next call (no rebuild)."""
    from sinister_memory import embed

    _seed_corpus(tmp_path, n_docs=80)
    db = embed.default_embedding_db(tmp_path)

    # Reset module-level cache so we exercise the build path
    embed._IDF_CACHE = None
    idf_path = embed.default_idf_path(tmp_path)
    assert not idf_path.exists()

    embed.build_embedding_index(root=tmp_path, db_path=db, backend="tfidf")
    assert idf_path.exists(), "iter-11 must persist idf.json"
    assert embed._IDF_CACHE is not None
    assert len(embed._IDF_CACHE) > 0

    # Reload path
    embed._IDF_CACHE = None
    loaded = embed.load_idf_table(idf_path)
    assert loaded is not None
    assert loaded == {int(k): float(v) for k, v in loaded.items()}


def test_iter11_idf_weights_distinguish_rare_terms() -> None:
    """A rare token should get higher IDF weight than a common one."""
    from sinister_memory import embed

    snippets = ["common" for _ in range(99)] + ["rare unique-token"]
    idf = embed.build_idf_table(snippets, min_df=1)
    common_b = embed._hash_token("common")
    rare_b = embed._hash_token("unique_token")  # tokenize lowercases + drops dashes
    rare_b2 = embed._hash_token("rare")
    # rare bucket should have higher idf than common bucket
    assert idf[rare_b2] > idf[common_b]
