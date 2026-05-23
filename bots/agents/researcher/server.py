"""
Researcher agent — chains stealth-browser scrapes + Ollama summarization.

Tier 2 (Ollama; $0). Falls back to plain returns when Ollama down (caller gets the
raw scrape and can decide what to do).

The key cost-saving move: operator says "look up X" -> researcher picks a URL,
hands off to stealth-browser, summarizes locally via qwen2.5-coder:7b, returns
~500 tokens to the operator instead of paying Opus to ingest a 50KB page.

Tools:
  researcher.lookup(query, url=None, top_k=3)        -> {answer, sources}
  researcher.summarize_url(url, focus=None)          -> {summary, source_url, mode}
  researcher.compare(urls, focus)                    -> {comparison, sources}
  researcher.health()                                -> {ok, ollama_healthy, stealth_available}

Note: researcher CALLS stealth-browser by importing its module locally (so we don't
need real MCP-to-MCP wiring yet). When this fleet eventually grows an HTTP layer,
this becomes a real cross-agent dispatch.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[researcher] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Bot memory loader (see 12_LLM_ORCHESTRATION/BOT-MEMORY-PROTOCOL.md)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from _shared import bot_memory  # type: ignore
    HAS_BOT_MEMORY = True
except Exception:
    HAS_BOT_MEMORY = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "researcher"
AGENT_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
STEALTH_SERVER = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "stealth-browser" / "server.py"

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
SYNTH_MODEL = os.environ.get("RESEARCHER_MODEL", "qwen2.5-coder:7b")

# Lazy-loaded stealth-browser module (so researcher can run even if stealth deps missing)
_stealth = None


def log_call(tool: str, model: str | None = None, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "researcher",
        "model": model,
        "input_tokens": extra.pop("input_tokens", 0),
        "output_tokens": extra.pop("output_tokens", 0),
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def get_stealth():
    """Lazy-import the stealth-browser module from its own path."""
    global _stealth
    if _stealth is not None:
        return _stealth
    if not STEALTH_SERVER.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("stealth_browser_server", STEALTH_SERVER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _stealth = mod
        return mod
    except Exception as e:
        print(f"[researcher] stealth-browser load failed: {e}", file=sys.stderr)
        return None


def ollama_healthy() -> bool:
    if not HAS_REQUESTS:
        return False
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_system_prompt_prefix() -> str:
    """Prepend the loaded SYSTEM-PROMPT + gotchas + learned facts to the Ollama prompt."""
    if HAS_BOT_MEMORY:
        sys = bot_memory.load_memory("researcher")
        if sys and "[no SYSTEM-PROMPT.md found" not in sys:
            return f"# Role + persistent memory\n\n{sys}\n\n# === Task ===\n\n"
    return ""


def ollama_summarize(text: str, focus: str | None = None) -> str | None:
    """Summarize a page via Ollama. Returns None on failure."""
    if not HAS_REQUESTS or not ollama_healthy():
        return None
    prompt = (
        get_system_prompt_prefix()
        + f"Summarize the following page content. "
        + (f"Focus on: {focus}.\n\n" if focus else "Give a tight 5-10 bullet summary covering the page's main claims, key facts, and any actionable items.\n\n")
        + f"Page text:\n{text[:12000]}"
    )
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": SYNTH_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.1, "num_predict": 600}},
            timeout=60,
        )
        if r.status_code != 200:
            return None
        return r.json().get("response", "").strip()
    except Exception:
        return None


def _call(name: str, *args, **kwargs):
    """Call a stealth-browser tool by name, handling the @mcp.tool() wrapper."""
    st = get_stealth()
    if st is None:
        return {"ok": False, "error": "stealth-browser module not available"}
    fn = getattr(st, name, None)
    if fn is None:
        return {"ok": False, "error": f"stealth tool not found: {name}"}
    # FastMCP-decorated tools expose .fn for the underlying callable in some versions
    raw = getattr(fn, "fn", fn)
    try:
        return raw(*args, **kwargs)
    except Exception as e:
        return {"ok": False, "error": f"stealth.{name} raised: {e}"}


mcp = FastMCP("researcher")


@mcp.tool()
def lookup(query: str, url: str | None = None, top_k: int = 3) -> dict[str, Any]:
    """Look up a topic. If url is given, summarize that page. Otherwise, return guidance.

    This intentionally does NOT do web search itself — that needs a search-engine
    integration. For now: operator (or another agent) provides URL; researcher
    handles fetch + summarize.
    """
    log_call("lookup", query=query[:200], url=(url or "")[:200])
    if not url:
        return {
            "ok": False,
            "error": "researcher.lookup currently requires a URL. Use translator/librarian first to find candidate URLs, then call again with url=...",
            "hint": "Future: integrate with a search-engine MCP (Brave/DuckDuckGo) and auto-pick top_k results.",
        }
    summary_result = summarize_url(url=url, focus=query)
    return {"ok": summary_result.get("ok", True), "answer": summary_result.get("summary"),
            "sources": [url], "mode": summary_result.get("mode"), "query": query}


@mcp.tool()
def summarize_url(url: str, focus: str | None = None) -> dict[str, Any]:
    """Open URL via stealth-browser, scrape text, summarize via Ollama."""
    log_call("summarize_url", url=url[:200])
    open_res = _call("open", url)
    if not open_res.get("ok"):
        return {"ok": False, "error": f"stealth.open failed: {open_res.get('error')}", "source_url": url}
    scrape = _call("scrape_text", max_chars=20000)
    if not scrape.get("ok"):
        return {"ok": False, "error": f"stealth.scrape_text failed: {scrape.get('error')}", "source_url": url}
    text = scrape.get("text", "")
    if not text.strip():
        return {"ok": False, "error": "page returned empty text", "source_url": url, "title": open_res.get("title")}
    summary = ollama_summarize(text, focus=focus)
    if summary is None:
        # Fall back: return the raw text (caller decides what to do)
        return {
            "ok": True,
            "mode": "raw",
            "fallback_reason": "Ollama unavailable",
            "source_url": url,
            "title": open_res.get("title"),
            "text_preview": text[:2000],
            "text_length": len(text),
        }
    log_call("summarize_url", model=SYNTH_MODEL, url=url[:200], summary_chars=len(summary))
    return {
        "ok": True,
        "mode": "ollama",
        "model": SYNTH_MODEL,
        "source_url": url,
        "title": open_res.get("title"),
        "summary": summary,
        "text_length": len(text),
    }


@mcp.tool()
def compare(urls: list[str], focus: str) -> dict[str, Any]:
    """Summarize multiple URLs, then ask Ollama for a comparison along `focus`."""
    log_call("compare", urls=len(urls), focus=focus[:200])
    summaries = []
    for u in urls[:5]:  # cap to avoid runaway
        r = summarize_url(url=u, focus=focus)
        summaries.append({"url": u, "summary": r.get("summary") or r.get("text_preview"), "title": r.get("title")})
    if not summaries:
        return {"ok": False, "error": "no URLs summarized"}
    if not ollama_healthy() or not HAS_REQUESTS:
        return {"ok": True, "mode": "raw", "summaries": summaries,
                "fallback_reason": "Ollama unavailable; returning individual summaries"}
    blob = "\n\n---\n\n".join(f"SOURCE {i+1}: {s['url']}\nTITLE: {s.get('title')}\n{s.get('summary')}" for i, s in enumerate(summaries))
    prompt = f"Compare these sources along the focus: {focus}.\nIdentify agreements, contradictions, and any unique claims per source.\n\n{blob[:14000]}"
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": SYNTH_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.1, "num_predict": 800}},
            timeout=90,
        )
        if r.status_code != 200:
            return {"ok": True, "mode": "raw", "summaries": summaries, "fallback_reason": f"ollama HTTP {r.status_code}"}
        comparison = r.json().get("response", "").strip()
    except Exception as e:
        return {"ok": True, "mode": "raw", "summaries": summaries, "fallback_reason": str(e)}
    return {"ok": True, "mode": "ollama", "model": SYNTH_MODEL, "comparison": comparison,
            "sources": [s["url"] for s in summaries]}


@mcp.tool()
def absorb(fact: str, source: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Persist a fact into researcher's memory. Audit-logged. See BOT-MEMORY-PROTOCOL.md."""
    if not HAS_BOT_MEMORY:
        return {"ok": False, "error": "bot_memory module not loadable"}
    return bot_memory.absorb_fact("researcher", fact, source, tags or [])


@mcp.tool()
def list_facts(limit: int = 50) -> list[dict[str, Any]]:
    if not HAS_BOT_MEMORY:
        return []
    return bot_memory.list_facts("researcher", limit=limit)


@mcp.tool()
def forget(fact_substring: str) -> dict[str, Any]:
    if not HAS_BOT_MEMORY:
        return {"ok": False, "error": "bot_memory module not loadable"}
    return bot_memory.forget_fact("researcher", fact_substring)


@mcp.tool()
def health() -> dict[str, Any]:
    """Health check - Ollama + stealth-browser + bot memory."""
    log_call("health")
    st = get_stealth()
    mem_stats = bot_memory.memory_stats("researcher") if HAS_BOT_MEMORY else {}
    return {
        "ok": True,
        "agent": "researcher",
        "ollama_healthy": ollama_healthy() if HAS_REQUESTS else False,
        "model": SYNTH_MODEL,
        "stealth_available": st is not None,
        "stealth_has_nodriver": getattr(st, "HAS_NODRIVER", False) if st else False,
        "bot_memory": {"loaded": HAS_BOT_MEMORY, **mem_stats},
    }


if __name__ == "__main__":
    mcp.run()
