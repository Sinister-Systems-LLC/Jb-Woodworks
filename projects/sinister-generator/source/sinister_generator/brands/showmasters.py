"""Showmasters (SMPL) brand-lock — cinematic stage lighting + gold-on-black."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import pathlib
from typing import Iterable, Optional, Union

from nano_banana import api as _nb

PathLike = Union[str, pathlib.Path]
RefImage = Union[bytes, str, pathlib.Path]

SMPL_STYLE = (
    " — cinematic volumetric stage lighting, deep black background (#0A0A0F),"
    " gold gradient accent (#E8C078 -> #D4A24A -> #9C7126), high-contrast subject,"
    " no text in image, no emojis, no logos"
)

BRAND_MD = pathlib.Path(
    r"D:\Sinister Sanctum\projects\sinister-generator\memory\per-project\showmasters\BRAND.md"
)


def smpl_image(
    prompt: str,
    output_path: PathLike,
    ref_images: Optional[Iterable[RefImage]] = None,
) -> _nb.GenerationResult:
    return _nb.generate(prompt, output_path, ref_images=ref_images, style_suffix=SMPL_STYLE)
