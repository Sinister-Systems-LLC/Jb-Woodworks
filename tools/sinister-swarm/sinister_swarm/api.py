# Sinister Sanctum :: sinister-swarm :: core API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
from __future__ import annotations
import hashlib, json, os, subprocess, time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "sinister.swarm.v1"
_AUTHOR = "RKOJ-ELENO :: 2026-05-21"
DEFAULT_SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
_root: Path = DEFAULT_SANCTUM_ROOT


def set_sanctum_root(p):
    global _root
    _root = Path(p)


def get_sanctum_root():
    return _root


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _shared_mem():
    return _root / "_shared-memory"


def _inbox(slug):
    d = _shared_mem() / "inbox" / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def _heartbeats_dir():
    return _shared_mem() / "heartbeats"


def _write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def _read_json(p):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def detect_my_slug():
    s = os.environ.get("SINISTER_AGENT_SLUG")
    if s:
        return s
    n = os.environ.get("SINISTER_AGENT_NAME")
    if n:
        return n.lower().replace(" ", "-")
    return "unknown-caller"


def dm(to_slug, message, *, tag="[MSG]", subject=None, from_slug=None):
    from_slug = from_slug or detect_my_slug()
    rec = {
        "_author": _AUTHOR,
        "schema_version": SCHEMA_VERSION,
        "tag": tag,
        "from": from_slug,
        "to": to_slug,
        "ts_utc": _now_iso(),
        "subject": subject or (message[:80] if isinstance(message, str) else "(dict)"),
        "message": message,
    }
    p = _inbox(to_slug) / f"{_now_iso()}-msg-from-{from_slug}.json"
    _write_json(p, rec)
    rec["_path"] = str(p)
    return rec


def broadcast(message, *, tag="[BROADCAST]", subject=None, exclude=None, use_mcp=True):
    exclude_set = set(exclude or [])
    from_slug = detect_my_slug()
    exclude_set.add(from_slug)
    drops = []
    for entry in list_active(stale_minutes=15):
        slug = entry.get("slug")
        if not slug or slug in exclude_set:
            continue
        drops.append(dm(slug, message, tag=tag, subject=subject, from_slug=from_slug))
    if use_mcp:
        try:
            mcp_broadcast(f"[{tag}] from {from_slug}: {(subject or str(message))[:120]}")
        except Exception:
            pass
    return drops


def spawn_agent(project, *, mode="resume", agent_name=None, accent="purple",
                headless=True, focus=None, dry_run=False):
    from_slug = detect_my_slug()
    ps1 = _root / "automations" / "start-sinister-session.ps1"
    if not ps1.exists():
        return {"ok": False, "error": f"launcher not found: {ps1}", "from": from_slug}
    args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1),
            "-Project", project, "-Mode", mode, "-AccentColor", accent]
    if agent_name:
        args += ["-AgentName", agent_name]
    if headless:
        args += ["-NoNotepad"]
    if focus:
        args += ["-FocusIntent", focus]
    stamp = _now_iso()
    rec = {
        "_author": _AUTHOR, "schema_version": SCHEMA_VERSION, "ts_utc": stamp,
        "from": from_slug, "project": project, "mode": mode, "agent_name": agent_name,
        "accent": accent, "headless": headless, "focus": focus, "command": args,
        "dry_run": dry_run,
    }
    if not dry_run:
        try:
            proc = subprocess.Popen(args, creationflags=8 if os.name == "nt" else 0)
            rec["pid"] = proc.pid
            rec["ok"] = True
        except Exception as e:
            rec["ok"] = False
            rec["error"] = str(e)
    else:
        rec["pid"] = None
        rec["ok"] = True
    p = _shared_mem() / "swarm-spawned" / f"{stamp}-{project}-by-{from_slug}.json"
    _write_json(p, rec)
    rec["_path"] = str(p)
    return rec


def list_active(stale_minutes=15):
    d = _heartbeats_dir()
    if not d.exists():
        return []
    cutoff = time.time() - stale_minutes * 60
    out = []
    for f in d.iterdir():
        if not f.is_file() or f.suffix not in (".json", ".beat"):
            continue
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            continue
        slug = f.stem
        entry = {
            "slug": slug,
            "mtime_utc": datetime.fromtimestamp(mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "age_seconds": int(time.time() - mtime),
            "heartbeat_path": str(f),
        }
        if f.suffix == ".json":
            rec = _read_json(f)
            if rec:
                entry["agent"] = rec.get("agent")
                entry["branch"] = rec.get("branch")
                entry["mode"] = rec.get("mode")
        out.append(entry)
    out.sort(key=lambda e: e["mtime_utc"], reverse=True)
    return out


@dataclass
class WatchHandle:
    path: Path
    poll_seconds: float
    stop_requested: bool = False

    def stop(self):
        self.stop_requested = True


def _hash_file(p):
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _watch_state_path(path):
    my = detect_my_slug()
    fh = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]
    return _shared_mem() / "swarm-watch" / my / f"{fh}.json"


def watch_file(path, *, on_change=None, poll_seconds=2.0, blocking=False):
    p = Path(path)
    handle = WatchHandle(path=p, poll_seconds=poll_seconds)
    state_path = _watch_state_path(p)
    state = _read_json(state_path) or {
        "_author": _AUTHOR, "path": str(p), "mtime": 0.0, "hash": "",
        "first_seen_utc": _now_iso(),
    }

    def _poll_once():
        if not p.exists():
            return None
        mtime = p.stat().st_mtime
        h = _hash_file(p)
        if h == state.get("hash"):
            return None
        event = {
            "path": str(p), "old_hash": state.get("hash", ""), "new_hash": h,
            "mtime_delta_s": int(mtime - (state.get("mtime") or 0)),
            "ts_utc": _now_iso(),
        }
        try:
            r = subprocess.run(["git", "log", "-1", "--format=%an|%s", "--", str(p)],
                               capture_output=True, text=True, cwd=str(_root), timeout=5)
            if r.returncode == 0 and "|" in r.stdout:
                a, s = r.stdout.strip().split("|", 1)
                event["last_commit_author"] = a
                event["last_commit_subject"] = s
        except Exception:
            pass
        event["current_active_agents"] = [a["slug"] for a in list_active(stale_minutes=15)]
        state["mtime"] = mtime
        state["hash"] = h
        state["last_event_utc"] = event["ts_utc"]
        _write_json(state_path, state)
        return event

    if blocking:
        while not handle.stop_requested:
            ev = _poll_once()
            if ev and on_change:
                on_change(ev)
            time.sleep(poll_seconds)
    else:
        _poll_once()
    return handle


def mark_done(task_label, *, result=None, from_slug=None):
    from_slug = from_slug or detect_my_slug()
    stamp = _now_iso()
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in task_label)[:64]
    rec = {
        "_author": _AUTHOR, "schema_version": SCHEMA_VERSION + ".status",
        "ts_utc": stamp, "from": from_slug, "task": task_label, "result": result,
    }
    p = _shared_mem() / "swarm-status" / f"{stamp}-{from_slug}-{safe}.json"
    _write_json(p, rec)
    rec["_path"] = str(p)
    return rec


def wait_for(slug, task, *, timeout_s=300, poll_seconds=2.0):
    d = _shared_mem() / "swarm-status"
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if d.exists():
            for f in sorted(d.glob("*.json")):
                rec = _read_json(f)
                if not rec:
                    continue
                if rec.get("from") == slug and rec.get("task") == task:
                    return rec
        time.sleep(poll_seconds)
    return None


def mcp_broadcast(message, *, priority="normal"):
    return {
        "ok": False, "stub": True,
        "note": "MCP fast-path not wired v0.1.0; disk drops already delivered.",
        "message": message[:200], "priority": priority,
    }


def mcp_hive_status():
    cache = _shared_mem() / "swarm-mcp-cache.json"
    return _read_json(cache) or {
        "_author": _AUTHOR, "hive_id_last_seen": None,
        "note": "Init via Ruflo hive-mind_init from Claude session.",
    }
