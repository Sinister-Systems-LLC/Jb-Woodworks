# Sinister Sanctum :: sanctum-backup :: click CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""click-based CLI for sanctum-backup.

Subcommands:
    sanctum-backup now                  - run one backup now
    sanctum-backup list                 - list known backups
    sanctum-backup verify <date>        - re-verify a backup's manifest
    sanctum-backup prune                - delete backups older than --keep
    sanctum-backup install-task         - register a Windows scheduled task
"""
from __future__ import annotations

import datetime
import json as _json
import subprocess
import sys
from pathlib import Path

import click

from . import __version__
from .engine import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_EXCLUDE_FILES,
    ROBOCOPY_OK_MAX,
    run_backup,
    verify_backup,
)
from .state import (
    backup_root,
    humanize_bytes,
    list_backups,
    prune_backups,
    sanctum_root,
)


@click.group(
    help=(
        "sanctum-backup — recurring Sinister Sanctum backups. "
        "Daily robocopy snapshots, 7-day retention, per-backup manifest."
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, prog_name="sanctum-backup")
def main() -> None:
    """Root click group; subcommands attach below."""


# ----- now ---------------------------------------------------------------


@main.command("now", help="Run a backup right now.")
@click.option("--source", type=click.Path(path_type=Path), default=None,
              help="Source path (default: $SANCTUM_ROOT or D:/Sinister Sanctum).")
@click.option("--dest-root", type=click.Path(path_type=Path), default=None,
              help="Destination root (default: $SANCTUM_BACKUP_ROOT or D:/sinister-sanctum-backups).")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite an existing snapshot for today's date.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Compute argv + source stats but skip the actual robocopy run.")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Emit the BackupResult as JSON to stdout.")
def _cmd_now(source, dest_root, force, dry_run, as_json) -> None:
    res = run_backup(
        source=source,
        dest_root=dest_root,
        overwrite_existing=force,
        dry_run=dry_run,
    )
    if as_json:
        click.echo(_json.dumps(res.to_dict(), indent=2))
    else:
        _print_result(res)
    sys.exit(0 if res.ok or dry_run else 2)


def _print_result(res) -> None:
    click.echo(f"sanctum-backup :: {res.date}")
    click.echo(f"  branch:   {res.branch}  head: {res.head}  {res.head_subject[:80]}")
    click.echo(f"  source:   {res.source.path}")
    click.echo(f"            {humanize_bytes(res.source.size_bytes)} "
               f"({res.source.file_count:,} files)")
    click.echo(f"  dest:     {res.destination.path}")
    click.echo(f"            {humanize_bytes(res.destination.size_bytes)} "
               f"({res.destination.file_count:,} files)")
    click.echo(f"  excludes: {len(res.excluded_dirs)} dirs, {len(res.excluded_files)} files, /XJ junctions")
    click.echo(f"  exit:     {res.robocopy_exit_code}  "
               f"({'OK' if res.robocopy_exit_code <= ROBOCOPY_OK_MAX else 'FAIL'})")
    if res.errors:
        click.echo("  errors:")
        for e in res.errors:
            click.echo(f"    - {e}")
    if res.skipped:
        click.echo(f"  note:     {res.note or 'skipped'}")


# ----- list --------------------------------------------------------------


@main.command("list", help="List known backups under the backup root.")
@click.option("--json", "as_json", is_flag=True, default=False)
def _cmd_list(as_json) -> None:
    rows = list_backups()
    if as_json:
        click.echo(_json.dumps([r.to_dict() for r in rows], indent=2))
        return
    if not rows:
        click.echo(f"sanctum-backup: no backups found under {backup_root()}")
        sys.exit(0)
    click.echo(f"sanctum-backup :: {len(rows)} backup(s) under {backup_root()}")
    click.echo(f"{'date':<12} {'size':>10}  {'files':>9}  manifest")
    click.echo("-" * 48)
    for r in rows:
        manifest = "yes" if r.has_manifest else "no"
        click.echo(f"{r.date:<12} {humanize_bytes(r.size_bytes):>10}  "
                   f"{r.file_count:>9,}  {manifest}")


# ----- verify ------------------------------------------------------------


@main.command("verify", help="Re-check a backup's manifest + on-disk state.")
@click.argument("date", required=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def _cmd_verify(date, as_json) -> None:
    snap = backup_root() / date
    res = verify_backup(snap)
    if as_json:
        click.echo(_json.dumps(res, indent=2))
    else:
        ok = "OK" if res.get("ok") else "FAIL"
        click.echo(f"[{ok}] {date}  {snap}")
        click.echo(f"  exists:           {res['exists']}")
        click.echo(f"  manifest:         {'yes' if res['has_manifest'] else 'no'}")
        if res["has_manifest"]:
            click.echo(f"  manifest-sha256:  {res['manifest_sha256']}")
        click.echo(f"  size:             {humanize_bytes(res['size_bytes'])}")
        click.echo(f"  files:            {res['file_count']:,}")
        for e in res.get("errors", []):
            click.echo(f"  error:            {e}")
    sys.exit(0 if res.get("ok") else 2)


# ----- prune -------------------------------------------------------------


@main.command("prune", help="Delete backups older than --keep (default 7).")
@click.option("--keep", type=int, default=7, show_default=True,
              help="Number of newest snapshots to retain.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Show what would be deleted but do nothing.")
@click.option("--json", "as_json", is_flag=True, default=False)
def _cmd_prune(keep, dry_run, as_json) -> None:
    victims = prune_backups(keep=keep, dry_run=dry_run)
    payload = {
        "keep": keep,
        "dry_run": dry_run,
        "removed": [v.to_dict() for v in victims],
    }
    if as_json:
        click.echo(_json.dumps(payload, indent=2))
        return
    if not victims:
        click.echo(f"sanctum-backup: nothing to prune (keep={keep}).")
        return
    label = "would remove" if dry_run else "removed"
    click.echo(f"sanctum-backup: {label} {len(victims)} backup(s):")
    for v in victims:
        click.echo(f"  - {v.date}  {humanize_bytes(v.size_bytes)}  {v.file_count:,} files")


# ----- install-task ------------------------------------------------------


@main.command("install-task", help="Register the daily Windows scheduled task (03:00).")
@click.option("--time", "at_time", default="03:00", show_default=True,
              help="Local time-of-day for the daily run (HH:MM).")
@click.option("--task-name", default="SinisterSanctumBackup", show_default=True,
              help="Windows Task Scheduler entry name.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print the PowerShell invocation but don't actually install.")
def _cmd_install_task(at_time, task_name, dry_run) -> None:
    script = Path(__file__).resolve().parent.parent / "install-task.ps1"
    if not script.exists():
        click.echo(f"sanctum-backup: helper script missing: {script}", err=True)
        sys.exit(2)
    ps_argv = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script),
        "-TaskName", task_name,
        "-AtTime", at_time,
    ]
    click.echo(f"sanctum-backup: install-task  name={task_name}  at={at_time}")
    click.echo(f"  helper: {script}")
    click.echo(f"  argv:   {' '.join(ps_argv)}")
    if dry_run:
        click.echo("  (dry-run; not invoked)")
        return
    click.echo("  invoking PowerShell helper ...")
    try:
        r = subprocess.run(ps_argv, capture_output=True, text=True, timeout=60)
        if r.stdout:
            click.echo(r.stdout.rstrip())
        if r.stderr:
            click.echo(r.stderr.rstrip(), err=True)
        sys.exit(r.returncode)
    except FileNotFoundError:
        click.echo("sanctum-backup: powershell.exe not available on this host.", err=True)
        sys.exit(2)


# ----- excludes ----------------------------------------------------------


@main.command("excludes", help="Print the default exclude lists.")
def _cmd_excludes() -> None:
    click.echo("[directories]")
    for d in DEFAULT_EXCLUDE_DIRS:
        click.echo(f"  {d}")
    click.echo("[files]")
    for f in DEFAULT_EXCLUDE_FILES:
        click.echo(f"  {f}")
    click.echo("[junctions]")
    click.echo("  skipped via /XJ")
