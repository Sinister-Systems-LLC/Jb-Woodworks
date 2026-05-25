# Sinister Term :: tests/test_sinister_ascii.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Unit-level smoke for the sinister-ascii sub-project (SA-PH1+PH2+PH3+PH4).
# Verifies palette math determinism, motion primitive shape, entity registry
# completeness, and renderer/frame_string output sanity. No subprocess work
# on render path — all imports + pure-function calls.

from __future__ import annotations

import sys
from pathlib import Path

import pytest


# Inject sinister-ascii source onto sys.path the same way demo.py does, so
# this test runs from the same `pytest -q` invocation as the term tests.
# Module-level insertion runs at collection time — guarantees the path is
# available to any sibling test that does `import sinister_ascii`.
_ASCII_SRC = (
    Path(__file__).resolve().parents[2] / "sinister-ascii" / "source"
)
if _ASCII_SRC.exists() and str(_ASCII_SRC) not in sys.path:
    sys.path.insert(0, str(_ASCII_SRC))


def test_public_api_importable():
    import sinister_ascii as sa
    assert sa.__version__ == "0.1.0"
    assert hasattr(sa, "ENTITIES")
    assert hasattr(sa, "MOTIONS")
    assert hasattr(sa, "PROJECT_PALETTES")
    assert hasattr(sa, "color_at")
    assert hasattr(sa, "frame_string")


# ---------- palette ----------

def test_palette_anchors_count_and_names():
    from sinister_ascii.palette import ANCHORS
    names = sorted(a.name for a in ANCHORS)
    assert names == ["cobalt", "crimson", "royal_indigo", "sinister_violet", "verdant"]


def test_color_at_deterministic_and_in_byte_range():
    from sinister_ascii.palette import color_at, PROJECT_PALETTES
    pal = PROJECT_PALETTES["sinister-term"]
    r1, g1, b1 = color_at(pal, 1.234, mix=0.0)
    r2, g2, b2 = color_at(pal, 1.234, mix=0.0)
    assert (r1, g1, b1) == (r2, g2, b2)
    for v in (r1, g1, b1):
        assert 0 <= v <= 255


def test_color_at_changes_with_time():
    from sinister_ascii.palette import color_at, PROJECT_PALETTES
    pal = PROJECT_PALETTES["sinister-term"]
    a = color_at(pal, 0.0, mix=0.5)
    b = color_at(pal, 5.0, mix=0.5)
    assert a != b


def test_rgb_to_ansi_truecolor_format():
    from sinister_ascii.palette import rgb_to_ansi_truecolor
    assert rgb_to_ansi_truecolor(255, 128, 0) == "\033[38;2;255;128;0m"
    assert rgb_to_ansi_truecolor(0, 0, 0, background=True) == "\033[48;2;0;0;0m"


def test_for_project_palette_fallback():
    from sinister_ascii.palette import for_project, PROJECT_PALETTES
    assert for_project("sinister-sanctum") is PROJECT_PALETTES["sinister-sanctum"]
    assert for_project("totally-unknown-key") is PROJECT_PALETTES["sinister-sanctum"]
    assert for_project(None) is PROJECT_PALETTES["sinister-sanctum"]


# ---------- motion ----------

def test_all_motion_primitives_return_valid_frames():
    from sinister_ascii.motion import MOTIONS
    assert sorted(MOTIONS.keys()) == ["breathe", "drift", "orbit", "pulse", "spiral"]
    for name, fn in MOTIONS.items():
        f = fn(2.5)
        assert -1.0 <= f.x <= 1.0, f"{name} x out of range: {f.x}"
        assert -1.0 <= f.y <= 1.0, f"{name} y out of range: {f.y}"
        assert 0.0 <= f.intensity <= 1.0, f"{name} intensity out of range: {f.intensity}"


def test_sample_unknown_motion_defaults_to_breathe():
    from sinister_ascii.motion import sample, breathe
    s = sample("nonexistent", 1.0)
    b = breathe(1.0)
    assert s.x == b.x
    assert s.y == b.y
    assert s.intensity == b.intensity


def test_drift_uses_irrational_periods_no_visible_loop():
    """Drift must not repeat within 60s (anti-loop guarantee)."""
    from sinister_ascii.motion import drift
    samples = [drift(t) for t in range(0, 60, 1)]
    seen = set()
    for f in samples:
        key = (round(f.x, 6), round(f.y, 6))
        assert key not in seen, f"drift looped at {key}"
        seen.add(key)


# ---------- entities ----------

def test_entity_registry_has_at_least_12():
    from sinister_ascii.entities import ENTITIES
    assert len(ENTITIES) >= 12


def test_entity_for_project_known_keys():
    from sinister_ascii.entities import for_project
    for key in (
        "sinister-sanctum",
        "sinister-term",
        "sinister-forge",
        "sinister-mind",
        "sinister-overseer",
        "sinister-chatbot",
    ):
        e = for_project(key)
        assert e.project_key == key
        assert e.name
        assert e.motion_kind in ("orbit", "pulse", "drift", "spiral", "breathe")


def test_entity_for_project_fallback_to_sanctum():
    from sinister_ascii.entities import for_project
    e = for_project("totally-not-a-project")
    assert e.project_key == "sinister-sanctum"
    assert e.name == "EVE-prime"


def test_entity_frame_intensity_bounded():
    from sinister_ascii.entities import for_project
    e = for_project("sinister-term")
    for t in (0.0, 0.5, 1.7, 5.3, 12.1):
        for sig in (0.0, 0.5, 1.0):
            f = e.frame(t, activity_signal=sig)
            assert 0.0 <= f.intensity <= 1.0


def test_entity_glyph_picker_intensity_to_glyph_monotonic():
    from sinister_ascii.entities import for_project
    e = for_project("sinister-term")
    g0 = e.pick_glyph(0.0)
    g1 = e.pick_glyph(1.0)
    assert g0 != g1
    assert g0 in e.glyphs
    assert g1 in e.glyphs


# ---------- renderer ----------

def test_frame_string_returns_non_empty_ansi():
    from sinister_ascii.entities import for_project
    from sinister_ascii.renderer import frame_string, Viewport
    e = for_project("sinister-term")
    vp = Viewport(cols=80, rows=24)
    out = frame_string(e, 1.5, activity_signal=0.3, viewport=vp)
    assert isinstance(out, str)
    assert len(out) > 0
    assert "\033[38;2;" in out
    assert "\033[H" in out
    assert "\033[0m" in out


def test_viewport_from_terminal_returns_sane_bounds():
    from sinister_ascii.renderer import Viewport
    vp = Viewport.from_terminal(default_cols=80, default_rows=24)
    assert vp.cols >= 20
    assert vp.rows >= 8


# ---------- loop config ----------

def test_loop_config_defaults():
    from sinister_ascii.render_loop import LoopConfig
    cfg = LoopConfig()
    assert cfg.target_fps == 60
    assert cfg.max_seconds is None
    assert cfg.activity_signal == 0.0
    assert cfg.use_alt_screen is True
