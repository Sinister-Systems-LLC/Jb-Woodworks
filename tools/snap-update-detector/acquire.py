# Author: RKOJ-ELENO :: 2026-05-25
"""Phase 1 of the Snap auto-update pipeline.

Acquires a Snap APK from APKMirror for a target version. Verifies SHA256
when --expect-sha256 is supplied. Caches under ~/.sinister/snap-apk-cache/.
Idempotent: cache hit returns 0 without re-downloading.

Shared exit-code contract: 0 ok, 1 usage error, 2 env/network error.

Pipeline: poll.ps1 (Phase 0) -> acquire.py (this) -> snap-emulator-api
re-extracts hooks (Phase 2) -> smoke_test.py (Phase 3) -> deploy
(Phase 4, panel-owned) -> rollback.py (Phase 5) if smoke fails.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path

CACHE_DEFAULT = Path.home() / ".sinister" / "snap-apk-cache"
APKMIRROR_LISTING = "https://www.apkmirror.com/apk/snap-inc/snapchat/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def _setup_log(cache_dir: Path) -> logging.Logger:
    cache_dir.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("acquire")
    log.setLevel(logging.INFO)
    if not log.handlers:
        h = RotatingFileHandler(cache_dir / "acquire.log", maxBytes=262144, backupCount=10)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(h)
    return log


def _emit(d: dict) -> None:
    sys.stdout.write(json.dumps(d, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dest: Path, log: logging.Logger, retries: int = 1) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                size = 0
                with dest.open("wb") as f:
                    for chunk in iter(lambda: r.read(1 << 20), b""):
                        f.write(chunk)
                        size += len(chunk)
            log.info("downloaded %s -> %s (%d bytes)", url, dest, size)
            return size
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last_err = e
            log.warning("attempt %d failed: %s", attempt + 1, e)
    raise RuntimeError(f"download failed after {retries + 1} attempts: {last_err}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 1 Snap APK acquire (kernel-apk lane)")
    ap.add_argument("--version", required=True, help="Snap version e.g. 13.93.0.51")
    ap.add_argument("--cache-dir", default=str(CACHE_DEFAULT))
    ap.add_argument("--download-url", default=None, help="Direct APK URL (APKMirror final link)")
    ap.add_argument("--expect-sha256", default=None, help="Verify cached/downloaded APK matches")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cache = Path(args.cache_dir)
    log = _setup_log(cache)
    dest = cache / f"snap-{args.version}.apk"

    if args.dry_run:
        _emit({
            "ok": True, "phase": "acquire", "dry_run": True,
            "version": args.version,
            "listing_url": APKMIRROR_LISTING,
            "download_url": args.download_url,
            "cache_path": str(dest),
        })
        return 0

    if dest.exists():
        sha = _sha256_file(dest)
        if args.expect_sha256 and sha.lower() != args.expect_sha256.lower():
            _emit({"ok": False, "phase": "acquire", "error": "cache sha mismatch", "have": sha, "want": args.expect_sha256, "path": str(dest)})
            return 2
        _emit({"ok": True, "phase": "acquire", "cached": True, "version": args.version, "path": str(dest), "sha256": sha, "size_bytes": dest.stat().st_size})
        return 0

    if not args.download_url:
        _emit({"ok": False, "phase": "acquire", "error": "no --download-url and not cached; resolve final APKMirror link first", "listing_url": APKMIRROR_LISTING})
        return 2

    try:
        size = _download(args.download_url, dest, log)
    except Exception as e:
        _emit({"ok": False, "phase": "acquire", "error": str(e)})
        return 2

    sha = _sha256_file(dest)
    if args.expect_sha256 and sha.lower() != args.expect_sha256.lower():
        _emit({"ok": False, "phase": "acquire", "error": "downloaded sha mismatch", "have": sha, "want": args.expect_sha256, "path": str(dest)})
        return 2

    _emit({"ok": True, "phase": "acquire", "version": args.version, "path": str(dest), "sha256": sha, "size_bytes": size})
    return 0


if __name__ == "__main__":
    sys.exit(main())
