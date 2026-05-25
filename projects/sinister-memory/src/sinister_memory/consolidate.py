# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: ambient consolidation pass.

jcode's "ambient mode" (Image #2 operator screenshot): "Memories are automatically
consolidated every so often via the ambient mode. This reorganizes, checks for
staleness and conflicts, etc."

Our impl orchestrates a 5-step pipeline:
  1. index.build (incremental; mtime-based skip)
  2. cluster.dedupe (Jaccard >= threshold; marks dupes as superseded by newest)
  3. prune.prune_low_confidence (drop confidence<0.15 + age>=24h rows)
  4. (optional) embed.build_embedding_index (kernel-vector pass)
  5. (optional) verify-then-supersede candidate sweep (Haiku grader for top-K
     near-duplicates not yet edged; promotes Contradicts edges)

Designed to run via schtask every 6h. dry_run=True by default per
safe-quality-loops doctrine -- the operator (or a 1-iter-later agent) must
explicitly apply.

Public API:
  consolidate(root, db_path, dry_run=True, with_embeddings=False,
              with_verify=False, **thresholds) -> dict
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from . import cluster, indexer, prune


def consolidate(
    root: Path,
    db_path: Optional[Path] = None,
    dry_run: bool = True,
    with_embeddings: bool = False,
    with_verify: bool = False,
    dedupe_threshold: float = 0.85,
    dedupe_layers: tuple = ("progress", "per-agent"),
    confidence_threshold: float = 0.15,
    age_hours: float = 24.0,
) -> dict:
    """Run the 5-step ambient consolidation pipeline. Returns aggregated stats.

    Args:
      root              : Sanctum root (default _shared-memory/ parent)
      db_path           : index.db path; default <root>/_shared-memory/sinister-memory/index.db
      dry_run           : if True, dedupe/prune DON'T persist changes; embeddings/verify still run
      with_embeddings   : run build_embedding_index step (RAM-bounded; opt-in)
      with_verify       : run Haiku grader sweep (cost-bound; opt-in)
      dedupe_threshold  : Jaccard threshold for cluster.dedupe
      dedupe_layers     : layers to dedupe (default progress + per-agent; brain stays curated)
      confidence_threshold / age_hours : prune.prune_low_confidence params
    """
    root = Path(root)
    if db_path is None:
        db_path = indexer.default_db_path(root)
    db_path = Path(db_path)

    stats: dict = {
        "dry_run": dry_run,
        "with_embeddings": with_embeddings,
        "with_verify": with_verify,
    }

    # Step 1: index (always runs; incremental)
    try:
        idx_stats = indexer.build(root, db_path)
        stats["index"] = idx_stats
    except Exception as exc:  # noqa: BLE001
        stats["index"] = {"error": f"{type(exc).__name__}: {exc}"}
        idx_stats = None

    # Step 2: cluster dedupe
    try:
        dedupe_stats = cluster.dedupe(
            db_path=db_path,
            threshold=dedupe_threshold,
            layers=dedupe_layers,
            dry_run=dry_run,
        )
        stats["dedupe"] = dedupe_stats
    except Exception as exc:  # noqa: BLE001
        stats["dedupe"] = {"error": f"{type(exc).__name__}: {exc}"}

    # Step 3: prune low confidence (only candidates phase if dry_run)
    try:
        prune_stats = prune.prune_low_confidence(
            root=root,
            db_path=db_path,
            confidence_threshold=confidence_threshold,
            age_hours=age_hours,
            dry_run=dry_run,
        )
        stats["prune"] = prune_stats
    except Exception as exc:  # noqa: BLE001
        stats["prune"] = {"error": f"{type(exc).__name__}: {exc}"}

    # Step 4: embeddings (opt-in)
    if with_embeddings:
        try:
            from . import embed

            emb_db = embed.default_embedding_db(root)
            emb_stats = embed.build_embedding_index(root=root, db_path=emb_db)
            stats["embeddings"] = emb_stats
        except Exception as exc:  # noqa: BLE001
            stats["embeddings"] = {"error": f"{type(exc).__name__}: {exc}"}
    else:
        stats["embeddings"] = {"skipped": True}

    # Step 5: verify sweep (opt-in; costs Haiku calls)
    if with_verify:
        try:
            from . import verify as _verify

            modes = _verify.available_modes()
            stats["verify"] = {"modes": modes, "swept": 0, "note": "verify sweep is gated -- needs explicit ANTHROPIC_API_KEY + a candidate selector; iter-3 ships modes-probe only"}
        except Exception as exc:  # noqa: BLE001
            stats["verify"] = {"error": f"{type(exc).__name__}: {exc}"}
    else:
        stats["verify"] = {"skipped": True}

    return stats
