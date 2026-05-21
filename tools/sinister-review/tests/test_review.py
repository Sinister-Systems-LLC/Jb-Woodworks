# Sinister Sanctum :: sinister-review :: smoke tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Smoke tests for sinister-review v0.1.0. Exercises the disk-first path
without ever calling a real LLM (dispatch_llm is intentionally a stub).
"""

from __future__ import annotations
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sinister_review import (
    SCHEMA_VERSION,
    judge,
    recent_reviews,
    review_diff,
    review_transcript,
    set_reviews_root,
)


class ReviewSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sinister-review-smoke-")
        set_reviews_root(self.tmp)
        os.environ["SINISTER_AGENT_SLUG"] = "smoke-test"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("SINISTER_AGENT_SLUG", None)

    def test_schema_constant(self):
        self.assertEqual(SCHEMA_VERSION, "sinister.review.v1")

    def test_review_diff_stub_persists(self):
        rec = review_diff("diff --git a/x b/x\n+hello\n", focus="lane-discipline")
        self.assertEqual(rec["schema_version"], "sinister.review.v1")
        self.assertEqual(rec["kind"], "diff")
        self.assertTrue(rec["stub"])
        self.assertEqual(rec["from"], "smoke-test")
        self.assertEqual(rec["verdict"]["rating"], "stub")
        self.assertTrue(Path(rec["_path"]).exists())

    def test_review_transcript_missing_path(self):
        rec = review_transcript("/nonexistent/path.jsonl")
        self.assertTrue(rec["stub"])
        self.assertIn("not found", rec["verdict"]["concerns"][0])

    def test_judge_stub_persists(self):
        rec = judge("is the sky blue?", context="trivial")
        self.assertEqual(rec["kind"], "judgment")
        self.assertTrue(rec["stub"])
        self.assertEqual(rec["verdict"]["rating"], "stub")

    def test_recent_reviews_round_trip(self):
        review_diff("a", focus="x")
        review_diff("b", focus="y")
        judge("q", context="c")
        out = recent_reviews(limit=10)
        self.assertEqual(len(out), 3)
        self.assertTrue(all(r["from"] == "smoke-test" for r in out))
        self.assertTrue(all(r["stub"] for r in out))

    def test_recent_reviews_namespace_filter(self):
        review_diff("a")
        os.environ["SINISTER_AGENT_SLUG"] = "other-slug"
        review_diff("b")
        os.environ["SINISTER_AGENT_SLUG"] = "smoke-test"
        smoke = recent_reviews(limit=10, namespace="smoke-test")
        other = recent_reviews(limit=10, namespace="other-slug")
        self.assertEqual(len(smoke), 1)
        self.assertEqual(len(other), 1)

    def test_persisted_json_is_valid(self):
        rec = review_diff("x", focus="schema")
        loaded = json.loads(Path(rec["_path"]).read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema_version"], "sinister.review.v1")
        self.assertEqual(loaded["kind"], "diff")


if __name__ == "__main__":
    unittest.main()
