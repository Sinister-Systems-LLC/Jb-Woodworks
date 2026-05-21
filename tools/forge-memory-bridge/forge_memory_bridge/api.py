# Sinister Sanctum :: forge-memory-bridge :: core disk-first API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Disk-first cross-session, cross-agent memory store. jcode-memory-feature parity
implemented on top of plain JSON files so any agent (with or without MCP loaded)
can read and write.

Layout:
    <root>/
        _index.json
        _consolidation-log.jsonl
        <namespace>/
            _meta.json
            <key>.json

See README.md for the full spec.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Local alias for the builtin list — our module-level `list` is rebound below
# to point at our ls() function (kept for back-compat with `from
# forge_memory_bridge.api import list` callers from v0.1.0). ALL internal
# references use builtins_list or ls() directly.
builtins_list = builtins.list

SCHEMA_VERSION = "sinister.forge-memory.v1"

# Default root: D:\Sinister Sanctum\_shared-memory\forge-memory
# Override via env SINISTER_FORGE_MEMORY_ROOT or set_root().
DEFAULT_ROOT = Path(
    os.environ.get(
        "SINISTER_FORGE_MEMORY_ROOT",
        r"D:\Sinister Sanctum\_shared-memory\forge-memory",
    )
)

_AUTHOR_LINE = "RKOJ-ELENO :: 2026-05-21"

_root: Path = DEFAULT_ROOT


def set_root(path: str | Path) -> None:
    """Override the store root (mainly for tests + alt fleets)."""
    global _root
    _root = Path(path)
    _root.mkdir(parents=True, exist_ok=True)


def get_root() -> Path:
    return _root


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash(value: Any) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_slug(s: str) -> str:
    """Filesystem-safe slug. Preserves operator-readable keys."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "_"


def _namespace_dir(namespace: str) -> Path:
    ns = _safe_slug(namespace)
    d = _root / ns
    d.mkdir(parents=True, exist_ok=True)
    meta = d / "_meta.json"
    if not meta.exists():
        meta.write_text(
            json.dumps(
                {
                    "_author": _AUTHOR_LINE,
                    "schema_version": SCHEMA_VERSION,
                    "namespace": ns,
                    "created_utc": _now_iso(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return d


def _record_path(namespace: str, key: str) -> Path:
    return _namespace_dir(namespace) / f"{_safe_slug(key)}.json"


def _read_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def write(
    namespace: str,
    key: str,
    value: str | dict,
    tags: list[str] | None = None,
    upsert: bool = True,
) -> dict:
    """Write a memory record. Returns the stored object.

    upsert=True: if key already exists, merge (increment writes counter,
                 update ts_utc_last, raise confidence). Last value wins.
    upsert=False: raise FileExistsError if key already exists.
    """
    # Use builtins.list explicitly — our module-level ls() used to shadow
    # builtin list() (renamed 0.1.1 per Term bug report 2026-05-21T1150Z).
    tags = builtins.list(tags or [])
    p = _record_path(namespace, key)
    existing = _read_json(p)
    now = _now_iso()
    content_hash = _hash(value)

    if existing and not upsert:
        raise FileExistsError(f"Memory key already exists: {namespace}/{key}")

    if existing:
        writes = int(existing.get("writes", 1)) + 1
        confidence = min(1.0, float(existing.get("confidence", 1.0)) + 0.05)
        ts_first = existing.get("ts_utc_first", now)
    else:
        writes = 1
        confidence = 1.0
        ts_first = now

    record = {
        "_author": _AUTHOR_LINE,
        "schema_version": SCHEMA_VERSION,
        "namespace": _safe_slug(namespace),
        "key": _safe_slug(key),
        "value": value,
        "tags": tags,
        "ts_utc_first": ts_first,
        "ts_utc_last": now,
        "writes": writes,
        "confidence": round(confidence, 4),
        "content_hash": content_hash,
    }
    _write_json(p, record)
    _bump_index(record)
    return record


def _bump_index(record: dict) -> None:
    """Maintain a global flat index for fast scans."""
    idx_path = _root / "_index.json"
    idx = _read_json(idx_path) or {
        "_author": _AUTHOR_LINE,
        "schema_version": SCHEMA_VERSION + ".index",
        "records": {},
    }
    rid = f"{record['namespace']}/{record['key']}"
    idx["records"][rid] = {
        "ts_utc_last": record["ts_utc_last"],
        "writes": record["writes"],
        "confidence": record["confidence"],
        "tags": record["tags"],
        "content_hash": record["content_hash"],
    }
    idx["updated_utc"] = _now_iso()
    _write_json(idx_path, idx)


def ls(
    namespace: str | None = None,
    tags: list[str] | None = None,
) -> list[dict]:
    """List records, optionally filtered by namespace and/or tags (AND-match).

    Renamed from list() in v0.1.1 to remove shadowing of builtin list() inside
    this module (per Term bug report 2026-05-21T1150Z). Public alias `list`
    preserved at the end of this module so existing `from forge_memory_bridge
    import list` callers continue to work.
    """
    if not _root.exists():
        return []
    tags_set = set(tags or [])
    out: list[dict] = []
    if namespace:
        dirs = [_namespace_dir(namespace)]
    else:
        dirs = [d for d in _root.iterdir() if d.is_dir() and not d.name.startswith("_")]
    for d in dirs:
        for f in d.glob("*.json"):
            if f.name.startswith("_"):
                continue
            rec = _read_json(f)
            if rec is None:
                continue
            if tags_set and not tags_set.issubset(set(rec.get("tags", []))):
                continue
            out.append(rec)
    out.sort(key=lambda r: r.get("ts_utc_last", ""), reverse=True)
    return out


# Public alias — keep `list` as an export name for callers who imported it,
# but ALL internal references go through ls() to avoid shadow.
list = ls  # noqa: A001


def delete(namespace: str, key: str) -> bool:
    p = _record_path(namespace, key)
    if not p.exists():
        return False
    p.unlink()
    idx_path = _root / "_index.json"
    idx = _read_json(idx_path)
    if idx:
        rid = f"{_safe_slug(namespace)}/{_safe_slug(key)}"
        idx.get("records", {}).pop(rid, None)
        idx["updated_utc"] = _now_iso()
        _write_json(idx_path, idx)
    return True


# ── Recall: TF-IDF keyword default + optional MCP semantic fast-path ──

_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokenize(text: str) -> builtins_list[str]:
    return _TOKEN_RE.findall(text.lower())


def _record_text(rec: dict) -> str:
    parts = [
        rec.get("namespace", ""),
        rec.get("key", ""),
        " ".join(rec.get("tags", [])),
    ]
    val = rec.get("value")
    if isinstance(val, str):
        parts.append(val)
    else:
        parts.append(json.dumps(val, default=str))
    return " ".join(parts)


def _tfidf_score(query_tokens: builtins_list[str], records: builtins_list[dict]) -> builtins_list[tuple[float, dict]]:
    if not records:
        return []
    # document frequencies
    df: dict[str, int] = {}
    docs: builtins_list[builtins_list[str]] = []
    for r in records:
        toks = _tokenize(_record_text(r))
        docs.append(toks)
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    n = len(records)
    scored: builtins_list[tuple[float, dict]] = []
    q_set = set(query_tokens)
    for r, toks in zip(records, docs):
        if not toks:
            scored.append((0.0, r))
            continue
        # term frequency for query tokens in this doc
        tf: dict[str, int] = {}
        for t in toks:
            if t in q_set:
                tf[t] = tf.get(t, 0) + 1
        if not tf:
            scored.append((0.0, r))
            continue
        score = 0.0
        for t, c in tf.items():
            idf = math.log(1 + n / (1 + df.get(t, 0)))
            score += (c / len(toks)) * idf
        # boost by confidence + recency proxy (writes count)
        score *= 1.0 + 0.1 * float(r.get("confidence", 1.0))
        score *= 1.0 + 0.02 * math.log(1 + int(r.get("writes", 1)))
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def bm25_rescore(query: str, candidates: builtins_list[dict]) -> builtins_list[dict]:
    """Re-order candidate hits using Okapi BM25 (jcode parity, pattern 6).

    jcode (Rust) uses BM25 for `~/.jcode/sessions/` ranking in
    `src/tool/session_search.rs`. Operator wants the same on RKOJ's recall
    path. This function takes whatever `recall()` produced (TF-IDF top-k or
    untouched pool) and re-orders by BM25 over the same record-text the
    TF-IDF pass saw.

    Each returned record gets a `_bm25_score` key (rounded float). The
    pre-existing `_recall_score` (TF-IDF) is preserved on the dict so
    debuggers can see both signals.

    Falls back gracefully if `rank_bm25` is not installed — returns the
    input list untouched. Empty inputs → empty list. Single-doc inputs
    skip the corpus build (BM25 needs n>=2 for IDF to be meaningful) and
    score 0.0.
    """
    if not candidates:
        return []
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
    except ImportError:
        # rank_bm25 not in this environment — caller asked for BM25 but
        # we can't deliver. Return the input unchanged so the recall path
        # degrades to whatever scoring it had before.
        return candidates

    query_tokens = _tokenize(query)
    if not query_tokens:
        return candidates

    corpus = [_tokenize(_record_text(r)) for r in candidates]
    # rank_bm25 errors on empty docs; substitute a single sentinel token.
    corpus = [doc if doc else ["__empty__"] for doc in corpus]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query_tokens)

    pairs = sorted(
        zip(scores, candidates), key=lambda x: float(x[0]), reverse=True
    )
    out: builtins_list[dict] = []
    for score, rec in pairs:
        rec_copy = dict(rec)
        rec_copy["_bm25_score"] = round(float(score), 6)
        out.append(rec_copy)
    return out


def recall(
    query: str,
    namespace: str | None = None,
    limit: int = 10,
    use_mcp: bool = False,
    bm25: bool = True,
) -> builtins_list[dict]:
    """Top-k matches by TF-IDF keyword (default) or Ruflo MCP semantic (use_mcp=True).

    MCP fast-path NOT implemented in v0.1.0 — falls back to disk TF-IDF.
    See README.md "Composes with" Ruflo section for the planned hookup.

    BM25 re-scoring (jcode parity, brain entry pattern 6): when
    `bm25=True` (default), the TF-IDF top-k is re-ordered by Okapi BM25
    as a final pass. Records carry both `_recall_score` (TF-IDF) and
    `_bm25_score` (BM25). Set `bm25=False` to keep the legacy TF-IDF
    ordering (regression-test path).
    """
    if use_mcp:
        # Stub: caller must invoke mcp__ruflo__memory_search themselves in
        # this v0.1.0; we'd shell out via subprocess once the MCP-call
        # transport is sorted (probably via mcp-client Python pkg).
        pass

    pool = ls(namespace=namespace)
    if not pool:
        return []
    query_tokens = _tokenize(query)
    if not query_tokens:
        out = pool[:limit]
        if bm25:
            out = bm25_rescore(query, out)
        return out
    scored = _tfidf_score(query_tokens, pool)
    out = []
    for score, rec in scored[:limit]:
        rec_copy = dict(rec)
        rec_copy["_recall_score"] = round(score, 6)
        out.append(rec_copy)
    if bm25:
        out = bm25_rescore(query, out)
    return out


# ── Graph: emit mermaid syntax for the matching subgraph ──

def _mermaid_safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", s)[:48]


def graph(
    namespace: str | None = None,
    query: str | None = None,
) -> str:
    """Emit mermaid-flowchart syntax of the matching memory subgraph.

    Nodes: one per record. Edges: shared tags (records with >=1 common tag
    get connected). Useful for piping into mermaid-rs-renderer for PNG.
    """
    if query:
        records = recall(query, namespace=namespace, limit=100)
    else:
        records = ls(namespace=namespace)
    if not records:
        return "flowchart LR\n    empty[No memories matched]"
    lines = ["flowchart LR"]
    # Nodes
    for r in records:
        nid = _mermaid_safe(f"{r.get('namespace','_')}__{r.get('key','_')}")
        label = (r.get("key", "") or "(no-key)")[:40].replace('"', "'")
        ns_label = (r.get("namespace", "") or "_")
        lines.append(f'    {nid}["{ns_label}:{label}"]')
    # Edges via shared tags
    seen_pairs: set[tuple[str, str]] = set()
    for i, ri in enumerate(records):
        ti = set(ri.get("tags", []))
        if not ti:
            continue
        nid_i = _mermaid_safe(f"{ri.get('namespace','_')}__{ri.get('key','_')}")
        for rj in records[i + 1 :]:
            tj = set(rj.get("tags", []))
            if not tj:
                continue
            shared = ti & tj
            if not shared:
                continue
            nid_j = _mermaid_safe(f"{rj.get('namespace','_')}__{rj.get('key','_')}")
            key = (nid_i, nid_j) if nid_i <= nid_j else (nid_j, nid_i)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            label = ",".join(sorted(shared))[:24]
            lines.append(f'    {nid_i} -- "{label}" --- {nid_j}')
    return "\n".join(lines)


# ── Consolidate: dedupe near-duplicates by content_hash + raise confidence ──

def consolidate(
    namespace: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Find duplicate-content records (same content_hash within a namespace),
    merge by raising confidence on the surviving record + bumping writes,
    and delete duplicates. Appends a line to _consolidation-log.jsonl.

    Returns: { 'scanned': N, 'duplicates_found': M, 'merged': K, 'dry_run': bool }
    """
    summary = {
        "scanned": 0,
        "duplicates_found": 0,
        "merged": 0,
        "dry_run": dry_run,
        "details": [],
        "ts_utc": _now_iso(),
    }
    if namespace:
        dirs = [_namespace_dir(namespace)]
    elif _root.exists():
        dirs = [d for d in _root.iterdir() if d.is_dir() and not d.name.startswith("_")]
    else:
        return summary

    for d in dirs:
        by_hash: dict[str, builtins_list[Path]] = {}
        for f in d.glob("*.json"):
            if f.name.startswith("_"):
                continue
            rec = _read_json(f)
            if rec is None:
                continue
            summary["scanned"] += 1
            h = rec.get("content_hash") or _hash(rec.get("value", ""))
            by_hash.setdefault(h, []).append(f)
        for h, paths in by_hash.items():
            if len(paths) < 2:
                continue
            summary["duplicates_found"] += len(paths) - 1
            paths.sort(key=lambda p: p.stat().st_mtime)
            survivor = paths[0]
            losers = paths[1:]
            if dry_run:
                summary["details"].append(
                    {"hash": h, "survivor": str(survivor), "losers": [str(p) for p in losers]}
                )
                continue
            rec = _read_json(survivor)
            if rec is None:
                continue
            rec["confidence"] = min(1.0, float(rec.get("confidence", 1.0)) + 0.1 * len(losers))
            rec["writes"] = int(rec.get("writes", 1)) + len(losers)
            rec["ts_utc_last"] = _now_iso()
            _write_json(survivor, rec)
            for p in losers:
                p.unlink(missing_ok=True)
            summary["merged"] += len(losers)
            summary["details"].append(
                {"hash": h, "survivor": str(survivor), "merged_count": len(losers)}
            )

    log_path = _root / "_consolidation-log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(summary, default=str) + "\n")
    return summary
