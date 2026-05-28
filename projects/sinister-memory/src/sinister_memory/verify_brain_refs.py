# Author: RKOJ-ELENO :: 2026-05-28
"""Sinister Memory :: verify-brain-refs.

Scans target files (or directories) for references to brain entries under
``_shared-memory/knowledge/<name>.md`` and reports which of those references
resolve to real files on disk. Generalizes the iter-63 doctor.py lint pattern
into a fleet-wide primitive every lane can adopt.

Why: docs/recipes/automations that paste cat instructions referencing brain
entries silently rot when the referenced entry is renamed, archived, or never
existed (the iter-63 bug). Per
``no-bullshit-tested-before-claimed-doctrine-2026-05-23`` Rule 8 (quality
limits), every cross-reference in shipped recipes must point at a verified-
present file.

Scope: ANY text file (Python source, Markdown, PowerShell, JSON) is scanned
by raw-string match — no language-specific parser needed. The same regex used
by tests/test_iter63.py is the canonical extraction rule.

Usage:
    from sinister_memory.verify_brain_refs import scan_paths
    report = scan_paths(root=Path("D:/Sinister Sanctum"),
                       targets=[Path("src/sinister_memory/doctor.py")])
    # report["missing"] -> list of (target_file, line_no, brain_ref) tuples
    # report["present"] -> same shape for refs that resolve

CLI:
    sinister-memory verify-brain-refs src/sinister_memory/doctor.py
    sinister-memory verify-brain-refs src/ automations/ --json
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

# Same regex as tests/test_iter63.py — keep them in lockstep.
BRAIN_REF_RE = re.compile(r"_shared-memory/knowledge/([A-Za-z0-9._\-]+\.md)")

# File extensions worth scanning when a directory is passed.
_SCANNABLE_SUFFIXES = frozenset({
    ".py", ".md", ".ps1", ".json", ".jsonl", ".txt", ".yml", ".yaml",
    ".toml", ".sh", ".bat", ".rs", ".ts", ".js",
})


def extract_refs(text: str) -> list[tuple[int, str]]:
    """Return ``[(line_no, brain_ref_filename), ...]`` for each match.

    Line numbers are 1-based to align with editor conventions and pytest output.
    """
    out: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in BRAIN_REF_RE.finditer(line):
            out.append((line_no, match.group(1)))
    return out


def iter_target_files(targets: Iterable[Path]) -> list[Path]:
    """Expand mixed file/dir targets into a sorted list of files to scan."""
    out: list[Path] = []
    seen: set[Path] = set()
    for t in targets:
        t = Path(t)
        if not t.exists():
            continue
        if t.is_file():
            if t not in seen:
                out.append(t)
                seen.add(t)
        else:
            for child in t.rglob("*"):
                if not child.is_file():
                    continue
                if child.suffix.lower() not in _SCANNABLE_SUFFIXES:
                    continue
                # Skip vendored / build / cache trees.
                parts = set(child.parts)
                if parts & {"__pycache__", ".git", "node_modules", "_archive",
                             "dist", "build", ".venv", "venv", ".mypy_cache"}:
                    continue
                if child not in seen:
                    out.append(child)
                    seen.add(child)
    return sorted(out)


def scan_paths(
    root: Path,
    targets: Iterable[Path],
    knowledge_dir: Path | None = None,
) -> dict:
    """Scan ``targets`` and return a report on brain-entry references.

    Args:
        root: Sanctum root (used to derive ``knowledge_dir`` default + render
            target paths as repo-relative when possible).
        targets: files or directories to scan.
        knowledge_dir: override; default is ``root/_shared-memory/knowledge``.

    Returns:
        ``{
            "knowledge_dir": str,
            "scanned_files": int,
            "files_with_refs": int,
            "total_refs": int,
            "unique_refs": int,
            "missing_count": int,
            "present_count": int,
            "missing": [{"file": ..., "line": ..., "ref": ...}, ...],
            "present": [{"file": ..., "line": ..., "ref": ...}, ...],
            "missing_unique": [<filename>, ...]
        }``

    ``file`` is rendered repo-relative when ``root`` is a prefix; otherwise
    the absolute path is kept.
    """
    root = Path(root).resolve()
    kdir = (knowledge_dir or (root / "_shared-memory" / "knowledge")).resolve()

    files = iter_target_files(targets)
    missing: list[dict] = []
    present: list[dict] = []
    files_with_refs = 0
    unique_refs: set[str] = set()
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        refs = extract_refs(text)
        if not refs:
            continue
        files_with_refs += 1
        try:
            display = str(f.resolve().relative_to(root))
        except ValueError:
            display = str(f.resolve())
        for line_no, name in refs:
            unique_refs.add(name)
            row = {"file": display.replace("\\", "/"), "line": line_no, "ref": name}
            if (kdir / name).is_file():
                present.append(row)
            else:
                missing.append(row)

    missing_unique = sorted({m["ref"] for m in missing})
    return {
        "knowledge_dir": str(kdir).replace("\\", "/"),
        "scanned_files": len(files),
        "files_with_refs": files_with_refs,
        "total_refs": len(missing) + len(present),
        "unique_refs": len(unique_refs),
        "missing_count": len(missing),
        "present_count": len(present),
        "missing": missing,
        "present": present,
        "missing_unique": missing_unique,
    }
