# Translator agent

**Role:** Semantic search across the 160+ MCP tools (7 servers).

**Tier:** 1 (pure Python). Zero LLM cost.

## Tools

| Tool | Args | Returns |
|---|---|---|
| `translator.find_tool` | `query, top_k=5` | top-N matching tools with relevance score |
| `translator.list_servers` | (none) | `[{name, tool_count}]` for each MCP server |
| `translator.tools_by_server` | `server` | all tools for one server |
| `translator.refresh_catalog` | (none) | force re-read catalog files |
| `translator.health` | (none) | `{ok, tool_count, cache_mtime}` |

## How it works

1. Reads `04_MCP/_catalog/by-server/*.md` on first call, caches in memory.
2. Re-reads on cache miss (any catalog file changed).
3. Scoring algorithm:
   - Substring match on tool name (+1.0)
   - Partial-word match (+0.6)
   - Substring in description (+0.4)
   - Fuzzy ratio bonus

## Example

```python
translator.find_tool("sign apk")
# Returns:
# [
#   {"server": "sinister-apk", "tool": "apk.creator.build", "snippet": "build creator APK", "score": 1.45},
#   {"server": "sinister-apk", "tool": "apk.creator.install", ...},
#   ...
# ]
```

## Run standalone

```powershell
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\translator'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

## Register

```json
"translator": {
  "command": "python",
  "args": ["server.py"],
  "cwd": "D:\\Sinister\\Sinister Skills\\12_LLM_ORCHESTRATION\\agents\\translator"
}
```

## Cross-references

- `04_MCP/_catalog/ALL-TOOLS.md` — full catalog (source of truth)
- `04_MCP/_catalog/by-server/*.md` — what Translator parses
- `04_MCP/_catalog/by-keyword/*.md` — pre-built keyword shards (alternative recall path)
