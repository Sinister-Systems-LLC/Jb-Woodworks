#!/usr/bin/env python3
"""vault_backup.py — Time-decay rotating snapshots of the Sinister vault.

Author: RKOJ-ELENO :: 2026-05-25

Composes with:
  - sinister-vault-architecture (vault is the canonical mirror substrate; backups are the DR copy)
  - version-snapshot-disaster-recovery-doctrine-2026-05-25 (snapshot-before-destructive pattern)
  - automate-everything-no-operator-admin-2026-05-25 (zero operator clicks)

Retention buckets (time-decay):
  hourly   -> keep last  7 days  (~168 snapshots cap with 1/hr cadence)
  daily    -> keep last 30 days  (one snapshot/day; oldest of the day wins)
  weekly   -> keep last 52 weeks (one snapshot/week; Monday wins)

Actions:
  --snapshot           create timestamped snapshot (robocopy /MIR on Windows; shutil fallback)
  --rotate             apply retention policy; delete out-of-bucket snapshots
  --restore <id>       PRINT restore plan (operator confirms; never executes)
  --list               print backup inventory (id + size + age)
  --install-schtask    register SinisterVaultBackup schtask (60-min cadence)
  --compress           write .zip (ZIP_DEFLATED) instead of dir snapshot
  --target <path>      override default backup root
  --dry-run            print plan without mutating
  --cloud              (deferred) future S3/R2/Backblaze hook; logs intent only
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = REPO_ROOT / "_vault"
DEFAULT_TARGET = REPO_ROOT / "_vault-backups"
LOG_PATH = REPO_ROOT / "_shared-memory" / "vault-backup-log.jsonl"
SCHTASK_NAME = "SinisterVaultBackup"

SNAPSHOT_RE = re.compile(r"^vault-(\d{8}T\d{6}Z)(?:\.zip)?$")


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_id() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _log(event: str, **fields) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": _now_iso(), "event": event, **fields}
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _parse_snapshot(name: str) -> _dt.datetime | None:
    m = SNAPSHOT_RE.match(name)
    if not m:
        return None
    try:
        return _dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=_dt.timezone.utc)
    except ValueError:
        return None


def _list_snapshots(target: Path) -> List[Tuple[str, _dt.datetime, int]]:
    """Return list of (name, timestamp, size_bytes), newest first."""
    if not target.exists():
        return []
    out: List[Tuple[str, _dt.datetime, int]] = []
    for entry in target.iterdir():
        ts = _parse_snapshot(entry.name)
        if not ts:
            continue
        try:
            if entry.is_file():
                size = entry.stat().st_size
            else:
                size = sum(p.stat().st_size for p in entry.rglob("*") if p.is_file())
        except OSError:
            size = 0
        out.append((entry.name, ts, size))
    out.sort(key=lambda r: r[1], reverse=True)
    return out


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def _snapshot(target: Path, compress: bool, dry_run: bool) -> int:
    if not VAULT_ROOT.exists():
        print(f"[snapshot] vault root missing at {VAULT_ROOT} — nothing to snapshot")
        _log("snapshot.skip", reason="vault root missing")
        return 0
    snap_id = _now_id()
    if compress:
        out_path = target / f"vault-{snap_id}.zip"
    else:
        out_path = target / f"vault-{snap_id}"
    print(f"[snapshot] plan: {VAULT_ROOT} -> {out_path}")
    if dry_run:
        _log("snapshot.dryrun", out=str(out_path))
        return 0
    target.mkdir(parents=True, exist_ok=True)
    if compress:
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for p in VAULT_ROOT.rglob("*"):
                if not p.is_file():
                    continue
                try:
                    zf.write(p, p.relative_to(VAULT_ROOT.parent))
                except (OSError, ValueError):
                    continue
        size = out_path.stat().st_size
    else:
        used_robocopy = False
        if sys.platform == "win32" and shutil.which("robocopy"):
            res = subprocess.run(
                ["robocopy", str(VAULT_ROOT), str(out_path), "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:1", "/W:1"],
                capture_output=True, text=True,
            )
            # robocopy exit codes: 0-7 = success/info; 8+ = failure
            if res.returncode < 8:
                used_robocopy = True
        if not used_robocopy:
            shutil.copytree(VAULT_ROOT, out_path, dirs_exist_ok=True)
        size = sum(p.stat().st_size for p in out_path.rglob("*") if p.is_file())
    _log("snapshot.done", id=snap_id, path=str(out_path), bytes=size, compressed=compress)
    print(f"[snapshot] done id={snap_id} size={_human_size(size)}")
    return 0


def _rotate(target: Path, dry_run: bool) -> int:
    """Apply tri-tier retention. Latest-per-bucket wins; everything else deleted."""
    snaps = _list_snapshots(target)
    if not snaps:
        print("[rotate] no snapshots present")
        return 0
    now = _dt.datetime.now(_dt.timezone.utc)
    keep: set[str] = set()
    seen_day: dict[str, str] = {}    # YYYY-MM-DD -> snap name
    seen_week: dict[str, str] = {}   # YYYY-Www  -> snap name

    for name, ts, _ in snaps:
        age = now - ts
        # hourly bucket: keep all within 7 days
        if age <= _dt.timedelta(days=7):
            keep.add(name)
        # daily bucket: keep newest-per-day within 30 days
        if age <= _dt.timedelta(days=30):
            day_key = ts.strftime("%Y-%m-%d")
            if day_key not in seen_day:
                seen_day[day_key] = name
                keep.add(name)
        # weekly bucket: keep newest-per-iso-week within 52 weeks
        if age <= _dt.timedelta(weeks=52):
            iso_year, iso_week, _ = ts.isocalendar()
            wk_key = f"{iso_year}-W{iso_week:02d}"
            if wk_key not in seen_week:
                seen_week[wk_key] = name
                keep.add(name)

    deletions = [n for n, _, _ in snaps if n not in keep]
    print(f"[rotate] keep={len(keep)} delete={len(deletions)}")
    for d in deletions[:20]:
        print(f"  -{d}")
    if dry_run:
        _log("rotate.dryrun", keep=len(keep), delete=len(deletions))
        return 0
    for d in deletions:
        p = target / d
        try:
            if p.is_file():
                p.unlink()
            else:
                shutil.rmtree(p, ignore_errors=True)
        except OSError as e:
            _log("rotate.delete_fail", name=d, err=str(e))
    _log("rotate.done", keep=len(keep), deleted=len(deletions))
    return 0


def _list(target: Path) -> int:
    snaps = _list_snapshots(target)
    if not snaps:
        print(f"[list] no snapshots at {target}")
        return 0
    now = _dt.datetime.now(_dt.timezone.utc)
    print(f"[list] {len(snaps)} snapshots at {target}")
    for name, ts, size in snaps:
        age = now - ts
        age_str = f"{age.days}d" if age.days else f"{age.seconds // 3600}h"
        print(f"  {name:40s} {_human_size(size):>10s}  age={age_str}")
    return 0


def _restore_plan(target: Path, snap_id: str) -> int:
    snaps = _list_snapshots(target)
    match = next((n for n, _, _ in snaps if snap_id in n), None)
    if not match:
        print(f"[restore] no snapshot matching '{snap_id}' under {target}")
        return 2
    src = target / match
    print("[restore] PLAN (operator must confirm + execute manually):")
    print(f"  source:      {src}")
    print(f"  destination: {VAULT_ROOT}")
    print("  steps:")
    print("    1. shutdown vault daemon")
    print(f"    2. mv '{VAULT_ROOT}' '{VAULT_ROOT}-prerestore-{_now_id()}'")
    if match.endswith(".zip"):
        print(f"    3. unzip '{src}' -> '{VAULT_ROOT.parent}'")
    else:
        print(f"    3. robocopy '{src}' '{VAULT_ROOT}' /MIR")
    print("    4. restart vault daemon; verify checksums via vault_github_sync.py --scan")
    _log("restore.planned", id=match)
    return 0


def _install_schtask() -> int:
    script_path = Path(__file__).resolve()
    import shutil as _sh
    _pw = _sh.which("pythonw") or str(Path(sys.executable).parent / "pythonw.exe")
    _py = _pw if Path(_pw).exists() else "python"
    cmd_str = f'"{_py}" "{script_path}" --snapshot --rotate'
    args = [
        "schtasks.exe", "/Create", "/F",
        "/SC", "MINUTE", "/MO", "60",
        "/TN", SCHTASK_NAME,
        "/TR", cmd_str,
        "/RL", "LIMITED",
    ]
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[schtask] FAIL: {res.stderr.strip()}", file=sys.stderr)
        _log("schtask.fail", stderr=res.stderr[:500])
        return res.returncode
    print(f"[schtask] registered {SCHTASK_NAME} (60-min cadence)")
    _log("schtask.installed", name=SCHTASK_NAME)
    return 0


def _cloud_stub(target: Path) -> int:
    """Deferred hook: future cloud upload (S3 / R2 / Backblaze).
    For now we just record intent so the schtask schema is forward-compatible.
    Implementation outline:
      - read env: SINISTER_CLOUD_PROVIDER, SINISTER_CLOUD_BUCKET, SINISTER_CLOUD_KEY
      - boto3 / s3cmd / rclone upload of newest snapshot only
      - prune cloud snapshots same retention as local
    """
    print("[cloud] deferred — no cloud provider configured; logging intent only")
    _log("cloud.stub", target=str(target))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Vault rotating snapshot backups")
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--rotate", action="store_true")
    ap.add_argument("--restore", metavar="SNAP_ID")
    ap.add_argument("--list", action="store_true", dest="do_list")
    ap.add_argument("--install-schtask", action="store_true")
    ap.add_argument("--compress", action="store_true")
    ap.add_argument("--target", default=str(DEFAULT_TARGET))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cloud", action="store_true")
    args = ap.parse_args()

    target = Path(args.target)

    if args.install_schtask:
        return _install_schtask()

    rc = 0
    did_anything = False
    if args.do_list:
        rc |= _list(target)
        did_anything = True
    if args.snapshot:
        rc |= _snapshot(target, args.compress, args.dry_run)
        did_anything = True
    if args.rotate:
        rc |= _rotate(target, args.dry_run)
        did_anything = True
    if args.restore:
        rc |= _restore_plan(target, args.restore)
        did_anything = True
    if args.cloud:
        rc |= _cloud_stub(target)
        did_anything = True

    if not did_anything:
        ap.print_help()
        return 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
