# Author: RKOJ-ELENO :: 2026-05-25
"""End-to-end integration test for consolidate.py (all 8 steps).

Iter-18 wired up step 8 (lane_briefings). This test exercises the full
pipeline in a temp tree and asserts each step produced sensible output.
Catches future regressions where someone edits one step and silently breaks
another's wiring.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _seed_full_tree(tmp_path: Path) -> None:
    """Seed a Sanctum-like tree with corpus + projects + per-agent dir."""
    from sinister_memory import indexer

    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "PROGRESS").mkdir(parents=True, exist_ok=True)
    (sm / "heartbeats").mkdir(parents=True, exist_ok=True)
    (sm / "sinister-memory" / "per-agent" / "test-lane").mkdir(parents=True, exist_ok=True)

    # Multi-doc corpus so dedupe + embeddings have signal
    for i in range(20):
        (sm / "knowledge" / f"doctrine-{i:02d}.md").write_text(
            f"<!-- decay: category: preference -->\n"
            f"# Doctrine {i}\n\nLoop relentless pursuit feature {i % 5}. "
            f"Kernel vector cosine similarity. Sinister memory layer.\n",
            encoding="utf-8",
        )
    for slug in ("test-lane", "other-lane"):
        (sm / "PROGRESS" / f"{slug}.md").write_text(
            f"## iter-1 :: {slug}\n\nshipped feature; verified.\n",
            encoding="utf-8",
        )
    (sm / "heartbeats" / "test-lane.json").write_text(
        json.dumps({"slug": "test-lane", "status": "alive"}), encoding="utf-8",
    )

    # projects.json for lane_briefings + adoption sub-score
    pj_dir = tmp_path / "automations" / "session-templates"
    pj_dir.mkdir(parents=True, exist_ok=True)
    (pj_dir / "projects.json").write_text(json.dumps({
        "projects": [
            {"key": "test-lane", "display": "Test Lane"},
            {"key": "other-lane", "display": "Other Lane"},
        ],
    }), encoding="utf-8")

    # Seed a v2-frontmatter save so adoption is non-zero
    (sm / "sinister-memory" / "per-agent" / "test-lane" / "iter-0001.md").write_text(
        "---\n"
        "slug: test-lane\n"
        "format_version: 2\n"
        "category: preference\n"
        "confidence: 0.9\n"
        "---\n"
        "# test-lane :: iter-0001\n\nseeded for end-to-end test\n",
        encoding="utf-8",
    )

    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)


def test_consolidate_all_eight_steps_dry_run(tmp_path: Path) -> None:
    """Full pipeline in dry-run. Every step must produce a sensible dict."""
    from sinister_memory import consolidate, indexer

    _seed_full_tree(tmp_path)
    db = indexer.default_db_path(tmp_path)

    stats = consolidate.consolidate(
        root=tmp_path,
        db_path=db,
        dry_run=True,
        with_embeddings=True,
        with_verify=False,
    )

    # Required top-level keys
    for k in ("index", "dedupe", "prune", "embeddings", "verify", "rotate", "lane_briefings"):
        assert k in stats, f"step {k} missing from consolidate output"

    # Step 1 :: index ran
    assert isinstance(stats["index"], dict)
    assert "indexed" in stats["index"] or "error" in stats["index"]

    # Step 2 :: dedupe ran
    assert "scanned" in stats["dedupe"] or "error" in stats["dedupe"]

    # Step 3 :: prune ran (dry-run honored)
    assert stats["prune"].get("dry_run") is True

    # Step 4 :: embeddings ran (because with_embeddings=True)
    assert "scanned" in stats["embeddings"], f"embeddings sub: {stats['embeddings']}"
    assert stats["embeddings"]["scanned"] > 0

    # Step 5 :: verify explicitly skipped
    assert stats["verify"].get("skipped") is True

    # Step 6+7 :: rotate present
    assert "progress" in stats["rotate"]
    assert "fleet_updates" in stats["rotate"]

    # Step 8 :: lane_briefings wrote per-lane docs
    assert "written" in stats["lane_briefings"], f"lane_briefings: {stats['lane_briefings']}"
    assert stats["lane_briefings"]["written"] >= 1, f"expected briefings written, got {stats['lane_briefings']}"

    # Verify briefings actually landed on disk
    briefings_dir = tmp_path / "_shared-memory" / "audits" / "per-lane-briefings"
    assert briefings_dir.is_dir()
    assert (briefings_dir / "test-lane.md").exists()
    assert (briefings_dir / "other-lane.md").exists()


def test_consolidate_step_8_briefing_content(tmp_path: Path) -> None:
    """Briefings must contain the right structural sections."""
    from sinister_memory import consolidate, indexer

    _seed_full_tree(tmp_path)
    db = indexer.default_db_path(tmp_path)
    consolidate.consolidate(
        root=tmp_path, db_path=db, dry_run=True,
        with_embeddings=True, with_verify=False,
    )

    briefing = (tmp_path / "_shared-memory" / "audits" / "per-lane-briefings" / "test-lane.md").read_text(encoding="utf-8")
    assert "Lane briefing :: Test Lane" in briefing
    assert "Top recall hits" in briefing
    assert "Per-agent saves" in briefing
    assert "Supersede/Contradicts edges" in briefing
    # The seeded iter-0001 save should appear in per-agent section
    assert "iter-0001" in briefing


def test_iter23_rotation_rejects_degenerate_split(tmp_path: Path) -> None:
    """Iter-23 contradict-fix: rotation must NOT report 'rotated' when the split
    point lands too close to EOF (i.e. no meaningful shrinkage). Catches the
    real-world bug where `\\n---\\n` was past the search window and the file
    silently kept ~100% of original size.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import rotate_progress as rp

    # File that has \n---\n only NEAR the end (past keep_bytes + scan_bytes
    # window) -- the degenerate case from real fleet data
    p = tmp_path / "degenerate.md"
    keep_kb = 80
    # 90 KB body, separator at byte 88000 (well past keep + scan_window)
    body = "filler line\n" * 7000  # ~84 KB
    body += "more filler\n" * 800  # extend
    body = body[:88000] + "\n---\n" + "tail content\n"
    p.write_text(body, encoding="utf-8")
    assert p.stat().st_size > keep_kb * 1024

    stats = rp.rotate_progress_file(p, keep_kb=keep_kb, dry_run=False)
    # Must NOT silently claim 'rotated' with kept ratio ~1.0
    assert stats["action"] != "rotated" or float(stats.get("ratio_kept", "1.0")) <= 0.95, (
        f"degenerate rotation should be rejected or actually shrink the file; got {stats}"
    )


def test_consolidate_apply_persists_rotation(tmp_path: Path) -> None:
    """With dry_run=False, rotation step must actually write to disk if oversized."""
    from sinister_memory import consolidate, indexer

    _seed_full_tree(tmp_path)
    # Make one PROGRESS file oversized to trigger rotation
    big = tmp_path / "_shared-memory" / "PROGRESS" / "big-lane.md"
    big.write_text("## iter-1 :: big\n\n" + ("filler line\n" * 8000), encoding="utf-8")
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)

    stats = consolidate.consolidate(
        root=tmp_path, db_path=db, dry_run=False,
        with_embeddings=False, with_verify=False,
    )

    # Rotation should report the big file as rotated (not skip-under-threshold)
    rotated = [p for p in stats["rotate"]["progress"]
               if isinstance(p, dict) and p.get("action") == "rotated"]
    assert any(r["path"].endswith("big-lane.md") for r in rotated), (
        f"big-lane.md should have been rotated; got: {rotated}"
    )

    # Archive must exist
    archive_dir = tmp_path / "_shared-memory" / "_archive" / "PROGRESS"
    assert archive_dir.is_dir()
    archives = list(archive_dir.glob("big-lane-*.md"))
    assert len(archives) >= 1, "archive file should be written"
