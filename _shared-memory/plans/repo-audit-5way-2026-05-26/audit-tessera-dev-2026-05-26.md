# tessera-dev audit (2026-05-26) — sinister-term slice of HIVE

> Full audit by general-purpose Explore sub-agent. Stored here for reference. Sub-agent's **honest verdict: "Moderately valuable, not essential."** Cherry-pick 4 iters worth porting.

## Fleet-allocation claim posted

`fu-20260526184825-58d20d` (priority=high, kind=status, fleet-wide):
- sinister-term claimed `tessera-dev` from HIVE
- Flagged hivemind-master + jcode-master in HIVE as DUPLICATES (already audited at `/audit-jcode-gap-2026-05-26.md` + `/plan.md`)
- Suggested allocation: sanctum=genesis-architect, eve-exe=petals, os=CALM, memory=sahajBERT+DALLE-pytorch

## What tessera is

TypeScript (Node ≥20) + Electron desktop + Next.js browser. ~16K LOC core. `@horang-labs/tessera` on npm. Apache-2.0.

**Scope:** desktop/web workspace orchestrator for running multiple AI coding agents side-by-side (Claude Code / Codex / OpenCode) without losing track of sessions/worktrees/branches/PRs/tasks.

**Core data model:**
- **Task** (`src/types/task-entity.ts:24-62`) = workflow unit with `workflowStatus: todo|in_progress|in_review|done`, `worktreeBranch: string?`, list of `sessions`
- **Session** (`src/lib/db/schema.ts:26-45`) = chat session with provider + worktreeBranch + workDir + provider_state JSON blob
- **Message** (`src/types/chat.ts:14-79`) = TextMessage | ToolCallMessage | ThinkingMessage | SystemMessage (typed union)
- **Worktree** = git worktree tracked with async diff stats + GitHub PR sync
- Persistence = local SQLite (`~/.tessera/tessera.db`)

## High-value patterns extracted

1. **Provider adapter contract** (`src/lib/cli/providers/types.ts`) — `CliProvider` interface (spawn / isAvailable / consumeStartupMessages / parseProtocol) abstracts Claude Code vs Codex vs OpenCode. **sterm could standardize /peer + /agents + /swarm around a similar contract.**

2. **Worktree branch ownership per task** (`src/types/task-entity.ts:29-55`) — task ID uniquely owns one branch; no two sessions claim same worktreeBranch. Better than our current "lanes pick any branch hoping no conflict" model.

3. **Session resume with lazy-load** (`src/lib/session/session-orchestrator-lifecycle.ts`) — full chat history in DB but tool outputs + thinking blocks fetched on-demand for big sessions. Our resume-points reload everything eagerly.

4. **Async diff stats broadcast** (`src/lib/git/worktree-diff-stats.ts:14-80`) — `git diff --numstat HEAD` runs in background with 512KB untracked-file cap; updates broadcast over WebSocket. We currently block on `/diff` calls.

5. **ParsedMessageSideEffect dispatch** (`src/lib/cli/process-manager-message-dispatch.ts:44-120`) — protocol parser emits typed side-effect objects (set_generating / update_provider_state / add_pending_tool_call) instead of imperatively mutating. Cleaner than our stdout-regex tool detection.

6. **Task → Collection → Project hierarchy** (`src/lib/db/schema.ts:64-96`) — collections = user labels, projects = filesystem roots. sterm `/find` + `/grep` could auto-scope.

7. **Zustand stores separate state from disk** (`src/stores/board-store.ts`, `tab-store.ts`) — UI state vs network/disk state separated. We've conflated them in places.

8. **Git-state-change detection** (`src/lib/github/pr-command-detector.ts`) — when agent runs `git push` or `git commit`, auto-refresh diff + PR. We rely on manual `/branch` polls.

9. **Normalized typed message union** (`src/types/chat.ts`) — better than our plain-text inbox tuples.

10. **Provider registry + availability probing** (`src/lib/cli/providers/registry.ts:16-68`) — checks native + WSL availability. sterm `/sysinfo` could surface this.

## Cherry-picked integrations promoted to iter-100+ queue

**iter-100 — Unified slash-command registry [M]** (`src/lib/cli/providers/registry.ts:1-29`)
- New `term/cmd_registry.py` with `{name, args, help, handler}` entries
- Auto-complete on `/` using registry keys
- Dynamic `/help` regeneration

**iter-101 — Worktree branch ownership per task [L]** (`src/types/task-entity.ts:29-55`)
- New `/task-worktree <name> <branch>` claims a branch as owned by a named task
- Releases on lane exit via heartbeat-stale-detect
- Prevents two lanes from `git worktree add` on the same branch

**iter-102 — Session resume with cached diff stats [M]** (`src/lib/session/session-orchestrator-lifecycle.ts`)
- Extends existing `automations/resume-point-write.ps1` to cache `git diff --numstat`
- `/resume-session` reads cache, refreshes async only when needed

**iter-104 — Unified git-state-change detector [S]** (`src/lib/github/pr-command-detector.ts`)
- Tails agent stdout via existing `/watch`; on `git push` / `git commit` lines, auto-trigger `/progress` refresh
- Faster PR-state sync across lanes

**iter-103 (ParsedMessageSideEffect) DEFERRED** — sub-agent rated L effort and the parsing layer change is invasive. Wait until we hit a real bug from regex-scraping stdout.

## NOT to port

- Electron + Next.js UI stack (sterm is a terminal)
- sql.js SQLite (we're file-based)
- npm build/package pipeline
- OAuth + bcryptjs auth (single-operator)
- Multi-tenant team workspace roadmap

## Sub-agent's honest verdict

> "Tessera's strengths are Kanban drag-and-drop, multi-pane tabs, and live diffs in the UI — areas sterm doesn't occupy. The 5-way audit queue already includes 22 iters; Tessera adds ~4 concrete iters (worktree ownership, resume caching, side-effect JSON, git-state detection) that would reduce lane collision risk and improve cross-lane responsiveness. **If Sinister's bottleneck is agent-to-agent handoff latency or branch conflicts, then iter-101 and iter-103 are high-ROI; if bottleneck is UI/visibility, Tessera's dashboard design is inspirational but not directly portable. Recommend cherry-pick iters 100-103 into the master queue; defer full architecture port.**"

## Master ship queue now: 22 + 4 = **26 iters** (iter-78 through iter-104, with iter-103 deferred)
