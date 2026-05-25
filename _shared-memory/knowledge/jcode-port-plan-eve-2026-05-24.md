<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 1
  half_life_days: 90
-->
# jcode 0.12.4 → EVE port plan (4-area aggregate)

**Operator verbatim 2026-05-24T19:30Z:** *"I WANT REAL SWARM FROM HERE: C:\Users\Zonia\Desktop\jcode-0.12.4 ... THIS SHOULD be easy as fuck you have the entire source code. add what we need including the animations. there will be 5 total sanctum agents im launching from the eve exe"*

**Provenance:** 4 parallel research subagents (token-efficient: each ≤250 word brief) dispatched 2026-05-24T19:30Z; results aggregated below.

## Area summary (what to lift from jcode, mapped to our stack)

| Area | jcode source | EVE port path | Effort |
|---|---|---|---|
| **Swarm** | `src/server/comm_session.rs:290` `spawn_swarm_agent`; `src/server/swarm_channels.rs`; `~/.jcode/jcode-swarm-state/{id}.json` | JSON registry at `_shared-memory/swarm-state/<id>.json` + heartbeat polling (extend `spawned-windows.jsonl`) + named-pipe broadcast | ~500 LOC Python, 1-2 iters |
| **Mermaid** | `jcode-tui-mermaid/src/mermaid_cache_render.rs` calls `mermaid-rs-renderer` crate → PNG via `resvg`/`usvg`, displayed via `ratatui-image` | mintty has no Kitty/Sixel; path: optional `mermaid-cli` (npm) → PNG → external open. R28 Rust-fork doctrine already exists for native port. | gated on operator tool install OR R28 |
| **Memory** | `src/memory*.rs` + `src/embedding.rs`: ONNX all-MiniLM-L6-v2 (384-dim) + Haiku sidecar verify + memory_graph (HasTag/Supersedes/RelatesTo/ClusterEntry edges) | **Option C** — wrap Ruflo MCP `memory_*` (HNSW; same model via Xenova) + EVE-side verify-before-inject (~50 LOC) | ~50 LOC, 1 iter |
| **Compact log render** | `jcode-tui-tool-display/lib.rs:5-29`; `ui_tools.rs:1383-1465`; `cache.rs:91-127` | Sinister-term renderer: batch header `✓ batch N calls · X tok` + per-subcall + width-budgeted truncate + severity badge | ~300 LOC, 1-2 iters |
| **Animated banner** | Not present in jcode — `workspace_map_widget.rs:128` has 4-frame tile spinner `◴◷◶◵` via `tick % 4` | EVE already has an animated banner; optionally add tick-driven status spinner for swarm-active sessions | ~50 LOC nice-to-have |

## Concrete port surface — 5 deliverables

### D1. Swarm registry + heartbeat (~500 LOC Python)

```
_shared-memory/swarm-state/<swarm_id>.json
{
  "swarm_id": "uuid",
  "coordinator": "sanctum",
  "members": [
    {"session_id": "...", "agent": "kernel-apk", "status": "running",
     "last_heartbeat_utc": "...", "completion_report": null}
  ],
  "plan_version": 1,
  "tasks": [...]
}
```

- Status enum: `Spawned → Running → RunningStale (45 s no heartbeat) → Completed/Failed/Stopped`
- Reaper: scan `spawned-windows.jsonl`; for dead PIDs, mark `closed_at_utc` + decrement refcount per `resource-refcount-cleanup-sleep-wake-doctrine-2026-05-24.md`.
- EVE.exe `--swarm-status` flag prints all active swarms.

### D2. Memory MCP wrapper (~50 LOC, eve-launcher/memory_recall.py)

- `memory_recall(query, top_k=5)` → calls `mcp__ruflo__memory_search` if available, falls back to `forge-memory recall`.
- `memory_verify(candidates, query)` → 1 Haiku call grades relevance per candidate → returns top-K filtered list.
- Wire into `Build-Phrase` in `start-sinister-session.ps1` (replaces existing 5 s `forge-memory recall` block).

### D3. Compact log formatter (~300 LOC, projects/sinister-term/source)

Five primitives lifted from jcode:
1. Batch summary header: `✓ batch N calls · X tok` (one cache per batch_id)
2. Tool-name resolution: bash→`$`, read→path, grep→`'pattern'`, edit→file
3. Token-budget truncation: width = terminal − reserved(icon+name+intent) − badge
4. Badge severity coloring: normal gray / warn yellow (>1k tok) / danger red (>10k)
5. Batch footer suppression: strip `Completed: N/M` from rendered compact line

### D4. Mermaid stub (gated)

- IF `mermaid-cli` (`mmdc`) is on PATH: `eve --diagram <file.mmd>` → `mmdc -i x.mmd -o x.png` → `start x.png` (Windows default opener).
- ELSE: log a friendly hint pointing at the R28 Rust-fork doctrine (`r28-sinister-mermaid-render-rust-fork-doctrine-2026-05-24`).

### D5. Tick-driven session spinner (~50 LOC, optional)

- 4-frame `◴◷◶◵` on the status line for any session marked `running` in swarm-state/.
- Reuse `tick % 4` pattern from `workspace_map_widget.rs:139`.

## Order of work (operator-prioritized, smallest-first)

1. **Now (this turn — done)**: Reconcile-AccountSessions + repair claude-accounts.json bloat + preparing-spawn feedback line.
2. **Next iter**: D1 swarm registry skeleton + reaper (extends existing `spawned-windows.jsonl`).
3. **Next iter**: D3 compact log formatter (sinister-term primitives 1-3 first).
4. **Next iter**: D2 memory wrapper.
5. **Gated**: D4 mermaid (needs operator npm install OR R28 Rust unblock).
6. **Optional**: D5 spinner.

## What we are NOT porting (and why)

- **handterm** — operator-quoted *"work in progress, scrolling is still well implemented for normal terminals"*; sinister-term already has its own scroll. Defer until evidence sinister-term scrolling is too slow.
- **ratatui-image inline image protocol** — mintty doesn't support it; would require terminal swap.
- **jcode telemetry** — explicitly omitted by us (per `jcode-eve-exe-parity-audit-2026-05-24` row).

## Composes with

- `jcode-eve-exe-parity-audit-2026-05-24` — the 30-row parity audit; this plan executes its open rows.
- `resource-refcount-cleanup-sleep-wake-doctrine-2026-05-24` — D1 reaper IS the spawned-windows reaper from that doctrine.
- `r28-sinister-mermaid-render-rust-fork-doctrine-2026-05-24` — D4 fallback path.
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — each deliverable above ships with smoke-test acceptance criterion before claim.

Updated: 2026-05-24
