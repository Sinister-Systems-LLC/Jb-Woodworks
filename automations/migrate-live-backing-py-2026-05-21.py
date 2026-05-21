#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-21
# LIVE-BACKING migration v3 — pure Python. os.unlink() on a junction removes the
# junction without touching the backing data. shutil.move() then moves the
# backing data into the now-empty Sanctum slot.
#
# Approach: for each of the 5 LIVE-BACKING dirs:
#   1. os.unlink(Sanctum junction)  — removes junction, leaves D:/Sinister side intact
#   2. shutil.move(D:/Sinister source, Sanctum dest)  — moves real data into Sanctum
#   3. archive the now-empty parent shell at D:/Sinister into _archive/

from __future__ import annotations
import os
import shutil
import sys
import time
from pathlib import Path

LOG = Path(r"D:\Sinister Sanctum\_shared-memory\migration-live-backing-v3-2026-05-21.log")
ARCHIVE_ROOT = Path(r"D:\Sinister Sanctum\_archive\d-sinister-01_projects-pointers-2026-05-21\Sinister")


def log(msg: str) -> None:
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"{stamp} {msg}"
    print(line)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def remove_junction(p: Path) -> bool:
    """Remove a junction WITHOUT traversing it."""
    if not p.exists() and not p.is_symlink():
        log(f"  junction already absent: {p}")
        return True
    try:
        # On Windows, junctions look like directories. os.rmdir works on
        # empty junctions; for non-empty (which junctions appear to be),
        # we need os.unlink — but Python's os.unlink fails on dirs.
        # The reliable path: os.rmdir works on junctions on Windows because
        # the junction itself is a "reparse point" that rmdir handles.
        os.rmdir(p)
        log(f"  removed junction: {p}")
        return True
    except OSError as e:
        log(f"  os.rmdir failed: {e}; trying _winapi.RemoveDirectoryW")
        try:
            # Fall back to direct Win32 RemoveDirectoryW (works on junctions).
            import ctypes
            ok = ctypes.windll.kernel32.RemoveDirectoryW(str(p))
            if ok:
                log(f"  Win32 RemoveDirectoryW succeeded: {p}")
                return True
            else:
                err = ctypes.windll.kernel32.GetLastError()
                log(f"  Win32 RemoveDirectoryW failed err={err}: {p}")
                return False
        except Exception as e2:
            log(f"  Win32 fallback raised: {e2}")
            return False


def move_dir(src: Path, dst: Path) -> bool:
    """Move src dir to dst. Both Path objects."""
    if not src.exists():
        log(f"  src missing: {src}")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dst))
        log(f"  moved: {src} -> {dst}")
        return True
    except Exception as e:
        log(f"  shutil.move failed: {e}")
        return False


def migrate(name: str, src_inner: Path, dest: Path, shell_parent: Path | None) -> bool:
    log(f"=== {name} ===")
    log(f"  src_inner = {src_inner}")
    log(f"  dest      = {dest}")

    # Step 1: remove the Sanctum junction at dest
    if dest.exists() or dest.is_symlink():
        if not remove_junction(dest):
            log(f"  ABORT {name} — junction removal failed")
            return False

    # Step 2: move the real data from src_inner into dest
    if not move_dir(src_inner, dest):
        log(f"  ABORT {name} — move failed")
        return False

    # Step 3: archive the now-empty parent shell (if applicable)
    if shell_parent and shell_parent.exists():
        # Verify shell_parent doesn't still contain the source dir we just moved.
        # (For Sinister-APK, src_inner == shell_parent itself, so this is moot.)
        # If it's a different parent (e.g. Sinister-Panel where src_inner was
        # /Sinister-Panel/source), the shell still has top-level scripts.
        if shell_parent != src_inner:
            arch = ARCHIVE_ROOT / name
            arch.parent.mkdir(parents=True, exist_ok=True)
            if not move_dir(shell_parent, arch):
                log(f"  WARN: shell archive failed for {name}; manual cleanup needed")
                # don't fail overall — the main data IS moved
    log(f"  {name} DONE")
    return True


def main() -> int:
    SINISTER = Path(r"D:\Sinister\01_Projects\Sinister")
    SANCTUM_PROJECTS = Path(r"D:\Sinister Sanctum\projects")

    log("=== LIVE-BACKING v3 (Python) START ===")

    ok_count = 0
    fail_count = 0

    targets = [
        # (name, src_inner, dest, shell_parent)
        # 1a: Sinister-APK — junction targets the dir ITSELF (no inner source/)
        ("Sinister-APK",
         SINISTER / "Sinister-APK",
         SANCTUM_PROJECTS / "sinister-kernel-apk" / "source",
         None),
        # 1b: Sinister-Emulator-Bundle — junction targets inner source/
        ("Sinister-Emulator-Bundle",
         SINISTER / "Sinister-Emulator-Bundle" / "source",
         SANCTUM_PROJECTS / "sinister-emulator-bundle" / "source",
         SINISTER / "Sinister-Emulator-Bundle"),
        # 1c: Sinister-Panel — junction targets inner source/
        ("Sinister-Panel",
         SINISTER / "Sinister-Panel" / "source",
         SANCTUM_PROJECTS / "sinister-panel" / "source",
         SINISTER / "Sinister-Panel"),
        # 1d: Sinister-Snap-EMU
        ("Sinister-Snap-EMU",
         SINISTER / "Sinister-Snap-EMU" / "source",
         SANCTUM_PROJECTS / "sinister-snap-emu" / "source",
         SINISTER / "Sinister-Snap-EMU"),
        # 1e: Sinister-TikTok-EMU
        ("Sinister-TikTok-EMU",
         SINISTER / "Sinister-TikTok-EMU" / "source",
         SANCTUM_PROJECTS / "sinister-tiktok-emu" / "source",
         SINISTER / "Sinister-TikTok-EMU"),
    ]

    for name, src, dest, shell in targets:
        if migrate(name, src, dest, shell):
            ok_count += 1
        else:
            fail_count += 1

    log(f"=== LIVE-BACKING v3 END — {ok_count} OK / {fail_count} FAIL ===")
    if SINISTER.exists():
        remaining = sorted(p.name for p in SINISTER.iterdir())
        log(f"Remaining at {SINISTER}: {remaining}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
