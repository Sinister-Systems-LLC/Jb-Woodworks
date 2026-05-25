"""python -m sinister_generator.sorter_web entry point."""
# Author: RKOJ-ELENO :: 2026-05-24

from __future__ import annotations

import argparse
import pathlib
import sys

from .server import run_server


def main() -> int:
    parser = argparse.ArgumentParser(prog="sinister_generator.sorter_web")
    parser.add_argument("--folder", required=True, help="image folder to sort (drag-drop root)")
    parser.add_argument("--port", type=int, default=7099, help="local port to serve on")
    args = parser.parse_args()
    folder = pathlib.Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        sys.stderr.write(f"folder not found: {folder}\n")
        return 2
    return run_server(folder, args.port)


if __name__ == "__main__":
    sys.exit(main())
