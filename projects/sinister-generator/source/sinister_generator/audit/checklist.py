"""Structural pre-save checks — automated portion of docs/ANTI-SLOP.md.

Visual + brand checks still require operator review; this catches the mechanical
failures (truncated file, wrong resolution, missing meta sidecar) before promotion.
"""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import List, Union

PathLike = Union[str, pathlib.Path]

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_JPEG_SIG = b"\xff\xd8\xff"
_MIN_DIMENSION = 1024


@dataclass
class StructuralReport:
    output_path: str
    file_exists: bool = False
    is_recognized_image: bool = False
    file_format: str = "unknown"
    width: int = 0
    height: int = 0
    min_dimension_ok: bool = False
    meta_sidecar_present: bool = False
    issues: List[str] = field(default_factory=list)

    @property
    def passes(self) -> bool:
        return (
            self.file_exists
            and self.is_recognized_image
            and self.min_dimension_ok
            and self.meta_sidecar_present
            and not self.issues
        )


def _read_png_size(head: bytes) -> tuple[int, int]:
    if len(head) < 24:
        return 0, 0
    width = int.from_bytes(head[16:20], "big")
    height = int.from_bytes(head[20:24], "big")
    return width, height


def _read_jpeg_size(data: bytes) -> tuple[int, int]:
    i = 2
    n = len(data)
    while i < n - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            height = int.from_bytes(data[i + 5 : i + 7], "big")
            width = int.from_bytes(data[i + 7 : i + 9], "big")
            return width, height
        seg_len = int.from_bytes(data[i + 2 : i + 4], "big")
        i += 2 + seg_len
    return 0, 0


def structural_check(output_path: PathLike) -> StructuralReport:
    out = pathlib.Path(output_path)
    report = StructuralReport(output_path=str(out))

    if not out.exists():
        report.issues.append("file does not exist")
        return report
    report.file_exists = True

    try:
        with out.open("rb") as f:
            head = f.read(32)
    except OSError as e:
        report.issues.append(f"unreadable: {e}")
        return report

    if head.startswith(_PNG_SIG):
        report.is_recognized_image = True
        report.file_format = "png"
        report.width, report.height = _read_png_size(head)
    elif head.startswith(_JPEG_SIG):
        report.is_recognized_image = True
        report.file_format = "jpeg"
        try:
            data = out.read_bytes()
        except OSError:
            data = b""
        report.width, report.height = _read_jpeg_size(data)
    else:
        report.issues.append("not a recognized PNG or JPEG file")

    smaller_side = min(report.width, report.height) if report.width and report.height else 0
    report.min_dimension_ok = smaller_side >= _MIN_DIMENSION
    if report.is_recognized_image and not report.min_dimension_ok:
        report.issues.append(
            f"min dimension {smaller_side}px is below {_MIN_DIMENSION}px floor"
        )

    sidecar = out.with_suffix(out.suffix + ".meta.json")
    report.meta_sidecar_present = sidecar.exists()
    if not report.meta_sidecar_present:
        report.issues.append("missing .meta.json sidecar")

    return report
