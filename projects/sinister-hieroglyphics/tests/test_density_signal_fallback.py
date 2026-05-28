"""Regression test — _density_signal() graceful-fallback contract.

Pins iter-31 (multi-objective per-category density signal) edge cases so a
future refactor cannot regress the "available: False" fallback path. The
trainer relies on this fallback when:
  - the corpus dir is missing (e.g. fresh checkout)
  - the hgly_density.py sibling CLI is missing (rare — but possible during
    cross-agent working-tree races, per the iter-31 heartbeat lesson)
  - the --by-category flag has not yet landed in the on-disk density CLI

When those happen the trainer falls back to the placeholder score instead of
crashing — this test pins that contract so the fallback never silently
flips to "available: True" with a None composite.

Author: RKOJ-ELENO :: 2026-05-27
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(r"D:\Sinister Sanctum")
HGLY_TRAINER_PATH = REPO_ROOT / "automations" / "hgly_trainer.py"


def _load_trainer_module():
    spec = importlib.util.spec_from_file_location("hgly_trainer", HGLY_TRAINER_PATH)
    assert spec and spec.loader, f"cannot load spec for {HGLY_TRAINER_PATH}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hgly_trainer"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestDensitySignalFallback(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not HGLY_TRAINER_PATH.exists():
            raise unittest.SkipTest(f"hgly_trainer.py not present at {HGLY_TRAINER_PATH}")
        cls.trainer = _load_trainer_module()

    def test_missing_corpus_dir_returns_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ghost = Path(td) / "definitely-does-not-exist-corpus"
            result = self.trainer._density_signal(ghost)

        self.assertIsInstance(result, dict)
        self.assertFalse(
            result.get("available", True),
            "expected available=False when corpus dir does not exist",
        )
        self.assertIn("error", result, "fallback dict must include an error reason")
        self.assertIn("corpus", str(result["error"]).lower())

    def test_glyph_categories_constant_excludes_other(self) -> None:
        cats = self.trainer.GLYPH_CATEGORIES
        self.assertEqual(len(cats), 8, "expected exactly 8 glyph categories")
        self.assertNotIn(
            "other",
            cats,
            "'other' bucket must NOT be in GLYPH_CATEGORIES (iter-29 reframe)",
        )

    def test_density_goal_matches_claude_md_rule_one(self) -> None:
        self.assertAlmostEqual(
            self.trainer.DENSITY_GOAL,
            0.20,
            places=5,
            msg="DENSITY_GOAL must remain 0.20 per CLAUDE.md prime-directive",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
