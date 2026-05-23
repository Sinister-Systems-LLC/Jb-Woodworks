"""
Librarian agent — RAG over 02_MD_ARCHIVE (8,500+ .md files).

Tier 2 default: Ollama (qwen2.5-coder:7b for synthesis, nomic-embed-text for embeddings).
Fallback: grep-only (zero LLM, deterministic) when Ollama down.

Index: FAISS over chunked markdown. Stored at agents/librarian/index/.
First-run index build: ~3-5 min depending on hardware.

Tools:
  librarian.search(query, top_k=5)            -> [{path, snippet, score}]
  librarian.reindex(section=None)             -> {ok, indexed_count}
  librarian.health()                          -> {ok, index_size, ollama_status}
  librarian.grep_fallback(query, top_k=5)     -> [{path, line, content}] (when Ollama down)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[librarian] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Optional imports (graceful degradation if missing)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import faiss
    import numpy as np
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
ARCHIVE_DIR = HUB_ROOT / "02_MD_ARCHIVE"
KEYWORD_DIR = ARCHIVE_DIR / "_index" / "by-keyword"
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "librarian"
INDEX_DIR = AGENT_DIR / "index"
INDEX_DIR.mkdir(parents=True, exist_ok=True)
FAISS_INDEX_PATH = INDEX_DIR / "faiss.index"
METADATA_PATH = INDEX_DIR / "metadata.jsonl"
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"
SYNTH_MODEL = "qwen2.5-coder:7b"

CHUNK_SIZE = 1500  # chars per chunk
CHUNK_OVERLAP = 200


def log_call(tool: str, model: str | None = None, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "librarian",
        "model": model,
        "input_tokens": extra.pop("input_tokens", 0),
        "output_tokens": extra.pop("output_tokens", 0),
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def ollama_healthy() -> bool:
    if not HAS_REQUESTS:
        return False
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def embed(text: str) -> list[float] | None:
    """Get embedding from Ollama. Returns None if Ollama unreachable."""
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        if r.status_code != 200:
            return None
        return r.json().get("embedding")
    except Exception:
        return None


def chunk_markdown(text: str) -> list[str]:
    """Naive chunker — by character count with overlap."""
    out = []
    i = 0
    while i < len(text):
        chunk = text[i:i + CHUNK_SIZE]
        if chunk.strip():
            out.append(chunk)
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return out


def grep_search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Pure-Python grep fallback. Reads the keyword shards first."""
    q = query.lower()
    results: list[dict[str, Any]] = []
    # 1) Try matching a known keyword shard
    keyword_words = set(re.findall(r"[a-z0-9]+", q))
    for kw in keyword_words:
        kw_file = KEYWORD_DIR / f"{kw}.md"
        if kw_file.exists():
            for line in kw_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("- "):
                    results.append({"path": str(kw_file.relative_to(HUB_ROOT)), "line": 0, "content": line[:200]})
                    if len(results) >= top_k:
                        return results
    # 2) Brute grep across archive (slower)
    if results:
        return results[:top_k]
    pattern = re.compile(re.escape(q), re.IGNORECASE)
    for md in ARCHIVE_DIR.rglob("*.md"):
        try:
            for lineno, line in enumerate(md.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if pattern.search(line):
                    results.append({
                        "path": str(md.relative_to(HUB_ROOT)),
                        "line": lineno,
                        "content": line.strip()[:200],
                    })
                    if len(results) >= top_k:
                        return results
        except Exception:
            continue
    return results


# ===== MCP server =====
mcp = FastMCP("librarian")


@mcp.tool()
def search(query: str, top_k: int = 5) -> dict[str, Any]:
    """Search the MD archive. Uses FAISS + Ollama if available, else grep fallback.

    Returns {results: [{path, snippet, score}], mode: 'vector'|'grep'}.
    """
    if HAS_FAISS and HAS_REQUESTS and ollama_healthy() and FAISS_INDEX_PATH.exists():
        # Vector search path
        log_call("search", model=EMBED_MODEL, mode="vector", query=query[:100])
        qvec = embed(query)
        if qvec is None:
            # fall through to grep
            results = grep_search(query, top_k)
            return {"results": results, "mode": "grep", "fallback_reason": "embed failed"}
        index = faiss.read_index(str(FAISS_INDEX_PATH))
        metadata = [json.loads(l) for l in METADATA_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
        qarr = np.array([qvec], dtype="float32")
        scores, ids = index.search(qarr, top_k)
        out = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            m = metadata[idx]
            out.append({"path": m["path"], "snippet": m["chunk"][:300], "score": float(score)})
        return {"results": out, "mode": "vector"}
    # Grep fallback
    log_call("search", mode="grep", query=query[:100])
    results = grep_search(query, top_k)
    return {"results": results, "mode": "grep", "fallback_reason": "Ollama or FAISS unavailable"}


@mcp.tool()
def reindex(section: str | None = None) -> dict[str, Any]:
    """Build or rebuild the FAISS index from 02_MD_ARCHIVE/.

    If section is given, only re-indexes that subdirectory.
    Requires Ollama + FAISS available; otherwise returns error.
    """
    log_call("reindex", section=section or "all")
    if not (HAS_FAISS and HAS_REQUESTS):
        return {"ok": False, "error": "Install requirements: pip install faiss-cpu requests numpy"}
    if not ollama_healthy():
        return {"ok": False, "error": "Ollama unreachable. Start docker compose up -d in 12_LLM_ORCHESTRATION/docker/"}
    scan_dir = ARCHIVE_DIR / section if section else ARCHIVE_DIR
    if not scan_dir.exists():
        return {"ok": False, "error": f"section not found: {scan_dir}"}
    metadata = []
    vectors = []
    files_seen = 0
    for md in scan_dir.rglob("*.md"):
        if md.name.startswith("_"):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if len(text) < 50:
            continue
        chunks = chunk_markdown(text)
        for chunk in chunks:
            v = embed(chunk)
            if v is None:
                continue
            vectors.append(v)
            metadata.append({
                "path": str(md.relative_to(HUB_ROOT)),
                "chunk": chunk,
                "sha": hashlib.sha256(chunk.encode()).hexdigest()[:16],
            })
        files_seen += 1
        if files_seen % 100 == 0:
            print(f"[librarian] reindex: {files_seen} files processed", flush=True)
    if not vectors:
        return {"ok": False, "error": "No vectors generated"}
    dim = len(vectors[0])
    index = faiss.IndexFlatIP(dim)
    arr = np.array(vectors, dtype="float32")
    # normalize for cosine similarity via inner product
    faiss.normalize_L2(arr)
    index.add(arr)
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    METADATA_PATH.write_text("\n".join(json.dumps(m) for m in metadata), encoding="utf-8")
    return {"ok": True, "indexed_count": len(vectors), "files_seen": files_seen, "dim": dim}


@mcp.tool()
def grep_fallback(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Pure-grep search (always available, even without Ollama/FAISS)."""
    log_call("grep_fallback", query=query[:100])
    return grep_search(query, top_k)


@mcp.tool()
def health() -> dict[str, Any]:
    """Health check."""
    log_call("health")
    return {
        "ok": True,
        "agent": "librarian",
        "has_faiss": HAS_FAISS,
        "has_requests": HAS_REQUESTS,
        "ollama_healthy": ollama_healthy() if HAS_REQUESTS else False,
        "index_exists": FAISS_INDEX_PATH.exists(),
        "index_size_bytes": FAISS_INDEX_PATH.stat().st_size if FAISS_INDEX_PATH.exists() else 0,
        "fallback_mode": not (HAS_FAISS and HAS_REQUESTS and ollama_healthy() and FAISS_INDEX_PATH.exists()),
    }


if __name__ == "__main__":
    mcp.run()
