"""
Translator agent — semantic search across 160+ MCP tools.

Pure Python (no LLM). Reads 04_MCP/_catalog/ALL-TOOLS.md + by-keyword/ shards
and surfaces matching tools when operator asks "is there an MCP tool for X?"

Tier 1 (zero cost). Tools:
  translator.find_tool(query, top_k=5) -> [{server, tool, signature, snippet}]
  translator.list_servers()             -> [{name, tool_count}]
  translator.tools_by_server(server)    -> [{name, signature, snippet}]
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[translator] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
CATALOG_DIR = HUB_ROOT / "04_MCP" / "_catalog"
ALL_TOOLS_PATH = CATALOG_DIR / "ALL-TOOLS.md"
BY_SERVER_DIR = CATALOG_DIR / "by-server"
BY_KEYWORD_DIR = CATALOG_DIR / "by-keyword"
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)


def log_call(tool: str, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "translator",
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


_TOOL_CACHE: list[dict[str, Any]] | None = None
_CACHE_MTIME: float = 0.0


def _parse_by_server_files() -> list[dict[str, Any]]:
    """Walk 04_MCP/_catalog/by-server/*.md, extract each tool entry."""
    tools = []
    if not BY_SERVER_DIR.exists():
        return tools
    tool_pattern = re.compile(r"^-\s+`([a-z][a-z0-9_-]*\.[a-z0-9_.\-]+)`(?:\s+—\s+(.+))?$")
    for md in BY_SERVER_DIR.glob("*.md"):
        server_name = md.stem
        for line in md.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = tool_pattern.match(line.strip())
            if m:
                tools.append({
                    "server": server_name,
                    "tool": m.group(1),
                    "snippet": (m.group(2) or "").strip(),
                    "source_file": str(md.relative_to(HUB_ROOT)),
                })
    return tools


def get_tools(force_refresh: bool = False) -> list[dict[str, Any]]:
    """Cached read of all tool entries. Refreshes when catalog files change."""
    global _TOOL_CACHE, _CACHE_MTIME
    if not BY_SERVER_DIR.exists():
        return []
    latest_mtime = max(
        (f.stat().st_mtime for f in BY_SERVER_DIR.glob("*.md")),
        default=0.0,
    )
    if force_refresh or _TOOL_CACHE is None or latest_mtime > _CACHE_MTIME:
        _TOOL_CACHE = _parse_by_server_files()
        _CACHE_MTIME = latest_mtime
    return _TOOL_CACHE


def _score(query: str, tool_name: str, snippet: str) -> float:
    """Score = combination of substring match + fuzzy ratio."""
    q = query.lower()
    name = tool_name.lower()
    desc = (snippet or "").lower()
    # Substring matches weight high
    base = 0.0
    if q in name:
        base += 1.0
    elif any(p in name for p in q.split()):
        base += 0.6
    if q in desc:
        base += 0.4
    elif any(p in desc for p in q.split()):
        base += 0.2
    # Fuzzy ratio on name
    base += SequenceMatcher(None, q, name).ratio() * 0.5
    return base


# ===== MCP server =====
mcp = FastMCP("translator")


@mcp.tool()
def find_tool(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Semantic search across all MCP tools (across 7 servers, ~160 tools).

    Returns top-N matching tools ranked by relevance. Each result has
    {server, tool, signature, snippet, score}.
    """
    log_call("find_tool", query=query, top_k=top_k)
    tools = get_tools()
    if not tools:
        return [{"error": "Tool catalog empty. Confirm 04_MCP/_catalog/by-server/ exists."}]
    scored = [(t, _score(query, t["tool"], t["snippet"])) for t in tools]
    scored.sort(key=lambda x: x[1], reverse=True)
    out = []
    for t, score in scored[:top_k]:
        if score < 0.1:
            break
        out.append({**t, "score": round(score, 3)})
    return out


@mcp.tool()
def list_servers() -> list[dict[str, Any]]:
    """List all MCP servers + their tool counts."""
    log_call("list_servers")
    tools = get_tools()
    counts: dict[str, int] = {}
    for t in tools:
        counts[t["server"]] = counts.get(t["server"], 0) + 1
    return [{"name": s, "tool_count": c} for s, c in sorted(counts.items())]


@mcp.tool()
def tools_by_server(server: str) -> list[dict[str, Any]]:
    """List all tools for a given server."""
    log_call("tools_by_server", server=server)
    tools = get_tools()
    return [t for t in tools if t["server"].lower() == server.lower()]


@mcp.tool()
def refresh_catalog() -> dict[str, Any]:
    """Force re-read of the tool catalog from disk."""
    log_call("refresh_catalog")
    tools = get_tools(force_refresh=True)
    return {"ok": True, "tool_count": len(tools)}


@mcp.tool()
def health() -> dict[str, Any]:
    """Health check."""
    log_call("health")
    tools = get_tools()
    return {
        "ok": True,
        "agent": "translator",
        "catalog_dir": str(BY_SERVER_DIR),
        "tool_count": len(tools),
        "cache_mtime": _CACHE_MTIME,
    }


if __name__ == "__main__":
    mcp.run()
