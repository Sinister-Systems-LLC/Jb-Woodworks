"""JOKR brand-lock — purple cartoon demon-jester w/ gold crown + jester staff + cards."""
# Author: RKOJ-ELENO :: 2026-05-23 (renamed 2026-05-24 to JOKR — file stays jkor.py since brand-key slug is jkor)

from __future__ import annotations

import pathlib
from typing import Iterable, Optional, Union

from nano_banana import api as _nb

PathLike = Union[str, pathlib.Path]
RefImage = Union[bytes, str, pathlib.Path]

JOKR_STYLE = (
    " — preserve the canonical JOKR look: playful cartoon purple demon-jester"
    " character with cheeky showing-teeth grin, small horns, gold crown,"
    " jester staff topped with a mini-jester-head bell, fan of playing cards,"
    " purple-and-gold royal-jester collar with central gem. Background uses"
    " the canonical runic circle with purple-and-cyan magic glow + sparkles,"
    " just dialed back slightly so the character pops more — deep purple-navy"
    " at the corners (#1A0D3A fading to #0A0B1E). The JOKR display lettering"
    " stays where the source has it. NO download icons, NO UI buttons, NO"
    " interface chrome in any corner."
)

JKOR_STYLE = JOKR_STYLE  # back-compat alias (will be removed; use JOKR_STYLE)

BRAND_MD = pathlib.Path(
    r"D:\Sinister Sanctum\projects\sinister-generator\memory\per-project\jkor\BRAND.md"
)


def jokr_image(
    prompt: str,
    output_path: PathLike,
    ref_images: Optional[Iterable[RefImage]] = None,
) -> _nb.GenerationResult:
    return _nb.generate(prompt, output_path, ref_images=ref_images, style_suffix=JOKR_STYLE)


jkor_image = jokr_image  # back-compat alias (will be removed; use jokr_image)
