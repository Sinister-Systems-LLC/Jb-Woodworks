#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# build_eve_sha_sidecar.py -- Emit EVE.exe.sha256 sidecar next to EVE.exe.
#
# Purpose: the auto-updater (`eve_self_update.py`) fetches a small text file
# `EVE.exe.sha256` from GitHub raw to decide whether the local binary is
# stale. This script regenerates that sidecar after every EVE.exe rebuild
# so the published hash always matches the published binary.
#
# Usage:
#   python automations/build_eve_sha_sidecar.py            # default repo EVE.exe
#   python automations/build_eve_sha_sidecar.py --path P   # custom location
#   python automations/build_eve_sha_sidecar.py --check    # verify only, no write
#
# Output format: single line of 64 lowercase hex chars + trailing newline.

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVE = REPO_ROOT / "EVE.exe"
CHUNK = 1024 * 256


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write EVE.exe.sha256 sidecar.")
    ap.add_argument("--path", default=str(DEFAULT_EVE), help="EVE.exe path")
    ap.add_argument("--check", action="store_true", help="Verify only; do not write.")
    ns = ap.parse_args(argv or sys.argv[1:])

    eve = Path(ns.path)
    if not eve.is_file():
        print(f"[build_eve_sha_sidecar] not found: {eve}", file=sys.stderr)
        return 2

    digest = sha256_file(eve)
    sidecar = eve.with_name(eve.name + ".sha256")

    if ns.check:
        if sidecar.is_file() and sidecar.read_text(encoding="utf-8").strip() == digest:
            print(f"[build_eve_sha_sidecar] OK {digest} -> {sidecar}")
            return 0
        print(f"[build_eve_sha_sidecar] DRIFT {digest} vs sidecar={sidecar}")
        return 1

    sidecar.write_text(digest + "\n", encoding="utf-8")
    print(f"[build_eve_sha_sidecar] wrote {sidecar} ({digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
