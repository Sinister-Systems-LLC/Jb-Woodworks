#!/usr/bin/env python3
"""loop_checkpoint.py — checkpoint + revert-to-peak for the quality-monotonic loop.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 ~12:55Z (verbatim):
  "i need the loop system going and i need a forever updating option that
   stops once quality goes down and reverts back to the peak of the part"
And ~13:05Z:
  "i need you to have real loop in this and real swarm how jcode does"

PURPOSE
=======
`quality-monotonic-loop.ps1` already detects regression / plateau and stops.
What was missing: per-iter CHECKPOINT and auto-RESTORE-TO-PEAK on regression.
This module fills that gap.

DESIGN
======
File-snapshot strategy (NOT git stash) because the Sanctum repo is shared
across ~10 concurrent agents — a global stash race-conditions every lane.
Instead, each iteration snapshots the lane's OWNED paths into
`_shared-memory/loop-checkpoints/<lane>/<run_id>-iter<N>/` as a plain
file mirror plus a `manifest.json` with sha256 + bytes per file.

Restore reads `_shared-memory/quality-loop-log.jsonl` filtered to
(lane, run_id), picks the iter with max score, and copies its mirror
back into the working tree. Lane stays decoupled — restore only touches
the paths the lane snapshotted.

USAGE
=====
CLI (called from quality-monotonic-loop.ps1):
  python loop_checkpoint.py save --lane LANE --run-id RUNID --iter N \
      --paths automations/eve-launcher tools/eve-picker --sanctum-root ROOT
  python loop_checkpoint.py restore-best --lane LANE --run-id RUNID
  python loop_checkpoint.py list --lane LANE

Import:
  from loop_checkpoint import save, restore_best
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys
import time

DEFAULT_SANCTUM = "D:/Sinister Sanctum"
SKIP_PARTS = {
    "__pycache__", "build", "dist", "node_modules", ".next",
    ".git", ".venv", "venv", "target", ".cache", ".pytest_cache",
}


def _now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_paths(root: pathlib.Path, rel_targets: list[str]):
    """Yield (abs, rel) for each file under each target path. Skips SKIP_PARTS.

    iter-27: switched from src.rglob('*') to os.walk so we can PRUNE
    SKIP_PARTS directories before descending into them. Prior version
    descended into `build/` (etc.) first and only filtered post-discovery,
    which blew up on Windows when build/ contained Linux-side WSL
    symlinks/junctions (sinister-os build/_work/.../airootfs/bin OSError
    1920). Also tolerate per-file PermissionError so one bad symlink
    doesn't kill the whole checkpoint."""
    import os as _os
    for rel in rel_targets:
        src = root / rel
        if not src.exists():
            continue
        if src.is_file():
            yield src, pathlib.Path(rel)
            continue
        for dirpath, dirnames, filenames in _os.walk(str(src), followlinks=False):
            # PRUNE: remove SKIP_PARTS subdirs from descent in-place
            dirnames[:] = [d for d in dirnames if d not in SKIP_PARTS]
            for fn in filenames:
                p = pathlib.Path(dirpath) / fn
                try:
                    rel_p = p.relative_to(root)
                except ValueError:
                    continue
                if any(part in SKIP_PARTS for part in rel_p.parts):
                    continue
                try:
                    if not p.is_file():
                        continue
                except OSError:
                    continue  # skip on permission/symlink issues
                yield p, rel_p


def save(lane: str, run_id: str, iter_n: int, paths: list[str], sanctum_root: str) -> dict:
    root = pathlib.Path(sanctum_root).resolve()
    ckpt_root = root / "_shared-memory" / "loop-checkpoints" / lane / f"{run_id}-iter{iter_n}"
    ckpt_root.mkdir(parents=True, exist_ok=True)
    manifest: dict = {
        "lane": lane,
        "run_id": run_id,
        "iter": iter_n,
        "ts_utc": _now_utc(),
        "paths": list(paths),
        "files": [],
    }
    for src, rel in _iter_paths(root, paths):
        dst = ckpt_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except (PermissionError, OSError) as e:
            manifest.setdefault("skipped", []).append({"path": str(rel), "error": str(e)})
            continue
        try:
            sz = src.stat().st_size
            sha = _sha256_file(src)
        except OSError as e:
            manifest.setdefault("skipped", []).append({"path": str(rel), "error": str(e)})
            continue
        manifest["files"].append({"path": str(rel).replace("\\", "/"), "sha256": sha, "bytes": sz})
    (ckpt_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"ok": True, "checkpoint": str(ckpt_root), "files": len(manifest["files"])}


def _read_log_best(log_path: pathlib.Path, lane: str, run_id: str) -> tuple[int, float]:
    best_iter, best_score = -1, float("-inf")
    if not log_path.exists():
        return best_iter, best_score
    with log_path.open(encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if r.get("run_id") != run_id or r.get("lane") != lane:
                continue
            sc = r.get("score")
            if sc is None or not isinstance(sc, (int, float)):
                continue
            if sc > best_score:
                best_score = float(sc)
                best_iter = int(r.get("iter", -1))
    return best_iter, best_score


def restore_best(lane: str, run_id: str, sanctum_root: str) -> dict:
    root = pathlib.Path(sanctum_root).resolve()
    log = root / "_shared-memory" / "quality-loop-log.jsonl"
    best_iter, best_score = _read_log_best(log, lane, run_id)
    if best_iter < 0:
        return {"ok": False, "error": f"no scored iter for lane={lane} run_id={run_id}"}
    ckpt_root = root / "_shared-memory" / "loop-checkpoints" / lane / f"{run_id}-iter{best_iter}"
    manifest_path = ckpt_root / "manifest.json"
    if not manifest_path.exists():
        return {"ok": False, "error": f"checkpoint missing: {ckpt_root}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    restored: list[str] = []
    failed: list[dict] = []
    for entry in manifest.get("files", []):
        rel = entry["path"]
        src = ckpt_root / rel
        dst = root / rel
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(rel)
        except (PermissionError, OSError) as e:
            failed.append({"path": rel, "error": str(e)})
    return {
        "ok": len(failed) == 0,
        "restored_iter": best_iter,
        "best_score": best_score,
        "files_restored": len(restored),
        "files_failed": failed,
    }


def list_checkpoints(lane: str, sanctum_root: str) -> dict:
    root = pathlib.Path(sanctum_root).resolve()
    base = root / "_shared-memory" / "loop-checkpoints" / lane
    if not base.exists():
        return {"ok": True, "checkpoints": []}
    rows = []
    for p in sorted(base.iterdir()):
        if not p.is_dir():
            continue
        mp = p / "manifest.json"
        meta = {"name": p.name}
        if mp.exists():
            try:
                m = json.loads(mp.read_text(encoding="utf-8"))
                meta["iter"] = m.get("iter")
                meta["ts_utc"] = m.get("ts_utc")
                meta["files"] = len(m.get("files", []))
            except json.JSONDecodeError:
                pass
        rows.append(meta)
    return {"ok": True, "checkpoints": rows}


def prune(lane: str, sanctum_root: str, keep_runs: int = 5) -> dict:
    """Keep only the last N run_ids per lane to avoid unbounded growth."""
    root = pathlib.Path(sanctum_root).resolve()
    base = root / "_shared-memory" / "loop-checkpoints" / lane
    if not base.exists():
        return {"ok": True, "removed": 0}
    by_run: dict[str, list[pathlib.Path]] = {}
    for p in base.iterdir():
        if not p.is_dir():
            continue
        run_id = p.name.split("-iter", 1)[0]
        by_run.setdefault(run_id, []).append(p)
    runs_sorted = sorted(by_run.keys(), reverse=True)
    to_remove = runs_sorted[keep_runs:]
    removed = 0
    for run_id in to_remove:
        for d in by_run[run_id]:
            try:
                shutil.rmtree(d)
                removed += 1
            except OSError:
                continue
    return {"ok": True, "removed": removed, "kept_runs": runs_sorted[:keep_runs]}


def main() -> int:
    p = argparse.ArgumentParser(description="Loop checkpoint manager (save/restore-best/list/prune)")
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("save", help="snapshot lane paths for a given iter")
    s.add_argument("--lane", required=True)
    s.add_argument("--run-id", required=True)
    s.add_argument("--iter", dest="iter_n", type=int, required=True)
    s.add_argument("--paths", nargs="+", required=True,
                   help="repo-relative paths (files or dirs) to checkpoint")
    s.add_argument("--sanctum-root", default=DEFAULT_SANCTUM)

    r = sp.add_parser("restore-best", help="restore the peak-score iter for (lane, run_id)")
    r.add_argument("--lane", required=True)
    r.add_argument("--run-id", required=True)
    r.add_argument("--sanctum-root", default=DEFAULT_SANCTUM)

    l = sp.add_parser("list", help="list checkpoints for a lane")
    l.add_argument("--lane", required=True)
    l.add_argument("--sanctum-root", default=DEFAULT_SANCTUM)

    pr = sp.add_parser("prune", help="keep only last N run_ids per lane")
    pr.add_argument("--lane", required=True)
    pr.add_argument("--keep-runs", type=int, default=5)
    pr.add_argument("--sanctum-root", default=DEFAULT_SANCTUM)

    args = p.parse_args()
    try:
        if args.cmd == "save":
            out = save(args.lane, args.run_id, args.iter_n, args.paths, args.sanctum_root)
        elif args.cmd == "restore-best":
            out = restore_best(args.lane, args.run_id, args.sanctum_root)
        elif args.cmd == "list":
            out = list_checkpoints(args.lane, args.sanctum_root)
        elif args.cmd == "prune":
            out = prune(args.lane, args.sanctum_root, args.keep_runs)
        else:
            out = {"ok": False, "error": f"unknown cmd {args.cmd}"}
    except Exception as e:
        out = {"ok": False, "error": str(e), "type": type(e).__name__}
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
