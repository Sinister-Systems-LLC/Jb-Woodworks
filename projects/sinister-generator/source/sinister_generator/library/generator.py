"""High-level generation API — auto-loads endorsed refs + anti-patterns + lands
the result in the brand's desktop library.

Every fleet agent should call this instead of calling nano_banana directly:

    from sinister_generator.library import generate
    result = generate(brand="jkor", prompt="...", kind="pfp")

The generated PNG lands in the desktop library root (e.g. JOKR/) with a
.meta.json sidecar. Operator moves it to ✅ Yes/ or ❌ No/. Next call
auto-honors that feedback.
"""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import pathlib
import sys
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Union

# Make sure nano_banana is importable when called from fleet agents.
_NANO_BANANA = pathlib.Path(r"D:\Sinister Sanctum\tools\nano-banana")
if str(_NANO_BANANA) not in sys.path:
    sys.path.insert(0, str(_NANO_BANANA))

from nano_banana import api as _nb  # noqa: E402

from .registry import get_brand  # noqa: E402
from .feedback import get_anti_patterns, get_endorsed_refs, refresh_feedback  # noqa: E402

PathLike = Union[str, pathlib.Path]
RefImage = Union[bytes, str, pathlib.Path]


@dataclass
class LibraryResult:
    status: str
    output_path: Optional[str] = None
    meta_path: Optional[str] = None
    desktop_path: Optional[str] = None  # where the operator will see it
    elapsed_seconds: float = 0.0
    image_bytes: int = 0
    refs_used: int = 0
    error: Optional[str] = None


def generate(
    brand: str,
    prompt: str,
    kind: Optional[str] = None,
    extra_refs: Optional[Iterable[RefImage]] = None,
    model: str = _nb.DEFAULT_MODEL,
    refresh_first: bool = True,
) -> LibraryResult:
    """Generate an image for `brand`, honoring all operator feedback to date.

    Steps:
      1. (optional) refresh feedback — scan ✅ Yes / ❌ No / 📥 Refs
      2. Build the ref list: 📥 Refs first, then ✅ Yes, then `extra_refs`
      3. Inject anti-patterns (from ❌ No notes) into the prompt
      4. Generate via nano_banana (text-free by default; no JOKR_STYLE override)
      5. Land output in <brand_desktop>/<UTC>-<kind>-<short-prompt>.png
      6. Operator can drag-drop into ✅ Yes / ❌ No to update the learning loop
    """
    started = time.time()
    cfg = get_brand(brand)

    if refresh_first:
        refresh_feedback(brand)

    endorsed_refs = get_endorsed_refs(brand)
    anti_patterns = get_anti_patterns(brand)

    all_refs: List[RefImage] = list(endorsed_refs)
    if extra_refs:
        all_refs.extend(extra_refs)

    full_prompt = prompt
    if anti_patterns:
        full_prompt = f"{prompt}\n\n{anti_patterns}"

    # Ensure the 3-tier folder structure exists (idempotent).
    cfg.great_dir.mkdir(parents=True, exist_ok=True)
    cfg.good_dir.mkdir(parents=True, exist_ok=True)
    cfg.bad_dir.mkdir(parents=True, exist_ok=True)
    cfg.refs_dir.mkdir(parents=True, exist_ok=True)

    # Land output directly in the desktop library root so operator sees it.
    utc = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    kind_part = f"-{kind}" if kind else ""
    short_prompt = _slug_from_prompt(prompt)
    filename = f"{utc}{kind_part}-{short_prompt}.png"
    desktop_output = cfg.desktop_dir / filename
    desktop_output.parent.mkdir(parents=True, exist_ok=True)

    result = _nb.generate(
        prompt=full_prompt,
        output_path=desktop_output,
        ref_images=all_refs if all_refs else None,
        style_suffix=None,  # rely on refs + brand-md; no hard-coded suffix
        model=model,
    )

    return LibraryResult(
        status=result.status,
        output_path=str(desktop_output) if result.status == "ok" else None,
        meta_path=result.meta_path,
        desktop_path=str(cfg.desktop_dir),
        elapsed_seconds=round(time.time() - started, 2),
        image_bytes=result.image_bytes,
        refs_used=len(all_refs),
        error=result.error,
    )


def _slug_from_prompt(prompt: str, max_len: int = 40) -> str:
    """Tiny slugifier — first ~40 chars of the prompt as a filename-safe string."""
    out = []
    for ch in prompt[:max_len * 2]:
        if ch.isalnum():
            out.append(ch.lower())
        elif ch in " -_":
            out.append("-")
        if len(out) >= max_len:
            break
    s = "".join(out).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s or "gen"
