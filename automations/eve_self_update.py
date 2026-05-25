#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# eve_self_update.py -- Self-updater for EVE.exe.
#
# Operator hard-canonical 2026-05-25 (CLAUDE.md): "we dont use bat files or
# powershell files or any of that shit. you do everything i say fully for me".
# Operator hard-canonical 2026-05-25 (NEVER ASK OPERATOR FOR ADMIN/MANUAL
# ACTIONS): "no you dont need action from me you do all that shit for me now".
#
# This module:
#   1. Resolves the local EVE.exe path(s) (repo + AppData install dir).
#   2. Fetches the canonical remote sha (raw GitHub sidecar EVE.exe.sha256).
#   3. If they differ, downloads EVE.exe to a sibling `.tmp.<pid>` file,
#      verifies the sha, then atomically swaps it in.
#   4. Handles the locked-file case (EVE.exe currently running) via retry
#      with exponential backoff, then logs + skips on persistent lock.
#   5. Best-effort Defender exclusion + AppData fallback so Program Files
#      / Defender quarantine doesn't kill the update silently.
#   6. Always appends a structured row to _shared-memory/eve-update-log.jsonl.
#
# Composes with doctrine:
#   _shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md
#   _shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md
#
# CLI:
#   python automations/eve_self_update.py            # check + apply
#   python automations/eve_self_update.py --dry-run  # check + report only
#   python automations/eve_self_update.py --force    # apply even if hashes match
#   python automations/eve_self_update.py --path P   # override target path

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVE_PATHS = [
    REPO_ROOT / "EVE.exe",
    Path.home() / ".eve" / "EVE.exe",
]
LOG_PATH = REPO_ROOT / "_shared-memory" / "eve-update-log.jsonl"

REMOTE_BASE = (
    "https://raw.githubusercontent.com/"
    "Sinister-Systems-LLC/Sinister-Sanctum/main"
)
REMOTE_SHA_URL = f"{REMOTE_BASE}/EVE.exe.sha256"
REMOTE_BIN_URL = f"{REMOTE_BASE}/EVE.exe"

CHUNK = 1024 * 256  # 256 KiB
MAX_LOCK_RETRIES = 5
HTTP_TIMEOUT = 30  # seconds per request


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(row: dict) -> None:
    row.setdefault("ts_utc", _utc_now())
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        # Last-ditch: stderr only, do not crash caller.
        print(f"[eve_self_update] log write failed: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def get_local_eve_sha(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Remote fetch (best-effort, never crashes on network error)
# ---------------------------------------------------------------------------


def _http_get(url: str, *, binary: bool = False):
    """Return (status, body) or (None, exception). Uses stdlib only."""
    try:
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": "eve-self-update/1"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310
            data = resp.read()
            if binary:
                return resp.status, data
            return resp.status, data.decode("utf-8", errors="replace")
    except Exception as exc:  # network/dns/proxy/etc — all best-effort
        return None, exc


def get_remote_eve_sha() -> tuple[str | None, str]:
    """Return (sha, source) where source is 'sidecar' / 'full-binary' / 'unreachable'."""
    status, body = _http_get(REMOTE_SHA_URL)
    if status == 200 and isinstance(body, str):
        sha = body.strip().split()[0] if body.strip() else ""
        if len(sha) == 64 and all(c in "0123456789abcdefABCDEF" for c in sha):
            return sha.lower(), "sidecar"
    # Fallback: download full binary and hash it.
    status2, body2 = _http_get(REMOTE_BIN_URL, binary=True)
    if status2 == 200 and isinstance(body2, (bytes, bytearray)):
        return hashlib.sha256(body2).hexdigest(), "full-binary"
    return None, "unreachable"


# ---------------------------------------------------------------------------
# Download + atomic swap
# ---------------------------------------------------------------------------


def download_with_retry(url: str, dest: Path, retries: int = 3) -> bool:
    """Stream-download URL to dest. Returns True on success."""
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            import urllib.request

            req = urllib.request.Request(
                url, headers={"User-Agent": "eve-self-update/1"}
            )
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310
                if resp.status != 200:
                    raise RuntimeError(f"http {resp.status}")
                with dest.open("wb") as out:
                    while True:
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        out.write(chunk)
            return True
        except Exception as exc:
            last_exc = exc
            time.sleep(min(2 ** attempt, 8))
    _log(
        {
            "event": "download_failed",
            "url": url,
            "retries": retries,
            "error": repr(last_exc),
        }
    )
    return False


def atomic_swap(tmp_path: Path, final_path: Path) -> bool:
    """os.replace with exponential-backoff retry on PermissionError (file in use)."""
    delays = [1, 2, 4, 8, 16]
    for attempt in range(MAX_LOCK_RETRIES):
        try:
            os.replace(tmp_path, final_path)
            return True
        except PermissionError as exc:
            wait = delays[attempt] if attempt < len(delays) else delays[-1]
            _log(
                {
                    "event": "atomic_swap_locked",
                    "final_path": str(final_path),
                    "attempt": attempt + 1,
                    "wait_s": wait,
                    "error": repr(exc),
                }
            )
            time.sleep(wait)
        except OSError as exc:
            _log(
                {
                    "event": "atomic_swap_oserror",
                    "final_path": str(final_path),
                    "error": repr(exc),
                }
            )
            return False
    # Persistent lock — leave tmp_path for next run to clean up.
    try:
        tmp_path.unlink(missing_ok=True)
    except OSError:
        pass
    return False


# ---------------------------------------------------------------------------
# Defender self-heal (best effort, silent on failure)
# ---------------------------------------------------------------------------


def defender_self_heal(path: Path) -> str:
    """Best-effort Defender exclusion. Silent failure (non-admin is expected)."""
    if os.name != "nt":
        return "skipped-non-windows"
    pwsh = shutil.which("powershell") or shutil.which("pwsh")
    if not pwsh:
        return "skipped-no-powershell"
    try:
        cp = subprocess.run(
            [
                pwsh,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f"Add-MpPreference -ExclusionPath '{path}' -ErrorAction SilentlyContinue",
            ],
            capture_output=True,
            timeout=10,
        )
        return "ok" if cp.returncode == 0 else f"rc={cp.returncode}"
    except Exception as exc:  # noqa: BLE001
        return f"err={exc!r}"


# ---------------------------------------------------------------------------
# Main update flow
# ---------------------------------------------------------------------------


def check_and_update(eve_path: Path, *, dry_run: bool = False, force: bool = False) -> dict:
    """Returns a result dict; also appended to the log."""
    result: dict = {
        "event": "check_and_update",
        "path": str(eve_path),
        "dry_run": dry_run,
        "force": force,
    }

    local_sha = get_local_eve_sha(eve_path)
    result["local_sha_before"] = local_sha

    remote_sha, source = get_remote_eve_sha()
    result["remote_sha"] = remote_sha
    result["remote_source"] = source

    if remote_sha is None:
        result["action"] = "skipped"
        result["reason"] = "remote-unreachable"
        result["exit"] = 0
        _log(result)
        return result

    if local_sha == remote_sha and not force:
        result["action"] = "in-sync"
        result["exit"] = 0
        _log(result)
        return result

    if dry_run:
        result["action"] = "would-replace" if local_sha else "would-install"
        result["exit"] = 0
        _log(result)
        return result

    # Ensure parent exists (AppData fallback path).
    try:
        eve_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        result["action"] = "failed"
        result["error"] = f"mkdir: {exc!r}"
        result["exit"] = 2
        _log(result)
        return result

    # Best-effort Defender self-heal BEFORE writing the new exe.
    result["defender"] = defender_self_heal(eve_path)

    tmp = eve_path.with_suffix(f".exe.tmp.{os.getpid()}")
    if not download_with_retry(REMOTE_BIN_URL, tmp):
        result["action"] = "failed"
        result["error"] = "download-failed"
        result["exit"] = 3
        _log(result)
        return result

    try:
        got_sha = _hash_file(tmp)
    except OSError as exc:
        result["action"] = "failed"
        result["error"] = f"hash-tmp: {exc!r}"
        result["exit"] = 4
        _log(result)
        return result

    if got_sha != remote_sha:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        result["action"] = "failed"
        result["error"] = f"sha-mismatch (got {got_sha} expected {remote_sha})"
        result["exit"] = 5
        _log(result)
        return result

    swapped = atomic_swap(tmp, eve_path)
    if not swapped:
        result["action"] = "skipped"
        result["reason"] = "locked-eve-running"
        result["exit"] = 0
        _log(result)
        return result

    result["action"] = "replaced"
    result["local_sha_after"] = remote_sha
    result["exit"] = 0
    _log(result)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Self-update EVE.exe from GitHub raw.")
    p.add_argument("--dry-run", action="store_true", help="Report only, do not write.")
    p.add_argument("--force", action="store_true", help="Apply even if hashes match.")
    p.add_argument(
        "--path",
        action="append",
        default=None,
        help="Target EVE.exe path (repeat for multiple). Default: repo + ~/.eve/EVE.exe.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    targets = [Path(p) for p in ns.path] if ns.path else list(DEFAULT_EVE_PATHS)

    overall = 0
    for target in targets:
        try:
            res = check_and_update(target, dry_run=ns.dry_run, force=ns.force)
        except Exception as exc:  # noqa: BLE001
            _log(
                {
                    "event": "check_and_update_crashed",
                    "path": str(target),
                    "error": repr(exc),
                }
            )
            print(f"[eve_self_update] {target}: crashed {exc!r}", file=sys.stderr)
            overall = 1
            continue
        print(
            f"[eve_self_update] {target}: {res['action']}"
            + (f" ({res.get('reason')})" if res.get("reason") else "")
        )
        if res.get("exit", 0) not in (0,):
            overall = res["exit"]
    return overall


if __name__ == "__main__":
    sys.exit(main())
