"""format_duration.py :: jcode-parity duration formatter.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25T02:10Z: "we can save resources by doing it
jcodes way". jcode renders durations as `1.3s` / `42ms` / `2m 15s` per
`crates/jcode-message-types/src/lib.rs:211-227` (`format_duration`).

This is the Python port + PowerShell counterpart. Used by status_line.py +
EVE.exe + per-agent log emitters. Centralizing the rule means every surface
shows the same format ("connecting... 1.3s · opening websocket" not
"connecting... 0:00:01.3 · opening websocket").

Format spec (matches jcode):

    < 1 ms          -> "<1ms"
    < 1000 ms       -> "Nms"          (no decimals; integer ms)
    < 10000 ms      -> "N.Ns"         (one decimal; seconds)
    < 60000 ms      -> "Ns"           (integer seconds)
    < 3600000 ms    -> "Mm Ss"        (minute + seconds, both integer; drop "0s")
    >= 3600000 ms   -> "Hh Mm"        (hour + minutes, both integer; drop "0m")

Negative durations clamp to 0. Non-numeric input raises TypeError (loud-fail
per no-bullshit doctrine; don't paper over bugs with fake "0s" outputs).

Smoke test: `python format_duration.py --smoke` runs 12 cases.
"""
from __future__ import annotations

import sys
from typing import Union

__version__ = "0.1.0"


def format_duration(ms: Union[int, float]) -> str:
    """Format a duration in milliseconds as a human-readable string.

    See module docstring for the exact format spec (jcode parity).

    Raises TypeError on non-numeric input. Negative clamps to 0.
    """
    if not isinstance(ms, (int, float)) or isinstance(ms, bool):
        raise TypeError(f"format_duration: expected int or float ms, got {type(ms).__name__}")
    if ms < 0:
        ms = 0
    if ms < 1:
        return "<1ms"
    if ms < 1000:
        return f"{int(ms)}ms"
    if ms < 10000:
        # One decimal, e.g. "1.3s"
        return f"{ms / 1000:.1f}s"
    if ms < 60000:
        # Integer seconds, e.g. "42s"
        return f"{int(ms // 1000)}s"
    if ms < 3600000:
        # Minutes + seconds
        total_s = int(ms // 1000)
        m = total_s // 60
        s = total_s % 60
        if s == 0:
            return f"{m}m"
        return f"{m}m {s}s"
    # Hours + minutes
    total_m = int(ms // 60000)
    h = total_m // 60
    m = total_m % 60
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"


def format_duration_s(seconds: Union[int, float]) -> str:
    """Convenience wrapper for seconds (multiplies by 1000)."""
    return format_duration(seconds * 1000)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

_CASES = [
    (0,         "<1ms"),
    (0.5,       "<1ms"),
    (1,         "1ms"),
    (42,        "42ms"),
    (999,       "999ms"),
    (1000,      "1.0s"),
    (1300,      "1.3s"),
    (9999,      "10.0s"),
    (10000,     "10s"),
    (42000,     "42s"),
    (60000,     "1m"),
    (90000,     "1m 30s"),
    (3599000,   "59m 59s"),
    (3600000,   "1h"),
    (3660000,   "1h 1m"),
    (7320000,   "2h 2m"),
    (-100,      "<1ms"),  # negative clamps
]


def _smoke() -> int:
    fails = 0
    for ms, expected in _CASES:
        got = format_duration(ms)
        ok = (got == expected)
        if not ok:
            fails += 1
        marker = "[+]" if ok else "[x]"
        print(f"  {marker} format_duration({ms!r:>10}) -> {got!r:<10} (expected {expected!r})")
    if fails == 0:
        print(f"[+] format_duration smoke: {len(_CASES)}/{len(_CASES)} PASS")
        return 0
    print(f"[x] format_duration smoke: {fails}/{len(_CASES)} FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        sys.exit(_smoke())
    print(f"format_duration.py v{__version__}  (jcode-parity duration formatter)")
    print(f"  usage: python format_duration.py --smoke")
    print(f"  source spec: crates/jcode-message-types/src/lib.rs:211-227")
