# Sinister Sanctum :: sinister-login :: smoke tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Pytest-free smoke tests (stdlib unittest only). Run via:
    python -m unittest discover -s tools/sinister-login/tests -v
"""
import os
import tempfile
import unittest
from pathlib import Path

import sys
HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sinister_login import (
    PROVIDERS,
    get_provider,
    provider_status,
    status_all,
    resolve_active,
    doctor,
    print_env_for,
    add_to_envfile,
)


class TestProviderRegistry(unittest.TestCase):
    def test_eleven_providers(self):
        self.assertEqual(len(PROVIDERS), 11)

    def test_all_have_required_fields(self):
        for p in PROVIDERS:
            self.assertTrue(p.slug)
            self.assertTrue(p.display)
            self.assertIn(p.auth, ("apikey", "oauth", "local"))

    def test_get_provider_known(self):
        p = get_provider("claude")
        self.assertIsNotNone(p)
        self.assertEqual(p.slug, "claude")
        self.assertIn("ANTHROPIC_API_KEY", p.key_envs)

    def test_get_provider_unknown(self):
        self.assertIsNone(get_provider("nonsense"))

    def test_local_providers_marked_local(self):
        for slug in ("lmstudio", "ollama"):
            p = get_provider(slug)
            self.assertIsNotNone(p)
            self.assertEqual(p.auth, "local")
            self.assertEqual(p.key_envs, ())


class TestProviderStatus(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in (
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
            "SINISTER_LOGIN_PREFERENCE",
        )}
        for k in self._saved:
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_no_env_marks_apikey_unconfigured(self):
        p = get_provider("claude")
        s = provider_status(p)
        self.assertFalse(s["key_present"])
        self.assertFalse(s["configured"])
        self.assertIn("ANTHROPIC_API_KEY", s["missing_envs"])

    def test_env_set_marks_configured(self):
        os.environ["ANTHROPIC_API_KEY"] = "sk-test-fake-key"
        p = get_provider("claude")
        s = provider_status(p)
        self.assertTrue(s["key_present"])
        self.assertTrue(s["configured"])
        self.assertEqual(s["key_env_found"], "ANTHROPIC_API_KEY")

    def test_status_all_returns_eleven_rows(self):
        rows = status_all()
        self.assertEqual(len(rows), 11)

    def test_local_provider_always_configured(self):
        p = get_provider("ollama")
        s = provider_status(p)
        self.assertTrue(s["configured"])


class TestResolveActive(unittest.TestCase):
    def setUp(self):
        self._saved_keys = {k: os.environ.pop(k, None) for k in (
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
            "FIREWORKS_API_KEY", "SINISTER_LOGIN_PREFERENCE",
        )}

    def tearDown(self):
        for k, v in self._saved_keys.items():
            if v is not None:
                os.environ[k] = v

    def test_resolve_falls_back_to_local(self):
        # No apikey envs set; preference still ends with locals.
        s = resolve_active()
        self.assertIsNotNone(s)
        self.assertIn(s["slug"], ("lmstudio", "ollama"))

    def test_resolve_picks_claude_first_when_key_present(self):
        os.environ["ANTHROPIC_API_KEY"] = "sk-test"
        s = resolve_active()
        self.assertIsNotNone(s)
        self.assertEqual(s["slug"], "claude")

    def test_preference_override(self):
        os.environ["SINISTER_LOGIN_PREFERENCE"] = "openai,claude"
        os.environ["OPENAI_API_KEY"] = "sk-test-openai"
        os.environ["ANTHROPIC_API_KEY"] = "sk-test-claude"
        s = resolve_active()
        self.assertEqual(s["slug"], "openai")


class TestDoctor(unittest.TestCase):
    def setUp(self):
        for k in ("ANTHROPIC_API_KEY",):
            os.environ.pop(k, None)

    def test_doctor_unknown_provider(self):
        r = doctor("doesnotexist")
        self.assertFalse(r["ok"])
        self.assertIn("unknown", r["error"])

    def test_doctor_env_only(self):
        r = doctor("claude", probe=False)
        self.assertFalse(r["probed"])
        self.assertIsNone(r["reachable"])

    def test_doctor_local_always_ok(self):
        r = doctor("ollama", probe=False)
        self.assertTrue(r["configured"])


class TestPrintEnv(unittest.TestCase):
    def test_print_env_lines_for_known(self):
        lines = print_env_for("claude")
        self.assertTrue(any("ANTHROPIC_API_KEY" in ln for ln in lines))

    def test_print_env_empty_for_unknown(self):
        self.assertEqual(print_env_for("nonsense"), [])

    def test_print_env_local_provider(self):
        lines = print_env_for("ollama")
        self.assertTrue(any("local" in ln.lower() or "11434" in ln for ln in lines))


class TestAddToEnvfile(unittest.TestCase):
    def test_refuses_plaintext_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            r = add_to_envfile("claude", "sk-fake", envfile_path=Path(td) / "x.env")
            self.assertFalse(r["ok"])
            self.assertIn("plaintext", r["error"])
            self.assertFalse((Path(td) / "x.env").exists())

    def test_writes_when_opted_in(self):
        with tempfile.TemporaryDirectory() as td:
            ef = Path(td) / "login.env"
            r = add_to_envfile("claude", "sk-test-1", envfile_path=ef, allow_plaintext=True)
            self.assertTrue(r["ok"])
            self.assertTrue(ef.exists())
            txt = ef.read_text(encoding="utf-8")
            self.assertIn("ANTHROPIC_API_KEY=sk-test-1", txt)

    def test_local_provider_refuses_add(self):
        with tempfile.TemporaryDirectory() as td:
            r = add_to_envfile("ollama", "x", envfile_path=Path(td) / "x.env", allow_plaintext=True)
            self.assertFalse(r["ok"])
            self.assertIn("local-only", r["error"])


if __name__ == "__main__":
    unittest.main()
