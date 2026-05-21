# Author: RKOJ-ELENO :: 2026-05-21
"""Filesystem-polling state — heartbeats, inbox, brain, projects, devices.

A lightweight pull-only model. No daemons, no FastAPI. The Qt timers tick every
N seconds and the widgets read the latest snapshot.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
SHARED_MEMORY = SANCTUM_ROOT / "_shared-memory"
HEARTBEATS_DIR = SHARED_MEMORY / "heartbeats"
INBOX_DIR = SHARED_MEMORY / "inbox"
KNOWLEDGE_DIR = SHARED_MEMORY / "knowledge"
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"


@dataclass
class Project:
    key: str
    display: str
    tag: str = ""
    root: str = ""


def load_projects() -> list[Project]:
    """Read projects.json and return the project list."""
    try:
        with open(PROJECTS_JSON, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        out: list[Project] = []
        for p in data.get("projects", []):
            out.append(Project(
                key=p.get("key", ""),
                display=p.get("display", p.get("key", "")),
                tag=p.get("tag", ""),
                root=p.get("root", ""),
            ))
        return out
    except Exception:
        return []


@dataclass
class Heartbeat:
    slug: str
    agent: str
    last_seen_iso: str = ""
    last_seen_age_s: float = 0.0
    online: bool = False


def load_heartbeats(stale_after_s: float = 600.0) -> list[Heartbeat]:
    """Scan heartbeats/*.json and bucket by age."""
    out: list[Heartbeat] = []
    if not HEARTBEATS_DIR.exists():
        return out
    now = time.time()
    for fp in HEARTBEATS_DIR.glob("*.json"):
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            mtime = fp.stat().st_mtime
            age = now - mtime
            out.append(Heartbeat(
                slug=fp.stem,
                agent=data.get("agent") or data.get("agent_display") or data.get("agent_identity") or fp.stem,
                last_seen_iso=data.get("ts") or data.get("timestamp") or "",
                last_seen_age_s=age,
                online=age <= stale_after_s,
            ))
        except Exception:
            continue
    return out


def count_inbox_messages() -> int:
    """Count unread JSON messages across the inbox tree."""
    if not INBOX_DIR.exists():
        return 0
    count = 0
    try:
        for fp in INBOX_DIR.rglob("*.json"):
            if "_archive" in fp.parts:
                continue
            count += 1
    except Exception:
        pass
    return count


def count_brain_entries() -> int:
    """Count knowledge/*.md files."""
    if not KNOWLEDGE_DIR.exists():
        return 0
    try:
        return sum(1 for _ in KNOWLEDGE_DIR.glob("*.md"))
    except Exception:
        return 0


@dataclass
class Device:
    serial: str
    state: str = "device"
    model: str = ""
    transport: str = "usb"


def list_adb_devices(timeout_s: float = 5.0) -> list[Device]:
    """Run `adb devices -l` and parse the output.

    Returns empty list on any failure (adb not installed, no devices, etc.).
    """
    out: list[Device] = []
    try:
        proc = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True, text=True, timeout=timeout_s,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for line in proc.stdout.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial = parts[0]
            state = parts[1]
            model = ""
            transport = "usb"
            for chunk in parts[2:]:
                if chunk.startswith("model:"):
                    model = chunk.split(":", 1)[1]
                elif chunk.startswith("transport_id:"):
                    transport = "tcp" if ":" in serial else "usb"
            out.append(Device(serial=serial, state=state, model=model, transport=transport))
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    return out


def adb_shell(serial: str, cmd: str, timeout_s: float = 10.0) -> str:
    """Run `adb -s <serial> shell <cmd>` and return stdout/stderr concatenated."""
    try:
        proc = subprocess.run(
            ["adb", "-s", serial, "shell", cmd],
            capture_output=True, text=True, timeout=timeout_s,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = proc.stdout
        if proc.stderr:
            out += ("\n" + proc.stderr) if out else proc.stderr
        return out.strip()
    except FileNotFoundError:
        return "[error] adb not installed or not on PATH"
    except subprocess.TimeoutExpired:
        return f"[error] adb shell timed out after {timeout_s}s"
    except Exception as exc:
        return f"[error] {exc}"


def adb_logcat_tail(serial: str, lines: int = 50, timeout_s: float = 4.0) -> str:
    """Tail the last N logcat lines for a device."""
    try:
        proc = subprocess.run(
            ["adb", "-s", serial, "logcat", "-d", "-t", str(lines)],
            capture_output=True, text=True, timeout=timeout_s,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return proc.stdout
    except FileNotFoundError:
        return "[error] adb not on PATH"
    except subprocess.TimeoutExpired:
        return "[error] logcat timed out"
    except Exception as exc:
        return f"[error] {exc}"


def active_projects() -> list[str]:
    """Return unique project_keys with at least one live agent.

    Placeholder: until AgentsView/SinisterWindow wires its live registry in,
    return ["sanctum"] so the folder-tab strip has at least one chip.
    The AgentsView code overrides this by reading its own `_cards` map.
    """
    return ["sanctum"]


@dataclass
class CounterSnapshot:
    agents_online: int = 0
    agents_total: int = 0
    inbox_count: int = 0
    brain_count: int = 0
    phones_online: int = 0
    phones_offline: int = 0
    phones_needs_auth: int = 0
    phones_armed: int = 0  # RKA armed; placeholder logic
    vault_used_pct: float = 0.0
    pending_requests: int = 0
    heartbeats: list[Heartbeat] = field(default_factory=list)


def snapshot() -> CounterSnapshot:
    """Single read across heartbeats + inbox + brain + adb."""
    snap = CounterSnapshot()
    snap.heartbeats = load_heartbeats()
    snap.agents_total = len(snap.heartbeats)
    snap.agents_online = sum(1 for h in snap.heartbeats if h.online)
    snap.inbox_count = count_inbox_messages()
    snap.brain_count = count_brain_entries()
    devices = list_adb_devices()
    snap.phones_online = sum(1 for d in devices if d.state == "device")
    snap.phones_offline = sum(1 for d in devices if d.state == "offline")
    snap.phones_needs_auth = sum(1 for d in devices if d.state == "unauthorized")
    snap.phones_armed = snap.phones_online  # treat all online as armed by default
    # Vault used % — read sinister-vault status if available, otherwise 0.
    try:
        vault_dir = Path(r"D:\sinister-vault")
        if vault_dir.exists():
            stat = os.statvfs(str(vault_dir)) if hasattr(os, "statvfs") else None
            if stat:
                total = stat.f_blocks * stat.f_frsize
                avail = stat.f_bavail * stat.f_frsize
                if total > 0:
                    snap.vault_used_pct = (1 - avail / total) * 100
            else:
                import shutil
                usage = shutil.disk_usage(str(vault_dir))
                if usage.total > 0:
                    snap.vault_used_pct = (1 - usage.free / usage.total) * 100
    except Exception:
        pass
    # Pending requests — count messages in inbox/sanctum/ (operator-facing)
    try:
        op_dir = INBOX_DIR / "sanctum"
        if op_dir.exists():
            snap.pending_requests = sum(1 for fp in op_dir.glob("*.json") if "_archive" not in fp.parts)
    except Exception:
        pass
    return snap
