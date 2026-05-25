# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: auto_save.

Per-agent iter-close persistence. Each call writes one markdown file to
`<root>/_shared-memory/sinister-memory/per-agent/<slug>/iter-<N>.md` with
frontmatter (timestamp, slug, iter, len), then optionally re-indexes.

Public API:
  save_iter_close(slug, iter_num, summary, root, do_reindex=False) -> Path
  list_iters(slug, root) -> list[Path]
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,64}$")


def _validate_slug(slug: str) -> str:
    slug_l = slug.strip().lower()
    if not SLUG_RE.match(slug_l):
        raise ValueError(f"invalid slug: {slug!r} (must match {SLUG_RE.pattern})")
    return slug_l


def per_agent_dir(slug: str, root: Path) -> Path:
    return Path(root) / "_shared-memory" / "sinister-memory" / "per-agent" / _validate_slug(slug)


def save_iter_close(
    slug: str,
    iter_num: int,
    summary: str,
    root: Path,
    do_reindex: bool = False,
) -> Path:
    """Write the iter-close memory file and return its path.

    The file is markdown with a YAML-ish frontmatter block. Body is the summary
    verbatim. Bash-safe: backticks in the summary are escaped so PowerShell
    here-strings consuming the file later don't break.
    """
    slug_l = _validate_slug(slug)
    if not isinstance(iter_num, int) or iter_num < 0:
        raise ValueError(f"iter_num must be non-negative int, got {iter_num!r}")

    summary = summary or "(no summary)"
    # Defensive: clamp absurdly long summaries
    if len(summary) > 16_000:
        summary = summary[:16_000] + "\n\n... [truncated]"

    out_dir = per_agent_dir(slug_l, root)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"iter-{iter_num:04d}.md"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = (
        f"---\n"
        f"author: RKOJ-ELENO\n"
        f"slug: {slug_l}\n"
        f"iter: {iter_num}\n"
        f"saved_at: {now}\n"
        f"length: {len(summary)}\n"
        f"---\n\n"
        f"# {slug_l} :: iter-{iter_num:04d}\n\n"
        f"{summary}\n"
    )
    out_path.write_text(body, encoding="utf-8")

    if do_reindex:
        # Local import to avoid circular reference at module load
        from . import indexer

        indexer.build(Path(root), indexer.default_db_path(root))

    return out_path


def list_iters(slug: str, root: Path) -> list[Path]:
    """Return iter-*.md files for the slug, newest-first by iter number."""
    d = per_agent_dir(slug, root)
    if not d.is_dir():
        return []
    iters = sorted(d.glob("iter-*.md"))
    # Sort by parsed iter number descending
    def _n(p: Path) -> int:
        try:
            return int(p.stem.split("-", 1)[1])
        except (IndexError, ValueError):
            return -1

    return sorted(iters, key=_n, reverse=True)
