#!/usr/bin/env python3
"""sinister-config-watcher — inotify daemon for /etc/sinister/*.toml.

Author: RKOJ-ELENO :: 2026-05-24
Status: SCAFFOLDED. Parse-clean; not installed; not running on dev workstation.

For each modify/create event under /etc/sinister/, this daemon:
  1. Diffs the file against the last-known snapshot at /var/cache/sinister/last/.
  2. Calls classify-change.py with the diff to get a verdict {hot, target_unit, reason, severity}.
  3. If HOT: signals the target systemd unit (SIGHUP or try-restart depending on verdict).
  4. If COLD: invokes emit-reboot-banner.sh with the reason.
  5. Updates the last-known snapshot to the new state.

Dependencies: pyinotify (or python-inotify_simple). Falls back to polling if neither is available.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

WATCH_DIR = Path("/etc/sinister")
SNAPSHOT_DIR = Path("/var/cache/sinister/last")
CLASSIFIER = Path("/usr/local/bin/classify-change.py")
EMITTER = Path("/usr/local/bin/emit-reboot-banner.sh")

POLL_INTERVAL_S = 2.0


def diff_files(old: Path, new: Path) -> str:
    """Return unified diff of old vs new files. Empty string if identical."""
    if not old.exists():
        return new.read_text(errors="replace")
    if not new.exists():
        return ""
    try:
        out = subprocess.run(
            ["diff", "-u", str(old), str(new)],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: read both, return basic line-diff.
        a = old.read_text(errors="replace").splitlines()
        b = new.read_text(errors="replace").splitlines()
        return "\n".join(f"+{line}" for line in b if line not in a)


def classify(diff: str, filename: str) -> dict:
    """Call classify-change.py, return parsed JSON verdict. Defaults to reboot on parse failure."""
    try:
        out = subprocess.run(
            [sys.executable, str(CLASSIFIER), filename],
            input=diff, capture_output=True, text=True, timeout=10,
        )
        return json.loads(out.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"hot": False, "target_unit": None, "reason": f"classifier-failed: {exc}", "severity": "warn"}


def apply_hot(verdict: dict) -> None:
    """SIGHUP or try-restart the target systemd unit."""
    unit = verdict.get("target_unit")
    if not unit:
        return
    subprocess.run(["systemctl", "kill", "-s", "HUP", unit], check=False)


def emit_cold(filename: str, verdict: dict) -> None:
    """Invoke emit-reboot-banner.sh to record a reboot-required reason."""
    subprocess.run(
        [str(EMITTER), "add", filename, verdict.get("reason", "unknown")],
        check=False,
    )


def snapshot(file: Path) -> None:
    """Copy file to /var/cache/sinister/last/ preserving filename."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    target = SNAPSHOT_DIR / file.name
    shutil.copy2(file, target)


def handle_change(file: Path) -> None:
    """Process a single config-file change."""
    old = SNAPSHOT_DIR / file.name
    diff = diff_files(old, file)
    if not diff.strip():
        return
    verdict = classify(diff, file.name)
    if verdict.get("hot"):
        apply_hot(verdict)
    else:
        emit_cold(file.name, verdict)
    snapshot(file)


def poll_loop() -> None:
    """Polling fallback when inotify-bindings aren't available."""
    mtimes: dict[str, float] = {}
    while True:
        try:
            if WATCH_DIR.is_dir():
                for f in WATCH_DIR.glob("*.toml"):
                    mt = f.stat().st_mtime
                    if mtimes.get(f.name) != mt:
                        mtimes[f.name] = mt
                        handle_change(f)
        except Exception:
            pass
        time.sleep(POLL_INTERVAL_S)


def main() -> None:
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    try:
        import inotify_simple  # type: ignore
        i = inotify_simple.INotify()
        flags = inotify_simple.flags
        i.add_watch(str(WATCH_DIR), flags.MODIFY | flags.CREATE | flags.MOVED_TO)
        while True:
            for event in i.read():
                f = WATCH_DIR / event.name
                if f.suffix == ".toml":
                    handle_change(f)
    except ImportError:
        poll_loop()


if __name__ == "__main__":
    main()
