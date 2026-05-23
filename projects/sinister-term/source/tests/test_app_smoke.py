# Sinister Term :: test_app_smoke.py
# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later
# RKOJ-ELENO :: 2026-05-23 :: trivial import smoke — catches ImportError regressions fast


def test_imports():
    from term import app, commands, completer, keybindings, theme  # noqa: F401
