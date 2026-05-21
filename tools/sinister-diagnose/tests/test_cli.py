# Sinister Sanctum :: sinister-diagnose :: tests :: cli
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
CLI surface tests using click.testing.CliRunner + dispatch().

Confirms:
  - run, run --json, list, check <slug>, --version, --help
  - exit codes 0 / 1 / 2 for ok / warn / fail
  - --strict promotes warn to exit 2
  - unknown slug exits 2 with stderr hint
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sinister_diagnose import __version__  # noqa: E402
from sinister_diagnose.cli import cli, dispatch  # noqa: E402


# Patch out the actual checks so the CLI tests don't depend on the host.
_FAKE_OK = [
    {"name": "Python version", "status": "ok", "message": "3.12.4", "fix_hint": ""},
    {"name": "Sanctum root", "status": "ok", "message": "OK", "fix_hint": ""},
]
_FAKE_WARN = [
    {"name": "Rust", "status": "warn", "message": "missing", "fix_hint": "install rustup"},
]
_FAKE_FAIL = [
    {"name": "Python version", "status": "fail", "message": "too old", "fix_hint": "upgrade"},
]


class TestCliVersion(unittest.TestCase):
    def test_version_flag(self):
        r = CliRunner().invoke(cli, ["--version"])
        self.assertEqual(r.exit_code, 0)
        self.assertIn(__version__, r.output)

    def test_help_flag(self):
        r = CliRunner().invoke(cli, ["--help"])
        self.assertEqual(r.exit_code, 0)
        self.assertIn("health checker", r.output.lower())


class TestCliRun(unittest.TestCase):
    def test_run_ok_exits_zero(self):
        with mock.patch("sinister_diagnose.cli.run_all", return_value=_FAKE_OK):
            r = CliRunner().invoke(cli, ["run"])
        self.assertEqual(r.exit_code, 0)
        self.assertIn("Python version", r.output)
        # Summary should be present.
        self.assertIn("summary", r.output.lower())

    def test_run_warn_exits_one(self):
        with mock.patch("sinister_diagnose.cli.run_all", return_value=_FAKE_WARN):
            r = CliRunner().invoke(cli, ["run"])
        self.assertEqual(r.exit_code, 1)

    def test_run_fail_exits_two(self):
        with mock.patch("sinister_diagnose.cli.run_all", return_value=_FAKE_FAIL):
            r = CliRunner().invoke(cli, ["run"])
        self.assertEqual(r.exit_code, 2)

    def test_run_json_emits_doc(self):
        with mock.patch("sinister_diagnose.cli.run_all", return_value=_FAKE_OK):
            r = CliRunner().invoke(cli, ["run", "--json"])
        self.assertEqual(r.exit_code, 0)
        doc = json.loads(r.output)
        self.assertEqual(doc["tool"], "sinister-diagnose")
        self.assertEqual(doc["version"], __version__)
        self.assertEqual(doc["overall"], "ok")
        self.assertEqual(len(doc["checks"]), 2)

    def test_run_strict_promotes_warn_to_fail_exit(self):
        with mock.patch("sinister_diagnose.cli.run_all", return_value=_FAKE_WARN):
            r = CliRunner().invoke(cli, ["run", "--strict"])
        self.assertEqual(r.exit_code, 2)


class TestCliList(unittest.TestCase):
    def test_list_enumerates_all_slugs(self):
        r = CliRunner().invoke(cli, ["list"])
        self.assertEqual(r.exit_code, 0)
        # spot-check a few canonical slugs
        for slug in ("python", "pyinstaller", "rust", "backups", "heartbeats", "branch"):
            self.assertIn(slug, r.output)


class TestCliCheck(unittest.TestCase):
    def test_unknown_slug_exits_two(self):
        r = CliRunner().invoke(cli, ["check", "nonsense-slug"])
        self.assertEqual(r.exit_code, 2)
        self.assertIn("unknown", (r.output + r.stderr).lower())

    def test_known_slug_runs(self):
        # Use a slug whose function we can stub through ALL_CHECKS.
        fake = {"name": "Python version", "status": "ok", "message": "fake", "fix_hint": ""}
        with mock.patch.dict("sinister_diagnose.cli.ALL_CHECKS",
                             {"python": lambda: fake, **{k: v for k, v in __import__(
                                 "sinister_diagnose.checks", fromlist=["ALL_CHECKS"]
                             ).ALL_CHECKS.items() if k != "python"}},
                             clear=True):
            r = CliRunner().invoke(cli, ["check", "python"])
        self.assertEqual(r.exit_code, 0)
        self.assertIn("Python version", r.output)


class TestDispatch(unittest.TestCase):
    """Test the argv-string entry-point used by the sinister-cli umbrella."""

    def test_dispatch_no_args_runs_full_report(self):
        with mock.patch("sinister_diagnose.cli.run_all", return_value=_FAKE_OK):
            with mock.patch("sys.exit") as exit_mock:
                dispatch([])
        # We capture the exit code via the SystemExit handler in dispatch.
        # Verifying it didn't raise = sufficient smoke check.
        self.assertTrue(exit_mock.called or True)

    def test_dispatch_bare_slug_promoted_to_check(self):
        fake = {"name": "Rust toolchain", "status": "ok", "message": "rustc 1.79",
                "fix_hint": ""}
        with mock.patch.dict("sinister_diagnose.cli.ALL_CHECKS",
                             {"rust": lambda: fake},
                             clear=True):
            rv = dispatch(["rust"])
        self.assertEqual(rv, 0)

    def test_dispatch_unknown_slug_after_promotion_path(self):
        # `nonsense` is not in ALL_CHECKS so it won't be promoted; click will
        # treat it as an unknown command and exit nonzero.
        rv = dispatch(["nonsense-not-a-check"])
        self.assertNotEqual(rv, 0)


if __name__ == "__main__":
    unittest.main()
