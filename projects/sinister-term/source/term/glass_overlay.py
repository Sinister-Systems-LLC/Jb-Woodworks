# Sinister Term :: glass_overlay.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Minimal "liquid glass" overlay placeholder. Default-off; only invoked
# when SINISTER_TERM_GLASS=on per app.py comment. Kept as a stub so the
# import in app.py succeeds. Real implementation TODO.

from __future__ import annotations

import sys


def emit(stream=None) -> None:
    s = stream if stream is not None else sys.stdout
    try:
        if not getattr(s, "isatty", lambda: False)():
            return
        # Single line, dim — placeholder. Real glass-overlay arrives later.
        s.write("\x1b[2m◈ glass overlay (stub)\x1b[0m\n")
        s.flush()
    except Exception:
        pass
