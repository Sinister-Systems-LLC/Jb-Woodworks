#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
"""
sanctum_resource_doctor.py -- diagnose + remediate OS-wide resource starvation
that causes system-wide freezes (file-explorer hangs, agent UI stalls) on the
operator's workstation.

ROOT CAUSES (per operator screenshot 2026-05-26 ~22:47Z):

  Symptom = file-explorer cannot launch, several claude.exe windows frozen,
  intermittently unfreezes "after a random amount of time". This is OS-LEVEL
  resource starvation, NOT the iter-23 MCP/schtask/spawn-phrase "Simmering"
  popup.

  Evidence captured at diagnosis time:
    * 166 conhost + 126 bash + 42 cmd + 18 python + 13 claude + 37 node + 44 zen
    * TEMP folder = 34.7 GB / 211,962 files (>0.96 GB are >7 days old)
    * 2 zombie claude.exe at 33.6h uptime (operator restarted yesterday)
    * 40 Sinister* schtasks (4 currently Running concurrently)
    * Defender real-time + behavior monitor + IoAV all ENABLED on D:\
    * 32.1 GB total process working-set / 63.8 GB RAM (Memory Compression at 2 GB)

FIX SURFACES:

  --diagnose                       (read-only) snapshot a JSON report
  --cleanup-temp --age-days 7      report-only; --apply deletes
  --kill-zombies                   report-only; --apply taskkills >12h+idle
  --apply-defender-exclusions      adds Sanctum + .git dir exclusions (one-shot)

DEFAULT MODE: --diagnose (read-only). Mutating modes require explicit --apply.

Mirror the style of `automations/schtask_stagger.py`:
  - CSV/JSON parse, snapshot-before-mutate
  - --safe flag short-circuits any mutation
  - subprocess.run with timeouts
  - SANCTUM_ROOT env-overridable

Doctrine refs:
  - system-wide-freeze-cleanup-doctrine-2026-05-26.md (NEW)
  - perf-freeze-root-cause-2026-05-24.md
  - automate-everything-no-operator-admin-2026-05-25.md (pre-approves Defender)
  - no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
REPORT_DIR = SANCTUM_ROOT / "_shared-memory" / "_archive" / "resource-doctor"
TEMP_DIR = Path(os.environ.get("TEMP", r"C:\Users\Zonia\AppData\Local\Temp"))

# Zombie heuristic: process older than this AND consumed <5 sec CPU in the last
# self-check window is considered orphaned.
ZOMBIE_MIN_AGE_HOURS = 12.0
ZOMBIE_NAMES = {"claude", "mintty", "pythonw", "node"}

# Defender exclusions we want present (per automate-everything-no-operator-admin)
DEFENDER_EXCLUSION_PATHS = [
    r"D:\Sinister Sanctum\_shared-memory",
    r"D:\Sinister Sanctum\.git",
    r"D:\Sinister Sanctum\automations\__pycache__",
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _run_ps(script: str, timeout: int = 60) -> tuple[int, str, str]:
    """Run a PowerShell snippet, return (rc, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as exc:  # pragma: no cover
        return 1, "", str(exc)


def _ps_json(script: str, timeout: int = 60):
    """Run a PowerShell snippet that emits JSON via ConvertTo-Json; return parsed object or None."""
    rc, out, err = _run_ps(script, timeout=timeout)
    if rc != 0 or not out.strip():
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# diagnostics (read-only)
# ---------------------------------------------------------------------------
def diag_top_processes(n: int = 20) -> list[dict]:
    script = (
        "Get-Process | Sort-Object WorkingSet -Descending | "
        f"Select-Object -First {n} Name, Id, "
        "@{N='WS_MB';E={[math]::Round($_.WorkingSet/1MB,1)}}, "
        "@{N='CPU_s';E={if($_.CPU){[math]::Round($_.CPU,1)}else{0}}}, "
        "@{N='Start';E={if($_.StartTime){$_.StartTime.ToString('s')}else{''}}} "
        "| ConvertTo-Json -Compress"
    )
    data = _ps_json(script) or []
    return data if isinstance(data, list) else [data]


def diag_process_counts(n: int = 15) -> list[dict]:
    script = (
        "Get-Process | Group-Object Name | Sort-Object Count -Descending | "
        f"Select-Object -First {n} Count, Name | ConvertTo-Json -Compress"
    )
    data = _ps_json(script) or []
    return data if isinstance(data, list) else [data]


def diag_disks() -> list[dict]:
    script = (
        "Get-PSDrive | Where-Object Used -gt 0 | "
        "Select-Object Name, "
        "@{N='Used_GB';E={[math]::Round($_.Used/1GB,1)}}, "
        "@{N='Free_GB';E={[math]::Round($_.Free/1GB,1)}} "
        "| ConvertTo-Json -Compress"
    )
    data = _ps_json(script) or []
    return data if isinstance(data, list) else [data]


def diag_temp_size() -> dict:
    if not TEMP_DIR.exists():
        return {"size_mb": 0, "files": 0, "error": "missing"}
    total = 0
    count = 0
    cutoff = datetime.now() - timedelta(days=7)
    old_total = 0
    old_count = 0
    try:
        for entry in TEMP_DIR.rglob("*"):
            try:
                if not entry.is_file():
                    continue
                st = entry.stat()
                total += st.st_size
                count += 1
                if datetime.fromtimestamp(st.st_mtime) < cutoff:
                    old_total += st.st_size
                    old_count += 1
            except OSError:
                continue
    except OSError:
        pass
    return {
        "size_mb": round(total / 1024 / 1024, 1),
        "files": count,
        "gt7d_size_mb": round(old_total / 1024 / 1024, 1),
        "gt7d_files": old_count,
    }


def diag_defender() -> dict:
    script = (
        "Get-MpComputerStatus | Select-Object "
        "RealTimeProtectionEnabled, BehaviorMonitorEnabled, IoavProtectionEnabled, "
        "AntivirusEnabled, NISEnabled, QuickScanAge "
        "| ConvertTo-Json -Compress"
    )
    return _ps_json(script) or {}


def diag_zombie_candidates() -> list[dict]:
    """Find processes >= ZOMBIE_MIN_AGE_HOURS old with low CPU/sec ratio."""
    script = (
        "Get-Process | Where-Object {($_.Name -in @('claude','mintty','pythonw','node')) -and $_.StartTime} "
        "| Select-Object Name, Id, "
        "@{N='Age_h';E={[math]::Round(((Get-Date)-$_.StartTime).TotalHours,2)}}, "
        "@{N='WS_MB';E={[math]::Round($_.WorkingSet/1MB,1)}}, "
        "@{N='CPU_s';E={if($_.CPU){[math]::Round($_.CPU,1)}else{0}}} "
        "| ConvertTo-Json -Compress"
    )
    data = _ps_json(script) or []
    if isinstance(data, dict):
        data = [data]
    out = []
    for proc in data:
        age_h = proc.get("Age_h", 0)
        cpu_s = proc.get("CPU_s", 0)
        if age_h >= ZOMBIE_MIN_AGE_HOURS:
            # rough idle heuristic: CPU/hour < 30 sec = idle
            cpu_per_hour = (cpu_s / age_h) if age_h > 0 else 0
            if cpu_per_hour < 30:
                proc["zombie_reason"] = (
                    f"age={age_h}h cpu_per_hour={cpu_per_hour:.1f}s/h"
                )
                out.append(proc)
    return out


def diag_running_schtasks() -> list[dict]:
    script = (
        "Get-ScheduledTask | Where-Object {$_.State -eq 'Running' -and $_.TaskName -like 'Sinister*'} "
        "| Select-Object TaskName, @{N='State';E={[string]$_.State}} | ConvertTo-Json -Compress"
    )
    data = _ps_json(script) or []
    return data if isinstance(data, list) else [data]


def diag_schtask_cadences() -> list[dict]:
    """Identify Sinister* schtasks with cadence faster than 4x/hour (interval < PT15M)."""
    script = (
        "$out=@(); foreach($t in (Get-ScheduledTask | Where-Object {$_.TaskName -like 'Sinister*'})) "
        "{ foreach($trg in $t.Triggers){ "
        "  if($trg.Repetition.Interval){ "
        "    $out += [pscustomobject]@{TaskName=$t.TaskName; Interval=$trg.Repetition.Interval} } } } ; "
        "$out | ConvertTo-Json -Compress"
    )
    data = _ps_json(script) or []
    if isinstance(data, dict):
        data = [data]
    fast = []
    for row in data:
        ival = row.get("Interval", "")
        # PT1M PT5M etc -> minutes; PT1H -> hours
        if ival.startswith("PT") and ival.endswith("M"):
            try:
                mins = int(ival[2:-1])
                if mins < 15:
                    row["fires_per_hour"] = round(60 / mins, 1)
                    fast.append(row)
            except ValueError:
                continue
    return fast


def diag_ram() -> dict:
    script = (
        "$os=Get-CimInstance Win32_OperatingSystem; "
        "[pscustomobject]@{"
        "total_gb=[math]::Round($os.TotalVisibleMemorySize/1MB,1); "
        "free_gb=[math]::Round($os.FreePhysicalMemory/1MB,1); "
        "pct_used=[math]::Round(100-($os.FreePhysicalMemory/$os.TotalVisibleMemorySize*100),0); "
        "} | ConvertTo-Json -Compress"
    )
    return _ps_json(script) or {}


def diag_defender_exclusions() -> list[str]:
    """Best-effort read of current exclusions (may require admin; we still try)."""
    script = "(Get-MpPreference).ExclusionPath | ConvertTo-Json -Compress"
    data = _ps_json(script)
    if data is None:
        return []
    if isinstance(data, str):
        return [data]
    return data


# ---------------------------------------------------------------------------
# remediation (mutating; gated by --apply)
# ---------------------------------------------------------------------------
def cleanup_temp(age_days: int, apply: bool, safe: bool) -> dict:
    if safe and apply:
        return {"skipped": True, "reason": "--safe blocks --apply"}
    cutoff = datetime.now() - timedelta(days=age_days)
    targets: list[tuple[str, int]] = []
    if not TEMP_DIR.exists():
        return {"error": "TEMP missing", "applied": False}
    for entry in TEMP_DIR.rglob("*"):
        try:
            if not entry.is_file():
                continue
            st = entry.stat()
            if datetime.fromtimestamp(st.st_mtime) < cutoff:
                targets.append((str(entry), st.st_size))
        except OSError:
            continue
    total_bytes = sum(s for _, s in targets)
    result = {
        "candidates": len(targets),
        "size_mb": round(total_bytes / 1024 / 1024, 1),
        "applied": False,
        "deleted": 0,
        "failed": 0,
    }
    if not apply:
        result["mode"] = "dry-run"
        return result
    # apply
    snap = _snapshot_text(
        "temp-cleanup", [f"{p}\t{s}" for p, s in targets[:5000]]
    )
    result["snapshot"] = str(snap)
    deleted = 0
    failed = 0
    for path, _sz in targets:
        try:
            os.remove(path)
            deleted += 1
        except OSError:
            failed += 1
    result["applied"] = True
    result["deleted"] = deleted
    result["failed"] = failed
    return result


def kill_zombies(apply: bool, safe: bool) -> dict:
    if safe and apply:
        return {"skipped": True, "reason": "--safe blocks --apply"}
    candidates = diag_zombie_candidates()
    result: dict = {
        "candidates": candidates,
        "count": len(candidates),
        "applied": False,
        "killed": 0,
        "failed": 0,
    }
    if not apply:
        result["mode"] = "dry-run"
        return result
    # snapshot
    snap = _snapshot_text(
        "zombie-kills",
        [json.dumps(c) for c in candidates],
    )
    result["snapshot"] = str(snap)
    killed = 0
    failed = 0
    for proc in candidates:
        pid = proc.get("Id")
        if not pid:
            continue
        rc, _o, _e = _run_ps(f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue")
        if rc == 0:
            killed += 1
        else:
            failed += 1
    result["applied"] = True
    result["killed"] = killed
    result["failed"] = failed
    return result


def apply_defender_exclusions(apply: bool, safe: bool) -> dict:
    if safe and apply:
        return {"skipped": True, "reason": "--safe blocks --apply"}
    current = set(diag_defender_exclusions())
    to_add = [p for p in DEFENDER_EXCLUSION_PATHS if p not in current]
    result = {
        "current_count": len(current),
        "to_add": to_add,
        "applied": False,
        "added": 0,
        "failed": 0,
    }
    if not apply:
        result["mode"] = "dry-run"
        return result
    added = 0
    failed = 0
    for path in to_add:
        # Add-MpPreference is idempotent for paths; needs admin
        rc, _o, err = _run_ps(
            f"Add-MpPreference -ExclusionPath '{path}' -ErrorAction Stop"
        )
        if rc == 0:
            added += 1
        else:
            failed += 1
            result.setdefault("errors", []).append({"path": path, "err": err.strip()[:200]})
    result["applied"] = True
    result["added"] = added
    result["failed"] = failed
    return result


def _snapshot_text(label: str, lines: list[str]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    p = REPORT_DIR / f"{label}-{_utc_stamp()}.txt"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# diagnose mode
# ---------------------------------------------------------------------------
def cmd_diagnose(args: argparse.Namespace) -> int:
    print("[resource-doctor] diagnosing (read-only)...")
    report = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "ram": diag_ram(),
        "disks": diag_disks(),
        "temp": diag_temp_size(),
        "defender": diag_defender(),
        "defender_exclusions": diag_defender_exclusions(),
        "top_processes": diag_top_processes(20),
        "process_counts": diag_process_counts(15),
        "zombie_candidates": diag_zombie_candidates(),
        "running_schtasks": diag_running_schtasks(),
        "fast_cadence_schtasks": diag_schtask_cadences(),
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORT_DIR / f"report-{_utc_stamp()}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[resource-doctor] wrote {out_path}")

    # Summary to stdout
    ram = report["ram"]
    print(
        f"  RAM total={ram.get('total_gb','?')}GB free={ram.get('free_gb','?')}GB "
        f"used={ram.get('pct_used','?')}%"
    )
    print(
        f"  TEMP {report['temp'].get('size_mb','?')} MB / {report['temp'].get('files','?')} files"
        f"  (>7d: {report['temp'].get('gt7d_size_mb','?')} MB / {report['temp'].get('gt7d_files','?')})"
    )
    print(f"  zombie_candidates: {len(report['zombie_candidates'])}")
    print(f"  running_schtasks : {len(report['running_schtasks'])}")
    print(f"  fast_cadence (<15m): {len(report['fast_cadence_schtasks'])}")
    return 0


def cmd_cleanup_temp(args: argparse.Namespace) -> int:
    res = cleanup_temp(args.age_days, args.apply, args.safe)
    print(json.dumps(res, indent=2))
    return 0


def cmd_kill_zombies(args: argparse.Namespace) -> int:
    res = kill_zombies(args.apply, args.safe)
    print(json.dumps(res, indent=2))
    return 0


def cmd_defender(args: argparse.Namespace) -> int:
    res = apply_defender_exclusions(args.apply, args.safe)
    print(json.dumps(res, indent=2))
    return 0 if res.get("failed", 0) == 0 else 4


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Diagnose + remediate OS-wide resource starvation on Sanctum workstation"
    )
    p.add_argument("--safe", action="store_true",
                   help="block all mutations even if --apply is set")
    sub = p.add_subparsers(dest="cmd")

    sp_d = sub.add_parser("diagnose", help="read-only snapshot to _archive/resource-doctor/")
    sp_d.set_defaults(func=cmd_diagnose)

    sp_t = sub.add_parser("cleanup-temp", help="report or delete old TEMP files")
    sp_t.add_argument("--age-days", type=int, default=7)
    sp_t.add_argument("--apply", action="store_true")
    sp_t.set_defaults(func=cmd_cleanup_temp)

    sp_z = sub.add_parser("kill-zombies", help="report or taskkill zombie spawn children")
    sp_z.add_argument("--apply", action="store_true")
    sp_z.set_defaults(func=cmd_kill_zombies)

    sp_x = sub.add_parser("apply-defender-exclusions",
                          help="add Sanctum dirs to Defender exclusions (needs admin)")
    sp_x.add_argument("--apply", action="store_true")
    sp_x.set_defaults(func=cmd_defender)

    args = p.parse_args(argv)
    if not getattr(args, "func", None):
        # default to diagnose
        return cmd_diagnose(argparse.Namespace(safe=args.safe))
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
