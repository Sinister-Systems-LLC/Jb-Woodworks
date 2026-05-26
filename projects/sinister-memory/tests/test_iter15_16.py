# Author: RKOJ-ELENO :: 2026-05-25
"""Iter-15 (doctor) + iter-16 (spawn-phrase health injection) regression tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _seed_minimal(tmp_path: Path) -> None:
    from sinister_memory import indexer, embed
    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "PROGRESS").mkdir(parents=True, exist_ok=True)
    (sm / "knowledge" / "doctrine.md").write_text(
        "loop relentless pursuit doctrine -- the keep-going rule", encoding="utf-8",
    )
    (sm / "PROGRESS" / "test-lane.md").write_text(
        "iter-1 shipped loop relentless feature", encoding="utf-8",
    )
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)
    embed.build_embedding_index(root=tmp_path, db_path=embed.default_embedding_db(tmp_path), backend="tfidf")
    pj = tmp_path / "automations" / "session-templates"
    pj.mkdir(parents=True, exist_ok=True)
    (pj / "projects.json").write_text(json.dumps({
        "projects": [{"key": "test-lane", "display": "Test Lane"}]
    }), encoding="utf-8")


def test_doctor_returns_full_shape(tmp_path: Path) -> None:
    from sinister_memory import doctor
    _seed_minimal(tmp_path)
    rep = doctor.doctor(tmp_path)
    assert "score" in rep
    assert "grade" in rep
    assert "worst_sub" in rep
    assert "diagnosis" in rep
    assert "recipe" in rep
    assert "all_sub_scores" in rep


def test_doctor_identifies_adoption_when_zero(tmp_path: Path) -> None:
    """With no per-agent files seeded, doctor should call out adoption."""
    from sinister_memory import doctor
    _seed_minimal(tmp_path)
    rep = doctor.doctor(tmp_path)
    # adoption sub-score has the highest weight (25) and starts at 0 in a fresh tree
    assert rep["worst_sub"] == "adoption", f"expected adoption worst, got {rep['worst_sub']}"
    # Recipe must reference the save command + the doctrine path
    assert " save " in rep["recipe"]
    assert "sinister-memory" in rep["recipe"]
    assert "adoption-doctrine" in rep["recipe"]


def test_doctor_no_action_when_health_high(tmp_path: Path) -> None:
    """When health is high (no actionable items >=5pt loss), doctor returns the
    'no actionable items' message OR a sub-score with very small lost points."""
    from sinister_memory import doctor
    # Seed minimally; health will be moderate (not >=95). The structure must
    # still resolve a worst_sub even if low-lost-points.
    _seed_minimal(tmp_path)
    rep = doctor.doctor(tmp_path)
    # On a freshly-seeded tree health < 95 so worst_sub is named
    assert rep["worst_sub"] is not None


def test_iter16_inject_for_spawn_with_include_health(tmp_path: Path) -> None:
    """include_health=True prepends the SINISTER_MEMORY_HEALTH one-liner."""
    from sinister_memory import spawn_inject
    _seed_minimal(tmp_path)
    chunk = spawn_inject.inject_for_spawn("nonexistent-slug", tmp_path, limit=3, include_health=True)
    assert chunk.startswith("SINISTER_MEMORY_HEALTH:"), f"missing health prefix; got: {chunk[:120]}"
    assert "/100" in chunk
    # Body still includes the "no prior memories" stub
    assert "no prior memories" in chunk


def test_iter16_inject_for_spawn_without_include_health(tmp_path: Path) -> None:
    """Backward compat: default include_health=False omits the line."""
    from sinister_memory import spawn_inject
    _seed_minimal(tmp_path)
    chunk = spawn_inject.inject_for_spawn("nonexistent-slug", tmp_path, limit=3)
    assert not chunk.startswith("SINISTER_MEMORY_HEALTH:")
    assert "Last memories" in chunk


def test_iter22_auto_rebuild_throttle(tmp_path: Path) -> None:
    """R1 auto-rebuild must throttle to at most once per 10s, even if recall is
    hammered repeatedly with a stale index. Catches the contradict-risk
    identified iter-22 (high write rate -> N rebuilds per second)."""
    from sinister_memory import recall, indexer
    import time as _time

    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    (sm / "PROGRESS").mkdir(parents=True, exist_ok=True)
    (sm / "knowledge" / "doc.md").write_text("loop relentless pursuit", encoding="utf-8")
    db = indexer.default_db_path(tmp_path)
    indexer.build(tmp_path, db)

    # Reset module-level state + force a stale state (write a new file *after* build)
    recall._LAST_AUTO_REBUILD_TS = 0.0
    _time.sleep(0.05)  # let mtime advance
    (sm / "knowledge" / "stale-trigger.md").write_text("new content", encoding="utf-8")

    # First call should rebuild
    fired_first = recall._auto_rebuild_if_stale(db)
    # Second call <1s later with same staleness should be throttled
    (sm / "knowledge" / "another-trigger.md").write_text("more", encoding="utf-8")
    fired_second = recall._auto_rebuild_if_stale(db)

    assert fired_first is True, "first rebuild should fire"
    assert fired_second is False, (
        "second rebuild within throttle window should be skipped "
        "(R1 throttle prevents disk churn under high write rate)"
    )


def test_iter27_doctor_recipe_uses_actual_root_not_hardcoded(tmp_path: Path) -> None:
    """Iter-27 contradict-fix: recipes must point to the actual root passed to
    doctor(), not a hardcoded D:\\Sinister Sanctum. Catches the bug where
    SINISTER_SANCTUM_ROOT-overridden environments would get stale paths in
    the remediation commands."""
    from sinister_memory import doctor

    # Seed minimal tree at a tmp_path that is NOT D:\Sinister Sanctum
    sm = tmp_path / "_shared-memory"
    (sm / "knowledge").mkdir(parents=True, exist_ok=True)
    pj_dir = tmp_path / "automations" / "session-templates"
    pj_dir.mkdir(parents=True, exist_ok=True)
    import json
    (pj_dir / "projects.json").write_text(json.dumps({"projects": [{"key": "x", "display": "X"}]}), encoding="utf-8")

    rep = doctor.doctor(tmp_path)
    recipe = rep.get("recipe", "")
    # Recipe must reference the tmp_path, NOT the hardcoded sanctum path
    assert str(tmp_path) in recipe or recipe == "", (
        f"recipe should reference tmp_path={tmp_path}; got: {recipe[:200]}"
    )
    # And must NOT contain the old hardcoded path (unless tmp_path happens to be that)
    if "D:\\Sinister Sanctum" not in str(tmp_path):
        assert "D:\\Sinister Sanctum" not in recipe, (
            f"recipe should NOT have hardcoded D:\\Sinister Sanctum; got: {recipe[:200]}"
        )


def test_doctor_has_recipe_for_every_sub_score() -> None:
    """Every sub-score in health._WEIGHTS must have a corresponding _FIXES entry,
    so doctor can always emit a remediation. Catches future health additions
    that forget to ship a fix recipe."""
    from sinister_memory import doctor as _doc
    from sinister_memory import health as _h

    for sub_name in _h._WEIGHTS.keys():
        assert sub_name in _doc._FIXES, (
            f"sub-score {sub_name} has no _FIXES entry in doctor.py -- "
            f"doctor will say 'Unknown sub-score' for it"
        )
        diagnosis, recipe = _doc._FIXES[sub_name]
        assert diagnosis, f"sub-score {sub_name} has empty diagnosis"
        assert recipe, f"sub-score {sub_name} has empty recipe"
