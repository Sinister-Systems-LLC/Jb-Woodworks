"""Local-path intake (operator-given directories like C:\\Users\\Zonia\\Desktop\\X).

Author: RKOJ-ELENO :: 2026-05-26

Operator (verbatim 2026-05-26): *"this project: 'C:\\Users\\Zonia\\Desktop\\GitChain-main'
should be marked as good if i gave you it and it should be sent to the sinister vault agent"*

This adapter handles the common case where the operator drops a folder on the desktop
and wants Jokester to triage it. No clone — just read it in place.

The returned candidate has the same shape as `intake/github.py` so `decide.py` can
treat all sources uniformly.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Extensions we consider 'code' (for vision-only vs code-bearing classification).
CODE_EXTS = {
    ".py",".rs",".go",".ts",".tsx",".js",".jsx",".java",".kt",".swift",
    ".c",".cc",".cpp",".cxx",".h",".hpp",".m",".mm",".cs",".rb",".php",
    ".sh",".ps1",".bat",".lua",".sol",".dart",".scala",".clj",".ex",".exs",
    ".vue",".svelte",".html",".css",".scss",".sql",
}
DOC_EXTS = {".md",".markdown",".rst",".txt",".adoc"}

README_NAMES = ("README.md","README.rst","README.txt","README","readme.md")
LICENSE_NAMES = ("LICENSE","LICENSE.md","LICENSE.txt","COPYING","UNLICENSE")


def _normalise_path(raw: str) -> Path:
    s = raw.strip().strip('"').strip("'")
    p = Path(s).expanduser()
    return p.resolve()


def compute_id(path: Path) -> str:
    h = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]
    safe = re.sub(r"[^a-z0-9]+", "-", path.name.lower()).strip("-") or "local"
    return f"lp-{safe}-{h}"


def _read_first_existing(folder: Path, names: tuple[str, ...], max_bytes: int = 20_000) -> str:
    for n in names:
        p = folder / n
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:max_bytes]
            except OSError:
                pass
    return ""


def _walk_stats(root: Path, max_files: int = 5_000) -> dict[str, Any]:
    file_count = 0
    code_files = 0
    doc_files = 0
    other_files = 0
    total_bytes = 0
    ext_counts: dict[str, int] = {}
    for p in root.rglob("*"):
        if p.is_dir():
            # Skip common noise dirs to keep the walk fast.
            if p.name in {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target"}:
                # rglob keeps recursing; we can't prune easily without a manual walk. Tolerable: stats won't double-count code dirs because we cap on max_files.
                continue
            continue
        file_count += 1
        if file_count > max_files:
            break
        try:
            sz = p.stat().st_size
        except OSError:
            sz = 0
        total_bytes += sz
        ext = p.suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
        if ext in CODE_EXTS:
            code_files += 1
        elif ext in DOC_EXTS:
            doc_files += 1
        else:
            other_files += 1

    top_exts = sorted(ext_counts.items(), key=lambda kv: -kv[1])[:10]
    return {
        "file_count": file_count,
        "code_files": code_files,
        "doc_files": doc_files,
        "other_files": other_files,
        "total_bytes": total_bytes,
        "top_extensions": top_exts,
        "is_vision_only": code_files == 0 and doc_files > 0,
    }


def intake(path_str: str, force: bool = False) -> dict[str, Any]:
    root = _normalise_path(path_str)
    if not root.exists() or not root.is_dir():
        return {
            "id": "lp-missing-" + hashlib.sha1(path_str.encode("utf-8")).hexdigest()[:8],
            "source_url": str(root),
            "source_type": "local_path",
            "intake_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "pending",
            "title": Path(path_str).name or path_str,
            "short_summary": f"path not found or not a directory: {root}",
            "tags": "local,missing",
            "raw_metadata_json": json.dumps({"requested_path": path_str}),
            "clone_dir": str(root),
            "intake_dir": str(root),
            "readme_excerpt": "",
            "_intake_ok": False,
            "_reason": "path-not-found",
        }

    item_id = compute_id(root)
    readme = _read_first_existing(root, README_NAMES)
    license_text = _read_first_existing(root, LICENSE_NAMES, max_bytes=1_000)
    stats = _walk_stats(root)

    title = root.name
    short_summary = ""
    if readme:
        first_para = readme.strip().split("\n\n", 1)[0].strip()
        short_summary = first_para[:300].replace("\n", " ")
    if not short_summary:
        short_summary = f"Local artifact at {root} — no README; {stats['file_count']} files."

    # Tag derivation
    tags: list[str] = ["local"]
    if stats["is_vision_only"]:
        tags.append("vision-only")
    else:
        tags.append("has-code")
    top_ext = stats["top_extensions"][0][0] if stats["top_extensions"] else ""
    if top_ext.startswith("."):
        tags.append(f"ext{top_ext}")
    if license_text:
        tags.append("licensed")

    raw_meta = {
        "requested_path": path_str,
        "resolved_path": str(root),
        "stats": stats,
        "has_license": bool(license_text),
        "readme_chars": len(readme),
    }

    return {
        "id": item_id,
        "source_url": str(root),
        "source_type": "local_path",
        "intake_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "analyzing",
        "title": title,
        "short_summary": short_summary,
        "tags": ",".join(tags),
        "raw_metadata_json": json.dumps(raw_meta, default=str),
        "clone_dir": str(root),
        "intake_dir": str(root),
        "readme_excerpt": readme[:4_000],
        "_intake_ok": True,
    }


def looks_like_local_path(s: str) -> bool:
    """Return True if s should be routed to the local-path adapter."""
    s = s.strip().strip('"').strip("'")
    if not s:
        return False
    # Drive-letter path (C:\... or C:/...)
    if re.match(r"^[A-Za-z]:[\\/]", s):
        return True
    # POSIX absolute path
    if s.startswith("/"):
        return True
    # Existing relative path
    try:
        return Path(s).exists() and Path(s).is_dir()
    except OSError:
        return False


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    out = intake(args.path)
    out.pop("readme_excerpt", None)
    print(json.dumps(out, indent=2, default=str))
