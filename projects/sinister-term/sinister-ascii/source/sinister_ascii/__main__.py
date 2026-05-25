# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Demo entrypoint — `python -m sinister_ascii [project_key] [--seconds N]`.
# Operator-facing one-liner to see Sinister ASCII in action.

from __future__ import annotations

import argparse
import sys

from sinister_ascii.entities import ENTITIES, for_project
from sinister_ascii.render_loop import LoopConfig, run


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="sinister_ascii",
        description="Sinister ASCII — living-being ASCII for each Sinister project.",
    )
    p.add_argument("project", nargs="?", default="sinister-term",
                   help="project key (e.g. sinister-term, sinister-sanctum, sinister-forge); "
                        "default: sinister-term")
    p.add_argument("--seconds", type=float, default=None,
                   help="auto-exit after N seconds (default: run forever, Ctrl+C to quit)")
    p.add_argument("--fps", type=int, default=60,
                   help="target frames per second (default: 60)")
    p.add_argument("--activity", type=float, default=0.0,
                   help="activity_signal 0.0-1.0 (intensity boost; default 0.0 = idle)")
    p.add_argument("--list", action="store_true",
                   help="list all known per-project entities and exit")
    p.add_argument("--inline", action="store_true",
                   help="render in current screen instead of switching to alt-screen")
    return p.parse_args()


def main() -> int:
    args = _parse()

    if args.list:
        print("Sinister ASCII — known per-project entities:")
        print()
        for key in sorted(ENTITIES.keys()):
            e = ENTITIES[key]
            print(f"  {key:<22} -> {e.name:<22} motion={e.motion_kind:<8} "
                  f"palette={e.palette.dominant.name}")
        print()
        print("Run: python -m sinister_ascii <project_key>")
        return 0

    entity = for_project(args.project)
    cfg = LoopConfig(
        target_fps=args.fps,
        max_seconds=args.seconds,
        activity_signal=max(0.0, min(1.0, args.activity)),
        use_alt_screen=not args.inline,
    )
    print(f"\033[35;1mSinister ASCII\033[0m :: entity=\033[35m{entity.name}\033[0m "
          f"  project=\033[35m{entity.project_key}\033[0m  "
          f"motion=\033[35m{entity.motion_kind}\033[0m  "
          f"fps=\033[35m{args.fps}\033[0m" +
          (f"  for {args.seconds}s" if args.seconds else "  (Ctrl+C to quit)"))
    print("\033[2m(starting in 1s...)\033[0m")
    import time
    time.sleep(1.0)
    try:
        run(entity, cfg)
    except KeyboardInterrupt:
        pass
    print("\033[35;1m> sinister ascii out\033[0m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
