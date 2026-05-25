#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# sanctum_custodian.py - autonomous fleet hygiene for Sinister Sanctum.
#
# Replaces operator manual cleanup. Per "no-bat-no-ps1-do-it-for-me" doctrine
# this is Python 3 stdlib-only. Scheduled hourly via Windows schtasks (run install
# action once; uses schtasks.exe directly, no .ps1 wrapper).
#
# Actions:
#   audit            scan repo for hygiene violations, print punch list
#   clean            rotate oversized JSONL + quarantine oversized inbox JSON
#                    (--dry-run by default; pass --apply to perform writes)
#   claude-md-trim   audit CLAUDE.md, list extraction candidates (>2k chars
#                    in any "Operator hard-canonical" block). Read-only.
#   install-task     install Windows scheduled task SinisterCustodianHourly
#                    (audit --quiet every hour, starting :05).
#
# Smoke:  python sanctum_custodian.py audit
#         python sanctum_custodian.py clean --dry-run
#
# Composes with:
#   - safe-quality-loops doctrine (reversibility wall via _archive/, not delete)
#   - sanctum-scope-discipline (operates on _shared-memory/, not per-project)
#   - no-bullshit doctrine (precise verbs in punch list; smoke-tested before claim)

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED = REPO_ROOT / "_shared-memory"
ARCHIVE_ROOT = SHARED / "_archive"
ARCHIVE_OVERSIZED_INBOX = ARCHIVE_ROOT / "oversized-inbox"

# Thresholds (bytes / chars / rows)
THRESH_FILE_SIZE = 50 * 1024 * 1024            # 50 MB
THRESH_JSONL_SIZE = 100 * 1024 * 1024          # 100 MB
THRESH_CLAUDE_MD = 38_000                       # chars
THRESH_BRAIN_INDEX_ROWS = 150
THRESH_PROGRESS_SIZE = 300 * 1024              # 300 KB
KEEP_TAIL_FRACTION = 0.20                       # rotate: keep tail 20%, archive 80%
KEEP_FLEET_UPDATES_TAIL_ROWS = 500              # special-case for fleet-updates


def utc_today_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def utc_ts_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# -- scanners ---------------------------------------------------------------

def scan_big_files(root: Path, threshold: int) -> list[tuple[Path, int]]:
    """Return [(path, size_bytes), ...] for files >threshold under root.

    Per sanctum-scope-discipline, default skip list excludes per-project
    directories — custodian operates on sanctum-owned paths (_shared-memory,
    automations, docs, top-level CLAUDE.md). Per-project hygiene is owned
    by the per-project lane.
    """
    hits = []
    skip_dirs = {".git", "node_modules", "__pycache__", "_archive",
                 "projects", "_vault", ".next", "build", "dist",
                 "tmp-worktrees-2026-05-21", "venv", ".venv"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            fp = Path(dirpath) / fname
            try:
                sz = fp.stat().st_size
            except OSError:
                continue
            if sz > threshold:
                hits.append((fp, sz))
    return sorted(hits, key=lambda x: -x[1])


def scan_big_jsonl(root: Path, threshold: int) -> list[tuple[Path, int]]:
    """JSONL files exceeding threshold."""
    hits = []
    for fp, sz in scan_big_files(root, threshold):
        if fp.suffix == ".jsonl":
            hits.append((fp, sz))
    return hits


def scan_claude_md(repo: Path) -> tuple[int, bool]:
    p = repo / "CLAUDE.md"
    if not p.exists():
        return 0, False
    size = len(p.read_text(encoding="utf-8"))
    return size, size > THRESH_CLAUDE_MD


def scan_brain_index(shared: Path) -> tuple[int, bool]:
    p = shared / "knowledge" / "_INDEX.md"
    if not p.exists():
        return 0, False
    rows = sum(1 for ln in p.read_text(encoding="utf-8").splitlines()
               if ln.strip().startswith("|") and not ln.strip().startswith("|---")
               and not ln.strip().startswith("| Topic"))
    return rows, rows > THRESH_BRAIN_INDEX_ROWS


def scan_progress(shared: Path) -> list[tuple[Path, int]]:
    """Oversized PROGRESS files."""
    progress_dir = shared / "PROGRESS"
    hits = []
    if not progress_dir.exists():
        return hits
    for fp in progress_dir.glob("*.md"):
        try:
            sz = fp.stat().st_size
        except OSError:
            continue
        if sz > THRESH_PROGRESS_SIZE:
            hits.append((fp, sz))
    return sorted(hits, key=lambda x: -x[1])


# -- actions ----------------------------------------------------------------

def action_audit(quiet: bool = False) -> int:
    """Print hygiene punch list. Exit 0 if clean, 1 if violations."""
    violations = []

    big_files = scan_big_files(REPO_ROOT, THRESH_FILE_SIZE)
    big_jsonl = scan_big_jsonl(REPO_ROOT, THRESH_JSONL_SIZE)
    claude_size, claude_bad = scan_claude_md(REPO_ROOT)
    brain_rows, brain_bad = scan_brain_index(SHARED)
    big_progress = scan_progress(SHARED)

    if big_files:
        violations.append(("files>50MB", big_files))
    if big_jsonl:
        violations.append(("jsonl>100MB", big_jsonl))
    if claude_bad:
        violations.append(("CLAUDE.md>38k", [(REPO_ROOT / "CLAUDE.md", claude_size)]))
    if brain_bad:
        violations.append(("brain-index>150rows", [(SHARED / "knowledge" / "_INDEX.md", brain_rows)]))
    if big_progress:
        violations.append(("progress>300KB", big_progress))

    if quiet and not violations:
        return 0

    print(f"=== sanctum_custodian audit @ {utc_ts_stamp()} ===")
    if not violations:
        print("  CLEAN: no hygiene violations detected.")
        return 0

    for label, hits in violations:
        print(f"\n[{label}]  {len(hits)} item(s)")
        for fp, val in hits[:20]:
            try:
                rel = fp.relative_to(REPO_ROOT)
            except ValueError:
                rel = fp
            if label == "CLAUDE.md>38k":
                print(f"  {val:>12,} chars  {rel}")
            elif label == "brain-index>150rows":
                print(f"  {val:>12,} rows   {rel}")
            else:
                mb = val / (1024 * 1024)
                print(f"  {val:>12,} B ({mb:6.2f} MB)  {rel}")
    print()
    return 1


def rotate_jsonl(fp: Path, apply: bool, keep_tail_rows: int | None = None,
                 keep_tail_fraction: float = KEEP_TAIL_FRACTION) -> dict:
    """Rotate a big JSONL: archive oldest portion, keep tail live.

    If keep_tail_rows is set, keep that exact count of last rows. Otherwise
    keep keep_tail_fraction of rows (default 20%).
    """
    if not fp.exists():
        return {"file": str(fp), "skipped": "missing"}

    # Count rows cheaply by lines.
    with fp.open("rb") as fh:
        total_rows = sum(1 for _ in fh)

    if keep_tail_rows is not None:
        keep = min(keep_tail_rows, total_rows)
    else:
        keep = max(1, int(total_rows * keep_tail_fraction))

    archive_count = total_rows - keep
    if archive_count <= 0:
        return {"file": str(fp), "skipped": "no-rotation-needed", "rows": total_rows}

    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_ROOT / f"{fp.stem}-{utc_today_stamp()}{fp.suffix}"
    suffix_n = 0
    while archive_path.exists():
        suffix_n += 1
        archive_path = ARCHIVE_ROOT / f"{fp.stem}-{utc_today_stamp()}-{suffix_n}{fp.suffix}"

    if not apply:
        return {"file": str(fp), "would-archive-rows": archive_count,
                "would-keep-rows": keep, "archive-target": str(archive_path),
                "dry-run": True}

    # Streaming rotate: write archive+ kept rows to temp, then swap.
    tmp_kept = fp.with_suffix(fp.suffix + ".keep.tmp")
    with fp.open("rb") as fh, archive_path.open("wb") as arc, tmp_kept.open("wb") as keep_fh:
        for i, line in enumerate(fh):
            if i < archive_count:
                arc.write(line)
            else:
                keep_fh.write(line)
    # Atomic-ish swap on Windows: remove + rename.
    backup = fp.with_suffix(fp.suffix + ".bak")
    if backup.exists():
        backup.unlink()
    fp.rename(backup)
    tmp_kept.rename(fp)
    backup.unlink()

    return {"file": str(fp), "archived-rows": archive_count, "kept-rows": keep,
            "archive-path": str(archive_path), "applied": True}


def quarantine_oversized_json(fp: Path, apply: bool) -> dict:
    """Move an oversized single-file inbox JSON to _archive/oversized-inbox/.

    First reads first 500 + last 500 bytes to diagnose. Then moves wholesale.
    """
    if not fp.exists():
        return {"file": str(fp), "skipped": "missing"}

    sz = fp.stat().st_size
    head = b""
    tail = b""
    try:
        with fp.open("rb") as fh:
            head = fh.read(500)
            if sz > 1000:
                fh.seek(-500, 2)
                tail = fh.read(500)
    except OSError as e:
        return {"file": str(fp), "skipped": f"read-error: {e}"}

    diag = {
        "file": str(fp),
        "size_bytes": sz,
        "head_500_preview": head.decode("utf-8", errors="replace")[:300],
        "tail_500_preview": tail.decode("utf-8", errors="replace")[:300],
    }

    if not apply:
        diag["dry-run"] = True
        diag["would-move-to"] = str(ARCHIVE_OVERSIZED_INBOX / fp.name)
        return diag

    ARCHIVE_OVERSIZED_INBOX.mkdir(parents=True, exist_ok=True)
    target = ARCHIVE_OVERSIZED_INBOX / fp.name
    if target.exists():
        target = ARCHIVE_OVERSIZED_INBOX / f"{fp.stem}-{utc_ts_stamp()}{fp.suffix}"
    shutil.move(str(fp), str(target))

    # Note explaining the move.
    note_path = target.with_suffix(target.suffix + ".QUARANTINE-NOTE.md")
    note_path.write_text(
        f"# Quarantine note\n\n"
        f"- Author: RKOJ-ELENO :: {utc_today_stamp()}\n"
        f"- Quarantined by: sanctum_custodian.py\n"
        f"- Original path: `{fp}`\n"
        f"- Size: {sz:,} bytes ({sz / (1024*1024):.2f} MB)\n"
        f"- Reason: exceeded {THRESH_FILE_SIZE:,} byte inbox threshold\n"
        f"  (likely runaway-loop / mojibake-explosion bug in producer).\n\n"
        f"## Head 500B preview\n```\n{diag['head_500_preview']}\n```\n\n"
        f"## Tail 500B preview\n```\n{diag['tail_500_preview']}\n```\n",
        encoding="utf-8",
    )

    diag["applied"] = True
    diag["moved-to"] = str(target)
    diag["note-path"] = str(note_path)
    return diag


def action_clean(apply: bool) -> int:
    """Rotate oversized JSONL + quarantine oversized inbox JSON.

    --apply executes; default is dry-run preview.
    """
    print(f"=== sanctum_custodian clean ({'APPLY' if apply else 'DRY-RUN'}) @ {utc_ts_stamp()} ===")
    results = []

    # JSONL rotation.
    big_jsonl = scan_big_jsonl(REPO_ROOT, THRESH_JSONL_SIZE)
    for fp, sz in big_jsonl:
        # fleet-updates.jsonl special-case: keep last 500 rows.
        if fp.name == "fleet-updates.jsonl":
            r = rotate_jsonl(fp, apply, keep_tail_rows=KEEP_FLEET_UPDATES_TAIL_ROWS)
        else:
            r = rotate_jsonl(fp, apply)
        results.append(("jsonl-rotate", r))

    # Oversized inbox JSON quarantine.
    inbox_root = SHARED / "inbox"
    if inbox_root.exists():
        for fp, sz in scan_big_files(inbox_root, THRESH_FILE_SIZE):
            if fp.suffix == ".json":
                r = quarantine_oversized_json(fp, apply)
                results.append(("inbox-quarantine", r))

    if not results:
        print("  CLEAN: nothing to clean.")
        return 0

    for kind, r in results:
        print(f"\n[{kind}]")
        for k, v in r.items():
            if isinstance(v, str) and len(v) > 200:
                v = v[:200] + "..."
            print(f"  {k}: {v}")
    return 0


def action_claude_md_trim() -> int:
    """Read-only audit: which 'Operator hard-canonical' blocks are >2k chars
    and would benefit from extraction to a brain entry?"""
    p = REPO_ROOT / "CLAUDE.md"
    if not p.exists():
        print("CLAUDE.md missing")
        return 1
    text = p.read_text(encoding="utf-8")
    total = len(text)
    print(f"=== CLAUDE.md trim audit @ {utc_ts_stamp()} ===")
    print(f"  total chars: {total:,}  (threshold: {THRESH_CLAUDE_MD:,})")

    # Split on '## ' headings.
    chunks = []
    current_header = None
    current_lines = []
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            if current_header is not None:
                chunks.append((current_header, "".join(current_lines)))
            current_header = line.rstrip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_header is not None:
        chunks.append((current_header, "".join(current_lines)))

    # Rank by size, flag candidates.
    candidates = []
    for header, body in chunks:
        sz = len(body)
        if sz > 2000 and "hard-canonical" in header.lower():
            candidates.append((header, sz, body))
    candidates.sort(key=lambda x: -x[1])

    print(f"\n  hard-canonical blocks >2k chars: {len(candidates)}")
    for header, sz, body in candidates:
        # Try to find existing brain pointer.
        brain_ref = ""
        for line in body.splitlines():
            if "_shared-memory/knowledge/" in line and ".md" in line:
                brain_ref = line.strip()[:120]
                break
        print(f"\n  [{sz:>5,} chars]  {header}")
        if brain_ref:
            print(f"     pointer: {brain_ref}")
        else:
            print(f"     pointer: NONE (would need new brain entry)")

    total_extractable = sum(sz for _, sz, _ in candidates)
    print(f"\n  total extractable: {total_extractable:,} chars")
    print(f"  if trimmed to 400-char stubs each: ~{len(candidates) * 400:,} chars retained")
    saved = total_extractable - len(candidates) * 400
    print(f"  net savings: ~{saved:,} chars")
    print(f"  projected new size: ~{total - saved:,} chars")
    return 0


def action_install_task() -> int:
    """Install SinisterCustodianHourly via schtasks.exe (direct call, no .ps1)."""
    python_exe = sys.executable
    script_path = str(Path(__file__).resolve())
    # /TR must be one string; quote the python exe + script.
    tr = f'"{python_exe}" "{script_path}" audit --quiet'
    cmd = [
        "schtasks.exe", "/Create",
        "/TN", "SinisterCustodianHourly",
        "/SC", "HOURLY",
        "/ST", "00:05",
        "/TR", tr,
        "/F",
    ]
    print(f"=== installing schtask SinisterCustodianHourly ===")
    print(f"  cmd: {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"  FAILED: {e}")
        return 2
    print(f"  stdout: {r.stdout.strip()}")
    if r.stderr:
        print(f"  stderr: {r.stderr.strip()}")
    print(f"  exit: {r.returncode}")
    return r.returncode


# -- main -------------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Sinister Sanctum autonomous fleet hygiene custodian.",
    )
    sub = ap.add_subparsers(dest="action", required=True)

    p_audit = sub.add_parser("audit", help="scan hygiene; exit 1 if violations")
    p_audit.add_argument("--quiet", action="store_true",
                         help="suppress output when clean")

    p_clean = sub.add_parser("clean", help="rotate JSONL + quarantine inbox JSON")
    grp = p_clean.add_mutually_exclusive_group()
    grp.add_argument("--dry-run", action="store_true",
                     help="(default) preview only")
    grp.add_argument("--apply", action="store_true",
                     help="actually do destructive work")

    sub.add_parser("claude-md-trim", help="audit CLAUDE.md extraction candidates")
    sub.add_parser("install-task", help="install hourly Windows scheduled task")

    args = ap.parse_args(argv)

    if args.action == "audit":
        return action_audit(quiet=args.quiet)
    if args.action == "clean":
        return action_clean(apply=args.apply)
    if args.action == "claude-md-trim":
        return action_claude_md_trim()
    if args.action == "install-task":
        return action_install_task()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
