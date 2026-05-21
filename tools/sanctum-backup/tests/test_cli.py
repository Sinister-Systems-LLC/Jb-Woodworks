# Sinister Sanctum :: sanctum-backup :: CLI tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""click-runner tests for `sanctum-backup` subcommands."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from sanctum_backup.cli import main as cli_main
from sanctum_backup.state import MANIFEST_NAME


# ----- helpers ------------------------------------------------------------


def _make_snap(root: Path, date: str, *, with_manifest: bool = True) -> Path:
    snap = root / date
    snap.mkdir(parents=True, exist_ok=True)
    (snap / "data.txt").write_text("payload")
    if with_manifest:
        (snap / MANIFEST_NAME).write_text(
            "# Sanctum backup manifest :: " + date
        )
    return snap


@pytest.fixture
def cli_env(tmp_path: Path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "f.txt").write_text("hello")
    dest = tmp_path / "backups"
    dest.mkdir()
    monkeypatch.setenv("SANCTUM_ROOT", str(src))
    monkeypatch.setenv("SANCTUM_BACKUP_ROOT", str(dest))
    return src, dest


# ----- root help / version ------------------------------------------------


def test_cli_help_lists_subcommands():
    r = CliRunner().invoke(cli_main, ["--help"])
    assert r.exit_code == 0
    for sub in ("now", "list", "verify", "prune", "install-task", "excludes"):
        assert sub in r.output


def test_cli_version_prints_semver():
    r = CliRunner().invoke(cli_main, ["--version"])
    assert r.exit_code == 0
    assert "0.1.0" in r.output


# ----- excludes -----------------------------------------------------------


def test_cli_excludes_includes_pycache():
    r = CliRunner().invoke(cli_main, ["excludes"])
    assert r.exit_code == 0
    assert "__pycache__" in r.output
    assert "*.pyc" in r.output
    assert "/XJ" in r.output


# ----- list ---------------------------------------------------------------


def test_cli_list_empty(cli_env):
    r = CliRunner().invoke(cli_main, ["list"])
    assert r.exit_code == 0
    assert "no backups" in r.output


def test_cli_list_populated(cli_env):
    _, dest = cli_env
    _make_snap(dest, "2026-05-21")
    _make_snap(dest, "2026-05-20")
    r = CliRunner().invoke(cli_main, ["list"])
    assert r.exit_code == 0
    assert "2026-05-21" in r.output
    assert "2026-05-20" in r.output


def test_cli_list_json(cli_env):
    _, dest = cli_env
    _make_snap(dest, "2026-05-21")
    r = CliRunner().invoke(cli_main, ["list", "--json"])
    assert r.exit_code == 0
    payload = json.loads(r.output)
    assert isinstance(payload, list)
    assert payload[0]["date"] == "2026-05-21"
    assert payload[0]["has_manifest"] is True


# ----- verify -------------------------------------------------------------


def test_cli_verify_ok(cli_env):
    _, dest = cli_env
    _make_snap(dest, "2026-05-21")
    r = CliRunner().invoke(cli_main, ["verify", "2026-05-21"])
    assert r.exit_code == 0
    assert "OK" in r.output


def test_cli_verify_missing(cli_env):
    r = CliRunner().invoke(cli_main, ["verify", "2026-05-21"])
    assert r.exit_code == 2
    assert "FAIL" in r.output


def test_cli_verify_json(cli_env):
    _, dest = cli_env
    _make_snap(dest, "2026-05-21")
    r = CliRunner().invoke(cli_main, ["verify", "2026-05-21", "--json"])
    assert r.exit_code == 0
    payload = json.loads(r.output)
    assert payload["ok"] is True
    assert payload["manifest_sha256"]


# ----- prune --------------------------------------------------------------


def test_cli_prune_noop(cli_env):
    _, dest = cli_env
    _make_snap(dest, "2026-05-21")
    r = CliRunner().invoke(cli_main, ["prune", "--keep", "7"])
    assert r.exit_code == 0
    assert "nothing to prune" in r.output


def test_cli_prune_dry_run(cli_env):
    _, dest = cli_env
    for d in ("2026-05-15", "2026-05-16", "2026-05-17"):
        _make_snap(dest, d)
    r = CliRunner().invoke(cli_main, ["prune", "--keep", "1", "--dry-run"])
    assert r.exit_code == 0
    assert "would remove" in r.output
    # nothing actually deleted
    assert (dest / "2026-05-15").exists()


def test_cli_prune_actually_deletes(cli_env):
    _, dest = cli_env
    for d in ("2026-05-15", "2026-05-16", "2026-05-17"):
        _make_snap(dest, d)
    r = CliRunner().invoke(cli_main, ["prune", "--keep", "1"])
    assert r.exit_code == 0
    assert "removed" in r.output
    assert not (dest / "2026-05-15").exists()
    assert (dest / "2026-05-17").exists()


def test_cli_prune_json(cli_env):
    _, dest = cli_env
    for d in ("2026-05-15", "2026-05-16", "2026-05-17"):
        _make_snap(dest, d)
    r = CliRunner().invoke(cli_main, ["prune", "--keep", "1", "--json"])
    assert r.exit_code == 0
    payload = json.loads(r.output)
    assert payload["keep"] == 1
    assert len(payload["removed"]) == 2


# ----- now ----------------------------------------------------------------


def test_cli_now_dry_run(cli_env):
    r = CliRunner().invoke(cli_main, ["now", "--dry-run"])
    # dry_run sets res.skipped True and res.ok False; we exit 0 in dry-run path.
    assert r.exit_code == 0
    assert "robocopy" in r.output or "exit" in r.output


def test_cli_now_dry_run_json(cli_env):
    r = CliRunner().invoke(cli_main, ["now", "--dry-run", "--json"])
    assert r.exit_code == 0
    payload = json.loads(r.output)
    assert payload["skipped"] is True
    assert isinstance(payload["robocopy_argv"], list)


# ----- install-task -------------------------------------------------------


def test_cli_install_task_dry_run(cli_env):
    r = CliRunner().invoke(cli_main, ["install-task", "--dry-run"])
    assert r.exit_code == 0
    assert "SinisterSanctumBackup" in r.output
    assert "03:00" in r.output


def test_cli_install_task_custom_name_and_time_dry_run(cli_env):
    r = CliRunner().invoke(
        cli_main,
        ["install-task", "--task-name", "MyBackup", "--time", "02:30", "--dry-run"],
    )
    assert r.exit_code == 0
    assert "MyBackup" in r.output
    assert "02:30" in r.output
