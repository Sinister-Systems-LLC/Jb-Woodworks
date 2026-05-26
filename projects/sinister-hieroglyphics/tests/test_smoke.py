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
    # Version is bumped per phase; assert it parses as SemVer-ish 0.x.y.
    v = hgly.__version__
    parts = v.split(".")
    assert len(parts) == 3, f"expected x.y.z, got {v!r}"
    assert all(p.isdigit() for p in parts), f"non-numeric segment in {v!r}"
    assert int(parts[0]) == 0, f"unexpected major in {v!r}"


if __name__ == "__main__":
    test_version()
    print("OK", hgly.__version__)
