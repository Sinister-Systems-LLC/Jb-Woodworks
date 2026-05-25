# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# SA-PH2 :: entities/_base.py — Entity ABC. Each per-project entity declares
# its (name, glyphs, palette, motion). Renderer iterates frames at 60 FPS.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from sinister_ascii.motion import MotionFrame, sample
from sinister_ascii.palette import Palette


# Each entity has a small set of glyphs it cycles through. The glyph picked
# for a given frame is chosen by intensity (low intensity = sparse glyphs;
# high intensity = dense glyphs). This is what makes the entity feel "more
# alive" when Claude is working hard.
DEFAULT_GLYPH_RAMP = ("·", "∘", "○", "◌", "◍", "◉", "●", "✦", "✶", "✷", "❖")


@dataclass(frozen=True)
class Entity:
    """One per-project living-being entity."""
    name: str               # operator-facing "character name" (e.g. "Glyph-keeper")
    project_key: str        # projects.json key (e.g. "sinister-term")
    motion_kind: str        # one of: orbit / pulse / drift / spiral / breathe
    palette: Palette
    glyphs: tuple[str, ...] = field(default=DEFAULT_GLYPH_RAMP)
    intensity_floor: float = 0.15
    motion_kwargs: dict = field(default_factory=dict)

    def frame(self, t_seconds: float, *, activity_signal: float = 0.0) -> MotionFrame:
        """Return one motion frame, modulated by external activity_signal in [0, 1].

        `activity_signal` represents how hard the agent is working (more tokens,
        more file edits = higher signal). It only INCREASES intensity — never
        decreases below the entity's natural floor.
        """
        base = sample(self.motion_kind, t_seconds, **self.motion_kwargs)
        # Composite intensity: own motion intensity + activity boost
        boost = max(0.0, min(1.0, activity_signal))
        composite = max(self.intensity_floor, base.intensity)
        composite = composite + (1.0 - composite) * boost
        return MotionFrame(base.x, base.y, max(0.0, min(1.0, composite)))

    def pick_glyph(self, intensity: float) -> str:
        """Choose a glyph from the ramp based on intensity in [0, 1]."""
        if not self.glyphs:
            return "·"
        idx = int(max(0.0, min(1.0, intensity)) * (len(self.glyphs) - 1) + 0.5)
        idx = max(0, min(len(self.glyphs) - 1, idx))
        return self.glyphs[idx]
