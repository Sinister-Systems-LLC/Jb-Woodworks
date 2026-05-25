#!/usr/bin/env python3
"""project_manager.py -- canonical CREATE / RECALL / CATEGORIZE for Sanctum projects.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 (verbatim):
    "make sure the system has a place for a project create or project recall
     handling that agents will find and know if i ask them to do either of
     them. auto add and catergories all projects to eve exe"

THE SINGLE PLACE every fleet agent looks when the operator says:
  * "create a new project for X"           ->  --create
  * "remember the project I was doing on Y"->  --recall "Y"
  * "what projects do we have"             ->  --list
  * "categorize all projects"              ->  --categorize

WHAT IT DOES:

--create <key> [--display <name>] [--tag <one-liner>] [--tier <1-4>] [--github <slug>]
    1. Scaffolds projects/<key>/ with README.md + CLAUDE.md + PROGRESS template
    2. Appends an entry to automations/session-templates/projects.json
    3. Adds key to picker.visible_keys (auto-categorized into the right section)
    4. Sets default_modes.loop="relentless" + swarm=true (default doctrine)
    5. Sets github=Sinister-Sanctum unless --github overrides (single-repo policy)
    6. Writes spawn-detection: creates _shared-memory/heartbeats/<slug>.json stub
    7. Optionally adds sibling links per --sibling argument

--recall <query>
    Searches across:
      - projects.json (key / display / tag fields)
      - _shared-memory/PROGRESS/<display>.md (most-recent rows)
      - _shared-memory/heartbeats/<slug>.json (last-active ts)
      - _shared-memory/operator-utterances.jsonl (mentions)
      - _shared-memory/knowledge/ (any brain doctrine for that project)
    Returns top-N matches with: last-active, current focus, branch, agent-name.

--list [--tier N] [--category <name>]
    Print every registered project + status (active heartbeat / dead / archived).

--categorize
    Auto-categorize all projects using rule table (keyword-based) and update
    picker.categories[] in projects.json.

--add-to-picker <key>
    Add an existing project key to picker.visible_keys (auto-categorize).

CATEGORIZATION RULES (keyword -> category):
    sanctum / overseer / custodian / memory / sleight   -> "Sanctum + Core"
    api / sdk / wrapper / emulator                       -> "Tooling + API"
    kernel / panel / chatbot / freeze / generator        -> "Sinister Systems"
    woodworks / showmasters / letstext / compliance      -> "Client Sites"
    term / theme / ancestral                             -> "Sinister Term"
    overseer                                             -> "Overseer"
    otherwise                                            -> "Other"

DOCTRINE: _shared-memory/knowledge/project-create-recall-handler-doctrine-2026-05-25.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
PROJECTS_DIR = SANCTUM_ROOT / "projects"
PROGRESS_DIR = SANCTUM_ROOT / "_shared-memory" / "PROGRESS"
HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
UTTERANCES = SANCTUM_ROOT / "_shared-memory" / "operator-utterances.jsonl"
KNOWLEDGE_DIR = SANCTUM_ROOT / "_shared-memory" / "knowledge"

CATEGORIZE_RULES = [
    ("Sanctum + Core", ["sanctum", "custodian", "memory", "sleight", "imessage"]),
    ("Tooling + API",  ["api", "sdk", "wrapper", "emulator", "rkoj"]),
    ("Client Sites",   ["woodworks", "showmasters", "letstext", "compliance"]),
    ("Sinister Term",  ["term", "ancestral", "remotion", "theme"]),
    ("Overseer",       ["overseer"]),
    ("Sinister Systems", ["kernel", "panel", "chatbot", "freeze", "generator", "snap", "tiktok", "bumble", "jkor", "quantum", "jbw", "os"]),
]


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_projects() -> dict:
    try:
        return json.loads(PROJECTS_JSON.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"version": 1, "projects": [], "picker": {"visible_keys": [], "categories": []}}


def save_projects(data: dict) -> None:
    PROJECTS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def categorize_one(key: str, display: str = "", tag: str = "") -> str:
    """Return the category label for a project based on rule table."""
    haystack = f"{key} {display} {tag}".lower()
    for label, keywords in CATEGORIZE_RULES:
        for kw in keywords:
            if kw in haystack:
                return label
    return "Other"


def categorize_all() -> dict:
    """Walk every project in projects.json and rebuild picker.categories[]."""
    data = load_projects()
    buckets: dict[str, list[str]] = {}
    for label, _ in CATEGORIZE_RULES:
        buckets[label] = []
    buckets["Other"] = []
    visible = (data.get("picker") or {}).get("visible_keys") or []
    for p in data.get("projects", []):
        key = p.get("key")
        if not key or key not in visible:
            continue
        cat = categorize_one(key, p.get("display", ""), p.get("tag", ""))
        buckets.setdefault(cat, []).append(key)
    cats = [{"label": lbl, "keys": keys} for lbl, keys in buckets.items() if keys]
    data.setdefault("picker", {})["categories"] = cats
    save_projects(data)
    return {"categories": cats, "total_projects": len(visible)}


def create_project(key: str, display: str | None = None, tag: str | None = None,
                   tier: int = 3, github: str | None = None,
                   siblings: list[str] | None = None, no_scaffold: bool = False) -> dict:
    """Scaffold + register a new project lane."""
    if not re.match(r"^[a-z0-9][-a-z0-9]*$", key):
        return {"ok": False, "error": f"invalid key (lowercase + dashes only): {key!r}"}

    data = load_projects()
    if any(p.get("key") == key for p in data.get("projects", [])):
        return {"ok": False, "error": f"project '{key}' already exists in projects.json"}

    display = display or key.replace("-", " ").title()
    tag = tag or f"{display} project lane"
    proj_root = PROJECTS_DIR / key

    if not no_scaffold:
        proj_root.mkdir(parents=True, exist_ok=True)
        (proj_root / "README.md").write_text(
            f"# {display}\n\n**Author:** RKOJ-ELENO :: {utc_iso()[:10]}\n\n{tag}\n\n"
            f"Scaffolded by `automations/project_manager.py --create {key}`.\n\n"
            f"## Status\nP0 scaffold — fill in MISSION + WHO + WHAT here.\n",
            encoding="utf-8",
        )
        (proj_root / "CLAUDE.md").write_text(
            f"# CLAUDE.md — {display}\n\n**Author:** RKOJ-ELENO :: {utc_iso()[:10]}\n\n"
            f"Per-lane CLAUDE.md for the `{key}` project. Inherits sanctum-wide doctrine\n"
            f"from `D:\\Sinister Sanctum\\CLAUDE.md`. Add lane-specific rules below.\n\n"
            f"## Lane scope\n- Tag: {tag}\n- Tier: T{tier}\n- Sibling lanes: {', '.join(siblings or []) or '(none)'}\n",
            encoding="utf-8",
        )
        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        (PROGRESS_DIR / f"{display}.md").write_text(
            f"# PROGRESS — {display}\n\n_Append-only progress log; newest on top._\n\n"
            f"## {utc_iso()} — Scaffold\nProject scaffolded via project_manager.py.\n",
            encoding="utf-8",
        )

    entry = {
        "key": key,
        "display": display,
        "tag": tag,
        "root": str(proj_root).replace("/", "\\"),
        "session_start": "",
        "claude_md": str(proj_root / "CLAUDE.md").replace("/", "\\"),
        "github": github or "Sinister-Systems-LLC/Sinister-Sanctum",
        "tier": tier,
        "default_modes": {"swarm": True, "loop": "relentless", "loop_relentless": True},
    }
    if siblings:
        entry["siblings"] = siblings
    data.setdefault("projects", []).append(entry)
    visible = (data.setdefault("picker", {})).setdefault("visible_keys", [])
    if key not in visible:
        visible.append(key)
    save_projects(data)
    cat_result = categorize_all()

    # Heartbeat stub so spawn detector knows project exists
    HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    stub = HEARTBEAT_DIR / f"{key}.json"
    if not stub.exists():
        stub.write_text(json.dumps({
            "slug": key, "display": display, "created_utc": utc_iso(),
            "status": "scaffolded", "last_seen_utc": None,
        }, indent=2), encoding="utf-8")

    return {
        "ok": True, "key": key, "display": display, "tier": tier,
        "github": entry["github"], "category": categorize_one(key, display, tag),
        "scaffolded_at": str(proj_root) if not no_scaffold else None,
        "siblings": siblings or [],
    }


def recall(query: str, max_results: int = 5) -> dict:
    """Search every project surface for `query`. Return ranked matches."""
    q = query.lower().strip()
    if not q:
        return {"ok": False, "error": "empty query"}

    data = load_projects()
    matches: list[dict] = []
    for p in data.get("projects", []):
        score = 0
        key = (p.get("key") or "").lower()
        display = (p.get("display") or "").lower()
        tag = (p.get("tag") or "").lower()
        if q in key: score += 10
        if q in display: score += 8
        if q in tag: score += 5

        # Heartbeat (recency boost)
        hb_path = HEARTBEAT_DIR / f"{p.get('key')}.json"
        last_seen = None
        if hb_path.exists():
            try:
                hb = json.loads(hb_path.read_text(encoding="utf-8"))
                last_seen = hb.get("last_seen_utc") or hb.get("created_utc")
                age_h = None
                if last_seen:
                    try:
                        dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                        age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                        if age_h < 1: score += 5
                        elif age_h < 24: score += 3
                    except Exception:
                        pass
            except Exception:
                pass

        # PROGRESS file scan (cheap — last 50 lines)
        prog = PROGRESS_DIR / f"{p.get('display', '')}.md"
        prog_hit = None
        if prog.exists():
            try:
                txt = prog.read_text(encoding="utf-8", errors="replace")
                if q in txt.lower():
                    score += 4
                    # First matching line for context
                    for line in txt.splitlines()[:200]:
                        if q in line.lower():
                            prog_hit = line.strip()[:120]
                            break
            except Exception:
                pass

        if score > 0:
            matches.append({
                "key": p.get("key"),
                "display": p.get("display"),
                "tag": p.get("tag"),
                "tier": p.get("tier"),
                "github": p.get("github"),
                "score": score,
                "last_seen_utc": last_seen,
                "progress_hit": prog_hit,
            })

    # Also search recent operator-utterances for mentions
    if UTTERANCES.exists():
        try:
            recent = UTTERANCES.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]
            for line in recent:
                try:
                    row = json.loads(line)
                    txt = (row.get("text") or "").lower()
                    if q in txt:
                        # Boost any matches whose key shows up in this utterance
                        for m in matches:
                            if m["key"] and m["key"] in txt:
                                m["score"] += 2
                                m["operator_mention"] = row.get("ts_utc") or row.get("ts")
                except Exception:
                    continue
        except Exception:
            pass

    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"ok": True, "query": query, "results": matches[:max_results], "total_scored": len(matches)}


def list_projects(tier: int | None = None, category: str | None = None) -> dict:
    data = load_projects()
    out: list[dict] = []
    for p in data.get("projects", []):
        if tier and int(p.get("tier") or 99) != tier:
            continue
        cat = categorize_one(p.get("key", ""), p.get("display", ""), p.get("tag", ""))
        if category and cat.lower() != category.lower():
            continue
        hb = HEARTBEAT_DIR / f"{p.get('key')}.json"
        last_seen = None
        if hb.exists():
            try:
                last_seen = json.loads(hb.read_text(encoding="utf-8")).get("last_seen_utc")
            except Exception:
                pass
        out.append({
            "key": p.get("key"), "display": p.get("display"), "tier": p.get("tier"),
            "category": cat, "github": p.get("github"),
            "last_seen_utc": last_seen,
        })
    return {"ok": True, "count": len(out), "projects": out}


def add_to_picker(key: str) -> dict:
    data = load_projects()
    if not any(p.get("key") == key for p in data.get("projects", [])):
        return {"ok": False, "error": f"project '{key}' not in projects.json (use --create first)"}
    visible = (data.setdefault("picker", {})).setdefault("visible_keys", [])
    if key in visible:
        return {"ok": True, "msg": "already in picker", "key": key}
    visible.append(key)
    save_projects(data)
    cat = categorize_all()
    return {"ok": True, "added": key, "categories": cat["categories"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="project_manager")
    sub = ap.add_subparsers(dest="cmd", required=False)

    c = sub.add_parser("create", help="scaffold + register a new project")
    c.add_argument("key")
    c.add_argument("--display")
    c.add_argument("--tag")
    c.add_argument("--tier", type=int, default=3)
    c.add_argument("--github")
    c.add_argument("--sibling", action="append", default=[])
    c.add_argument("--no-scaffold", action="store_true")

    r = sub.add_parser("recall", help="search projects + heartbeats + PROGRESS + utterances")
    r.add_argument("query")
    r.add_argument("--max", type=int, default=5)

    l = sub.add_parser("list", help="list all registered projects")
    l.add_argument("--tier", type=int)
    l.add_argument("--category")

    cat = sub.add_parser("categorize", help="auto-rebuild picker.categories from rules")

    ap_add = sub.add_parser("add-to-picker", help="add an existing project to picker.visible_keys")
    ap_add.add_argument("key")

    # Top-level flag aliases so operator can type either form
    ap.add_argument("--create", dest="create_alias")
    ap.add_argument("--recall", dest="recall_alias")
    ap.add_argument("--list", action="store_true", dest="list_alias")
    ap.add_argument("--categorize", action="store_true", dest="categorize_alias")
    ap.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    out: dict
    if args.cmd == "create":
        out = create_project(args.key, args.display, args.tag, args.tier,
                              args.github, args.sibling, args.no_scaffold)
    elif args.cmd == "recall":
        out = recall(args.query, args.max)
    elif args.cmd == "list":
        out = list_projects(args.tier, args.category)
    elif args.cmd == "categorize":
        out = categorize_all()
    elif args.cmd == "add-to-picker":
        out = add_to_picker(args.key)
    elif args.create_alias:
        out = create_project(args.create_alias)
    elif args.recall_alias:
        out = recall(args.recall_alias)
    elif args.list_alias:
        out = list_projects()
    elif args.categorize_alias:
        out = categorize_all()
    else:
        ap.print_help()
        return 1

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        if isinstance(out, dict):
            for k, v in out.items():
                print(f"  {k}: {v}")
        else:
            print(out)
    return 0 if (isinstance(out, dict) and out.get("ok", True)) else 2


if __name__ == "__main__":
    sys.exit(main())
