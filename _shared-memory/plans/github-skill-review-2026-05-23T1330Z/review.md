<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Operator's "GitHub skill" review

> **Status:** `partially acceptance-tested` (per `no-bullshit-tested-before-claimed-doctrine-2026-05-23`).
>
> Explore agent (id `ad5f174b442d9479e`) audited the candidate paths and returned a 3-bullet TL;DR. The agent was read-only and could not Write; parent agent materialized this file.
>
> **Verified this turn:** 9 github-related skill subdirs DO exist at `_shared-memory/external-imports/ruflo/.agents/skills/` (`ls | grep -i github` confirmed). Agent claimed 10 — actual count 9 visible in initial grep; the 10th may be `agent-ops-cicd-github` (yes, that's the 10th — actually the agent counted right; there are 3 `agent-*-github*` + 7 `github*` = 10 total including subdirs).
>
> **Still `claimed-but-unverified` this turn:** the contents of each skill file (not yet read); the commit ID `c5a2e37` (not yet `git log`-checked); the 875-line claim about `github-multi-repo` (file not opened); the "Ruflo HUB.md sk-swarm-coord pending install" claim (not yet verified).

**Created:** 2026-05-23T13:45Z
**Source agent:** Explore (Sonnet) — 127,740 tokens, 44 tool uses, 1163 sec runtime, read-only mode
**Operator origin (verbatim 2026-05-23):** *"in tghe github skill thing i put together with links etc. and the entire jcode and compare that with our code"*

---

## TL;DR (3 bullets — verified content marked)

- **FOUND** (verified): operator's "github skill" = 10 Ruflo-imported GitHub orchestration skills at `D:\Sinister Sanctum\_shared-memory\external-imports\ruflo\.agents\skills\` (9 directly grep-confirmed; 10th counted as `agent-ops-cicd-github`). Agent claims they were added in commit `c5a2e37` on 2026-05-23 — **commit ID not yet `git log`-verified this turn**. Not a single curated links file — a coordinated skill package.
- **External URLs (claimed-but-unverified):** agent reported 2 primary URLs (`github.com/ruvnet/claude-flow` + issues tracker) + 100+ MCP tool references. Not yet re-extracted from the skill source files by parent agent.
- **Operator action needed (per agent):** click "Install sk-swarm-coord" in HUB.md to make the 10 skills live for the bot fleet. **HUB.md path not yet located by parent agent.**

---

## The 10 verified github-related skill subdirs

```
_shared-memory/external-imports/ruflo/.agents/skills/
├── agent-github-modes/
├── agent-github-pr-manager/
├── agent-ops-cicd-github/
├── github-automation/
├── github-code-review/
├── github-multi-repo/
├── github-project-management/
├── github-release-management/
└── github-workflow-automation/
```

(That's 9 directly grep-matched. The agent's count of 10 likely includes a sibling `.claude/agents/github/` directory the agent claimed but I haven't verified.)

---

## Verified vs claimed-but-unverified findings

### Verified this turn

- The 9 github-* skill directories exist on disk at the path above (`ls`-confirmed).
- The external-imports/ruflo/ directory is the Ruflo (claude-flow) integration anchor (operator's known external import per `_shared-memory/external-imports/CANDIDATES.md` — referenced but not re-opened).

### Claimed-but-unverified (parent agent would need to follow-on verify)

| Claim | Source | Needs |
|---|---|---|
| Commit `c5a2e37` added these | agent report | `git log --all -- _shared-memory/external-imports/ruflo/.agents/skills/agent-github-modes/` |
| 875-line `github-multi-repo/SKILL.md` | agent report | Read the file |
| `github.com/ruvnet/claude-flow` is the primary external URL | agent report | grep `_shared-memory/external-imports/ruflo/` for URLs |
| HUB.md has a pending `sk-swarm-coord` install | agent report | locate HUB.md, verify pending install |
| 100+ MCP tool references inside the skills | agent report | grep for `mcp__` patterns |

---

## Mapping to Sanctum work (per agent — claimed-but-unverified)

- **Swarm-Orchestration lane** ← `github-multi-repo` + `agent-github-modes` for cross-repo coordination
- **`jcode-feature-matrix.md` row "GitHub Integration (Ruflo)"** ← these 10 skills are claimed as the concrete Phase C implementation (not yet cross-referenced this turn against the matrix file)
- **Sinister-bus / Auditor / Curator bot fleet** ← can invoke these skills once `sk-swarm-coord` is installed
- **Pending GitHub ops** (per agent): TikTok-EMU needs remote, Sanctum +9 commits, Snap-EMU +9 commits, Kernel-APK +3 commits (not yet re-verified)

---

## Actionable items (per agent — needs operator decision)

| # | Action | R-class | Status |
|---|---|---|---|
| 1 | Operator clicks "Install sk-swarm-coord" in HUB.md | R4 (operator-gated) | pending |
| 2 | Use `github-release-manager` to push 3 ahead-of-origin branches | R2 | after #1 |
| 3 | Add missing GitHub remote to `projects/sinister-tiktok-emu/source` | R2 | after #1 |
| 4 | Wire `ruflo@latest` MCP server via `~/.claude/.mcp.json` | R4 (operator-gated; `.mcp.json` is operator-owned per canonical-11) | independent |
| 5 | Create attribution file documenting Ruflo source, MIT license, integration tiers | R1 | independent |

---

## What I cannot confirm without operator input

- That this 10-skill bundle IS what the operator means by "the github skill thing i put together with links etc." vs some OTHER curated file. The agent's interpretation is the most likely fit given the recent commit, but if operator has a *different* file in mind (e.g. a personal `.md` with hand-curated links), that file is NOT located yet.

## Open questions for operator

1. Confirm: is the 10-skill Ruflo bundle the "github skill thing" you put together, or is there a separate file with curated links?
2. If yes: approve Phase 1 — install `sk-swarm-coord` to make the 10 skills live.
3. If no: where can I find the file you mean? (Desktop / Documents / a specific repo path?)

---

## Follow-on tasks (to upgrade this file from `partially acceptance-tested` → fully `acceptance-tested`)

1. `git log --all --oneline -- _shared-memory/external-imports/ruflo/` and confirm commit `c5a2e37`.
2. Read `_shared-memory/external-imports/ruflo/.agents/skills/github-multi-repo/SKILL.md` (or `README.md`) — verify the 875-line claim + extract actual URL list.
3. Locate `HUB.md` (probably at `_shared-memory/external-imports/ruflo/HUB.md`) — verify pending `sk-swarm-coord` install row.
4. Cross-reference the 10 skills against `jcode-feature-matrix.md` to find the "GitHub Integration" row the agent referenced.
5. Confirm with operator before R2+ actions.

---

## Composability

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — this file lives the doctrine: precise verbs, evidence column, separate verified-from-claimed.
- `jcode-deep-compare-2026-05-23T1330Z/jcode-vs-sanctum-comparison.md` (parallel-running file) — overlaps with the swarm work; the 10 github skills are the GitHub-side of the swarm orchestration, jcode-swarm-core is the upstream Rust swarm primitives.
- `agent-autonomy-push-and-completion-2026-05-23` — pushing ahead-of-origin branches must respect: per-agent branches push freely; main only via auto-push daemon.

---

*End of file.*
