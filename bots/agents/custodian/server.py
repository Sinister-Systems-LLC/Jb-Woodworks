"""
Custodian agent — active incremental backup for the Sinister drive.

Tier 1 (pure Python, $0). Watches configured source paths, snapshots changed files
into D:\\_backups\\snapshots\\<source>\\<rel-path>\\<basename>.<utc>.<sha8>.<ext>,
appends a one-line manifest entry, prunes per the retention policy.

Tools:
  custodian.snapshot_now(source=None)               -> {scanned, new, unchanged, errors, manifest_entries}
  custodian.list_versions(path)                     -> [{snapshot, ts, sha8, size}]
  custodian.restore(path, version=None, dest=None)  -> {ok, restored_to, sha}
  custodian.cleanup(dry_run=False)                  -> {removed, kept, freed_bytes}
  custodian.diff(path)                              -> {changed, last_snapshot_ts, current_sha, snapshot_sha}
  custodian.config()                                -> watch-list config (read-only)
  custodian.health()                                -> {ok, backup_root, total_snapshots, total_bytes}
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[custodian] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "custodian"
AGENT_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = Path(os.environ.get("CUSTODIAN_CONFIG", r"D:\_backups\_config\watch-list.json"))
DEFAULT_BACKUP_ROOT = Path(r"D:\_backups")


def log_call(tool: str, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "custodian",
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Custodian config not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def globs_match(path: Path, patterns: list[str], root: Path) -> bool:
    rel = str(path.relative_to(root)).replace("\\", "/")
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(path.name, p) for p in patterns)


def is_secret_path(name: str, patterns: list[str]) -> bool:
    return any(re.search(p, name) for p in patterns)


def snapshot_target_path(source_name: str, src_root: Path, file_path: Path, sha: str, backup_root: Path) -> Path:
    rel = file_path.relative_to(src_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = "".join(file_path.suffixes) or ""
    base = file_path.name[: -len(suffix)] if suffix else file_path.name
    versioned_name = f"{base}.{stamp}.{sha[:8]}{suffix}"
    return backup_root / "snapshots" / source_name / rel.parent / versioned_name


def append_manifest(manifest_path: Path, entry: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(entry) + "\n")


def latest_sha_for(manifest_path: Path, source: str, rel_path: str) -> str | None:
    """Return the sha of the most recent snapshot recorded for this file."""
    if not manifest_path.exists():
        return None
    latest = None
    for line in manifest_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("source") == source and r.get("rel_path") == rel_path:
            latest = r
    return latest.get("sha") if latest else None


def all_snapshots_for(manifest_path: Path, source: str, rel_path: str) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        return []
    out = []
    for line in manifest_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("source") == source and r.get("rel_path") == rel_path:
            out.append(r)
    out.sort(key=lambda r: r.get("ts", ""))
    return out


def do_snapshot(source: dict[str, Any], cfg: dict[str, Any], single_path: Path | None = None) -> dict[str, Any]:
    """Snapshot one source. If single_path given, only that file is considered."""
    src_root = Path(source["root"])
    if not src_root.exists():
        return {"source": source["name"], "error": f"source missing: {src_root}", "scanned": 0, "new": 0, "unchanged": 0, "errors": 0}
    backup_root = Path(cfg.get("snapshot_root", DEFAULT_BACKUP_ROOT / "snapshots")).parent
    manifest_path = Path(cfg.get("manifest_path", backup_root / "_manifest.jsonl"))
    include = source.get("include_globs", ["**/*"])
    ignore = source.get("ignore_globs", [])
    max_bytes = cfg.get("policy", {}).get("max_file_size_mb", 50) * 1024 * 1024
    secret_patterns = cfg.get("ignore_secret_patterns", [])

    scanned = new = unchanged = errors = 0
    new_entries: list[str] = []

    files_iter = [single_path] if single_path else _walk(src_root, include, ignore)
    for f in files_iter:
        if not f.exists() or not f.is_file():
            continue
        if cfg.get("ignore_secret_files") and is_secret_path(f.name, secret_patterns):
            continue
        try:
            size = f.stat().st_size
        except OSError:
            errors += 1
            continue
        if size > max_bytes:
            continue
        scanned += 1
        sha = sha256_file(f)
        if sha is None:
            errors += 1
            continue
        rel_str = str(f.relative_to(src_root)).replace("\\", "/")
        last_sha = latest_sha_for(manifest_path, source["name"], rel_str)
        if last_sha == sha:
            unchanged += 1
            continue
        target = snapshot_target_path(source["name"], src_root, f, sha, backup_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(f, target)
        except Exception:
            errors += 1
            continue
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": source["name"],
            "src_root": str(src_root),
            "rel_path": rel_str,
            "snapshot": str(target),
            "sha": sha,
            "size": size,
        }
        append_manifest(manifest_path, entry)
        new += 1
        new_entries.append(rel_str)
    return {
        "source": source["name"],
        "scanned": scanned,
        "new": new,
        "unchanged": unchanged,
        "errors": errors,
        "new_files": new_entries[:50],
    }


def _walk(root: Path, include: list[str], ignore: list[str]) -> list[Path]:
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        if any(fnmatch.fnmatch(rel, ig) or fnmatch.fnmatch(p.name, ig) for ig in ignore):
            continue
        if include and not any(fnmatch.fnmatch(rel, inc) or fnmatch.fnmatch(p.name, inc) for inc in include):
            continue
        out.append(p)
    return out


mcp = FastMCP("custodian")


@mcp.tool()
def snapshot_now(source: str | None = None, path: str | None = None) -> dict[str, Any]:
    """Run an incremental snapshot pass. If source given, only that source. If path given, only that file."""
    cfg = load_config()
    sources = cfg.get("sources", [])
    if source:
        sources = [s for s in sources if s.get("name") == source]
        if not sources:
            return {"ok": False, "error": f"unknown source: {source}"}
    results = []
    single_file = Path(path) if path else None
    for s in sources:
        res = do_snapshot(s, cfg, single_path=single_file)
        results.append(res)
    log_call("snapshot_now", source=source, path=path,
             new_total=sum(r.get("new", 0) for r in results),
             unchanged_total=sum(r.get("unchanged", 0) for r in results))
    return {"ok": True, "sources": results,
            "totals": {
                "new": sum(r.get("new", 0) for r in results),
                "unchanged": sum(r.get("unchanged", 0) for r in results),
                "errors": sum(r.get("errors", 0) for r in results),
            }}


@mcp.tool()
def list_versions(path: str, source: str | None = None) -> dict[str, Any]:
    """List all snapshots recorded for a file. path is absolute or relative-to-source-root."""
    log_call("list_versions", path=path[:300])
    cfg = load_config()
    manifest_path = Path(cfg.get("manifest_path"))
    # Resolve: if absolute, find which source it lives under
    p = Path(path)
    resolved = None
    for s in cfg.get("sources", []):
        if source and s["name"] != source:
            continue
        root = Path(s["root"])
        if p.is_absolute():
            try:
                rel = p.relative_to(root)
                resolved = (s["name"], str(rel).replace("\\", "/"))
                break
            except ValueError:
                continue
        else:
            if not source or s["name"] == source:
                resolved = (s["name"], path.replace("\\", "/"))
                break
    if not resolved:
        return {"ok": False, "error": "path not under any configured source root"}
    src_name, rel = resolved
    snaps = all_snapshots_for(manifest_path, src_name, rel)
    return {"ok": True, "source": src_name, "rel_path": rel,
            "versions": [{"ts": s["ts"], "sha8": s["sha"][:8], "size": s["size"], "snapshot": s["snapshot"]} for s in snaps],
            "count": len(snaps)}


@mcp.tool()
def restore(path: str, version: str | None = None, dest: str | None = None, source: str | None = None) -> dict[str, Any]:
    """Restore a file from backup. version is an ISO ts or sha8; default = latest snapshot.

    dest = where to write. Default = the original path (will OVERWRITE).
    """
    cfg = load_config()
    info = list_versions(path, source=source)
    if not info.get("ok"):
        return info
    snaps = info["versions"]
    if not snaps:
        return {"ok": False, "error": "no snapshots recorded for this path"}
    if version is None:
        chosen = snaps[-1]
    else:
        chosen = next((s for s in snaps if s["sha8"] == version or s["ts"].startswith(version)), None)
        if not chosen:
            return {"ok": False, "error": f"no snapshot matching version: {version}"}
    snap_path = Path(chosen["snapshot"])
    if not snap_path.exists():
        return {"ok": False, "error": f"snapshot file missing on disk: {snap_path}"}
    # Resolve destination
    if dest:
        target = Path(dest)
    else:
        # write back to original location
        src_root = next(Path(s["root"]) for s in cfg["sources"] if s["name"] == info["source"])
        target = src_root / info["rel_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + f".restore.{os.urandom(4).hex()}")
    shutil.copy2(snap_path, tmp)
    os.replace(tmp, target)
    log_call("restore", path=str(target), from_snapshot=str(snap_path), sha8=chosen["sha8"])
    return {"ok": True, "restored_to": str(target), "from": str(snap_path), "sha8": chosen["sha8"], "ts": chosen["ts"]}


@mcp.tool()
def cleanup(dry_run: bool = False) -> dict[str, Any]:
    """Apply retention policy to snapshot directory + manifest.

    Policy (from config):
      - keep_minimum_versions: never prune below this many per file
      - keep_versions_within_days: always keep snapshots within this window
      - max_versions_per_file: hard cap; oldest pruned first
    """
    cfg = load_config()
    policy = cfg.get("policy", {}).get("retention", {})
    keep_min = policy.get("keep_minimum_versions", 5)
    keep_window_days = policy.get("keep_versions_within_days", 7)
    max_versions = policy.get("max_versions_per_file", 30)
    manifest_path = Path(cfg.get("manifest_path"))
    if not manifest_path.exists():
        return {"ok": True, "removed": 0, "kept": 0, "freed_bytes": 0, "note": "no manifest yet"}

    # Group manifest entries by (source, rel_path)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for line in manifest_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        groups.setdefault((r.get("source"), r.get("rel_path")), []).append(r)

    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_window_days)
    keep_entries: list[dict[str, Any]] = []
    remove_entries: list[dict[str, Any]] = []
    for (src, rel), entries in groups.items():
        entries.sort(key=lambda r: r.get("ts", ""))
        n = len(entries)
        # Decide keep/remove per entry
        for idx, e in enumerate(entries):
            try:
                ts = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
            except Exception:
                keep_entries.append(e)
                continue
            within_window = ts >= cutoff
            from_top = (n - 1 - idx)  # 0 = newest
            keep_for_min = from_top < keep_min
            keep_for_cap = from_top < max_versions
            if (within_window or keep_for_min) and keep_for_cap:
                keep_entries.append(e)
            else:
                remove_entries.append(e)

    freed = 0
    removed = 0
    for e in remove_entries:
        snap = Path(e.get("snapshot", ""))
        size = e.get("size", 0)
        if snap.exists():
            if not dry_run:
                try:
                    snap.unlink()
                except Exception:
                    continue
            freed += size
            removed += 1

    # Rewrite manifest with kept entries only
    if not dry_run and remove_entries:
        tmp = manifest_path.with_suffix(f".tmp.{os.urandom(4).hex()}")
        tmp.write_text("\n".join(json.dumps(e) for e in keep_entries) + "\n", encoding="utf-8")
        os.replace(tmp, manifest_path)

    log_call("cleanup", removed=removed, kept=len(keep_entries), freed_bytes=freed, dry_run=dry_run)
    return {"ok": True, "removed": removed, "kept": len(keep_entries), "freed_bytes": freed, "dry_run": dry_run}


@mcp.tool()
def diff(path: str, source: str | None = None) -> dict[str, Any]:
    """Compare current file sha to its most-recent snapshot sha."""
    log_call("diff", path=path[:200])
    cfg = load_config()
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": "current path does not exist"}
    info = list_versions(path, source=source)
    if not info.get("ok"):
        return info
    current_sha = sha256_file(p)
    versions = info["versions"]
    if not versions:
        return {"ok": True, "changed": True, "current_sha": current_sha, "snapshot_sha": None, "note": "no prior snapshot"}
    latest = versions[-1]
    return {"ok": True, "changed": current_sha[:8] != latest["sha8"], "current_sha": current_sha,
            "snapshot_sha": latest["sha8"], "last_snapshot_ts": latest["ts"]}


@mcp.tool()
def config() -> dict[str, Any]:
    """Return the active watch-list config (read-only view)."""
    log_call("config")
    cfg = load_config()
    return cfg


@mcp.tool()
def health() -> dict[str, Any]:
    """Counts + sizes for the snapshot tree."""
    log_call("health")
    cfg = load_config() if CONFIG_PATH.exists() else {}
    snap_root = Path(cfg.get("snapshot_root", DEFAULT_BACKUP_ROOT / "snapshots"))
    total = 0
    bytes_total = 0
    if snap_root.exists():
        for p in snap_root.rglob("*"):
            if p.is_file():
                total += 1
                try:
                    bytes_total += p.stat().st_size
                except OSError:
                    pass
    return {
        "ok": True,
        "agent": "custodian",
        "config_path": str(CONFIG_PATH),
        "config_exists": CONFIG_PATH.exists(),
        "snapshot_root": str(snap_root),
        "manifest_path": cfg.get("manifest_path"),
        "snapshot_count": total,
        "snapshot_total_bytes": bytes_total,
        "sources": [s.get("name") for s in cfg.get("sources", [])],
    }


if __name__ == "__main__":
    mcp.run()
