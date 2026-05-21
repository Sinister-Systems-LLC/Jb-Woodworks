"""Mermaid diagram subprocess wrapper for Sinister Forge.

Author: RKOJ-ELENO :: 2026-05-21

Wraps the ``mmdr`` CLI (1jehuang/mermaid-rs-renderer, MIT, 100-1400x faster
than mermaid-cli) into a single :func:`render` call usable from Forge panes,
the REST bridge, or any sibling agent that wants a diagram on disk.

Output lands at ``_shared-memory/forge-diagrams/<sha>.<ext>`` (sha = SHA-256
of the source ``.mmd`` text + format). Re-renders are skipped when the cache
file already exists, so callers can cheaply re-request the same diagram.

Forge plan row: **R8** of ``_shared-memory/plans/sinister-forge-2026-05-21/plan.md``.

Composes with:
    - sinister-forge-harness-pattern brain entry (wrap-don't-replace)
    - forge-bridge-rest-sse-pattern brain entry (bridge endpoint can render)
    - planned RKOJ Forge dashboard tab (renders thumbnails from this cache)

Usage::

    from forge.mermaid_render import render, render_text

    png_path = render_text("flowchart LR\\n  A --> B --> C", fmt="png")
    svg_path = render(Path("diagram.mmd"), fmt="svg")
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Fmt = Literal["png", "svg"]


_SANCTUM_ROOT_ENV = "SINISTER_SANCTUM_ROOT"
_DEFAULT_SANCTUM_ROOT = Path("D:/Sinister Sanctum")
_CACHE_SUBPATH = Path("_shared-memory") / "forge-diagrams"
_MMDR_BIN_ENV = "FORGE_MMDR_BIN"


class MermaidNotInstalledError(RuntimeError):
    """Raised when the mmdr binary cannot be located on PATH or via env."""


class MermaidRenderError(RuntimeError):
    """Raised when mmdr exits non-zero. ``stderr`` is preserved on the exception."""

    def __init__(self, returncode: int, stderr: str) -> None:
        super().__init__(f"mmdr exited {returncode}: {stderr.strip() or '<empty>'}")
        self.returncode = returncode
        self.stderr = stderr


@dataclass(frozen=True)
class RenderResult:
    path: Path
    sha: str
    fmt: Fmt
    cached: bool


def _sanctum_root() -> Path:
    env = os.environ.get(_SANCTUM_ROOT_ENV)
    return Path(env) if env else _DEFAULT_SANCTUM_ROOT


def _cache_dir() -> Path:
    d = _sanctum_root() / _CACHE_SUBPATH
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resolve_mmdr() -> str:
    env = os.environ.get(_MMDR_BIN_ENV)
    if env and Path(env).exists():
        return env
    found = shutil.which("mmdr")
    if found:
        return found
    raise MermaidNotInstalledError(
        "mmdr CLI not found. Install via `cargo install mermaid-rs-renderer` "
        "or `scoop install mmdr`, or set FORGE_MMDR_BIN to an explicit path."
    )


def _digest(text: str, fmt: Fmt) -> str:
    h = hashlib.sha256()
    h.update(fmt.encode("utf-8"))
    h.update(b"\x00")
    h.update(text.encode("utf-8"))
    return h.hexdigest()[:16]


def render_text(source: str, fmt: Fmt = "png") -> RenderResult:
    """Render a Mermaid source string to ``forge-diagrams/<sha>.<fmt>``.

    Returns a :class:`RenderResult` whose ``cached`` flag is ``True`` when
    the digest was already on disk and rendering was skipped.
    """
    sha = _digest(source, fmt)
    out_path = _cache_dir() / f"{sha}.{fmt}"
    if out_path.exists():
        return RenderResult(path=out_path, sha=sha, fmt=fmt, cached=True)

    bin_path = _resolve_mmdr()
    proc = subprocess.run(
        [bin_path, "-o", str(out_path), "-e", fmt],
        input=source,
        text=True,
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0 or not out_path.exists():
        if out_path.exists():
            try:
                out_path.unlink()
            except OSError:
                pass
        raise MermaidRenderError(proc.returncode, proc.stderr)
    return RenderResult(path=out_path, sha=sha, fmt=fmt, cached=False)


def render(path: Path | str, fmt: Fmt = "png") -> RenderResult:
    """Render a ``.mmd`` file. Equivalent to ``render_text(path.read_text(), fmt)``."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return render_text(text, fmt=fmt)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="forge.mermaid_render",
        description="Sinister Forge :: render a Mermaid diagram via mmdr.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a .mmd file. If omitted, read from stdin.",
    )
    parser.add_argument("-e", "--format", choices=("png", "svg"), default="png")
    parser.add_argument(
        "--print-path",
        action="store_true",
        help="Print only the absolute path of the rendered file (script-friendly).",
    )
    args = parser.parse_args()

    if args.input:
        result = render(args.input, fmt=args.format)
    else:
        result = render_text(sys.stdin.read(), fmt=args.format)

    if args.print_path:
        print(result.path)
    else:
        tag = "cached" if result.cached else "rendered"
        print(f"[{tag}] {result.path}  ({result.sha}.{result.fmt})")
