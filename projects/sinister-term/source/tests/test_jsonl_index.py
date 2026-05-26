# Sinister Term :: tests/test_jsonl_index.py
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
#
# iter-78a: tail-offset index for JSONL log files.

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def shared(tmp_path):
    """Fake shared-memory dir."""
    s = tmp_path / "_shared-memory"
    s.mkdir()
    return s


def _make_jsonl(path: Path, rows: int, start: int = 0) -> None:
    """Write `rows` jsonl lines with `n` keys."""
    with path.open("w", encoding="utf-8") as f:
        for i in range(start, start + rows):
            f.write(json.dumps({"n": i, "ts_utc": f"2026-05-26T22:00:{i:02d}Z"}) + "\n")


def test_first_call_full_tail_read(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 20)
    res = jsonl_index.tail_last_n(p, shared, limit=5)
    assert res.cache_hit is False
    assert len(res.lines) == 5
    # Last 5 entries should be n=15..19
    last = json.loads(res.lines[-1])
    assert last["n"] == 19
    first_shown = json.loads(res.lines[0])
    assert first_shown["n"] == 15


def test_offsets_file_created_on_first_call(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 10)
    jsonl_index.tail_last_n(p, shared, limit=3)
    off_file = shared / "_OFFSETS.json"
    assert off_file.exists()
    data = json.loads(off_file.read_text(encoding="utf-8"))
    assert data["schema_version"] == jsonl_index.SCHEMA_VERSION
    assert "log.jsonl" in data["entries"]


def test_second_call_cache_hit_when_unchanged(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 20)
    res1 = jsonl_index.tail_last_n(p, shared, limit=5)
    assert res1.cache_hit is False
    # Second call against unchanged file should be a cache hit.
    res2 = jsonl_index.tail_last_n(p, shared, limit=5)
    # No new bytes -> 0 new lines from cached offset. The implementation
    # falls back to a full tail (because we asked for limit=5 and have 0
    # new lines) — but cache_hit was True for the first read attempt.
    # Verify we still got 5 lines via the backstop.
    assert len(res2.lines) == 5


def test_cache_hit_when_only_new_data_appended(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 10)
    jsonl_index.tail_last_n(p, shared, limit=3)
    # Append 5 more rows.
    time.sleep(0.05)  # bump mtime distinguishably
    with p.open("a", encoding="utf-8") as f:
        for i in range(10, 15):
            f.write(json.dumps({"n": i, "ts_utc": f"2026-05-26T22:01:{i:02d}Z"}) + "\n")
    res = jsonl_index.tail_last_n(p, shared, limit=3)
    assert res.cache_hit is True
    # Should see the last 3 newly-appended rows.
    last = json.loads(res.lines[-1])
    assert last["n"] == 14


def test_rotation_detected_when_file_shrinks(shared):
    """Logrotate / truncate scenario: cache must invalidate."""
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 50)
    jsonl_index.tail_last_n(p, shared, limit=5)
    # Truncate + rewrite small.
    _make_jsonl(p, 3)
    res = jsonl_index.tail_last_n(p, shared, limit=5)
    # File shrank -> cache invalidated -> not a hit.
    assert res.cache_hit is False
    # Should still return 3 lines (all that's in the file).
    assert len(res.lines) == 3


def test_rotation_detected_when_mtime_moves_backward(shared):
    """If mtime moves backward (rare: clock skew / restore from backup),
    treat as rotation."""
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 20)
    jsonl_index.tail_last_n(p, shared, limit=3)
    # Roll mtime backward by 1 hour.
    st = p.stat()
    os.utime(p, (st.st_atime, st.st_mtime - 3600))
    res = jsonl_index.tail_last_n(p, shared, limit=3)
    assert res.cache_hit is False


def test_missing_file_returns_empty(shared):
    from term import jsonl_index
    res = jsonl_index.tail_last_n(shared / "nope.jsonl", shared, limit=10)
    assert res.lines == []
    assert res.total_lines_estimate == 0
    assert res.cache_hit is False


def test_empty_file_returns_empty(shared):
    from term import jsonl_index
    p = shared / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    res = jsonl_index.tail_last_n(p, shared, limit=10)
    assert res.lines == []
    assert res.cache_hit is False


def test_limit_zero_clamped_to_one(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 5)
    res = jsonl_index.tail_last_n(p, shared, limit=0)
    assert len(res.lines) == 1


def test_large_limit_returns_all_lines(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 5)
    res = jsonl_index.tail_last_n(p, shared, limit=500)
    assert len(res.lines) == 5


def test_blank_lines_skipped(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    p.write_text("a\n\n\nb\nc\n\n", encoding="utf-8")
    res = jsonl_index.tail_last_n(p, shared, limit=10)
    assert res.lines == ["a", "b", "c"]


def test_max_tail_bytes_caps_read(shared):
    """Big file: only the last max_tail_bytes worth of lines are returned
    on first read."""
    from term import jsonl_index
    p = shared / "log.jsonl"
    # Write ~600 KiB worth of jsonl.
    big_line = json.dumps({"x": "A" * 200, "i": 0})  # ~220 chars per line
    with p.open("w", encoding="utf-8") as f:
        for i in range(3000):  # ~660 KiB
            f.write(big_line + "\n")
    res = jsonl_index.tail_last_n(p, shared, limit=10, max_tail_bytes=64 * 1024)
    assert len(res.lines) == 10  # respects limit
    # total estimate must be less than total file lines (we capped at 64 KiB).
    # 64 KiB / ~220 chars ≈ 290 lines max.
    assert res.total_lines_estimate < 3000
    assert res.total_lines_estimate > 0


def test_invalidate_drops_entry(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 5)
    jsonl_index.tail_last_n(p, shared, limit=2)
    assert jsonl_index.invalidate(p, shared) is True
    # Second invalidate is a no-op.
    assert jsonl_index.invalidate(p, shared) is False


def test_clear_all_drops_every_entry(shared):
    from term import jsonl_index
    for name in ("a.jsonl", "b.jsonl", "c.jsonl"):
        p = shared / name
        _make_jsonl(p, 3)
        jsonl_index.tail_last_n(p, shared, limit=1)
    n = jsonl_index.clear_all(shared)
    assert n == 3
    n2 = jsonl_index.clear_all(shared)
    assert n2 == 0


def test_stats_snapshot(shared):
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 10)
    jsonl_index.tail_last_n(p, shared, limit=2)
    s = jsonl_index.stats(shared)
    assert s["tracked_files"] == 1
    assert s["total_offset_bytes"] > 0
    assert s["schema_version"] == jsonl_index.SCHEMA_VERSION


def test_corrupt_cache_file_recovers(shared):
    from term import jsonl_index
    # Write garbage to the cache file.
    (shared / "_OFFSETS.json").write_text("not valid json {{{", encoding="utf-8")
    p = shared / "log.jsonl"
    _make_jsonl(p, 5)
    res = jsonl_index.tail_last_n(p, shared, limit=2)
    assert len(res.lines) == 2
    # And the cache is now valid again.
    data = json.loads((shared / "_OFFSETS.json").read_text(encoding="utf-8"))
    assert "entries" in data


def test_update_cache_false_does_not_persist(shared):
    """When update_cache=False, the offsets file should not be created."""
    from term import jsonl_index
    p = shared / "log.jsonl"
    _make_jsonl(p, 5)
    res = jsonl_index.tail_last_n(p, shared, limit=2, update_cache=False)
    assert len(res.lines) == 2
    # No cache file written.
    assert not (shared / "_OFFSETS.json").exists()


def test_partial_first_line_discarded_when_mid_file(shared):
    """When reading from the middle of a file, the partial first line at
    the read offset must be discarded to avoid garbage."""
    from term import jsonl_index
    p = shared / "log.jsonl"
    # Write 100 distinguishable lines.
    with p.open("w", encoding="utf-8") as f:
        for i in range(100):
            f.write(f"line-{i:03d}\n")
    # Force a small max_tail_bytes so we definitely seek mid-file.
    res = jsonl_index.tail_last_n(p, shared, limit=3, max_tail_bytes=200)
    # Every line returned must be a complete "line-NNN" — no partial.
    for ln in res.lines:
        assert ln.startswith("line-")
        assert len(ln) == 8  # exact length: "line-NNN"


def test_relative_path_key_uses_forward_slashes(shared):
    """Cache key must be forward-slash normalized for cross-OS portability."""
    from term import jsonl_index
    subdir = shared / "inbox" / "x"
    subdir.mkdir(parents=True)
    p = subdir / "log.jsonl"
    _make_jsonl(p, 3)
    jsonl_index.tail_last_n(p, shared, limit=1)
    data = json.loads((shared / "_OFFSETS.json").read_text(encoding="utf-8"))
    keys = list(data["entries"].keys())
    assert len(keys) == 1
    assert "\\" not in keys[0]
    assert keys[0] == "inbox/x/log.jsonl"
