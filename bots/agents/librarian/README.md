# Librarian agent

**Role:** RAG over the 8,500+ MD archive. The highest-impact agent — replaces operator's "grep for X" Opus queries with $0 Ollama calls.

**Tier:** 2 (Ollama). Graceful degradation: when Ollama down, falls back to Tier 1 grep.

## Tools

| Tool | Args | Returns |
|---|---|---|
| `librarian.search` | `query, top_k=5` | `{results: [{path, snippet, score}], mode: 'vector'\|'grep'}` |
| `librarian.reindex` | `section=None` | rebuilds FAISS index |
| `librarian.grep_fallback` | `query, top_k=5` | always-available pure-grep search |
| `librarian.health` | (none) | full status: FAISS+Ollama+index state |

## How it works

```
Query received
├── Is FAISS + Ollama available?
│   ├── Yes → Embed query (nomic-embed-text)
│   │        → FAISS top-K cosine similarity
│   │        → Return chunks with paths
│   └── No → grep_search() fallback
│           → reads 02_MD_ARCHIVE/_index/by-keyword/ shards first
│           → brute grep if no keyword match
└── Mode flagged in response for telemetry
```

## First-time setup

```powershell
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\librarian'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Start Ollama (one-time):
cd ..\..\docker
.\setup.bat

# Build the FAISS index (~3-5 min first run):
cd ..\agents\librarian
python -c "from server import reindex; print(reindex())"
```

After first index build:
- Index at `agents/librarian/index/faiss.index` (~50-200 MB)
- Metadata at `agents/librarian/index/metadata.jsonl`

## Register with Claude Code

```json
"librarian": {
  "command": "python",
  "args": ["server.py"],
  "cwd": "D:\\Sinister\\Sinister Skills\\12_LLM_ORCHESTRATION\\agents\\librarian",
  "env": {
    "OLLAMA_HOST": "http://localhost:11434",
    "SINISTER_HUB_ROOT": "D:\\Sinister\\Sinister Skills"
  }
}
```

## Cost comparison

Operator asks "find docs about Yurikey expiry":

**Before Librarian:**
- Opus reads grep output across 8,500 .md
- ~5-10k input tokens, ~500-1k output tokens
- Cost: ~$0.07-0.18 per query

**With Librarian:**
- Embed query (Ollama, $0)
- FAISS lookup (local, $0)
- Return top-K snippets ($0)
- Cost: $0.00 per query

**Daily savings (assuming 20 recall queries):** $1.40-3.60/day → $42-108/month.

## Reindex policy

- Manual: `librarian.reindex()` rebuilds full index
- Section-only: `librarian.reindex("snap-signer")` for one project
- Auto (when Watcher agent ships, Phase 8d): incremental on drift detection
- Scheduled: daily 03:00 via Task Scheduler

## Cross-references

- `02_MD_ARCHIVE/` — what gets indexed
- `02_MD_ARCHIVE/_index/by-keyword/` — fallback shards (grep mode reads these first)
- `12_LLM_ORCHESTRATION/config/routing-rules.yaml` — Librarian's escalation rules
- `12_LLM_ORCHESTRATION/docker/setup.bat` — bring Ollama up
