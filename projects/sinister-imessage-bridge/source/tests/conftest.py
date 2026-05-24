"""Pytest fixtures. RKOJ-ELENO :: 2026-05-24.

Inserts source/ into sys.path so tests can import package modules without
the package being pip-installed; then exposes a `canned_chatdb` fixture
that materialises the canned fixture into a per-test tmpdir.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from fixtures.make_canned_chatdb import build  # noqa: E402


@pytest.fixture
def canned_chatdb(tmp_path: Path) -> Path:
    """Build a fresh canned chat.db in tmp_path and return its Path."""
    db = tmp_path / "canned-chat.db"
    build(db)
    return db
