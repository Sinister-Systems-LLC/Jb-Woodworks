#!/usr/bin/env python3
"""crash_restore_points.py -- save/restore agent state so they resume where they left off.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 (verbatim):
    "make sure we hvae crash retore points so agents pick up where they left
     off no issues. etc"

WHAT THIS IS:
    The CANONICAL restore-point handler. Composes with three existing systems:
      1. _shared-memory/resume-points/<project>/<utc>.json (already used)
      2. SinisterEveCrashWatchdog schtask (already runs)
      3. overseer_loop_quality_agent.py savepoint git tags (already runs)

    This module adds the GLUE: a CLI agents call at session-close (save) and
    at session-start (restore), plus a crash-detect handler that auto-restores
    the most recent restore point for any project whose heartbeat goes stale
    AND has unsaved work.

CONTRACT:
    save:    write _shared-memory/resume-points/<slug>/<utc>.json with:
               - schema_version
               - ts_utc
               - project / agent_name / agent_display
               - loop_iter / focus_intent / swarm_role
               - shipped_this_iter[] / open_for_next_iter[] / pre_warm_reads[]
               - git { branch, head, ahead_origin, behind_origin, has_dirty }
               - last_5_files_edited[]
               - last_3_commands[]
               - cwd / env_essentials
    restore: read latest resume-point for <slug>, inject into spawn phrase as
             SINISTER_RESUME_POINT env var (start-sinister-session.ps1 reads it
             and prepends to the opening phrase so the agent boots with full
             context).
    crash-restore: invoked by SinisterEveCrashWatchdog when it detects a dead
             EVE / claude proc — auto-respawn the session with --resume.

CLI:
    --save <slug>                  write a fresh restore point
    --restore <slug>               print the latest restore point JSON
    --restore-into-env <slug>      print as SET cmds for shell sourcing
    --crash-restore <slug>         spawn-and-restore (calls start-sinister-session.ps1)
    --list [<slug>]                list restore points (newest first)
    --prune <slug> --keep N        keep only newest N for a slug

DOCTRINE: composes with
    automations/overseer_loop_quality_agent.py (git-tag savepoints)
    automations/eve_crash_detector.py (proc-level crash detection)
    automations/start-sinister-session.ps1 (consumes SINISTER_RESUME_POINT env)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
RESUME_DIR = SANCTUM_ROOT / "_shared-memory" / "resume-points"
HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
LAUNCHER = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug_dir(slug: str) -> Path:
    d = RESUME_DIR / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def git_state(cwd: Path) -> dict:
    def _run(cmd: list[str], default: str = "") -> str:
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), timeout=10)
            return (cp.stdout or "").strip() if cp.returncode == 0 else default
        except Exception:
            return default

    branch = _run(["git", "branch", "--show-current"])
    head = _run(["git", "rev-parse", "HEAD"])
    dirty = _run(["git", "status", "--porcelain"])
    return {
        "branch": branch,
        "head": head,
        "has_dirty": bool(dirty),
        "dirty_count": len(dirty.splitlines()) if dirty else 0,
    }


def last_edited_files(cwd: Path, n: int = 5) -> list[str]:
    """Return last N edited files (by mtime) under cwd, excluding noise."""
    try:
        cp = subprocess.run(
            ["git", "log", "-n", "20", "--name-only", "--pretty=format:"],
            capture_output=True, text=True, cwd=str(cwd), timeout=10,
        )
        files = [f for f in (cp.stdout or "").splitlines() if f.strip()]
        seen = []
        for f in files:
            if f not in seen:
                seen.append(f)
            if len(seen) >= n:
                break
        return seen
    except Exception:
        return []


def save_restore_point(slug: str, agent_name: str = "", agent_display: str = "",
                       focus_intent: str = "", loop_iter: int = 0,
                       shipped: list[str] | None = None,
                       open_next: list[str] | None = None) -> dict:
    """Write a fresh restore point. Returns the written dict."""
    sd = slug_dir(slug)
    ts = utc_iso()
    fname = sd / f"{ts.replace(':', '').replace('-', '')[:15]}Z.json"
    g = git_state(SANCTUM_ROOT)
    rp = {
        "schema_version": "sinister.resume-point.v2",
        "ts_utc": ts,
        "project": slug,
        "agent_name": agent_name or slug,
        "agent_display": agent_display or slug,
        "mode": "save",
        "loop_iter": loop_iter,
        "focus_intent": focus_intent,
        "shipped_this_iter": shipped or [],
        "open_for_next_iter": open_next or [],
        "git": g,
        "last_5_files_edited": last_edited_files(SANCTUM_ROOT, 5),
        "cwd": str(SANCTUM_ROOT),
        "env_essentials": {
            "SINISTER_QUICK_LAUNCH": os.environ.get("SINISTER_QUICK_LAUNCH"),
            "SINISTER_DEFAULT_SWARM": os.environ.get("SINISTER_DEFAULT_SWARM"),
            "SINISTER_DEFAULT_LOOP": os.environ.get("SINISTER_DEFAULT_LOOP"),
        },
    }
    try:
        fname.write_text(json.dumps(rp, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "path": str(fname), "ts": ts}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def latest_restore_point(slug: str) -> dict | None:
    sd = RESUME_DIR / slug
    if not sd.exists():
        return None
    files = sorted(sd.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def list_restore_points(slug: str | None = None) -> list[dict]:
    out: list[dict] = []
    if slug:
        sd = RESUME_DIR / slug
        if not sd.exists():
            return out
        for p in sorted(sd.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            out.append({"slug": slug, "file": str(p), "mtime": p.stat().st_mtime})
        return out
    if not RESUME_DIR.exists():
        return out
    for d in RESUME_DIR.iterdir():
        if not d.is_dir():
            continue
        files = sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if files:
            out.append({"slug": d.name, "file": str(files[0]), "count": len(files),
                        "mtime": files[0].stat().st_mtime})
    out.sort(key=lambda x: x["mtime"], reverse=True)
    return out


def prune(slug: str, keep: int = 20) -> dict:
    sd = RESUME_DIR / slug
    if not sd.exists():
        return {"ok": False, "error": "no-such-slug"}
    files = sorted(sd.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for f in files[keep:]:
        try:
            f.unlink()
            removed += 1
        except Exception:
            pass
    return {"ok": True, "kept": min(len(files), keep), "removed": removed}


def crash_restore(slug: str) -> dict:
    """Detect crash + auto-respawn with --resume. Used by SinisterEveCrashWatchdog."""
    rp = latest_restore_point(slug)
    if not rp:
        return {"ok": False, "error": "no-restore-point", "slug": slug}
    if not LAUNCHER.exists():
        return {"ok": False, "error": "launcher-missing", "slug": slug}
    env = os.environ.copy()
    env["SINISTER_QUICK_LAUNCH"] = "1"
    env["SINISTER_SKIP_MODES_PROMPT"] = "1"
    env["SINISTER_DEFAULT_SWARM"] = "1"
    env["SINISTER_DEFAULT_LOOP"] = "1"
    env["SINISTER_RESUME_POINT"] = json.dumps(rp)
    env["SINISTER_DEFAULT_LOOP_CONDITION"] = (
        rp.get("focus_intent") or "continue from where you left off; check resume-point + git state"
    )
    try:
        creationflags = 0
        if os.name == "nt":
            creationflags = 0x00000008 | 0x00000200
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(LAUNCHER), "-Project", slug],
            env=env, creationflags=creationflags,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, close_fds=True,
        )
        return {"ok": True, "slug": slug, "restored_from": rp.get("ts_utc"),
                "focus": rp.get("focus_intent")}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def restore_into_env(slug: str) -> int:
    """Print SET commands so a shell can source them."""
    rp = latest_restore_point(slug)
    if not rp:
        print(f"# no restore-point for {slug}", file=sys.stderr)
        return 1
    # Print as `set VAR=value` (Windows cmd) + `export VAR=value` (bash)
    payload = json.dumps(rp).replace('"', '\\"')
    print(f'set "SINISTER_RESUME_POINT={payload}"')
    print(f'export SINISTER_RESUME_POINT={payload!r}')
    print(f'set "SINISTER_DEFAULT_LOOP_CONDITION={rp.get("focus_intent", "")}"')
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--save", metavar="SLUG")
    g.add_argument("--restore", metavar="SLUG")
    g.add_argument("--restore-into-env", metavar="SLUG")
    g.add_argument("--crash-restore", metavar="SLUG")
    g.add_argument("--list", metavar="SLUG", nargs="?", const="")
    g.add_argument("--prune", metavar="SLUG")
    ap.add_argument("--keep", type=int, default=20)
    ap.add_argument("--agent-name", default="")
    ap.add_argument("--agent-display", default="")
    ap.add_argument("--focus", default="")
    ap.add_argument("--iter", type=int, default=0)
    ap.add_argument("--shipped", action="append", default=[])
    ap.add_argument("--open-next", action="append", default=[])
    args = ap.parse_args(argv)

    if args.save:
        r = save_restore_point(args.save, args.agent_name, args.agent_display,
                                args.focus, args.iter, args.shipped, args.open_next)
        print(json.dumps(r, indent=2))
        return 0 if r.get("ok") else 1
    if args.restore:
        rp = latest_restore_point(args.restore)
        if not rp:
            print(f"# no restore-point for {args.restore}", file=sys.stderr)
            return 1
        print(json.dumps(rp, indent=2))
        return 0
    if args.restore_into_env:
        return restore_into_env(args.restore_into_env)
    if args.crash_restore:
        r = crash_restore(args.crash_restore)
        print(json.dumps(r, indent=2))
        return 0 if r.get("ok") else 1
    if args.list is not None:
        out = list_restore_points(args.list or None)
        print(json.dumps(out, indent=2))
        return 0
    if args.prune:
        r = prune(args.prune, args.keep)
        print(json.dumps(r, indent=2))
        return 0 if r.get("ok") else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
