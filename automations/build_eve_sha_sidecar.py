#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# build_eve_sha_sidecar.py -- Emit *.sha256 sidecars for canonical deliverables.
#
# Purpose: the auto-updater (`eve_self_update.py`) fetches small text files
# `<file>.sha256` from GitHub raw to decide whether the local copy is stale.
# This script regenerates each sidecar after every rebuild so the published
# hash always matches the published binary/script.
#
# Canonical defaults (RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q extension --
# operator hard-canonical "treated with the same amount of love"):
#   D:/Sinister Sanctum/EVE.exe
#   D:/Sinister Sanctum/Sinister Start.bat   (one-click launcher; Leo gets same)
#
# Usage:
#   python automations/build_eve_sha_sidecar.py
#       -> builds sidecars for BOTH default targets
#   python automations/build_eve_sha_sidecar.py --path P [--path Q ...]
#       -> overrides default list; pass --path repeatedly for N targets
#   python automations/build_eve_sha_sidecar.py --check
#       -> verify only, no write (exit 0 if ALL targets match)
#
# Output format: single line of 64 lowercase hex chars + trailing newline.

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: dual-target default list (EVE.exe +
# Sinister Start.bat). Pass --path to override; pass --path repeatedly for N.
DEFAULT_TARGETS = [
    REPO_ROOT / "EVE.exe",
    REPO_ROOT / "Sinister Start.bat",
]
CHUNK = 1024 * 256


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def process_one(target: Path, check_only: bool) -> int:
    """Return 0 on ok, 1 on drift (check-mode), 2 on missing file."""
    if not target.is_file():
        print(f"[build_eve_sha_sidecar] not found: {target}", file=sys.stderr)
        return 2

    digest = sha256_file(target)
    sidecar = target.with_name(target.name + ".sha256")

    if check_only:
        if sidecar.is_file() and sidecar.read_text(encoding="utf-8").strip() == digest:
            print(f"[build_eve_sha_sidecar] OK    {digest} -> {sidecar}")
            return 0
        print(f"[build_eve_sha_sidecar] DRIFT {digest} vs sidecar={sidecar}")
        return 1

    sidecar.write_text(digest + "\n", encoding="utf-8")
    print(f"[build_eve_sha_sidecar] wrote {sidecar} ({digest})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write <file>.sha256 sidecars.")
    ap.add_argument("--path", action="append", default=None,
                    help="Target path (repeatable). Default: EVE.exe + Sinister Start.bat.")
    ap.add_argument("--check", action="store_true", help="Verify only; do not write.")
    ns = ap.parse_args(argv or sys.argv[1:])

    targets = [Path(p) for p in (ns.path or [])] or list(DEFAULT_TARGETS)

    worst = 0
    for t in targets:
        rc = process_one(t, ns.check)
        # Bubble up the worst exit code (2 > 1 > 0).
        if rc > worst:
            worst = rc
    return worst


if __name__ == "__main__":
    sys.exit(main())
