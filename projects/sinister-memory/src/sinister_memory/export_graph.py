# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: graph export for Sinister Mind D3 visualization.

P14 from iter-3 plan: render the memory graph (nodes + typed edges) as JSON
so Sinister Mind's force-directed graph can ingest it natively.

Output schema (D3-compatible):
  {
    "nodes": [
      {"id": "<memory_id>", "layer": "...", "slug": "...", "snippet": "...",
       "category": "...", "confidence": 0.85, "ts_utc": "..."}
      ...
    ],
    "edges": [
      {"src": "...", "dst": "...", "kind": "Supersedes", "weight": 0.8, "reason": "..."}
      ...
    ],
    "meta": {"generated_at": "...", "node_count": N, "edge_count": M,
             "from_db": "<path>"}
  }

Public API:
  export_graph(root, db_path, out_path, layers=None) -> dict (stats)
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence


def _read_v2_frontmatter(path: str) -> dict:
    """Best-effort extract category + confidence from a v2 frontmatter file."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    out: dict = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip().lower()
            if k in {"category", "confidence", "trust", "format_version"}:
                out[k] = v.strip()
    return out


def export_graph(
    root: Path,
    db_path: Path,
    out_path: Path,
    layers: Optional[Sequence[str]] = None,
    limit_nodes: int = 5000,
) -> dict:
    """Export nodes + edges to a Sinister-Mind-compatible JSON file.

    Args:
      root        : Sanctum root
      db_path     : FTS5 index.db (contains both `memories` and `edges` tables)
      out_path    : output .json path
      layers      : optional restrict to one or more layers
      limit_nodes : safety cap

    Returns: {nodes: N, edges: M, written_to: <path>}.
    """
    db_path = Path(db_path)
    out_path = Path(out_path)
    if not db_path.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps({"nodes": [], "edges": [], "meta": {"error": "db not found"}}),
            encoding="utf-8",
        )
        return {"nodes": 0, "edges": 0, "written_to": str(out_path), "error": "db not found"}

    conn = sqlite3.connect(str(db_path))
    try:
        # Nodes
        sql = "SELECT DISTINCT layer, slug, path, line, snippet FROM memories"
        params: list = []
        if layers:
            placeholders = ",".join("?" for _ in layers)
            sql += f" WHERE layer IN ({placeholders})"
            params.extend(layers)
        sql += f" LIMIT {int(limit_nodes)}"
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    nodes: list[dict] = []
    seen: set[str] = set()
    for layer, slug, path, line, snippet in rows:
        nid = f"{layer}:{path}:{line}"
        if nid in seen:
            continue
        seen.add(nid)
        fm = _read_v2_frontmatter(path) if "per-agent" in (path or "") else {}
        nodes.append({
            "id": nid,
            "layer": layer,
            "slug": slug or "",
            "path": path,
            "line": line,
            "snippet": (snippet or "")[:240],
            "category": fm.get("category", ""),
            "confidence": fm.get("confidence", ""),
            "trust": fm.get("trust", ""),
        })

    # Edges -- both legacy supersedes and typed edges
    edges: list[dict] = []
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            for r in conn.execute("SELECT src_id, dst_id, kind, weight, reason, ts_utc FROM edges"):
                edges.append({
                    "src": r[0],
                    "dst": r[1],
                    "kind": r[2],
                    "weight": r[3],
                    "reason": r[4] or "",
                    "ts_utc": r[5],
                })
        finally:
            conn.close()
    except sqlite3.OperationalError:
        pass

    try:
        conn = sqlite3.connect(str(db_path))
        try:
            for r in conn.execute("SELECT new_id, old_id, reason, ts_utc FROM supersedes"):
                edges.append({
                    "src": r[0],
                    "dst": r[1],
                    "kind": "Supersedes",
                    "weight": None,
                    "reason": r[2] or "",
                    "ts_utc": r[3],
                })
        finally:
            conn.close()
    except sqlite3.OperationalError:
        pass

    payload = {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "from_db": str(db_path),
            "schema_version": 1,
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"nodes": len(nodes), "edges": len(edges), "written_to": str(out_path)}
