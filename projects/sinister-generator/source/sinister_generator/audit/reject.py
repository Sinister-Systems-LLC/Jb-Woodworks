"""Reject workflow — move a failed generation to <output-dir>/_rejected/ with a note."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import pathlib
import shutil
import time
from dataclasses import dataclass
from typing import Optional, Union

PathLike = Union[str, pathlib.Path]


@dataclass
class RejectResult:
    moved_image: Optional[str] = None
    moved_meta: Optional[str] = None
    reject_note: Optional[str] = None


def move_to_rejected(output_path: PathLike, reason: str) -> RejectResult:
    """Move the image (+ meta sidecar if present) into a sibling `_rejected/` dir
    and write a `.reject.txt` capturing the rejection reason.

    The _rejected/ dir is created if missing. Existing files in _rejected/ with
    the same name get a `.dupN` suffix instead of being overwritten.
    """
    src = pathlib.Path(output_path)
    if not src.exists():
        raise FileNotFoundError(f"no such file: {src}")

    rejected_dir = src.parent / "_rejected"
    rejected_dir.mkdir(parents=True, exist_ok=True)

    dest = _next_available(rejected_dir / src.name)
    shutil.move(str(src), str(dest))
    result = RejectResult(moved_image=str(dest))

    meta_src = src.with_suffix(src.suffix + ".meta.json")
    if meta_src.exists():
        meta_dest = dest.with_suffix(dest.suffix + ".meta.json")
        shutil.move(str(meta_src), str(meta_dest))
        result.moved_meta = str(meta_dest)

    note = dest.with_suffix(dest.suffix + ".reject.txt")
    utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    note.write_text(f"rejected_utc: {utc}\nreason: {reason}\n", encoding="utf-8")
    result.reject_note = str(note)
    return result


def _next_available(path: pathlib.Path) -> pathlib.Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    for i in range(1, 1000):
        candidate = parent / f"{stem}.dup{i}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"too many duplicates of {path}")
