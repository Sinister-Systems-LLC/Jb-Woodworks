"""
bot_memory - shared loader + absorb implementation for Tier-2/Tier-3 Sinister Bots.

See 12_LLM_ORCHESTRATION/BOT-MEMORY-PROTOCOL.md for the full design.

Tier-1 bots (sentinel, translator, watcher, auditor, sinister-bus, custodian,
stealth-browser) don't need this - they have no LLM in the loop.

Usage from a bot's server.py:

    from agents._shared.bot_memory import load_memory, absorb_fact, list_facts, forget_fact

    SYSTEM_PROMPT = load_memory(bot_name="researcher")  # gets full system prompt

    @mcp.tool()
    def absorb(fact: str, source: str, tags: list[str] | None = None) -> dict:
        return absorb_fact("researcher", fact, source, tags or [])
"""

from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from . import codec as _codec  # type: ignore
    HAS_CODEC = True
except Exception:
    try:
        import codec as _codec  # type: ignore
        HAS_CODEC = True
    except Exception:
        HAS_CODEC = False

# Codec opt-in via env var so operator can flip globally.
CODEC_ENABLED = os.environ.get("SINISTER_MEMORY_CODEC", "1").lower() in ("1", "true", "yes")

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENTS_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents"
UNIVERSAL_GOTCHAS = HUB_ROOT / "09_REFERENCE" / "SANDBOX-GOTCHAS.md"
ABSORPTION_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "absorption-log.jsonl"
ABSORPTION_LOG.parent.mkdir(parents=True, exist_ok=True)
HEARTBEAT_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "heartbeat.jsonl"

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.environ.get("BOT_MEMORY_EMBED_MODEL", "nomic-embed-text")

# Smart-retrieval threshold: when learned.md has > N facts, do vector retrieval
# instead of full-dump. Below this, ship them all (cheaper than embed roundtrip).
SMART_RETRIEVAL_THRESHOLD = 20
DEFAULT_TOP_K = 10
RECENT_DAYS_ALWAYS_INCLUDE = 7


def _bot_dir(bot_name: str) -> Path:
    return AGENTS_DIR / bot_name


def _atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _log_absorption(entry: dict[str, Any]) -> None:
    """Append-only audit log."""
    with ABSORPTION_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(entry) + "\n")


_OLLAMA_CACHE: tuple[bool, float] | None = None
_OLLAMA_TTL = 30.0  # seconds; avoids 12x probes per memory_garden call


def _ollama_healthy() -> bool:
    """Cached 30s. Single probe per process unless explicitly reset."""
    global _OLLAMA_CACHE
    if not HAS_REQUESTS:
        return False
    import time as _t
    now = _t.time()
    if _OLLAMA_CACHE is not None:
        ok, ts = _OLLAMA_CACHE
        if (now - ts) < _OLLAMA_TTL:
            return ok
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        ok = (r.status_code == 200)
    except Exception:
        ok = False
    _OLLAMA_CACHE = (ok, now)
    return ok


def _embed(text: str) -> list[float] | None:
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text[:2000]},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        return r.json().get("embedding")
    except Exception:
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _fact_age_days(ts_iso: str) -> float | None:
    try:
        ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - ts).total_seconds() / 86400.0
    except Exception:
        return None


def _embeddings_cache_path(bot_name: str) -> Path:
    return _bot_dir(bot_name) / "learned-embeddings.jsonl"


def _load_embeddings_cache(bot_name: str) -> dict[str, list[float]]:
    """Map fact -> embedding vector. Persisted so we don't re-embed on every call."""
    p = _embeddings_cache_path(bot_name)
    if not p.exists():
        return {}
    out: dict[str, list[float]] = {}
    for line in _safe_read(p).splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            out[r["fact"]] = r["embedding"]
        except Exception:
            continue
    return out


def _append_embedding(bot_name: str, fact: str, embedding: list[float]) -> None:
    p = _embeddings_cache_path(bot_name)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"fact": fact, "embedding": embedding}) + "\n")


def _retrieve_relevant_facts(bot_name: str, query: str | None, top_k: int) -> tuple[list[dict[str, Any]], str]:
    """Smart-retrieve facts.

    Returns (selected_facts, mode) where mode in {"full", "recent+vector", "recent-only", "full-fallback"}.

    Strategy:
      - If total facts <= SMART_RETRIEVAL_THRESHOLD: return all (mode="full").
      - Else if Ollama up + query provided: return RECENT_DAYS_ALWAYS_INCLUDE-day facts + top-K vector matches (mode="recent+vector").
      - Else: return recent-only (mode="recent-only"). Cheap; deterministic.
    """
    all_facts = list_facts(bot_name, limit=10000)
    if not all_facts:
        return [], "full"
    if len(all_facts) <= SMART_RETRIEVAL_THRESHOLD:
        return all_facts, "full"

    # Pinned (tag:pin) facts always included
    pinned = [f for f in all_facts if "pin" in f.get("tags", []) or "pinned" in f.get("tags", [])]

    # Recent facts always included
    recent = []
    for f in all_facts:
        age = _fact_age_days(f.get("ts", ""))
        if age is not None and age <= RECENT_DAYS_ALWAYS_INCLUDE:
            recent.append(f)

    base = {id(f): f for f in pinned + recent}

    if query and _ollama_healthy():
        query_vec = _embed(query)
        if query_vec:
            cache = _load_embeddings_cache(bot_name)
            scored: list[tuple[float, dict[str, Any]]] = []
            for f in all_facts:
                if id(f) in base:
                    continue
                vec = cache.get(f["fact"])
                if vec is None:
                    vec = _embed(f["fact"])
                    if vec is not None:
                        _append_embedding(bot_name, f["fact"], vec)
                if vec is None:
                    continue
                scored.append((_cosine(query_vec, vec), f))
            scored.sort(key=lambda x: x[0], reverse=True)
            for score, f in scored[:top_k]:
                if score > 0.35:  # cosine-similarity floor; tunable
                    base[id(f)] = f
            return list(base.values()), "recent+vector"

    if recent or pinned:
        return list(base.values()), "recent-only"
    # Cold-start without Ollama: still return everything (truthfulness > token cost)
    return all_facts, "full-fallback"


def load_memory(bot_name: str, query: str | None = None, top_k: int = DEFAULT_TOP_K) -> str:
    """Concatenate the bot's full system prompt: SYSTEM-PROMPT + universal gotchas + bot gotchas + relevant learned facts.

    When `query` is supplied AND bot has many facts AND Ollama is up, only the
    top-K relevant facts (plus pinned + last-7-day) are included. Otherwise
    falls back to full dump.

    Returns a single string ready to be passed as a Claude/Ollama system prompt.
    Cache-eligible.
    """
    bot_dir = _bot_dir(bot_name)
    parts: list[str] = []

    sys_prompt = _safe_read(bot_dir / "SYSTEM-PROMPT.md")
    if sys_prompt.strip():
        parts.append(sys_prompt.strip())
    else:
        parts.append(f"[no SYSTEM-PROMPT.md found for {bot_name}; falling back to bot's hard-coded default]")

    universal = _safe_read(UNIVERSAL_GOTCHAS)
    if universal.strip():
        # Cap universal gotchas at 8KB to stop it dominating the prompt
        if len(universal) > 8000:
            universal = universal[:8000] + "\n\n... [truncated; see 09_REFERENCE/SANDBOX-GOTCHAS.md for full]"
        parts.append("\n\n# === Universal sandbox gotchas (do not attempt the blocked path; propose the green path) ===\n\n" + universal.strip())

    bot_gotchas = _safe_read(bot_dir / "KNOWN-GOTCHAS.md")
    if bot_gotchas.strip():
        parts.append(f"\n\n# === Bot-specific gotchas ({bot_name}) ===\n\n" + bot_gotchas.strip())

    # Smart retrieval of learned facts
    selected, mode = _retrieve_relevant_facts(bot_name, query, top_k)
    if selected:
        facts_lines = []
        for f in selected:
            fact_str = f['fact']
            # Apply codec to the fact body (NOT the metadata) for token savings
            if CODEC_ENABLED and HAS_CODEC:
                fact_str = _codec.encode(fact_str)
            line = f"- [{f['ts']}] {fact_str} (source: {f['source']})"
            if f.get('tags'):
                line += f" [tags: {','.join(f['tags'])}]"
            facts_lines.append(line)
        facts_block = "\n".join(facts_lines)
        codec_note = " (codec-encoded; bot can decode via bus.decode)" if CODEC_ENABLED and HAS_CODEC else ""
        parts.append(f"\n\n# === Absorbed facts ({bot_name}, mode={mode}, count={len(selected)}{codec_note}) ===\n\n" + facts_block)

    return "\n".join(parts)


def absorb_fact(bot_name: str, fact: str, source: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Add a fact to the bot's learned.md. Dedupes by exact-match. Logs to audit.
    Auto-embeds when Ollama is up (so smart retrieval works on next call)."""
    if not isinstance(fact, str) or not fact.strip():
        return {"ok": False, "error": "fact must be a non-empty string"}
    if not isinstance(source, str) or not source.strip():
        return {"ok": False, "error": "source must be a non-empty string (where did this fact come from?)"}
    fact = fact.strip()
    source = source.strip()
    tags = tags or []

    bot_dir = _bot_dir(bot_name)
    if not bot_dir.exists():
        return {"ok": False, "error": f"bot dir not found: {bot_dir}"}
    learned_path = bot_dir / "learned.md"

    existing = _safe_read(learned_path)
    if fact in existing:
        return {"ok": False, "error": "fact already absorbed (exact dedupe)", "fact": fact}

    ts = datetime.now(timezone.utc).isoformat()
    tag_str = ",".join(tags) if tags else ""
    line = f"- [{ts}] {fact} (source: {source})" + (f" [tags: {tag_str}]" if tag_str else "")
    new_content = existing.rstrip() + ("\n" if existing.strip() else "") + line + "\n"
    _atomic_write(learned_path, new_content)

    # Embed eagerly when Ollama is available so smart retrieval has the vector ready
    embedded = False
    if _ollama_healthy():
        vec = _embed(fact)
        if vec is not None:
            _append_embedding(bot_name, fact, vec)
            embedded = True

    count_after = sum(1 for ln in new_content.splitlines() if ln.strip().startswith("- ["))
    # Codec the fact for the audit log (operator preference) -- saves disk + grep
    # works on @token form. Original plaintext fact remains in learned.md on disk.
    log_fact = fact
    if CODEC_ENABLED and HAS_CODEC:
        log_fact = _codec.encode(fact)
    _log_absorption({
        "ts": ts,
        "bot": bot_name,
        "action": "absorb",
        "fact": log_fact,
        "fact_encoded": (log_fact != fact),
        "source": source,
        "tags": tags,
        "fact_count_after": count_after,
        "embedded": embedded,
    })
    _heartbeat(bot_name, "absorb")
    return {"ok": True, "fact_count_after": count_after, "path": str(learned_path), "embedded": embedded}


def _heartbeat(bot_name: str, kind: str) -> None:
    """Light append-only pulse log so health() can report aliveness."""
    try:
        HEARTBEAT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with HEARTBEAT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "bot": bot_name, "kind": kind}) + "\n")
    except Exception:
        pass


def heartbeat_stats(bot_name: str) -> dict[str, Any]:
    """Read recent heartbeat lines for this bot. Used by every bot's health()."""
    if not HEARTBEAT_LOG.exists():
        return {"lifetime_calls": 0, "last_called": None, "last_absorbed": None}
    last_called = None
    last_absorbed = None
    lifetime = 0
    try:
        for line in HEARTBEAT_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("bot") != bot_name:
                continue
            lifetime += 1
            ts = r.get("ts")
            last_called = ts
            if r.get("kind") == "absorb":
                last_absorbed = ts
    except Exception:
        pass
    return {"lifetime_calls": lifetime, "last_called": last_called, "last_absorbed": last_absorbed}


def list_facts(bot_name: str, limit: int = 50) -> list[dict[str, Any]]:
    """Parse learned.md back into structured records."""
    bot_dir = _bot_dir(bot_name)
    learned = _safe_read(bot_dir / "learned.md")
    out = []
    pattern = re.compile(r"^- \[(?P<ts>[^\]]+)\] (?P<fact>.+?) \(source: (?P<source>.+?)\)(?: \[tags: (?P<tags>[^\]]+)\])?$")
    for line in learned.splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        out.append({
            "ts": m.group("ts"),
            "fact": m.group("fact"),
            "source": m.group("source"),
            "tags": (m.group("tags") or "").split(",") if m.group("tags") else [],
        })
    return out[-limit:]


def forget_fact(bot_name: str, fact_substring: str) -> dict[str, Any]:
    """Remove all lines from learned.md whose fact contains fact_substring. Logged."""
    if not isinstance(fact_substring, str) or len(fact_substring) < 4:
        return {"ok": False, "error": "fact_substring must be >= 4 chars (avoid accidental mass-delete)"}
    bot_dir = _bot_dir(bot_name)
    learned_path = bot_dir / "learned.md"
    existing = _safe_read(learned_path)
    if not existing.strip():
        return {"ok": True, "removed": 0, "note": "learned.md empty"}
    kept = []
    removed = []
    for line in existing.splitlines():
        if line.strip().startswith("- [") and fact_substring in line:
            removed.append(line)
        else:
            kept.append(line)
    if not removed:
        return {"ok": True, "removed": 0, "note": f"no facts contained: {fact_substring}"}
    _atomic_write(learned_path, "\n".join(kept) + "\n")
    ts = datetime.now(timezone.utc).isoformat()
    for r in removed:
        _log_absorption({
            "ts": ts,
            "bot": bot_name,
            "action": "forget",
            "removed_line": r,
            "match": fact_substring,
        })
    return {"ok": True, "removed": len(removed)}


def memory_stats(bot_name: str) -> dict[str, Any]:
    """Quick health view of a bot's memory + aliveness signals.
    Single list_facts call per invocation (was 2x). Ollama check is module-cached."""
    bot_dir = _bot_dir(bot_name)
    embeds = _load_embeddings_cache(bot_name)
    facts = list_facts(bot_name, limit=10000)
    fact_count = len(facts)
    base = {
        "bot": bot_name,
        "has_system_prompt": (bot_dir / "SYSTEM-PROMPT.md").exists(),
        "has_known_gotchas": (bot_dir / "KNOWN-GOTCHAS.md").exists(),
        "has_learned": (bot_dir / "learned.md").exists(),
        "fact_count": fact_count,
        "embedded_fact_count": len(embeds),
        "universal_gotchas_present": UNIVERSAL_GOTCHAS.exists(),
        "absorption_log_size": ABSORPTION_LOG.stat().st_size if ABSORPTION_LOG.exists() else 0,
        "ollama_for_retrieval": _ollama_healthy(),
        "smart_retrieval_active": fact_count > SMART_RETRIEVAL_THRESHOLD,
    }
    base.update(heartbeat_stats(bot_name))
    return base
