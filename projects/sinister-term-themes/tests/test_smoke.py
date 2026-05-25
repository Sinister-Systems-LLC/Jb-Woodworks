# Author: RKOJ-ELENO :: 2026-05-25
"""Ancestral Remotion smoke tests.

P0 — verifies the package skeleton functions:
1. Entity registry loads (sanctum at minimum).
2. Palette table loads (violet-core at minimum).
3. Engine renders a frame without crashing.
"""

import io
import sys
from pathlib import Path

# Allow running pytest without installing the package
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_entity_registry_loads_sanctum():
    from sinister_term_themes import entities
    keys = entities.list_keys()
    assert "sanctum" in keys, f"sanctum not in registry: {keys}"
    defn = entities.load("sanctum")
    assert defn["project_key"] == "sanctum"
    assert defn["name"] == "The Seed"
    assert isinstance(defn["glyph"], list)
    assert len(defn["glyph"]) >= 6, "sanctum glyph should be at least 6 lines"


def test_palette_table_loads_violet_core():
    from sinister_term_themes import palettes
    pal = palettes.get_palette("violet-core")
    assert "primary" in pal
    assert "secondary" in pal
    assert "tertiary" in pal
    assert "highlight" in pal
    # 5th role is dim OR danger depending on idle/hot
    assert ("dim" in pal) or ("danger" in pal)
    # Each role is a (hex, ansi_256) tuple
    hex6, ansi_256 = pal["primary"]
    assert len(hex6) == 6
    assert isinstance(ansi_256, int)


def test_engine_renders_a_frame_without_crashing():
    from sinister_term_themes import engine, entities
    defn = entities.load("sanctum")
    frame_str = engine.render_frame(defn, frame=0, energy=0.5, width=60)
    assert isinstance(frame_str, str)
    assert len(frame_str) > 0
    # Frame should contain the title fragment
    assert "ANCESTRAL REMOTION" in frame_str or "The Seed" in frame_str


def test_demo_render_exit_zero():
    from sinister_term_themes import engine
    buf = io.StringIO()
    rc = engine.demo_render(project_key="sanctum", frames=3, out=buf)
    assert rc == 0
    output = buf.getvalue()
    assert "frame 1/3" in output
    assert "frame 3/3" in output


def test_cli_list_runs():
    from sinister_term_themes.cli import main
    rc = main(["list"])
    assert rc == 0


def test_cli_version_runs():
    from sinister_term_themes.cli import main
    rc = main(["--version"])
    assert rc == 0
