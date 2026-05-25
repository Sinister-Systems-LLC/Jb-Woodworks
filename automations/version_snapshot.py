#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""
version_snapshot.py — Sinister Sanctum disaster-recovery versioning tool.

SemVer scheme: v<MAJOR>.<MINOR>.<PATCH>-<LABEL>
  MAJOR — operator-declared milestone (e.g. v22 = first version-tagged iter)
  MINOR — significant feature land (new subsystem / breaking change to deploy/)
  PATCH — incremental fix / per-iteration milestone
  LABEL — short kebab-case slug ("leo-ready", "crash-fix", "ui-polish")

Operator hard-canonical 2026-05-25 ~06:30Z:
  "we need to satrt taking a versions appraoch to everything we do
   so we always have versions we can revret back to incase diaster strikes"

Subcommands:
  --create <label> [--bump major|minor|patch] [--include-zip] [--push] [--dry-run]
  --list
  --revert <version>            (prints plan, never executes)
  --diff <v1> <v2>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "versions" / "MANIFEST.md"
SNAP_DIR = REPO / "versions" / "snapshots"
BASELINE = "v22.0.0-leo-ready"
BASELINE_PARTS = (22, 0, 0)
ZIP_INCLUDES = ("deploy", "automations", "CLAUDE.md", "_shared-memory/knowledge")

VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)-([a-z0-9][a-z0-9\-]*)$")
ROW_RE = re.compile(r"^\|\s*(\S+)\s*\|\s*(v\d+\.\d+\.\d+-[a-z0-9\-]+)\s*\|")


def _utc() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _run(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(REPO), check=check,
                          capture_output=capture, text=True)


def _git_head_sha() -> str:
    return _run(["git", "rev-parse", "HEAD"]).stdout.strip()[:12]


def _git_tag_exists(tag: str) -> bool:
    res = _run(["git", "tag", "--list", tag], check=False)
    return tag in res.stdout.split()


def _read_manifest_rows() -> list[dict]:
    if not MANIFEST.exists():
        return []
    rows: list[dict] = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        # Reject the table-header separator (|---|---|...|)
        if m.group(1).startswith("---"):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 6:
            continue
        rows.append({
            "utc_ts": parts[0],
            "version": parts[1],
            "commit_sha": parts[2],
            "label": parts[3],
            "headline": parts[4],
            "revert_command": parts[5],
        })
    return rows


def _last_version_parts() -> tuple[int, int, int]:
    rows = _read_manifest_rows()
    for row in reversed(rows):
        m = VERSION_RE.match(row["version"])
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return BASELINE_PARTS


def _next_version(bump: str, label: str) -> str:
    major, minor, patch = _last_version_parts()
    if bump == "major":
        major, minor, patch = major + 1, 0, 0
    elif bump == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"v{major}.{minor}.{patch}-{label}"


def _append_manifest_row(version: str, sha: str, label: str, headline: str) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    row = (f"| {_utc()} | {version} | {sha} | {label} | {headline} | "
           f"`git checkout {version}` |\n")
    with MANIFEST.open("a", encoding="utf-8") as fh:
        fh.write(row)


def _make_zip(version: str) -> Path:
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    zpath = SNAP_DIR / f"{version}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for inc in ZIP_INCLUDES:
            p = REPO / inc
            if not p.exists():
                continue
            if p.is_file():
                zf.write(p, arcname=inc)
                continue
            for fp in p.rglob("*"):
                if fp.is_file():
                    zf.write(fp, arcname=str(fp.relative_to(REPO)))
    return zpath


def cmd_create(args: argparse.Namespace) -> int:
    label = args.create.strip().lower().replace(" ", "-")
    if not re.match(r"^[a-z0-9][a-z0-9\-]*$", label):
        print(f"FAIL: label must be kebab-case alnum, got {label!r}")
        return 2
    version = _next_version(args.bump, label)
    sha = _git_head_sha()
    headline = args.message or f"Snapshot {version} from {sha}"
    plan = [
        f"compute next version -> {version}",
        f"verify tag not present -> {version}",
        f"git tag -a {version} -m '{headline}'",
        f"append manifest row -> {MANIFEST}",
    ]
    if args.include_zip:
        plan.append(f"zip subset -> versions/snapshots/{version}.zip")
    if args.push:
        plan.append(f"git push origin {version}")
    if args.dry_run:
        print("DRY-RUN plan:")
        for step in plan:
            print(f"  - {step}")
        return 0
    if _git_tag_exists(version):
        print(f"already-exists: tag {version} present locally; nothing to do")
        return 0
    _run(["git", "tag", "-a", version, "-m", headline])
    _append_manifest_row(version, sha, label, headline)
    if args.include_zip:
        zpath = _make_zip(version)
        print(f"snapshot zip -> {zpath.relative_to(REPO)}")
    if args.push:
        _run(["git", "push", "origin", version], check=False)
    print(f"OK: created {version} @ {sha}")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    rows = _read_manifest_rows()
    if not rows:
        print("(empty manifest — no versions recorded yet)")
        return 0
    widths = {k: max(len(k), max(len(r[k]) for r in rows)) for k in rows[0]}
    header = "  ".join(k.ljust(widths[k]) for k in rows[0])
    print(header)
    print("-" * len(header))
    for r in rows:
        print("  ".join(r[k].ljust(widths[k]) for k in r))
    return 0


def cmd_revert(args: argparse.Namespace) -> int:
    v = args.revert
    print(f"REVERT PLAN for {v}  (not executed — operator runs the chosen shape)")
    print("")
    print("  (a) Full revert (detached HEAD; create branch to keep changes):")
    print(f"        git fetch --tags && git checkout {v}")
    print("")
    print("  (b) Single-file recovery (overwrite path with version's copy):")
    print(f"        git show {v}:<path> > <path>")
    print("")
    print("  (c) Subsystem extract (stage paths from version into working tree):")
    print(f"        git checkout {v} -- <path>...")
    print("")
    print("  (d) Snapshot zip extract (if --include-zip was used):")
    print(f"        unzip -o versions/snapshots/{v}.zip -d <target-dir>")
    print("")
    print("Verify after revert:")
    print(f"        git log -1 --format='%H %s' {v}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    v1, v2 = args.diff
    res = _run(["git", "diff", f"{v1}..{v2}", "--stat"], check=False)
    sys.stdout.write(res.stdout)
    if res.returncode != 0:
        sys.stderr.write(res.stderr)
    return res.returncode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sinister Sanctum version snapshot tool")
    p.add_argument("--create", metavar="LABEL", help="create a new version snapshot")
    p.add_argument("--bump", choices=("major", "minor", "patch"), default="patch")
    p.add_argument("--message", "-m", help="annotated tag message / headline")
    p.add_argument("--include-zip", action="store_true",
                   help="also write versions/snapshots/<v>.zip")
    p.add_argument("--push", action="store_true", help="git push origin <tag>")
    p.add_argument("--dry-run", action="store_true", help="print plan, do not act")
    p.add_argument("--list", action="store_true", help="print MANIFEST as a table")
    p.add_argument("--revert", metavar="VERSION", help="print revert plan for VERSION")
    p.add_argument("--diff", nargs=2, metavar=("V1", "V2"),
                   help="git diff --stat between two versions")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        return cmd_list(args)
    if args.revert:
        return cmd_revert(args)
    if args.diff:
        return cmd_diff(args)
    if args.create:
        return cmd_create(args)
    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
