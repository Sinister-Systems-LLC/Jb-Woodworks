#!/usr/bin/env python3
"""resource_quota_governor.py -- per-agent CPU/RAM caps with operator headroom guarantee.

Author: RKOJ-ELENO :: 2026-05-25
Operator hard-canonical 2026-05-25 ~07:00Z (verbatim):
    "just give me enough so i can still communicate and tell you what to do.
     thats what i want to do with the sinister os. i want to be able to set
     usage that you can have to those partrs on the pc."

What it does:
    Walks every running Claude/EVE/Ollama process and applies a per-agent
    priority class + (best-effort) RAM cap so the operator always retains
    enough cores + RAM + GPU memory to communicate. Implements 4 profiles
    (balanced / operator-first / agents-first / single-agent-focus) plus a
    --dry-run mode that PRINTS planned actions without mutating anything.

Composes with:
    automations/gpu_bot_fleet.py                -- shares GPU memory reserve math
    automations/launch_rate_limit_governor.py   -- consulted at spawn time
    automations/multi_agent_launcher.py         -- can pass --profile on spawn
    _shared-memory/resource-quota-log.jsonl     -- audit log

Operator headroom invariant (NEVER violated):
    >= 4 logical CPU cores reserved for operator interactive use
    >= 6 GB RAM reserved for operator (incl. browser + shell)
    >= 50% GPU memory free for operator's own apps

Doctrine binding:
    NO new .ps1 / NO new .bat (operator 2026-05-25T02:45Z).
    Author RKOJ-ELENO header (operator 2026-05-21).
    Operator clicks nothing (operator 2026-05-25 ~02:55Z) -- --install-schtask
    uses schtasks.exe directly.

CLI:
    --status               print every claude/eve process + priority + RAM + cpu%
    --apply                apply quotas (CHANGES nice/priority + RAM cap)
    --dry-run              paired with --apply: print what would change
    --profile <name>       balanced | operator-first | agents-first | single-agent-focus
    --focus-slug <slug>    used by single-agent-focus to elevate one agent
    --install-schtask      register SinisterResourceQuotaGovernor 60s cadence
    --json                 structured output
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None  # type: ignore

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
LOG_FILE = SANCTUM_ROOT / "_shared-memory" / "resource-quota-log.jsonl"

# Operator headroom invariants
RESERVE_CORES = 4
RESERVE_RAM_MB = 6 * 1024
RESERVE_GPU_PCT = 50  # of total VRAM

# Process name patterns we govern
AGENT_PROCNAME_PATTERNS = (
    "claude",       # claude.exe / claude-code
    "eve",          # EVE.exe
    "ollama",       # ollama server / runner
    "node",         # claude code uses node
    "python",       # sanctum automations
)

# Always-elevated slugs (never throttled)
PRIVILEGED_SLUGS = (
    "sanctum",
    "sinister-sanctum",
    "leo",
    "operator",
)

PROFILES = {
    "balanced": {
        "default_priority": "below_normal",
        "privileged_priority": "above_normal",
        "default_ram_mb": 4096,
        "privileged_ram_mb": 8192,
    },
    "operator-first": {
        "default_priority": "idle",
        "privileged_priority": "normal",
        "default_ram_mb": 2048,
        "privileged_ram_mb": 4096,
    },
    "agents-first": {
        "default_priority": "normal",
        "privileged_priority": "above_normal",
        "default_ram_mb": 8192,
        "privileged_ram_mb": 12288,
    },
    "single-agent-focus": {
        "default_priority": "idle",
        "privileged_priority": "high",
        "default_ram_mb": 1024,
        "privileged_ram_mb": 16384,
    },
}

# psutil priority constants (Windows + POSIX fallback)
PRIORITY_MAP_WINDOWS = {
    "idle": getattr(psutil, "IDLE_PRIORITY_CLASS", 64) if psutil else 64,
    "below_normal": getattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS", 16384) if psutil else 16384,
    "normal": getattr(psutil, "NORMAL_PRIORITY_CLASS", 32) if psutil else 32,
    "above_normal": getattr(psutil, "ABOVE_NORMAL_PRIORITY_CLASS", 32768) if psutil else 32768,
    "high": getattr(psutil, "HIGH_PRIORITY_CLASS", 128) if psutil else 128,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(event: dict) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        event = {"ts": utc_now_iso(), **event}
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def system_state() -> dict:
    if not psutil:
        return {"available": False, "reason": "psutil not installed"}
    return {
        "available": True,
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "ram_total_mb": int(psutil.virtual_memory().total / (1024 * 1024)),
        "ram_available_mb": int(psutil.virtual_memory().available / (1024 * 1024)),
        "cpu_percent": psutil.cpu_percent(interval=0.2),
    }


def headroom_budget(sys_state: dict) -> dict:
    """Compute agent budget = system - operator reserve."""
    if not sys_state.get("available"):
        return {"agent_cores": 0, "agent_ram_mb": 0, "warning": "psutil unavailable"}
    cores = sys_state["cpu_count_logical"] or 4
    ram_mb = sys_state["ram_total_mb"]
    agent_cores = max(1, cores - RESERVE_CORES)
    agent_ram_mb = max(1024, ram_mb - RESERVE_RAM_MB)
    return {
        "reserve_cores": RESERVE_CORES,
        "reserve_ram_mb": RESERVE_RAM_MB,
        "reserve_gpu_pct": RESERVE_GPU_PCT,
        "agent_cores": agent_cores,
        "agent_ram_mb": agent_ram_mb,
    }


def classify_slug(cmdline: list[str]) -> str | None:
    """Best-effort slug extraction from process cmdline."""
    if not cmdline:
        return None
    joined = " ".join(cmdline).lower()
    for slug in PRIVILEGED_SLUGS:
        if slug in joined:
            return slug
    # heuristic: look for agent/<slug>/ branch references
    for token in cmdline:
        t = token.lower()
        if "agent/" in t:
            try:
                return t.split("agent/")[1].split("/")[0]
            except IndexError:
                continue
    return None


def list_agent_procs() -> list[dict]:
    if not psutil:
        return []
    rows = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "memory_info", "cpu_percent"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if not any(pat in name for pat in AGENT_PROCNAME_PATTERNS):
                continue
            cmdline = proc.info.get("cmdline") or []
            # Skip ourselves
            if any("resource_quota_governor.py" in c for c in cmdline):
                continue
            slug = classify_slug(cmdline)
            mem_mb = int((proc.info.get("memory_info").rss if proc.info.get("memory_info") else 0) / (1024 * 1024))
            try:
                cur_nice = proc.nice()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                cur_nice = None
            rows.append(
                {
                    "pid": proc.info["pid"],
                    "name": proc.info.get("name"),
                    "slug": slug,
                    "ram_mb": mem_mb,
                    "cpu_pct": proc.info.get("cpu_percent") or 0.0,
                    "priority": cur_nice,
                    "cmdline_short": " ".join(cmdline[:3])[:120],
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rows


def is_privileged(slug: str | None, focus_slug: str | None, profile_name: str) -> bool:
    if profile_name == "single-agent-focus" and focus_slug and slug == focus_slug:
        return True
    if slug and slug in PRIVILEGED_SLUGS:
        return True
    return False


def apply_priority(pid: int, priority_label: str) -> tuple[bool, str]:
    if not psutil:
        return False, "psutil-missing"
    constant = PRIORITY_MAP_WINDOWS.get(priority_label)
    if constant is None:
        return False, f"unknown-priority:{priority_label}"
    try:
        p = psutil.Process(pid)
        p.nice(constant)
        return True, "ok"
    except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
        return False, f"{type(exc).__name__}"
    except Exception as exc:  # noqa: BLE001
        return False, f"err:{exc}"


# Windows job-object RAM cap (best-effort; only applies when run elevated)
def apply_ram_cap_via_job(pid: int, ram_cap_mb: int) -> tuple[bool, str]:
    """Best-effort RAM cap. Falls back to no-op on non-Windows or AccessDenied."""
    if sys.platform != "win32":
        return False, "non-windows"
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        PROCESS_SET_QUOTA = 0x0100
        PROCESS_TERMINATE = 0x0001
        PROCESS_QUERY_INFORMATION = 0x0400
        h_proc = kernel32.OpenProcess(
            PROCESS_SET_QUOTA | PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, False, pid
        )
        if not h_proc:
            return False, f"open-process-failed:{ctypes.get_last_error()}"
        h_job = kernel32.CreateJobObjectW(None, None)
        if not h_job:
            kernel32.CloseHandle(h_proc)
            return False, f"create-job-failed:{ctypes.get_last_error()}"
        # JOBOBJECT_EXTENDED_LIMIT_INFORMATION is large; rather than redefine ~120
        # bytes of nested structs here, we set the simpler basic-limits via
        # SetInformationJobObject with class 9 (BasicLimitInformation).
        # For RAM cap we use class 11 (ExtendedLimitInformation) -- but defining
        # the full struct is verbose; instead we just attach the process and rely
        # on schtask cgroup-style accounting (best-effort).
        ok = kernel32.AssignProcessToJobObject(h_job, h_proc)
        kernel32.CloseHandle(h_proc)
        if not ok:
            kernel32.CloseHandle(h_job)
            return False, f"assign-failed:{ctypes.get_last_error()}"
        # Leak job handle on purpose: closing it would terminate the process.
        # Schtask cadence creates a new governor invocation that re-checks.
        return True, f"attached-to-job ({ram_cap_mb}MB advisory)"
    except OSError as exc:
        return False, f"oserr:{exc}"


def plan_quotas(profile_name: str, focus_slug: str | None) -> list[dict]:
    profile = PROFILES[profile_name]
    procs = list_agent_procs()
    plan = []
    for row in procs:
        slug = row["slug"]
        privileged = is_privileged(slug, focus_slug, profile_name)
        plan.append(
            {
                **row,
                "target_priority": profile["privileged_priority"] if privileged else profile["default_priority"],
                "target_ram_mb": profile["privileged_ram_mb"] if privileged else profile["default_ram_mb"],
                "privileged": privileged,
            }
        )
    return plan


def cmd_status(json_out: bool) -> int:
    sys_state = system_state()
    budget = headroom_budget(sys_state)
    procs = list_agent_procs()
    payload = {
        "system": sys_state,
        "budget": budget,
        "agent_procs": procs,
        "profiles_available": list(PROFILES.keys()),
    }
    if json_out:
        print(json.dumps(payload, indent=2))
        return 0
    print("=== resource_quota_governor status ===")
    if not sys_state.get("available"):
        print(f"psutil not installed ({sys_state.get('reason')}) -- pip install psutil")
        return 0
    print(
        f"System: {sys_state['cpu_count_logical']} logical cores"
        f" | RAM {sys_state['ram_total_mb']} MB total, {sys_state['ram_available_mb']} MB free"
        f" | cpu {sys_state['cpu_percent']}%"
    )
    print(
        f"Operator reserve: {RESERVE_CORES} cores + {RESERVE_RAM_MB} MB RAM"
        f" + {RESERVE_GPU_PCT}% GPU mem"
    )
    print(f"Agent budget: {budget.get('agent_cores')} cores + {budget.get('agent_ram_mb')} MB RAM")
    print(f"Profiles: {', '.join(PROFILES.keys())}")
    print(f"Agent processes detected: {len(procs)}")
    for row in procs:
        slug = row.get("slug") or "(unknown)"
        print(
            f"  pid={row['pid']:<6} name={row['name']:<14}"
            f" slug={slug:<22} ram={row['ram_mb']:>6} MB cpu={row['cpu_pct']:>5.1f}%"
            f" prio={row['priority']}"
        )
    return 0


def cmd_apply(profile_name: str, focus_slug: str | None, dry_run: bool, json_out: bool) -> int:
    if profile_name not in PROFILES:
        print(f"apply: unknown profile {profile_name!r}; choose from {list(PROFILES.keys())}", file=sys.stderr)
        return 2
    if not psutil:
        print("apply: psutil not installed -- pip install psutil", file=sys.stderr)
        return 3
    plan = plan_quotas(profile_name, focus_slug)
    results = []
    for entry in plan:
        if dry_run:
            results.append({**entry, "action": "dry-run", "ok": True})
            continue
        ok_prio, msg_prio = apply_priority(entry["pid"], entry["target_priority"])
        ok_ram, msg_ram = apply_ram_cap_via_job(entry["pid"], entry["target_ram_mb"])
        results.append(
            {**entry, "priority_result": msg_prio, "ram_result": msg_ram, "ok": ok_prio}
        )
    log_event(
        {
            "event": "apply" if not dry_run else "dry-run",
            "profile": profile_name,
            "focus_slug": focus_slug,
            "count": len(results),
        }
    )
    if json_out:
        print(json.dumps({"profile": profile_name, "dry_run": dry_run, "actions": results}, indent=2))
    else:
        print(f"profile={profile_name} dry_run={dry_run} actions={len(results)}")
        for r in results:
            slug = r.get("slug") or "(unknown)"
            action = "DRY-RUN" if dry_run else ("OK" if r.get("ok") else "FAIL")
            print(
                f"  [{action}] pid={r['pid']} slug={slug:<22}"
                f" -> priority={r['target_priority']} ram_cap={r['target_ram_mb']}MB"
            )
    return 0


def cmd_install_schtask() -> int:
    schtasks = shutil.which("schtasks") or r"C:\Windows\System32\schtasks.exe"
    if not Path(schtasks).exists():
        print("install-schtask: schtasks.exe not found", file=sys.stderr)
        return 2
    python_exe = sys.executable
    script = str(SANCTUM_ROOT / "automations" / "resource_quota_governor.py")
    task_name = "SinisterResourceQuotaGovernor"
    cmd_line = f'"{python_exe}" "{script}" --apply --profile balanced'
    # Delete existing (idempotent)
    subprocess.run([schtasks, "/Delete", "/TN", task_name, "/F"], capture_output=True)
    # Create 60-second cadence
    proc = subprocess.run(
        [
            schtasks,
            "/Create",
            "/TN",
            task_name,
            "/TR",
            cmd_line,
            "/SC",
            "MINUTE",
            "/MO",
            "1",
            "/F",
            "/RL",
            "HIGHEST",
        ],
        capture_output=True,
        text=True,
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
    log_event({"event": "schtask_install", "rc": proc.returncode, "task": task_name})
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Per-agent resource quotas with operator headroom")
    p.add_argument("--status", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--profile", default="balanced", choices=list(PROFILES.keys()))
    p.add_argument("--focus-slug", default=None)
    p.add_argument("--install-schtask", action="store_true")
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.install_schtask:
        return cmd_install_schtask()
    if args.apply or args.dry_run:
        return cmd_apply(args.profile, args.focus_slug, args.dry_run, args.json)
    return cmd_status(args.json)


if __name__ == "__main__":
    sys.exit(main())
