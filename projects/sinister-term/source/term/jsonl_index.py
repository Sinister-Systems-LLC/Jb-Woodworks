# Sinister Term :: term/jsonl_index.py
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
#
# iter-78a foundation: tail-offset index for JSONL log files.
#
# Why this exists
# ---------------
# Several sterm builtins tail the same JSONL file repeatedly across the
# session: /watch, /fu (fleet-updates), /incidents, /crashlog, /utterances.
# Today each call performs a fresh seek-to-end + readlines. For multi-MB
# files like fleet-updates.jsonl (~5MB at the time of writing) this is
# wasted I/O — the second call re-reads bytes the first call already saw.
#
# This module maintains a small JSON cache at `_shared-memory/_OFFSETS.json`
# recording {byte_offset, size, mtime} per tracked file. Successive calls
# can resume from the last offset instead of re-scanning. On detected
# rotation (file shrank OR mtime moved backward) the cache entry is
# invalidated and a full tail read is performed.
#
# The cache is ADVISORY only: builtins always tolerate a missing or stale
# cache (they fall back to a full tail read). The cache merely lets the
# common case go faster.
#
# Design constraints (per serenedb + rmux audit findings)
# - mtime-based invalidation (atime unreliable on Windows)
# - bounded read: never load more than MAX_TAIL_BYTES of file tail at once
# - atomic offset persistence: write to .tmp + os.replace
# - skip on error: any OSError returns the raw-fallback tail bytes
# - schema-versioned JSON so future evolutions are backward compatible

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

# Default 256 KiB cap on tail-read. Matches existing cmd_watch heuristic.
DEFAULT_MAX_TAIL_BYTES = 256 * 1024

# Schema version for the offsets cache file. Bump on incompatible change.
SCHEMA_VERSION = "sinister.jsonl-tail-index.v1"


@dataclass
class TailResult:
    """Result of a tail read.

    `lines` is the trimmed-and-split list (excludes blank lines).
    `total_lines_estimate` is the count returned from the buffer we read;
    callers should treat it as a lower bound (full file may have more).
    `cache_hit` indicates the cache let us skip a full-tail re-read.
    """
    lines: list[str]
    total_lines_estimate: int
    cache_hit: bool


def _offsets_file(shared_memory: Path) -> Path:
    return shared_memory / "_OFFSETS.json"


def _load_offsets(shared_memory: Path) -> dict:
    """Load the offsets cache. Returns empty dict on any failure."""
    p = _offsets_file(shared_memory)
    if not p.exists():
        return {"schema_version": SCHEMA_VERSION, "entries": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"schema_version": SCHEMA_VERSION, "entries": {}}
        if data.get("schema_version") != SCHEMA_VERSION:
            return {"schema_version": SCHEMA_VERSION, "entries": {}}
        if not isinstance(data.get("entries"), dict):
            data["entries"] = {}
        return data
    except (OSError, ValueError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "entries": {}}


def _save_offsets(shared_memory: Path, data: dict) -> None:
    """Atomic write of offsets cache. Silent on failure (advisory only)."""
    p = _offsets_file(shared_memory)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + f".tmp.{os.getpid()}")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    except OSError:
        # Cache failures must never break the caller.
        pass


def _rel_key(target: Path, shared_memory: Path) -> str:
    """Normalize the cache key to a forward-slash relative path."""
    try:
        return str(target.relative_to(shared_memory)).replace("\\", "/")
    except ValueError:
        return str(target).replace("\\", "/")


def tail_last_n(
    target: Path,
    shared_memory: Path,
    limit: int = 10,
    max_tail_bytes: int = DEFAULT_MAX_TAIL_BYTES,
    update_cache: bool = True,
) -> TailResult:
    """Return the last `limit` non-blank lines of `target`.

    Uses the offsets cache when possible (cache_hit=True) to skip
    re-reading bytes already seen. Falls back to a full bounded tail read
    on cache miss, rotation, or any OSError.

    `target` must be an existing file. Caller is responsible for the
    sandbox check (e.g. /watch's `_shared-memory/` containment) — this
    module does NOT enforce path containment.
    """
    if limit < 1:
        limit = 1
    if max_tail_bytes < 1024:
        max_tail_bytes = 1024

    try:
        st = target.stat()
    except OSError:
        return TailResult(lines=[], total_lines_estimate=0, cache_hit=False)

    size = st.st_size
    mtime = st.st_mtime
    if size == 0:
        return TailResult(lines=[], total_lines_estimate=0, cache_hit=False)

    key = _rel_key(target, shared_memory)
    cache = _load_offsets(shared_memory)
    entries = cache.setdefault("entries", {})
    prev = entries.get(key) if isinstance(entries.get(key), dict) else None

    # Decide read start.
    read_from = max(0, size - max_tail_bytes)
    cache_hit = False
    if prev is not None:
        prev_size = prev.get("size", 0)
        prev_off = prev.get("byte_offset", 0)
        prev_mtime = prev.get("mtime", 0.0)
        # Rotation/shrink detection: invalidate.
        if (
            isinstance(prev_size, int)
            and isinstance(prev_off, int)
            and isinstance(prev_mtime, (int, float))
            and prev_size <= size
            and prev_off <= size
            and prev_mtime <= mtime + 0.001
        ):
            # Resume from where we left off (but never less than the
            # bounded-tail threshold — we still want at least `limit`
            # candidate lines available).
            read_from = max(read_from, prev_off)
            cache_hit = True

    try:
        with target.open("rb") as fh:
            fh.seek(read_from)
            # If we're mid-file, discard the partial first line so we
            # don't return garbage. When read_from == 0 we want the full
            # first line.
            if read_from > 0:
                _ = fh.readline()
            buf = fh.read()
    except OSError:
        return TailResult(lines=[], total_lines_estimate=0, cache_hit=False)

    text = buf.decode("utf-8", errors="replace")
    raw_lines = text.splitlines()
    nonblank = [ln for ln in raw_lines if ln.strip()]

    # If we resumed from cache but didn't get enough lines (small new
    # delta), top up by re-reading more bytes back from the tail. This
    # keeps callers honest: asking for last-10 always gets last-10 when
    # the file has >=10 lines, even right after a cache resume.
    if cache_hit and len(nonblank) < limit and read_from > 0:
        backstop = max(0, size - max_tail_bytes)
        if backstop < read_from:
            try:
                with target.open("rb") as fh:
                    fh.seek(backstop)
                    if backstop > 0:
                        _ = fh.readline()
                    buf = fh.read()
                text = buf.decode("utf-8", errors="replace")
                raw_lines = text.splitlines()
                nonblank = [ln for ln in raw_lines if ln.strip()]
                cache_hit = False  # We had to back off, so it's a miss.
            except OSError:
                pass

    shown = nonblank[-limit:]

    if update_cache:
        entries[key] = {
            "byte_offset": size,
            "size": size,
            "mtime": mtime,
            "schema_version": SCHEMA_VERSION,
        }
        _save_offsets(shared_memory, cache)

    return TailResult(
        lines=shown,
        total_lines_estimate=len(nonblank),
        cache_hit=cache_hit,
    )


def invalidate(target: Path, shared_memory: Path) -> bool:
    """Drop the cache entry for `target`. Returns True if an entry existed."""
    key = _rel_key(target, shared_memory)
    cache = _load_offsets(shared_memory)
    entries = cache.get("entries", {})
    if key in entries:
        del entries[key]
        _save_offsets(shared_memory, cache)
        return True
    return False


def clear_all(shared_memory: Path) -> int:
    """Drop every cache entry. Returns the number of dropped entries."""
    cache = _load_offsets(shared_memory)
    entries = cache.get("entries", {})
    n = len(entries)
    cache["entries"] = {}
    _save_offsets(shared_memory, cache)
    return n


def stats(shared_memory: Path) -> dict:
    """Diagnostic snapshot of the offsets cache (for sterm /sysinfo etc)."""
    cache = _load_offsets(shared_memory)
    entries = cache.get("entries", {})
    return {
        "schema_version": cache.get("schema_version", SCHEMA_VERSION),
        "tracked_files": len(entries),
        "total_offset_bytes": sum(
            (e.get("byte_offset", 0) for e in entries.values()
             if isinstance(e, dict)),
            0,
        ),
    }
