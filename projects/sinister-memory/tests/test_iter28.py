# Author: RKOJ-ELENO :: 2026-05-25
"""Iter-28 wait-for-heartbeat regression tests."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_wait_returns_fresh_when_hb_exists_and_recent(tmp_path: Path) -> None:
    from sinister_memory import heartbeat_wait

    hb_dir = tmp_path / "_shared-memory" / "heartbeats"
    hb_dir.mkdir(parents=True)
    (hb_dir / "test-lane.json").write_text(json.dumps({"slug": "test-lane"}), encoding="utf-8")

    result = heartbeat_wait.wait_for_heartbeat("test-lane", tmp_path, timeout_s=3.0, poll_interval_s=0.5)
    assert result["ok"] is True
    assert result["status"] == "fresh"
    assert result["elapsed_s"] < 1.5  # found on first poll


def test_wait_returns_missing_timeout_when_hb_never_appears(tmp_path: Path) -> None:
    from sinister_memory import heartbeat_wait
    (tmp_path / "_shared-memory" / "heartbeats").mkdir(parents=True)

    t0 = time.time()
    result = heartbeat_wait.wait_for_heartbeat("nonexistent", tmp_path, timeout_s=1.5, poll_interval_s=0.5)
    elapsed = time.time() - t0

    assert result["ok"] is False
    assert result["status"] == "missing-timeout"
    assert 1.0 <= elapsed <= 3.0  # should bail at timeout


def test_wait_returns_stale_when_hb_too_old(tmp_path: Path) -> None:
    from sinister_memory import heartbeat_wait

    hb_dir = tmp_path / "_shared-memory" / "heartbeats"
    hb_dir.mkdir(parents=True)
    hb_path = hb_dir / "old-lane.json"
    hb_path.write_text("{}", encoding="utf-8")
    # Backdate mtime by 5 minutes (over the default 120s freshness window)
    old_mtime = time.time() - 300
    os.utime(hb_path, (old_mtime, old_mtime))

    result = heartbeat_wait.wait_for_heartbeat("old-lane", tmp_path, timeout_s=1.0, poll_interval_s=0.3)
    assert result["ok"] is False
    assert result["status"] == "stale"
    assert result["age_s"] >= 240


def test_wait_rejects_invalid_slug(tmp_path: Path) -> None:
    from sinister_memory import heartbeat_wait
    result = heartbeat_wait.wait_for_heartbeat("bad slug!", tmp_path, timeout_s=0.5)
    assert result["ok"] is False
    assert result["status"] == "invalid-slug"


def test_wait_appears_late_within_timeout(tmp_path: Path) -> None:
    """File appears after first poll but before timeout -- must be detected."""
    import threading
    from sinister_memory import heartbeat_wait

    hb_dir = tmp_path / "_shared-memory" / "heartbeats"
    hb_dir.mkdir(parents=True)

    def _delayed_write():
        time.sleep(0.8)
        (hb_dir / "delayed.json").write_text("{}", encoding="utf-8")

    threading.Thread(target=_delayed_write, daemon=True).start()
    result = heartbeat_wait.wait_for_heartbeat("delayed", tmp_path, timeout_s=2.5, poll_interval_s=0.3)
    assert result["ok"] is True
    assert result["status"] == "fresh"


def test_iter41_freshness_used_s_present_in_all_return_paths(tmp_path: Path) -> None:
    """Iter-41 contradict-fix for iter-40: freshness_used_s must appear in EVERY
    return path (invalid-slug / missing-timeout / fresh / stale) so JSON
    consumers don't crash. Iter-40 only added it to fresh + stale."""
    import os
    from sinister_memory import heartbeat_wait

    hb_dir = tmp_path / "_shared-memory" / "heartbeats"
    hb_dir.mkdir(parents=True)

    # invalid-slug
    r_invalid = heartbeat_wait.wait_for_heartbeat("bad slug!", tmp_path, timeout_s=0.5)
    assert "freshness_used_s" in r_invalid, f"invalid-slug missing freshness_used_s: {r_invalid}"

    # missing-timeout
    r_missing = heartbeat_wait.wait_for_heartbeat("never-here", tmp_path, timeout_s=0.6, poll_interval_s=0.2)
    assert "freshness_used_s" in r_missing, f"missing-timeout missing freshness_used_s: {r_missing}"

    # fresh
    (hb_dir / "alive.json").write_text("{}", encoding="utf-8")
    r_fresh = heartbeat_wait.wait_for_heartbeat("alive", tmp_path, timeout_s=0.5)
    assert "freshness_used_s" in r_fresh, f"fresh missing freshness_used_s: {r_fresh}"

    # stale
    hb = hb_dir / "old.json"
    hb.write_text("{}", encoding="utf-8")
    os.utime(hb, (time.time() - 300, time.time() - 300))
    r_stale = heartbeat_wait.wait_for_heartbeat("old", tmp_path, timeout_s=0.5, freshness_window_s=120.0)
    assert "freshness_used_s" in r_stale, f"stale missing freshness_used_s: {r_stale}"


def test_iter43_grace_multiplier_rejects_negative(tmp_path: Path) -> None:
    """Iter-43 contradict-fix for iter-42: negative grace_multiplier was
    accepted + produced nonsense freshness_used_s (e.g. -10000.0 with gm=-100).
    Now rejected at function entry with status='invalid-grace-multiplier'."""
    from sinister_memory import heartbeat_wait

    (tmp_path / "_shared-memory" / "heartbeats").mkdir(parents=True)

    for gm in [-1.0, -100.0, -0.5]:
        r = heartbeat_wait.wait_for_heartbeat(
            "lane", tmp_path, timeout_s=0.5, from_heartbeat=True, grace_multiplier=gm,
        )
        assert r["ok"] is False, f"gm={gm} should be rejected; got {r}"
        assert r["status"] == "invalid-grace-multiplier", (
            f"gm={gm} status should be invalid-grace-multiplier; got {r['status']}"
        )
        assert r["grace_multiplier"] == gm
        # freshness_used_s should still be present (consistent shape from iter-41)
        assert "freshness_used_s" in r

    # gm=0.0 is technically valid (zero window = always stale; user opt-in)
    r_zero = heartbeat_wait.wait_for_heartbeat(
        "lane", tmp_path, timeout_s=0.5, from_heartbeat=True, grace_multiplier=0.0,
    )
    # 0 is non-negative, so it shouldn't be rejected -- it gives a 0-second window
    # which causes stale or missing-timeout, both legitimate
    assert r_zero["status"] != "invalid-grace-multiplier", (
        f"gm=0.0 is non-negative; should NOT be rejected; got {r_zero}"
    )


def test_iter42_grace_multiplier_configurable(tmp_path: Path) -> None:
    """Iter-42: grace_multiplier is configurable (was hardcoded 3.0).
    Same heartbeat, different multipliers, different fresh/stale verdicts."""
    import json as _json
    import os
    from sinister_memory import heartbeat_wait

    hb_dir = tmp_path / "_shared-memory" / "heartbeats"
    hb_dir.mkdir(parents=True)
    hb = hb_dir / "lane.json"
    hb.write_text(_json.dumps({"slug": "lane", "expected_interval_s": 100}), encoding="utf-8")
    # Backdate by 250s
    os.utime(hb, (time.time() - 250, time.time() - 250))

    # grace=1.0 -> 100s window -> 250 > 100 -> stale
    r_strict = heartbeat_wait.wait_for_heartbeat(
        "lane", tmp_path, timeout_s=0.5, from_heartbeat=True, grace_multiplier=1.0,
    )
    assert r_strict["ok"] is False
    assert r_strict["status"] == "stale"
    assert r_strict["freshness_used_s"] == 100.0

    # grace=3.0 -> 300s window -> 250 < 300 -> fresh
    r_default = heartbeat_wait.wait_for_heartbeat(
        "lane", tmp_path, timeout_s=0.5, from_heartbeat=True, grace_multiplier=3.0,
    )
    assert r_default["ok"] is True
    assert r_default["status"] == "fresh"
    assert r_default["freshness_used_s"] == 300.0

    # grace=10.0 -> 1000s window -> definitely fresh
    r_loose = heartbeat_wait.wait_for_heartbeat(
        "lane", tmp_path, timeout_s=0.5, from_heartbeat=True, grace_multiplier=10.0,
    )
    assert r_loose["ok"] is True
    assert r_loose["freshness_used_s"] == 1000.0


def test_iter40_from_heartbeat_uses_expected_interval(tmp_path: Path) -> None:
    """Iter-40 (iter-29 open item shipped): when --from-heartbeat is set, the
    freshness window comes from the heartbeat JSON's `expected_interval_s` (x3
    grace), not the default. Lets per-lane heartbeats declare their own cadence."""
    import json as _json
    import os
    from sinister_memory import heartbeat_wait

    hb_dir = tmp_path / "_shared-memory" / "heartbeats"
    hb_dir.mkdir(parents=True)
    hb = hb_dir / "slow-lane.json"
    hb.write_text(_json.dumps({"slug": "slow-lane", "expected_interval_s": 600}), encoding="utf-8")
    # Backdate file by 5 minutes (300s) -- would be stale under default 120s
    # but FRESH under expected_interval_s=600 (with 3x grace = 1800s)
    old_mtime = time.time() - 300
    os.utime(hb, (old_mtime, old_mtime))

    # Without --from-heartbeat: default freshness 120s -> stale
    r_default = heartbeat_wait.wait_for_heartbeat(
        "slow-lane", tmp_path, timeout_s=1.0, poll_interval_s=0.3, freshness_window_s=120.0,
    )
    assert r_default["ok"] is False
    assert r_default["status"] == "stale"

    # With --from-heartbeat: reads 600s, applies 3x grace = 1800s -> fresh
    r_fromhb = heartbeat_wait.wait_for_heartbeat(
        "slow-lane", tmp_path, timeout_s=1.0, poll_interval_s=0.3,
        freshness_window_s=120.0, from_heartbeat=True,
    )
    assert r_fromhb["ok"] is True, f"expected fresh; got {r_fromhb}"
    assert r_fromhb["status"] == "fresh"
    assert r_fromhb["freshness_used_s"] == 1800.0  # 600 * 3


def test_iter29_cli_exit_code_and_json_via_subprocess(tmp_path: Path) -> None:
    """Iter-29 contradict-fix for iter-28: verify CLI exit code + JSON output
    end-to-end via subprocess. iter-28 only tested the Python API directly,
    not the actual shell-chain behavior that callers will use.
    """
    import subprocess, json as _json

    hb_dir = tmp_path / "_shared-memory" / "heartbeats"
    hb_dir.mkdir(parents=True)
    (hb_dir / "alive.json").write_text(_json.dumps({"slug": "alive"}), encoding="utf-8")

    # Case 1: fresh heartbeat -> exit 0
    r1 = subprocess.run(
        [sys.executable, "-m", "sinister_memory", "--root", str(tmp_path),
         "wait-for-heartbeat", "alive", "--timeout", "1", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert r1.returncode == 0, f"alive case must exit 0; got {r1.returncode}; stderr={r1.stderr}"
    payload = _json.loads(r1.stdout)
    assert payload["ok"] is True
    assert payload["status"] == "fresh"

    # Case 2: missing heartbeat -> exit 1
    r2 = subprocess.run(
        [sys.executable, "-m", "sinister_memory", "--root", str(tmp_path),
         "wait-for-heartbeat", "nonexistent", "--timeout", "1", "--poll", "0.3", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert r2.returncode == 1, f"missing case must exit 1; got {r2.returncode}; stderr={r2.stderr}"
    payload2 = _json.loads(r2.stdout)
    assert payload2["ok"] is False
    assert payload2["status"] == "missing-timeout"
