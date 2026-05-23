"""Brand registry — what brands exist, where their desktop libraries live."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import json
import pathlib
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

PROJECT_ROOT = pathlib.Path(r"D:\Sinister Sanctum\projects\sinister-generator")
REGISTRY_PATH = PROJECT_ROOT / "memory" / "learning" / "_brands.json"
DESKTOP_ROOT = pathlib.Path(r"C:\Users\Zonia\Desktop")

# 3-tier endorsement structure (operator directive 2026-05-23 evening):
#   💎 Great → "I'd actually use this" — top tier; ref[0]/ref[1] for next gens
#   ✅ Good  → "in theme but needs work / good gen but stupid in some areas"
#               — secondary endorsement; informs the next gens but lower priority
#   ❌ Bad   → rejected; anti-patterns
#   📥 Refs  → operator-supplied canonical references (highest authority)
GREAT_SUBDIR = "💎 Great"
GOOD_SUBDIR = "✅ Good"
BAD_SUBDIR = "❌ Bad"
REFS_SUBDIR = "📥 Refs"

# Legacy aliases — older sessions used "✅ Yes" and "❌ No"; feedback.py
# scans both old and new names so existing sorted content migrates cleanly.
LEGACY_YES_SUBDIR = "✅ Yes"
LEGACY_NO_SUBDIR = "❌ No"


@dataclass
class BrandConfig:
    brand: str
    display_name: str
    desktop_name: str
    desktop_path: str
    brand_md: str
    kinds: List[str] = field(default_factory=list)
    default_kind: str = "pfp"
    style_helper: str = ""  # nano_banana function name (jkor_image / smpl_image / jbw_image)

    @property
    def desktop_dir(self) -> pathlib.Path:
        return pathlib.Path(self.desktop_path)

    @property
    def great_dir(self) -> pathlib.Path:
        return self.desktop_dir / GREAT_SUBDIR

    @property
    def good_dir(self) -> pathlib.Path:
        return self.desktop_dir / GOOD_SUBDIR

    @property
    def bad_dir(self) -> pathlib.Path:
        return self.desktop_dir / BAD_SUBDIR

    @property
    def refs_dir(self) -> pathlib.Path:
        return self.desktop_dir / REFS_SUBDIR

    # Legacy properties — kept so older code paths keep working until migrated.
    @property
    def yes_dir(self) -> pathlib.Path:
        return self.good_dir

    @property
    def no_dir(self) -> pathlib.Path:
        return self.bad_dir

    @property
    def learning_path(self) -> pathlib.Path:
        return PROJECT_ROOT / "memory" / "learning" / f"{self.brand}.json"


# Seed registry — fleet-known brands. Operator can add more via init_brand().
_SEED: Dict[str, BrandConfig] = {
    "jkor": BrandConfig(
        brand="jkor",
        display_name="JKOR",
        desktop_name="JOKR",
        desktop_path=str(DESKTOP_ROOT / "JOKR"),
        brand_md=str(PROJECT_ROOT / "memory" / "per-project" / "jkor" / "BRAND.md"),
        kinds=["pfp", "banner", "logo", "social", "cards", "thumbs", "word-marks", "cutouts"],
        default_kind="pfp",
        style_helper="jkor_image",
    ),
    "showmasters": BrandConfig(
        brand="showmasters",
        display_name="Showmasters",
        desktop_name="Showmasters",
        desktop_path=str(DESKTOP_ROOT / "Showmasters"),
        brand_md=str(PROJECT_ROOT / "memory" / "per-project" / "showmasters" / "BRAND.md"),
        kinds=["banners", "social", "blog-heroes", "service-illustrations", "city-heros"],
        default_kind="blog-heroes",
        style_helper="smpl_image",
    ),
    "jb-woodworks": BrandConfig(
        brand="jb-woodworks",
        display_name="JB Woodworks",
        desktop_name="JB Woodworks",
        desktop_path=str(DESKTOP_ROOT / "JB Woodworks"),
        brand_md=str(PROJECT_ROOT / "memory" / "per-project" / "jb-woodworks" / "BRAND.md"),
        kinds=["banners", "social", "blog-heroes", "portfolio-teasers"],
        default_kind="banners",
        style_helper="jbw_image",
    ),
}


def _load_registry() -> Dict[str, BrandConfig]:
    """Read user-added entries from the on-disk registry; merge over seed."""
    out = dict(_SEED)
    if REGISTRY_PATH.is_file():
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            for slug, cfg in data.items():
                out[slug] = BrandConfig(**cfg)
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return out


def _save_registry(registry: Dict[str, BrandConfig]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {slug: asdict(cfg) for slug, cfg in registry.items() if slug not in _SEED}
    REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


BRAND_REGISTRY: Dict[str, BrandConfig] = _load_registry()


def list_brands() -> List[BrandConfig]:
    return list(BRAND_REGISTRY.values())


def get_brand(slug: str) -> BrandConfig:
    if slug not in BRAND_REGISTRY:
        raise KeyError(f"unknown brand: {slug!r}. Known: {list(BRAND_REGISTRY.keys())}")
    return BRAND_REGISTRY[slug]


def ensure_sorter_folders(cfg: BrandConfig) -> List[pathlib.Path]:
    """Idempotently create the 4 sorter folders for a brand's desktop library.

    Returns the list of folders that were actually created (empty list when
    everything already existed). Called by `feedback.refresh_feedback` so the
    operator never sees missing drag-drop targets after a brand is seeded.
    """
    created: List[pathlib.Path] = []
    cfg.desktop_dir.mkdir(parents=True, exist_ok=True)
    for d in (cfg.great_dir, cfg.good_dir, cfg.bad_dir, cfg.refs_dir):
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created


def init_brand(
    brand: str,
    display_name: Optional[str] = None,
    desktop_name: Optional[str] = None,
    kinds: Optional[List[str]] = None,
    default_kind: str = "banner",
    style_helper: str = "",
) -> BrandConfig:
    """Register a new brand + scaffold its desktop folder structure.

    Idempotent — calling on an existing brand updates the config and re-creates
    any missing subfolders. Does NOT touch existing operator-arranged files.
    """
    desktop_name = desktop_name or (display_name or brand)
    cfg = BrandConfig(
        brand=brand,
        display_name=display_name or brand.upper(),
        desktop_name=desktop_name,
        desktop_path=str(DESKTOP_ROOT / desktop_name),
        brand_md=str(PROJECT_ROOT / "memory" / "per-project" / brand / "BRAND.md"),
        kinds=kinds or ["pfp", "banner", "logo", "social"],
        default_kind=default_kind,
        style_helper=style_helper,
    )
    cfg.desktop_dir.mkdir(parents=True, exist_ok=True)
    cfg.great_dir.mkdir(parents=True, exist_ok=True)
    cfg.good_dir.mkdir(parents=True, exist_ok=True)
    cfg.bad_dir.mkdir(parents=True, exist_ok=True)
    cfg.refs_dir.mkdir(parents=True, exist_ok=True)
    BRAND_REGISTRY[brand] = cfg
    _save_registry(BRAND_REGISTRY)
    return cfg
