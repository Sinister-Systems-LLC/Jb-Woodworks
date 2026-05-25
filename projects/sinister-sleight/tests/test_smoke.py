# Author: RKOJ-ELENO :: 2026-05-24
"""Smoke test placeholder.

P0 SCAFFOLD — only verifies the package imports + version constant exists.
Real test suite grows phase by phase per docs/06-roadmap.md.
"""

import sys
from pathlib import Path

# Allow running pytest without installing the package
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_package_imports():
    import sleight
    assert hasattr(sleight, "__version__")
    assert sleight.__version__ == "0.0.1"


def test_author_is_rkoj_eleno():
    """Per CLAUDE.md hard-canonical 2026-05-21 — every file must be RKOJ-ELENO authored."""
    import sleight
    assert sleight.__author__ == "RKOJ-ELENO"


def test_cli_main_returns_zero():
    from sleight.__main__ import main
    rc = main(["status"])
    assert rc == 0
