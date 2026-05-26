#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""Per-lane memory wiring audit (D8.4 from master plan).

For each of the project lanes in projects.json, measure:
  save?              -- per-agent/<slug>/ has a v2 frontmatter file in last 14d
  recall?            -- BM25 recall on slug returns >=1 hit
  embed?             -- embeddings.db has >=1 row tagged with slug
  superseded?        -- supersede edges table has >=1 row mentioning slug
  progress_fresh?    -- PROGRESS/<lane>.md mtime within 7d
  contradiction?     -- (FUTURE) spawn-phrase contains SINISTER_MEMORY_CONTRADICTIONS
  progress_size_kb   -- live size after R4 rotation
  embed_count        -- # embeddings for this lane
  brain_mentions     -- # brain entries mentioning the slug

Writes the report to `_shared-memory/audits/per-lane-memory-wiring-<utc>.md`.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _load_projects(projects_json: Path) -> list[dict]:
    with projects_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("projects", [])


def _per_agent_v2_in_last_days(root: Path, slug: str, days: int = 14) -> int:
    """Iter-14 fix: auto_save writes to namespaced `_shared-memory/sinister-memory/per-agent/<slug>/`,
    but fleet conventions may also use `_shared-memory/per-agent/<slug>/`. Check BOTH.
    """
    candidates = [
        root / "_shared-memory" / "sinister-memory" / "per-agent" / slug,  # canonical (auto_save iter-2)
        root / "_shared-memory" / "per-agent" / slug,                       # fleet-root variant
    ]
    cutoff = time.time() - days * 86400
    count = 0
    for d in candidates:
        if not d.is_dir():
            continue
        try:
            for p in d.iterdir():
                if p.is_file() and p.suffix.lower() == ".md":
                    try:
                        if p.stat().st_mtime >= cutoff:
                            try:
                                head = p.read_text(encoding="utf-8", errors="replace")[:500]
                            except OSError:
                                continue
                            if head.startswith("---\n") and "format_version" in head:
                                count += 1
                    except OSError:
                        continue
        except OSError:
            continue
    return count


def _recall_count(db_path: Path, slug: str, limit: int = 5) -> int:
    if not db_path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            rows = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE memories MATCH ? LIMIT ?",
                (f'"{slug}"', limit),
            ).fetchone()
        finally:
            conn.close()
        return int(rows[0]) if rows else 0
    except sqlite3.OperationalError:
        return 0


def _embed_count(emb_db: Path, slug: str) -> int:
    if not emb_db.exists():
        return 0
    try:
        conn = sqlite3.connect(str(emb_db))
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM embeddings WHERE slug = ? OR path LIKE ?",
                (slug, f"%{slug}%"),
            ).fetchone()
        finally:
            conn.close()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return 0


def _supersede_count(db_path: Path, slug: str) -> int:
    if not db_path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(db_path))
        n = 0
        for tbl, cols in [("edges", ("src_id", "dst_id")), ("supersedes", ("new_id", "old_id"))]:
            try:
                for col in cols:
                    row = conn.execute(
                        f"SELECT COUNT(*) FROM {tbl} WHERE {col} LIKE ?", (f"%{slug}%",)
                    ).fetchone()
                    if row:
                        n += int(row[0])
            except sqlite3.OperationalError:
                continue
        conn.close()
        return n
    except sqlite3.OperationalError:
        return 0


def _progress_size_kb(root: Path, display_name: str) -> Optional[int]:
    # PROGRESS/<display>.md naming. Try a few common variants.
    candidates = [
        root / "_shared-memory" / "PROGRESS" / f"{display_name}.md",
        root / "_shared-memory" / "PROGRESS" / f"{display_name.replace(' ', '-').lower()}.md",
        root / "_shared-memory" / "PROGRESS" / f"{display_name.lower().replace(' ', '_')}.md",
    ]
    for c in candidates:
        if c.exists():
            return c.stat().st_size // 1024
    return None


def _progress_fresh(root: Path, display_name: str, days: int = 7) -> bool:
    candidates = [
        root / "_shared-memory" / "PROGRESS" / f"{display_name}.md",
        root / "_shared-memory" / "PROGRESS" / f"{display_name.replace(' ', '-').lower()}.md",
        root / "_shared-memory" / "PROGRESS" / f"{display_name.lower().replace(' ', '_')}.md",
    ]
    cutoff = time.time() - days * 86400
    for c in candidates:
        if c.exists() and c.stat().st_mtime >= cutoff:
            return True
    return False


def _brain_mentions(root: Path, slug: str) -> int:
    d = root / "_shared-memory" / "knowledge"
    if not d.is_dir():
        return 0
    n = 0
    needle = slug.lower()
    for p in d.iterdir():
        if p.is_file() and p.suffix.lower() == ".md":
            try:
                text = p.read_text(encoding="utf-8", errors="replace").lower()
            except OSError:
                continue
            if needle in text:
                n += 1
    return n


def _gap_priority(row: dict) -> str:
    """HIGH if recall + embed + save all 0; MED if any 2 are 0; LOW otherwise."""
    zeros = sum(1 for k in ("recall_hits", "embed_count", "save_v2_14d") if row[k] == 0)
    if zeros >= 3:
        return "HIGH"
    if zeros == 2:
        return "MED"
    if zeros == 1:
        return "LOW"
    return "OK"


def audit(root: Path, projects_json: Path) -> list[dict]:
    db_path = root / "_shared-memory" / "sinister-memory" / "index.db"
    emb_db = root / "_shared-memory" / "sinister-memory" / "embeddings.db"
    projects = _load_projects(projects_json)
    rows: list[dict] = []
    for proj in projects:
        slug = proj["key"]
        display = proj.get("display", slug)
        row = {
            "slug": slug,
            "display": display,
            "save_v2_14d": _per_agent_v2_in_last_days(root, slug, days=14),
            "recall_hits": _recall_count(db_path, slug, limit=5),
            "embed_count": _embed_count(emb_db, slug),
            "supersede_count": _supersede_count(db_path, slug),
            "progress_fresh_7d": _progress_fresh(root, display),
            "progress_kb": _progress_size_kb(root, display),
            "brain_mentions": _brain_mentions(root, slug),
        }
        row["gap_priority"] = _gap_priority(row)
        rows.append(row)
    return rows


def render_markdown(rows: list[dict]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = [
        "# Per-lane memory wiring audit",
        f"",
        f"**Author:** RKOJ-ELENO :: 2026-05-25 (sinister-memory lane, iter-9 D8.4)",
        f"**Generated:** {ts}",
        f"**Source script:** `projects/sinister-memory/scripts/audit_per_lane.py`",
        f"**Operator hard-canonical 2026-05-25T~13:25Z:** *\"create a plan to complete everything I said above and how you are going to audit and test all aspects of memory and deep dive into how you can improve it. full auditing starting with the main projects.\"*",
        f"",
        "## How to read",
        "",
        "- **save_v2_14d** -- count of v2-frontmatter files under `_shared-memory/per-agent/<slug>/` modified in the last 14 days. >=1 means the lane writes structured memory.",
        "- **recall_hits** -- BM25 hits when querying the slug as a literal. >=1 means agents recalling on this slug get something back.",
        "- **embed_count** -- rows in `embeddings.db` tagged with slug OR with the slug in the path. >=1 means vector recall works for this lane.",
        "- **supersede_count** -- typed edges (Supersedes/Contradicts/RelatesTo/...) mentioning slug. >0 means lane has been touched by the contradiction system.",
        "- **progress_fresh_7d** -- PROGRESS/<lane>.md mtime within 7 days.",
        "- **progress_kb** -- live PROGRESS file size in KB (after R4 rotation; >80 KB means rotation should fire next ambient pass).",
        "- **brain_mentions** -- brain entries mentioning the slug (should be >=1 for any active lane).",
        "- **gap_priority** -- HIGH if save+recall+embed are all 0; MED if 2 of 3; LOW if 1 of 3; OK if all >0.",
        "",
        "## Results",
        "",
        "| slug | save_v2_14d | recall_hits | embed_count | supersede | prog_fresh | prog_kb | brain | gap |",
        "|---|---:|---:|---:|---:|:---:|---:|---:|:---:|",
    ]
    # Sort: HIGH first, then by recall_hits asc (worst-recall first)
    sort_key = {"HIGH": 0, "MED": 1, "LOW": 2, "OK": 3}
    rows_sorted = sorted(rows, key=lambda r: (sort_key.get(r["gap_priority"], 9), r["recall_hits"]))
    for r in rows_sorted:
        out.append(
            f"| `{r['slug']}` | {r['save_v2_14d']} | {r['recall_hits']} | {r['embed_count']} | "
            f"{r['supersede_count']} | {'Y' if r['progress_fresh_7d'] else 'n'} | "
            f"{r['progress_kb'] if r['progress_kb'] is not None else '--'} | "
            f"{r['brain_mentions']} | **{r['gap_priority']}** |"
        )
    # Aggregates
    n = len(rows)
    high = sum(1 for r in rows if r["gap_priority"] == "HIGH")
    med = sum(1 for r in rows if r["gap_priority"] == "MED")
    low = sum(1 for r in rows if r["gap_priority"] == "LOW")
    ok = sum(1 for r in rows if r["gap_priority"] == "OK")
    out.extend([
        "",
        "## Aggregates",
        "",
        f"- Lanes total: **{n}**",
        f"- gap=OK (all 3 of save/recall/embed >0): **{ok}**",
        f"- gap=LOW (1 of 3 zero): **{low}**",
        f"- gap=MED (2 of 3 zero): **{med}**",
        f"- gap=HIGH (all 3 zero): **{high}**",
        "",
        "## Iter-10 fix actions (HIGH lanes first)",
        "",
        "For each HIGH lane, run the per-lane backfill (master plan SUB-C):",
        "1. `sinister-memory --root \"D:\\Sinister Sanctum\" index` (whole-tree, idempotent).",
        "2. `sinister-memory --root \"D:\\Sinister Sanctum\" embed-index --limit 200` (incremental kernel-vector pass; R8 IDF table when shipped).",
        "3. `sinister-memory --root \"D:\\Sinister Sanctum\" cluster-dedupe --apply --layer progress --threshold 0.85` (mark dupes).",
        "4. Write `_shared-memory/per-agent/<slug>/.memory-wired-2026-05-25.flag` sentinel.",
        "",
        "## Composes with",
        "",
        "- `_shared-memory/plans/sinister-memory-master-plan-2026-05-25/plan.md` (D8.4 is this script's charter)",
        "- `loop-relentless-pursuit-doctrine-2026-05-25` (audit runs as part of ambient consolidation)",
        "- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (numbers, not vibes)",
        "- `safe-quality-loops-doctrine-2026-05-24` (12 guardrails)",
        "",
    ])
    return "\n".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Per-lane memory wiring audit")
    p.add_argument("--root", default=r"D:\Sinister Sanctum")
    p.add_argument("--projects-json", default=None)
    p.add_argument("--out", default=None, help="output path; default _shared-memory/audits/per-lane-memory-wiring-<utc>.md")
    p.add_argument("--json", action="store_true", help="emit raw JSON instead of markdown")
    args = p.parse_args(argv)
    root = Path(args.root)
    projects_json = Path(args.projects_json) if args.projects_json else root / "automations" / "session-templates" / "projects.json"
    rows = audit(root, projects_json)
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    md = render_markdown(rows)
    if args.out:
        out_path = Path(args.out)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
        out_path = root / "_shared-memory" / "audits" / f"per-lane-memory-wiring-{ts}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"wrote {out_path} -- {len(rows)} lanes audited")
    return 0


if __name__ == "__main__":
    sys.exit(main())
