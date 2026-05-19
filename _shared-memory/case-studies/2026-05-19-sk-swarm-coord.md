# Case study :: sk-swarm-coord (forked from ruvnet/ruflo)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19T13:30Z
> **Tags:** review, external, ruflo, sk-swarm-coord, candidate

## 1. What it is

`ruflo-swarm` ships in the ruvnet/ruflo MIT-licensed package as a plugin for the Ruflo MCP ecosystem. It provides 12 MCP tools (`swarm_init/status/shutdown/health` + 8 `agent_*` lifecycle tools), 6 topologies (hierarchical / mesh / hierarchical-mesh / ring / star / adaptive), and 5 Byzantine consensus strategies. Pairs with Claude Code's native `Task` / `SendMessage` / `Monitor` / `EnterWorktree` / `ExitWorktree` tools for git-worktree-isolated multi-agent execution. Smoke contract at `plugins/ruflo-swarm/scripts/smoke.sh`. Anti-drift defaults documented (hierarchical + maxAgents=6-8 + specialized + raft).

Sanctum fork lives at `skills/sk-swarm-coord/`; upstream snapshot at `_shared-memory/external-imports/ruflo/plugins/ruflo-swarm/`.

## 2. Strengths

- **Direct match to Sanctum's existing 5+ parallel-session model.** Operator already runs master + snap-emu + tiktok-emu + panel + kernel-apk sessions with the `agent/<slug>/<topic>` branch discipline (DIRECTIVES standing rule #3). ruflo-swarm formalizes that into topology + consensus rather than ad-hoc.
- **Worktree isolation pairs with per-agent branch rule.** Existing convention says "each session, own branch." Swarm adds "each agent, own worktree" — closes git-index race conditions when two sessions touch the same file.
- **MCP-callable from any session.** Once `claude mcp add ruflo` is wired (done 2026-05-19), the swarm tools are available everywhere — no per-bot wiring.
- **Monitor streams complement RKOJ's `/api/sse/changes`.** Both are SSE-style real-time event streams; observability across the fleet becomes uniform.
- **MIT license, open source, well-documented.** Anti-drift table is operator-friendly; "specialized" strategy maps to Sanctum's lane discipline naturally.

## 3. Weaknesses + risks

- **Upstream dependency on `@claude-flow/cli` v3.6.x.** Ruflo pins major.minor; patch bumps no-op. Sanctum's fork inherits that pin. If the cli evolves incompatibly, Sanctum needs a rebase.  *Reference: `_shared-memory/external-imports/ruflo/plugins/ruflo-swarm/README.md:21-22`*
- **Spawns external processes (`npx`).** `npx ruflo@latest mcp start` pulls latest on first run; subsequent runs are cached. Operator network egress + npm registry availability are runtime deps.
- **Topology choice has hidden cost.** Mesh topology can fan out N² messages between agents; without observability (Phase E — `sk-observability` if that fork lands too), bad topology picks are invisible until token bills spike.
- **No native fallback when ruflo MCP is down.** Sanctum's existing inbox keeps working without swarm, but agents that have *adapted to swarm idioms* (e.g., consensus-aware delegations) will degrade.
- **Smoke contract is plugin-internal.** Sanctum doesn't currently invoke `scripts/smoke.sh` on a schedule. Without that, version drift goes unnoticed.

## 4. Better-than-found proposal (~50 LOC outline)

Three Sanctum-specific adaptations layer above the fork, none destructive to the upstream contract:

1. **Sanctum-swarm-wrapper.ps1** (~30 LOC) — wraps `swarm_init` with Sanctum defaults (purple accent, RKOJ identity, lane-aware agent assignment by `projects.json` keys). One-line invocation: `& Sanctum-Swarm.ps1 -Topic "<ask>" -Lanes snap-emu,tiktok-emu`.
2. **Brain-entry bridge** (~20 LOC, new tool `tools/sanctum-swarm/`) — listens on the ruflo-swarm monitor stream, writes interesting events (agent_spawn / consensus_reached / hop_limit_exceeded) into `_shared-memory/knowledge/swarm-runs/<UTC>.md`. Makes the swarm's behavior auditable across sessions.
3. **Smoke gate** (~10 LOC scheduler entry) — adds `_shared-memory/schedule.json` weekly job that runs `bash plugins/ruflo-swarm/scripts/smoke.sh` + writes verdict to `_shared-memory/external-imports/ruflo/smoke-<UTC>.md`. Fleet learns about upstream breakage automatically.

Net: ~60 LOC adapters. Upstream stays vendor; Sanctum-specific value-add stays in `skills/sk-swarm-coord/` + `tools/sanctum-swarm/`.

## 5. Recommendation

**KEEP-WITH-CHANGES.** Direct fit for Sanctum's multi-session model. Risks (upstream pin, network egress, topology cost) are manageable with the proposed adapters. The case for owning the source over MCP-only is clear: "work forever" requires Sanctum to survive ruflo's upstream evolution.

Implementation path on operator thumbs-up:
1. Land the 3 adapters above (~60 LOC + 2 new tool/skill folders).
2. Add a section to `_shared-memory/knowledge/cross-agent-coordination.md` codifying swarm usage patterns.
3. Flip `skills/_INDEX.md` row from `candidate` to `fixed`.
4. Pair with Codex peer-review on the adapters (per standing rule, > 50 LOC + multi-agent-coord, deep tier).

---

## Operator decision

(blank — operator drops 👍 / 👎 / free text)
