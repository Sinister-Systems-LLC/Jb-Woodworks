# Sinister Forge :: resume/point.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import asyncio
import json
import subprocess
from pathlib import Path

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
RESUME_POINTS_DIR = SANCTUM_ROOT / "_shared-memory" / "resume-points"
RESUME_POINT_WRITE_PS1 = SANCTUM_ROOT / "automations" / "resume-point-write.ps1"


def latest_resume_point(project_key: str) -> dict | None:
    proj_dir = RESUME_POINTS_DIR / project_key
    if not proj_dir.exists():
        return None
    files = sorted(proj_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception:
        return None


async def write_resume_point(project_key: str, agent_name: str, mode: str, focus: str = "") -> bool:
    if not RESUME_POINT_WRITE_PS1.exists():
        return False
    argv = [
        "powershell.exe",
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(RESUME_POINT_WRITE_PS1),
        "-SanctumRoot", str(SANCTUM_ROOT),
        "-ProjectKey", project_key,
        "-AgentName", agent_name,
        "-Mode", mode,
    ]
    if focus:
        argv.extend(["-FocusIntent", focus])
    try:
        await asyncio.create_subprocess_exec(
            *argv,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except Exception:
        return False


def pre_warm_reads(project_key: str) -> list[str]:
    rp = latest_resume_point(project_key)
    if not rp:
        return []
    return rp.get("pre_warm_reads", [])
