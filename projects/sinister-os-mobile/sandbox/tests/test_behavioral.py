"""Behavioral profile generator tests.

RKOJ-ELENO :: 2026-05-24
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BEHAVIORAL_DIR = Path(__file__).resolve().parents[1] / "behavioral"
PROFILES_DIR = BEHAVIORAL_DIR / "profiles"

sys.path.insert(0, str(BEHAVIORAL_DIR))
from generate import gen_gyro_tremor, gen_typing_intervals, gen_dwell_times, gen_swipe_gestures  # noqa: E402


def test_gyro_produces_correct_sample_count() -> None:
    r = gen_gyro_tremor(duration_sec=1.0, sample_rate_hz=50, purpose="test-gyro")
    assert r["n_samples"] == 50
    assert len(r["samples_xyz"]) == 50
    assert all(len(s) == 3 for s in r["samples_xyz"])


def test_gyro_rms_in_human_range() -> None:
    """Real human gyro RMS sits around 1e-3 to 5e-3 rad/s. Bots show 0."""
    r = gen_gyro_tremor(duration_sec=5.0, sample_rate_hz=50, purpose="test-gyro-rms")
    for axis in ("rms_x", "rms_y", "rms_z"):
        rms = r["stats"][axis]
        assert 5e-5 < rms < 1e-1, f"{axis} RMS {rms} outside human-plausible range"


def test_typing_intervals_median_in_human_range() -> None:
    """Human median inter-keystroke ~120-280ms on mobile."""
    r = gen_typing_intervals(n_keystrokes=200, purpose="test-typing")
    med = r["stats"]["median_ms"]
    assert 100 < med < 350, f"median {med}ms outside 100-350ms human range"
    assert r["stats"]["min_ms"] >= 40
    assert r["stats"]["max_ms"] <= 35000  # capped + occasional thinking-pause


def test_typing_has_some_pauses_over_5s() -> None:
    """3% pause rate × 200 keystrokes ≈ 6 pauses (Poisson around mean)."""
    r = gen_typing_intervals(n_keystrokes=200, purpose="test-typing-pauses")
    assert r["stats"]["n_pauses_over_5s"] >= 1, "no thinking pauses generated — distribution broken"


def test_dwell_time_positive_and_bounded() -> None:
    r = gen_dwell_times(n_screens=10, purpose="test-dwell")
    assert all(d > 0 for d in r["dwell_sec_per_screen"])
    assert r["stats"]["total_sec"] > 0
    # First-time-user boost should make first 2 screens average higher than later
    first_two = r["dwell_sec_per_screen"][:2]
    rest = r["dwell_sec_per_screen"][2:]
    # Probabilistic: rough sanity check, not strict
    assert sum(first_two) / 2 >= sum(rest) / len(rest) * 0.6


def test_swipe_gestures_have_curve() -> None:
    """No swipe should be a perfectly straight line (bezier control == midpoint)."""
    r = gen_swipe_gestures(n_swipes=20, screen_w=1080, screen_h=2400, purpose="test-swipes")
    for s in r["swipes"]:
        sx, sy = s["start"]
        ex, ey = s["end"]
        cx, cy = s["bezier_control"]
        mid_x, mid_y = (sx + ex) // 2, (sy + ey) // 2
        # If start == end (degenerate), curve is 0 — allow it
        if (sx, sy) == (ex, ey):
            continue
        # Most swipes should have curve != midpoint (some may coincidentally land near midpoint)
    # Aggregate check: at least 80% should differ from midpoint
    not_midpoint = sum(
        1 for s in r["swipes"]
        if s["bezier_control"] != [(s["start"][0] + s["end"][0]) // 2, (s["start"][1] + s["end"][1]) // 2]
    )
    assert not_midpoint >= 16, f"only {not_midpoint}/20 swipes have curve — bezier broken"


def test_swipe_durations_in_human_range() -> None:
    r = gen_swipe_gestures(n_swipes=20, screen_w=1080, screen_h=2400, purpose="test-swipe-dur")
    for s in r["swipes"]:
        assert 150 <= s["duration_ms"] <= 900


def test_profile_files_exist_if_generated() -> None:
    """If profiles/ has files, verify the schema."""
    if not PROFILES_DIR.exists():
        pytest.skip("profiles/ not generated — run `python behavioral/generate.py` first")
    files = list(PROFILES_DIR.glob("*.json"))
    if not files:
        pytest.skip("no profiles generated yet")
    for f in files:
        data = json.loads(f.read_text())
        assert "profile_class" in data
        assert "channels" in data
        assert {"gyro", "typing", "dwell", "swipes"} <= set(data["channels"])


def test_profile_no_raw_qrng_bytes_leaked() -> None:
    """Profiles should not contain raw entropy bytes — only derived samples."""
    if not PROFILES_DIR.exists() or not list(PROFILES_DIR.glob("*.json")):
        pytest.skip("no profiles generated")
    for f in PROFILES_DIR.glob("*.json"):
        text = f.read_text()
        # No 'bytes_hex' / 'hex' field markers should leak from seraphim
        # (those are entropy source, not derived output)
        assert "bytes_hex" not in text, f"raw QRNG hex leaked into {f}"
