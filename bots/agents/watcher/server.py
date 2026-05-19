"""
Watcher agent — source-drift detection.

Pure Python (Tier 1, no LLM). Polls source project mtimes vs _manifest.json sha256.
Reports drift, queues refresh, optionally notifies Librarian to reindex.

Tools:
  watcher.scan(project=None)        -> [{path, status: 'changed'|'new'|'deleted'}]
  watcher.queue_refresh(file)       -> {ok}
  watcher.list_queue()              -> queued items
  watcher.health()                  -> {ok, last_scan_ts, drifted_count}
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[watcher] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
MANIFEST_PATH = HUB_ROOT / "_manifest.json"
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "watcher"
STATE_PATH = AGENT_DIR / "state.json"
QUEUE_PATH = AGENT_DIR / "queue.jsonl"
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"

AGENT_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)


def log_call(tool: str, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "watcher",
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"projects": []}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"last_scan_ts": None, "files": {}}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    tmp = STATE_PATH.with_suffix(f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(tmp, STATE_PATH)


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def append_queue(item: dict[str, Any]) -> None:
    with QUEUE_PATH.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(item) + "\n")


mcp = FastMCP("watcher")


@mcp.tool()
def scan(project: str | None = None) -> list[dict[str, Any]]:
    """Scan source projects for drift since last scan. Returns drifted files."""
    log_call("scan", project=project or "all")
    manifest = load_manifest()
    state = load_state()
    drift: list[dict[str, Any]] = []
    projects = manifest.get("projects", [])
    if project:
        projects = [p for p in projects if p.get("name") == project]

    for proj in projects:
        src = Path(proj.get("source_path", ""))
        if not src.exists():
            drift.append({"project": proj["name"], "path": str(src), "status": "source_missing"})
            continue
        # Only scan key memory files (not whole tree — that's robocopy's job)
        candidates = [
            src / "SESSION-START.md",
            src / "docs" / "AUTONOMY-LOG.md",
            src / "docs" / "SESSION-LOG.md",
            src / "docs" / "PROJECT-STATUS.md",
            src / "docs" / "WHAT-FAILED.md",
            src / "CLAUDE.md",
            src / "README.md",
            src / "RESUME-HERE.md",
        ]
        for f in candidates:
            if not f.exists():
                continue
            key = str(f)
            current_mtime = f.stat().st_mtime
            current_sha = sha256_file(f)
            prev = state.get("files", {}).get(key)
            if prev is None:
                drift.append({"project": proj["name"], "path": str(f.relative_to(src) if src in f.parents else f), "status": "new", "sha": current_sha})
                state.setdefault("files", {})[key] = {"mtime": current_mtime, "sha": current_sha}
                append_queue({"ts": datetime.now(timezone.utc).isoformat(), "project": proj["name"], "file": str(f), "action": "refresh"})
            elif prev.get("sha") != current_sha:
                drift.append({
                    "project": proj["name"],
                    "path": str(f.relative_to(src) if src in f.parents else f),
                    "status": "changed",
                    "old_sha": prev.get("sha"),
                    "new_sha": current_sha,
                })
                state["files"][key] = {"mtime": current_mtime, "sha": current_sha}
                append_queue({"ts": datetime.now(timezone.utc).isoformat(), "project": proj["name"], "file": str(f), "action": "refresh"})

    state["last_scan_ts"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    return drift


@mcp.tool()
def queue_refresh(file: str, project: str | None = None) -> dict[str, Any]:
    """Manually queue a file for refresh."""
    log_call("queue_refresh", file=file)
    append_queue({"ts": datetime.now(timezone.utc).isoformat(), "project": project, "file": file, "action": "refresh"})
    return {"ok": True}


@mcp.tool()
def list_queue(limit: int = 50) -> list[dict[str, Any]]:
    """List recent queued items."""
    log_call("list_queue")
    if not QUEUE_PATH.exists():
        return []
    lines = QUEUE_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines[-limit:] if l.strip()]


@mcp.tool()
def clear_queue() -> dict[str, Any]:
    """Clear the refresh queue (typically called by refresh.ps1 after it consumes)."""
    log_call("clear_queue")
    if QUEUE_PATH.exists():
        QUEUE_PATH.unlink()
    return {"ok": True}


@mcp.tool()
def health() -> dict[str, Any]:
    log_call("health")
    state = load_state()
    return {
        "ok": True,
        "agent": "watcher",
        "last_scan_ts": state.get("last_scan_ts"),
        "tracked_files": len(state.get("files", {})),
        "queue_size": len(load_state().get("files", {})) if QUEUE_PATH.exists() else 0,
    }


if __name__ == "__main__":
    mcp.run()
