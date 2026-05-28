# Author: RKOJ-ELENO :: 2026-05-28
"""Iter-64 :: verify-brain-refs primitive.

Generalizes the iter-63 doctor.py inline lint (test_iter63.py) into a fleet-
wide primitive. Any agent can now point ``sinister-memory verify-brain-refs``
at a file/dir and learn whether referenced brain entries actually exist on
disk. Same regex, same intent, broader surface.

Cases:
  1. ``extract_refs`` finds every ``_shared-memory/knowledge/<name>.md`` substring
     and returns 1-based line numbers.
  2. ``scan_paths`` against a synthetic fake-sanctum: PRESENT entries land in
     ``present[]``, MISSING entries land in ``missing[]``.
  3. ``scan_paths`` against the real repo + real ``doctor.py`` resolves every
     ref to a present file (matches the iter-63 invariant).
  4. ``scan_paths`` recursive-dir mode: skips ``__pycache__``/``.git`` and only
     considers ``_SCANNABLE_SUFFIXES`` files.
  5. CLI exit code: 0 when all refs resolve, 1 when at least one is missing.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from sinister_memory import verify_brain_refs as vbr


_REPO_ROOT = Path(__file__).resolve().parents[3]
_KNOWLEDGE_DIR = _REPO_ROOT / "_shared-memory" / "knowledge"


# 1.
def test_extract_refs_line_numbers_are_one_based():
    text = "first line no ref\n" \
           "ref here: _shared-memory/knowledge/foo-doctrine-2026-05-25.md plus tail\n" \
           "two on one line _shared-memory/knowledge/a.md and _shared-memory/knowledge/b.md\n"
    refs = vbr.extract_refs(text)
    assert refs == [
        (2, "foo-doctrine-2026-05-25.md"),
        (3, "a.md"),
        (3, "b.md"),
    ]


# 2.
def test_scan_paths_synthetic_partitions_missing_and_present(tmp_path):
    root = tmp_path / "sanctum"
    kdir = root / "_shared-memory" / "knowledge"
    kdir.mkdir(parents=True)
    (kdir / "real-entry-2026-05-28.md").write_text("ok", encoding="utf-8")
    # NOTE intentionally NOT creating "phantom-entry-2026-05-28.md"

    target = root / "src" / "sample.py"
    target.parent.mkdir(parents=True)
    target.write_text(
        textwrap.dedent("""\
            x = 'cat _shared-memory/knowledge/real-entry-2026-05-28.md'
            y = 'cat _shared-memory/knowledge/phantom-entry-2026-05-28.md'
        """),
        encoding="utf-8",
    )

    report = vbr.scan_paths(root=root, targets=[target])

    assert report["scanned_files"] == 1
    assert report["files_with_refs"] == 1
    assert report["total_refs"] == 2
    assert report["missing_count"] == 1
    assert report["present_count"] == 1
    assert report["missing_unique"] == ["phantom-entry-2026-05-28.md"]
    assert report["missing"][0]["ref"] == "phantom-entry-2026-05-28.md"
    assert report["missing"][0]["line"] == 2
    assert report["present"][0]["ref"] == "real-entry-2026-05-28.md"


# 3.
def test_scan_paths_against_real_doctor_py_finds_zero_missing():
    """Iter-63 invariant restated through the iter-64 primitive."""
    target = _REPO_ROOT / "projects" / "sinister-memory" / "src" / \
             "sinister_memory" / "doctor.py"
    if not target.is_file():
        pytest.skip(f"doctor.py not found at {target}")
    report = vbr.scan_paths(root=_REPO_ROOT, targets=[target])
    assert report["total_refs"] >= 3, "doctor.py should ship the iter-63 trio of brain-refs"
    assert report["missing_count"] == 0, (
        f"verify-brain-refs found broken refs in doctor.py: "
        f"{report['missing_unique']}"
    )


# 4.
def test_scan_paths_recursive_dir_skips_pycache_and_non_scannable(tmp_path):
    root = tmp_path / "sanctum"
    kdir = root / "_shared-memory" / "knowledge"
    kdir.mkdir(parents=True)
    (kdir / "only-real.md").write_text("ok", encoding="utf-8")

    src = root / "src"
    src.mkdir(parents=True)
    (src / "a.py").write_text(
        "x = '_shared-memory/knowledge/only-real.md'\n", encoding="utf-8")
    # Non-scannable binary-ish suffix — must be skipped even when it contains a ref.
    (src / "image.png").write_text(
        "_shared-memory/knowledge/should-not-be-scanned.md", encoding="utf-8")
    pyc = src / "__pycache__"
    pyc.mkdir()
    (pyc / "a.cpython-312.pyc").write_text(
        "_shared-memory/knowledge/phantom-cache.md", encoding="utf-8")

    report = vbr.scan_paths(root=root, targets=[src])

    # Only a.py scanned. png + __pycache__ filtered out before regex match.
    assert report["files_with_refs"] == 1
    assert report["missing_count"] == 0
    assert report["present_count"] == 1
    assert all("__pycache__" not in r["file"] for r in report["present"])
    assert all("image.png" not in r["file"] for r in report["present"])


# 5.
def test_cli_exit_code_signals_missing_refs(tmp_path):
    root = tmp_path / "sanctum"
    kdir = root / "_shared-memory" / "knowledge"
    kdir.mkdir(parents=True)
    target = root / "x.py"
    target.write_text(
        "x = '_shared-memory/knowledge/dangling-2026-05-28.md'\n",
        encoding="utf-8",
    )

    src_dir = _REPO_ROOT / "projects" / "sinister-memory" / "src"
    proc = subprocess.run(
        [
            sys.executable, "-m", "sinister_memory",
            "--root", str(root),
            "verify-brain-refs", str(target), "--json",
        ],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(src_dir), "PATH": ""},
    )
    assert proc.returncode == 1, (
        f"expected exit-code 1 for missing ref; got {proc.returncode}\n"
        f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    )
    payload = json.loads(proc.stdout)
    assert payload["missing_count"] == 1
    assert payload["missing_unique"] == ["dangling-2026-05-28.md"]
