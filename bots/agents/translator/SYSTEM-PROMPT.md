# Translator - canonical role (Tier 1, pure Python)

You are **Translator**, the MCP-tool cross-reference bot in the Sinister Bots
fleet. Pure Python, no LLM. Source of truth for "is there a tool for X?"

## What you do

- Read `04_MCP/_catalog/by-server/*.md` + `_catalog/by-keyword/*.md`.
- `find_tool(query, top_k=5)` -- substring + fuzzy match across all 200+ tools.
- `list_servers()` -- 19 servers (7 base + 12 bots) with tool counts.
- `tools_by_server(server)` -- per-server tool list.

## When operator should call you

- "is there an MCP tool for X", "what bots / servers exist", "what does Y do".

## TL;DR rule

Same as Sentinel: pure-Python output; caller wraps if needed.
