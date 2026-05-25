# Sinister Term :: tests/test_cache.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Covers the consolidated term/cache.py — replaces 3 hand-rolled `_cached`
# helpers in status.py / intensity.py / jcode_popup.py.

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


from term import cache as termcache  # noqa: E402


@pytest.fixture(autouse=True)
def _clear():
    termcache.clear_all()
    yield
    termcache.clear_all()


def test_factory_called_once_within_ttl():
    calls = {"n": 0}
    def fac():
        calls["n"] += 1
        return 42
    a = termcache.cached("ns", "k", 5.0, fac)
    b = termcache.cached("ns", "k", 5.0, fac)
    assert a == 42 and b == 42
    assert calls["n"] == 1


def test_zero_ttl_bypasses_cache():
    calls = {"n": 0}
    def fac():
        calls["n"] += 1
        return 1
    termcache.cached("ns", "k", 0.0, fac)
    termcache.cached("ns", "k", 0.0, fac)
    assert calls["n"] == 2


def test_negative_ttl_bypasses_cache():
    calls = {"n": 0}
    def fac():
        calls["n"] += 1
        return 1
    termcache.cached("ns", "k", -1.0, fac)
    termcache.cached("ns", "k", -1.0, fac)
    assert calls["n"] == 2


def test_namespaces_are_isolated():
    termcache.cached("a", "k", 5.0, lambda: "a-val")
    termcache.cached("b", "k", 5.0, lambda: "b-val")
    assert termcache.cached("a", "k", 5.0, lambda: "fail") == "a-val"
    assert termcache.cached("b", "k", 5.0, lambda: "fail") == "b-val"


def test_invalidate_single_key():
    termcache.cached("ns", "k1", 5.0, lambda: 1)
    termcache.cached("ns", "k2", 5.0, lambda: 2)
    n = termcache.invalidate("ns", "k1")
    assert n == 1
    # k1 is recomputed, k2 stays
    assert termcache.cached("ns", "k1", 5.0, lambda: 99) == 99
    assert termcache.cached("ns", "k2", 5.0, lambda: 99) == 2


def test_invalidate_whole_namespace():
    termcache.cached("ns", "k1", 5.0, lambda: 1)
    termcache.cached("ns", "k2", 5.0, lambda: 2)
    termcache.cached("other", "k", 5.0, lambda: 3)
    n = termcache.invalidate("ns")
    assert n == 2
    # other namespace untouched
    assert termcache.cached("other", "k", 5.0, lambda: 99) == 3


def test_clear_all_drops_everything():
    termcache.cached("a", "k", 5.0, lambda: 1)
    termcache.cached("b", "k", 5.0, lambda: 2)
    n = termcache.clear_all()
    assert n == 2
    assert termcache.size() == 0


def test_ttl_expiry():
    calls = {"n": 0}
    def fac():
        calls["n"] += 1
        return calls["n"]
    a = termcache.cached("ns", "k", 0.05, fac)
    time.sleep(0.08)
    b = termcache.cached("ns", "k", 0.05, fac)
    assert a == 1
    assert b == 2


def test_size_reflects_entries():
    assert termcache.size() == 0
    termcache.cached("a", "k", 5.0, lambda: 1)
    termcache.cached("a", "k2", 5.0, lambda: 2)
    termcache.cached("b", "k", 5.0, lambda: 3)
    assert termcache.size() == 3


def test_concurrent_callers_share_factory():
    """Stampede protection: 10 threads requesting the same key should
    only invoke the factory ONCE within the TTL window."""
    calls = {"n": 0}
    started = threading.Event()
    def fac():
        calls["n"] += 1
        time.sleep(0.05)
        return 7
    results: list[int] = []
    def worker():
        started.wait()
        results.append(termcache.cached("ns", "k", 5.0, fac))
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    started.set()
    for t in threads:
        t.join()
    assert all(r == 7 for r in results)
    assert len(results) == 10
    # Stampede protection: factory called exactly once
    assert calls["n"] == 1
