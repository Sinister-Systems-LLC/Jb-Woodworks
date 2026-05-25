#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
#
# sync_eve_internal.py — mirror PyInstaller _internal/ from ~/.eve/ to repo
# root + deploy/ targets so EVE.exe runs from any of those locations.
#
# Why this exists: EVE.exe is a PyInstaller --onedir bundle. Without a
# sibling _internal/ directory (python312.dll + 55 other deps) it fails
# with PYI-47016 "Failed to load Python DLL". Sub-D iter-22 caught this:
# repo-root EVE.exe + deploy/EVE.exe both crashed because _internal/ only
# lived in ~/.eve/. Now this script keeps all three copies parity.
#
# Idempotent. Safe to run after every verify-eve-features.ps1 rebuild.

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
SOURCE = Path.home() / ".eve" / "_internal"
TARGETS = [
    SANCTUM_ROOT / "_internal",
    SANCTUM_ROOT / "deploy" / "_internal",
]


def hash_dir(p: Path) -> str:
    if not p.is_dir():
        return ""
    h = hashlib.sha256()
    for f in sorted(p.rglob("*")):
        if f.is_file():
            h.update(f.name.encode())
            h.update(str(f.stat().st_size).encode())
    return h.hexdigest()[:16]


def sync_one(src: Path, dst: Path, *, dry_run: bool) -> tuple[str, str]:
    if not src.is_dir():
        return ("source-missing", str(src))
    if dst.is_dir() and hash_dir(src) == hash_dir(dst):
        return ("in-sync", str(dst))
    if dry_run:
        return ("would-mirror", str(dst))
    if dst.is_dir():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return ("mirrored", str(dst))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not SOURCE.is_dir():
        print(f"ERROR: source {SOURCE} missing — run verify-eve-features.ps1 -AutoRebuild first", file=sys.stderr)
        return 2

    rc = 0
    for t in TARGETS:
        action, path = sync_one(SOURCE, t, dry_run=args.dry_run)
        print(f"{action}\t{path}")
        if action.startswith("source-missing"):
            rc = 3
    return rc


if __name__ == "__main__":
    sys.exit(main())
