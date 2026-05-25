# Sinister Term :: ascii_bridge.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# SA-PH6 :: bridge sinister-ascii into the running sterm shell.
# Operator vision (verbatim 2026-05-25T11:36Z): "have everything be slighly
# different based on the project ... showing me visual emotion while you
# work ... it being endless that leaves me breathles".
#
# Runs the sinister-ascii renderer in a DAEMON background thread at a low
# refresh rate (default 1 Hz) so it never blocks input. Renders a tiny
# entity glyph to a fixed terminal cell via OSC cursor save/restore; the
# operator's actual prompt cursor is undisturbed.
#
# Activated when:
#   - `SINISTER_ASCII` env in {on, 1, true, full}
#   - The sinister-ascii sub-project is importable (its source dir on sys.path)
#
# Off by default (operator hard-canonical 2026-05-25T12:09Z "laggy as fuck").
# Even when on, runs at 1 Hz with cached intensity reads so per-keystroke
# latency stays under the 2ms budget.

from __future__ import annotations

import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------- env gating ----------

_ENABLED_VALUES = frozenset({"on", "1", "true", "yes", "full"})


def is_enabled() -> bool:
    """Operator opt-in: only run when SINISTER_ASCII env is set on/1/true/yes/full."""
    return os.environ.get("SINISTER_ASCII", "").lower() in _ENABLED_VALUES


def project_for_current_dir() -> str:
    """Best-effort: pick the project key based on cwd → projects.json mapping.
    Falls back to 'sinister-term' so the default entity is Glyph-keeper."""
    try:
        # term.status already does cwd → project detection; reuse it
        from term.status import detect_project_for_cwd
        disp = detect_project_for_cwd()
        if not disp:
            return "sinister-term"
        # The detect helper returns display names (e.g. "Sinister Term");
        # map common ones back to keys.
        DISPLAY_TO_KEY = {
            "Sinister Sanctum":   "sinister-sanctum",
            "Sinister Term":      "sinister-term",
            "Sinister Forge":     "sinister-forge",
            "Sinister Mind":      "sinister-mind",
            "Sinister Overseer":  "sinister-overseer",
            "Sinister Chatbot":   "sinister-chatbot",
            "Sinister Vault":     "sinister-vault",
            "Sinister Memory":    "sinister-memory",
            "Sinister Kernel APK": "sinister-kernel-apk",
            "Sinister Panel":     "sinister-panel",
            "Sinister Link":      "sinister-link",
            "Sinister OS":        "sinister-os",
            "Sinister Emulator":  "sinister-emulator",
            "Sinister Designer":  "sinister-designer",
            "Sinister Watcher":   "sinister-watcher",
            "Sinister Bumble":    "sinister-bumble",
            "Eve EXE":            "eve-exe",
            "Eve Compliance":     "eve-compliance",
            "LetsText":           "letstext",
            "Showmasters":        "showmasters",
            "JB Woodworks":       "jb-woodworks",
        }
        return DISPLAY_TO_KEY.get(disp, disp.lower().replace(" ", "-") if isinstance(disp, str) else "sinister-term")
    except Exception:
        return "sinister-term"


# ---------- sinister-ascii import (best-effort + path-resolving) ----------

def _ensure_ascii_on_path() -> bool:
    """Inject sinister-ascii source dir on sys.path. Returns True if the
    import succeeded (or is already loaded), False otherwise."""
    if "sinister_ascii" in sys.modules:
        return True
    # Look for sinister-ascii relative to term/ : term/ → source/ → sinister-term/ → sinister-ascii/source
    here = Path(__file__).resolve()
    candidate = here.parent.parent.parent / "sinister-ascii" / "source"
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
    try:
        import sinister_ascii  # noqa: F401
        return True
    except Exception:
        return False


# ---------- bridge state ----------

@dataclass
class BridgeStatus:
    running: bool
    project_key: str
    refresh_seconds: float
    frames_rendered: int
    last_intensity: float
    started_at: Optional[float]
    error: Optional[str] = None


class AsciiBridge:
    """Background daemon-thread that polls intensity + paints a glyph corner.

    Start: bridge.start(); stop: bridge.stop(). Idempotent.
    """

    def __init__(self,
                 project_key: Optional[str] = None,
                 refresh_seconds: float = 1.0,
                 corner: str = "tr"):
        self._project_key = project_key or project_for_current_dir()
        self._refresh = max(0.25, float(refresh_seconds))
        self._corner = corner if corner in ("tl", "tr", "bl", "br") else "tr"
        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._frames = 0
        self._last_intensity = 0.0
        self._started_at: Optional[float] = None
        self._error: Optional[str] = None

    # ---- lifecycle ----

    def start(self) -> bool:
        """Start the daemon thread. Returns True if it started (or was
        already running); False if sinister-ascii is unavailable."""
        if self._thread and self._thread.is_alive():
            return True
        if not _ensure_ascii_on_path():
            self._error = "sinister_ascii not importable"
            return False
        self._stop_evt.clear()
        self._started_at = time.time()
        self._thread = threading.Thread(
            target=self._run, name="sinister-ascii-bridge", daemon=True
        )
        self._thread.start()
        return True

    def stop(self, *, join_timeout_s: float = 1.0) -> None:
        """Signal stop + best-effort join. Daemon thread will die with the
        process even if join times out."""
        self._stop_evt.set()
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=max(0.0, join_timeout_s))

    # ---- internal loop ----

    def _run(self) -> None:
        try:
            from sinister_ascii.entities import for_project
            from sinister_ascii.intensity import sample as sample_intensity
            from sinister_ascii.palette import color_at, rgb_to_ansi_truecolor
        except Exception as e:
            self._error = f"import failed: {e}"
            return

        entity = for_project(self._project_key)
        start = time.monotonic()

        while not self._stop_evt.is_set():
            try:
                snap = sample_intensity()
                self._last_intensity = snap.combined
                self._render_frame(entity, snap.combined,
                                   color_at, rgb_to_ansi_truecolor,
                                   elapsed=time.monotonic() - start)
                self._frames += 1
            except Exception as e:
                # Daemon must never crash the host shell — swallow + try
                # again next tick. Keep last error visible via status().
                self._error = f"render error: {e}"
            # Sleep in small slices so stop() responds quickly
            self._stop_evt.wait(self._refresh)

    def _render_frame(self, entity, intensity: float,
                      color_at, rgb_to_ansi_truecolor,
                      elapsed: float) -> None:
        """Paint a single glyph at the chosen corner. OSC save/restore so
        the operator's prompt cursor is undisturbed."""
        try:
            f = entity.frame(elapsed, activity_signal=intensity)
            r, g, b = color_at(entity.palette, elapsed, mix=f.intensity)
            glyph = entity.pick_glyph(f.intensity)
            color = rgb_to_ansi_truecolor(r, g, b)
            # corner placement — TR by default. Use ANSI cursor positioning.
            # Top-right corner is row 1, near right edge.
            # We can't easily query terminal size from a daemon thread; use a
            # safe column 78 (works on 80+ col terms).
            row, col = self._corner_cell()
            seq = (
                "\x1b[s"                       # save cursor
                f"\x1b[{row};{col}H"           # move
                f"{color}{glyph}\x1b[0m"       # paint + reset
                "\x1b[u"                       # restore cursor
            )
            sys.stdout.write(seq)
            sys.stdout.flush()
        except Exception:
            pass  # bridge must never raise

    def _corner_cell(self) -> tuple[int, int]:
        """Map self._corner to (row, col). Safe defaults for an 80x24 terminal."""
        try:
            import shutil
            sz = shutil.get_terminal_size((80, 24))
            cols, rows = sz.columns, sz.lines
        except Exception:
            cols, rows = 80, 24
        if self._corner == "tl":
            return (1, 1)
        if self._corner == "tr":
            return (1, max(1, cols - 1))
        if self._corner == "bl":
            return (max(1, rows), 1)
        # br
        return (max(1, rows), max(1, cols - 1))

    # ---- observability ----

    def status(self) -> BridgeStatus:
        return BridgeStatus(
            running=bool(self._thread and self._thread.is_alive()),
            project_key=self._project_key,
            refresh_seconds=self._refresh,
            frames_rendered=self._frames,
            last_intensity=self._last_intensity,
            started_at=self._started_at,
            error=self._error,
        )


# ---------- module-level convenience ----------

_DEFAULT_BRIDGE: Optional[AsciiBridge] = None
_DEFAULT_LOCK = threading.Lock()


def default_bridge() -> AsciiBridge:
    global _DEFAULT_BRIDGE
    with _DEFAULT_LOCK:
        if _DEFAULT_BRIDGE is None:
            _DEFAULT_BRIDGE = AsciiBridge()
        return _DEFAULT_BRIDGE


def start_if_enabled() -> bool:
    """Operator-facing entry point. Returns True if the bridge started."""
    if not is_enabled():
        return False
    return default_bridge().start()


def stop_default() -> None:
    """Shutdown for atexit / clean exit paths."""
    global _DEFAULT_BRIDGE
    with _DEFAULT_LOCK:
        b = _DEFAULT_BRIDGE
    if b is not None:
        b.stop()


__all__ = [
    "AsciiBridge",
    "BridgeStatus",
    "default_bridge",
    "is_enabled",
    "project_for_current_dir",
    "start_if_enabled",
    "stop_default",
]
