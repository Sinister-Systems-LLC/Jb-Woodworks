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

    # Step 6 (iter-8) :: rotate oversized PROGRESS files (R4).
    # Keeps recall corpus lean. Runs even on dry_run (rotation itself preserves
    # full history in _archive/, so it's reversible). Threshold 80 KB.
    try:
        # Import lazily so consolidate doesn't depend on the script package at
        # import time. The rotation scripts live in projects/sinister-memory/scripts/,
        # which is NOT on sys.path; load via runpy.
        import runpy, sys
        script_dir = Path(__file__).resolve().parents[2] / "scripts"
        rotate_prog = script_dir / "rotate_progress.py"
        rotate_fu = script_dir / "rotate_fleet_updates.py"
        rot_stats: dict = {}
        if rotate_prog.exists():
            mod = runpy.run_path(str(rotate_prog), run_name="__sm_rotate_progress__")
            progress_dir = root / "_shared-memory" / "PROGRESS"
            rot_stats["progress"] = mod["rotate_all"](progress_dir, keep_kb=80, dry_run=dry_run)
        else:
            rot_stats["progress"] = {"error": f"script missing: {rotate_prog}"}
        # Step 7 :: rotate fleet-updates.jsonl (R11) when oversized
        if rotate_fu.exists():
            mod = runpy.run_path(str(rotate_fu), run_name="__sm_rotate_fleet__")
            fu_path = root / "_shared-memory" / "fleet-updates.jsonl"
            # Iter-46 preventive fix: pass max_row_kb=100 so the ambient pass
            # truncates oversized single-row payloads. Without this, iter-45's
            # 485 MB regression (24 rows * 21 MB avg from agents broadcasting
            # massive payloads) would silently recur every few hours.
            rot_stats["fleet_updates"] = mod["rotate"](
                fu_path, keep=1000, max_mb=100, dry_run=dry_run, max_row_kb=100,
            )
        else:
            rot_stats["fleet_updates"] = {"error": f"script missing: {rotate_fu}"}
        stats["rotate"] = rot_stats
    except Exception as exc:  # noqa: BLE001
        stats["rotate"] = {"error": f"{type(exc).__name__}: {exc}"}

    # Step 8 (iter-18) :: regenerate per-lane briefings via R3 --lane recall slice.
    # Briefings live at _shared-memory/audits/per-lane-briefings/<slug>.md and
    # are what spawning agents `cat` to see their lane's status. Auto-runs in
    # ambient pass so briefings are always fresh.
    try:
        import runpy
        script_dir = Path(__file__).resolve().parents[2] / "scripts"
        brief_script = script_dir / "generate_lane_briefings.py"
        if brief_script.exists():
            mod = runpy.run_path(str(brief_script), run_name="__sm_lane_briefings__")
            projects_json = root / "automations" / "session-templates" / "projects.json"
            out_dir = root / "_shared-memory" / "audits" / "per-lane-briefings"
            out_dir.mkdir(parents=True, exist_ok=True)
            projects = mod["_load_projects"](projects_json) if projects_json.exists() else []
            n_written = 0
            for proj in projects:
                slug = proj["key"]
                display = proj.get("display", slug)
                try:
                    top = mod["_top_recall"](slug, root, limit=5)
                    saves = mod["_per_agent_files"](slug, root, limit=5)
                    edges = mod["_supersede_edges"](slug, root, limit=5)
                    md = mod["render"](slug, display, top, saves, edges)
                    (out_dir / f"{slug}.md").write_text(md, encoding="utf-8")
                    n_written += 1
                except Exception:  # noqa: BLE001
                    continue
            stats["lane_briefings"] = {"written": n_written, "out_dir": str(out_dir)}
        else:
            stats["lane_briefings"] = {"error": f"script missing: {brief_script}"}
    except Exception as exc:  # noqa: BLE001
        stats["lane_briefings"] = {"error": f"{type(exc).__name__}: {exc}"}

    # Step 9 (iter-47) :: adoption sweep -- write newest PROGRESS heading per
    # lane into _shared-memory/sinister-memory/per-agent/<key>/ with v2
    # frontmatter so the health.adoption sub-score climbs without per-lane
    # manual saves. Idempotent: existing rows with same body are not rewritten.
    # Runs even on dry_run because saves are non-destructive (new files only).
    try:
        from . import adoption_sweep

        sweep_stats = adoption_sweep.sweep_progress_to_per_agent(root, dry_run=dry_run)
        # Trim per-lane action lists to keep the consolidated stats dict lean.
        stats["adoption_sweep"] = {
            k: v for k, v in sweep_stats.items()
            if k not in ("lanes", "errors")  # drop verbose arrays
        }
        stats["adoption_sweep"]["lane_count"] = len(sweep_stats.get("lanes", []))
        if sweep_stats.get("errors"):
            stats["adoption_sweep"]["error_count"] = len(sweep_stats["errors"])
    except Exception as exc:  # noqa: BLE001
        stats["adoption_sweep"] = {"error": f"{type(exc).__name__}: {exc}"}

    return stats
