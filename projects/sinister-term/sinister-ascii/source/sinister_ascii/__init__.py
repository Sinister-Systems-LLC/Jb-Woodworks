# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Public API for the Sinister ASCII rendering engine — the artistic ASCII
# masterpiece that fills the dead-space while Claude is working.
#
# Operator hard-canonical 2026-05-25T11:36:29Z: *"call it sinister ascii"*.
# Vision: living, color-expressive entities (one per project), endless motion,
# <2ms keystroke / 16ms frame budget. Reds/blues/greens/indigos/violets.
#
# Phase status (2026-05-25):
#   SA-PH0 scaffold              ✅
#   SA-PH1 palette (5 anchors)   ✅
#   SA-PH2 motion (5 primitives) ✅
#   SA-PH3 entity ABC + 12       ✅
#   SA-PH4 renderer + loop       ✅
#   SA-PH5 intensity sampler     queued
#   SA-PH6 sterm integration     queued
#   SA-PH7 remaining entities    queued (12/25 projects covered so far)
#   SA-PH8 perf audit            queued
#   SA-PH9 default-on ship       queued

from __future__ import annotations

__version__ = "0.1.0"  # SA-PH1+PH2+PH3+PH4 shipped

from sinister_ascii.entities import ENTITIES, Entity, for_project as entity_for_project
from sinister_ascii.motion import MOTIONS, MotionFrame, sample as sample_motion
from sinister_ascii.palette import (
    ANCHORS,
    COBALT_BLUE,
    CRIMSON_RED,
    ColorFamily,
    PROJECT_PALETTES,
    Palette,
    ROYAL_INDIGO,
    SINISTER_VIOLET,
    VERDANT_GREEN,
    color_at,
    for_project as palette_for_project,
    golden_ratio_phase,
    hsv_to_rgb_bytes,
    rgb_to_ansi_truecolor,
)
from sinister_ascii.renderer import Viewport, frame_string
from sinister_ascii.render_loop import LoopConfig, run

__all__ = [
    "__version__",
    # palette
    "ANCHORS",
    "COBALT_BLUE",
    "CRIMSON_RED",
    "ColorFamily",
    "PROJECT_PALETTES",
    "Palette",
    "ROYAL_INDIGO",
    "SINISTER_VIOLET",
    "VERDANT_GREEN",
    "color_at",
    "palette_for_project",
    "golden_ratio_phase",
    "hsv_to_rgb_bytes",
    "rgb_to_ansi_truecolor",
    # motion
    "MOTIONS",
    "MotionFrame",
    "sample_motion",
    # entities
    "ENTITIES",
    "Entity",
    "entity_for_project",
    # renderer + loop
    "Viewport",
    "frame_string",
    "LoopConfig",
    "run",
]
