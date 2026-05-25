#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25 Sub-O
# eve_update_notifier.py -- Detect EVE.exe drift across Sinister LINK peers
# and fire a 3-layer popup (eve.py banner marker / Windows toast / stdout).
#
# Operator hard-canonical 2026-05-25 ~07:12Z (verbatim from CLAUDE.md +
# Sub-O brief): "make the eexe update oiver sinsiter link and leo will have
# popup to say update availabe or something".
#
# This daemon does NOT install updates -- it ONLY detects + notifies. Install
# is delegated to `automations/eve_self_update.py --transport link --peer <id>`
# (Sub-O extension), which the operator/Leo invokes after seeing the popup.
#
# Composes with doctrine:
#   _shared-memory/knowledge/eve-update-over-link-and-popup-doctrine-2026-05-25.md
#   _shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md
#   _shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md
#   _shared-memory/knowledge/leo-deploy-folder-bootstrap-doctrine-2026-05-25.md
#
# Layers (try in order; later layers ALWAYS run regardless of earlier success):
#   A. Marker file `_shared-memory/eve-update-available.json` -- consumed by
#      eve.py main_menu re-render (see deploy/EVE-UPDATE-OVER-LINK.md for the
#      integration TODO referencing tools/eve-picker/main_menu.py).
#   B. Windows toast (PowerShell COM bridge). Best-effort; silent fail when
#      blocked.
#   C. Stdout banner -- always prints when invoked with --scan/--once.
#
# CLI:
#   python automations/eve_update_notifier.py --scan --once
#   python automations/eve_update_notifier.py --watch
#   python automations/eve_update_notifier.py --clear
#   python automations/eve_update_notifier.py --install-schtask
#
# Idempotent. JSONL log at _shared-memory/eve-update-notifier-log.jsonl.

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_MIRROR_ROOT = REPO_ROOT / "_vault" / "sanctum-mirror"
LOCAL_EVE = REPO_ROOT / "EVE.exe"
LOCAL_EVE_SHA_SIDECAR = REPO_ROOT / "EVE.exe.sha256"
MARKER_PATH = REPO_ROOT / "_shared-memory" / "eve-update-available.json"
LOG_PATH = REPO_ROOT / "_shared-memory" / "eve-update-notifier-log.jsonl"

DEFAULT_POLL_SECONDS = 60
SCHTASK_NAME = "SinisterEveUpdateNotifier"

CHUNK = 1024 * 256


# ---------------------------------------------------------------------------
# Helpers
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
        print(f"[eve_update_notifier] log write failed: {exc}", file=sys.stderr)


def _hash_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(CHUNK), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _read_sha_sidecar(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        body = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not body:
        return None
    sha = body.split()[0]
    if len(sha) == 64 and all(c in "0123456789abcdefABCDEF" for c in sha):
        return sha.lower()
    return None


def _local_sha() -> str | None:
    """Prefer sidecar (cheap), fall back to hashing the binary."""
    sha = _read_sha_sidecar(LOCAL_EVE_SHA_SIDECAR)
    if sha:
        return sha
    return _hash_file(LOCAL_EVE)


def _list_peers() -> list[str]:
    """Peers visible under _vault/sanctum-mirror/, excluding self if marked."""
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


def _peer_sha(peer: str) -> str | None:
    return _read_sha_sidecar(VAULT_MIRROR_ROOT / peer / "EVE.exe.sha256")


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def detect_drift() -> dict:
    """Scan local vs every peer mirror; return a structured report.

    Drift = peer sha differs AND peer-bin exists AND local sha is known.
    Multiple peers may diverge; we surface the FIRST one we can install from.
    """
    local = _local_sha()
    peers = _list_peers()
    report: dict = {
        "event": "detect_drift",
        "local_sha": local,
        "peers_seen": peers,
        "drift": [],
        "install_candidate": None,
    }
    if not peers:
        report["reason"] = "no-peers"
        return report
    if not local:
        report["reason"] = "no-local-sha"
        return report

    for peer in peers:
        peer_dir = VAULT_MIRROR_ROOT / peer
        peer_sha = _peer_sha(peer)
        if not peer_sha:
            continue
        if peer_sha == local:
            continue
        bin_present = (peer_dir / "EVE.exe").exists()
        report["drift"].append(
            {
                "peer": peer,
                "peer_sha": peer_sha,
                "bin_present": bin_present,
            }
        )
        if bin_present and report["install_candidate"] is None:
            report["install_candidate"] = peer
    report["reason"] = "drift-found" if report["drift"] else "in-sync"
    return report


# ---------------------------------------------------------------------------
# Marker (Layer A)
# ---------------------------------------------------------------------------


def write_marker(report: dict) -> bool:
    """Persist the drift snapshot for eve.py menu to pick up on next render."""
    candidate = report.get("install_candidate")
    if not candidate:
        return False
    peer_sha = None
    for row in report.get("drift", []):
        if row.get("peer") == candidate:
            peer_sha = row.get("peer_sha")
            break
    payload = {
        "available_from_peer": candidate,
        "peer_sha": peer_sha,
        "local_sha": report.get("local_sha"),
        "detected_utc": _utc_now(),
        "install_cmd": (
            f"python automations/eve_self_update.py "
            f"--transport link --peer {candidate}"
        ),
    }
    try:
        MARKER_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Idempotent: skip rewrite if same payload (avoids spam).
        if MARKER_PATH.exists():
            try:
                existing = json.loads(MARKER_PATH.read_text(encoding="utf-8"))
                if (
                    existing.get("peer_sha") == payload["peer_sha"]
                    and existing.get("local_sha") == payload["local_sha"]
                    and existing.get("available_from_peer")
                    == payload["available_from_peer"]
                ):
                    return False
            except (OSError, json.JSONDecodeError):
                pass
        MARKER_PATH.write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return True
    except OSError as exc:
        _log({"event": "marker_write_failed", "error": repr(exc)})
        return False


def clear_marker() -> bool:
    if not MARKER_PATH.exists():
        return True
    try:
        MARKER_PATH.unlink()
        _log({"event": "marker_cleared"})
        return True
    except OSError as exc:
        _log({"event": "marker_clear_failed", "error": repr(exc)})
        return False


# ---------------------------------------------------------------------------
# Toast (Layer B)
# ---------------------------------------------------------------------------


def fire_toast(peer: str, peer_sha: str | None) -> str:
    """Fire a Windows toast via PowerShell COM bridge.

    Best-effort; silent fail when blocked (corporate policy, no shell, etc).
    """
    if os.name != "nt":
        return "skipped-non-windows"
    short = (peer_sha or "")[:8]
    title = "EVE Update Available"
    body = f"From peer {peer} (sha {short}). Open EVE.exe and press U to install."
    # Use the Windows Runtime ToastNotificationManager.
    ps = (
        "$ErrorActionPreference='SilentlyContinue';"
        "[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]|Out-Null;"
        "$tmpl=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
        "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        f"$nodes=$tmpl.GetElementsByTagName('text');"
        f"$nodes.Item(0).AppendChild($tmpl.CreateTextNode('{title}'))|Out-Null;"
        f"$nodes.Item(1).AppendChild($tmpl.CreateTextNode('{body}'))|Out-Null;"
        "$toast=[Windows.UI.Notifications.ToastNotification]::new($tmpl);"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('EVE').Show($toast)"
    )
    try:
        cp = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            timeout=10,
        )
        if cp.returncode == 0:
            return "ok"
        return f"rc={cp.returncode}"
    except Exception as exc:  # noqa: BLE001
        return f"err={exc!r}"


# ---------------------------------------------------------------------------
# Stdout banner (Layer C)
# ---------------------------------------------------------------------------


def print_stdout_banner(peer: str, peer_sha: str | None) -> None:
    short = (peer_sha or "")[:12]
    print(
        f"[EVE UPDATE AVAILABLE] from peer {peer} (sha {short}...); "
        f"run: python automations/eve_self_update.py --transport link --peer {peer}"
    )


# ---------------------------------------------------------------------------
# One-shot scan
# ---------------------------------------------------------------------------


def run_scan() -> int:
    report = detect_drift()
    candidate = report.get("install_candidate")
    if not candidate:
        _log({"event": "scan", **report})
        # No popup; nothing to do.
        return 0

    peer_sha = None
    for row in report.get("drift", []):
        if row.get("peer") == candidate:
            peer_sha = row.get("peer_sha")
            break

    wrote = write_marker(report)
    toast_status = fire_toast(candidate, peer_sha)
    print_stdout_banner(candidate, peer_sha)

    _log(
        {
            "event": "popup_fired",
            "peer": candidate,
            "peer_sha": peer_sha,
            "local_sha": report.get("local_sha"),
            "marker_written": wrote,
            "toast_status": toast_status,
        }
    )
    return 0


# ---------------------------------------------------------------------------
# Watch loop
# ---------------------------------------------------------------------------


def run_watch(interval: int = DEFAULT_POLL_SECONDS) -> int:
    print(f"[eve_update_notifier] watch every {interval}s (Ctrl+C to stop)")
    try:
        while True:
            try:
                run_scan()
            except Exception as exc:  # noqa: BLE001
                _log({"event": "scan_crashed", "error": repr(exc)})
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[eve_update_notifier] watch stopped")
        return 0


# ---------------------------------------------------------------------------
# schtask install
# ---------------------------------------------------------------------------


def install_schtask() -> int:
    """Register a 60s schtask that re-invokes --scan --once.

    Per doctrine, schtasks.exe is called inline; we do NOT create new .ps1/.bat.
    """
    if os.name != "nt":
        print("[eve_update_notifier] schtask install skipped: non-Windows")
        return 0

    py = sys.executable
    script = str(REPO_ROOT / "automations" / "eve_update_notifier.py")
    cmd_args = f'"{script}" --scan --once'
    # Use PT1M (60s) cadence; restart on failure handled by retry-on-mismatch.
    schtask_cmd = [
        "schtasks.exe",
        "/Create",
        "/F",
        "/SC", "MINUTE",
        "/MO", "1",
        "/TN", SCHTASK_NAME,
        "/TR", f'"{py}" {cmd_args}',
        "/RL", "LIMITED",
    ]
    try:
        cp = subprocess.run(schtask_cmd, capture_output=True, text=True, timeout=15)
        if cp.returncode == 0:
            print(f"[eve_update_notifier] schtask {SCHTASK_NAME} installed (1 min cadence)")
            _log({"event": "schtask_installed", "name": SCHTASK_NAME})
            return 0
        print(
            f"[eve_update_notifier] schtask install rc={cp.returncode}: "
            f"{cp.stderr.strip() or cp.stdout.strip()}",
            file=sys.stderr,
        )
        _log({"event": "schtask_install_failed", "rc": cp.returncode, "stderr": cp.stderr})
        return cp.returncode
    except Exception as exc:  # noqa: BLE001
        print(f"[eve_update_notifier] schtask install crashed: {exc!r}", file=sys.stderr)
        _log({"event": "schtask_install_crashed", "error": repr(exc)})
        return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detect EVE.exe drift across Sinister LINK peers + popup."
    )
    action = p.add_mutually_exclusive_group()
    action.add_argument("--scan", action="store_true", help="One-shot check + marker.")
    action.add_argument("--watch", action="store_true", help="Loop --scan every 60s.")
    action.add_argument("--clear", action="store_true", help="Delete marker file.")
    action.add_argument(
        "--install-schtask",
        action="store_true",
        help=f"Register {SCHTASK_NAME} scheduled task (1 min cadence).",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="With --scan, ensure single pass + exit 0 (test mode).",
    )
    p.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_POLL_SECONDS,
        help=f"Watch loop interval (seconds). Default {DEFAULT_POLL_SECONDS}.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    if ns.clear:
        ok = clear_marker()
        return 0 if ok else 1
    if ns.install_schtask:
        return install_schtask()
    if ns.watch:
        return run_watch(interval=max(5, ns.interval))
    # default: --scan (also covers --scan --once)
    return run_scan()


if __name__ == "__main__":
    sys.exit(main())
