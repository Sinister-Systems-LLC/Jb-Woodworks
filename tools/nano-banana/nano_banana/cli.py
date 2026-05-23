"""nano-banana CLI."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import argparse
import json
import sys

from . import api as nb_api


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="nano-banana",
        description="Generate images via Gemini 2.5 Flash Image (Nano Banana).",
    )
    p.add_argument("--prompt", required=True, help="The image prompt.")
    p.add_argument("--output", required=True, help="Where to write the PNG.")
    p.add_argument(
        "--ref",
        action="append",
        default=[],
        help="Path to a reference image (repeatable).",
    )
    p.add_argument(
        "--brand",
        choices=["none", "smpl", "jbw", "jkor"],
        default="none",
        help="Brand-lock style: smpl=Showmasters, jbw=JB Woodworks, jkor=JKOR.",
    )
    p.add_argument("--model", default=nb_api.DEFAULT_MODEL, help="Override the model id.")
    p.add_argument(
        "--no-meta",
        action="store_true",
        help="Skip writing the .meta.json sidecar.",
    )
    args = p.parse_args(argv)

    refs = args.ref or None
    if args.brand == "smpl":
        result = nb_api.smpl_image(args.prompt, args.output, ref_images=refs)
    elif args.brand == "jbw":
        result = nb_api.jbw_image(args.prompt, args.output, ref_images=refs)
    elif args.brand == "jkor":
        result = nb_api.jkor_image(args.prompt, args.output, ref_images=refs)
    else:
        result = nb_api.generate(
            args.prompt,
            args.output,
            ref_images=refs,
            model=args.model,
            write_meta=not args.no_meta,
        )

    print(
        json.dumps(
            {
                "status": result.status,
                "output_path": result.output_path,
                "meta_path": result.meta_path,
                "model": result.model,
                "elapsed_seconds": result.elapsed_seconds,
                "image_bytes": result.image_bytes,
                "error": result.error,
                "text_excerpt": result.text_excerpt,
            },
            indent=2,
        )
    )
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
