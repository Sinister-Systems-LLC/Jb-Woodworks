"""Nano Banana - Gemini 2.5 Flash Image wrapper API."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import base64
import json
import os
import pathlib
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional, Union

DEFAULT_MODEL = "gemini-2.5-flash-image"

RefImage = Union[bytes, str, pathlib.Path]


def _resolve_key() -> str:
    for var in ("GEMINI_API_KEY", "NANO_BANANA_API_KEY", "GOOGLE_API_KEY"):
        v = os.environ.get(var)
        if v:
            return v
    raise RuntimeError(
        "No API key. Set GEMINI_API_KEY (or NANO_BANANA_API_KEY) in the user env."
    )


def _import_sdk():
    try:
        from google import genai
        from google.genai import types as genai_types
        return genai, genai_types
    except ImportError as e:
        raise ImportError(
            "google-genai not installed. Run: pip install google-genai"
        ) from e


@dataclass
class GenerationResult:
    status: str
    output_path: Optional[str] = None
    meta_path: Optional[str] = None
    model: str = DEFAULT_MODEL
    prompt: str = ""
    elapsed_seconds: float = 0.0
    error: Optional[str] = None
    image_bytes: int = 0
    text_excerpt: Optional[str] = None
    raw: dict = field(default_factory=dict)


def _normalize_refs(refs: Optional[Iterable[RefImage]], genai_types) -> list:
    if not refs:
        return []
    out = []
    for r in refs:
        if isinstance(r, (str, pathlib.Path)):
            path = pathlib.Path(r)
            data = path.read_bytes()
            mime = "image/png"
            ext = path.suffix.lower()
            if ext in (".jpg", ".jpeg"):
                mime = "image/jpeg"
            elif ext == ".webp":
                mime = "image/webp"
            out.append(genai_types.Part.from_bytes(data=data, mime_type=mime))
        elif isinstance(r, bytes):
            out.append(genai_types.Part.from_bytes(data=r, mime_type="image/png"))
    return out


def generate(
    prompt: str,
    output_path: Union[str, pathlib.Path],
    ref_images: Optional[Iterable[RefImage]] = None,
    style_suffix: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    write_meta: bool = True,
) -> GenerationResult:
    started = time.time()
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    full_prompt = prompt + (style_suffix or "")

    try:
        genai, genai_types = _import_sdk()
        client = genai.Client(api_key=_resolve_key())
    except Exception as e:
        return GenerationResult(
            status="error",
            model=model,
            prompt=full_prompt,
            error=str(e),
            elapsed_seconds=round(time.time() - started, 2),
        )

    parts: list = [full_prompt]
    parts.extend(_normalize_refs(ref_images, genai_types))

    try:
        response = client.models.generate_content(model=model, contents=parts)
    except Exception as e:
        return GenerationResult(
            status="error",
            model=model,
            prompt=full_prompt,
            error=str(e),
            elapsed_seconds=round(time.time() - started, 2),
        )

    img_bytes: Optional[bytes] = None
    text_chunks: list[str] = []
    for cand in (response.candidates or []):
        if not cand.content or not cand.content.parts:
            continue
        for part in cand.content.parts:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                data = inline.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                img_bytes = data
            elif getattr(part, "text", None):
                text_chunks.append(part.text)

    text_excerpt = (" | ".join(text_chunks))[:500] or None

    if not img_bytes:
        return GenerationResult(
            status="error",
            model=model,
            prompt=full_prompt,
            error=f"No image bytes returned. Text: {text_excerpt}",
            elapsed_seconds=round(time.time() - started, 2),
            text_excerpt=text_excerpt,
        )

    output_path.write_bytes(img_bytes)
    meta_path: Optional[pathlib.Path] = None
    if write_meta:
        meta_path = output_path.with_suffix(output_path.suffix + ".meta.json")
        meta = {
            "prompt": full_prompt,
            "model": model,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "elapsed_seconds": round(time.time() - started, 2),
            "ref_image_count": len(list(ref_images) if ref_images else []),
            "image_bytes": len(img_bytes),
            "text_response_excerpt": text_excerpt,
        }
        meta_path.write_text(json.dumps(meta, indent=2))

    return GenerationResult(
        status="ok",
        output_path=str(output_path),
        meta_path=str(meta_path) if meta_path else None,
        model=model,
        prompt=full_prompt,
        elapsed_seconds=round(time.time() - started, 2),
        image_bytes=len(img_bytes),
        text_excerpt=text_excerpt,
    )


SMPL_STYLE = (
    " — cinematic volumetric stage lighting, deep black background (#0A0A0F),"
    " gold gradient accent (#E8C078 -> #D4A24A -> #9C7126), high-contrast subject,"
    " no text in image, no emojis, no logos"
)

JBW_STYLE = (
    " — premium craftsmanship, hand-finished wood close-up, warm gold accent (#c9a84c)"
    " on deep black (#080808) background, soft directional light, photographic realism,"
    " no text in image, no emojis, no plastic / faux finishes"
)

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


def smpl_image(
    prompt: str,
    output_path: Union[str, pathlib.Path],
    ref_images: Optional[Iterable[RefImage]] = None,
) -> GenerationResult:
    return generate(prompt, output_path, ref_images=ref_images, style_suffix=SMPL_STYLE)


def jbw_image(
    prompt: str,
    output_path: Union[str, pathlib.Path],
    ref_images: Optional[Iterable[RefImage]] = None,
) -> GenerationResult:
    return generate(prompt, output_path, ref_images=ref_images, style_suffix=JBW_STYLE)


def jokr_image(
    prompt: str,
    output_path: Union[str, pathlib.Path],
    ref_images: Optional[Iterable[RefImage]] = None,
) -> GenerationResult:
    return generate(prompt, output_path, ref_images=ref_images, style_suffix=JOKR_STYLE)


jkor_image = jokr_image  # back-compat alias (will be removed; use jokr_image)
