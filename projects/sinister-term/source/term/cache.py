# Sinister Term :: cache.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Consolidated TTL cache primitive — replaces the 3 separate _cached
# helpers that lived in status.py / intensity.py / jcode_popup.py. Thread-
# safe, monotonic-clock based, namespaced.
#
# Operator hard-canonical 2026-05-25T~14:14Z ("rock solid in all aspects"):
# one cache implementation across the lane = fewer subtle bugs from
# divergent implementations.

from __future__ import annotations

import threading
import time
from typing import Callable, TypeVar


T = TypeVar("T")


# Single process-wide store. Keys are namespaced by caller to avoid
# collisions: `<namespace>:<key>`.
_STORE: dict[str, tuple[float, object]] = {}
_LOCK = threading.RLock()


def cached(namespace: str, key: str, ttl_seconds: float,
           factory: Callable[[], T]) -> T:
    """Return the cached value for (namespace, key) or compute + cache it.

    `ttl_seconds` is the freshness window in seconds (monotonic clock).
    A zero or negative ttl bypasses the cache entirely (always recompute).
    `factory` is called at most once per ttl window per key.

    Thread-safe: protected by a single recursive lock. The lock is held
    across the factory call so concurrent callers requesting the same
    key won't fan out N factory calls — they all wait + get the same value.
    """
    if ttl_seconds <= 0:
        return factory()
    full_key = f"{namespace}:{key}"
    now = time.monotonic()
    with _LOCK:
        hit = _STORE.get(full_key)
        if hit is not None and now - hit[0] < ttl_seconds:
            return hit[1]  # type: ignore[return-value]
        value = factory()
        _STORE[full_key] = (now, value)
        return value


def invalidate(namespace: str, key: str | None = None) -> int:
    """Drop cache entries.

    If `key` is None, drop ALL entries for the namespace.
    Returns the count of entries dropped.
    """
    with _LOCK:
        if key is None:
            prefix = f"{namespace}:"
            doomed = [k for k in _STORE if k.startswith(prefix)]
            for k in doomed:
                _STORE.pop(k, None)
            return len(doomed)
        full_key = f"{namespace}:{key}"
        return 1 if _STORE.pop(full_key, None) is not None else 0


def clear_all() -> int:
    """Wipe the entire cache (for tests + restart scenarios). Returns count."""
    with _LOCK:
        n = len(_STORE)
        _STORE.clear()
        return n


def size() -> int:
    """Current number of cached entries (observability)."""
    with _LOCK:
        return len(_STORE)


__all__ = ["cached", "invalidate", "clear_all", "size"]
