# Sinister Sanctum :: sinister-model :: pytest config
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""Make the local package importable when running tests outside `pip install -e`."""
from __future__ import annotations
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

# Default to a per-test state-path so tests never touch ~/.config/sinister/model.json.
# Individual tests override via monkeypatch.setenv where they need a tmp_path.
import pytest


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Every test gets a tmp state file by default. Tests that need a
    specific path override SINISTER_MODEL_STATE_PATH inside the test."""
    state_file = tmp_path / "model.json"
    monkeypatch.setenv("SINISTER_MODEL_STATE_PATH", str(state_file))
    yield state_file
