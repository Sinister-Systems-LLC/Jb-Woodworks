# 02 — CLI usage

> Author: RKOJ-ELENO :: 2026-05-25

All examples assume:
- CWD = `D:\Sinister Sanctum\projects\sinister-memory\`
- Python = 3.12 (FTS5 + BM25 confirmed in stdlib)
- No install required: run via `python -m sinister_memory.cli ...` from the
  `src/` dir, or via `python src/sinister_memory/cli.py ...`

## `recall <topic>` — BM25 search

```bash
# Default: top 5 hits across all layers
python -m sinister_memory.cli recall "loop relentless"

# Limit to 3, restrict to brain layer only
python -m sinister_memory.cli recall "token efficiency" --limit 3 --layer brain

# Scope to one agent's PROGRESS + per-agent memory (brain is always included)
python -m sinister_memory.cli recall "kernel crash" --agent sinister-kernel-apk

# Combine layer + agent
python -m sinister_memory.cli recall "spawn" --layer progress --agent sinister-overseer --limit 10
```

Output format (markdown list):

```
- **[brain]** `—` `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md:42` — After every shipped deliverable, immediately start the next iteration.
- **[progress]** `sinister-sanctum` `_shared-memory/PROGRESS/Sinister Sanctum.md:12` — iter-21 shipped 9-subagent batch; loop-relentless tested.
```

Empty result → `_(no memories matched)_`.

## `save <key> <summary> --agent <slug>` — iter-close memory

```bash
python -m sinister_memory.cli save iter-23 \
  "shipped Sinister Memory P0 scaffold; 5/5 pytest PASS; FTS5 + BM25" \
  --agent sinister-sanctum --reindex
# saved: D:\Sinister Sanctum\_shared-memory\sinister-memory\per-agent\sinister-sanctum\iter-0023.md
```

- `key` is any token containing a trailing integer (e.g. `iter-23`, `23`, `cycle7`)
- `summary` is one positional arg — quote it
- `--agent` is required (slug is validated against `^[a-z0-9][a-z0-9._-]{1,64}$`)
- `--reindex` runs the incremental indexer immediately so the new memory is
  searchable in the same shell session

## `index --layer all` — refresh the FTS5 index

```bash
# Full incremental rebuild (only re-indexes files whose mtime changed)
python -m sinister_memory.cli index --layer all
# indexed=3 skipped=87 removed=0
# db: D:\Sinister Sanctum\_shared-memory\sinister-memory\index.db
```

- `--layer` is reserved; today only `all` is meaningful (per-layer scoping
  comes in P2 when we add separate `files_<layer>` tables for parallel build).

## `inject-spawn-phrase <agent-slug>` — markdown chunk for PS1

```bash
python -m sinister_memory.cli inject-spawn-phrase sinister-overseer --limit 5
```

Output (markdown, PS-heredoc-safe):

```
## Last memories (sinister-memory)

### iter-0007 (_shared-memory/sinister-memory/per-agent/sinister-overseer/iter-0007.md)
learned token-tier routing pays for itself within 2 days

### iter-0006 (...)
...
```

To embed in `automations/start-sinister-session.ps1` Build-Phrase:

```powershell
$memoryChunk = & python -m sinister_memory.cli inject-spawn-phrase $slug --limit 5 2>$null
if ($LASTEXITCODE -eq 0 -and $memoryChunk) {
    $spawnPhrase += "`n$memoryChunk"
}
```

(documented here; wiring deferred to P2 to keep P0 small and reviewable.)

## `version` — print + exit

```bash
python -m sinister_memory.cli version
# sinister-memory 0.1.0 (author: RKOJ-ELENO)
```

## Environment

| Var                    | Default                       | Purpose                  |
|------------------------|-------------------------------|--------------------------|
| `SINISTER_SANCTUM_ROOT`| `D:\Sinister Sanctum` (Win)   | Sanctum root override    |
| `--root` (flag)        | (env or default)              | Per-invocation override  |
| `--db` (flag)          | `<root>/_shared-memory/sinister-memory/index.db` | Custom index location |
