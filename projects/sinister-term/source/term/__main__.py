# Sinister Term :: entry-point (python -m term)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

import sys


def _is_demo_invocation(argv: list[str]) -> bool:
    return any(a in ("--demo", "demo") for a in argv[1:])


def _is_version(argv: list[str]) -> bool:
    return any(a in ("--version", "-V") for a in argv[1:])


def _demo() -> int:
    """Operator-facing live preview: 'see it in action' (utterance 2026-05-25T11:49Z).

    Boots the sinister-ascii sub-project for the current/configured project for
    a short duration, then exits cleanly. Picks --seconds 15 + --activity 0.6
    + --inline so the operator's scrollback is preserved.
    """
    import os
    from pathlib import Path

    here = Path(__file__).resolve()
    # source/term/__main__.py -> source/ -> sinister-term/ -> sinister-ascii/source
    ascii_src = here.parent.parent.parent / "sinister-ascii" / "source"
    if ascii_src.exists() and str(ascii_src) not in sys.path:
        sys.path.insert(0, str(ascii_src))

    project = os.environ.get("SINISTER_DEMO_PROJECT", "sinister-term")
    seconds = float(os.environ.get("SINISTER_DEMO_SECONDS", "15"))

    try:
        from sinister_ascii.entities import for_project
        from sinister_ascii.render_loop import LoopConfig, run as ascii_run
    except Exception as e:
        print(f"sinister-ascii not importable: {e}")
        print(f"  expected at: {ascii_src}")
        return 1

    entity = for_project(project)
    cfg = LoopConfig(
        target_fps=60,
        max_seconds=seconds,
        activity_signal=0.6,
        use_alt_screen=True,
    )
    print(f"\033[35;1mSinister ASCII demo\033[0m :: entity=\033[35m{entity.name}\033[0m "
          f"  project=\033[35m{entity.project_key}\033[0m  "
          f"motion=\033[35m{entity.motion_kind}\033[0m  "
          f"for \033[35m{seconds}s\033[0m  (Ctrl+C to quit early)")
    print("\033[2m(starting in 1s — switching to alt screen)\033[0m")
    import time
    time.sleep(1.0)
    try:
        ascii_run(entity, cfg)
    except KeyboardInterrupt:
        pass
    print("\033[35;1m> sinister-term demo out\033[0m")
    return 0


if __name__ == "__main__":
    if _is_demo_invocation(sys.argv):
        sys.exit(_demo())
    if _is_version(sys.argv):
        try:
            from term import __version__
        except Exception:
            __version__ = "0.0.0"
        print(f"sinister-term {__version__}")
        sys.exit(0)
    from term.app import run
    run()
