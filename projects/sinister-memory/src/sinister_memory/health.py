# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: composite health score.

Single 0-100 metric the operator / Panel can read in one shot to answer
"is fleet memory working?". Composed of 7 sub-scores each weighted by
their operational severity. Returns a dict so Panel can render the
breakdown.

Sub-scores (each 0-100):

  index_present       :: FTS5 index.db exists + has rows                  (15)
  embeddings_present  :: embeddings.db exists + has rows + IDF active     (15)
  layer_coverage      :: % of FTS5 layers also in embeddings.db            (10)
  recall_works        :: known-good query returns >=1 hit                  (15)
  vector_works        :: known-good vector-recall returns >=1 hit          (10)
  rotation_healthy    :: no PROGRESS file > 200KB; fleet-updates < 100MB   (10)
  adoption            :: % of lanes with save_v2 in last 14d               (25)

Total weights = 100. Returns {score: 0-100, sub_scores: {...}, ts_utc: ...}.
"""
from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_TEST_QUERY = "loop relentless pursuit"  # known-good query; brain entry always present


def _sub_index(root: Path) -> tuple[float, dict]:
    db = root / "_shared-memory" / "sinister-memory" / "index.db"
    if not db.exists():
        return 0.0, {"reason": "index.db missing"}
    try:
        conn = sqlite3.connect(str(db))
        n = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
    except sqlite3.OperationalError as exc:
        return 0.0, {"reason": str(exc)}
    if n == 0:
        return 0.0, {"reason": "index empty"}
    # Anything >100 rows = full health
    return 100.0, {"row_count": n}


def _sub_embeddings(root: Path) -> tuple[float, dict]:
    db = root / "_shared-memory" / "sinister-memory" / "embeddings.db"
    idf = root / "_shared-memory" / "sinister-memory" / "idf.json"
    if not db.exists():
        return 0.0, {"reason": "embeddings.db missing"}
    try:
        conn = sqlite3.connect(str(db))
        n = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        conn.close()
    except sqlite3.OperationalError as exc:
        return 0.0, {"reason": str(exc)}
    if n == 0:
        return 0.0, {"reason": "embeddings empty"}
    score = 80.0  # partial credit for rows existing
    if idf.exists():
        score = 100.0  # full credit when IDF table also present (iter-11 R8)
    return score, {"row_count": n, "idf_present": idf.exists()}


def _sub_layer_coverage(root: Path) -> tuple[float, dict]:
    ix = root / "_shared-memory" / "sinister-memory" / "index.db"
    em = root / "_shared-memory" / "sinister-memory" / "embeddings.db"
    if not (ix.exists() and em.exists()):
        return 0.0, {"reason": "missing db"}
    try:
        c1 = sqlite3.connect(str(ix))
        c2 = sqlite3.connect(str(em))
        ix_layers = {r[0] for r in c1.execute("SELECT DISTINCT layer FROM memories")}
        em_layers = {r[0] for r in c2.execute("SELECT DISTINCT layer FROM embeddings")}
        c1.close(); c2.close()
    except sqlite3.OperationalError as exc:
        return 0.0, {"reason": str(exc)}
    if not ix_layers:
        return 0.0, {"reason": "no layers in index"}
    covered = len(ix_layers & em_layers) / len(ix_layers)
    return covered * 100.0, {"index_layers": sorted(ix_layers), "embed_layers": sorted(em_layers)}


def _sub_recall(root: Path) -> tuple[float, dict]:
    db = root / "_shared-memory" / "sinister-memory" / "index.db"
    from .recall import recall
    t0 = time.perf_counter()
    try:
        hits = recall(_TEST_QUERY, db, limit=1, rrf=False)
    except Exception as exc:  # noqa: BLE001
        return 0.0, {"reason": str(exc)}
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if not hits:
        return 0.0, {"reason": "no hits", "elapsed_ms": elapsed_ms}
    return 100.0, {"top_hit_path": str(hits[0].path), "elapsed_ms": round(elapsed_ms, 2)}


def _sub_vector(root: Path) -> tuple[float, dict]:
    from . import embed
    db = embed.default_embedding_db(root)
    if not db.exists():
        return 0.0, {"reason": "embeddings.db missing"}
    t0 = time.perf_counter()
    try:
        hits = embed.recall_by_vector(_TEST_QUERY, db, limit=1, threshold=0.05)
    except Exception as exc:  # noqa: BLE001
        return 0.0, {"reason": str(exc)}
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if not hits:
        return 0.0, {"reason": "no vector hits", "elapsed_ms": elapsed_ms}
    return 100.0, {"top_score": round(hits[0].score, 3), "elapsed_ms": round(elapsed_ms, 2)}


def _sub_rotation(root: Path) -> tuple[float, dict]:
    """Penalize oversized PROGRESS files (>200KB) and oversized fleet-updates (>100MB)."""
    pdir = root / "_shared-memory" / "PROGRESS"
    fu = root / "_shared-memory" / "fleet-updates.jsonl"
    issues = []
    if pdir.is_dir():
        for p in pdir.iterdir():
            if p.is_file() and p.suffix.lower() == ".md":
                kb = p.stat().st_size // 1024
                if kb > 200:
                    issues.append({"path": p.name, "kb": kb})
    if fu.exists() and fu.stat().st_size > 100 * 1024 * 1024:
        issues.append({"path": "fleet-updates.jsonl", "mb": fu.stat().st_size // 1024 // 1024})
    if not issues:
        return 100.0, {"oversized_count": 0}
    # Penalize: 100 - (10 per oversized file)
    score = max(0.0, 100.0 - 10.0 * len(issues))
    return score, {"oversized_count": len(issues), "issues": issues[:5]}


def _sub_adoption(root: Path) -> tuple[float, dict]:
    """% of lanes with at least 1 v2-frontmatter file in last 14d.

    Iter-14 fix: auto_save writes to the namespaced path
    `_shared-memory/sinister-memory/per-agent/<slug>/` (shipped iter-2), but
    fleet conventions may also use `_shared-memory/per-agent/<slug>/`. Check
    BOTH.
    """
    pa_canonical = root / "_shared-memory" / "sinister-memory" / "per-agent"
    pa_fleet = root / "_shared-memory" / "per-agent"
    projects_json = root / "automations" / "session-templates" / "projects.json"
    if not projects_json.exists():
        return 0.0, {"reason": "missing projects.json"}
    import json
    with projects_json.open("r", encoding="utf-8") as f:
        projects = json.load(f).get("projects", [])
    n_lanes = len(projects)
    if n_lanes == 0:
        return 0.0, {"reason": "no lanes"}
    cutoff = time.time() - 14 * 86400
    adopted = 0
    for proj in projects:
        candidates = [pa_canonical / proj["key"], pa_fleet / proj["key"]]
        lane_adopted = False
        for d in candidates:
            if lane_adopted:
                break
            if not d.is_dir():
                continue
            try:
                for f in d.iterdir():
                    if not (f.is_file() and f.suffix.lower() == ".md"):
                        continue
                    if f.stat().st_mtime < cutoff:
                        continue
                    try:
                        head = f.read_text(encoding="utf-8", errors="replace")[:500]
                    except OSError:
                        continue
                    if head.startswith("---\n") and "format_version" in head:
                        adopted += 1
                        lane_adopted = True
                        break
            except OSError:
                continue
    pct = adopted / n_lanes * 100.0
    return pct, {"adopted_lanes": adopted, "total_lanes": n_lanes, "pct": round(pct, 1)}


_WEIGHTS = {
    "index_present": 15,
    "embeddings_present": 15,
    "layer_coverage": 10,
    "recall_works": 15,
    "vector_works": 10,
    "rotation_healthy": 10,
    "adoption": 25,
}

_RUNNERS = {
    "index_present": _sub_index,
    "embeddings_present": _sub_embeddings,
    "layer_coverage": _sub_layer_coverage,
    "recall_works": _sub_recall,
    "vector_works": _sub_vector,
    "rotation_healthy": _sub_rotation,
    "adoption": _sub_adoption,
}


def health(root: Path) -> dict:
    """Run every sub-score, weight + aggregate, return composite + breakdown."""
    root = Path(root)
    sub_scores: dict = {}
    weighted_sum = 0.0
    for name, runner in _RUNNERS.items():
        try:
            score, detail = runner(root)
        except Exception as exc:  # noqa: BLE001 -- per-sub-score guard
            score, detail = 0.0, {"error": f"{type(exc).__name__}: {exc}"}
        sub_scores[name] = {"score": round(score, 1), "weight": _WEIGHTS[name], "detail": detail}
        weighted_sum += score * _WEIGHTS[name] / 100.0
    return {
        "score": round(weighted_sum, 1),
        "max_score": 100,
        "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sub_scores": sub_scores,
    }


def health_grade(score: float) -> str:
    """Letter-grade a numeric score for at-a-glance reporting."""
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "F"
