# Sinister Term :: tests/test_sinister_ascii_smoke.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Smoke test for the Sinister ASCII sub-project — imports + palette math +
# motion primitives + per-project entity registry resolve without crash.
# Lives in sinister-term/source/tests so pytest picks it up by default; the
# sub-project source dir is inserted into sys.path here.

from __future__ import annotations

import math
import sys
from pathlib import Path


def _add_ascii_source_to_path():
    """Insert the Sinister ASCII source dir on sys.path. Idempotent."""
    here = Path(__file__).resolve()
    # source/tests/ → projects/sinister-term/source → up two → sinister-term
    # then into sinister-ascii/source so `import sinister_ascii` works.
    term_root = here.parent.parent.parent
    ascii_src = term_root / "sinister-ascii" / "source"
    if str(ascii_src) not in sys.path:
        sys.path.insert(0, str(ascii_src))
    return ascii_src


def test_sinister_ascii_imports():
    _add_ascii_source_to_path()
    import sinister_ascii
    from sinister_ascii import palette, motion, entities
    assert hasattr(sinister_ascii, "__version__")
    assert sinister_ascii.__version__.startswith("0.")
    # Anchor families exist
    assert palette.CRIMSON_RED.name == "crimson"
    assert palette.COBALT_BLUE.name == "cobalt"
    assert palette.VERDANT_GREEN.name == "verdant"
    assert palette.ROYAL_INDIGO.name == "royal_indigo"
    assert palette.SINISTER_VIOLET.name == "sinister_violet"


def test_palette_color_at_returns_rgb_bytes():
    _add_ascii_source_to_path()
    from sinister_ascii import palette
    p = palette.for_project("sinister-term")
    r, g, b = palette.color_at(p, t_seconds=0.0)
    assert 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255
    # At t=0 the dominant color drives (mix=0) — sinister-term dominant is
    # SINISTER_VIOLET starting at hue 270 — expect a purple-ish tone where
    # blue > green and red is non-zero.
    assert b > g


def test_palette_hue_rotation_changes_over_time():
    _add_ascii_source_to_path()
    from sinister_ascii import palette
    p = palette.for_project("sinister-forge")
    c0 = palette.color_at(p, t_seconds=0.0)
    c1 = palette.color_at(p, t_seconds=5.0)
    # Color must move — not byte-identical across 5s
    assert c0 != c1


def test_motion_orbit_returns_valid_frame():
    _add_ascii_source_to_path()
    from sinister_ascii.motion import orbit
    f = orbit(0.0)
    assert -1.0 <= f.x <= 1.0
    assert -1.0 <= f.y <= 1.0
    assert 0.0 <= f.intensity <= 1.0


def test_motion_all_primitives_dispatch():
    _add_ascii_source_to_path()
    from sinister_ascii.motion import sample, MOTIONS
    assert set(MOTIONS.keys()) == {"orbit", "pulse", "drift", "spiral", "breathe"}
    for name in MOTIONS:
        f = sample(name, 1.234)
        assert -1.0 <= f.x <= 1.0
        assert -1.0 <= f.y <= 1.0
        assert 0.0 <= f.intensity <= 1.0


def test_motion_breathe_asymmetric():
    """Breathe should produce different intensities during inhale vs exhale."""
    _add_ascii_source_to_path()
    from sinister_ascii.motion import breathe
    # Within inhale phase (~peak)
    inhale = breathe(2.0, inhale_s=2.4, exhale_s=3.6)
    # Deep into exhale phase
    exhale = breathe(5.5, inhale_s=2.4, exhale_s=3.6)
    assert inhale.intensity != exhale.intensity


def test_entities_resolve_for_known_projects():
    _add_ascii_source_to_path()
    from sinister_ascii.entities import for_project, ENTITIES
    # 12 starter entities (per __init__)
    assert len(ENTITIES) >= 10
    # Each entity exposes the expected attributes
    e = for_project("sinister-term")
    assert e.name == "Glyph-keeper"
    assert e.project_key == "sinister-term"
    assert e.motion_kind == "pulse"


def test_entities_fall_back_to_sanctum():
    """Unknown project_key falls back to sanctum-master entity (not crash)."""
    _add_ascii_source_to_path()
    from sinister_ascii.entities import for_project
    e = for_project("not-a-real-project")
    assert e.project_key == "sinister-sanctum"
    assert e.name == "EVE-prime"


def test_entity_frame_intensity_boost_by_activity_signal():
    """High activity_signal should INCREASE intensity over the natural floor."""
    _add_ascii_source_to_path()
    from sinister_ascii.entities import for_project
    e = for_project("sinister-term")
    idle = e.frame(t_seconds=0.5, activity_signal=0.0)
    busy = e.frame(t_seconds=0.5, activity_signal=0.95)
    assert busy.intensity >= idle.intensity


def test_entity_pick_glyph_intensity_ramp():
    """Low intensity → sparse glyph; high intensity → dense glyph."""
    _add_ascii_source_to_path()
    from sinister_ascii.entities import for_project
    e = for_project("sinister-term")
    sparse = e.pick_glyph(0.0)
    dense = e.pick_glyph(1.0)
    # First glyph (sparse) should be different from last (dense)
    assert sparse != dense


def test_palette_golden_ratio_phase_spreads():
    """golden_ratio_phase should never return the same value for two consecutive ints."""
    _add_ascii_source_to_path()
    from sinister_ascii.palette import golden_ratio_phase
    a = golden_ratio_phase(0)
    b = golden_ratio_phase(1)
    c = golden_ratio_phase(2)
    assert a != b
    assert b != c
    assert a != c
    # All in [0, 1)
    for v in (a, b, c):
        assert 0.0 <= v < 1.0
