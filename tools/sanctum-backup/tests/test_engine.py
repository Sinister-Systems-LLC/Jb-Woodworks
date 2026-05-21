# Sinister Sanctum :: sanctum-backup :: engine tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""Engine + state tests. Robocopy is mocked everywhere — no real backup runs."""
from __future__ import annotations

import datetime
import subprocess
from pathlib import Path

import pytest

from sanctum_backup import (
    BackupResult,
    DEFAULT_EXCLUDES,
    build_robocopy_cmd,
    compute_dir_stats,
    list_backups,
    prune_backups,
    run_backup,
    verify_backup,
    write_manifest,
)
from sanctum_backup.engine import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_EXCLUDE_FILES,
    ROBOCOPY_OK_MAX,
    BackupSummary,
)
from sanctum_backup.state import (
    DATE_FMT,
    MANIFEST_NAME,
    backup_root,
    humanize_bytes,
    sanctum_root,
    snapshot_dir,
)


# ----- fixtures -----------------------------------------------------------


@pytest.fixture
def tmp_source(tmp_path: Path) -> Path:
    """Build a tiny source tree that resembles Sanctum's shape."""
    src = tmp_path / "sanctum-source"
    (src / "subdir").mkdir(parents=True)
    (src / "file_a.txt").write_text("alpha")
    (src / "file_b.md").write_text("# beta")
    (src / "subdir" / "nested.py").write_text("print('hi')\n")
    # An excluded dir + an excluded file, just to confirm patterns are
    # plumbed into the argv (we mock robocopy so they aren't actually filtered).
    (src / "__pycache__").mkdir()
    (src / "__pycache__" / "x.pyc").write_text("byte")
    return src


@pytest.fixture
def fake_runner():
    """Return a runner that records argv + returns a configured exit code."""
    calls: list[list[str]] = []

    def make(exit_code: int = 1, stderr: str = ""):
        def _runner(argv: list[str]) -> subprocess.CompletedProcess:
            calls.append(list(argv))
            # We can't easily synthesize the snapshot dir here because the
            # runner is called by run_backup AFTER the dest is created;
            # for realism we drop a small marker file so compute_dir_stats
            # downstream sees non-zero output.
            try:
                dst = Path(argv[2])
                dst.mkdir(parents=True, exist_ok=True)
                (dst / "copied.txt").write_text("copied by fake robocopy")
            except Exception:
                pass
            return subprocess.CompletedProcess(
                args=argv, returncode=exit_code, stdout="", stderr=stderr
            )

        return _runner, calls

    return make


# ----- exclude defaults ---------------------------------------------------


def test_default_excludes_contains_required_dirs():
    required = {
        ".swarm", ".claude/worktrees", "__pycache__", "build", "dist",
        "node_modules", ".pytest_cache", ".venv", "venv",
        ".mypy_cache", ".ruff_cache",
    }
    assert required.issubset(set(DEFAULT_EXCLUDE_DIRS))


def test_default_excludes_contains_required_files():
    assert "*.pyc" in DEFAULT_EXCLUDE_FILES
    assert "*.pyo" in DEFAULT_EXCLUDE_FILES


def test_default_excludes_union_contains_all():
    for x in (*DEFAULT_EXCLUDE_DIRS, *DEFAULT_EXCLUDE_FILES):
        assert x in DEFAULT_EXCLUDES


# ----- robocopy argv ------------------------------------------------------


def test_build_robocopy_cmd_basic(tmp_path: Path):
    src = tmp_path / "s"
    dst = tmp_path / "d"
    argv = build_robocopy_cmd(src, dst)
    assert argv[0] == "robocopy"
    assert argv[1] == str(src)
    assert argv[2] == str(dst)
    assert "/MIR" in argv
    assert "/XJ" in argv
    assert "/XD" in argv
    assert "/XF" in argv
    assert "*.pyc" in argv
    assert "__pycache__" in argv


def test_build_robocopy_cmd_optional_flags(tmp_path: Path):
    argv = build_robocopy_cmd(
        tmp_path / "s",
        tmp_path / "d",
        mirror=False,
        skip_junctions=False,
        multi_thread=0,
        retries=3,
        wait=4,
    )
    assert "/MIR" not in argv
    assert "/XJ" not in argv
    assert "/MT:0" not in argv  # zero MT suppressed entirely
    assert "/R:3" in argv
    assert "/W:4" in argv


def test_build_robocopy_cmd_custom_excludes(tmp_path: Path):
    argv = build_robocopy_cmd(
        tmp_path / "s", tmp_path / "d",
        exclude_dirs=("just_one",),
        exclude_files=("*.tmp",),
    )
    assert "just_one" in argv
    assert "*.tmp" in argv
    # The standard names should NOT be present when overridden.
    assert "__pycache__" not in argv


# ----- dir-stats ---------------------------------------------------------


def test_compute_dir_stats_counts_files(tmp_source: Path):
    s = compute_dir_stats(tmp_source)
    assert isinstance(s, BackupSummary)
    # 3 regular + 1 pycache = 4 files total
    assert s.file_count == 4
    assert s.size_bytes > 0


def test_compute_dir_stats_missing_path(tmp_path: Path):
    s = compute_dir_stats(tmp_path / "nope")
    assert s.size_bytes == 0
    assert s.file_count == 0


# ----- state paths -------------------------------------------------------


def test_backup_root_env_override(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SANCTUM_BACKUP_ROOT", str(tmp_path))
    assert backup_root() == tmp_path


def test_sanctum_root_env_override(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SANCTUM_ROOT", str(tmp_path))
    assert sanctum_root() == tmp_path


def test_snapshot_dir_string_date(tmp_path: Path):
    sd = snapshot_dir("2026-05-21", root=tmp_path)
    assert sd == tmp_path / "2026-05-21"


def test_snapshot_dir_date_obj(tmp_path: Path):
    sd = snapshot_dir(datetime.date(2026, 5, 21), root=tmp_path)
    assert sd == tmp_path / "2026-05-21"


def test_humanize_bytes_scales():
    assert humanize_bytes(0).endswith(" B")
    assert humanize_bytes(2048).endswith(" KB")
    assert humanize_bytes(5 * 1024 * 1024).endswith(" MB")


# ----- run_backup --------------------------------------------------------


def test_run_backup_happy_path(tmp_path: Path, tmp_source: Path, fake_runner):
    runner, calls = fake_runner(exit_code=1)
    dest = tmp_path / "backups"
    res = run_backup(
        source=tmp_source,
        dest_root=dest,
        date="2026-05-21",
        runner=runner,
    )
    assert isinstance(res, BackupResult)
    assert res.ok is True
    assert res.skipped is False
    assert res.robocopy_exit_code == 1
    assert res.date == "2026-05-21"
    assert len(calls) == 1
    # Manifest should have been written.
    assert (dest / "2026-05-21" / MANIFEST_NAME).exists()


def test_run_backup_writes_manifest_with_expected_fields(
    tmp_path: Path, tmp_source: Path, fake_runner
):
    runner, _ = fake_runner(exit_code=0)
    dest = tmp_path / "backups"
    res = run_backup(
        source=tmp_source, dest_root=dest, date="2026-05-21", runner=runner
    )
    manifest = (dest / "2026-05-21" / MANIFEST_NAME).read_text(encoding="utf-8")
    assert "Sanctum backup manifest" in manifest
    assert "RKOJ-ELENO" in manifest
    assert "robocopy exit" in manifest
    assert "__pycache__" in manifest
    assert "*.pyc" in manifest
    assert res.robocopy_argv[0] == "robocopy"


def test_run_backup_failure_exit_code(tmp_path: Path, tmp_source: Path, fake_runner):
    runner, _ = fake_runner(exit_code=16, stderr="boom")
    res = run_backup(
        source=tmp_source,
        dest_root=tmp_path / "b",
        date="2026-05-21",
        runner=runner,
    )
    assert res.ok is False
    assert res.robocopy_exit_code == 16
    assert any("exit code 16" in e for e in res.errors)


def test_run_backup_refuses_existing_destination(
    tmp_path: Path, tmp_source: Path, fake_runner
):
    runner, _ = fake_runner(exit_code=1)
    dest = tmp_path / "backups"
    snap = dest / "2026-05-21"
    snap.mkdir(parents=True)
    res = run_backup(
        source=tmp_source, dest_root=dest, date="2026-05-21", runner=runner
    )
    assert res.skipped is True
    assert any("already exists" in e for e in res.errors)


def test_run_backup_force_overwrites(tmp_path: Path, tmp_source: Path, fake_runner):
    runner, _ = fake_runner(exit_code=1)
    dest = tmp_path / "backups"
    snap = dest / "2026-05-21"
    snap.mkdir(parents=True)
    (snap / "old.txt").write_text("stale")
    res = run_backup(
        source=tmp_source, dest_root=dest, date="2026-05-21",
        runner=runner, overwrite_existing=True,
    )
    assert res.skipped is False
    assert res.ok is True


def test_run_backup_dry_run(tmp_path: Path, tmp_source: Path, fake_runner):
    runner, calls = fake_runner(exit_code=1)
    dest = tmp_path / "backups"
    res = run_backup(
        source=tmp_source, dest_root=dest, date="2026-05-21",
        runner=runner, dry_run=True,
    )
    assert res.skipped is True
    assert len(calls) == 0
    assert not (dest / "2026-05-21" / MANIFEST_NAME).exists()


def test_run_backup_robocopy_missing(tmp_path: Path, tmp_source: Path):
    def _missing(argv):
        raise FileNotFoundError("robocopy not found")

    res = run_backup(
        source=tmp_source,
        dest_root=tmp_path / "b",
        date="2026-05-21",
        runner=_missing,
    )
    assert res.skipped is True
    assert any("robocopy" in e for e in res.errors)


# ----- list_backups + prune ---------------------------------------------


def _make_snapshot(root: Path, date: str, *, with_manifest: bool = True) -> Path:
    snap = root / date
    snap.mkdir(parents=True, exist_ok=True)
    (snap / "data.txt").write_text("payload" * 50)
    if with_manifest:
        (snap / MANIFEST_NAME).write_text("# fake manifest")
    return snap


def test_list_backups_sorted_newest_first(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SANCTUM_BACKUP_ROOT", str(tmp_path))
    _make_snapshot(tmp_path, "2026-05-19")
    _make_snapshot(tmp_path, "2026-05-21")
    _make_snapshot(tmp_path, "2026-05-20")
    rows = list_backups()
    assert [r.date for r in rows] == ["2026-05-21", "2026-05-20", "2026-05-19"]
    assert all(r.has_manifest for r in rows)
    assert all(r.file_count >= 1 for r in rows)


def test_list_backups_ignores_non_date_dirs(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SANCTUM_BACKUP_ROOT", str(tmp_path))
    _make_snapshot(tmp_path, "2026-05-21")
    (tmp_path / "junk").mkdir()
    rows = list_backups()
    assert {r.date for r in rows} == {"2026-05-21"}


def test_prune_keeps_newest(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SANCTUM_BACKUP_ROOT", str(tmp_path))
    for d in (
        "2026-05-14", "2026-05-15", "2026-05-16", "2026-05-17",
        "2026-05-18", "2026-05-19", "2026-05-20", "2026-05-21",
        "2026-05-13",
    ):
        _make_snapshot(tmp_path, d)
    removed = prune_backups(keep=7)
    assert len(removed) == 2
    survivors = {r.date for r in list_backups()}
    assert "2026-05-21" in survivors
    assert "2026-05-13" not in survivors
    assert "2026-05-14" not in survivors


def test_prune_dry_run_doesnt_delete(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SANCTUM_BACKUP_ROOT", str(tmp_path))
    for d in ("2026-05-01", "2026-05-02", "2026-05-03"):
        _make_snapshot(tmp_path, d)
    victims = prune_backups(keep=1, dry_run=True)
    assert len(victims) == 2
    assert len(list_backups()) == 3  # still all present


def test_prune_noop_when_under_keep(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SANCTUM_BACKUP_ROOT", str(tmp_path))
    _make_snapshot(tmp_path, "2026-05-21")
    assert prune_backups(keep=7) == []


# ----- verify ------------------------------------------------------------


def test_verify_ok(tmp_path: Path):
    snap = _make_snapshot(tmp_path, "2026-05-21")
    out = verify_backup(snap)
    assert out["ok"] is True
    assert out["has_manifest"] is True
    assert out["manifest_sha256"]
    assert out["file_count"] >= 2  # data.txt + manifest


def test_verify_missing_manifest(tmp_path: Path):
    snap = _make_snapshot(tmp_path, "2026-05-21", with_manifest=False)
    out = verify_backup(snap)
    assert out["ok"] is False
    assert "missing" in " ".join(out["errors"]).lower()


def test_verify_missing_snapshot(tmp_path: Path):
    out = verify_backup(tmp_path / "nope")
    assert out["ok"] is False


# ----- write_manifest direct --------------------------------------------


def test_write_manifest_returns_path(tmp_path: Path):
    snap = tmp_path / "2026-05-21"
    snap.mkdir()
    res = BackupResult(
        date="2026-05-21",
        branch="agent/sinister-sanctum/cli-dispatcher-2026-05-21",
        head="deadbee",
        head_subject="feat(sanctum-backup): seed",
        source=BackupSummary(tmp_path / "src", 1024, 3),
        destination=BackupSummary(snap, 1024, 3),
        excluded_dirs=DEFAULT_EXCLUDE_DIRS,
        excluded_files=DEFAULT_EXCLUDE_FILES,
        robocopy_argv=("robocopy", "src", "dst", "/MIR"),
        robocopy_exit_code=1,
        started_at="2026-05-21T03:00:00",
        finished_at="2026-05-21T03:05:00",
    )
    out_path = write_manifest(snap, res)
    assert out_path.exists()
    text = out_path.read_text(encoding="utf-8")
    assert "agent/sinister-sanctum/cli-dispatcher-2026-05-21" in text
    assert "deadbee" in text
    assert "/MIR" in text
    assert res.robocopy_exit_code <= ROBOCOPY_OK_MAX


# ----- DATE_FMT sanity ---------------------------------------------------


def test_date_fmt_round_trip():
    today = datetime.date.today()
    s = today.strftime(DATE_FMT)
    again = datetime.datetime.strptime(s, DATE_FMT).date()
    assert again == today
