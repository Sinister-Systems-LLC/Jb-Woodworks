# RKOJ extension :: brain

> Author: RKOJ-ELENO :: 2026-05-21

Bridges the RKOJ PyQt6 shell to the **knowledge brain** at `_shared-memory/knowledge/` and to the **memory-graph-render** mermaid tooling.

## What it adds

| Surface | Effect |
|---|---|
| Sidebar `AI` section | New nav row "Brain" with glyph `⛁` |
| Header chip-tabs | New tab `brain` (ASCII glyph `B` per doctrine — no emoji) |
| Workstation tab | Action card "Open Brain Graph" — opens the most recent mermaid HTML render |
| Agent pane slash | `/brain search <q>` / `/brain grep <regex>` / `/brain render [file]` / `/brain index` |

## Slash usage

```text
/brain search ssh keys      # top-5 substring hits, ranked (heading-hits boosted)
/brain grep eve persona     # regex search, top-20 file:line:snippet hits
/brain render               # full index render via memory-graph-render
/brain render foo.md        # single-file render
/brain index                # corpus stats (file count, bytes, newest file)
```

## Path discovery

Walks up from `extensions/brain/` looking for `_shared-memory/` to locate the Sanctum root, so the extension keeps working when bundled into the EXE or moved sideways. If the knowledge dir is missing every command degrades to a friendly error string.

## Render integration

`/brain render` late-imports `tools/memory-graph-render/memory_graph_render/api.py`. It tries (in order) `render_file(path)`, `render_index()`, then `render([path])`, and finally falls back to `python -m memory_graph_render` CLI. If none of those exist the extension reports `tools/memory-graph-render not installed` without crashing.

## Self-contained

Drop this directory into any PyQt6 host implementing the slash + workstation hook signatures. No imports from `sinister_rkoj_qt.*`.
