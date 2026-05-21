# Author: RKOJ-ELENO :: 2026-05-21
"""Entry point: python -m sinister_rkoj_qt OR frozen PyInstaller RKOJ.exe.

Uses ABSOLUTE imports — PyInstaller wraps __main__.py outside the package
context, so `from .app import run` (relative) raises
`ImportError: attempted relative import with no known parent package`.
"""

import sys
import traceback
from pathlib import Path


def _log_crash(msg: str) -> None:
    """Write to RKOJ.crash.log next to the EXE — PyInstaller windowed build
    has sys.stderr = None so we can't print errors. Log to file instead."""
    try:
        if getattr(sys, "frozen", False):
            log_dir = Path(sys.executable).resolve().parent
        else:
            log_dir = Path(__file__).resolve().parent
        with (log_dir / "RKOJ.crash.log").open("a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    except Exception:
        pass


def main() -> int:
    try:
        # ABSOLUTE import — works both `python -m sinister_rkoj_qt` AND frozen EXE.
        from sinister_rkoj_qt.app import run
    except ImportError as exc:
        _log_crash(f"=== ImportError in __main__ ===\n{traceback.format_exc()}")
        # Try a Qt dialog (PyQt6 may still be importable even if app.py fails)
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "RKOJ :: startup error",
                f"Failed to load sinister_rkoj_qt.app:\n\n{exc}\n\n"
                f"See RKOJ.crash.log next to RKOJ.exe.",
            )
        except Exception:
            _log_crash("(Qt fallback also failed)")
        return 1
    try:
        return run(sys.argv)
    except Exception:
        _log_crash(f"=== Unhandled in run() ===\n{traceback.format_exc()}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
