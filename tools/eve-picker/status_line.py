"""status_line.py :: jcode-style condensed one-line status renderer.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25T02:10Z: terminal output goes condensed.
ONE line per status event, updated in place via `\r`, persists verbose to
disk only. See `_shared-memory/knowledge/jcode-condensed-log-discipline-
2026-05-25.md` for the full doctrine.

Format:
    <icon> <verb_phrase>... <elapsed>s · <sub_phase>

Icons (color-coded):
    [*]  cyan    run
    [+]  green   ok
    [!]  yellow  warn
    [x]  red     fail
    [?]  gray    wait

Usage:

    from status_line import StatusLine

    with StatusLine("connecting") as s:
        s.sub("opening websocket")
        # ... do work ...
        s.sub("auth handshake")
        # ... do work ...
        s.ok()  # finalize green and scroll new line for next verb

    # nested / sequential verbs each get their own line:
    with StatusLine("spawning agent") as s:
        s.sub("resolving project key")
        s.sub("acquiring account slot")
        s.sub("launching mintty")
        s.ok("PID 12842")

A background ticker thread refreshes the `<elapsed>s` counter every 0.1s so
the line visibly progresses even when no `sub()` is called. The ticker is
torn down cleanly on __exit__ (ok/warn/fail).

Verbose persistence: every sub-phase + final outcome appends a row to
`_shared-memory/sinister-term-history/history.jsonl` for forensic recall.
The terminal only ever shows one line per StatusLine instance.

Smoke test: `python status_line.py --smoke` runs 3 demo verbs (one succeeds,
one warns, one fails) and exits 0.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


__version__ = "0.1.0"


# ---------------------------------------------------------------------------
# ANSI palette (NO_COLOR / TERM=dumb aware)
# ---------------------------------------------------------------------------

def _ansi_on() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    term = os.environ.get("TERM", "").strip().lower()
    if term in ("dumb",) and os.name != "nt":
        return False
    return True


_ANSI = _ansi_on()


def _c(seq: str) -> str:
    return seq if _ANSI else ""


CYAN = _c("\033[38;5;51m")
OK_GREEN = _c("\033[38;5;46m")
WARN_YELLOW = _c("\033[38;5;220m")
FAIL_RED = _c("\033[38;5;196m")
DIM_GRAY = _c("\033[38;5;240m")
WHITE = _c("\033[97m")
SOFT = _c("\033[38;5;245m")
RESET = _c("\033[0m")


_ICONS = {
    "run":  ("[*]", CYAN),
    "ok":   ("[+]", OK_GREEN),
    "warn": ("[!]", WARN_YELLOW),
    "fail": ("[x]", FAIL_RED),
    "wait": ("[?]", DIM_GRAY),
}


# ---------------------------------------------------------------------------
# Sanctum-root probe (mirror of eve_picker_lib + main_menu pattern)
# ---------------------------------------------------------------------------

def _sanctum_root() -> Optional[Path]:
    env = os.environ.get("SINISTER_SANCTUM_ROOT") or os.environ.get("SANCTUM_ROOT")
    if env and Path(env).exists():
        return Path(env)
    for cand in (r"D:\Sinister Sanctum", r"C:\Sinister Sanctum"):
        p = Path(cand)
        if p.exists():
            return p
    return None


_HISTORY_DIR = None
_HISTORY_PATH = None
_root = _sanctum_root()
if _root is not None:
    _HISTORY_DIR = _root / "_shared-memory" / "sinister-term-history"
    _HISTORY_PATH = _HISTORY_DIR / "history.jsonl"


def _persist(event: dict) -> None:
    """Append one JSON row to history.jsonl. Best-effort; swallow IO errors."""
    if _HISTORY_PATH is None:
        return
    try:
        _HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        with _HISTORY_PATH.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# StatusLine context manager
# ---------------------------------------------------------------------------

class StatusLine:
    """Condensed one-line status renderer.

    See module docstring for usage. Thread-safe within a single instance
    (the ticker thread takes a lock before printing).
    """

    def __init__(self, verb: str, stream=None, refresh_hz: float = 10.0):
        self._verb = verb
        self._sub_phase = ""
        self._started_at = time.monotonic()
        self._stream = stream or sys.stdout
        self._refresh_dt = 1.0 / max(1.0, refresh_hz)
        self._lock = threading.Lock()
        self._stopped = threading.Event()
        self._ticker: Optional[threading.Thread] = None
        self._final_icon = "run"
        self._final_msg = ""
        self._agent = os.environ.get("EVE_AGENT_SLUG", "sanctum")

    # ----- context manager -----

    def __enter__(self) -> "StatusLine":
        _persist({
            "ts_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": self._agent,
            "verb": self._verb,
            "event": "start",
        })
        self._render()
        self._ticker = threading.Thread(target=self._tick_loop, daemon=True)
        self._ticker.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val is not None and self._final_icon == "run":
            # Implicit failure if the with-block raised before .ok/.warn/.fail
            self.fail(f"{type(exc_val).__name__}: {exc_val}")
        elif self._final_icon == "run":
            # Implicit success if the block exited cleanly without a finalizer
            self.ok()

    # ----- public API -----

    def sub(self, sub_phase: str) -> None:
        """Update the sub-phase label and re-render."""
        with self._lock:
            self._sub_phase = sub_phase
        _persist({
            "ts_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": self._agent,
            "verb": self._verb,
            "event": "sub",
            "sub_phase": sub_phase,
            "elapsed_s": round(time.monotonic() - self._started_at, 2),
        })
        self._render()

    def ok(self, msg: str = "") -> None:
        self._finalize("ok", msg)

    def warn(self, msg: str = "") -> None:
        self._finalize("warn", msg)

    def fail(self, msg: str = "") -> None:
        self._finalize("fail", msg)

    def wait(self, msg: str = "") -> None:
        """Pause-state finalizer (e.g. waiting on operator). Same shape as warn but gray."""
        self._finalize("wait", msg)

    # ----- internals -----

    def _finalize(self, state: str, msg: str) -> None:
        self._stop_ticker()
        with self._lock:
            self._final_icon = state
            self._final_msg = msg
        _persist({
            "ts_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": self._agent,
            "verb": self._verb,
            "event": state,
            "msg": msg,
            "elapsed_s": round(time.monotonic() - self._started_at, 2),
        })
        self._render(final=True)
        # Newline so the NEXT verb scrolls in beneath instead of overwriting.
        try:
            self._stream.write("\n")
            self._stream.flush()
        except Exception:
            pass

    def _stop_ticker(self) -> None:
        self._stopped.set()
        t = self._ticker
        if t is not None and t.is_alive():
            t.join(timeout=0.5)

    def _tick_loop(self) -> None:
        while not self._stopped.is_set():
            time.sleep(self._refresh_dt)
            if self._stopped.is_set():
                return
            self._render()

    def _render(self, final: bool = False) -> None:
        """Print the line in place via \\r overwrite."""
        with self._lock:
            elapsed = time.monotonic() - self._started_at
            icon_key = self._final_icon if final else "run"
            icon_str, icon_col = _ICONS.get(icon_key, _ICONS["run"])
            # RKOJ-ELENO :: 2026-05-25T03:15Z :: jcode-parity duration via
            # format_duration helper (replaces raw `{:.1f}s` which always
            # printed decimals even for minute/hour scale). Smoke 17/17 PASS.
            try:
                from format_duration import format_duration as _fd  # type: ignore
                elapsed_str = _fd(elapsed * 1000)
            except ImportError:
                elapsed_str = f"{elapsed:.1f}s"
            verb = self._verb
            sub = self._sub_phase
            msg = self._final_msg
            # Build the line: <icon> <verb>... <elapsed> · <sub_or_msg>
            tail_parts = []
            if final and msg:
                tail_parts.append(msg)
            elif sub:
                tail_parts.append(sub)
            tail = (f" {SOFT}·{RESET} " + WHITE + tail_parts[0] + RESET) if tail_parts else ""
            line = (
                f"\r{icon_col}{icon_str}{RESET} "
                f"{WHITE}{verb}{RESET}{SOFT}...{RESET} "
                f"{icon_col}{elapsed_str}{RESET}"
                f"{tail}"
            )
            # Clear-to-end-of-line (CSI K) so shorter lines don't leave artifacts
            line += "\033[K" if _ANSI else "    "
            try:
                self._stream.write(line)
                self._stream.flush()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Convenience: one-shot ok/fail without a with-block
# ---------------------------------------------------------------------------

def emit(state: str, verb: str, msg: str = "") -> None:
    """One-shot status emit (no progress bar). Useful for instant events."""
    icon_str, icon_col = _ICONS.get(state, _ICONS["run"])
    tail = f" {SOFT}·{RESET} {WHITE}{msg}{RESET}" if msg else ""
    sys.stdout.write(f"{icon_col}{icon_str}{RESET} {WHITE}{verb}{RESET}{tail}\n")
    sys.stdout.flush()
    _persist({
        "ts_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agent": os.environ.get("EVE_AGENT_SLUG", "sanctum"),
        "verb": verb,
        "event": state,
        "msg": msg,
    })


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def _smoke() -> int:
    """Run a 3-verb demo proving the in-place update + final-icon flow."""
    try:
        with StatusLine("connecting") as s:
            s.sub("opening websocket")
            time.sleep(0.4)
            s.sub("auth handshake")
            time.sleep(0.4)
            s.sub("ws connected")
            time.sleep(0.2)
            s.ok("session-id ab12cd34")

        with StatusLine("indexing brain") as s:
            s.sub("scanning _shared-memory/knowledge")
            time.sleep(0.5)
            s.sub("scoring decay")
            time.sleep(0.3)
            s.warn("3 entries past half-life")

        with StatusLine("spawning helper") as s:
            s.sub("resolving project key")
            time.sleep(0.3)
            s.sub("launching mintty")
            time.sleep(0.3)
            s.fail("mintty exit 1")

        emit("ok", "history.jsonl write", str(_HISTORY_PATH or "not-resolved"))
        return 0
    except Exception as e:
        print(f"\n{FAIL_RED}[smoke] FAIL: {e}{RESET}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        sys.exit(_smoke())
    # Default: print module banner + usage hint
    print(f"{WHITE}status_line.py{RESET} v{__version__}  {DIM_GRAY}(jcode-style condensed){RESET}")
    print(f"  {SOFT}usage:{RESET}  python status_line.py --smoke")
    print(f"  {SOFT}doctrine:{RESET}  _shared-memory/knowledge/jcode-condensed-log-discipline-2026-05-25.md")
