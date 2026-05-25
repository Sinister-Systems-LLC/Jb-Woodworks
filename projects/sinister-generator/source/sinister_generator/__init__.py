"""Sinister Generator — fleet-wide image generation project (application layer).

This package sits on top of `nano_banana` (the raw Gemini SDK wrapper) and adds:

  - Per-brand style locks (`brands.jokr_image`, `brands.smpl_image`, `brands.jbw_image`)
  - Local PIL compositing (`compose.left_aligned_banner`, `compose.erase_region`)
  - Anti-slop audit (`audit.append_cost_row`, `audit.structural_check`,
    `audit.move_to_rejected`)

The brand helpers are also re-exported at top level so consumers can write:

  >>> from sinister_generator import jokr_image, smpl_image, jbw_image
"""
# Author: RKOJ-ELENO :: 2026-05-23 (jkor->JOKR display rename 2026-05-24)

from .compose import (
    ComposeResult,
    erase_region,
    left_aligned_banner,
)
from .brands import (
    BRAND_REGISTRY,
    JBW_STYLE,
    JKOR_STYLE,
    JOKR_STYLE,
    SMPL_STYLE,
    jbw_image,
    jkor_image,
    jokr_image,
    smpl_image,
)
from .audit import (
    StructuralReport,
    append_cost_row,
    cost_for_model,
    move_to_rejected,
    structural_check,
)

__version__ = "0.3.0"
__all__ = [
    "ComposeResult",
    "erase_region",
    "left_aligned_banner",
    "BRAND_REGISTRY",
    "JBW_STYLE",
    "JOKR_STYLE",
    "JKOR_STYLE",
    "SMPL_STYLE",
    "jbw_image",
    "jokr_image",
    "jkor_image",
    "smpl_image",
    "StructuralReport",
    "append_cost_row",
    "cost_for_model",
    "move_to_rejected",
    "structural_check",
]
