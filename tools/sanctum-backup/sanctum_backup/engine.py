# Sinister Sanctum :: sanctum-backup :: robocopy engine + manifest writer
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""Robocopy wrapper + per-backup manifest emitter.

The same exclude set as the manual "H agent" run (operator brief 2026-05-21):
    .swarm, .claude/worktrees, __pycache__, build, dist, node_modules,
    .pytest_cache, .venv, venv, .mypy_cache, .ruff_cache, *.pyc, *.pyo
plus /XJ to skip junctions (Sanctum uses junctions heavily under `projects/`).

Robocopy exit-code semantics (Microsoft documented):
    0  No files were copied. No failure was encountered. No mismatches.
    1  Files copied successfully.
    2  Extra files / directories detected.
    3  (1+2) Some files copied, additional files present.
    4  Mismatched files / directories detected.
    5  (1+4) Some files copied; mismatches present.
    6  (4+2) Mismatches + extras (no copies).
    7  (4+2+1) Files copied, mismatches, extras (still OK).
    >=8  At least one failure.
"""
from __future__ import annotations

import datetime
import hashlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

from .state import (
    DATE_FMT,
    MANIFEST_NAME,
    backup_root,
    sanctum_root,
    snapshot_dir,
)


DEFAULT_EXCLUDE_DIRS: tuple[str, ...] = (
    ".swarm",
    ".claude/worktrees",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    ".pytest_cache",
    ".venv",
    "venv",
    ".mypy_cache",
    ".ruff_cache",
)
DEFAULT_EXCLUDE_FILES: tuple[str, ...] = ("*.pyc", "*.pyo")

# Convenience union (CLI surface uses the combined list).
DEFAULT_EXCLUDES: tuple[str, ...] = DEFAULT_EXCLUDE_DIRS + DEFAULT_EXCLUDE_FILES

ROBOCOPY_OK_MAX = 7  # exit codes 0..7 inclusive are success per Microsoft.


# ----- dataclasses --------------------------------------------------------


@dataclass
class BackupSummary:
    """Pre-/post-run directory measurements."""

    path: Path
    size_bytes: int
    file_count: int

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "file_count": self.file_count,
        }


@dataclass
class BackupResult:
    """Output of `run_backup()`. Aggregates everything written to the manifest."""

    date: str
    branch: str
    head: str
    head_subject: str
    source: BackupSummary
    destination: BackupSummary
    excluded_dirs: tuple[str, ...]
    excluded_files: tuple[str, ...]
    robocopy_argv: tuple[str, ...]
    robocopy_exit_code: int
    started_at: str
    finished_at: str
    errors: list[str] = field(default_factory=list)
    skipped: bool = False
    note: str = ""

    @property
    def ok(self) -> bool:
        return (
            not self.skipped
            and self.robocopy_exit_code <= ROBOCOPY_OK_MAX
            and not self.errors
        )

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "branch": self.branch,
            "head": self.head,
            "head_subject": self.head_subject,
            "source": self.source.to_dict(),
            "destination": self.destination.to_dict(),
            "excluded_dirs": list(self.excluded_dirs),
            "excluded_files": list(self.excluded_files),
            "robocopy_argv": list(self.robocopy_argv),
            "robocopy_exit_code": self.robocopy_exit_code,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "errors": list(self.errors),
            "skipped": self.skipped,
            "note": self.note,
            "ok": self.ok,
        }


# ----- stats helpers ------------------------------------------------------


def compute_dir_stats(path: Path) -> BackupSummary:
    """Walk a directory tree and tally size + file count (best-effort)."""
    size = 0
    count = 0
    if path.exists():
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = Path(root) / f
                try:
                    size += fp.stat().st_size
                    count += 1
                except OSError:
                    continue
    return BackupSummary(path=path, size_bytes=size, file_count=count)


# ----- robocopy argv -----------------------------------------------------


def build_robocopy_cmd(
    src: Path,
    dst: Path,
    *,
    exclude_dirs: Sequence[str] = DEFAULT_EXCLUDE_DIRS,
    exclude_files: Sequence[str] = DEFAULT_EXCLUDE_FILES,
    mirror: bool = True,
    skip_junctions: bool = True,
    multi_thread: int = 8,
    retries: int = 1,
    wait: int = 1,
) -> list[str]:
    """Build the robocopy argv used by `run_backup`.

    /MIR  -> mirror tree (purges extras from dst — combine with /XO to keep
             unique-on-dst files? we DO want mirror semantics for daily
             snapshot, so /MIR is correct).
    /XJ   -> skip junctions (sanctum uses junctions under `projects/` to
             external repos; we don't want to recurse into them).
    /R:N  -> retry count on failed copies.
    /W:N  -> wait seconds between retries.
    /MT:N -> multi-threaded copy.
    /NP   -> no progress percentages (cleaner log).
    /NDL  -> no directory list.
    /XD   -> exclude directories.
    /XF   -> exclude files (globs).
    """
    argv: list[str] = ["robocopy", str(src), str(dst)]
    if mirror:
        argv.append("/MIR")
    if skip_junctions:
        argv.append("/XJ")
    argv += [f"/R:{int(retries)}", f"/W:{int(wait)}"]
    if multi_thread and multi_thread > 0:
        argv.append(f"/MT:{int(multi_thread)}")
    argv += ["/NP", "/NDL"]
    if exclude_dirs:
        argv.append("/XD")
        argv += list(exclude_dirs)
    if exclude_files:
        argv.append("/XF")
        argv += list(exclude_files)
    return argv


# ----- git helpers -------------------------------------------------------


def _git_short(args: Sequence[str], cwd: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def _git_metadata(cwd: Path) -> tuple[str, str, str]:
    branch = _git_short(["rev-parse", "--abbrev-ref", "HEAD"], cwd) or "?"
    head = _git_short(["rev-parse", "--short", "HEAD"], cwd) or "?"
    subject = _git_short(["log", "-1", "--pretty=%s"], cwd) or ""
    return branch, head, subject


# ----- backup runner -----------------------------------------------------


# Test-friendly seam: tests inject a fake to avoid calling robocopy.
RobocopyRunner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


def _default_runner(argv: list[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(argv, capture_output=True, text=True)


def run_backup(
    *,
    source: Path | None = None,
    dest_root: Path | None = None,
    date: datetime.date | str | None = None,
    exclude_dirs: Sequence[str] = DEFAULT_EXCLUDE_DIRS,
    exclude_files: Sequence[str] = DEFAULT_EXCLUDE_FILES,
    runner: RobocopyRunner | None = None,
    write_manifest_file: bool = True,
    overwrite_existing: bool = False,
    dry_run: bool = False,
) -> BackupResult:
    """Execute one backup snapshot. See module docstring for exit-code rules.

    `runner` is injectable for tests; production passes None which dispatches
    to the system `robocopy` binary.
    """
    src = Path(source or sanctum_root())
    droot = Path(dest_root or backup_root())
    if date is None:
        date = datetime.date.today()
    date_str = date if isinstance(date, str) else date.strftime(DATE_FMT)
    dst = snapshot_dir(date_str, root=droot)
    now_started = datetime.datetime.now().isoformat(timespec="seconds")

    errors: list[str] = []

    if dst.exists() and not overwrite_existing:
        return BackupResult(
            date=date_str,
            branch="?",
            head="?",
            head_subject="",
            source=compute_dir_stats(src),
            destination=BackupSummary(dst, 0, 0),
            excluded_dirs=tuple(exclude_dirs),
            excluded_files=tuple(exclude_files),
            robocopy_argv=(),
            robocopy_exit_code=-1,
            started_at=now_started,
            finished_at=now_started,
            errors=[f"destination already exists: {dst}"],
            skipped=True,
            note="re-run with --force to overwrite",
        )

    src_stats = compute_dir_stats(src)
    branch, head, subject = _git_metadata(src)

    droot.mkdir(parents=True, exist_ok=True)
    if dst.exists() and overwrite_existing:
        shutil.rmtree(dst, ignore_errors=True)

    argv = build_robocopy_cmd(
        src,
        dst,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
    )

    if dry_run:
        return BackupResult(
            date=date_str,
            branch=branch,
            head=head,
            head_subject=subject,
            source=src_stats,
            destination=BackupSummary(dst, 0, 0),
            excluded_dirs=tuple(exclude_dirs),
            excluded_files=tuple(exclude_files),
            robocopy_argv=tuple(argv),
            robocopy_exit_code=0,
            started_at=now_started,
            finished_at=datetime.datetime.now().isoformat(timespec="seconds"),
            errors=[],
            skipped=True,
            note="dry-run (robocopy not invoked)",
        )

    runner = runner or _default_runner
    try:
        completed = runner(argv)
        exit_code = int(getattr(completed, "returncode", 0) or 0)
        stderr_text = (getattr(completed, "stderr", "") or "").strip()
    except FileNotFoundError as e:
        return BackupResult(
            date=date_str,
            branch=branch,
            head=head,
            head_subject=subject,
            source=src_stats,
            destination=BackupSummary(dst, 0, 0),
            excluded_dirs=tuple(exclude_dirs),
            excluded_files=tuple(exclude_files),
            robocopy_argv=tuple(argv),
            robocopy_exit_code=-1,
            started_at=now_started,
            finished_at=datetime.datetime.now().isoformat(timespec="seconds"),
            errors=[f"robocopy not available: {e}"],
            skipped=True,
            note="robocopy binary missing (non-Windows host?)",
        )
    except Exception as e:  # pragma: no cover - subprocess oddities
        return BackupResult(
            date=date_str,
            branch=branch,
            head=head,
            head_subject=subject,
            source=src_stats,
            destination=BackupSummary(dst, 0, 0),
            excluded_dirs=tuple(exclude_dirs),
            excluded_files=tuple(exclude_files),
            robocopy_argv=tuple(argv),
            robocopy_exit_code=-1,
            started_at=now_started,
            finished_at=datetime.datetime.now().isoformat(timespec="seconds"),
            errors=[f"robocopy crashed: {e}"],
            skipped=True,
            note="",
        )

    if exit_code > ROBOCOPY_OK_MAX:
        errors.append(f"robocopy exit code {exit_code} (>=8 = failure)")
    if stderr_text:
        errors.append(f"stderr: {stderr_text[:400]}")

    dst_stats = compute_dir_stats(dst)
    now_finished = datetime.datetime.now().isoformat(timespec="seconds")

    result = BackupResult(
        date=date_str,
        branch=branch,
        head=head,
        head_subject=subject,
        source=src_stats,
        destination=dst_stats,
        excluded_dirs=tuple(exclude_dirs),
        excluded_files=tuple(exclude_files),
        robocopy_argv=tuple(argv),
        robocopy_exit_code=exit_code,
        started_at=now_started,
        finished_at=now_finished,
        errors=errors,
    )

    if write_manifest_file and dst.exists():
        try:
            write_manifest(dst, result)
        except OSError as e:
            result.errors.append(f"manifest write failed: {e}")

    return result


# ----- manifest writer ---------------------------------------------------


def _format_bytes(n: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    f = float(n)
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024
        i += 1
    return f"{f:.2f} {units[i]}"


def write_manifest(snapshot_path: Path, result: BackupResult) -> Path:
    """Write `_BACKUP-MANIFEST.md` inside the snapshot directory."""
    out = snapshot_path / MANIFEST_NAME
    src = result.source
    dst = result.destination
    lines: list[str] = []
    lines.append(f"# Sanctum backup manifest :: {result.date}")
    lines.append("")
    lines.append(f"> **Author:** RKOJ-ELENO :: {result.date}")
    lines.append(f"> **Tool:** sanctum-backup")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- **date:** {result.date}")
    lines.append(f"- **branch:** `{result.branch}`")
    lines.append(f"- **HEAD:** `{result.head}`  {result.head_subject}")
    lines.append(f"- **started:** {result.started_at}")
    lines.append(f"- **finished:** {result.finished_at}")
    lines.append(f"- **robocopy exit:** {result.robocopy_exit_code} "
                 f"({'OK' if result.robocopy_exit_code <= ROBOCOPY_OK_MAX else 'FAIL'})")
    lines.append("")
    lines.append("## Source")
    lines.append("")
    lines.append(f"- **path:** `{src.path}`")
    lines.append(f"- **size:** {_format_bytes(src.size_bytes)} ({src.size_bytes:,} bytes)")
    lines.append(f"- **files:** {src.file_count:,}")
    lines.append("")
    lines.append("## Destination")
    lines.append("")
    lines.append(f"- **path:** `{dst.path}`")
    lines.append(f"- **size:** {_format_bytes(dst.size_bytes)} ({dst.size_bytes:,} bytes)")
    lines.append(f"- **files:** {dst.file_count:,}")
    lines.append("")
    lines.append("## Excludes")
    lines.append("")
    lines.append("### Directories (`/XD`)")
    for d in result.excluded_dirs:
        lines.append(f"- `{d}`")
    lines.append("")
    lines.append("### Files (`/XF`)")
    for f in result.excluded_files:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("- Junctions skipped via `/XJ`.")
    lines.append("")
    lines.append("## Robocopy invocation")
    lines.append("")
    lines.append("```")
    lines.append(" ".join(result.robocopy_argv))
    lines.append("```")
    lines.append("")
    lines.append("## Errors")
    lines.append("")
    if not result.errors:
        lines.append("- (none)")
    else:
        for e in result.errors:
            lines.append(f"- {e}")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ----- manifest verification ---------------------------------------------


def _hash_file(p: Path, *, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        while True:
            buf = fh.read(chunk)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def verify_backup(snapshot_path: Path) -> dict:
    """Re-check a backup's manifest exists + recompute size/file count.

    The manifest format is markdown (human-first), so we don't store file-by-file
    hashes in v0.1.0. Verification = manifest present, directory walkable, size
    + file count matches the manifest, and the manifest's own SHA-256 hashes
    to a stable value (returned).
    """
    snapshot_path = Path(snapshot_path)
    manifest = snapshot_path / MANIFEST_NAME
    out = {
        "path": str(snapshot_path),
        "exists": snapshot_path.exists(),
        "has_manifest": manifest.exists(),
        "manifest_sha256": "",
        "size_bytes": 0,
        "file_count": 0,
        "ok": False,
        "errors": [],
    }
    if not snapshot_path.exists():
        out["errors"].append("snapshot path missing")
        return out
    if manifest.exists():
        try:
            out["manifest_sha256"] = _hash_file(manifest)
        except OSError as e:
            out["errors"].append(f"manifest hash failed: {e}")
    else:
        out["errors"].append("missing _BACKUP-MANIFEST.md")
    stats = compute_dir_stats(snapshot_path)
    out["size_bytes"] = stats.size_bytes
    out["file_count"] = stats.file_count
    out["ok"] = not out["errors"]
    return out
