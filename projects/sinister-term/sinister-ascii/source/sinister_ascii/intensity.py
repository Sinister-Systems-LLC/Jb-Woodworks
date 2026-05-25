# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# SA-PH5 :: intensity.py — reads "agent activity" signals so the entity
# glows brighter / moves faster when Claude is actively working.
#
# Two signal sources:
#   1. Claude session jsonl growth — `~/.claude/projects/<proj>/*.jsonl`
#      modification timestamp + size delta in the last N seconds. Faster
#      growth = more work happening.
#   2. Sinister bus broadcast rate — count of broadcasts in the last N
#      seconds from `_shared-memory/cross-agent/` + `_shared-memory/fleet-updates.jsonl`.
#      More broadcasts = busier fleet.
#
# Both signals are normalized to [0, 1] independently then combined with a
# smooth max (avoids one signal dominating). The combined value is the
# `activity_signal` consumed by `render_loop.LoopConfig` + `Entity.frame()`.
#
# Per-keystroke + per-frame discipline: stat() + small file reads only —
# never subprocess on the sampling path. All reads cached on a 2s TTL.

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# -------- tunables --------

CACHE_TTL_S = 2.0          # don't re-stat more often than this
WINDOW_S = 30.0            # rolling growth/broadcast window

# Claude session growth saturation: when the jsonl grows more than N bytes
# per second on average over the window, signal reaches 1.0.
CLAUDE_GROWTH_SATURATION_BPS = 4_000.0    # 4 KiB/s of new tokens = full glow

# Bus broadcast saturation: N broadcasts in the window = full glow.
BUS_BROADCASTS_SATURATION = 6.0


# -------- snapshot / cache --------

@dataclass
class IntensitySnapshot:
    ts_seen: float
    claude_signal: float          # [0, 1]
    bus_signal: float             # [0, 1]
    combined: float               # [0, 1] — smooth max of the two
    claude_path: Optional[str] = None
    claude_bytes_per_s: float = 0.0
    bus_broadcasts_in_window: int = 0


_CACHE: dict[str, tuple[float, object]] = {}


def _cached(key: str, factory, ttl: float = CACHE_TTL_S):
    now = time.monotonic()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    v = factory()
    _CACHE[key] = (now, v)
    return v


# -------- sources --------

def _newest_claude_jsonl(claude_root: Path) -> Optional[Path]:
    """Find the most recently-modified ~/.claude/projects/<proj>/*.jsonl."""
    def _impl() -> Optional[Path]:
        if not claude_root.exists():
            return None
        newest: Optional[Path] = None
        newest_mtime = 0.0
        try:
            for sub in claude_root.iterdir():
                if not sub.is_dir():
                    continue
                try:
                    for f in sub.glob("*.jsonl"):
                        try:
                            m = f.stat().st_mtime
                        except OSError:
                            continue
                        if m > newest_mtime:
                            newest_mtime = m
                            newest = f
                except OSError:
                    continue
        except OSError:
            return None
        return newest
    return _cached(f"newest_jsonl:{claude_root}", _impl, ttl=CACHE_TTL_S)


# RKOJ-ELENO :: 2026-05-25 :: migrated to term.cache shared primitive
# (iter-47/48). Tries the sibling sinister-term cache; falls back to a
# local helper if the import path isn't wired (e.g. running standalone).
try:
    from term.cache import cached as _shared_cached  # type: ignore

    def _cached_via_shared(key, factory, ttl=CACHE_TTL_S):
        return _shared_cached("ascii_intensity", key, ttl, factory)

    _cached = _cached_via_shared  # noqa: F811 — intentional override
except Exception:
    pass  # keep the local _cached helper defined above


# Track jsonl size at last sample so we can compute bytes/s growth
_SIZE_HISTORY: dict[str, list[tuple[float, int]]] = {}


def _claude_growth_signal(claude_root: Optional[Path] = None) -> tuple[float, float, Optional[str]]:
    """Returns (signal_in_0_1, bytes_per_s, path_str_or_None)."""
    root = claude_root or (Path.home() / ".claude" / "projects")
    newest = _newest_claude_jsonl(root)
    if newest is None:
        return (0.0, 0.0, None)
    try:
        size = newest.stat().st_size
    except OSError:
        return (0.0, 0.0, str(newest))

    now = time.time()
    key = str(newest)
    history = _SIZE_HISTORY.setdefault(key, [])
    history.append((now, size))
    # Prune entries older than 2 windows
    cutoff = now - 2 * WINDOW_S
    history[:] = [(t, s) for t, s in history if t >= cutoff]

    if len(history) < 2:
        return (0.0, 0.0, str(newest))

    # Compute bytes/s over the in-window samples
    t_first, s_first = history[0]
    t_last, s_last = history[-1]
    dt = max(0.001, t_last - t_first)
    bps = max(0.0, (s_last - s_first) / dt)

    signal = min(1.0, bps / CLAUDE_GROWTH_SATURATION_BPS)
    return (signal, bps, str(newest))


def _bus_broadcast_signal(sanctum_root: Optional[Path] = None) -> tuple[float, int]:
    """Returns (signal_in_0_1, broadcasts_in_window).

    Counts files in `_shared-memory/cross-agent/` modified in the last WINDOW_S
    seconds (we treat each cross-agent file as one broadcast).
    """
    root = sanctum_root or Path(
        os.environ.get("SINISTER_SANCTUM_ROOT", "D:/Sinister Sanctum")
    )
    ca_dir = root / "_shared-memory" / "cross-agent"

    def _impl() -> tuple[float, int]:
        if not ca_dir.exists():
            return (0.0, 0)
        cutoff = time.time() - WINDOW_S
        count = 0
        try:
            for f in ca_dir.iterdir():
                try:
                    if f.stat().st_mtime >= cutoff:
                        count += 1
                except OSError:
                    continue
        except OSError:
            return (0.0, 0)
        signal = min(1.0, count / BUS_BROADCASTS_SATURATION)
        return (signal, count)

    return _cached(f"bus:{ca_dir}", _impl, ttl=CACHE_TTL_S)


def _smooth_max(a: float, b: float) -> float:
    """Soft max — feels like the louder signal dominates but the quieter one
    still nudges. p-norm with p=4 gives a nice rounded max."""
    p = 4.0
    return min(1.0, ((a ** p) + (b ** p)) ** (1.0 / p))


# -------- public API --------

def sample(claude_root: Optional[Path] = None,
           sanctum_root: Optional[Path] = None) -> IntensitySnapshot:
    """Sample both signals + return a snapshot. Safe to call every frame."""
    c_sig, c_bps, c_path = _claude_growth_signal(claude_root)
    b_sig, b_count = _bus_broadcast_signal(sanctum_root)
    combined = _smooth_max(c_sig, b_sig)
    return IntensitySnapshot(
        ts_seen=time.time(),
        claude_signal=c_sig,
        bus_signal=b_sig,
        combined=combined,
        claude_path=c_path,
        claude_bytes_per_s=c_bps,
        bus_broadcasts_in_window=b_count,
    )


def reset_caches() -> None:
    """Clear cached samples (for tests + restart scenarios)."""
    _CACHE.clear()
    _SIZE_HISTORY.clear()


__all__ = [
    "IntensitySnapshot",
    "sample",
    "reset_caches",
    "CACHE_TTL_S",
    "WINDOW_S",
    "CLAUDE_GROWTH_SATURATION_BPS",
    "BUS_BROADCASTS_SATURATION",
]
