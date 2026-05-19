# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""Cycle points :: one-click project-state resume.

A cycle point is a JSON snapshot of an in-flight project session so the
operator can pause + resume from the same agent / model / mode / open
files later. Snapshots live under
`<sanctum_root>/_shared-memory/cycle-points/<project-slug>/<cycle-slug>.json`
and are catalogued in `_INDEX.md` for the human-readable view.

This module is the pure-Python persistence layer; FastAPI endpoints in
server.py drive it and the optional `resume_payload` helper composes the
body passed to `/api/launcher/spawn` so a resume is identical to a fresh
launch with the captured context pre-loaded.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "rkoj/cycle-point/v1"


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def cycle_dir(sanctum_root) -> Path:
    return Path(sanctum_root) / "_shared-memory" / "cycle-points"


def list_cycle_points(sanctum_root) -> list[dict]:
    """Return [{slug, project, name, note, created_at, file}] sorted recent-first."""
    base = cycle_dir(sanctum_root)
    if not base.exists():
        return []
    out: list[dict] = []
    for project_dir in base.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith("_"):
            for cf in project_dir.glob("*.json"):
                try:
                    d = json.loads(cf.read_text(encoding="utf-8"))
                    out.append({
                        "slug": d.get("slug", cf.stem),
                        "project": d.get("project", project_dir.name),
                        "name": d.get("name", ""),
                        "note": d.get("note", ""),
                        "created_at": d.get("created_at", ""),
                        "file": str(cf),
                    })
                except Exception:
                    continue
    out.sort(key=lambda x: x["created_at"], reverse=True)
    return out


def load_cycle(sanctum_root, slug: str) -> dict | None:
    """Load the first cycle-point JSON whose `slug` field matches."""
    base = cycle_dir(sanctum_root)
    if not base.exists():
        return None
    for p in base.rglob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("slug") == slug:
                return d
        except Exception:
            continue
    return None


def save_cycle(sanctum_root, payload: dict) -> dict:
    """Validate, normalise, write `<project>/<slug>.json`, append to _INDEX.md."""
    payload.setdefault("schema", SCHEMA)
    payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    if "slug" not in payload or not payload["slug"]:
        seed = payload.get("name") or str(int(time.time()))
        payload["slug"] = _slugify(seed) or f"cycle-{int(time.time())}"
    if "project" not in payload or not payload["project"]:
        agent = payload.get("agent") or {}
        payload["project"] = agent.get("name", "unknown") if isinstance(agent, dict) else "unknown"
    project_slug = _slugify(payload["project"]) or "unknown"
    base = cycle_dir(sanctum_root) / project_slug
    base.mkdir(parents=True, exist_ok=True)
    fp = base / f"{payload['slug']}.json"
    fp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _append_index(sanctum_root, payload, fp)
    return {"ok": True, "slug": payload["slug"], "file": str(fp)}


def delete_cycle(sanctum_root, slug: str) -> dict:
    """Delete every file whose JSON `slug` matches the given slug."""
    cp = load_cycle(sanctum_root, slug)
    if not cp:
        return {"ok": False, "error": "not found"}
    removed: list[str] = []
    base = cycle_dir(sanctum_root)
    for p in base.rglob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("slug") == slug:
                try:
                    p.unlink()
                    removed.append(str(p))
                except Exception:
                    continue
        except Exception:
            continue
    return {"ok": True, "removed": removed}


def _append_index(sanctum_root, payload: dict, fp: Path) -> None:
    idx = cycle_dir(sanctum_root) / "_INDEX.md"
    idx.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"| {payload.get('slug','')} | {payload.get('project','')} | "
        f"{payload.get('name','')} | {payload.get('created_at','')} | "
        f"{payload.get('note','')} |\n"
    )
    if not idx.exists():
        idx.write_text(
            "> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19\n\n"
            "# Cycle points :: index\n\n"
            "| Slug | Project | Name | Created | Note |\n|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    with idx.open("a", encoding="utf-8") as f:
        f.write(line)


def resume_payload(cp: dict) -> dict:
    """Build the `/api/launcher/spawn` body from a loaded cycle point."""
    agent = cp.get("agent") or {}
    context = cp.get("context") or {}
    files_hint = ""
    open_files = context.get("open_files") or []
    if open_files:
        files_hint = "First read these files: " + "; ".join(open_files) + ". "
    custom = (
        f"Resume cycle '{cp.get('name','')}'. "
        f"{files_hint}Continue from: {cp.get('note','')}"
    )
    return {
        "project": cp.get("project", ""),
        "mode": agent.get("mode", "dev"),
        "fast": bool(agent.get("fast", False)),
        "custom_prompt": custom,
    }
