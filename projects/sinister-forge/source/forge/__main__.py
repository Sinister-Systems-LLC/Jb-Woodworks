# Sinister Forge :: __main__.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Entry point: `python -m forge` or the installed `forge` console script.
# Per PH1: launches the Textual app with the Sinister Vault Boy boot art
# + a single placeholder agent pane. Multi-agent, picker, subprocess
# spawning all land in later phases.

import sys


def run() -> int:
    """Console-script entry point. Returns process exit code."""
    try:
        from forge.app import ForgeApp
    except ImportError as e:
        print(f"[forge] Textual not installed: {e}", file=sys.stderr)
        print("[forge] Install with: pip install -e .", file=sys.stderr)
        return 1

    app = ForgeApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(run())
