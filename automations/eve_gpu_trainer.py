"""eve_gpu_trainer.py — 24/7 GPU training daemon for EVE Compliance image moderation

Author: RKOJ-ELENO :: 2026-05-26

Operator hard-canonical 2026-05-26T17:14Z:
   "setup 24/7 training using my 4090 gpu that i can easily allocate resources
    to and turn on and off"

Design: projects/eve-compliance/training/DESIGN-GPU-TRAINER-2026-05-26.md
Primary path: PyTorch + HuggingFace Transformers + PEFT LoRA on top of
`Falconsai/nsfw_image_detection` (ViT-base-224), trained on the human-labeled
JSONL emitted by `LetsText/backend/scripts/export-moderation-training.ts`.

CLI:
   python automations/eve_gpu_trainer.py start          # spawn daemon (detached)
   python automations/eve_gpu_trainer.py stop           # graceful: finish batch + ckpt + exit
   python automations/eve_gpu_trainer.py status         # print heartbeat + control.json + pid
   python automations/eve_gpu_trainer.py pause          # alias: set --enabled false
   python automations/eve_gpu_trainer.py resume         # alias: set --enabled true
   python automations/eve_gpu_trainer.py set --gpu-pct N --batch N --enabled true|false --auto-pause true|false
   python automations/eve_gpu_trainer.py run            # foreground (the actual training loop)
   python automations/eve_gpu_trainer.py self-test      # inline assertions, no torch needed

Resource toggle model:
   control.json is the source of truth. Daemon watcher thread polls it every 5s
   and re-applies caps (GPU mem fraction, CPU threads, batch size, enabled
   flag). Pause does NOT free the model — it idles the train loop so the
   operator can flip back without re-init cost. Contention auto-pause kicks
   in when free VRAM drops below threshold (game/SD coexistence).

Singleton: per-machine pidfile at _shared-memory/eve-gpu-trainer.pid. Reuses
the same pattern as eve_compliance_train_loop.py so the fleet's monitoring
treats it identically.

This file is INTENTIONALLY runnable without torch installed (self-test +
status + set + stop work without any ML deps). The `run` subcommand is the
only one that requires torch/transformers/peft/pynvml — it defers imports
until called so install failures don't break the CLI.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
LETSTEXT_ROOT = Path("C:/Users/Zonia/Desktop/LetsText")
LANE_ROOT = SANCTUM_ROOT / "projects" / "eve-compliance"
TRAINING_ROOT = LANE_ROOT / "training"
VENV_PYTHON = TRAINING_ROOT / ".venv" / "Scripts" / "python.exe"

CONTROL_PATH = TRAINING_ROOT / "control.json"
PIDFILE_PATH = SANCTUM_ROOT / "_shared-memory" / "eve-gpu-trainer.pid"
HEARTBEAT_PATH = SANCTUM_ROOT / "_shared-memory" / "heartbeats" / "eve-gpu-trainer.json"
DATA_DIR = TRAINING_ROOT / "data"
WORKING_JSONL = DATA_DIR / "working.jsonl"
CHECKPOINT_DIR = TRAINING_ROOT / "checkpoints"
ADAPTER_DIR = TRAINING_ROOT / "adapters"
LOG_DIR = TRAINING_ROOT / "logs"

BASE_MODEL = "Falconsai/nsfw_image_detection"
DEFAULT_CONTROL: dict[str, Any] = {
    "$schema": "control.schema.json",
    "version": 1,
    "enabled": True,
    "gpu_mem_pct": 50,
    "max_batch": 32,
    "max_cpu_threads": 8,
    "checkpoint_every_steps": 500,
    "data_refresh_minutes": 60,
    "auto_pause_on_contention": True,
    "contention_free_vram_mb": 4096,
    "contention_hold_seconds": 30,
    "resume_free_vram_mb": 6144,
    "resume_hold_seconds": 60,
    "max_steps_per_session": 0,
    "base_model": BASE_MODEL,
    "lora_rank": 8,
    "learning_rate": 3e-5,
    "logging": {"level": "INFO"},
}

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    level=logging.INFO,
)
log = logging.getLogger("eve-gpu-trainer")

_shutdown_requested = False


def _handle_signal(signum: int, frame: Any) -> None:
    global _shutdown_requested
    log.info(f"Signal {signum} received — graceful shutdown after current batch")
    _shutdown_requested = True


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Singleton PID-file guard (copied from eve_compliance_train_loop.py R10) ──

def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            h = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not h:
                return False
            try:
                exit_code = ctypes.c_ulong()
                ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(exit_code))
                return bool(ok) and exit_code.value == STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(h)
        except (OSError, AttributeError):
            return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return pid > 0


def acquire_singleton_lock() -> tuple[bool, str]:
    PIDFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if PIDFILE_PATH.exists():
        try:
            existing = int(PIDFILE_PATH.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            existing = 0
        if existing and existing != os.getpid() and _pid_alive(existing):
            return False, f"pid {existing} already running"
    PIDFILE_PATH.write_text(str(os.getpid()), encoding="utf-8")
    return True, f"acquired pidfile pid={os.getpid()}"


def release_singleton_lock() -> None:
    try:
        if PIDFILE_PATH.exists():
            current = PIDFILE_PATH.read_text(encoding="utf-8").strip()
            if current == str(os.getpid()):
                PIDFILE_PATH.unlink()
    except OSError:
        pass


def read_pidfile() -> int:
    if not PIDFILE_PATH.exists():
        return 0
    try:
        return int(PIDFILE_PATH.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return 0


# ── Control file (hot-reload knob) ──────────────────────────────────────

def read_control() -> dict[str, Any]:
    if not CONTROL_PATH.exists():
        return dict(DEFAULT_CONTROL)
    try:
        loaded = json.loads(CONTROL_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        log.warning(f"control.json unreadable — falling back to defaults")
        return dict(DEFAULT_CONTROL)
    merged = dict(DEFAULT_CONTROL)
    merged.update(loaded)
    return merged


def write_control(updates: dict[str, Any]) -> dict[str, Any]:
    """Atomically merge `updates` into control.json. Returns the new state."""
    CONTROL_PATH.parent.mkdir(parents=True, exist_ok=True)
    current = read_control()
    current.update({k: v for k, v in updates.items() if v is not None})
    tmp = CONTROL_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(current, indent=2), encoding="utf-8")
    os.replace(tmp, CONTROL_PATH)
    return current


def ensure_control_exists() -> dict[str, Any]:
    if not CONTROL_PATH.exists():
        write_control({})
    return read_control()


# ── Heartbeat ───────────────────────────────────────────────────────────

def write_heartbeat(state: dict[str, Any]) -> None:
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    full = {
        "slug": "eve-gpu-trainer",
        "agent_display": "EVE GPU Trainer",
        "ts_utc": utc_now_iso(),
        "pid": os.getpid(),
        **state,
    }
    tmp = HEARTBEAT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(full, indent=2), encoding="utf-8")
    os.replace(tmp, HEARTBEAT_PATH)


def read_heartbeat() -> dict[str, Any]:
    if not HEARTBEAT_PATH.exists():
        return {}
    try:
        return json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


# ── CLI subcommands ─────────────────────────────────────────────────────

def cmd_start(args: argparse.Namespace) -> int:
    if read_pidfile() and _pid_alive(read_pidfile()):
        print(f"already running: pid {read_pidfile()}")
        return 0
    ensure_control_exists()
    cmd = [str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable,
           str(Path(__file__).resolve()), "run"]
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
    log_path = LOG_DIR / f"trainer-{utc_now_iso().replace(':', '')}.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logf = open(log_path, "ab")
    p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                         creationflags=flags, close_fds=True)
    # Don't wait for pid file — return immediately. Operator can `status`.
    print(f"spawned pid {p.pid} · log {log_path}")
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    pid = read_pidfile()
    if not pid or not _pid_alive(pid):
        print("not running")
        return 0
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.GenerateConsoleCtrlEvent(1, pid)  # CTRL_BREAK_EVENT
        except OSError:
            os.kill(pid, signal.SIGTERM)
    else:
        os.kill(pid, signal.SIGTERM)
    # Wait up to 60s for graceful release.
    for _ in range(60):
        if not _pid_alive(pid):
            print(f"stopped pid {pid}")
            return 0
        time.sleep(1)
    print(f"pid {pid} still alive after 60s — operator can `taskkill /PID {pid} /F` if needed")
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    pid = read_pidfile()
    ctrl = read_control()
    hb = read_heartbeat()
    alive = pid and _pid_alive(pid)
    lines = []
    lines.append(f"EVE GPU Trainer :: {'RUNNING' if alive else 'STOPPED'} (pid {pid or '-'})")
    lines.append("-" * 60)
    lines.append(f" enabled            {ctrl.get('enabled')}")
    lines.append(f" gpu_mem_pct        {ctrl.get('gpu_mem_pct')}")
    lines.append(f" max_batch          {ctrl.get('max_batch')}")
    lines.append(f" max_cpu_threads    {ctrl.get('max_cpu_threads')}")
    lines.append(f" auto_pause_on_*    {ctrl.get('auto_pause_on_contention')}")
    if hb:
        lines.append("-" * 60)
        lines.append(f" state              {hb.get('state', '?')}")
        lines.append(f" vram_used_mib      {hb.get('vram_used_mib', '?')}")
        lines.append(f" epoch              {hb.get('epoch', '-')}    step {hb.get('step', '-')}")
        lines.append(f" loss               {hb.get('loss', '-')}    eval_acc {hb.get('eval_acc', '-')}")
        lines.append(f" last_checkpoint    {hb.get('last_checkpoint', '-')}")
        lines.append(f" last_data_pull     {hb.get('last_data_pull_utc', '-')}")
        lines.append(f" ts_utc             {hb.get('ts_utc', '-')}")
    lines.append("-" * 60)
    lines.append(f" control.json       {CONTROL_PATH}")
    lines.append(f" heartbeat          {HEARTBEAT_PATH}")
    lines.append(f" pidfile            {PIDFILE_PATH}")
    lines.append(f" venv_python        {VENV_PYTHON} (exists: {VENV_PYTHON.exists()})")
    print("\n".join(lines))
    return 0 if alive else 1


def cmd_set(args: argparse.Namespace) -> int:
    updates: dict[str, Any] = {}
    if args.gpu_pct is not None:
        updates["gpu_mem_pct"] = max(5, min(95, args.gpu_pct))
    if args.batch is not None:
        updates["max_batch"] = max(1, min(256, args.batch))
    if args.cpu_threads is not None:
        updates["max_cpu_threads"] = max(1, min(64, args.cpu_threads))
    if args.enabled is not None:
        updates["enabled"] = args.enabled.lower() == "true"
    if args.auto_pause is not None:
        updates["auto_pause_on_contention"] = args.auto_pause.lower() == "true"
    new = write_control(updates)
    print(json.dumps(new, indent=2))
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    new = write_control({"enabled": False})
    print(f"paused — daemon will idle within 5s (model stays resident)")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    new = write_control({"enabled": True})
    print(f"resumed — daemon will resume training within 5s")
    return 0


def cmd_self_test(args: argparse.Namespace) -> int:
    """Inline assertions for control + heartbeat + pidfile. No torch needed."""
    import tempfile
    global CONTROL_PATH, PIDFILE_PATH, HEARTBEAT_PATH
    saved = (CONTROL_PATH, PIDFILE_PATH, HEARTBEAT_PATH)
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        CONTROL_PATH = td_p / "control.json"
        PIDFILE_PATH = td_p / "loop.pid"
        HEARTBEAT_PATH = td_p / "hb.json"

        def check(name: str, cond: bool, detail: str = "") -> None:
            tag = "PASS" if cond else "FAIL"
            print(f"  {tag}  {name}" + (f" :: {detail}" if detail and not cond else ""))
            if not cond:
                failures.append(name)

        # control round-trip
        ctrl = ensure_control_exists()
        check("ensure_control creates file", CONTROL_PATH.exists())
        check("default enabled is True", ctrl.get("enabled") is True)
        check("default gpu_mem_pct is 50", ctrl.get("gpu_mem_pct") == 50)

        # atomic write
        write_control({"gpu_mem_pct": 75, "enabled": False})
        ctrl2 = read_control()
        check("write_control updates gpu_mem_pct", ctrl2["gpu_mem_pct"] == 75)
        check("write_control updates enabled", ctrl2["enabled"] is False)
        check("write_control preserves other fields", ctrl2["max_batch"] == DEFAULT_CONTROL["max_batch"])

        # clamping in cmd_set
        class A: pass
        a = A()
        a.gpu_pct = 999; a.batch = 0; a.cpu_threads = None; a.enabled = "true"; a.auto_pause = None
        cmd_set(a)
        ctrl3 = read_control()
        check("cmd_set clamps gpu_pct to 95", ctrl3["gpu_mem_pct"] == 95)
        check("cmd_set clamps batch to 1", ctrl3["max_batch"] == 1)
        check("cmd_set parses enabled=true", ctrl3["enabled"] is True)

        # pidfile
        ok, _ = acquire_singleton_lock()
        check("acquire fresh pidfile", ok)
        ok2, _ = acquire_singleton_lock()
        check("idempotent re-acquire by same pid", ok2)
        PIDFILE_PATH.write_text("999999", encoding="utf-8")
        ok3, _ = acquire_singleton_lock()
        check("reclaim stale pidfile", ok3)
        release_singleton_lock()
        check("release removes pidfile", not PIDFILE_PATH.exists())

        # heartbeat
        write_heartbeat({"state": "TRAINING", "epoch": 1, "step": 100})
        hb = read_heartbeat()
        check("heartbeat round-trip state", hb.get("state") == "TRAINING")
        check("heartbeat includes pid", hb.get("pid") == os.getpid())
        check("heartbeat includes ts_utc", "ts_utc" in hb)

    CONTROL_PATH, PIDFILE_PATH, HEARTBEAT_PATH = saved
    print()
    if failures:
        print(f"FAIL :: {len(failures)} failed")
        return 1
    print(f"PASS :: all self-test assertions green")
    return 0


# ── The actual training loop (run subcommand) ───────────────────────────

def cmd_run(args: argparse.Namespace) -> int:
    """Foreground training loop. This is what `start` spawns detached."""
    ok, reason = acquire_singleton_lock()
    if not ok:
        log.warning(f"Singleton lock refused: {reason} — exiting cleanly")
        return 0

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    if os.name == "nt":
        try:
            signal.signal(signal.SIGBREAK, _handle_signal)  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass

    try:
        return _run_loop()
    finally:
        release_singleton_lock()


def _run_loop() -> int:
    """The actual training loop. Defers all ML imports so the rest of the
    CLI works even when torch isn't installed."""
    log.info("EVE GPU trainer starting")

    # Heartbeat right away so `status` can see us before ML imports.
    write_heartbeat({"state": "BOOTING", "msg": "importing ml stack"})

    try:
        import torch  # noqa: F401
    except ImportError as e:
        log.error(f"torch not installed — run `pip install torch==2.4.1+cu121 ...` in {VENV_PYTHON.parent}")
        write_heartbeat({"state": "ERROR", "error": f"torch ImportError: {e}"})
        return 2

    # Import-by-path: keeps the loop module decoupled from the CLI so torch
    # imports stay deferred until `run` is invoked.
    import importlib.util
    loop_path = Path(__file__).parent / "eve_gpu_trainer_loop.py"
    if not loop_path.exists():
        log.error(f"trainer loop module missing: {loop_path}")
        write_heartbeat({"state": "ERROR", "error": "trainer loop module missing"})
        return 3
    spec = importlib.util.spec_from_file_location("eve_gpu_trainer_loop", loop_path)
    if spec is None or spec.loader is None:
        return 4
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_training_loop(
        read_control_fn=read_control,
        write_heartbeat_fn=write_heartbeat,
        shutdown_check=lambda: _shutdown_requested,
        paths={
            "data": DATA_DIR,
            "checkpoints": CHECKPOINT_DIR,
            "adapters": ADAPTER_DIR,
            "logs": LOG_DIR,
            "working_jsonl": WORKING_JSONL,
            "letstext_root": LETSTEXT_ROOT,
        },
    )


# ── argparse wire-up ────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="eve_gpu_trainer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("start", help="Spawn the training daemon (detached)")
    sub.add_parser("stop", help="Graceful stop: finish batch + ckpt + exit")
    sub.add_parser("status", help="Print current state + control + heartbeat")
    sub.add_parser("pause", help="alias for `set --enabled false`")
    sub.add_parser("resume", help="alias for `set --enabled true`")
    sub.add_parser("run", help="Foreground training loop (used by `start`)")
    sub.add_parser("self-test", help="Inline assertions; no torch required")

    p_set = sub.add_parser("set", help="Update control.json knobs (hot-reload)")
    p_set.add_argument("--gpu-pct", type=int, default=None)
    p_set.add_argument("--batch", type=int, default=None)
    p_set.add_argument("--cpu-threads", type=int, default=None)
    p_set.add_argument("--enabled", choices=["true", "false"], default=None)
    p_set.add_argument("--auto-pause", choices=["true", "false"], default=None)

    args = parser.parse_args(argv)

    dispatch = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "set": cmd_set,
        "run": cmd_run,
        "self-test": cmd_self_test,
    }
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
