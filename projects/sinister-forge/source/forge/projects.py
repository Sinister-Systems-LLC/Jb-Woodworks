# Sinister Forge :: projects.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"


@dataclass(frozen=True, slots=True)
class Project:
    key: str
    display: str
    tag: str
    root: str
    session_start: str
    claude_md: str
    github: str


def load_projects() -> list[Project]:
    if not PROJECTS_JSON.exists():
        return []
    try:
        data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[Project] = []
    for p in data.get("projects", []):
        out.append(Project(
            key=p.get("key", ""),
            display=p.get("display", ""),
            tag=p.get("tag", ""),
            root=p.get("root", ""),
            session_start=p.get("session_start", ""),
            claude_md=p.get("claude_md", ""),
            github=p.get("github", ""),
        ))
    return out


def get_project(key: str) -> Project | None:
    for p in load_projects():
        if p.key == key:
            return p
    return None
