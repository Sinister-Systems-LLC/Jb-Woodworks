# 03 — Agent integration

> Author: RKOJ-ELENO :: 2026-05-25

How a running fleet agent calls Sinister Memory at three integration tiers:

1. **CLI** — shell-out from any script (PS1, bash, Python)
2. **Python import** — in-process for Python agents (forge / overseer / sleight)
3. **MCP-side** — future; via Ruflo MCP semantic-route once P3 wires it

This doc also explains how iter-close auto-save + spawn-inject feed the
RELENTLESS loop continuity doctrine.

## Tier 1 — CLI (universal)

Any agent that can shell out can use sinister-memory:

```bash
# At the top of your turn — recall what you knew last time
python -m sinister_memory.cli recall "<topic>" --agent <your-slug> --limit 5

# At the end of your turn — persist what you learned
python -m sinister_memory.cli save iter-<N> "<one-paragraph summary>" \
  --agent <your-slug> --reindex
```

This works from PowerShell, bash, and from inside Claude harness `Bash` tool
calls. No install required — `pip install -e projects/sinister-memory/` is
optional (it just registers the `sinister-memory` console script).

## Tier 2 — Python import (in-process)

For Python-native fleet projects (sinister-overseer, sinister-sleight, the
forge backend), bypass the CLI and import directly:

```python
import sys
sys.path.insert(0, r"D:\Sinister Sanctum\projects\sinister-memory\src")

from sinister_memory import auto_save, indexer, recall, spawn_inject
from pathlib import Path

ROOT = Path(r"D:\Sinister Sanctum")
DB = indexer.default_db_path(ROOT)

# Recall
hits = recall.recall("loop relentless", DB, limit=5, agent="sinister-overseer")
for h in hits:
    print(f"{h.layer} {h.path}:{h.line} -- {h.snippet}")

# Save at iter close
auto_save.save_iter_close(
    slug="sinister-overseer",
    iter_num=42,
    summary="finished triage cycle 7; 3 fixes auto-applied, 1 escalated",
    root=ROOT,
    do_reindex=True,
)

# Get spawn-phrase chunk for a different agent
chunk = spawn_inject.inject_for_spawn("sinister-sleight", ROOT, limit=3)
```

## Tier 3 — Future MCP integration (P3)

P3 wires `mcp__ruflo__agentdb_hierarchical-recall` into `recall.try_ruflo_augment()`.
Once that ships, every recall call automatically gets a semantic second pass
when the MCP is reachable, merged by score. Today the stub passes through.

## Iter-close auto-save (how RELENTLESS continuity works)

The RELENTLESS loop doctrine (2026-05-25) demands that "after every shipped
deliverable, immediately start the next iteration in the same turn." That
requires the agent to know what the LAST iter did. Sinister Memory provides
the substrate:

### At iter-close (per agent, per turn)

The agent (or `forever-improve.ps1 -Action Tally`) calls:

```bash
sinister-memory save iter-<N> "<summary>" --agent <slug> --reindex
```

This writes one markdown file to `per-agent/<slug>/iter-<N>.md` and refreshes
the index. The file is < 500 bytes typical; storage cost is negligible.

### At spawn (next iter)

`automations/start-sinister-session.ps1` Build-Phrase will (P2) call:

```bash
sinister-memory inject-spawn-phrase <slug> --limit 5
```

The output is a markdown chunk listing the last 5 iter summaries. It is
embedded directly into the spawn phrase so the new spawn sees:

```
## Last memories (sinister-memory)

### iter-0042 (per-agent/sinister-overseer/iter-0042.md)
finished triage cycle 7; 3 fixes auto-applied, 1 escalated

### iter-0041 (...)
...
```

The new spawn now picks up exactly where the last left off. Combined with
`SINISTER_LOOP_CONDITION` (the loop's acceptance criterion env var), the
continuity is complete: same goal + memory of last 5 attempts.

## Composes with existing doctrine

| Doctrine | How Sinister Memory contributes |
|---|---|
| `loop-relentless-pursuit-doctrine-2026-05-25` | provides the cross-iter "what did I just do" the loop assumes |
| `no-bullshit-tested-before-claimed-doctrine-2026-05-23` | every iter-close memory carries a verified-claims trail |
| `forever-improve-review-doctrine-2026-05-24` | `-Action Tally` becomes the natural auto-save hook |
| `frequent-detailed-commits-doctrine` | commit message bodies can be reused as iter summaries |
| `gradual-growth-memory-push-eve-exe-ready-2026-05-24` | memory growth becomes structured + searchable, not file-bloat |

## Operational notes

- **Index location** is `_shared-memory/sinister-memory/index.db`. Add this
  path to `.gitignore` if you don't want to commit a hot DB. (At P0 the
  scaffold does NOT auto-modify `.gitignore`; the operator decides.)
- **Per-agent memory** lives under `_shared-memory/sinister-memory/per-agent/<slug>/`.
  These ARE committed by default (they're the durable continuity layer).
- **No daemon at P0.** Indexer runs on-demand (`--reindex` flag on `save`) or
  via a future schtask the operator can opt into.
- **MCP fallback is feature-detected.** If Ruflo is unreachable, FTS5 is the
  only oracle; no errors surfaced to the user.
