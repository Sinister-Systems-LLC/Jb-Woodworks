"""Smoke test for the hgly package. Author: RKOJ-ELENO :: 2026-05-25."""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import hgly  # noqa: E402


def test_version() -> None:
    assert hgly.__version__ == "0.0.1", f"unexpected version: {hgly.__version__}"


if __name__ == "__main__":
    test_version()
    print("OK", hgly.__version__)
