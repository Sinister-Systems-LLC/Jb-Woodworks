#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""Generate per-lane briefing docs: one .md per project lane showing the
top-N recall hits + active per-agent saves + recent supersede edges.

Uses iter-6 R3 --lane recall slice. Output:
  _shared-memory/audits/per-lane-briefings/<slug>.md

Operator-facing: any new agent spawning into a lane can `cat` its briefing
file and get a one-page summary of what's known about that lane.
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
        return json.load(f).get("projects", [])


def _top_recall(slug: str, root: Path, limit: int = 5) -> list[dict]:
    """Use R3 --lane filter via direct call (no subprocess)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from sinister_memory import recall as _r
    db = root / "_shared-memory" / "sinister-memory" / "index.db"
    hits = _r.recall(slug, db, limit=limit, lane=slug, rrf=True)
    return [
        {"layer": h.layer, "path": h.path, "line": str(h.line), "snippet": (h.snippet or "")[:200]}
        for h in hits
    ]


def _per_agent_files(slug: str, root: Path, limit: int = 5) -> list[dict]:
    """List up to N most-recent per-agent v2-frontmatter files for slug."""
    out: list[dict] = []
    for d in (
        root / "_shared-memory" / "sinister-memory" / "per-agent" / slug,
        root / "_shared-memory" / "per-agent" / slug,
    ):
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if not (p.is_file() and p.suffix.lower() == ".md"):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            body = text
            if text.startswith("---\n"):
                end = text.find("\n---\n", 4)
                if end != -1:
                    body = text[end + 5:]
            out.append({
                "path": str(p),
                "mtime_iso": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                "head": body.strip().splitlines()[0][:120] if body.strip() else "(empty)",
            })
            if len(out) >= limit:
                return out
    return out


def _supersede_edges(slug: str, root: Path, limit: int = 5) -> list[dict]:
    """Recent supersede edges where slug appears in either side."""
    db = root / "_shared-memory" / "sinister-memory" / "index.db"
    if not db.exists():
        return []
    out: list[dict] = []
    try:
        conn = sqlite3.connect(str(db))
        for tbl, kind in [("edges", None), ("supersedes", "Supersedes")]:
            try:
                if tbl == "edges":
                    rows = conn.execute(
                        "SELECT src_id, dst_id, kind, reason, ts_utc FROM edges "
                        "WHERE src_id LIKE ? OR dst_id LIKE ? ORDER BY ts_utc DESC LIMIT ?",
                        (f"%{slug}%", f"%{slug}%", limit),
                    ).fetchall()
                    for r in rows:
                        out.append({"src": r[0], "dst": r[1], "kind": r[2], "reason": r[3] or "", "ts_utc": r[4]})
                else:
                    rows = conn.execute(
                        "SELECT new_id, old_id, reason, ts_utc FROM supersedes "
                        "WHERE new_id LIKE ? OR old_id LIKE ? ORDER BY ts_utc DESC LIMIT ?",
                        (f"%{slug}%", f"%{slug}%", limit),
                    ).fetchall()
                    for r in rows:
                        out.append({"src": r[0], "dst": r[1], "kind": "Supersedes", "reason": r[2] or "", "ts_utc": r[3]})
            except sqlite3.OperationalError:
                continue
        conn.close()
    except sqlite3.OperationalError:
        pass
    return out[:limit]


def render(slug: str, display: str, top: list[dict], saves: list[dict], edges: list[dict]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = [
        f"# Lane briefing :: {display} (`{slug}`)",
        "",
        f"**Generated:** {ts}",
        f"**Source script:** `projects/sinister-memory/scripts/generate_lane_briefings.py`",
        f"**Cold-start hint:** any agent spawning into this lane can `cat` this file for a 1-page status snapshot.",
        "",
        "## Top recall hits (RRF + IDF, --lane filtered)",
        "",
    ]
    if not top:
        out.append("_(no recall hits for this lane -- corpus may be sparse or slug-mismatch)_")
    else:
        for h in top:
            out.append(f"- **[{h['layer']}]** `{h['path']}:{h['line']}` -- {h['snippet']}")
    out += [
        "",
        f"## Per-agent saves (last {len(saves)})",
        "",
    ]
    if not saves:
        out.append("_(no v2-frontmatter saves -- lane has not called `sinister-memory save` yet; see sinister-memory-save-adoption-doctrine-2026-05-25)_")
    else:
        for s in saves:
            out.append(f"- `{s['path']}` ({s['mtime_iso']}) -- {s['head']}")
    out += [
        "",
        f"## Supersede/Contradicts edges ({len(edges)})",
        "",
    ]
    if not edges:
        out.append("_(no typed edges -- contradiction-gate not yet exercised for this lane)_")
    else:
        for e in edges:
            out.append(f"- `{e['kind']}` :: `{e['src']}` -> `{e['dst']}` ({e['ts_utc']}) -- {e['reason']}")
    out += [
        "",
        "## Composes with",
        "",
        "- `sinister-memory-master-plan-2026-05-25/plan.md` (the master plan that asked for this briefing)",
        "- `loop-relentless-pursuit-doctrine-2026-05-25` (briefings auto-regenerate in ambient consolidation)",
        "- `sinister-memory-save-adoption-doctrine-2026-05-25` (the doctrine that fixes empty per-agent saves)",
        "",
    ]
    return "\n".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Per-lane briefing generator")
    p.add_argument("--root", default=r"D:\Sinister Sanctum")
    p.add_argument("--projects-json", default=None)
    p.add_argument("--out-dir", default=None)
    p.add_argument("--lane", help="generate briefing for ONE lane only")
    p.add_argument("--top", type=int, default=5, help="top-N recall hits per lane")
    args = p.parse_args(argv)
    root = Path(args.root)
    projects_json = Path(args.projects_json) if args.projects_json else root / "automations" / "session-templates" / "projects.json"
    out_dir = Path(args.out_dir) if args.out_dir else root / "_shared-memory" / "audits" / "per-lane-briefings"
    out_dir.mkdir(parents=True, exist_ok=True)
    projects = _load_projects(projects_json)
    if args.lane:
        projects = [pr for pr in projects if pr["key"] == args.lane]
    n = 0
    for proj in projects:
        slug = proj["key"]
        display = proj.get("display", slug)
        try:
            top = _top_recall(slug, root, limit=args.top)
            saves = _per_agent_files(slug, root, limit=5)
            edges = _supersede_edges(slug, root, limit=5)
            md = render(slug, display, top, saves, edges)
            (out_dir / f"{slug}.md").write_text(md, encoding="utf-8")
            n += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {slug}: {type(exc).__name__}: {exc}")
            continue
    print(f"wrote {n} briefing(s) to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
