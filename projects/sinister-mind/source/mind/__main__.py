# Sinister Mind :: __main__.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# `python -m mind` -> Flask on http://127.0.0.1:5079/. Auto-opens browser.

import sys
import threading
import time
import webbrowser


def run() -> int:
    try:
        from mind.server import app
    except ImportError as e:
        print(f"[mind] Flask not installed: {e}", file=sys.stderr)
        print("[mind] Install with: pip install -e .", file=sys.stderr)
        return 1

    host = "127.0.0.1"
    port = 5079

    def _open_browser_after_start():
        time.sleep(1.5)
        try:
            webbrowser.open(f"http://{host}:{port}/")
        except Exception:
            pass

    threading.Thread(target=_open_browser_after_start, daemon=True).start()
    print(f"[mind] Sinister Mind on http://{host}:{port}/  (Ctrl+C to stop)")
    app.run(host=host, port=port, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    sys.exit(run())
