# Sinister Term :: crash_recovery.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Port of jcode's panic-hook + terminal-restore pattern
# (src/cli/terminal.rs:21-38 + 141-157 + 238-254). Source MIT (Copyright (c)
# 2025 Jeremy Huang). Re-licensed under AGPL-3.0-or-later per upstream MIT.
#
# Provides:
#   - install_atexit_reset() — at exit, restore terminal mode (DECAWM on,
#     show cursor, disable bracketed paste, drop alternate screen). jcode
#     handles this via crossterm cleanup_tui_runtime; our equivalent writes
#     the matching ANSI escapes so even an abrupt SystemExit leaves the
#     terminal in a usable state.
#   - log_crash(context, exc) — append jsonl entry to ~/.sterm/crashes.jsonl
#     plus a CRASH line via concise_log.crash. Mirrors jcode's
#     mark_current_session_crashed.
#   - safe_call(fn, *args, ctx=...) — invoke fn; on exception log_crash
#     + return None. Never raises.
#   - safe_loop(loop_fn, ctx=..., max_consecutive_errors=...) — keep calling
#     loop_fn() until it returns False (clean exit) or N consecutive
#     exceptions force a give-up. Same shape as jcode's TUI lifecycle
#     `loop { … }` that survives transient panics.
#   - install_signal_handlers() — best-effort SIGTERM/SIGHUP handler that
#     calls restore_terminal() before re-raising. jcode terminal.rs:257-283
#     does the equivalent via tokio signal watchers.

from __future__ import annotations

import atexit
import json
import os
import signal
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

CRASH_LOG = Path.home() / ".sterm" / "crashes.jsonl"


# ---------------------------------------------------------------------------
# Terminal restore
# ---------------------------------------------------------------------------

# ANSI escapes we emit on shutdown. These are the minimum set that an
# interactive shell needs to leave the terminal in a good state:
#   ESC[?2004l  - disable bracketed paste (jcode DisableBracketedPaste)
#   ESC[?1004l  - disable focus change (jcode DisableFocusChange)
#   ESC[?1000l..1003l, ?1006l - disable mouse capture variants
#   ESC[?25h    - show cursor
#   ESC[?7h     - DECAWM on (line wrap)
#   ESC[?1049l  - leave alternate screen (jcode LeaveAlternateScreen)
#   ESC[?12l    - stop cursor blink override
#   ESC[0m      - reset SGR
_RESTORE_SEQ = (
    "\x1b[?2004l"  # bracketed paste off
    "\x1b[?1004l"  # focus events off
    "\x1b[?1000l\x1b[?1002l\x1b[?1003l\x1b[?1006l"  # mouse off
    "\x1b[?25h"    # show cursor
    "\x1b[?7h"     # line wrap on
    "\x1b[?1049l"  # leave alt screen
    "\x1b[?12l"    # cursor blink off (browser/iTerm sometimes flicker)
    "\x1b[0m"      # SGR reset
)

_restore_lock = threading.Lock()
_restored = False


def restore_terminal() -> None:
    """Idempotent. Writes the restore-escapes to stdout + stderr (whichever
    is a tty) and flushes. Safe to call from atexit/signal handlers."""
    global _restored
    with _restore_lock:
        if _restored:
            return
        _restored = True
    for stream in (sys.stdout, sys.stderr):
        try:
            if getattr(stream, "isatty", lambda: False)():
                stream.write(_RESTORE_SEQ)
                stream.flush()
                return
        except Exception:
            pass


def install_atexit_reset() -> None:
    """Hook restore_terminal into atexit. Calling more than once is
    idempotent (atexit dedup is automatic per function obj)."""
    atexit.register(restore_terminal)


def _allow_resignal() -> None:
    """Re-arm flag so restore_terminal can fire again on subsequent exits.
    Used by tests; not normally needed in production."""
    global _restored
    with _restore_lock:
        _restored = False


# ---------------------------------------------------------------------------
# Crash logging
# ---------------------------------------------------------------------------

def log_crash(context: str, exc: BaseException, extra: Optional[dict] = None) -> None:
    """Append a jsonl crash record. NEVER raises."""
    try:
        CRASH_LOG.parent.mkdir(parents=True, exist_ok=True)
        rec: dict[str, Any] = {
            "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "context": context,
            "type": exc.__class__.__name__,
            "message": str(exc)[:500],
            "traceback": traceback.format_exc(limit=8)[:4000],
            "pid": os.getpid(),
        }
        if extra:
            rec.update({k: v for k, v in extra.items() if isinstance(k, str)})
        with open(CRASH_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        # last-resort: best-effort stderr ping. We deliberately swallow.
        try:
            sys.stderr.write(f"[crash_recovery] could not write crash log\n")
        except Exception:
            pass

    # Also push to concise_log so the operator sees it in the same place
    # they see normal events.
    try:
        from term import concise_log as _cl
        _cl.crash(f"{exc.__class__.__name__}: {exc}", context)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# safe_call + safe_loop decorators (jcode-style error tolerance)
# ---------------------------------------------------------------------------

T = TypeVar("T")


def safe_call(fn: Callable[..., T], *args: Any, ctx: str = "", default: Optional[T] = None,
              **kwargs: Any) -> Optional[T]:
    """Call fn(*args, **kwargs). On any Exception (NOT BaseException — we let
    KeyboardInterrupt + SystemExit through), log_crash and return default."""
    try:
        return fn(*args, **kwargs)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:  # noqa: BLE001
        log_crash(ctx or getattr(fn, "__qualname__", "unknown"), e)
        return default


def safe_loop(step: Callable[[], bool], *, ctx: str = "loop",
              max_consecutive_errors: int = 5,
              backoff_initial_s: float = 0.05,
              backoff_max_s: float = 2.0) -> None:
    """Keep calling step() until it returns False (clean exit). If step
    raises Exception, increment consecutive-error count + exponential
    backoff. After max_consecutive_errors raises in a row, give up. A
    successful (non-raising) step resets the counter.

    Mirrors jcode's TUI event-loop posture (tui/app/turn.rs) where transient
    errors are absorbed; only an unrecoverable signal exits the loop."""
    errs = 0
    backoff = backoff_initial_s
    while True:
        try:
            keep_going = step()
            errs = 0
            backoff = backoff_initial_s
            if keep_going is False:
                return
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:  # noqa: BLE001
            log_crash(ctx, e, extra={"consecutive_errors": errs + 1})
            errs += 1
            if errs >= max_consecutive_errors:
                return
            time.sleep(backoff)
            backoff = min(backoff_max_s, backoff * 2.0)


# ---------------------------------------------------------------------------
# Signal handlers (Unix; Windows is a no-op since signal semantics differ)
# ---------------------------------------------------------------------------

def install_signal_handlers() -> None:
    """Install SIGTERM/SIGHUP handlers that restore the terminal before
    bubbling out. jcode does the equivalent in cli/terminal.rs:257-283."""
    def _handler(signum: int, _frame: Any) -> None:
        try:
            log_crash(f"signal_{signum}", RuntimeError(f"received signal {signum}"))
        finally:
            restore_terminal()
            # Re-raise default behaviour
            signal.signal(signum, signal.SIG_DFL)
            try:
                os.kill(os.getpid(), signum)
            except Exception:
                sys.exit(128 + signum)

    for sig_name in ("SIGTERM", "SIGHUP", "SIGQUIT"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            # Non-main thread or unsupported on this platform
            pass
