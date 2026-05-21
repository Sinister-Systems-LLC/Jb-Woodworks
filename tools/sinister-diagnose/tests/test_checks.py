# Sinister Sanctum :: sinister-diagnose :: tests :: checks
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Pytest-compatible (also runnable via `python -m unittest`) tests for the
14 check functions + the runner.

Goal: 20+ assertions, mocking subprocess + filesystem so the suite is
hermetic regardless of the dev's environment.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

# Make the package importable when run directly from the test folder.
HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sinister_diagnose import checks  # noqa: E402
from sinister_diagnose.checks import (  # noqa: E402
    ALL_CHECKS,
    check_anthropic_sdk,
    check_backups,
    check_branch,
    check_claude_cli,
    check_disk_space,
    check_git_config,
    check_heartbeats,
    check_mcp_servers,
    check_pyinstaller,
    check_python_version,
    check_rkoj_exe,
    check_rust_toolchain,
    check_sanctum_root,
    check_vault_daemon,
    overall_status,
    run_all,
)


# ---------------------------------------------------------------------------
# tiny helpers
# ---------------------------------------------------------------------------

def _completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def _result_shape_ok(r):
    """Every check must return a 4-key dict."""
    return (
        isinstance(r, dict)
        and set(r.keys()) >= {"name", "status", "message", "fix_hint"}
        and r["status"] in ("ok", "warn", "fail", "info")
    )


# ---------------------------------------------------------------------------
# python version
# ---------------------------------------------------------------------------

class TestPythonVersion(unittest.TestCase):
    def test_python_ok_or_fail_shape(self):
        r = check_python_version()
        self.assertTrue(_result_shape_ok(r))
        self.assertEqual(r["name"], "Python version")

    def test_python_3_11_passes_when_running_on_311_plus(self):
        # If the test interpreter is >= 3.11 we expect ok; otherwise fail.
        r = check_python_version()
        if sys.version_info >= (3, 11):
            self.assertEqual(r["status"], "ok")
        else:  # pragma: no cover
            self.assertEqual(r["status"], "fail")


# ---------------------------------------------------------------------------
# pyinstaller / anthropic / claude-cli
# ---------------------------------------------------------------------------

class TestPyInstaller(unittest.TestCase):
    def test_pyinstaller_missing_returns_fail(self):
        # Force the import to fail by removing PyInstaller from sys.modules
        # and inserting a None entry so `import` raises ImportError.
        with mock.patch.dict(sys.modules, {"PyInstaller": None}):
            r = check_pyinstaller()
        self.assertTrue(_result_shape_ok(r))
        self.assertEqual(r["status"], "fail")
        self.assertIn("pip install pyinstaller", r["fix_hint"])

    def test_pyinstaller_present_returns_ok(self):
        fake_pyi = mock.MagicMock()
        fake_pyi.__version__ = "6.99.0"
        with mock.patch.dict(sys.modules, {"PyInstaller": fake_pyi}):
            r = check_pyinstaller()
        self.assertEqual(r["status"], "ok")
        self.assertIn("6.99.0", r["message"])


class TestAnthropicSdk(unittest.TestCase):
    def test_missing_sdk_fails(self):
        with mock.patch.dict(sys.modules, {"anthropic": None}):
            with mock.patch.dict(os.environ, {}, clear=False):
                r = check_anthropic_sdk()
        self.assertEqual(r["status"], "fail")

    def test_sdk_present_but_no_key_warns(self):
        fake = mock.MagicMock()
        fake.__version__ = "0.30.0"
        with mock.patch.dict(sys.modules, {"anthropic": fake}):
            saved = os.environ.pop("ANTHROPIC_API_KEY", None)
            try:
                r = check_anthropic_sdk()
            finally:
                if saved is not None:
                    os.environ["ANTHROPIC_API_KEY"] = saved
        self.assertEqual(r["status"], "warn")
        self.assertIn("ANTHROPIC_API_KEY", r["message"])

    def test_sdk_present_with_key_ok(self):
        fake = mock.MagicMock()
        fake.__version__ = "0.30.0"
        with mock.patch.dict(sys.modules, {"anthropic": fake}), \
             mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-1234567890"}):
            r = check_anthropic_sdk()
        self.assertEqual(r["status"], "ok")


class TestClaudeCli(unittest.TestCase):
    def test_claude_on_path_ok(self):
        with mock.patch("sinister_diagnose.checks.shutil.which",
                        side_effect=lambda x: r"C:\bin\claude.exe" if "claude" in x else None):
            r = check_claude_cli()
        self.assertEqual(r["status"], "ok")

    def test_claude_missing_fails(self):
        with mock.patch("sinister_diagnose.checks.shutil.which", return_value=None), \
             mock.patch("sinister_diagnose.checks.Path.exists", return_value=False):
            r = check_claude_cli()
        self.assertEqual(r["status"], "fail")


# ---------------------------------------------------------------------------
# rust + git
# ---------------------------------------------------------------------------

class TestRustToolchain(unittest.TestCase):
    def test_rust_missing_warns(self):
        with mock.patch("sinister_diagnose.checks._run_cmd", return_value=None):
            r = check_rust_toolchain()
        self.assertEqual(r["status"], "warn")  # rust is optional
        self.assertIn("rustup", r["fix_hint"])

    def test_rust_present_ok(self):
        cp = _completed("rustc 1.79.0 (129f3b996 2024-06-10)\n", 0)
        with mock.patch("sinister_diagnose.checks._run_cmd", return_value=cp):
            r = check_rust_toolchain()
        self.assertEqual(r["status"], "ok")
        self.assertIn("rustc", r["message"])


class TestGitConfig(unittest.TestCase):
    def test_both_set_ok(self):
        calls = iter([_completed("RKOJ-ELENO\n"), _completed("rkoj@x\n")])
        with mock.patch("sinister_diagnose.checks._run_cmd",
                        side_effect=lambda *_a, **_kw: next(calls)):
            r = check_git_config()
        self.assertEqual(r["status"], "ok")
        self.assertIn("RKOJ-ELENO", r["message"])

    def test_both_unset_fails(self):
        calls = iter([_completed(""), _completed("")])
        with mock.patch("sinister_diagnose.checks._run_cmd",
                        side_effect=lambda *_a, **_kw: next(calls)):
            r = check_git_config()
        self.assertEqual(r["status"], "fail")

    def test_no_git_binary_fails(self):
        with mock.patch("sinister_diagnose.checks._run_cmd", return_value=None):
            r = check_git_config()
        self.assertEqual(r["status"], "fail")
        self.assertIn("git", r["fix_hint"].lower())


# ---------------------------------------------------------------------------
# sanctum-root / backups / disk / rkoj-exe / branch / heartbeats / mcp / vault
# ---------------------------------------------------------------------------

class TestSanctumRoot(unittest.TestCase):
    def test_missing_root_fails(self):
        with tempfile.TemporaryDirectory() as td:
            ghost = Path(td) / "ghost"
            with mock.patch.dict(os.environ, {"SANCTUM_ROOT": str(ghost)}):
                r = check_sanctum_root()
            self.assertEqual(r["status"], "fail")

    def test_root_without_claude_md_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"SANCTUM_ROOT": td}):
                r = check_sanctum_root()
            self.assertEqual(r["status"], "fail")
            self.assertIn("CLAUDE.md", r["message"])

    def test_root_with_claude_md_ok(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "CLAUDE.md").write_text("# CLAUDE.md", encoding="utf-8")
            with mock.patch.dict(os.environ, {"SANCTUM_ROOT": td}):
                r = check_sanctum_root()
            self.assertEqual(r["status"], "ok")


class TestBackups(unittest.TestCase):
    def test_missing_backups_dir_fails(self):
        with tempfile.TemporaryDirectory() as td:
            ghost = Path(td) / "ghost"
            with mock.patch.dict(os.environ, {"SANCTUM_BACKUPS": str(ghost)}):
                r = check_backups()
            self.assertEqual(r["status"], "fail")

    def test_no_manifest_warns(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"SANCTUM_BACKUPS": td}):
                r = check_backups()
            self.assertEqual(r["status"], "warn")
            self.assertIn("MANIFEST", r["message"])

    def test_recent_dir_ok(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "MANIFEST.md").write_text("# manifest", encoding="utf-8")
            (tp / "2026-05-21").mkdir()
            with mock.patch.dict(os.environ, {"SANCTUM_BACKUPS": td}):
                r = check_backups()
            self.assertEqual(r["status"], "ok")
            self.assertIn("recent", r["message"])

    def test_stale_dirs_warn(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "MANIFEST.md").write_text("# manifest", encoding="utf-8")
            old = tp / "2020-01-01"
            old.mkdir()
            old_ts = time.time() - (30 * 86400)
            os.utime(old, (old_ts, old_ts))
            with mock.patch.dict(os.environ, {"SANCTUM_BACKUPS": td}):
                r = check_backups()
            self.assertEqual(r["status"], "warn")


class TestDiskSpace(unittest.TestCase):
    def test_plenty_of_space_ok(self):
        usage = type("U", (), {"free": 200 * (1024**3), "total": 1000 * (1024**3), "used": 0})
        with mock.patch("sinister_diagnose.checks.shutil.disk_usage", return_value=usage):
            r = check_disk_space()
        self.assertEqual(r["status"], "ok")

    def test_low_space_warns(self):
        usage = type("U", (), {"free": 20 * (1024**3), "total": 1000 * (1024**3), "used": 0})
        with mock.patch("sinister_diagnose.checks.shutil.disk_usage", return_value=usage):
            r = check_disk_space()
        self.assertEqual(r["status"], "warn")

    def test_critical_space_fails(self):
        usage = type("U", (), {"free": 5 * (1024**3), "total": 1000 * (1024**3), "used": 0})
        with mock.patch("sinister_diagnose.checks.shutil.disk_usage", return_value=usage):
            r = check_disk_space()
        self.assertEqual(r["status"], "fail")

    def test_disk_error_fails(self):
        with mock.patch("sinister_diagnose.checks.shutil.disk_usage",
                        side_effect=OSError("no such drive")):
            r = check_disk_space()
        self.assertEqual(r["status"], "fail")


class TestRkojExe(unittest.TestCase):
    def test_missing_rkoj_warns(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"USERPROFILE": td}):
                r = check_rkoj_exe()
            self.assertEqual(r["status"], "warn")

    def test_recent_rkoj_ok(self):
        with tempfile.TemporaryDirectory() as td:
            desk = Path(td) / "Desktop"
            desk.mkdir()
            exe = desk / "RKOJ.exe"
            exe.write_bytes(b"\x00" * 16)
            with mock.patch.dict(os.environ, {"USERPROFILE": td}):
                r = check_rkoj_exe()
            self.assertEqual(r["status"], "ok")

    def test_stale_rkoj_warns(self):
        with tempfile.TemporaryDirectory() as td:
            desk = Path(td) / "Desktop"
            desk.mkdir()
            exe = desk / "RKOJ.exe"
            exe.write_bytes(b"\x00" * 16)
            old = time.time() - (14 * 86400)
            os.utime(exe, (old, old))
            with mock.patch.dict(os.environ, {"USERPROFILE": td}):
                r = check_rkoj_exe()
            self.assertEqual(r["status"], "warn")
            self.assertIn("days old", r["message"])


class TestBranchCheck(unittest.TestCase):
    def test_matching_branch_ok(self):
        cp = _completed("agent/sinister-sanctum/cli-dispatcher-2026-05-21\n")
        with mock.patch("sinister_diagnose.checks._run_cmd", return_value=cp):
            r = check_branch()
        self.assertEqual(r["status"], "ok")

    def test_wrong_branch_warns(self):
        cp = _completed("main\n")
        with mock.patch("sinister_diagnose.checks._run_cmd", return_value=cp):
            r = check_branch()
        self.assertEqual(r["status"], "warn")

    def test_not_a_repo_warns(self):
        with mock.patch("sinister_diagnose.checks._run_cmd", return_value=None):
            r = check_branch()
        self.assertEqual(r["status"], "warn")


class TestHeartbeats(unittest.TestCase):
    def test_no_dir_warns(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"SANCTUM_ROOT": td}):
                r = check_heartbeats()
            self.assertEqual(r["status"], "warn")

    def test_empty_dir_warns(self):
        with tempfile.TemporaryDirectory() as td:
            hb = Path(td) / "_shared-memory" / "heartbeats"
            hb.mkdir(parents=True)
            with mock.patch.dict(os.environ, {"SANCTUM_ROOT": td}):
                r = check_heartbeats()
            self.assertEqual(r["status"], "warn")

    def test_fresh_heartbeat_ok(self):
        with tempfile.TemporaryDirectory() as td:
            hb = Path(td) / "_shared-memory" / "heartbeats"
            hb.mkdir(parents=True)
            (hb / "sanctum.json").write_text("{}", encoding="utf-8")
            with mock.patch.dict(os.environ, {"SANCTUM_ROOT": td}):
                r = check_heartbeats()
            self.assertEqual(r["status"], "ok")

    def test_stale_heartbeat_warns(self):
        with tempfile.TemporaryDirectory() as td:
            hb = Path(td) / "_shared-memory" / "heartbeats"
            hb.mkdir(parents=True)
            f = hb / "ghost.json"
            f.write_text("{}", encoding="utf-8")
            old = time.time() - (48 * 3600)
            os.utime(f, (old, old))
            with mock.patch.dict(os.environ, {"SANCTUM_ROOT": td}):
                r = check_heartbeats()
            self.assertEqual(r["status"], "warn")
            self.assertIn("stale", r["message"])


class TestMcpServers(unittest.TestCase):
    def test_missing_mcp_warns(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch("sinister_diagnose.checks.Path.home", return_value=Path(td)):
                r = check_mcp_servers()
            self.assertEqual(r["status"], "warn")

    def test_valid_mcp_ok(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            (home / ".claude").mkdir()
            (home / ".claude" / ".mcp.json").write_text(
                json.dumps({"mcpServers": {"a": {}, "b": {}}}), encoding="utf-8")
            with mock.patch("sinister_diagnose.checks.Path.home", return_value=home):
                r = check_mcp_servers()
            self.assertEqual(r["status"], "ok")
            self.assertIn("2 server", r["message"])

    def test_invalid_mcp_fails(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            (home / ".claude").mkdir()
            (home / ".claude" / ".mcp.json").write_text("{not-json", encoding="utf-8")
            with mock.patch("sinister_diagnose.checks.Path.home", return_value=home):
                r = check_mcp_servers()
            self.assertEqual(r["status"], "fail")


class TestVaultDaemon(unittest.TestCase):
    def test_info_when_not_listening(self):
        # Use a near-guaranteed-not-bound port by patching socket factory.
        fake_sock = mock.MagicMock()
        fake_sock.connect_ex.return_value = 10061  # Win32 connection refused
        with mock.patch("sinister_diagnose.checks.socket.socket", return_value=fake_sock):
            r = check_vault_daemon()
        self.assertEqual(r["status"], "info")
        self.assertIn("not listening", r["message"])

    def test_info_when_listening(self):
        fake_sock = mock.MagicMock()
        fake_sock.connect_ex.return_value = 0
        with mock.patch("sinister_diagnose.checks.socket.socket", return_value=fake_sock):
            r = check_vault_daemon()
        self.assertEqual(r["status"], "info")
        self.assertIn("listening", r["message"])


# ---------------------------------------------------------------------------
# runner + registry
# ---------------------------------------------------------------------------

class TestRunner(unittest.TestCase):
    def test_all_checks_registered(self):
        self.assertEqual(len(ALL_CHECKS), 14)
        for slug, fn in ALL_CHECKS.items():
            self.assertTrue(callable(fn), f"{slug} is not callable")

    def test_run_all_returns_one_row_per_check(self):
        results = run_all()
        self.assertEqual(len(results), len(ALL_CHECKS))
        for r in results:
            self.assertTrue(_result_shape_ok(r))

    def test_overall_status_priority(self):
        # fail dominates everything.
        rs = [
            {"name": "a", "status": "ok", "message": "", "fix_hint": ""},
            {"name": "b", "status": "fail", "message": "", "fix_hint": ""},
            {"name": "c", "status": "warn", "message": "", "fix_hint": ""},
        ]
        self.assertEqual(overall_status(rs), "fail")
        # warn dominates ok.
        rs[1]["status"] = "ok"
        self.assertEqual(overall_status(rs), "warn")
        # only ok → ok.
        rs[2]["status"] = "ok"
        self.assertEqual(overall_status(rs), "ok")


if __name__ == "__main__":
    unittest.main()
