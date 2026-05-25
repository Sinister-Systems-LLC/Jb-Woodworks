# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# SA-PH4 :: render_loop.py — drives the renderer at a target FPS, with
# auto-throttle if CPU budget is exceeded. Synchronous (single thread) for
# the demo loop; the future integration into sterm will run this in a
# dedicated worker thread so it never blocks input.

from __future__ import annotations

import signal
import sys
import time
from dataclasses import dataclass

from sinister_ascii.entities._base import Entity
from sinister_ascii.renderer import (
    Viewport, clear_screen, disable_alt_screen, enable_alt_screen,
    frame_string,
)

# Best-effort import of crash_recovery from the sibling sinister-term lane.
try:
    here = __file__
    _term_src = __import__("os").path.join(
        __import__("os").path.dirname(__import__("os").path.abspath(here)),
        "..", "..", "..", "source"
    )
    import sys as _sys
    if _term_src not in _sys.path:
        _sys.path.insert(0, _term_src)
    from term.crash_recovery import safe_loop, safe_call, install_atexit_reset, reset_terminal  # type: ignore
    _HAVE_RECOVERY = True
except Exception:
    _HAVE_RECOVERY = False
    def safe_loop(*a, **kw):  # type: ignore
        def deco(f): return f
        return deco
    def safe_call(*a, **kw):  # type: ignore
        def deco(f): return f
        return deco
    def install_atexit_reset(): pass  # type: ignore
    def reset_terminal(): pass  # type: ignore


@dataclass
class LoopConfig:
    target_fps: int = 60
    max_seconds: float | None = None
    activity_signal: float = 0.0
    use_alt_screen: bool = True


def _now_ms() -> float:
    return time.perf_counter() * 1000.0


@safe_loop("sinister_ascii.render_loop", max_restarts=10,
           backoff_initial_s=0.5, backoff_max_s=10.0)
def run(entity: Entity, config: LoopConfig | None = None) -> None:
    """Drive the renderer until SIGINT or max_seconds.

    Auto-throttles when sustained per-frame time exceeds budget — instead
    of trying to hit 60FPS on a busy CPU and burning more power, we drop
    to 30FPS, then 15FPS, then 10FPS in stages.
    """
    install_atexit_reset()
    cfg = config or LoopConfig()
    target_fps = max(5, min(120, cfg.target_fps))
    frame_budget_ms = 1000.0 / target_fps
    out = sys.stdout

    if cfg.use_alt_screen:
        out.write(enable_alt_screen())
        out.flush()

    started = time.perf_counter()
    overrun_streak = 0

    def _cleanup(*_a):
        if cfg.use_alt_screen:
            out.write(disable_alt_screen())
            out.flush()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, _cleanup)
    except (ValueError, OSError):
        pass

    viewport = Viewport.from_terminal()

    try:
        while True:
            t_now = time.perf_counter()
            elapsed = t_now - started
            if cfg.max_seconds is not None and elapsed >= cfg.max_seconds:
                break

            if int(elapsed * target_fps) % 30 == 0:
                viewport = Viewport.from_terminal()

            frame_start = _now_ms()
            s = frame_string(entity, elapsed,
                             activity_signal=cfg.activity_signal,
                             viewport=viewport)
            out.write(s)
            out.flush()
            frame_end = _now_ms()
            frame_time = frame_end - frame_start

            if frame_time > frame_budget_ms * 1.5:
                overrun_streak += 1
                if overrun_streak >= 3 and target_fps > 5:
                    target_fps = max(5, target_fps // 2)
                    frame_budget_ms = 1000.0 / target_fps
                    overrun_streak = 0
            else:
                overrun_streak = max(0, overrun_streak - 1)

            sleep_ms = frame_budget_ms - (_now_ms() - frame_start)
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
    finally:
        if cfg.use_alt_screen:
            out.write(disable_alt_screen())
            out.flush()
