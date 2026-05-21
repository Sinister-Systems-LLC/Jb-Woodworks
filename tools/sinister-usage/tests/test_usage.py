# Sinister Sanctum :: sinister-usage :: smoke tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Pytest-free smoke tests (stdlib unittest only).
    python -m unittest discover -s tools/sinister-usage/tests -v
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sinister_usage import (
    USAGE_ENDPOINTS,
    UsageEndpoint,
    get_endpoint,
    check,
    check_all,
    list_endpoints,
)


class TestEndpointRegistry(unittest.TestCase):
    def test_eleven_endpoints(self):
        self.assertEqual(len(USAGE_ENDPOINTS), 11)

    def test_each_endpoint_has_required_fields(self):
        for e in USAGE_ENDPOINTS:
            self.assertTrue(e.slug)
            self.assertTrue(e.display)
            self.assertIn(e.auth_method, ("bearer", "header", "console-only", "local"))

    def test_known_endpoints_are_actually_urls(self):
        for e in USAGE_ENDPOINTS:
            if e.endpoint_url is not None:
                self.assertTrue(e.endpoint_url.startswith(("http://", "https://")))

    def test_local_providers_marked_local(self):
        for slug in ("lmstudio", "ollama"):
            e = get_endpoint(slug)
            self.assertIsNotNone(e)
            self.assertEqual(e.auth_method, "local")

    def test_get_endpoint_unknown(self):
        self.assertIsNone(get_endpoint("nonsense"))


class TestCheck(unittest.TestCase):
    def test_check_unknown(self):
        r = check("nonsense")
        self.assertFalse(r["ok"])

    def test_check_known(self):
        r = check("openai")
        self.assertTrue(r["ok"])
        self.assertEqual(r["slug"], "openai")
        self.assertTrue(r["endpoint_known"])

    def test_check_all_returns_eleven_rows(self):
        rows = check_all()
        self.assertEqual(len(rows), 11)

    def test_check_endpoint_known_flag(self):
        r_claude = check("claude")
        r_openai = check("openai")
        self.assertFalse(r_claude["endpoint_known"])
        self.assertTrue(r_openai["endpoint_known"])


class TestListEndpoints(unittest.TestCase):
    def test_list_endpoints_does_not_touch_env(self):
        # list_endpoints() must NOT have a 'configured' field (no env lookup).
        rows = list_endpoints()
        self.assertEqual(len(rows), 11)
        for r in rows:
            self.assertNotIn("configured", r)

    def test_list_endpoints_shape(self):
        rows = list_endpoints()
        keys_required = {"slug", "display", "endpoint_url", "endpoint_known",
                         "auth_method", "docs_url", "notes"}
        for r in rows:
            self.assertTrue(keys_required.issubset(r.keys()))


class TestCrossToolDep(unittest.TestCase):
    def test_check_runs_without_sinister_login(self):
        # Even if sinister_login isn't importable, check() should not crash.
        r = check("openai")
        self.assertTrue(r["ok"])
        # configured is either True/False (if sinister-login installed) or None.
        self.assertIn(r["configured"], (True, False, None))


# === v0.1.0 additions: estimator + sources + CLI ===

import io
import json
import tempfile
from unittest import mock

from sinister_usage import (
    estimate_tokens,
    estimate_text_breakdown,
    scan_claude_local,
    scan_provider_registry,
    today_summary,
)
from sinister_usage.__main__ import main as cli_main


class TestEstimator(unittest.TestCase):
    def test_empty_string_is_zero(self):
        self.assertEqual(estimate_tokens(""), 0)

    def test_simple_english_nonzero(self):
        n = estimate_tokens("hello world")
        self.assertGreaterEqual(n, 2)
        self.assertLessEqual(n, 6)

    def test_words_at_least_word_count(self):
        text = "the quick brown fox jumps over the lazy dog"
        self.assertGreaterEqual(estimate_tokens(text), 9)

    def test_non_ascii_penalty(self):
        latin = estimate_tokens("a" * 40)
        cjk = estimate_tokens("中" * 40)
        self.assertGreater(cjk, latin)

    def test_breakdown_keys(self):
        bd = estimate_text_breakdown("hello\nworld")
        for k in ("chars", "words", "lines", "non_ascii", "tokens_estimate", "schema_version"):
            self.assertIn(k, bd)
        self.assertEqual(bd["lines"], 2)
        self.assertEqual(bd["words"], 2)


class TestSources(unittest.TestCase):
    def test_scan_nonexistent_dir(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "nope"
            out = scan_claude_local(fake)
            self.assertFalse(out["exists"])
            self.assertEqual(out["sessions_count"], 0)

    def test_scan_synthetic_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "settings.json").write_text("{}", encoding="utf-8")
            proj = root / "projects" / "fake-project"
            proj.mkdir(parents=True)
            (proj / "ssn1.jsonl").write_text('{"msg":"hi"}\n', encoding="utf-8")
            (proj / "ssn2.jsonl").write_text('{"msg":"there"}\n', encoding="utf-8")
            out = scan_claude_local(root)
            self.assertEqual(out["projects_count"], 1)
            self.assertEqual(out["sessions_count"], 2)
            self.assertGreater(out["total_session_bytes"], 0)
            self.assertTrue(out["settings_present"])

    def test_today_summary_schema(self):
        with tempfile.TemporaryDirectory() as td:
            out = today_summary(td)
            for k in ("as_of_utc", "claude_local", "sessions_today", "rough_tokens_today", "notes"):
                self.assertIn(k, out)

    def test_provider_registry_optional(self):
        out = scan_provider_registry()
        self.assertIsInstance(out, list)


class TestCli(unittest.TestCase):
    def _capture(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            rv = cli_main(argv)
        return rv, out.getvalue(), err.getvalue()

    def test_help_default(self):
        rv, out, _err = self._capture([])
        self.assertEqual(rv, 0)
        self.assertIn("sinister-usage", out)

    def test_list_json(self):
        rv, out, _err = self._capture(["list", "--json"])
        self.assertEqual(rv, 0)
        data = json.loads(out)
        self.assertEqual(len(data), 11)

    def test_check_known(self):
        rv, out, _err = self._capture(["check", "openai", "--json"])
        self.assertEqual(rv, 0)
        data = json.loads(out)
        self.assertTrue(data["ok"])

    def test_check_unknown_exit_2(self):
        rv, _out, err = self._capture(["check", "nonsense"])
        self.assertEqual(rv, 2)
        self.assertIn("unknown", err)

    def test_estimate_inline(self):
        rv, out, _err = self._capture(["estimate", "--text", "hello world"])
        self.assertEqual(rv, 0)
        self.assertTrue(out.strip().isdigit())

    def test_estimate_json(self):
        rv, out, _err = self._capture(["estimate", "--text", "abc", "--json"])
        self.assertEqual(rv, 0)
        data = json.loads(out)
        self.assertIn("tokens_estimate", data)

    def test_matrix_row(self):
        rv, out, _err = self._capture(["matrix"])
        self.assertEqual(rv, 0)
        self.assertIn("jcode `usage`", out)

    def test_doctor_no_state_ok(self):
        rv, out, _err = self._capture(["doctor", "--no-state-ok"])
        self.assertEqual(rv, 0)
        self.assertIn("OK", out)

    def test_local_nonexistent_dir(self):
        with tempfile.TemporaryDirectory() as td:
            fake = str(Path(td) / "nope")
            rv, out, _err = self._capture(["local", "--claude-dir", fake])
            self.assertEqual(rv, 0)
            self.assertIn("fresh install", out)

    def test_today_synthetic_dir(self):
        with tempfile.TemporaryDirectory() as td:
            rv, out, _err = self._capture(["today", "--claude-dir", td, "--json"])
            self.assertEqual(rv, 0)
            data = json.loads(out)
            self.assertIn("rough_tokens_today", data)


if __name__ == "__main__":
    unittest.main()
