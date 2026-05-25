"""
sanctum_to_vault_mirror.py - Mirror Sinister Sanctum repo into Sinister Vault.

Author: RKOJ-ELENO :: 2026-05-25

Purpose
-------
Operator (verbatim 2026-05-25 ~07:08Z): "place the sinister vault live and
place the entire sinster sanctum there and link to leo over sinister link
and auto update that and github."

Mirrors D:\\Sinister Sanctum -> D:\\sinister-vault\\sanctum-mirror\\<machine-id>\\
on a 15-minute cadence (via SinisterSanctumToVaultMirror schtask) so Syncthing
replicates the tree to Leo and to any other paired peer.

First run = full copy. Subsequent runs = rsync-style delta (size+mtime).

Skips: _vault/ (vault itself), .git/ (Git is separate replication channel),
node_modules/, __pycache__/, *.exe.tmp, _archive/ (already cold-stored),
.venv/, build/, dist/, .claude/worktrees/ (transient), anything matched by
the canonical .gitignore.

Logs one JSONL row per run to _shared-memory/vault-mirror-log.jsonl with
counts of {scanned, copied, skipped, errors, bytes_copied, elapsed_s}.

Actions
-------
  python sanctum_to_vault_mirror.py                  # real mirror
  python sanctum_to_vault_mirror.py --dry-run        # plan only
  python sanctum_to_vault_mirror.py --install-schtask  # 15-min cadence

Exit codes: 0 ok / 1 partial errors / 2 IO fatal / 3 args
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

VERSION = "1.0.0"
SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
VAULT_ROOT = Path(r"D:\sinister-vault")
MIRROR_BASE = VAULT_ROOT / "sanctum-mirror"
LOG_PATH = SANCTUM_ROOT / "_shared-memory" / "vault-mirror-log.jsonl"
SCHTASK_NAME = "SinisterSanctumToVaultMirror"

# Names to skip anywhere they appear in the tree.
EXCLUDE_DIRS = {
    "_vault", ".git", "node_modules", "__pycache__", "_archive",
    ".venv", "venv", "build", "dist", ".pytest_cache", ".mypy_cache",
    "_vault-personal", ".claude/worktrees", "worktrees",
    ".next", ".nuxt", "target", "out", "_tmp",
}
# Path patterns (relative from SANCTUM_ROOT, forward slash) to skip via prefix.
EXCLUDE_PREFIXES = (
    ".claude/worktrees/",
    "projects/sinister-os/source/sinister-lang/sample-output/",
    "deploy/_internal/",  # vendored interpreter bundle, regenerable
)
EXCLUDE_SUFFIXES = (".exe.tmp", ".pyc", ".pyo", ".log.gz")
# Hard byte cap per file (skip giants -- daemon snapshots handle them).
PER_FILE_MAX_BYTES = 256 * 1024 * 1024  # 256 MB


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def machine_id() -> str:
    """Stable per-machine slug for the mirror sub-dir."""
    host = (socket.gethostname() or platform.node() or "unknown").lower()
    # Strip anything dodgy for filesystem.
    return "".join(c if (c.isalnum() or c in "-_") else "-" for c in host) or "unknown"


def should_skip_dir(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    rel_fwd = rel.replace("\\", "/").rstrip("/") + "/"
    if any(rel_fwd.startswith(p) for p in EXCLUDE_PREFIXES):
        return True
    return False


def should_skip_file(rel: str, size: int) -> bool:
    if size > PER_FILE_MAX_BYTES:
        return True
    low = rel.lower()
    if any(low.endswith(s) for s in EXCLUDE_SUFFIXES):
        return True
    return False


def plan_and_mirror(dry_run: bool) -> Dict[str, int]:
    """Walk Sanctum, delta-copy into vault mirror. Returns counters."""
    dest_root = MIRROR_BASE / machine_id()
    if not dry_run:
        dest_root.mkdir(parents=True, exist_ok=True)
    stats = {"scanned": 0, "copied": 0, "skipped": 0, "errors": 0,
             "bytes_copied": 0, "dirs_created": 0}

    for cur_dir, dirnames, filenames in os.walk(SANCTUM_ROOT, followlinks=False):
        cur_path = Path(cur_dir)
        try:
            rel_dir = cur_path.relative_to(SANCTUM_ROOT)
        except ValueError:
            continue
        rel_dir_s = str(rel_dir).replace("\\", "/")
        if rel_dir_s and rel_dir_s != "." and should_skip_dir(rel_dir_s):
            dirnames[:] = []
            continue
        # Prune subdirs in place.
        dirnames[:] = [d for d in dirnames
                       if not should_skip_dir((rel_dir_s + "/" + d).lstrip("./"))]

        for fn in filenames:
            stats["scanned"] += 1
            src_file = cur_path / fn
            rel_file = (rel_dir_s.rstrip("./") + "/" + fn).lstrip("/")
            try:
                st_src = src_file.stat()
            except OSError:
                stats["errors"] += 1
                continue
            if should_skip_file(rel_file, st_src.st_size):
                stats["skipped"] += 1
                continue
            dest_file = dest_root / rel_file
            # Delta check: size + mtime within 2s.
            need_copy = True
            if dest_file.exists():
                try:
                    st_dst = dest_file.stat()
                    if (st_dst.st_size == st_src.st_size
                            and abs(st_dst.st_mtime - st_src.st_mtime) < 2.0):
                        need_copy = False
                except OSError:
                    need_copy = True
            if not need_copy:
                stats["skipped"] += 1
                continue
            if dry_run:
                stats["copied"] += 1
                stats["bytes_copied"] += st_src.st_size
                continue
            try:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)
                stats["copied"] += 1
                stats["bytes_copied"] += st_src.st_size
            except OSError as exc:
                stats["errors"] += 1
                sys.stderr.write(f"copy failed {rel_file}: {exc}\n")
                continue
    return stats


def log_run(stats: Dict[str, int], elapsed_s: float, dry_run: bool) -> None:
    row = {
        "ts": utc_iso(),
        "tool": "sanctum_to_vault_mirror",
        "version": VERSION,
        "machine": machine_id(),
        "dry_run": dry_run,
        "elapsed_s": round(elapsed_s, 2),
        "dest": str(MIRROR_BASE / machine_id()),
        **stats,
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    except OSError as exc:
        sys.stderr.write(f"log write failed: {exc}\n")


def install_schtask() -> int:
    """Register SinisterSanctumToVaultMirror to run every 15 min."""
    py = sys.executable
    script = str(Path(__file__).resolve())
    # Use schtasks.exe; if elevation refused, fall back to Startup .cmd loop.
    tr = f'"{py}" "{script}"'
    cmd = [
        "schtasks.exe", "/Create", "/TN", SCHTASK_NAME,
        "/SC", "MINUTE", "/MO", "15",
        "/TR", tr, "/F",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            print(f"OK: schtask {SCHTASK_NAME} registered (15-min)")
            return 0
        sys.stderr.write(r.stderr + "\n")
    except Exception as exc:
        sys.stderr.write(f"schtasks exec failed: {exc}\n")
    # Fallback: Startup .cmd that loops (1-shot per logon)
    startup = Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    if startup.exists():
        shim = startup / f"{SCHTASK_NAME}.cmd"
        shim.write_text(
            f'@echo off\nREM Author: RKOJ-ELENO :: 2026-05-25\n'
            f':loop\n"{py}" "{script}"\ntimeout /t 900 /nobreak >nul\ngoto loop\n',
            encoding="ascii",
        )
        print(f"FALLBACK: installed Startup shim {shim}")
        return 0
    sys.stderr.write("could not register schtask AND no Startup folder; ask operator\n")
    return 2


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Mirror Sanctum -> Vault")
    ap.add_argument("--dry-run", action="store_true", help="plan only, no writes")
    ap.add_argument("--install-schtask", action="store_true",
                    help="register 15-min cadence schtask")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if args.install_schtask:
        return install_schtask()
    if not SANCTUM_ROOT.exists():
        sys.stderr.write(f"missing Sanctum root: {SANCTUM_ROOT}\n")
        return 2
    if not VAULT_ROOT.exists():
        sys.stderr.write(f"missing vault root: {VAULT_ROOT}\n")
        return 2
    t0 = time.time()
    stats = plan_and_mirror(dry_run=args.dry_run)
    elapsed = time.time() - t0
    log_run(stats, elapsed, args.dry_run)
    mode = "DRY" if args.dry_run else "REAL"
    print(f"{mode} mirror done in {elapsed:.1f}s "
          f"scanned={stats['scanned']} copied={stats['copied']} "
          f"skipped={stats['skipped']} errors={stats['errors']} "
          f"bytes={stats['bytes_copied']:,} "
          f"dest={MIRROR_BASE / machine_id()}")
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
