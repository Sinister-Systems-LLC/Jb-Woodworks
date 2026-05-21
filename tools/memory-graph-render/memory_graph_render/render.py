# Sinister Sanctum :: memory-graph-render :: backend-detection + render
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Render mermaid output (from forge_memory_bridge.graph()) to PNG using
whichever backend is available on PATH. Always writes the .mmd source +
a CDN-mermaid HTML fallback even when no PNG-renderer backend exists.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    from forge_memory_bridge import graph as fmb_graph
except ImportError:
    fmb_graph = None  # type: ignore

BACKENDS = ("mermaid-rs-renderer", "mmdc", "html-fallback")
_AUTHOR = "RKOJ-ELENO :: 2026-05-21"


def detect_backend() -> str:
    """Return the highest-priority backend available on PATH."""
    if shutil.which("mermaid-rs-renderer"):
        return "mermaid-rs-renderer"
    if shutil.which("mmdc"):
        return "mmdc"
    return "html-fallback"


def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _default_output_dir() -> Path:
    return Path(
        os.environ.get(
            "SINISTER_MEMORY_GRAPHS_DIR",
            r"D:\Sinister Sanctum\inventions\memory-graphs",
        )
    )


def _write_mmd(mermaid_src: str, mmd_path: Path) -> None:
    _ensure_dir(mmd_path)
    mmd_path.write_text(mermaid_src, encoding="utf-8")


def _write_html_fallback(mermaid_src: str, html_path: Path, title: str) -> None:
    _ensure_dir(html_path)
    html = f"""<!doctype html>
<!-- Sinister Sanctum :: memory-graph fallback render :: {_AUTHOR} -->
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ background: #0d0d12; color: #c8c8d0; font-family: 'Cascadia Code', 'Consolas', monospace; margin: 0; padding: 24px; }}
    h1   {{ color: #7A3DD4; margin: 0 0 16px 0; }}
    .meta {{ color: #5a8898; font-size: 12px; margin-bottom: 24px; }}
    .mermaid {{ background: #15151c; padding: 16px; border-radius: 6px; }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">Sinister Sanctum :: memory-graph-render (HTML fallback) :: rendered client-side by mermaid@10 CDN</div>
  <div class="mermaid">{mermaid_src}</div>
  <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")


def _run_mmdc(mmd_path: Path, png_path: Path) -> tuple[bool, str]:
    """Render via @mermaid-js/mermaid-cli (mmdc). Returns (ok, stderr)."""
    try:
        proc = subprocess.run(
            ["mmdc", "-i", str(mmd_path), "-o", str(png_path), "-b", "transparent"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        ok = proc.returncode == 0 and png_path.exists()
        return ok, (proc.stderr or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def _run_mermaid_rs(mmd_path: Path, png_path: Path) -> tuple[bool, str]:
    """Render via mermaid-rs-renderer. CLI shape may vary per release."""
    try:
        proc = subprocess.run(
            ["mermaid-rs-renderer", str(mmd_path), "--output", str(png_path), "--format", "png"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        ok = proc.returncode == 0 and png_path.exists()
        return ok, (proc.stderr or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def render(
    mermaid_src: str | None = None,
    *,
    namespace: str | None = None,
    query: str | None = None,
    output: str | Path | None = None,
    mmd_only: bool = False,
    title: str | None = None,
) -> dict:
    """Render a mermaid graph to PNG (+.mmd + .html fallback).

    Either provide mermaid_src directly OR (namespace, query) to pull from
    forge_memory_bridge.graph(). If output is None, write into
    inventions/memory-graphs/<UTC>-<namespace>.<ext>.

    Returns: { backend, mmd, png?, html?, error? }
    """
    if mermaid_src is None:
        if fmb_graph is None:
            return {
                "backend": None,
                "error": "forge_memory_bridge not importable + no mermaid_src given",
            }
        mermaid_src = fmb_graph(namespace=namespace, query=query)

    if not mermaid_src.strip():
        mermaid_src = "flowchart LR\n    empty[No memories matched]"

    out_dir = _default_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    if output is None:
        stem = f"{_stamp()}-{(namespace or 'all')}"
        png_path = out_dir / f"{stem}.png"
    elif str(output) == "-":
        # stdout-mode: just return the mermaid src
        return {"backend": "stdout", "mmd": None, "png": None, "html": None, "src": mermaid_src}
    else:
        png_path = Path(output)
        if png_path.suffix.lower() != ".png":
            png_path = png_path.with_suffix(".png")

    mmd_path = png_path.with_suffix(".mmd")
    html_path = png_path.with_suffix(".html")
    label = title or f"sinister-memory-graph :: {namespace or 'all'}"

    _write_mmd(mermaid_src, mmd_path)
    _write_html_fallback(mermaid_src, html_path, label)

    if mmd_only:
        return {"backend": "mmd-only", "mmd": str(mmd_path), "html": str(html_path), "png": None}

    backend = detect_backend()
    result: dict = {"backend": backend, "mmd": str(mmd_path), "html": str(html_path)}

    if backend == "mermaid-rs-renderer":
        ok, err = _run_mermaid_rs(mmd_path, png_path)
    elif backend == "mmdc":
        ok, err = _run_mmdc(mmd_path, png_path)
    else:
        ok, err = False, "no PNG renderer on PATH; .mmd + .html fallback only"

    if ok:
        result["png"] = str(png_path)
    else:
        result["png"] = None
        result["error"] = err

    return result
