# sk-swarm-coord — multi-agent swarm coordination (Ruflo fork)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19 :: forked from ruvnet/ruflo (MIT) ruflo-swarm plugin
> **Status:** candidate (pending operator thumb per case-study `_shared-memory/case-studies/2026-05-19-sk-swarm-coord.md`)
> **Upstream snapshot:** `_shared-memory/external-imports/ruflo/plugins/ruflo-swarm/`

## What it is

Agent teams, swarm coordination, real-time monitor streams, and git-worktree isolation per Ruflo. Built on `@claude-flow/cli` v3.6, exposes 12 MCP tools (`swarm_init/status/shutdown/health` + `agent_spawn/execute/terminate/status/list/pool/health/update`), plus 6 topologies (hierarchical / mesh / hierarchical-mesh / ring / star / adaptive) and 5 consensus strategies (Byzantine / Raft / Gossip / CRDT / Quorum).

## Why Sanctum needs it

Sanctum already has cross-agent coordination via the file-based inbox (`bots/agents/_shared/inbox.py`) — that's good for async ASK/ANSWER/DELEGATE patterns but doesn't scale to dozens of parallel agents with active topology management. ruflo-swarm offers:

- **Topology-aware coordination** — hierarchical for tight control (most Sanctum work), mesh for peer-to-peer (operator + Leo cross-collab), adaptive for variable workloads (RKOJ-spawned bursts).
- **Worktree isolation** — pairs with the existing `agent/<slug>/<topic>` per-agent branch convention (DIRECTIVES standing rule #3). Worktree-per-agent prevents git index races even when 5+ Claude sessions all touch Sanctum.
- **Anti-drift defaults** — `topology=hierarchical`, `maxAgents=6-8`, `strategy=specialized`, `consensus=raft` — operator's existing 5-session model maps directly to these defaults.
- **Monitor streams** — real-time SSE-style swarm-status stream pairs with the existing RKOJ `/api/sse/changes` pattern for cross-window state sync.

## How Sanctum uses it (post operator-thumb)

1. RKOJ Console gets a new "Swarm" tab that exposes `swarm_init` + topology picker + agent-spawn forms.
2. The existing `agent-prefs.json` + `inbox` patterns get a Swarm-aware extension: when an agent registers, it joins the swarm's hierarchical tree per its lane.
3. Cross-project work (e.g., master + snap-emu + tiktok-emu coordinating an API refactor) becomes a one-command `swarm_init topology=hierarchical agents=3` instead of 3 separate launcher invocations.
4. The Sanctum brain entry `cross-agent-coordination.md` gets an "After ruflo-swarm" section codifying the new patterns.

## Dependencies

- Ruflo MCP registered at user scope (`claude mcp add ruflo -s user -- npx ruflo@latest mcp start` — done 2026-05-19).
- `ruflo-core` plugin (auto-pulled when ruflo MCP starts up).
- Claude Code 2.1+ (for Task / SendMessage / Monitor native tools that swarm composes with).

## License + attribution

- Upstream: MIT (RuvNet).
- Sanctum fork: stays MIT.
- Original code lives at `_shared-memory/external-imports/ruflo/plugins/ruflo-swarm/`.
- Adaptations specific to Sanctum (RKOJ tab wiring, Sanctum brain integration) go in this folder only.

## See also

- `_shared-memory/case-studies/2026-05-19-sk-swarm-coord.md` — verdict file (operator thumbs here)
- `_shared-memory/knowledge/cross-agent-coordination.md` — the existing Sanctum pattern this augments
- `_shared-memory/external-imports/CANDIDATES.md` — master import list
- `bots/agents/_shared/inbox.py` — the existing inbox skill (complementary)
