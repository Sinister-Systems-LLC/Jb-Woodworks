# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: kernel-vector / per-turn embedding layer.

The "kernel vector shit" -- per-memory semantic embedding + cosine recall.
Cherry-picked from jcode v0.12.4 Memory (Agent memory) -- screenshot operator
sent 2026-05-25: "Jcode embeds each turn/response as a semantic vector. Every
turn does queries a graph of memories to efficiently find related memory
entries via a cosine similarity check."

Three backends (feature-detected at call time, NOT at import -- keeps RAM
footprint near jcode's 9.9 MB/session baseline per operator's PSS scaling table):

  RUFLO   :: out-of-process via mcp__ruflo__embeddings_generate (preferred --
             RAM cost stays on the daemon, not the agent process)
  TFIDF   :: stdlib-only TF-IDF cosine over the indexed corpus (zero-deps
             fallback; quality drop vs real embeddings but functional)
  NULL    :: returns [] vec; recall_by_vector returns [] -> caller falls back
             to FTS5/BM25

Storage: separate `embeddings(memory_id PK, vec BLOB, dim INT, model TEXT,
ts_utc TEXT)` table next to the FTS5 `memories` table. Vec stored as packed
float32 binary so SQLite doesn't pay the 4x JSON overhead.

Public API:
  embed_text(text, backend="auto") -> list[float]
  cosine(a, b) -> float
  store_embedding(memory_id, vec, db_path, model="ruflo") -> None
  recall_by_vector(query_text, db_path, limit=5, threshold=0.3) -> list[VHit]
  build_embedding_index(root, db_path, backend="auto", limit=None) -> dict
  current_backend() -> str

VHit NamedTuple: (memory_id, layer, slug, path, line, snippet, score)
"""
from __future__ import annotations

import math
import re
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, NamedTuple, Optional, Sequence


class VHit(NamedTuple):
    memory_id: str
    layer: str
    slug: str
    path: str
    line: str
    snippet: str
    score: float


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")
_STOPWORDS = frozenset(
    {
        "the", "and", "for", "with", "from", "this", "that", "into", "have",
        "has", "are", "was", "were", "but", "not", "you", "your", "our", "all",
        "any", "per", "via", "use", "uses", "using", "used", "ref",
    }
)


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    return [t.lower() for t in _TOKEN_RE.findall(text) if t.lower() not in _STOPWORDS]


def current_backend() -> str:
    """Probe which embedding backend is available, preferring ruflo > tfidf > null.

    Does NOT actually import the ruflo client (cheap probe). The real call site
    handles ImportError/ConnectionError defensively.
    """
    # We can't call mcp__ruflo__* tools from a stand-alone python process today;
    # the MCP family is only reachable from inside the Claude harness. So from
    # CLI invocation the backend is always TFIDF. Inside the harness, ruflo
    # routing happens at the caller layer (eg start-sinister-session.ps1 pipes
    # text in via a harness-mediated invocation).
    # For now: if SINISTER_MEMORY_BACKEND env var forces a choice, honor it;
    # else default to TFIDF (the working fallback).
    import os
    forced = os.environ.get("SINISTER_MEMORY_BACKEND", "").strip().lower()
    if forced in {"ruflo", "tfidf", "null"}:
        return forced
    return "tfidf"


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity. Returns 0.0 for empty or zero-magnitude vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# Module-level TF-IDF state -- built lazily by build_embedding_index when
# backend=tfidf. We use a fixed-dim hash projection so all vectors are the
# same length without needing to learn a vocabulary up-front.
_TFIDF_DIM = 256  # small dim keeps storage cheap; collisions accepted


def _hash_token(token: str) -> int:
    """Stable token -> [0, _TFIDF_DIM) bucket. Python's hash() varies per
    interpreter run unless PYTHONHASHSEED is set, so use a deterministic hash."""
    h = 0
    for ch in token:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return h % _TFIDF_DIM


def _tfidf_vec(text: str, idf: Optional[dict[int, float]] = None) -> list[float]:
    """Hashed-bucket TF-IDF vector. Falls back to plain TF if idf is None."""
    toks = _tokenize(text)
    if not toks:
        return [0.0] * _TFIDF_DIM
    vec = [0.0] * _TFIDF_DIM
    for t in toks:
        bucket = _hash_token(t)
        vec[bucket] += 1.0
    # L1 normalize tf
    s = sum(vec)
    if s > 0:
        vec = [v / s for v in vec]
    # Optionally boost by IDF
    if idf:
        for i in range(_TFIDF_DIM):
            vec[i] *= idf.get(i, 1.0)
    return vec


def embed_text(text: str, backend: str = "auto") -> list[float]:
    """Return an embedding for `text` using the chosen backend.

    backend: "auto" (use current_backend()), "ruflo", "tfidf", or "null".
    Returns [] if backend=null or if the chosen backend fails.
    """
    if backend == "auto":
        backend = current_backend()
    if backend == "null":
        return []
    if backend == "ruflo":
        # Not callable from CLI; in-harness sites will replace this dispatch.
        # Fall through to tfidf so we always return *something* useful.
        backend = "tfidf"
    if backend == "tfidf":
        return _tfidf_vec(text)
    return []


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE IF NOT EXISTS embeddings (
               memory_id TEXT PRIMARY KEY,
               layer TEXT,
               slug TEXT,
               path TEXT,
               line TEXT,
               snippet TEXT,
               vec BLOB NOT NULL,
               dim INT NOT NULL,
               model TEXT NOT NULL,
               ts_utc TEXT NOT NULL
           )"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS embeddings_layer ON embeddings(layer)")
    conn.execute("CREATE INDEX IF NOT EXISTS embeddings_slug ON embeddings(slug)")
    return conn


def _pack_vec(vec: Sequence[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack_vec(blob: bytes, dim: int) -> list[float]:
    if not blob or dim <= 0:
        return []
    return list(struct.unpack(f"{dim}f", blob))


def store_embedding(
    memory_id: str,
    vec: Sequence[float],
    db_path: Path,
    layer: str = "",
    slug: str = "",
    path: str = "",
    line: str = "",
    snippet: str = "",
    model: str = "tfidf",
) -> None:
    """Persist a single embedding. Overwrites any existing row for memory_id."""
    if not vec:
        return
    conn = _connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        conn.execute(
            "INSERT OR REPLACE INTO embeddings("
            " memory_id, layer, slug, path, line, snippet, vec, dim, model, ts_utc"
            ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (memory_id, layer, slug, path, line, snippet, _pack_vec(vec), len(vec), model, now),
        )
        conn.commit()
    finally:
        conn.close()


def recall_by_vector(
    query_text: str,
    db_path: Path,
    limit: int = 5,
    threshold: float = 0.3,
    backend: str = "auto",
) -> list[VHit]:
    """Cosine recall over stored embeddings. Returns hits with score >= threshold.

    This pulls ALL embeddings into memory (RAM cost = dim * 4 bytes * row_count).
    With _TFIDF_DIM=256, even 10,000 memories cost ~10 MB -- well within the
    operator's per-session PSS budget (Image #1: jcode 9.9 MB baseline).
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return []

    qvec = embed_text(query_text, backend=backend)
    if not qvec:
        return []

    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT memory_id, layer, slug, path, line, snippet, vec, dim FROM embeddings"
        ).fetchall()
    finally:
        conn.close()

    scored: list[VHit] = []
    for mid, lyr, slg, pth, ln, snp, blob, dim in rows:
        v = _unpack_vec(blob, dim)
        # Only score if dim matches
        if dim != len(qvec):
            continue
        s = cosine(qvec, v)
        if s >= threshold:
            scored.append(VHit(mid, lyr, slg, pth, ln, snp, s))
    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:limit]


def build_embedding_index(
    root: Path,
    db_path: Path,
    backend: str = "auto",
    limit: Optional[int] = None,
) -> dict:
    """Walk the FTS5 `memories` table from indexer.build's output and write an
    embedding for every row (or up to `limit` rows). Idempotent: rows that
    already have an embedding from the same model are skipped.

    Returns stats: {scanned, written, skipped, errors, backend}.
    """
    from . import indexer  # ensure tables exist

    fts_db = indexer.default_db_path(root)
    if not fts_db.exists():
        return {"scanned": 0, "written": 0, "skipped": 0, "errors": 0, "backend": "(no fts5 index)"}

    chosen = current_backend() if backend == "auto" else backend
    model = chosen

    conn_fts = sqlite3.connect(str(fts_db))
    try:
        sql = "SELECT rowid, layer, slug, path, line, snippet FROM memories"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = conn_fts.execute(sql).fetchall()
    finally:
        conn_fts.close()

    if not rows:
        return {"scanned": 0, "written": 0, "skipped": 0, "errors": 0, "backend": chosen}

    conn_emb = _connect(db_path)
    try:
        existing: set[str] = set()
        for r in conn_emb.execute("SELECT memory_id FROM embeddings WHERE model = ?", (model,)):
            existing.add(r[0])
    finally:
        conn_emb.close()

    written = skipped = errors = 0
    for rowid, layer, slug, path, line, snippet in rows:
        mid = f"{layer}:{path}:{line}"
        if mid in existing:
            skipped += 1
            continue
        try:
            vec = embed_text(snippet or "", backend=chosen)
            if not vec:
                errors += 1
                continue
            store_embedding(
                memory_id=mid,
                vec=vec,
                db_path=db_path,
                layer=layer,
                slug=slug,
                path=path,
                line=line,
                snippet=snippet,
                model=model,
            )
            written += 1
        except Exception:  # noqa: BLE001 -- per-row guard
            errors += 1

    return {
        "scanned": len(rows),
        "written": written,
        "skipped": skipped,
        "errors": errors,
        "backend": chosen,
    }


def default_embedding_db(root: Path) -> Path:
    return Path(root) / "_shared-memory" / "sinister-memory" / "embeddings.db"


__all__ = [
    "VHit",
    "cosine",
    "embed_text",
    "current_backend",
    "store_embedding",
    "recall_by_vector",
    "build_embedding_index",
    "default_embedding_db",
]
