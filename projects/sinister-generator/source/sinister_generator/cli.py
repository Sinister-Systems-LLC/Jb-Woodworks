"""sinister-generator CLI — brand-locked image gen with anti-slop audit."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from nano_banana import api as _nb

from .brands import BRAND_REGISTRY
from .audit import append_cost_row, structural_check

_BRAND_TO_PROJECT = {
    "jkor": "jkor",
    "smpl": "showmasters",
    "showmasters": "showmasters",
    "jbw": "jb-woodworks",
    "jb-woodworks": "jb-woodworks",
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="sinister-generator",
        description="Fleet-wide image generation. Brand-locked + audit-gated.",
    )
    p.add_argument("--prompt", required=True, help="The image prompt.")
    p.add_argument("--output", required=True, help="Where to write the image.")
    p.add_argument(
        "--ref",
        action="append",
        default=[],
        help="Path to a reference image (repeatable).",
    )
    p.add_argument(
        "--brand",
        choices=["none", *sorted(BRAND_REGISTRY.keys())],
        default="none",
        help="Brand-lock helper to use.",
    )
    p.add_argument(
        "--project",
        default=None,
        help="Project slug for cost-ledger row. Defaults to brand mapping when --brand is set.",
    )
    p.add_argument("--model", default=_nb.DEFAULT_MODEL, help="Override the model id.")
    p.add_argument(
        "--no-meta",
        action="store_true",
        help="Skip writing the .meta.json sidecar.",
    )
    p.add_argument(
        "--no-audit",
        action="store_true",
        help="Skip the post-generation structural check + cost-ledger append.",
    )
    args = p.parse_args(argv)

    refs = args.ref or None
    if args.brand == "none":
        result = _nb.generate(
            args.prompt,
            args.output,
            ref_images=refs,
            model=args.model,
            write_meta=not args.no_meta,
        )
    else:
        helper = BRAND_REGISTRY[args.brand]
        result = helper(args.prompt, args.output, ref_images=refs)

    payload: dict = {
        "status": result.status,
        "output_path": result.output_path,
        "meta_path": result.meta_path,
        "model": result.model,
        "elapsed_seconds": result.elapsed_seconds,
        "image_bytes": result.image_bytes,
        "error": result.error,
        "text_excerpt": result.text_excerpt,
    }

    if result.status == "ok" and not args.no_audit:
        project = args.project or _BRAND_TO_PROJECT.get(args.brand, "ad-hoc")
        ledger = append_cost_row(
            output_path=result.output_path,
            model=result.model,
            image_bytes=result.image_bytes,
            project=project,
            prompt_excerpt=args.prompt,
            verdict="pending",
        )
        report = structural_check(result.output_path)
        payload["audit"] = {
            "cost_ledger": str(ledger),
            "structural": asdict(report),
            "structural_passes": report.passes,
        }

    print(json.dumps(payload, indent=2))
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
