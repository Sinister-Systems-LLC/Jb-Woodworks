#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
# SPDX-License-Identifier: AGPL-3.0-or-later
"""build_brain_index.py - Brain index builder for O(log n) /recall lookup.

Author: RKOJ-ELENO :: 2026-05-26
License: AGPL-3.0-or-later

Scans `_shared-memory/knowledge/*.md` and produces `_BRAIN_INDEX.json` with
per-file title / tags / sections (heading, byte_offset, sha256[:16] hash).

Schema: sinister.brain-index.v1

CLI:
    python build_brain_index.py             rebuild full index (overwrite JSON)
    python build_brain_index.py --dry-run   print stats, do not write
    python build_brain_index.py --incremental  re-index only newer files
    python build_brain_index.py --check     verify existing index, exit 1 on drift
    python build_brain_index.py --search Q  print entries matching tag/title

Wave 1.B of the Sinister parallel-execution plan: replaces the linear-grep
implementation of /recall in projects/sinister-term/source/term/commands.py
(Wave 2 will refactor /recall to call --search).

Composes with `no-bullshit-tested-before-claimed-2026-05-23` (smoke-tested
before claimed) and `we-have-the-source-read-it-doctrine-2026-05-25` (the
brain is the canonical source; we index it, never RE it).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "sinister.brain-index.v1"

# Default repo-relative paths. Resolved against the script's location so the
# tool works from any cwd (CLAUDE.md says agents shell from many cwds).
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_KNOWLEDGE_DIR = REPO_ROOT / "_shared-memory" / "knowledge"
DEFAULT_INDEX_PATH = DEFAULT_KNOWLEDGE_DIR / "_BRAIN_INDEX.json"

# Common words dropped from filename-derived tags. Kept conservative; the
# point is to filter "the / of / a" noise without losing real topic terms.
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "of",
        "for",
        "and",
        "to",
        "in",
        "on",
        "by",
        "is",
        "it",
        "be",
        "or",
        "md",
    }
)

DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def utc_iso_now() -> str:
    """Return current UTC time in ISO-8601 format (Z-suffix)."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def utc_iso_from_epoch(epoch: float) -> str:
    """Return ISO-8601 UTC string for the given epoch seconds."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def slug_from_path(p: Path) -> str:
    """Slug = filename without `.md` extension."""
    return p.stem


def derive_tags(slug: str) -> list[str]:
    """Split slug on `-`, drop stopwords, keep dates + remaining tokens.

    `automate-everything-no-operator-admin-2026-05-25` ->
        ["automate", "everything", "no", "operator", "admin", "2026-05-25"]
    Date tokens are recombined (YYYY, MM, DD reassembled if adjacent).
    """
    raw = slug.lower().split("-")
    tags: list[str] = []
    i = 0
    while i < len(raw):
        # Try to reassemble a YYYY-MM-DD date from three consecutive tokens.
        if (
            i + 2 < len(raw)
            and len(raw[i]) == 4
            and raw[i].isdigit()
            and len(raw[i + 1]) == 2
            and raw[i + 1].isdigit()
            and len(raw[i + 2]) == 2
            and raw[i + 2].isdigit()
        ):
            tags.append(f"{raw[i]}-{raw[i + 1]}-{raw[i + 2]}")
            i += 3
            continue
        tok = raw[i]
        if tok and tok not in STOPWORDS:
            tags.append(tok)
        i += 1
    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def is_author_or_meta_h1(text: str) -> bool:
    """True if the H1 line looks like authorship/license metadata, not a title."""
    t = text.strip().lower()
    return (
        t.startswith("author:")
        or t.startswith("spdx-")
        or t.startswith("license:")
        or t.startswith("copyright")
    )


def parse_markdown(text: str, fallback_title: str) -> tuple[str, list[dict[str, Any]]]:
    """Return (title, sections) parsed from the .md body.

    Title = first non-meta H1, else first H2, else fallback_title (slug-prettified).
    Sections = every H2 / H3 with byte_offset (line start) and section_hash
    (sha256[:16] hex over the section body, body = bytes until next H2/H3 or EOF).
    """
    # Use bytes for byte_offset accuracy (markdown is UTF-8; line lengths vary).
    raw_bytes = text.encode("utf-8")
    # Line spans: (start_byte, end_byte_exclusive_of_newline_break).
    line_spans: list[tuple[int, int]] = []
    pos = 0
    while pos < len(raw_bytes):
        nl = raw_bytes.find(b"\n", pos)
        if nl == -1:
            line_spans.append((pos, len(raw_bytes)))
            break
        line_spans.append((pos, nl))
        pos = nl + 1

    title: str | None = None
    first_h2_text: str | None = None
    section_marks: list[tuple[int, int, int, str]] = []
    # Each entry: (line_start_byte, line_idx, level, heading_full_text)

    for idx, (start, end) in enumerate(line_spans):
        line = raw_bytes[start:end].decode("utf-8", errors="replace")
        m = HEADING_RE.match(line)
        if not m:
            continue
        hashes, body = m.group(1), m.group(2)
        level = len(hashes)
        if level == 1:
            if title is None and not is_author_or_meta_h1(body):
                title = body.strip()
        elif level == 2:
            if first_h2_text is None:
                first_h2_text = body.strip()
            section_marks.append((start, idx, 2, line))
        elif level == 3:
            section_marks.append((start, idx, 3, line))

    if title is None:
        title = first_h2_text if first_h2_text else fallback_title

    # Build sections with body hashes. The body of a section is bytes from the
    # END of its heading line through the byte before the next section heading
    # (or EOF).
    sections: list[dict[str, Any]] = []
    for i, (start_byte, line_idx, level, heading_line) in enumerate(section_marks):
        body_start = line_spans[line_idx][1]  # end of heading line (excl. \n)
        if i + 1 < len(section_marks):
            body_end = section_marks[i + 1][0]
        else:
            body_end = len(raw_bytes)
        body_bytes = raw_bytes[body_start:body_end]
        section_hash = hashlib.sha256(body_bytes).hexdigest()[:16]
        sections.append(
            {
                "heading": heading_line.strip(),
                "level": level,
                "byte_offset": start_byte,
                "section_hash": section_hash,
            }
        )

    return title, sections


def prettify_stem(stem: str) -> str:
    """Slug-stem -> Title Case fallback when no H1/H2 exists."""
    parts = stem.split("-")
    return " ".join(p.capitalize() if not (len(p) == 4 and p.isdigit()) else p for p in parts)


def index_one_file(md_path: Path, knowledge_dir: Path) -> dict[str, Any] | None:
    """Index a single .md file. Returns None on skip/failure (logs to stderr)."""
    try:
        st = md_path.stat()
    except OSError as exc:
        print(f"[brain-index] stat-fail {md_path.name}: {exc}", file=sys.stderr)
        return None

    if st.st_size == 0:
        return None

    if md_path.name.startswith("_"):
        # Underscore-prefixed files are indexes / templates, not brain entries.
        return None

    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"[brain-index] read-fail {md_path.name}: {exc}", file=sys.stderr)
        return None

    stem = md_path.stem
    fallback_title = prettify_stem(stem)
    try:
        title, sections = parse_markdown(text, fallback_title)
    except Exception as exc:  # noqa: BLE001 - best-effort tolerance per spec
        print(f"[brain-index] parse-fail {md_path.name}: {exc}", file=sys.stderr)
        title, sections = fallback_title, []

    tags = derive_tags(stem)
    # Also surface any dates found inside the document body (catches retro-dates).
    body_dates = sorted(set(DATE_RE.findall(text)))
    for d in body_dates:
        if d not in tags:
            tags.append(d)

    try:
        rel_path = md_path.relative_to(knowledge_dir).as_posix()
    except ValueError:
        rel_path = md_path.name

    return {
        "slug": stem,
        "path": rel_path,
        "title": title,
        "byte_size": st.st_size,
        "mtime_utc": utc_iso_from_epoch(st.st_mtime),
        "mtime_epoch": st.st_mtime,
        "tags": tags,
        "sections": sections,
    }


def walk_knowledge_dir(knowledge_dir: Path) -> list[Path]:
    """Yield all .md files under knowledge_dir (recursive), skipping `_archive`.

    `_archive` is excluded because those entries are retired and shouldn't
    surface in /recall. README / _TEMPLATE / _INDEX* are skipped by
    `index_one_file` via the underscore-prefix rule.
    """
    if not knowledge_dir.exists():
        return []
    out: list[Path] = []
    for p in knowledge_dir.rglob("*.md"):
        # Skip _archive subdir entirely.
        parts = p.relative_to(knowledge_dir).parts
        if any(part == "_archive" for part in parts):
            continue
        out.append(p)
    return out


def build_index(
    knowledge_dir: Path,
    incremental_from: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full index dict. Pass `incremental_from` to reuse stale entries."""
    cutoff_epoch: float | None = None
    existing_entries_by_path: dict[str, dict[str, Any]] = {}
    if incremental_from is not None:
        built_at = incremental_from.get("built_at_utc", "")
        if built_at:
            try:
                cutoff_epoch = time.mktime(time.strptime(built_at, "%Y-%m-%dT%H:%M:%SZ"))
                # Adjust for timezone (mktime treats arg as local). Subtract
                # local offset to land back at the UTC epoch.
                cutoff_epoch -= time.timezone
            except ValueError:
                cutoff_epoch = None
        for ent in incremental_from.get("entries", []):
            existing_entries_by_path[ent.get("path", "")] = ent

    files = walk_knowledge_dir(knowledge_dir)
    entries: list[dict[str, Any]] = []
    reused = 0
    for md_path in files:
        try:
            rel = md_path.relative_to(knowledge_dir).as_posix()
        except ValueError:
            rel = md_path.name
        existing = existing_entries_by_path.get(rel)
        if (
            cutoff_epoch is not None
            and existing is not None
            and md_path.stat().st_mtime <= cutoff_epoch
        ):
            entries.append(existing)
            reused += 1
            continue
        ent = index_one_file(md_path, knowledge_dir)
        if ent is not None:
            entries.append(ent)

    # Sort by mtime DESC. Entries reused from the existing index keep their
    # original mtime_epoch field for sorting (else fall back to 0).
    entries.sort(key=lambda e: e.get("mtime_epoch", 0.0), reverse=True)

    total_sections = sum(len(e.get("sections", [])) for e in entries)

    index = {
        "schema_version": SCHEMA_VERSION,
        "built_at_utc": utc_iso_now(),
        "knowledge_dir": str(knowledge_dir.relative_to(REPO_ROOT).as_posix())
        if knowledge_dir.is_relative_to(REPO_ROOT)
        else str(knowledge_dir),
        "total_files": len(entries),
        "total_sections": total_sections,
        "incremental_reused": reused,
        "entries": entries,
    }
    return index


def write_index(index: dict[str, Any], index_path: Path) -> None:
    """Atomically write index to disk: tmp file + rename."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = index_path.with_suffix(index_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    os.replace(tmp, index_path)


def load_index(index_path: Path) -> dict[str, Any] | None:
    """Load existing index, or None if missing/corrupt (logs to stderr)."""
    if not index_path.exists():
        return None
    try:
        with index_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[brain-index] load-fail {index_path.name}: {exc}", file=sys.stderr)
        return None


def check_index(index: dict[str, Any], knowledge_dir: Path) -> tuple[bool, list[str]]:
    """Return (ok, drift_messages). Drift = stale entry or missing file."""
    drift: list[str] = []
    if index.get("schema_version") != SCHEMA_VERSION:
        drift.append(
            f"schema_version mismatch: got {index.get('schema_version')!r}, want {SCHEMA_VERSION!r}"
        )

    indexed_paths = {ent.get("path", ""): ent for ent in index.get("entries", [])}
    live_files = walk_knowledge_dir(knowledge_dir)
    live_rel: set[str] = set()
    for p in live_files:
        try:
            rel = p.relative_to(knowledge_dir).as_posix()
        except ValueError:
            rel = p.name
        if p.name.startswith("_") or p.stat().st_size == 0:
            continue
        live_rel.add(rel)

    # Entries in index but missing on disk:
    for path in indexed_paths:
        if path not in live_rel:
            drift.append(f"stale entry (file missing): {path}")

    # Files on disk but not in index:
    for path in live_rel:
        if path not in indexed_paths:
            drift.append(f"missing entry (file not indexed): {path}")

    # mtime drift:
    for path, ent in indexed_paths.items():
        if path not in live_rel:
            continue
        live_mtime = (knowledge_dir / path).stat().st_mtime
        indexed_mtime = ent.get("mtime_epoch", 0.0)
        # 2-second tolerance for filesystem mtime granularity.
        if abs(live_mtime - indexed_mtime) > 2.0:
            drift.append(f"mtime drift: {path} (live={live_mtime} idx={indexed_mtime})")

    return (len(drift) == 0, drift)


def search_index(index: dict[str, Any], query: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return entries whose tag matches OR title contains query (case-insensitive)."""
    q = query.strip().lower()
    if not q:
        return []
    hits: list[tuple[int, dict[str, Any]]] = []
    for ent in index.get("entries", []):
        score = 0
        tags = [t.lower() for t in ent.get("tags", [])]
        title_lc = ent.get("title", "").lower()
        slug_lc = ent.get("slug", "").lower()
        if q in tags:
            score += 100
        if q in slug_lc:
            score += 50
        if q in title_lc:
            score += 25
        # Partial tag match (substring inside any tag).
        for t in tags:
            if q in t and q != t:
                score += 10
                break
        if score > 0:
            hits.append((score, ent))
    hits.sort(key=lambda h: (-h[0], -h[1].get("mtime_epoch", 0.0)))
    return [h[1] for h in hits[:limit]]


def print_search_results(results: list[dict[str, Any]]) -> None:
    """Human-readable search output for /recall consumers."""
    if not results:
        print("(no matches)")
        return
    for ent in results:
        slug = ent.get("slug", "?")
        title = ent.get("title", "(no title)")
        mtime = ent.get("mtime_utc", "?")
        tags = ",".join(ent.get("tags", [])[:6])
        print(f"{slug}\t{mtime}\t{title}\t[{tags}]")


def cmd_build(args: argparse.Namespace, knowledge_dir: Path, index_path: Path) -> int:
    """Full or incremental rebuild."""
    incremental_from: dict[str, Any] | None = None
    if args.incremental:
        incremental_from = load_index(index_path)
        if incremental_from is None:
            print(
                "[brain-index] --incremental: no prior index, falling back to full rebuild",
                file=sys.stderr,
            )

    index = build_index(knowledge_dir, incremental_from=incremental_from)

    if args.dry_run:
        print(f"schema_version: {index['schema_version']}")
        print(f"built_at_utc:   {index['built_at_utc']}")
        print(f"knowledge_dir:  {index['knowledge_dir']}")
        print(f"total_files:    {index['total_files']}")
        print(f"total_sections: {index['total_sections']}")
        print(f"reused:         {index['incremental_reused']}")
        if index["entries"]:
            print("newest entries:")
            for ent in index["entries"][:5]:
                print(f"  - {ent['slug']}  ({ent['mtime_utc']})")
        return 0

    write_index(index, index_path)
    print(
        f"[brain-index] wrote {index_path.name}: "
        f"files={index['total_files']} sections={index['total_sections']} "
        f"reused={index['incremental_reused']}"
    )
    return 0


def cmd_check(_args: argparse.Namespace, knowledge_dir: Path, index_path: Path) -> int:
    """Verify the on-disk index against the live knowledge dir."""
    index = load_index(index_path)
    if index is None:
        print("[brain-index] check: no index found", file=sys.stderr)
        return 1
    ok, drift = check_index(index, knowledge_dir)
    if ok:
        print(
            f"[brain-index] check OK: files={index.get('total_files', 0)} "
            f"sections={index.get('total_sections', 0)}"
        )
        return 0
    print(f"[brain-index] check FAIL: {len(drift)} drift(s)", file=sys.stderr)
    for msg in drift[:20]:
        print(f"  - {msg}", file=sys.stderr)
    if len(drift) > 20:
        print(f"  ... and {len(drift) - 20} more", file=sys.stderr)
    return 1


def cmd_search(args: argparse.Namespace, knowledge_dir: Path, index_path: Path) -> int:
    """Tag / title / slug lookup."""
    index = load_index(index_path)
    if index is None:
        # Build in-memory rather than failing - keeps /recall robust if the
        # cached JSON is missing.
        index = build_index(knowledge_dir)
    results = search_index(index, args.search, limit=args.limit)
    print_search_results(results)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_brain_index",
        description=(
            "Build / search / verify the Sinister brain index "
            "(_shared-memory/knowledge/_BRAIN_INDEX.json)."
        ),
    )
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=DEFAULT_KNOWLEDGE_DIR,
        help=f"override knowledge dir (default: {DEFAULT_KNOWLEDGE_DIR})",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help=f"override output path (default: {DEFAULT_INDEX_PATH})",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="print summary stats, do not write"
    )
    mode.add_argument(
        "--incremental",
        action="store_true",
        help="reuse entries whose mtime is older than the prior index's built_at_utc",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="verify on-disk index is consistent with the knowledge dir; exit 1 on drift",
    )
    mode.add_argument(
        "--search",
        type=str,
        default=None,
        metavar="QUERY",
        help="print entries matching tag/slug/title substring (for /recall integration)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="max hits for --search (default: 50)",
    )

    args = parser.parse_args(argv)

    knowledge_dir: Path = args.knowledge_dir.resolve() if args.knowledge_dir else DEFAULT_KNOWLEDGE_DIR
    index_path: Path = args.index_path.resolve() if args.index_path else DEFAULT_INDEX_PATH

    if not knowledge_dir.exists():
        # Tolerant: create an empty index. /recall must still work in a
        # freshly-cloned repo before any brain entries land.
        print(
            f"[brain-index] knowledge dir missing: {knowledge_dir} (writing empty index)",
            file=sys.stderr,
        )
        empty = {
            "schema_version": SCHEMA_VERSION,
            "built_at_utc": utc_iso_now(),
            "knowledge_dir": str(knowledge_dir),
            "total_files": 0,
            "total_sections": 0,
            "incremental_reused": 0,
            "entries": [],
        }
        if not args.dry_run and not args.check and args.search is None:
            write_index(empty, index_path)
        if args.check:
            return 1
        if args.search is not None:
            print_search_results([])
        return 0

    if args.check:
        return cmd_check(args, knowledge_dir, index_path)
    if args.search is not None:
        return cmd_search(args, knowledge_dir, index_path)
    return cmd_build(args, knowledge_dir, index_path)


if __name__ == "__main__":
    sys.exit(main())
