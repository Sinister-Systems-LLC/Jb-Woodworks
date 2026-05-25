"""Per-project brand-lock helpers. Each module owns its style suffix + BRAND.md path."""
# Author: RKOJ-ELENO :: 2026-05-23 (jkor->JOKR display rename 2026-05-24)

from .jkor import JKOR_STYLE, JOKR_STYLE, jkor_image, jokr_image
from .showmasters import SMPL_STYLE, smpl_image
from .jb_woodworks import JBW_STYLE, jbw_image

__all__ = [
    "JOKR_STYLE",
    "JKOR_STYLE",
    "jokr_image",
    "jkor_image",
    "SMPL_STYLE",
    "smpl_image",
    "JBW_STYLE",
    "jbw_image",
    "BRAND_REGISTRY",
]

BRAND_REGISTRY = {
    "jkor": jokr_image,
    "jokr": jokr_image,
    "showmasters": smpl_image,
    "smpl": smpl_image,
    "jb-woodworks": jbw_image,
    "jbw": jbw_image,
}
