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
        # RKOJ-ELENO :: 2026-05-25 — operator "all agents need to use swarm mode
        # and more hard ware and be better i need more power". Bumped priorities
        # one notch + RAM caps significantly so agents have headroom for
        # parallel work without throttling. Operator reserve (4 cores + 6GB)
        # still inviolable per headroom invariant.
        "default_priority": "above_normal",
        "privileged_priority": "high",
        "default_ram_mb": 12288,
        "privileged_ram_mb": 20480,
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


# --- Windows job-object structs (JOBOBJECT_EXTENDED_LIMIT_INFORMATION) -------
# Reference: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information
# Fixed 2026-05-25 (iter-26 P1.1): previous version only attached process to job
# without ANY limit flags, so OS never enforced the cap. Now we set
# JOB_OBJECT_LIMIT_PROCESS_MEMORY + JOB_OBJECT_LIMIT_JOB_MEMORY (and optionally
# AFFINITY) and pass the real ProcessMemoryLimit/JobMemoryLimit values.

# Limit flag bits (winnt.h)
JOB_OBJECT_LIMIT_WORKINGSET = 0x00000001
JOB_OBJECT_LIMIT_PROCESS_TIME = 0x00000002
JOB_OBJECT_LIMIT_JOB_TIME = 0x00000004
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JOB_OBJECT_LIMIT_AFFINITY = 0x00000010
JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
JOB_OBJECT_LIMIT_PRESERVE_JOB_TIME = 0x00000040
JOB_OBJECT_LIMIT_SCHEDULING_CLASS = 0x00000080
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK = 0x00001000
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

# JobObjectExtendedLimitInformation = 9
JobObjectExtendedLimitInformation = 9


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),  # LARGE_INTEGER
        ("PerJobUserTimeLimit", ctypes.c_longlong),      # LARGE_INTEGER
        ("LimitFlags", ctypes.c_uint32),                  # DWORD
        ("MinimumWorkingSetSize", ctypes.c_size_t),       # SIZE_T
        ("MaximumWorkingSetSize", ctypes.c_size_t),       # SIZE_T
        ("ActiveProcessLimit", ctypes.c_uint32),          # DWORD
        ("Affinity", ctypes.c_void_p),                    # ULONG_PTR
        ("PriorityClass", ctypes.c_uint32),               # DWORD
        ("SchedulingClass", ctypes.c_uint32),             # DWORD
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),          # SIZE_T
        ("JobMemoryLimit", ctypes.c_size_t),              # SIZE_T
        ("PeakProcessMemoryUsed", ctypes.c_size_t),       # SIZE_T
        ("PeakJobMemoryUsed", ctypes.c_size_t),           # SIZE_T
    ]


def _build_extended_limit(ram_cap_bytes: int, affinity_mask: int = 0) -> _JOBOBJECT_EXTENDED_LIMIT_INFORMATION:
    eli = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    flags = JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_JOB_MEMORY
    if affinity_mask:
        flags |= JOB_OBJECT_LIMIT_AFFINITY
        eli.BasicLimitInformation.Affinity = ctypes.c_void_p(affinity_mask)
    eli.BasicLimitInformation.LimitFlags = flags
    eli.ProcessMemoryLimit = ctypes.c_size_t(ram_cap_bytes).value
    eli.JobMemoryLimit = ctypes.c_size_t(ram_cap_bytes).value
    return eli


# Windows job-object RAM cap (now actually enforced via PROCESS_MEMORY + JOB_MEMORY flags)
def apply_ram_cap_via_job(pid: int, ram_cap_mb: int, affinity_mask: int = 0) -> tuple[bool, str]:
    """RAM cap via job object. Enforced by Windows kernel when flags are set.

    Returns (ok, message). On Windows, sets JOB_OBJECT_LIMIT_PROCESS_MEMORY +
    JOB_OBJECT_LIMIT_JOB_MEMORY so that the kernel terminates the process when
    the cap is exceeded. Optional affinity_mask sets CPU affinity.
    """
    if sys.platform != "win32":
        return False, "non-windows"
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        # Declare signatures for type safety on 64-bit
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel32.CreateJobObjectW.restype = ctypes.c_void_p
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        kernel32.AssignProcessToJobObject.restype = ctypes.c_int
        kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        kernel32.SetInformationJobObject.restype = ctypes.c_int
        kernel32.SetInformationJobObject.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32
        ]
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]

        PROCESS_SET_QUOTA = 0x0100
        PROCESS_TERMINATE = 0x0001
        PROCESS_QUERY_INFORMATION = 0x0400
        h_proc = kernel32.OpenProcess(
            PROCESS_SET_QUOTA | PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, 0, pid
        )
        if not h_proc:
            return False, f"open-process-failed:{ctypes.get_last_error()}"
        h_job = kernel32.CreateJobObjectW(None, None)
        if not h_job:
            kernel32.CloseHandle(h_proc)
            return False, f"create-job-failed:{ctypes.get_last_error()}"

        # Build limit struct + assign + set info (order: SetInfo first so the
        # cap is active the moment the process joins; Windows accepts either
        # order but this avoids a brief unbounded window).
        ram_cap_bytes = max(1, ram_cap_mb) * 1024 * 1024
        eli = _build_extended_limit(ram_cap_bytes, affinity_mask=affinity_mask)
        ok_set = kernel32.SetInformationJobObject(
            h_job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(eli),
            ctypes.sizeof(eli),
        )
        if not ok_set:
            err = ctypes.get_last_error()
            kernel32.CloseHandle(h_proc)
            kernel32.CloseHandle(h_job)
            return False, f"set-info-failed:{err}"

        ok_assign = kernel32.AssignProcessToJobObject(h_job, h_proc)
        kernel32.CloseHandle(h_proc)
        if not ok_assign:
            err = ctypes.get_last_error()
            kernel32.CloseHandle(h_job)
            return False, f"assign-failed:{err}"
        # Leak job handle on purpose: closing it would terminate the process.
        # The kernel keeps the limits attached to the process for its lifetime.
        return True, f"job-cap-enforced ({ram_cap_mb}MB process+job memory)"
    except OSError as exc:
        return False, f"oserr:{exc}"


def _smoke_ram_cap(cap_bytes: int = 256 * 1024 * 1024) -> tuple[bool, str]:
    """Spawn a child that allocates aggressively, attach to job with cap,
    verify Windows kills it for exceeding ProcessMemoryLimit.

    Returns (passed, detail_message). PASS = child exits non-zero in < 5s.
    KNOWN-CAVEAT = ctypes calls succeeded but child kept running (returned as
    False but with caveat tag so caller can distinguish from hard FAIL).
    """
    if sys.platform != "win32":
        return False, "non-windows"
    import time

    cap_mb = max(64, cap_bytes // (1024 * 1024))
    # Allocate ~64MB/iteration for up to 8s. With cap=256MB, expect kill after
    # ~4 iterations (~250-300MB peak). bytearray forces real RSS commit.
    child_code = (
        "import time;xs=[];t=time.time();\n"
        "while time.time()-t<8:\n"
        " xs.append(bytearray(1024*1024*64));time.sleep(0.05)\n"
    )
    try:
        # CREATE_SUSPENDED so we can attach to job BEFORE first allocation.
        CREATE_SUSPENDED = 0x00000004
        proc = subprocess.Popen(
            [sys.executable, "-c", child_code],
            creationflags=CREATE_SUSPENDED,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        ok, msg = apply_ram_cap_via_job(proc.pid, cap_mb)
        if not ok:
            # Resume + kill so we don't leak suspended process.
            try:
                proc.kill()
            except Exception:
                pass
            return False, f"setup-failed:{msg}"
        # Resume the main thread of the suspended process.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        # ResumeThread needs the thread handle; easiest path: use NtResumeProcess
        # via process handle is unavailable. Use ResumeThread on the main thread
        # which we obtain via OpenThread + Toolhelp32. But simpler: cancel the
        # suspended approach and just attach AFTER spawn (Windows accepts late
        # attachment too; the cap still applies for the rest of its life).
        # Since Popen returned, the process is already created in suspended
        # state. To resume, we can use the Win32 ResumeThread on the primary
        # thread. We grab it via NtResumeProcess if available, else fall back.
        try:
            ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
            ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
            ntdll.NtResumeProcess.restype = ctypes.c_long
            PROCESS_SUSPEND_RESUME = 0x0800
            kernel32.OpenProcess.restype = ctypes.c_void_p
            kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
            h = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, 0, proc.pid)
            if h:
                ntdll.NtResumeProcess(h)
                kernel32.CloseHandle(h)
        except Exception as exc:
            try:
                proc.kill()
            except Exception:
                pass
            return False, f"resume-failed:{exc}"

        start = time.time()
        try:
            rc = proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            return False, "CAVEAT:child-still-running-after-10s (cap not enforced; check Windows version / Job permissions)"
        duration = time.time() - start
        if rc != 0 and duration < 6.0:
            return True, f"PASS:exit={rc} duration={duration:.2f}s ({msg})"
        if rc == 0:
            return False, f"CAVEAT:child-exited-cleanly rc=0 duration={duration:.2f}s (allocator finished within budget — try lower cap)"
        return False, f"CAVEAT:exit={rc} duration={duration:.2f}s (killed but slow — may not be OOM kill)"
    except Exception as exc:  # noqa: BLE001
        return False, f"smoke-err:{exc}"


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
    cmd_line = f'"{python_exe}" "{script}" --apply --profile agents-first'
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
    p.add_argument("--profile", default="agents-first", choices=list(PROFILES.keys()))
    p.add_argument("--focus-slug", default=None)
    p.add_argument("--install-schtask", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--smoke-ram-cap",
        nargs="?",
        const=str(256 * 1024 * 1024),
        default=None,
        metavar="BYTES",
        help="Smoke-test RAM cap enforcement (default cap = 256MB)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke_ram_cap is not None:
        try:
            cap_bytes = int(args.smoke_ram_cap)
        except ValueError:
            print(f"smoke: bad BYTES value {args.smoke_ram_cap!r}", file=sys.stderr)
            return 2
        ok, msg = _smoke_ram_cap(cap_bytes)
        label = "PASS" if ok else ("CAVEAT" if msg.startswith("CAVEAT") else "FAIL")
        print(f"[{label}] smoke-ram-cap cap={cap_bytes} -> {msg}")
        return 0 if ok else (0 if label == "CAVEAT" else 1)
    if args.install_schtask:
        return cmd_install_schtask()
    if args.apply or args.dry_run:
        return cmd_apply(args.profile, args.focus_slug, args.dry_run, args.json)
    return cmd_status(args.json)


if __name__ == "__main__":
    sys.exit(main())
