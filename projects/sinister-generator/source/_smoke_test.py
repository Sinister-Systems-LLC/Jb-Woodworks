"""Smoke test — verifies the sinister_generator package imports + introspects cleanly.

Run with:
  cd D:\Sinister Sanctum\projects\sinister-generator
  python source\_smoke_test.py
"""
# Author: RKOJ-ELENO :: 2026-05-23

import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
NANO_BANANA = pathlib.Path(r"D:\Sinister Sanctum\tools\nano-banana")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(NANO_BANANA))


def main() -> int:
    import sinister_generator as sg

    print("version:", sg.__version__)
    print("brands registry keys:", sorted(sg.BRAND_REGISTRY.keys()))
    print("jkor style len:", len(sg.JKOR_STYLE), "chars")
    print("smpl style len:", len(sg.SMPL_STYLE), "chars")
    print("jbw  style len:", len(sg.JBW_STYLE), "chars")

    existing_jpg = pathlib.Path(
        r"D:\Sinister Sanctum\projects\sinister-generator\outputs\jkor\banners\banner-wide-character.jpg"
    )
    report = sg.structural_check(existing_jpg)
    print()
    print("Structural check on existing JKOR banner:")
    print("  output_path:", report.output_path)
    print("  file_exists:", report.file_exists)
    print("  is_recognized_image:", report.is_recognized_image)
    print("  file_format:", report.file_format)
    print("  resolution:", (report.width, report.height))
    print("  min_dimension_ok:", report.min_dimension_ok)
    print("  meta_sidecar_present:", report.meta_sidecar_present)
    print("  issues:", report.issues)
    print("  passes:", report.passes)

    print()
    print("cost gemini-2.5-flash-image:", sg.cost_for_model("gemini-2.5-flash-image"))
    print("cost unknown-model         :", sg.cost_for_model("unknown-model"))

    from sinister_generator import cli  # noqa: F401

    print()
    print("CLI module loaded; main =", cli.main.__qualname__)
    print("compose left_aligned_banner =", sg.left_aligned_banner.__qualname__)
    print("\nALL CHECKS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
