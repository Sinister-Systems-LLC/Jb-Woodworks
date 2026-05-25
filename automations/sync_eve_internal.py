#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
#
# sync_eve_internal.py — mirror PyInstaller _internal/ + Sinister Start.bat
# from canonical sources to repo root + ~/.eve + deploy/ targets so EVE.exe
# AND the one-click launcher run from any of those locations.
#
# Why this exists: EVE.exe is a PyInstaller --onedir bundle. Without a
# sibling _internal/ directory (python312.dll + 55 other deps) it fails
# with PYI-47016 "Failed to load Python DLL". Sub-D iter-22 caught this:
# repo-root EVE.exe + deploy/EVE.exe both crashed because _internal/ only
# lived in ~/.eve/. Now this script keeps all three copies parity.
#
# RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: also mirrors Sinister Start.bat
# (operator hard-canonical "treated with the same amount of love") so all
# three EVE.exe locations have the matching one-click launcher next to them.
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

# RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: Sinister Start.bat lives at repo
# root (operator hard-canonical 07:13Z "place a sinister start bat at the
# main of the sinister sanctum"). Mirror to ~/.eve + deploy/.
BAT_SOURCE = SANCTUM_ROOT / "Sinister Start.bat"
BAT_TARGETS = [
    Path.home() / ".eve" / "Sinister Start.bat",
    SANCTUM_ROOT / "deploy" / "Sinister Start.bat",
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


def hash_file(p: Path) -> str:
    if not p.is_file():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
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


def sync_one_file(src: Path, dst: Path, *, dry_run: bool) -> tuple[str, str]:
    """File-level mirror (Sinister Start.bat). Sub-Q 2026-05-25T07:17Z."""
    if not src.is_file():
        return ("source-missing", str(src))
    if dst.is_file() and hash_file(src) == hash_file(dst):
        return ("in-sync", str(dst))
    if dry_run:
        return ("would-mirror", str(dst))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
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
    # Sinister Start.bat mirror (Sub-Q extension). Soft-warn (rc=0) if missing
    # so cold-start environments without the .bat don't fail the whole sync.
    if BAT_SOURCE.is_file():
        for bt in BAT_TARGETS:
            action, path = sync_one_file(BAT_SOURCE, bt, dry_run=args.dry_run)
            print(f"{action}\t{path}")
    else:
        print(f"warn-bat-missing\t{BAT_SOURCE}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
