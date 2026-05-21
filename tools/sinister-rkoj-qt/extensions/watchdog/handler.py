"""
Sinister RKOJ extension :: watchdog

Author: RKOJ-ELENO :: 2026-05-21

Bridges the RKOJ PyQt6 shell to `python -m sinister_watchdog` via QProcess so the
Qt event loop drains stdout/stderr without blocking the UI. Self-contained — no
imports from sinister_rkoj_qt.*. PyQt6 imports are deferred inside functions so
manifest.json can be parsed without Qt installed.

Hooks implemented:
  - hook_slash(args, pane, app)  : /watchdog status|tail|probe|tick
  - hook_ribbon(button_id, app)  : Start / Stop / Tail / Probe ribbon buttons
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from PyQt6.QtCore import QProcess  # noqa: F401
    from PyQt6.QtWidgets import QWidget  # noqa: F401


WATCHDOG_MODULE = "sinister_watchdog"
DEFAULT_TAIL_LINES = 50


class WatchdogExtension:
    """Plugin entry-point. One instance per RKOJ session."""

    id = "sinister-watchdog"
    version = "0.1.0"

    def __init__(self) -> None:
        # Tracks the long-running watchdog QProcess (when Start ribbon button clicked).
        # Keep it as Any so this module is import-safe without PyQt6.
        self._daemon_proc: Any | None = None
        # Tail viewer process (separate from daemon).
        self._tail_proc: Any | None = None

    # ------------------------------------------------------------ /watchdog
    def hook_slash(self, args: list[str], pane: "QWidget | None", app: Any) -> str:
        """
        /watchdog <subcommand> [args]
          status   — show daemon + heartbeat health
          tail [N] — stream last N log lines into the pane (default 50)
          probe    — probe every tracked heartbeat once
          tick     — fire a single watchdog tick (testing)
        """
        sub = (args[0] if args else "status").lower()
        rest = args[1:] if len(args) > 1 else []

        if sub == "status":
            return self._sync_run(["status"])
        if sub == "tail":
            n = self._safe_int(rest[0] if rest else None, DEFAULT_TAIL_LINES)
            return self._spawn_async_into_pane(["tail", "--lines", str(n)], pane)
        if sub == "probe":
            return self._sync_run(["probe"])
        if sub == "tick":
            return self._sync_run(["tick"])
        return f"[watchdog] unknown subcommand: {sub} (try: status|tail|probe|tick)"

    # ------------------------------------------------------------ ribbon ▶◼≡⌗
    def hook_ribbon(self, button_id: str, app: Any) -> dict[str, Any]:
        """Ribbon-button dispatcher. Returns a toast payload: {ok, message}."""
        if button_id == "watchdog.start":
            return self._ribbon_start()
        if button_id == "watchdog.stop":
            return self._ribbon_stop()
        if button_id == "watchdog.tail":
            return {"ok": True, "message": "Use /watchdog tail in an agent pane for live stream"}
        if button_id == "watchdog.probe":
            out = self._sync_run(["probe"])
            return {"ok": True, "message": out.splitlines()[0] if out else "probe done"}
        return {"ok": False, "message": f"unknown button: {button_id}"}

    def _ribbon_start(self) -> dict[str, Any]:
        """Spawn the watchdog daemon detached (if not already running)."""
        if self._daemon_proc is not None and self._is_running(self._daemon_proc):
            return {"ok": True, "message": "watchdog daemon already running"}
        try:
            QProcess = self._qprocess_cls()
            if QProcess is None:
                # Fall back to plain subprocess when Qt is unavailable (headless tests).
                self._daemon_proc = subprocess.Popen(
                    [sys.executable, "-m", WATCHDOG_MODULE, "daemon"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=self._detach_flags(),
                )
                return {"ok": True, "message": "watchdog daemon spawned (plain subprocess)"}
            proc = QProcess()
            proc.setProgram(sys.executable)
            proc.setArguments(["-m", WATCHDOG_MODULE, "daemon"])
            proc.startDetached()
            self._daemon_proc = proc
            return {"ok": True, "message": "watchdog daemon spawned"}
        except Exception as exc:
            return {"ok": False, "message": f"start failed: {exc}"}

    def _ribbon_stop(self) -> dict[str, Any]:
        """Ask the daemon to stop gracefully via the CLI."""
        out = self._sync_run(["stop"])
        if self._daemon_proc is not None:
            try:
                if hasattr(self._daemon_proc, "terminate"):
                    self._daemon_proc.terminate()
            except Exception:
                pass
            self._daemon_proc = None
        return {"ok": True, "message": out.splitlines()[0] if out else "watchdog stopped"}

    # ------------------------------------------------------------- internals
    def _sync_run(self, sub_args: list[str], timeout: float = 8.0) -> str:
        """Run `python -m sinister_watchdog <sub_args>` blocking; return combined output."""
        cmd = [sys.executable, "-m", WATCHDOG_MODULE, *sub_args]
        try:
            cp = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            out = (cp.stdout or "") + (cp.stderr or "")
            if not out.strip():
                return f"[watchdog] (no output; exit={cp.returncode})"
            return f"[watchdog] {' '.join(sub_args)}\n{out.rstrip()}"
        except FileNotFoundError:
            return "[watchdog] python interpreter not found"
        except subprocess.TimeoutExpired:
            return f"[watchdog] {' '.join(sub_args)} timed out after {timeout}s"
        except Exception as exc:
            return f"[watchdog] error: {exc}"

    def _spawn_async_into_pane(self, sub_args: list[str], pane: Any) -> str:
        """
        Spawn `python -m sinister_watchdog <sub_args>` via QProcess and route stdout
        into the pane's append_text() method (every pane is expected to expose this).
        Falls back to a sync run if Qt or the pane callback is unavailable.
        """
        QProcess = self._qprocess_cls()
        append: Callable[[str], None] | None = self._pane_appender(pane)
        if QProcess is None or append is None:
            return self._sync_run(sub_args)

        proc = QProcess()
        proc.setProgram(sys.executable)
        proc.setArguments(["-m", WATCHDOG_MODULE, *sub_args])

        def _on_stdout() -> None:
            data = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
            if data:
                append(data)

        def _on_stderr() -> None:
            data = bytes(proc.readAllStandardError()).decode("utf-8", errors="replace")
            if data:
                append(data)

        try:
            proc.readyReadStandardOutput.connect(_on_stdout)
            proc.readyReadStandardError.connect(_on_stderr)
        except Exception:
            # Older PyQt6 or stub object — fall back to blocking.
            return self._sync_run(sub_args)

        proc.start()
        # Stash on the pane so it isn't GC'd mid-stream.
        try:
            setattr(pane, "_watchdog_tail_proc", proc)
        except Exception:
            self._tail_proc = proc
        return f"[watchdog] streaming `{' '.join(sub_args)}` into pane..."

    # --------------------------------------------------------- Qt + helpers
    @staticmethod
    def _qprocess_cls() -> Any | None:
        try:
            from PyQt6.QtCore import QProcess  # noqa: WPS433
            return QProcess
        except Exception:
            return None

    @staticmethod
    def _pane_appender(pane: Any) -> Callable[[str], None] | None:
        if pane is None:
            return None
        for name in ("append_text", "append_output", "append"):
            fn = getattr(pane, name, None)
            if callable(fn):
                return fn  # type: ignore[return-value]
        return None

    @staticmethod
    def _is_running(proc: Any) -> bool:
        # subprocess.Popen
        if hasattr(proc, "poll"):
            return proc.poll() is None
        # QProcess
        if hasattr(proc, "state"):
            try:
                from PyQt6.QtCore import QProcess  # noqa: WPS433
                return proc.state() != QProcess.ProcessState.NotRunning
            except Exception:
                return True
        return False

    @staticmethod
    def _safe_int(value: str | None, default: int) -> int:
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _detach_flags() -> int:
        # Windows: DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        if sys.platform.startswith("win"):
            return 0x00000008 | 0x00000200
        return 0


# Doctrine-pattern bare-function fallback.
_singleton = WatchdogExtension()


def handle(args: list[str], pane: Any, app: Any) -> str:
    return _singleton.hook_slash(args, pane, app)
