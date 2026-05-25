# Sinister Term :: tests/test_sinister_ascii_intensity.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Cover SA-PH5 intensity sampler: claude jsonl growth signal + bus broadcast
# signal + smooth-max combination + 2s TTL cache. No subprocess + no real
# claude reads — all paths are pytest tmp_paths.

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest


# Insert sinister-ascii source on sys.path at collection time
_ASCII_SRC = (
    Path(__file__).resolve().parents[2] / "sinister-ascii" / "source"
)
if _ASCII_SRC.exists() and str(_ASCII_SRC) not in sys.path:
    sys.path.insert(0, str(_ASCII_SRC))


from sinister_ascii.intensity import (  # noqa: E402
    BUS_BROADCASTS_SATURATION,
    CACHE_TTL_S,
    CLAUDE_GROWTH_SATURATION_BPS,
    IntensitySnapshot,
    WINDOW_S,
    reset_caches,
    sample,
)


@pytest.fixture(autouse=True)
def _clear_caches():
    reset_caches()
    yield
    reset_caches()


def test_zero_signal_when_no_inputs(tmp_path: Path):
    snap = sample(claude_root=tmp_path / "claude", sanctum_root=tmp_path / "sanctum")
    assert snap.claude_signal == 0.0
    assert snap.bus_signal == 0.0
    assert snap.combined == 0.0
    assert snap.claude_path is None
    assert snap.bus_broadcasts_in_window == 0


def test_claude_growth_signal_rises_with_size_delta(tmp_path: Path):
    cr = tmp_path / "claude" / "proj1"
    cr.mkdir(parents=True)
    sf = cr / "session.jsonl"
    sf.write_text("a" * 1000, encoding="utf-8")
    snap1 = sample(claude_root=tmp_path / "claude", sanctum_root=tmp_path / "sanctum")
    # First call: only one size sample in history; growth = 0
    assert snap1.claude_path is not None
    assert snap1.claude_signal == 0.0

    # Reset caches to force re-stat; wait a moment then grow the file
    reset_caches()
    time.sleep(0.05)
    sf.write_text("a" * 50_000, encoding="utf-8")  # +49k bytes
    # First read after reset: only 1 sample in history again, signal still 0
    _ = sample(claude_root=tmp_path / "claude", sanctum_root=tmp_path / "sanctum")
    time.sleep(0.05)
    sf.write_text("a" * 100_000, encoding="utf-8")  # +50k more
    # Wait past TTL to bypass cache before re-sampling
    time.sleep(CACHE_TTL_S + 0.05)
    sf.write_text("a" * 200_000, encoding="utf-8")
    snap2 = sample(claude_root=tmp_path / "claude", sanctum_root=tmp_path / "sanctum")
    assert snap2.claude_signal > 0.0
    assert snap2.claude_bytes_per_s > 0.0


def test_bus_signal_rises_with_broadcast_count(tmp_path: Path):
    sanctum = tmp_path / "sanctum"
    ca = sanctum / "_shared-memory" / "cross-agent"
    ca.mkdir(parents=True)
    # Write 3 broadcast files
    for i in range(3):
        (ca / f"{i:03d}-bcast.md").write_text("hi", encoding="utf-8")
    snap = sample(claude_root=tmp_path / "claude", sanctum_root=sanctum)
    assert snap.bus_broadcasts_in_window == 3
    expected = min(1.0, 3 / BUS_BROADCASTS_SATURATION)
    assert abs(snap.bus_signal - expected) < 1e-9


def test_bus_signal_saturates_at_one(tmp_path: Path):
    sanctum = tmp_path / "sanctum"
    ca = sanctum / "_shared-memory" / "cross-agent"
    ca.mkdir(parents=True)
    for i in range(int(BUS_BROADCASTS_SATURATION) + 5):
        (ca / f"{i:03d}-bcast.md").write_text("x", encoding="utf-8")
    snap = sample(claude_root=tmp_path / "claude", sanctum_root=sanctum)
    assert snap.bus_signal == 1.0
    assert snap.combined >= 1.0 - 1e-9


def test_bus_signal_ignores_old_files(tmp_path: Path):
    sanctum = tmp_path / "sanctum"
    ca = sanctum / "_shared-memory" / "cross-agent"
    ca.mkdir(parents=True)
    old = ca / "old.md"
    old.write_text("old", encoding="utf-8")
    # Set mtime to far in the past (well outside WINDOW_S)
    past = time.time() - (WINDOW_S * 2 + 60)
    import os
    os.utime(old, (past, past))
    snap = sample(claude_root=tmp_path / "claude", sanctum_root=sanctum)
    assert snap.bus_broadcasts_in_window == 0
    assert snap.bus_signal == 0.0


def test_smooth_max_combines_two_signals(tmp_path: Path):
    sanctum = tmp_path / "sanctum"
    ca = sanctum / "_shared-memory" / "cross-agent"
    ca.mkdir(parents=True)
    # 3 broadcasts → bus_signal = 3/6 = 0.5
    for i in range(3):
        (ca / f"{i:03d}-bcast.md").write_text("x", encoding="utf-8")
    snap = sample(claude_root=tmp_path / "claude", sanctum_root=sanctum)
    # Smooth max of (0, 0.5) should be ~0.5 (because the other is 0)
    assert 0.49 < snap.combined < 0.51


def test_sample_returns_snapshot_type(tmp_path: Path):
    snap = sample(claude_root=tmp_path / "x", sanctum_root=tmp_path / "y")
    assert isinstance(snap, IntensitySnapshot)
    assert snap.ts_seen > 0


def test_reset_caches_clears_history(tmp_path: Path):
    cr = tmp_path / "claude" / "proj"
    cr.mkdir(parents=True)
    sf = cr / "s.jsonl"
    sf.write_text("hello", encoding="utf-8")
    _ = sample(claude_root=tmp_path / "claude", sanctum_root=tmp_path / "sanctum")
    reset_caches()
    # After reset, the file's history is gone, but the file still exists.
    snap = sample(claude_root=tmp_path / "claude", sanctum_root=tmp_path / "sanctum")
    assert snap.claude_path is not None
    # Single sample after reset: growth = 0
    assert snap.claude_signal == 0.0


def test_constants_match_spec():
    """Pin spec constants so accidental edits get flagged in CI."""
    assert CACHE_TTL_S == 2.0
    assert WINDOW_S == 30.0
    assert CLAUDE_GROWTH_SATURATION_BPS == 4000.0
    assert BUS_BROADCASTS_SATURATION == 6.0
