<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# forge-memory-bridge :: green-path usage

> **Status:** operational (verified 2026-05-23 by parallel audit agent)
> **Anchor:** parallel L-audit task ID `a1af63a26f414fad6` 2026-05-23 evening + `tools/forge-memory-bridge/README.md` + `_shared-memory/knowledge/jcode-feature-matrix.md` rows 8-12.
> **Why this entry:** the only existing doc was the package README + a one-row matrix entry; future agents asking "how do I use working memory in a session" needed a single brain entry to point at. Closes a documented L-audit gap.

## TL;DR

```python
from forge_memory_bridge import write, recall

# Persist (key required; value can be any JSON-able shape):
write('sanctum', 'launcher-state', {'version': '6.1', 'art_pool': 8}, tags=['launcher', 'config'])

# Retrieve (top-k by BM25 + TF-IDF over content + tags):
hits = recall('launcher status', namespace='sanctum', limit=5)
# Each hit: {'key': '...', '_recall_score': float, '_bm25_score': float, 'value': {...}, 'tags': [...]}
```

That's the entire surface for 90% of use. Records persist to `_shared-memory/forge-memory/<namespace>/<key>.json`.

## Full API

| Function | Signature | Purpose |
|---|---|---|
| `write` | `write(namespace, key, value, tags=None, upsert=True)` | Persist value under `namespace/key.json`. `tags=['x','y']` boost recall. `upsert=False` raises on existing key. |
| `recall` | `recall(query, namespace=None, limit=10, use_mcp=False)` | Top-k by BM25 + TF-IDF. `use_mcp=True` delegates to Ruflo `agentdb_pattern-search` for semantic. `namespace=None` searches across all. |
| `ls` (alias `list`) | `ls(namespace=None)` | Enumerate keys in a namespace (or all). |
| `graph` | `graph(namespace=None, fmt='mermaid')` | Emit mermaid graph of records + tag-edges. Composes with `memory-graph-render`. |
| `consolidate` | `consolidate(namespace, threshold=0.85)` | Merge similar records over the similarity threshold. Deduplication. |
| `delete` | `delete(namespace, key)` | Remove a single record. |

CLI mirror (when `forge-memory` is on PATH):

```
forge-memory write <ns> <key> <json-value> --tag a --tag b
forge-memory recall "<query>" --ns sanctum --limit 5
forge-memory list --ns sanctum
forge-memory graph --ns sanctum --format mermaid > out.mmd
forge-memory consolidate sanctum
forge-memory delete sanctum launcher-state
```

## Common gotchas

- **`write()` requires 3 positional args.** Earlier internal doc drift showed `api.write('test', {'k':'v'})` which omits `key` and crashes with `TypeError: write() missing 1 required positional argument: 'value'`. The L-audit hit this on the first pass.
- **No automatic flush.** `write()` is synchronous; the JSON file is on disk by the time the call returns. No need to call any `flush()` / `commit()`.
- **Tag bag normalization.** `tags=['Launcher', 'CONFIG']` becomes `['launcher', 'config']` at write-time. Recall queries are case-insensitive too.
- **Recall scoring is hybrid.** `_recall_score = 0.5 * bm25_normalized + 0.3 * tfidf + 0.2 * tag_overlap`. Scores below ~0.05 are usually noise — surface only top-5 to humans.
- **Cross-namespace recall is slower** (`namespace=None` walks every namespace). For interactive use, always pin the namespace.
- **The `use_mcp=True` path** requires Ruflo MCP loaded in the running session. If Ruflo isn't connected, it silently falls back to the local BM25 path with a warning to stderr.

## When to use forge-memory vs other surfaces

| Surface | Best for |
|---|---|
| **forge-memory** | mid-session working memory; "what was that error I saw 20 turns ago?", "remember this for later in the loop" |
| **`_shared-memory/PROGRESS/<agent>.md`** | append-only milestone log; humans + future cold-starts read this |
| **resume-points** | session-close snapshot; next session bootstraps off the LATEST |
| **`_shared-memory/knowledge/`** | doctrine; durable, append-only, indexed in `_INDEX.md`; survives multiple session lifetimes |
| **Ruflo `agentdb_*`** | semantic recall across the entire fleet; delegated for cross-session pattern search |

The forge-memory namespace is intended for **session-scoped** state. Anything you want to survive a session close should also land in PROGRESS or resume-points (forge-memory is not pruned, but it's also not surfaced on cold-start).

## Composition with memory-graph-render

```python
from forge_memory_bridge import graph as mem_graph
from memory_graph_render import render_html, render_png

mmd = mem_graph(namespace='sanctum')
render_html(mmd, 'inventions/memory-graphs/<UTC>-sanctum.html')
render_png(mmd, 'inventions/memory-graphs/<UTC>-sanctum.png')  # falls back to HTML if no PNG renderer
```

3-stage pipeline (also documented in `jcode-memory-graph-visualization-pattern`):

1. SOURCE = forge-memory disk (or Ruflo agentdb when `use_mcp=True`)
2. TRANSFORM = `forge_memory_bridge.graph()` emits mermaid
3. RENDER = mermaid-rs-renderer (Rust, fastest) → `mmdc` (Node fallback) → HTML+CDN-mermaid (last-resort, always succeeds)

## Anti-patterns

1. **Treating forge-memory as durable session-spanning context.** It's working memory. Survives sessions on disk, but cold-start doesn't load it. Use PROGRESS + resume-points for cross-session pickup.
2. **Writing to forge-memory instead of brain entries for doctrine.** Doctrine goes to `_shared-memory/knowledge/` + `_INDEX.md`. forge-memory is for ephemeral state.
3. **Recall without namespace.** Cross-namespace search is order-of-magnitude slower + dilutes scores. Pin `namespace=` whenever possible.
4. **Tag bag pollution.** Tags like `['important', 'note', 'work']` add no signal. Use semantic tags: `['launcher-v6.1', 'spawn-flow', 'parse-error']`.
5. **Not deleting test writes.** Leaves stale records in the namespace. Test-then-delete or write to a `__test__` namespace and prune.

## Empirical anchor

L-audit verified 2026-05-23: `api.write('test', 'demo-key', {'k':'v'}, tags=['audit'])` + `api.recall('demo', namespace='test')` round-trips clean. `_recall_score=0.075366`, `_bm25_score=-0.274653`. Test record deleted post-verify.

`pip show forge-memory-bridge` confirms editable install at `D:\Sinister Sanctum\tools\forge-memory-bridge`. Package import resolves to `D:\Sinister Sanctum\tools\forge-memory-bridge\forge_memory_bridge\__init__.py`.

## Composes with

- `jcode-feature-matrix` (rows 8-12 cover memory surfaces)
- `jcode-memory-graph-visualization-pattern` (the rendering pipeline)
- `jcode-agentic-loop-patterns-port-to-python` (the BM25 cross-session recall pattern)
- `pip-editable-hides-mcp-cwd-emptiness-2026-05-23` (audit anti-trap when verifying installed state)
- `wake-on-demand-bot-dispatcher-2026-05-23` (when forge-memory is called from a bot that needs to wake on demand)
- `forever-expanding-modular-architecture-doctrine` (disk-first surface; MCP fast-path optional)
