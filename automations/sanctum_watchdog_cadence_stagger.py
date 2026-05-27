#!/usr/bin/env python3
"""sanctum_watchdog_cadence_stagger.py -- F4 wave 3 fix.

Author: RKOJ-ELENO :: 2026-05-27

Per fleet-master-complete-everything-2026-05-27 plan Wave 3 F4:
  Stagger watchdog cadences to 5/6/7/8/9/10 min boundaries
  (6 watchdog tasks disjoint)

Current state (probed 2026-05-27T05:08Z):
  SinisterEVEWatchdog            PT1M
  SinisterEveGpuTrainerWatchdog  PT1M
  SinisterAccountWatchdog        PT5M
  SinisterAPKWatchdog            PT5M
  SinisterEveCrashWatchdog       PT5M
  SinisterLoopRelentlessWatchdog PT5M

Target staggered cadences (longer-running watchdogs get longer intervals so
they don't pile up on the same minute):

  SinisterEVEWatchdog            PT5M   (crash-detect critical -- fastest)
  SinisterAccountWatchdog        PT6M
  SinisterEveCrashWatchdog       PT7M
  SinisterAPKWatchdog            PT8M
  SinisterLoopRelentlessWatchdog PT9M
  SinisterEveGpuTrainerWatchdog  PT10M  (heavy GPU probe -- slowest)

Composes:
  - watchdog-cadence-stagger pattern (this script is the canonical fix)
  - automate-everything-no-operator-admin-2026-05-25
  - no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25 (Python over ps1)

Smoke (any iter):
  python automations/sanctum_watchdog_cadence_stagger.py --dry-run
  python automations/sanctum_watchdog_cadence_stagger.py --apply
  python automations/sanctum_watchdog_cadence_stagger.py --verify
"""
from __future__ import annotations
import argparse
import subprocess
import sys

TARGETS = {
    "SinisterEVEWatchdog":            "PT5M",
    "SinisterAccountWatchdog":        "PT6M",
    "SinisterEveCrashWatchdog":       "PT7M",
    "SinisterAPKWatchdog":            "PT8M",
    "SinisterLoopRelentlessWatchdog": "PT9M",
    "SinisterEveGpuTrainerWatchdog":  "PT10M",
}

# CIM Interval-string mapping for PowerShell New-TimeSpan compatibility.
INTERVAL_TS = {
    "PT5M":  "(New-TimeSpan -Minutes 5)",
    "PT6M":  "(New-TimeSpan -Minutes 6)",
    "PT7M":  "(New-TimeSpan -Minutes 7)",
    "PT8M":  "(New-TimeSpan -Minutes 8)",
    "PT9M":  "(New-TimeSpan -Minutes 9)",
    "PT10M": "(New-TimeSpan -Minutes 10)",
}


def set_interval(task_name: str, iso8601: str, dry: bool) -> int:
    """Use PowerShell Set-ScheduledTask + Set-ScheduledTaskTrigger pattern:
    grab the existing trigger, clone with the new RepetitionInterval, push.
    """
    if dry:
        print(f"  [dry-run] would set {task_name} -> Repetition.Interval = {iso8601}")
        return 0
    ts_expr = INTERVAL_TS.get(iso8601)
    if not ts_expr:
        print(f"  [FAIL] {task_name}: no TimeSpan mapping for {iso8601}")
        return 2
    # Build a fresh trigger: once + repetition with new interval, keep original
    # start time. NEW trigger ensures fully-formed Repetition.Interval (some
    # legacy triggers were created with empty Duration which Set-ScheduledTask
    # rejects when you only mutate Interval).
    ps = (
        f"$t = Get-ScheduledTask -TaskName '{task_name}' -ErrorAction Stop; "
        f"$existing = $t.Triggers[0]; "
        f"$start = if ($existing.StartBoundary) {{ [datetime]$existing.StartBoundary }} else {{ Get-Date }}; "
        f"$trig = New-ScheduledTaskTrigger -Once -At $start "
        f"-RepetitionInterval {ts_expr}; "
        f"Set-ScheduledTask -TaskName '{task_name}' -Trigger $trig -ErrorAction Stop | Out-Null; "
        f"'OK'"
    )
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        capture_output=True, text=True,
    )
    if proc.returncode == 0 and "OK" in proc.stdout:
        print(f"  [OK]   {task_name} -> {iso8601}")
        return 0
    print(f"  [FAIL] {task_name}: rc={proc.returncode}")
    if proc.stderr.strip():
        print(f"         stderr: {proc.stderr.strip()[:200]}")
    return proc.returncode


def verify() -> int:
    """Probe each task's current interval; return 0 if all match targets."""
    ps = (
        "Get-ScheduledTask | Where-Object { $_.TaskName -in @('"
        + "','".join(TARGETS.keys())
        + "') } | ForEach-Object { "
        "  $iv = $_.Triggers[0].Repetition.Interval; "
        "  '{0}={1}' -f $_.TaskName, $iv "
        "}"
    )
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        capture_output=True, text=True,
    )
    actual = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            actual[k] = v
    mismatched = []
    print(f"\n--- Verify (F4 acceptance) ---")
    for name, want in TARGETS.items():
        got = actual.get(name, "MISSING")
        ok = (got == want)
        print(f"  {'OK ' if ok else 'BAD'} {name}: got={got} want={want}")
        if not ok:
            mismatched.append(name)
    # F4 acceptance: 6 watchdog tasks on disjoint cadences
    intervals = [actual.get(n) for n in TARGETS if actual.get(n)]
    disjoint_ok = len(intervals) == len(set(intervals))
    print(f"  Disjoint cadences: {'YES' if disjoint_ok else 'NO'} (intervals={intervals})")
    return 0 if (not mismatched and disjoint_ok) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.verify:
        return verify()

    dry = args.dry_run
    print(f"--- {'DRY-RUN' if dry else 'APPLY'} :: stagger {len(TARGETS)} watchdog cadences ---\n")
    fails = 0
    for name, iso in TARGETS.items():
        print(f"\n[{name}]")
        rc = set_interval(name, iso, dry)
        if rc != 0:
            fails += 1
    print(f"\n--- Summary: {len(TARGETS) - fails} OK, {fails} FAIL ---")
    if not dry:
        return verify()
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
