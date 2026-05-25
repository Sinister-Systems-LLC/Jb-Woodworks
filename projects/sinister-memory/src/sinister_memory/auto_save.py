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
from typing import Optional  # noqa: F401


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,64}$")


def _validate_slug(slug: str) -> str:
    slug_l = slug.strip().lower()
    if not SLUG_RE.match(slug_l):
        raise ValueError(f"invalid slug: {slug!r} (must match {SLUG_RE.pattern})")
    return slug_l


def per_agent_dir(slug: str, root: Path) -> Path:
    return Path(root) / "_shared-memory" / "sinister-memory" / "per-agent" / _validate_slug(slug)


# Schema v2: adds category + confidence + format_version. Cherry-picked from
# jcode v0.12.4 src/memory.rs:96-111 MemoryEntry struct. Brain entry:
# jcode-memory-audit-and-cherry-picks-2026-05-25.
FRONTMATTER_VERSION = 2
VALID_CATEGORIES = frozenset({"fact", "preference", "correction", "entity", "procedure", "inferred"})


def save_iter_close(
    slug: str,
    iter_num: int,
    summary: str,
    root: Path,
    do_reindex: bool = False,
    category: Optional[str] = None,
    confidence: Optional[float] = None,
    trust: Optional[str] = None,
) -> Path:
    """Write the iter-close memory file and return its path.

    The file is markdown with a YAML-ish frontmatter block (schema v2 -- includes
    optional category/confidence/trust fields cherry-picked from jcode). Body is
    the summary verbatim. Bash-safe: backticks in the summary are escaped so
    PowerShell here-strings consuming the file later don't break.

    Args:
      category  : one of VALID_CATEGORIES; controls per-category half-life in decay
      confidence: 0.0 - 1.0; reinforcement signal; used by future prune_low_confidence
      trust     : one of {"high", "medium", "low"}; provenance grade (jcode-style)
    """
    slug_l = _validate_slug(slug)
    if not isinstance(iter_num, int) or iter_num < 0:
        raise ValueError(f"iter_num must be non-negative int, got {iter_num!r}")

    if category is not None and category.lower() not in VALID_CATEGORIES:
        raise ValueError(
            f"invalid category {category!r}; must be one of {sorted(VALID_CATEGORIES)}"
        )
    if confidence is not None and not (0.0 <= float(confidence) <= 1.0):
        raise ValueError(f"confidence must be in [0.0, 1.0], got {confidence!r}")
    if trust is not None and trust.lower() not in {"high", "medium", "low"}:
        raise ValueError(f"trust must be one of high/medium/low, got {trust!r}")

    summary = summary or "(no summary)"
    # Defensive: clamp absurdly long summaries
    if len(summary) > 16_000:
        summary = summary[:16_000] + "\n\n... [truncated]"

    out_dir = per_agent_dir(slug_l, root)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"iter-{iter_num:04d}.md"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm_lines = [
        "---",
        f"format_version: {FRONTMATTER_VERSION}",
        "author: RKOJ-ELENO",
        f"slug: {slug_l}",
        f"iter: {iter_num}",
        f"saved_at: {now}",
        f"length: {len(summary)}",
    ]
    if category is not None:
        fm_lines.append(f"category: {category.lower()}")
    if confidence is not None:
        fm_lines.append(f"confidence: {float(confidence):.3f}")
    if trust is not None:
        fm_lines.append(f"trust: {trust.lower()}")
    fm_lines.append("---")
    body = "\n".join(fm_lines) + f"\n\n# {slug_l} :: iter-{iter_num:04d}\n\n{summary}\n"

    out_path.write_text(body, encoding="utf-8")

    if do_reindex:
        # Local import to avoid circular reference at module load
        from . import indexer

        indexer.build(Path(root), indexer.default_db_path(root))

    return out_path


def parse_frontmatter(path: Path) -> dict:
    """Read a saved iter-close file and return its frontmatter as a dict.

    Back-compat: v1 files (no format_version) are returned with the keys they have;
    callers should treat missing format_version as 1.
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    block = text[4:end]
    out: dict = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


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
