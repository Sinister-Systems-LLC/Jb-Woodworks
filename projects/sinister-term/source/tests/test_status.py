# Sinister Term :: tests/test_status.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# PH14 (restored 2026-05-25): pytest coverage for term.status — TTL-cached
# helpers feeding the bottom toolbar + breadcrumb prompt.

from __future__ import annotations

import time


def test_cached_caches_within_ttl():
    """_cached respects TTL — second call within TTL hits cache (no factory call)."""
    from term import status
    calls = {"n": 0}

    def factory():
        calls["n"] += 1
        return "x"

    # Use a unique cache key to avoid pollution from other tests
    key = "test_cached_caches_within_ttl_key"
    # iter-48 migration: status._cached now routes to term.cache (shared);
    # invalidate via the shared API instead of touching the old _CACHE dict.
    from term.cache import invalidate as _invalidate
    _invalidate("status", key)
    a = status._cached(key, ttl=5.0, factory=factory)
    b = status._cached(key, ttl=5.0, factory=factory)
    assert a == "x" and b == "x"
    assert calls["n"] == 1  # second hit served from cache


def test_cached_refreshes_after_ttl():
    """_cached refreshes when ttl elapses."""
    from term import status
    calls = {"n": 0}

    def factory():
        calls["n"] += 1
        return calls["n"]

    key = "test_cached_refreshes_after_ttl_key"
    from term.cache import invalidate as _invalidate
    _invalidate("status", key)
    a = status._cached(key, ttl=0.05, factory=factory)
    time.sleep(0.08)  # exceed ttl
    b = status._cached(key, ttl=0.05, factory=factory)
    assert a == 1
    assert b == 2
    assert calls["n"] == 2


def test_short_cwd_passthrough_for_short_path():
    """short_cwd returns the cwd unchanged when it fits the budget."""
    from term import status
    out = status.short_cwd(max_len=500)
    assert len(out) <= 500
    assert out  # non-empty


def test_short_cwd_truncates_with_ellipsis():
    """short_cwd shortens long paths with leading '...'."""
    from term import status
    out = status.short_cwd(max_len=10)
    assert len(out) == 10
    assert out.startswith("...")


def test_pending_inbox_count_returns_int():
    """pending_inbox_count returns an int (zero if no inbox)."""
    from term import status
    n = status.pending_inbox_count()
    assert isinstance(n, int)
    assert n >= 0


def test_freshest_sibling_heartbeat_shape():
    """Returns either None or (str, int) tuple."""
    from term import status
    out = status.freshest_sibling_heartbeat()
    if out is not None:
        agent, age = out
        assert isinstance(agent, str)
        assert isinstance(age, int)
        assert age >= 0


def test_git_branch_returns_str_or_none():
    """git_branch returns a string (current branch) or None when not in a repo."""
    from term import status
    b = status.git_branch()
    assert b is None or isinstance(b, str)


def test_detect_project_for_cwd_returns_str_or_none():
    """detect_project_for_cwd returns a display name (str) or None."""
    from term import status
    out = status.detect_project_for_cwd()
    assert out is None or isinstance(out, str)


def test_short_cwd_relative_to_project_returns_str():
    """short_cwd_relative_to_project always returns a non-empty string."""
    from term import status
    out = status.short_cwd_relative_to_project(max_len=50)
    assert isinstance(out, str)
    assert out  # non-empty
    assert len(out) <= 50
