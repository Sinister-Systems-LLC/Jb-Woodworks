"""JB Woodworks brand-lock — premium hand-finished wood + warm gold on deep black."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import pathlib
from typing import Iterable, Optional, Union

from nano_banana import api as _nb

PathLike = Union[str, pathlib.Path]
RefImage = Union[bytes, str, pathlib.Path]

JBW_STYLE = (
    " — premium craftsmanship, hand-finished wood close-up, warm gold accent (#c9a84c)"
    " on deep black (#080808) background, soft directional light, photographic realism,"
    " no text in image, no emojis, no plastic / faux finishes"
)

BRAND_MD = pathlib.Path(
    r"D:\Sinister Sanctum\projects\sinister-generator\memory\per-project\jb-woodworks\BRAND.md"
)


def jbw_image(
    prompt: str,
    output_path: PathLike,
    ref_images: Optional[Iterable[RefImage]] = None,
) -> _nb.GenerationResult:
    return _nb.generate(prompt, output_path, ref_images=ref_images, style_suffix=JBW_STYLE)
