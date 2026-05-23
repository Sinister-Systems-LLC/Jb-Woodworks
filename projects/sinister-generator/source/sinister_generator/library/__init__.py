"""Sinister Generator — Library + feedback-loop system.

Single source of truth for fleet-wide image generation. Every brand has ONE
desktop folder (operator's review surface). The operator moves outputs into
✅ Yes / ❌ No subfolders, drops refs into 📥 Refs, and the next generation
automatically honors that feedback.

Layout per brand:

    C:\\Users\\Zonia\\Desktop\\<DESKTOP_NAME>\\
      ├── (new gens land here)                  flat folder; everything visible
      ├── ✅ Yes/                                operator endorses → next gens copy these traits
      ├── ❌ No/                                 operator rejects → next gens avoid these traits
      └── 📥 Refs/                               operator adds reference images here

Memory (project-side):

    projects/sinister-generator/memory/learning/<brand>.json
      Structured record of every endorsement / rejection / ref-add, parsed from
      the desktop folder by `feedback.refresh()`. Read by `brand.generate()` to
      auto-load endorsed refs + anti-pattern instructions on every call.

Fleet API:

    from sinister_generator.library import generate, refresh_feedback
    result = generate(brand="jkor", prompt="...", kind="pfp")
    # auto-loads endorsed refs + anti-patterns; lands in JOKR/ for operator review

    refresh_feedback("jkor")   # rescan desktop folder, update learning JSON
"""
# Author: RKOJ-ELENO :: 2026-05-23

from .registry import (
    BRAND_REGISTRY,
    BrandConfig,
    get_brand,
    init_brand,
    list_brands,
)
from .feedback import refresh_feedback, get_endorsed_refs, get_anti_patterns
from .generator import generate

__all__ = [
    "BRAND_REGISTRY",
    "BrandConfig",
    "get_brand",
    "init_brand",
    "list_brands",
    "refresh_feedback",
    "get_endorsed_refs",
    "get_anti_patterns",
    "generate",
]
