# Sinister Term :: swarm.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Multi-agent same-repo coordination — thin CLI surface composing the
# existing Sanctum-owned infrastructure (start-sinister-session.ps1 for
# spawn; _shared-memory/inbox/ for DMs; _shared-memory/cross-agent/ for
# broadcasts; heartbeats/ for live registry).
#
# jcode swarm parity per the operator directive 2026-05-21T11:55Z.
# Attribution per canonical-20 to Justin Huang's jcode (MIT).

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Optional


SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
SELF_SLUG = "sinister-term"
SELF_DISPLAY = "Sinister Term"
LAUNCHER_PS1 = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"


def _utc_ts_filename() -> str:
    return time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())


def _utc_ts_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def spawn(project_key: str) -> int:
    """Spawn a sibling agent into the given project lane. Delegates to the
    Sanctum-owned start-sinister-session.ps1 launcher.

    Returns 0 on success, non-zero on failure.
    """
    if not LAUNCHER_PS1.exists():
        print(f"launcher not found: {LAUNCHER_PS1}")
        return 1
    if platform.system() != "Windows":
        print("swarm spawn currently Windows-only (delegates to a .ps1)")
        return 1
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(LAUNCHER_PS1), "-Project", project_key,
    ]
    try:
        subprocess.Popen(cmd, cwd=str(SANCTUM_ROOT))
    except Exception as e:
        print(f"spawn failed: {e}")
        return 1
    print(f"spawned: {project_key}  (delegated to {LAUNCHER_PS1.name})")
    return 0


def list_agents() -> list[dict]:
    """Return a list of all sibling agents seen via heartbeats/.

    Each entry: { 'agent', 'age_min', 'marker' (●/○), 'cwd' }.
    """
    hb_dir = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
    if not hb_dir.exists():
        return []
    out: list[dict] = []
    now = time.time()
    for hb in sorted(hb_dir.glob("*.json")):
        try:
            data = json.loads(hb.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        age_min = max(0, int((now - hb.stat().st_mtime) // 60))
        out.append({
            "agent": data.get("agent", hb.stem),
            "age_min": age_min,
            "marker": "●" if age_min < 30 else "○",
            "cwd": data.get("cwd"),
            "alive": data.get("alive"),
        })
    return out


def dm(target_slug: str, message: str) -> Optional[Path]:
    """Drop an [ASK] in target's inbox. Returns the file path or None if
    target inbox doesn't exist.
    """
    target_dir = SANCTUM_ROOT / "_shared-memory" / "inbox" / target_slug
    if not target_dir.exists():
        return None
    ts_iso = _utc_ts_iso()
    ts_file = _utc_ts_filename()
    body = {
        "_author": "RKOJ-ELENO :: 2026-05-21",
        "tag": "[ASK]",
        "from": SELF_SLUG,
        "from_display": SELF_DISPLAY,
        "to": target_slug,
        "ts_utc": ts_iso,
        "subject": message[:80],
        "message": message,
        "via": "sinister swarm dm",
    }
    path = target_dir / f"{ts_file}-dm-from-{SELF_SLUG}.json"
    path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return path.relative_to(SANCTUM_ROOT)


def broadcast(message: str) -> Path:
    """Write a [BROADCAST] message to _shared-memory/cross-agent/ for all
    sibling agents to see. Returns the file path.
    """
    ca_dir = SANCTUM_ROOT / "_shared-memory" / "cross-agent"
    ca_dir.mkdir(parents=True, exist_ok=True)
    ts_file = _utc_ts_filename()
    path = ca_dir / f"{ts_file}-sinister-term-broadcast.md"
    body = [
        f"# {ts_file} — Sinister Term → ALL LANES: [BROADCAST]",
        "",
        "> **Author:** RKOJ-ELENO :: 2026-05-21",
        "> **Via:** `sinister swarm broadcast`",
        "",
        message,
        "",
        "## Asks (none — informational broadcast)",
        "",
        "Reply via your usual cross-agent channel if relevant.",
    ]
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path.relative_to(SANCTUM_ROOT)
