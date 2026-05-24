"""sinister-wake :: wake-on-demand bot dispatcher (C.5 impl).

Author: RKOJ-ELENO :: 2026-05-24
Doctrine: _shared-memory/knowledge/wake-on-demand-bot-dispatcher-2026-05-23.md

Standalone implementation of the lazy-spawn + idle-kill pattern. The
sinister-bus lane can import this when ready:

    from sinister_wake.wake_dispatcher import WakeDispatcher
    dispatcher = WakeDispatcher()  # uses tools/sinister-wake/bot-config.json
    proc = dispatcher.ensure_alive("librarian")  # spawns if cold, refreshes if warm
    dispatcher.idle_sweep()  # call from a 60s timer thread

No external deps. Stdlib only.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "bot-config.json"
DEFAULT_IDLE_TTL = 300.0  # 5 min
DEFAULT_READY_TIMEOUT = 5.0


class WakeDispatcher:
    """Lazy-spawn + idle-kill manager for bot subprocesses.

    Thread-safe. ensure_alive() blocks until ready; idle_sweep() runs
    on a timer thread; bus_health_target() peeks without waking.
    """

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path or DEFAULT_CONFIG_PATH)
        self.config = self._load_config()
        self.alive_until: dict[str, float] = {}
        self.subprocs: dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()
        self.hot_bots: set[str] = set(self.config.get("hot_bots", ["custodian", "sinister-bus"]))
        self.global_idle_ttl: float = float(self.config.get("global_idle_ttl_sec", DEFAULT_IDLE_TTL))

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            text = self.config_path.read_text(encoding="utf-8-sig")
            return json.loads(text)
        except Exception as exc:
            print(f"[wake] config load error: {exc}", file=sys.stderr)
            return {}

    def _bot_config(self, name: str) -> dict[str, Any]:
        bots = self.config.get("bots", {})
        per_bot = bots.get(name, {})
        cwd = per_bot.get("cwd")
        if cwd is None:
            # default: <sanctum-root>/bots/agents/<name>/
            sanctum = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
            cwd = str(sanctum / "bots" / "agents" / name)
        return {
            "python": per_bot.get("python", sys.executable),
            "server": per_bot.get("server", str(Path(cwd) / "server.py")),
            "cwd": cwd,
            "env": {**os.environ, **per_bot.get("env", {})},
            "idle_ttl": float(per_bot.get("idle_ttl_sec", self.global_idle_ttl)),
        }

    def _wait_ready(self, proc: subprocess.Popen, timeout_s: float = DEFAULT_READY_TIMEOUT) -> bool:
        """Block until bot prints 'ready' to stderr OR timeout."""
        if proc.stderr is None:
            time.sleep(0.5)
            return True
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            line = proc.stderr.readline()
            if not line:
                if proc.poll() is not None:
                    return False
                time.sleep(0.05)
                continue
            text = line.decode("utf-8", errors="ignore") if isinstance(line, bytes) else line
            if "ready" in text.lower():
                return True
        return False

    def ensure_alive(self, name: str) -> subprocess.Popen | None:
        """Spawn bot if cold; refresh alive-until. Returns proc or None on failure."""
        with self.lock:
            now = time.time()
            proc = self.subprocs.get(name)
            if proc is not None and proc.poll() is None:
                cfg = self._bot_config(name)
                self.alive_until[name] = now + cfg["idle_ttl"]
                return proc
            cfg = self._bot_config(name)
            if not Path(cfg["server"]).exists():
                print(f"[wake] {name}: server.py missing at {cfg['server']}", file=sys.stderr)
                return None
            try:
                new_proc = subprocess.Popen(
                    [cfg["python"], cfg["server"]],
                    cwd=cfg["cwd"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=cfg["env"],
                )
            except Exception as exc:
                print(f"[wake] {name}: spawn failed: {exc}", file=sys.stderr)
                return None
            if not self._wait_ready(new_proc):
                print(f"[wake] {name}: not ready in {DEFAULT_READY_TIMEOUT}s", file=sys.stderr)
                try:
                    new_proc.terminate()
                except Exception:
                    pass
                return None
            self.subprocs[name] = new_proc
            self.alive_until[name] = now + cfg["idle_ttl"]
            return new_proc

    def idle_sweep(self) -> dict[str, str]:
        """Kill any subproc past its alive-until. Returns name -> action map."""
        actions: dict[str, str] = {}
        with self.lock:
            now = time.time()
            for name, until in list(self.alive_until.items()):
                if name in self.hot_bots:
                    actions[name] = "hot-keep"
                    continue
                if until < now:
                    proc = self.subprocs.get(name)
                    if proc and proc.poll() is None:
                        try:
                            proc.terminate()
                            actions[name] = "terminated"
                        except Exception as exc:
                            actions[name] = f"terminate-error: {exc}"
                    else:
                        actions[name] = "already-dead"
                    self.subprocs.pop(name, None)
                    self.alive_until.pop(name, None)
        return actions

    def bus_health_target(self, name: str) -> dict[str, Any]:
        """Peek bot state without waking. Returns alive/idle/cold + ttl remaining."""
        with self.lock:
            proc = self.subprocs.get(name)
            until = self.alive_until.get(name)
            if proc is None or proc.poll() is not None:
                state = "cold"
                ttl_remaining = 0.0
            else:
                state = "hot" if name in self.hot_bots else "warm"
                ttl_remaining = max(0.0, (until or 0.0) - time.time())
            return {
                "name": name,
                "state": state,
                "ttl_remaining_sec": round(ttl_remaining, 1),
                "pid": proc.pid if (proc and proc.poll() is None) else None,
                "in_hot_set": name in self.hot_bots,
            }

    def shutdown_all(self) -> dict[str, str]:
        """Terminate every tracked subproc. For clean process exit."""
        actions: dict[str, str] = {}
        with self.lock:
            for name, proc in list(self.subprocs.items()):
                if proc.poll() is None:
                    try:
                        proc.terminate()
                        actions[name] = "terminated"
                    except Exception as exc:
                        actions[name] = f"terminate-error: {exc}"
                else:
                    actions[name] = "already-dead"
            self.subprocs.clear()
            self.alive_until.clear()
        return actions


def start_sweep_thread(dispatcher: WakeDispatcher, interval_sec: float = 60.0) -> threading.Thread:
    """Start a daemon thread that calls dispatcher.idle_sweep() on a timer."""
    stop_event = threading.Event()

    def _loop():
        while not stop_event.wait(interval_sec):
            try:
                dispatcher.idle_sweep()
            except Exception as exc:
                print(f"[wake] idle_sweep error: {exc}", file=sys.stderr)

    t = threading.Thread(target=_loop, daemon=True, name="wake-idle-sweep")
    t.start()
    t.stop_event = stop_event  # type: ignore
    return t


if __name__ == "__main__":
    # Smoke test: instantiate, report HOT_BOTS + idle TTL, peek every bot's health.
    d = WakeDispatcher()
    print(f"WakeDispatcher loaded config from {d.config_path}")
    print(f"  hot_bots: {sorted(d.hot_bots)}")
    print(f"  global_idle_ttl_sec: {d.global_idle_ttl}")
    bots = sorted(d.config.get("bots", {}).keys() or ["sentinel", "librarian", "vault"])
    print(f"  configured bots: {bots}")
    print()
    print("Per-bot health (peek without wake):")
    for name in bots:
        h = d.bus_health_target(name)
        print(f"  {name:20} state={h['state']:6} ttl={h['ttl_remaining_sec']:6}s pid={h['pid']} hot={h['in_hot_set']}")
