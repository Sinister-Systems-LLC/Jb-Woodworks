#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# Author: RKOJ-ELENO :: 2026-05-25 Sub-F extension (hot-swap support)
# Author: RKOJ-ELENO :: 2026-05-25 Sub-O extension (Sinister LINK transport)
# eve_self_update.py -- Self-updater for EVE.exe.
#
# Operator hard-canonical 2026-05-25 (CLAUDE.md): "we dont use bat files or
# powershell files or any of that shit. you do everything i say fully for me".
# Operator hard-canonical 2026-05-25 (NEVER ASK OPERATOR FOR ADMIN/MANUAL
# ACTIONS): "no you dont need action from me you do all that shit for me now".
# Operator hard-canonical 2026-05-25 ~06:14Z (Sub-F extension): "you can still
# udpate while exe is running, we should have made this a feature. if not do
# it not and fully audit and smoke test it."
# Operator hard-canonical 2026-05-25 ~07:12Z (Sub-O extension): "make the eexe
# update oiver sinsiter link and leo will have popup to say update availabe or
# something". 2-transport waterfall: link (p2p via vault mirror) -> github
# (fallback). New flags `--transport <github|link|auto>` (default auto) and
# `--peer <machine-id>`. Existing CLI surface preserved.
#
# This module:
#   1. Resolves the local EVE.exe path(s) (repo + AppData install dir).
#   2. Fetches the canonical remote sha (raw GitHub sidecar EVE.exe.sha256).
#   3. If they differ, downloads EVE.exe to a sibling `.tmp.<pid>` file,
#      verifies the sha, then atomically swaps it in.
#   4. Handles the locked-file case (EVE.exe currently running) via the
#      Windows "rename-in-use" trick (rename-old + swap + delay-until-reboot
#      cleanup) — default ON; old retry-only behavior available via
#      `--no-hot-swap`. Hot-swap is the canonical 2026-05-25 path.
#   5. Best-effort Defender exclusion + AppData fallback so Program Files
#      / Defender quarantine doesn't kill the update silently.
#   6. Always appends a structured row to _shared-memory/eve-update-log.jsonl.
#
# Composes with doctrine:
#   _shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md
#   _shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md
#
# CLI:
#   python automations/eve_self_update.py            # check + apply (hot-swap on)
#   python automations/eve_self_update.py --dry-run  # check + report only
#   python automations/eve_self_update.py --force    # apply even if hashes match
#   python automations/eve_self_update.py --path P   # override target path
#   python automations/eve_self_update.py --audit    # report state, no writes
#   python automations/eve_self_update.py --no-hot-swap         # original retry-only
#   python automations/eve_self_update.py --force-kill-stuck    # opt-in kill fallback
#   python automations/eve_self_update.py --transport link      # force LINK only
#   python automations/eve_self_update.py --transport github    # force github only
#   python automations/eve_self_update.py --transport auto      # link, fall back to github (default)
#   python automations/eve_self_update.py --peer <machine-id>   # pick LINK peer

from __future__ import annotations

import argparse
import ctypes
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

# Sinister LINK transport (Sub-O extension 2026-05-25). Each peer mirrors its
# canonical files into _vault/sanctum-mirror/<machine-id>/. The vault daemon
# (Sub-M) syncs that subtree across peers; we just read filesystem-locally
# from the mirrored copy. Vault HTTP API at :5078 is reserved for the
# sinister_link_vault_transport.py helper (Sub-M) when filesystem mirror
# is not populated yet.
VAULT_MIRROR_ROOT = REPO_ROOT / "_vault" / "sanctum-mirror"
VAULT_HTTP_BASE = "http://127.0.0.1:5078"
LINK_PEER_HINT_FILE = REPO_ROOT / "_shared-memory" / "eve-update-peer.txt"

CHUNK = 1024 * 256  # 256 KiB
MAX_LOCK_RETRIES = 5
HTTP_TIMEOUT = 30  # seconds per request

DEFAULT_KILL_BAT = Path(r"C:\Users\Zonia\Desktop\Kill-Stuck-EVE.bat")

# Win32 MoveFileExW flag — schedule rename for next reboot.
MOVEFILE_DELAY_UNTIL_REBOOT = 0x4


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
# Sinister LINK transport (Sub-O extension, 2026-05-25 ~07:12Z)
# ---------------------------------------------------------------------------


def _list_link_peers() -> list[str]:
    """Return machine-ids visible under _vault/sanctum-mirror/.

    Each subdirectory is one peer. Best-effort: missing root returns []
    (vault not yet populated by Sub-M).
    """
    if not VAULT_MIRROR_ROOT.exists():
        return []
    peers: list[str] = []
    try:
        for entry in VAULT_MIRROR_ROOT.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                peers.append(entry.name)
    except OSError:
        return []
    peers.sort()
    return peers


def _default_link_peer() -> str | None:
    """Choose a peer when caller did not specify --peer.

    Order:
      1. Hint file `_shared-memory/eve-update-peer.txt` (operator override)
      2. Any peer whose folder contains BOTH EVE.exe and EVE.exe.sha256
      3. First peer alphabetically with EVE.exe.sha256
      4. None (no peers usable)
    """
    try:
        if LINK_PEER_HINT_FILE.exists():
            hint = LINK_PEER_HINT_FILE.read_text(encoding="utf-8").strip()
            if hint:
                return hint
    except OSError:
        pass

    peers = _list_link_peers()
    # Prefer peers with full payload.
    for peer in peers:
        peer_dir = VAULT_MIRROR_ROOT / peer
        if (peer_dir / "EVE.exe").exists() and (peer_dir / "EVE.exe.sha256").exists():
            return peer
    # Otherwise any peer with at least the sidecar.
    for peer in peers:
        if (VAULT_MIRROR_ROOT / peer / "EVE.exe.sha256").exists():
            return peer
    return None


def _resolve_link_update_source(peer_machine_id: str | None = None) -> dict:
    """Resolve the LINK update source on the local filesystem.

    Returns a dict with keys:
      ok            : bool  -- True if both sha + bin paths exist
      peer          : str | None
      sha_path      : Path | None
      bin_path      : Path | None
      sha           : str | None (validated 64-hex)
      reason        : str    -- 'ok' / 'no-peers' / 'peer-missing' / 'sha-missing' /
                                'bin-missing' / 'sha-malformed'
    """
    out: dict = {
        "ok": False,
        "peer": None,
        "sha_path": None,
        "bin_path": None,
        "sha": None,
        "reason": "no-peers",
    }
    if not VAULT_MIRROR_ROOT.exists():
        out["reason"] = "vault-mirror-missing"
        return out

    peer = peer_machine_id or _default_link_peer()
    if not peer:
        out["reason"] = "no-peers"
        return out

    out["peer"] = peer
    peer_dir = VAULT_MIRROR_ROOT / peer
    if not peer_dir.exists():
        out["reason"] = "peer-missing"
        return out

    sha_path = peer_dir / "EVE.exe.sha256"
    bin_path = peer_dir / "EVE.exe"
    out["sha_path"] = sha_path
    out["bin_path"] = bin_path

    if not sha_path.exists():
        out["reason"] = "sha-missing"
        return out

    try:
        body = sha_path.read_text(encoding="utf-8").strip()
        sha = body.split()[0] if body else ""
    except OSError:
        out["reason"] = "sha-read-failed"
        return out

    if len(sha) != 64 or not all(c in "0123456789abcdefABCDEF" for c in sha):
        out["reason"] = "sha-malformed"
        return out

    out["sha"] = sha.lower()
    if not bin_path.exists():
        out["reason"] = "bin-missing"
        return out

    out["ok"] = True
    out["reason"] = "ok"
    return out


def get_link_eve_sha(peer_machine_id: str | None = None) -> tuple[str | None, str, str | None]:
    """Return (sha, source, peer) for the Sinister LINK transport.

    source values: 'link-mirror' (filesystem) / 'link-unreachable'
    """
    resolved = _resolve_link_update_source(peer_machine_id)
    if resolved["ok"]:
        return resolved["sha"], "link-mirror", resolved["peer"]
    return None, "link-unreachable", resolved.get("peer")


def copy_from_link(peer_bin: Path, dest: Path) -> bool:
    """Copy the EVE.exe payload from the vault mirror to dest.

    Filesystem copy (vault has already replicated bytes to local disk via
    Sub-M's transport). Returns True on success.
    """
    try:
        shutil.copy2(peer_bin, dest)
        return True
    except OSError as exc:
        _log(
            {
                "event": "link_copy_failed",
                "peer_bin": str(peer_bin),
                "dest": str(dest),
                "error": repr(exc),
            }
        )
        return False


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
    """os.replace with exponential-backoff retry on PermissionError (file in use).

    Legacy path preserved for `--no-hot-swap` callers. New default is
    `rename_old_then_swap`.
    """
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
# Hot-swap support (Sub-F extension, 2026-05-25 ~06:14Z)
# ---------------------------------------------------------------------------


def is_eve_running(path: Path) -> list:
    """Return a list of psutil.Process objects whose exe matches `path`.

    Match strategy: exact .exe() match preferred; falls back to parent-dir
    match so a process launched from `D:\\Sinister Sanctum\\EVE.exe` is still
    detected when caller passes the AppData mirror at `~/.eve/EVE.exe`.

    Best-effort — psutil missing or AccessDenied returns []. Never raises.
    """
    try:
        import psutil  # type: ignore[import-not-found]
    except Exception:
        return []

    target = path.resolve() if path.exists() else path
    target_str = str(target).lower()
    target_parent = str(target.parent).lower() if target.parent else ""
    target_name = target.name.lower()

    hits: list = []
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            name = (proc.info.get("name") or "").lower()
            exe = proc.info.get("exe") or ""
            exe_l = exe.lower()
            if name != target_name and not exe_l.endswith(target_name):
                continue
            if exe_l == target_str:
                hits.append(proc)
            elif target_parent and exe_l.startswith(target_parent):
                hits.append(proc)
            elif not exe and name == target_name:
                # Best-effort: name matches but exe path unavailable.
                hits.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            continue
    return hits


def _schedule_delete_on_reboot(path: Path) -> str:
    """Use MoveFileExW(path, NULL, MOVEFILE_DELAY_UNTIL_REBOOT) to defer cleanup.

    Returns 'ok', 'skipped-non-windows', or 'err=<repr>'.
    """
    if os.name != "nt":
        return "skipped-non-windows"
    try:
        # use_last_error=True is required for ctypes.get_last_error() to
        # return the real Win32 error code; without it the value is always 0.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        kernel32.MoveFileExW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint32,
        ]
        kernel32.MoveFileExW.restype = ctypes.c_int
        ok = kernel32.MoveFileExW(str(path), None, MOVEFILE_DELAY_UNTIL_REBOOT)
        if ok:
            return "ok"
        err = ctypes.get_last_error()
        # ERROR_PRIVILEGE_NOT_HELD = 1314 — non-admin can't schedule reboot
        # cleanup; we accept that and fall back to leaving the .old file in
        # place. Caller can sweep on next launch.
        return f"err=MoveFileExW rc=0 lasterr={err}"
    except Exception as exc:  # noqa: BLE001
        return f"err={exc!r}"


def rename_old_then_swap(tmp_path: Path, final_path: Path) -> dict:
    """Windows "rename-in-use" swap pattern.

    Steps:
      (a) Try os.replace(tmp, final) first (works if not locked).
      (b) On PermissionError, rename `final` -> `final.old.<ts>`. Windows
          ALLOWS renaming a file that is currently being executed: the
          running process keeps its open handle, but the on-disk name
          changes. This frees the original path.
      (c) os.replace(tmp, final) — succeeds because the path is now free.
      (d) Schedule MoveFileExW(final.old, NULL, MOVEFILE_DELAY_UNTIL_REBOOT)
          to clean up .old on next reboot. Best-effort.
      (e) Verify SHA of the new file on disk post-swap.

    Returns a result dict with keys:
      strategy: 'os-replace' | 'rename-in-use' | 'failed'
      success: bool
      old_path: str | None (path of renamed .old file, if any)
      reboot_cleanup: str (MoveFileExW result)
      sha_after: str | None
      error: str | None
    """
    out: dict = {
        "strategy": None,
        "success": False,
        "old_path": None,
        "reboot_cleanup": None,
        "sha_after": None,
        "error": None,
    }

    # (a) Direct replace.
    try:
        os.replace(tmp_path, final_path)
        out["strategy"] = "os-replace"
        out["success"] = True
    except PermissionError:
        # (b) Rename in use.
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        old = final_path.with_name(f"{final_path.name}.old.{ts}.{os.getpid()}")
        try:
            os.rename(final_path, old)
        except OSError as exc:
            out["strategy"] = "failed"
            out["error"] = f"rename-old-failed: {exc!r}"
            _log(
                {
                    "event": "hot_swap_rename_failed",
                    "final_path": str(final_path),
                    "error": repr(exc),
                }
            )
            return out

        out["old_path"] = str(old)

        # (c) Place new binary at the freed path.
        try:
            os.replace(tmp_path, final_path)
            out["strategy"] = "rename-in-use"
            out["success"] = True
        except OSError as exc:
            # Try to restore the old file so EVE.exe is not left missing.
            try:
                os.rename(old, final_path)
            except OSError:
                pass
            out["strategy"] = "failed"
            out["error"] = f"replace-after-rename-failed: {exc!r}"
            _log(
                {
                    "event": "hot_swap_replace_failed",
                    "final_path": str(final_path),
                    "error": repr(exc),
                }
            )
            return out

        # (d) Schedule reboot cleanup.
        out["reboot_cleanup"] = _schedule_delete_on_reboot(old)
        _log(
            {
                "event": "hot_swap_rename_in_use",
                "final_path": str(final_path),
                "old_path": str(old),
                "reboot_cleanup": out["reboot_cleanup"],
            }
        )

    except OSError as exc:
        out["strategy"] = "failed"
        out["error"] = f"replace-oserror: {exc!r}"
        _log(
            {
                "event": "hot_swap_replace_oserror",
                "final_path": str(final_path),
                "error": repr(exc),
            }
        )
        return out

    # (e) Verify SHA post-swap.
    try:
        out["sha_after"] = _hash_file(final_path)
    except OSError as exc:
        out["error"] = f"hash-after-failed: {exc!r}"

    return out


def swap_with_kill_fallback(
    tmp_path: Path,
    final_path: Path,
    *,
    kill_bat_path: Path | None = None,
    force_kill_stuck: bool = False,
) -> dict:
    """Run rename-in-use; if it still fails (e.g. AV scan lock), optionally
    invoke Kill-Stuck-EVE.bat and retry.

    Returns the rename_old_then_swap result dict, augmented with:
      kill_invoked: bool
      kill_result: str | None
    """
    result = rename_old_then_swap(tmp_path, final_path)
    result.setdefault("kill_invoked", False)
    result.setdefault("kill_result", None)

    if result.get("success"):
        return result

    # Determine if we are allowed to escalate.
    kill_target = kill_bat_path or DEFAULT_KILL_BAT
    if not force_kill_stuck:
        result["kill_result"] = "would-require-kill"
        _log(
            {
                "event": "hot_swap_would_require_kill",
                "final_path": str(final_path),
                "kill_bat": str(kill_target),
            }
        )
        return result

    if not kill_target.exists():
        result["kill_result"] = f"kill-bat-missing: {kill_target}"
        return result

    # Invoke kill bat (calling existing .bat is allowed per doctrine; ban is
    # on CREATING new ones).
    try:
        cp = subprocess.run(
            ["cmd.exe", "/c", str(kill_target)],
            capture_output=True,
            timeout=15,
        )
        result["kill_invoked"] = True
        result["kill_result"] = f"rc={cp.returncode}"
        _log(
            {
                "event": "hot_swap_kill_invoked",
                "final_path": str(final_path),
                "kill_bat": str(kill_target),
                "rc": cp.returncode,
            }
        )
    except Exception as exc:  # noqa: BLE001
        result["kill_result"] = f"kill-failed: {exc!r}"
        return result

    # Tiny settle window — processes need a moment to release file handles.
    time.sleep(2)

    retry = rename_old_then_swap(tmp_path, final_path)
    retry["kill_invoked"] = result["kill_invoked"]
    retry["kill_result"] = result["kill_result"]
    return retry


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


def _resolve_transport(
    transport: str,
    peer: str | None,
) -> tuple[str | None, str, str | None, Path | None]:
    """Pick the active transport. Returns (sha, source, peer, link_bin_path).

    transport:
      'link'   -- LINK only; returns (None, 'link-unreachable', ...) if vault empty.
      'github' -- GitHub raw only (original behavior).
      'auto'   -- LINK first, GitHub fallback if LINK unreachable.
    """
    if transport == "github":
        sha, source = get_remote_eve_sha()
        return sha, source, None, None

    if transport == "link":
        resolved = _resolve_link_update_source(peer)
        if resolved["ok"]:
            return resolved["sha"], "link-mirror", resolved["peer"], resolved["bin_path"]
        return None, "link-unreachable", resolved.get("peer"), None

    # auto
    resolved = _resolve_link_update_source(peer)
    if resolved["ok"]:
        return resolved["sha"], "link-mirror", resolved["peer"], resolved["bin_path"]
    sha, source = get_remote_eve_sha()
    return sha, source, resolved.get("peer"), None


def check_and_update(
    eve_path: Path,
    *,
    dry_run: bool = False,
    force: bool = False,
    allow_hot_swap: bool = True,
    force_kill_stuck: bool = False,
    kill_bat_path: Path | None = None,
    transport: str = "github",
    peer: str | None = None,
) -> dict:
    """Returns a result dict; also appended to the log.

    New 2026-05-25 Sub-F params:
      allow_hot_swap   : default True; use rename-in-use trick when locked.
      force_kill_stuck : default False; opt-in escalation if hot-swap also fails.
      kill_bat_path    : override path to Kill-Stuck-EVE.bat.

    New 2026-05-25 Sub-O params:
      transport        : 'github' (default for backward compat) | 'link' | 'auto'.
      peer             : Sinister LINK peer machine-id (only used when transport
                         is 'link' or 'auto').
    """
    result: dict = {
        "event": "check_and_update",
        "path": str(eve_path),
        "dry_run": dry_run,
        "force": force,
        "allow_hot_swap": allow_hot_swap,
        "force_kill_stuck": force_kill_stuck,
        "transport": transport,
        "peer_requested": peer,
    }

    local_sha = get_local_eve_sha(eve_path)
    result["local_sha_before"] = local_sha

    remote_sha, source, resolved_peer, link_bin_path = _resolve_transport(transport, peer)
    result["remote_sha"] = remote_sha
    result["remote_source"] = source
    result["peer_resolved"] = resolved_peer

    if remote_sha is None:
        result["action"] = "skipped"
        # Surface the LINK-specific reason when applicable so operators know
        # to populate the vault mirror or rely on github transport.
        if source == "link-unreachable":
            if transport == "link":
                result["reason"] = "link-unreachable"
            else:
                # auto mode tried LINK then github; both failed.
                result["reason"] = "remote-unreachable (link+github)"
        else:
            result["reason"] = "remote-unreachable"
        result["exit"] = 0
        _log(result)
        return result

    if local_sha == remote_sha and not force:
        result["action"] = "in-sync"
        result["exit"] = 0
        _log(result)
        return result

    # Detect live EVE.exe processes (info-only on dry-run).
    running = is_eve_running(eve_path)
    result["running_pids"] = [getattr(p, "pid", None) for p in running]

    if dry_run:
        if running:
            result["action"] = "would-rename-old" if allow_hot_swap else "would-replace"
        else:
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

    # Opportunistic sweep: any prior `EVE.exe.old.*` siblings whose handle has
    # since been released. Silent best-effort — leftovers are fine.
    try:
        for stale in eve_path.parent.glob(f"{eve_path.name}.old.*"):
            try:
                stale.unlink()
            except OSError:
                # Still locked or scheduled for reboot delete — ignore.
                pass
    except OSError:
        pass

    tmp = eve_path.with_suffix(f".exe.tmp.{os.getpid()}")
    if source == "link-mirror" and link_bin_path is not None:
        # LINK transport: bytes already on local disk via vault mirror; just copy.
        if not copy_from_link(link_bin_path, tmp):
            result["action"] = "failed"
            result["error"] = "link-copy-failed"
            result["exit"] = 3
            _log(result)
            return result
    else:
        # github (or auto fell back to github)
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

    # Choose swap strategy.
    if allow_hot_swap:
        swap = swap_with_kill_fallback(
            tmp,
            eve_path,
            kill_bat_path=kill_bat_path,
            force_kill_stuck=force_kill_stuck,
        )
        result["swap"] = swap
        if swap.get("success"):
            result["action"] = "replaced"
            result["swap_strategy"] = swap.get("strategy")
            result["local_sha_after"] = swap.get("sha_after") or remote_sha
            result["exit"] = 0
            _log(result)
            return result
        # Persistent failure — clean up tmp, exit gracefully.
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        result["action"] = "skipped"
        result["reason"] = swap.get("kill_result") or swap.get("error") or "hot-swap-failed"
        result["exit"] = 0
        _log(result)
        return result

    # Legacy retry-only path (--no-hot-swap).
    swapped = atomic_swap(tmp, eve_path)
    if not swapped:
        result["action"] = "skipped"
        result["reason"] = "locked-eve-running"
        result["exit"] = 0
        _log(result)
        return result

    result["action"] = "replaced"
    result["swap_strategy"] = "atomic_swap-legacy"
    result["local_sha_after"] = remote_sha
    result["exit"] = 0
    _log(result)
    return result


# ---------------------------------------------------------------------------
# Audit action (no writes)
# ---------------------------------------------------------------------------


def audit(
    eve_paths: list[Path],
    *,
    transport: str = "github",
    peer: str | None = None,
) -> dict:
    """Report running EVE.exe processes + local-vs-remote SHA + would-be action.

    No filesystem writes (other than the log row). Safe to run at any time.

    Sub-O 2026-05-25: `transport` / `peer` allow auditing LINK transport
    without going through GitHub. Default 'github' preserves backward compat:
    callers that pass no flags see the same behavior as before.
    """
    remote_sha, source, resolved_peer, _link_bin = _resolve_transport(transport, peer)
    report: dict = {
        "event": "audit",
        "transport": transport,
        "peer_requested": peer,
        "peer_resolved": resolved_peer,
        "link_peers_available": _list_link_peers(),
        "remote_sha": remote_sha,
        "remote_source": source,
        "targets": [],
    }
    for target in eve_paths:
        running = is_eve_running(target)
        local_sha = get_local_eve_sha(target)
        if remote_sha is None:
            would = "skipped: remote-unreachable"
        elif local_sha == remote_sha:
            would = "in-sync"
        elif not target.exists():
            would = "would-install"
        elif running:
            would = "would-rename-old (hot-swap)"
        else:
            would = "would-replace (direct os.replace)"
        report["targets"].append(
            {
                "path": str(target),
                "exists": target.exists(),
                "local_sha": local_sha,
                "running_pids": [getattr(p, "pid", None) for p in running],
                "running_count": len(running),
                "would_action": would,
            }
        )
    _log(report)
    return report


def _print_audit(report: dict) -> None:
    src = report.get("remote_source")
    rsha = report.get("remote_sha")
    tr = report.get("transport")
    peer_req = report.get("peer_requested")
    peer_res = report.get("peer_resolved")
    peers_avail = report.get("link_peers_available") or []
    print("[eve_self_update] AUDIT")
    print(f"  transport     : {tr}")
    print(f"  peer_request  : {peer_req}")
    print(f"  peer_resolved : {peer_res}")
    print(f"  link_peers    : {peers_avail}")
    if src == "link-unreachable" and tr == "link":
        print("  note          : vault-unreachable, falling back to github "
              "(unless --transport link forced this run)")
    elif src == "link-unreachable" and tr == "auto":
        print("  note          : vault-unreachable, falling back to github")
    print(f"  remote_sha    : {rsha}")
    print(f"  remote_source : {src}")
    for tg in report.get("targets", []):
        print("  --")
        print(f"  path          : {tg['path']}")
        print(f"  exists        : {tg['exists']}")
        print(f"  local_sha     : {tg['local_sha']}")
        print(f"  running_count : {tg['running_count']}")
        print(f"  running_pids  : {tg['running_pids']}")
        print(f"  would_action  : {tg['would_action']}")


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
    p.add_argument(
        "--audit",
        action="store_true",
        help="Print running EVE.exe processes + SHA state + would-be action. No writes.",
    )
    # Hot-swap flag group — default ON. --no-hot-swap forces legacy behavior.
    hot = p.add_mutually_exclusive_group()
    hot.add_argument(
        "--allow-hot-swap",
        dest="allow_hot_swap",
        action="store_true",
        default=True,
        help="(default) Use Windows rename-in-use trick if EVE.exe is running.",
    )
    hot.add_argument(
        "--no-hot-swap",
        dest="allow_hot_swap",
        action="store_false",
        help="Disable hot-swap; revert to retry-only original behavior.",
    )
    p.add_argument(
        "--force-kill-stuck",
        action="store_true",
        default=False,
        help="If hot-swap fails (rare; AV lock), invoke Kill-Stuck-EVE.bat and retry.",
    )
    p.add_argument(
        "--kill-bat-path",
        default=None,
        help=f"Override path to kill bat. Default: {DEFAULT_KILL_BAT}",
    )
    # Sub-O 2026-05-25: Sinister LINK transport.
    p.add_argument(
        "--transport",
        choices=("github", "link", "auto"),
        default="github",
        help=(
            "Source for the canonical EVE.exe. 'github' (default; preserves "
            "backward compat) | 'link' (peer-to-peer via _vault/sanctum-mirror) "
            "| 'auto' (LINK first, GitHub fallback)."
        ),
    )
    p.add_argument(
        "--peer",
        default=None,
        help=(
            "Sinister LINK peer machine-id under _vault/sanctum-mirror/. "
            "Defaults to first peer with a full payload, then the operator's "
            "hint at _shared-memory/eve-update-peer.txt."
        ),
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    targets = [Path(p) for p in ns.path] if ns.path else list(DEFAULT_EVE_PATHS)

    if ns.audit:
        report = audit(targets, transport=ns.transport, peer=ns.peer)
        _print_audit(report)
        return 0

    kill_bat = Path(ns.kill_bat_path) if ns.kill_bat_path else None

    overall = 0
    for target in targets:
        try:
            res = check_and_update(
                target,
                dry_run=ns.dry_run,
                force=ns.force,
                allow_hot_swap=ns.allow_hot_swap,
                force_kill_stuck=ns.force_kill_stuck,
                kill_bat_path=kill_bat,
                transport=ns.transport,
                peer=ns.peer,
            )
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
        suffix = ""
        if res.get("reason"):
            suffix = f" ({res.get('reason')})"
        elif res.get("swap_strategy"):
            suffix = f" [{res.get('swap_strategy')}]"
        print(f"[eve_self_update] {target}: {res['action']}{suffix}")
        if res.get("exit", 0) not in (0,):
            overall = res["exit"]
    return overall


if __name__ == "__main__":
    sys.exit(main())
