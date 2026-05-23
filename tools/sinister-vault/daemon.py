"""
Sinister Vault daemon (SV-A) — 1TB storage reservation at D:\\sinister-vault\\

Author: Sinister Sanctum SV-A agent (Claude) :: 2026-05-19

Pure-Python single-process daemon that manages the unified Sanctum storage
reservation. Exposes a small FastAPI surface on port 5078 (RKOJ owns 5077):

  GET  /api/vault/health         — liveness + headline stats
  GET  /api/vault/quota          — per-subtree usage breakdown
  GET  /api/vault/audit          — tail the JSONL audit stream
  POST /api/vault/audit          — append a custom audit event
  GET  /api/vault/list           — sandboxed recursive directory listing
  POST /api/vault/snapshot       — robocopy a sub-tree into snapshots/<UTC-iso>/

A background asyncio task recomputes usage every 60s, persists _quota.json,
emits warn events to the audit log when usage crosses the warn threshold,
and refuses writes (snapshot, audit append, list) with HTTP 507 once the
quota is fully exhausted.

Run:
    python daemon.py [--port 5078] [--max-gb 1024] [--warn-gb 950]

The daemon never deletes user data. It only writes to:
    D:\\sinister-vault\\audit\\<UTC-date>.jsonl     (audit stream)
    D:\\sinister-vault\\_quota.json                  (cache of running totals)
    D:\\sinister-vault\\snapshots\\<UTC-iso>\\        (robocopy targets)
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# ----------------------------------------------------------------- constants ---
VERSION = "1.0.0"
VAULT_ROOT = Path(r"D:\sinister-vault")
# /loop iter 4 of eve-into-rkoj-integration follow-ups: VAULT_ROOT on this
# operator workstation is an NTFS junction (mklink /J) that resolves to a
# different physical path. os.scandir + Path.resolve() walk through the
# junction, so entry.path is the resolved variant while VAULT_ROOT itself
# stays unresolved. Cache the resolved form once at module-init so
# Path.relative_to() lines up. (See OPERATOR-ACTION-QUEUE.md vault row.)
try:
    VAULT_ROOT_RESOLVED = VAULT_ROOT.resolve()
except (OSError, RuntimeError):
    # Junction broken / unreadable — fall back to unresolved so the daemon
    # still boots; /list will surface the error via the existing 404 path.
    VAULT_ROOT_RESOLVED = VAULT_ROOT
SUBTREES = ["repos", "sync", "snapshots", "audit", "accounts"]
QUOTA_FILE = VAULT_ROOT / "_quota.json"
AUDIT_DIR = VAULT_ROOT / "audit"
SNAPSHOTS_DIR = VAULT_ROOT / "snapshots"

# LIVENESS heartbeat (separate from quota-refresh ticker). HR-B audit
# 2026-05-19 flagged that _shared-memory/heartbeats/ had only build-stamps;
# fleet-monitor needs a "process alive AND responding" signal that the
# asyncio event loop is actually pumping. 30s cadence + 120s stale window.
HEARTBEAT_DIR = Path(r"D:\Sinister Sanctum\_shared-memory\heartbeats")
HEARTBEAT_FILE = HEARTBEAT_DIR / "sinister-vault.beat"
HEARTBEAT_INTERVAL_S = 30
HEARTBEAT_STALE_S = 120

REFRESH_INTERVAL_S = 60
LIST_CAP = 1000
DEFAULT_PORT = 5078
DEFAULT_MAX_GB = 1024  # 1 TB soft cap
DEFAULT_WARN_GB = 950  # ~93% of cap

# Filled in by main() before the FastAPI app is configured.
RUNTIME: Dict[str, Any] = {
    "started_at": time.time(),
    "port": DEFAULT_PORT,
    "max_gb": DEFAULT_MAX_GB,
    "warn_gb": DEFAULT_WARN_GB,
    "last_refresh_ts": 0.0,
    "last_quota": None,         # cached /api/vault/quota payload
    "warned_above_threshold": False,
}

# ------------------------------------------------------------------ logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [vault] %(levelname)s %(message)s",
)
log = logging.getLogger("vault")


# ---------------------------------------------------------------- helpers -----
def _human(n: int) -> str:
    """Render a byte count as a human-friendly string (KB / MB / GB / TB)."""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if n < 1024.0 or unit == "PB":
            return f"{n:.2f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.2f} PB"


def _subtree_size(p: Path) -> int:
    """Recursive size via os.scandir. Skips reparse points + symlinks to avoid
    counting external drives a junction might point at."""
    total = 0
    if not p.exists():
        return 0
    stack: List[Path] = [p]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
        except (OSError, PermissionError):
            continue
    return total


def _utc_iso(ts: Optional[float] = None) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(timezone.utc)
    return dt.isoformat(timespec="seconds")


def _audit_path_for(dt: Optional[datetime] = None) -> Path:
    dt = dt or datetime.now(timezone.utc)
    return AUDIT_DIR / f"{dt.strftime('%Y-%m-%d')}.jsonl"


def _safe_subpath(rel: str) -> Path:
    """Resolve <rel> beneath VAULT_ROOT, blocking path-traversal escapes."""
    rel = (rel or "").strip().lstrip("/\\").replace("\\", "/")
    candidate = (VAULT_ROOT / rel).resolve()
    root_res = VAULT_ROOT.resolve()
    try:
        candidate.relative_to(root_res)
    except ValueError:
        raise HTTPException(status_code=400, detail="path escapes vault root")
    return candidate


def _append_audit(event: Dict[str, Any]) -> None:
    """Append an event to today's JSONL audit log. Creates the file on demand."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    path = _audit_path_for()
    line = json.dumps(event, separators=(",", ":"), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _make_event(kind: str, actor: str, path: str = "", message: str = "",
                meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "ts": _utc_iso(),
        "kind": kind,
        "actor": actor or "unknown",
        "path": path or "",
        "message": message or "",
        "meta": meta or {},
    }


def _compute_quota() -> Dict[str, Any]:
    """Walk every subtree and build the full quota payload. Costly — cached
    for REFRESH_INTERVAL_S in the background loop and exposed via the API."""
    VAULT_ROOT.mkdir(parents=True, exist_ok=True)
    subtree_payload: Dict[str, Any] = {}
    total_bytes = 0
    for name in SUBTREES:
        p = VAULT_ROOT / name
        p.mkdir(parents=True, exist_ok=True)
        sz = _subtree_size(p)
        total_bytes += sz
        subtree_payload[name] = {
            "bytes": sz,
            "human": _human(sz),
        }
    max_bytes = RUNTIME["max_gb"] * 1024 ** 3
    warn_bytes = RUNTIME["warn_gb"] * 1024 ** 3
    # Now annotate percent_of_quota now that we have a total.
    for name, info in subtree_payload.items():
        info["percent_of_quota"] = round((info["bytes"] / max_bytes) * 100, 3) if max_bytes else 0.0

    try:
        du = shutil.disk_usage(str(VAULT_ROOT))
        disk = {"total": du.total, "used": du.used, "free": du.free,
                "total_human": _human(du.total), "free_human": _human(du.free)}
    except OSError:
        disk = None

    payload = {
        "ok": True,
        "ts": _utc_iso(),
        "vault_root": str(VAULT_ROOT),
        "max_gb": RUNTIME["max_gb"],
        "warn_gb": RUNTIME["warn_gb"],
        "used_bytes": total_bytes,
        "used_gb": round(total_bytes / 1024 ** 3, 3),
        "used_human": _human(total_bytes),
        "percent_used": round((total_bytes / max_bytes) * 100, 3) if max_bytes else 0.0,
        "over_warn": total_bytes >= warn_bytes,
        "over_max": total_bytes >= max_bytes,
        "subtrees": subtree_payload,
        "disk": disk,
    }
    return payload


def _persist_quota(payload: Dict[str, Any]) -> None:
    try:
        QUOTA_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        log.warning("could not persist _quota.json: %s", exc)


def _is_writes_blocked() -> bool:
    q = RUNTIME.get("last_quota") or {}
    return bool(q.get("over_max"))


# --------------------------------------------------------------- background ---
async def _refresh_loop() -> None:
    """Background ticker — recompute every REFRESH_INTERVAL_S seconds, persist
    the cache, and emit warn/info events as thresholds are crossed."""
    while True:
        try:
            payload = await asyncio.to_thread(_compute_quota)
            RUNTIME["last_quota"] = payload
            RUNTIME["last_refresh_ts"] = time.time()
            _persist_quota(payload)

            over_warn = payload["over_warn"]
            previously_warned = RUNTIME["warned_above_threshold"]
            if over_warn and not previously_warned:
                _append_audit(_make_event(
                    "warn", "daemon", "/",
                    f"vault usage {payload['used_human']} crossed warn threshold ({RUNTIME['warn_gb']} GB)",
                    {"used_bytes": payload["used_bytes"],
                     "warn_gb": RUNTIME["warn_gb"],
                     "max_gb": RUNTIME["max_gb"]}
                ))
                RUNTIME["warned_above_threshold"] = True
            elif (not over_warn) and previously_warned:
                _append_audit(_make_event(
                    "info", "daemon", "/",
                    f"vault usage {payload['used_human']} dropped back below warn threshold",
                    {"used_bytes": payload["used_bytes"]}
                ))
                RUNTIME["warned_above_threshold"] = False

            if payload["over_max"]:
                _append_audit(_make_event(
                    "error", "daemon", "/",
                    f"vault usage {payload['used_human']} exceeds hard cap {RUNTIME['max_gb']} GB; writes blocked",
                    {"used_bytes": payload["used_bytes"]}
                ))
        except Exception as exc:  # never let the loop die
            log.exception("refresh loop tick failed: %s", exc)
        await asyncio.sleep(REFRESH_INTERVAL_S)


def _write_heartbeat_line() -> str:
    """Build + write one heartbeat line. Pure blocking; called from the
    asyncio loop directly because the .write is sub-millisecond and the
    event loop won't notice."""
    HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    uptime = int(time.time() - RUNTIME["started_at"])
    line = (f"{_utc_iso()} pid={os.getpid()} "
            f"port={RUNTIME['port']} uptime={uptime}")
    HEARTBEAT_FILE.write_text(line + "\n", encoding="utf-8")
    return line


async def _heartbeat_loop() -> None:
    """Background ticker -- writes sinister-vault.beat every HEARTBEAT_INTERVAL_S
    seconds. Single line per tick: '<UTC-iso> pid=N port=N uptime=N'. Fleet
    monitor reads mtime; stale if >120s old. Never lets the loop die."""
    while True:
        try:
            _write_heartbeat_line()
        except Exception as exc:
            log.warning("heartbeat tick failed: %s", exc)
        await asyncio.sleep(HEARTBEAT_INTERVAL_S)


# ------------------------------------------------------------------- models ---
class AuditAppendBody(BaseModel):
    kind: str
    actor: str
    path: Optional[str] = ""
    message: Optional[str] = ""
    meta: Optional[Dict[str, Any]] = None


class SnapshotBody(BaseModel):
    subtree: str = "repos"          # which sub-tree to snapshot
    label: Optional[str] = None     # optional label appended to the folder
    actor: Optional[str] = "operator"


# --------------------------------------------------------------------- app ---
app = FastAPI(title="Sinister Vault", version=VERSION)


@app.on_event("startup")
async def _startup() -> None:
    VAULT_ROOT.mkdir(parents=True, exist_ok=True)
    for name in SUBTREES:
        (VAULT_ROOT / name).mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    _append_audit(_make_event(
        "info", "daemon", "/",
        f"vault daemon v{VERSION} starting (port={RUNTIME['port']}, "
        f"max_gb={RUNTIME['max_gb']}, warn_gb={RUNTIME['warn_gb']})",
        {"pid": os.getpid()}
    ))
    # Prime the cache on the very first tick so /api/vault/health has data.
    try:
        payload = await asyncio.to_thread(_compute_quota)
        RUNTIME["last_quota"] = payload
        RUNTIME["last_refresh_ts"] = time.time()
        _persist_quota(payload)
        if payload["over_warn"]:
            RUNTIME["warned_above_threshold"] = True
    except Exception as exc:
        log.warning("startup quota prime failed: %s", exc)
    # Prime the heartbeat on first tick so fleet-monitor sees it immediately
    # (don't wait 30s for the first asyncio sleep cycle).
    try:
        _write_heartbeat_line()
    except Exception as exc:
        log.warning("startup heartbeat prime failed: %s", exc)
    RUNTIME["refresh_task"] = asyncio.create_task(_refresh_loop())
    RUNTIME["heartbeat_task"] = asyncio.create_task(_heartbeat_loop())


@app.on_event("shutdown")
async def _shutdown() -> None:
    # Cancel background tasks so they don't fight a dying event loop.
    for key in ("refresh_task", "heartbeat_task"):
        task = RUNTIME.get(key)
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
    with contextlib.suppress(Exception):
        _append_audit(_make_event("info", "daemon", "/", "vault daemon stopping",
                                  {"pid": os.getpid()}))


@app.get("/api/vault/health")
def health() -> Dict[str, Any]:
    q = RUNTIME.get("last_quota") or {}
    return {
        "ok": True,
        "version": VERSION,
        "uptime_s": round(time.time() - RUNTIME["started_at"], 1),
        "port": RUNTIME["port"],
        "max_gb": RUNTIME["max_gb"],
        "warn_gb": RUNTIME["warn_gb"],
        "used_gb": q.get("used_gb", 0.0),
        "used_human": q.get("used_human", "0 B"),
        "over_warn": q.get("over_warn", False),
        "over_max": q.get("over_max", False),
        "last_refresh": _utc_iso(RUNTIME["last_refresh_ts"]) if RUNTIME["last_refresh_ts"] else None,
        "vault_root": str(VAULT_ROOT),
    }


@app.get("/api/vault/heartbeat")
def heartbeat() -> Dict[str, Any]:
    """Report the LIVENESS heartbeat file state. Different from /health --
    /health says "the HTTP socket answers"; this reads the file the asyncio
    heartbeat loop writes so a stuck event loop is detectable. alive = file
    mtime within HEARTBEAT_STALE_S (default 120s)."""
    info: Dict[str, Any] = {
        "file": str(HEARTBEAT_FILE),
        "exists": HEARTBEAT_FILE.exists(),
        "mtime_iso": None,
        "age_s": None,
        "last_line": None,
        "alive": False,
        "stale_after_s": HEARTBEAT_STALE_S,
    }
    if not info["exists"]:
        return info
    try:
        st = HEARTBEAT_FILE.stat()
        info["mtime_iso"] = _utc_iso(st.st_mtime)
        info["age_s"] = round(time.time() - st.st_mtime, 1)
        info["alive"] = info["age_s"] < HEARTBEAT_STALE_S
    except OSError as exc:
        info["error"] = f"stat failed: {exc}"
        return info
    try:
        text = HEARTBEAT_FILE.read_text(encoding="utf-8").rstrip("\r\n")
        if text:
            info["last_line"] = text.splitlines()[-1]
    except OSError as exc:
        info["error"] = f"read failed: {exc}"
    return info


@app.get("/api/vault/quota")
def quota(force: bool = False) -> Dict[str, Any]:
    """Return the cached quota payload. If `force=1`, recompute synchronously.
    The background loop also refreshes every 60s."""
    if force or RUNTIME.get("last_quota") is None or (
            time.time() - RUNTIME["last_refresh_ts"] > REFRESH_INTERVAL_S * 2):
        payload = _compute_quota()
        RUNTIME["last_quota"] = payload
        RUNTIME["last_refresh_ts"] = time.time()
        _persist_quota(payload)
        return payload
    return RUNTIME["last_quota"]


@app.get("/api/vault/audit")
def audit_tail(limit: int = Query(50, ge=1, le=2000),
               since: Optional[str] = None) -> Dict[str, Any]:
    """Tail the most recent N audit events, optionally filtered to events with
    `ts >= since` (ISO-UTC). Reads at most the last 4 daily files."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(AUDIT_DIR.glob("*.jsonl"), reverse=True)[:4]
    events: List[Dict[str, Any]] = []
    for f in files:
        try:
            for line in reversed(f.read_text(encoding="utf-8").splitlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if since and ev.get("ts", "") < since:
                    continue
                events.append(ev)
                if len(events) >= limit:
                    break
        except OSError:
            continue
        if len(events) >= limit:
            break
    return {"ok": True, "count": len(events), "events": events}


@app.post("/api/vault/audit")
def audit_append(body: AuditAppendBody) -> Dict[str, Any]:
    """Append a custom audit event. Other Sanctum services (Gitea hook,
    Syncthing watcher, MCP server) call this so all storage activity ends
    up in one unified stream."""
    if _is_writes_blocked():
        raise HTTPException(status_code=507, detail="vault over hard cap; writes blocked")
    kind = (body.kind or "").strip().lower()
    if not kind:
        raise HTTPException(status_code=400, detail="kind required")
    if kind not in {"commit", "push", "pull", "sync", "snapshot", "warn", "error", "info"}:
        # Allow it but tag as info-derived to keep the union closed without surprises.
        log.info("non-canonical audit kind %r accepted from %s", kind, body.actor)
    event = _make_event(kind, body.actor, body.path or "", body.message or "", body.meta or {})
    _append_audit(event)
    return {"ok": True, "event": event}


@app.get("/api/vault/list")
def list_dir(path: str = "", depth: int = Query(1, ge=1, le=4)) -> Dict[str, Any]:
    """Recursive directory listing rooted at D:\\sinister-vault\\<path>. Hard-capped
    at LIST_CAP entries. `depth` controls how many levels deep we descend."""
    if _is_writes_blocked():
        # Reads still serve, but flag the condition.
        pass
    base = _safe_subpath(path)
    if not base.exists():
        raise HTTPException(status_code=404, detail=f"no such path: {path!r}")
    if not base.is_dir():
        raise HTTPException(status_code=400, detail="path is not a directory")

    entries: List[Dict[str, Any]] = []
    truncated = False

    def walk(p: Path, d: int) -> None:
        nonlocal truncated
        if truncated or d > depth:
            return
        try:
            with os.scandir(p) as it:
                for entry in it:
                    if len(entries) >= LIST_CAP:
                        truncated = True
                        return
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    # /loop iter 4: use VAULT_ROOT_RESOLVED because base
                    # came from _safe_subpath which calls .resolve() — so
                    # entry.path is junction-resolved while VAULT_ROOT
                    # itself isn't. Without this, relative_to() raised
                    # ValueError on every list (pre-existing 500).
                    try:
                        rel = str(Path(entry.path).relative_to(VAULT_ROOT_RESOLVED)).replace("\\", "/")
                    except ValueError:
                        # Defensive: if neither root form lines up (shouldn't
                        # happen post-fix), fall back to the entry name.
                        rel = entry.name
                    entries.append({
                        "name": entry.name,
                        "path": rel,
                        "kind": "dir" if is_dir else "file",
                        "size": 0 if is_dir else st.st_size,
                        "mtime": st.st_mtime,
                    })
                    if is_dir and d < depth:
                        walk(Path(entry.path), d + 1)
        except (OSError, PermissionError):
            return

    walk(base, 1)
    entries.sort(key=lambda e: (e["kind"] != "dir", e["path"]))
    return {
        "ok": True,
        "root": str(base),
        "count": len(entries),
        "depth": depth,
        "truncated": truncated,
        "cap": LIST_CAP,
        "entries": entries,
    }


@app.post("/api/vault/snapshot")
def snapshot(body: SnapshotBody) -> Dict[str, Any]:
    """Snapshot a sub-tree by mirroring it into snapshots/<UTC-iso>[-label]/.
    Uses robocopy on Windows for speed; falls back to shutil.copytree elsewhere."""
    if _is_writes_blocked():
        raise HTTPException(status_code=507, detail="vault over hard cap; writes blocked")
    subtree = (body.subtree or "").strip().strip("/\\").replace("\\", "/")
    if not subtree or subtree.startswith("snapshots"):
        raise HTTPException(status_code=400, detail="invalid subtree (cannot snapshot snapshots)")
    src = _safe_subpath(subtree)
    if not src.exists() or not src.is_dir():
        raise HTTPException(status_code=404, detail=f"subtree not found: {subtree}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label_part = ""
    if body.label:
        safe = "".join(c if (c.isalnum() or c in "-_") else "-" for c in body.label)[:40]
        if safe:
            label_part = "-" + safe.strip("-")
    target = SNAPSHOTS_DIR / f"{stamp}-{subtree.replace('/', '_')}{label_part}"
    target.parent.mkdir(parents=True, exist_ok=True)

    started = time.time()
    method = "robocopy"
    rc: Optional[int] = None
    err: Optional[str] = None
    if sys.platform.startswith("win"):
        try:
            proc = subprocess.run(
                ["robocopy", str(src), str(target),
                 "/E", "/COPY:DAT", "/R:1", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS", "/NP"],
                capture_output=True, text=True, timeout=60 * 30,
            )
            rc = proc.returncode
            # robocopy exit codes 0..7 are success-ish; >=8 is failure
            if rc >= 8:
                err = proc.stderr.strip() or proc.stdout.strip() or f"robocopy rc={rc}"
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            method = "shutil"
            try:
                shutil.copytree(src, target, dirs_exist_ok=True)
                rc = 0
            except Exception as exc2:
                err = f"copytree failed: {exc2}"
    else:
        method = "shutil"
        try:
            shutil.copytree(src, target, dirs_exist_ok=True)
            rc = 0
        except Exception as exc:
            err = f"copytree failed: {exc}"

    elapsed = round(time.time() - started, 2)
    size = _subtree_size(target) if target.exists() else 0
    ok = err is None
    ev = _make_event(
        "snapshot", body.actor or "operator", "/" + subtree,
        f"snapshot of {subtree} -> {target.name} ({_human(size)}) in {elapsed}s",
        {"target": str(target), "bytes": size, "method": method, "rc": rc, "ok": ok,
         "label": body.label or None, "error": err},
    )
    _append_audit(ev)
    status = 200 if ok else 500
    body_out = {"ok": ok, "target": str(target), "bytes": size, "human": _human(size),
                "elapsed_s": elapsed, "method": method, "rc": rc, "error": err}
    return JSONResponse(status_code=status, content=body_out)


# ----------------------------------------------------------------- entrypoint ---
def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sinister Vault daemon")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--max-gb", type=int, default=DEFAULT_MAX_GB,
                    help="hard cap; writes refused above this")
    ap.add_argument("--warn-gb", type=int, default=DEFAULT_WARN_GB,
                    help="soft warning threshold (audit-only)")
    ap.add_argument("--host", default="127.0.0.1")
    return ap.parse_args()


def main() -> None:
    args = _parse_args()
    RUNTIME["port"] = args.port
    RUNTIME["max_gb"] = args.max_gb
    RUNTIME["warn_gb"] = args.warn_gb
    if RUNTIME["warn_gb"] >= RUNTIME["max_gb"]:
        log.warning("warn_gb >= max_gb; using warn = max - 1")
        RUNTIME["warn_gb"] = RUNTIME["max_gb"] - 1
    log.info("starting vault daemon v%s on %s:%d (max=%dGB warn=%dGB root=%s)",
             VERSION, args.host, args.port, args.max_gb, args.warn_gb, VAULT_ROOT)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
