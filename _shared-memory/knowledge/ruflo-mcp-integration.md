# Topic: Ruflo MCP integration — multi-agent orchestration sidecar for Claude Code

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

**Slug:** ruflo-mcp-integration
**First discovered:** 2026-05-19 12:30 by Sinister Sanctum
**Last updated:** 2026-05-19 12:30 by Sinister Sanctum
**Status:** workaround (will flip to `fixed` once 5-7 highest-value skills are forked into `skills/sk-*/`)
**Tags:** ruflo, mcp, claude-code, swarm, orchestration, multi-agent, vector-memory, external-import, standing-rule

## Problem

Sanctum's fleet has 13 MCP bots + cross-agent inbox + the Sanctum brain. What it lacks:

- Multi-agent **swarm coordination** with topologies (hierarchical / mesh / adaptive)
- **Self-learning neural patterns** (SONA-style) for persistent learning across sessions
- **Vector memory** with HNSW indexing (the brain is markdown-based; flat-text grep, not semantic)
- **Code quality automations**: test generation, gap detection, Playwright UI tests, git-diff risk scoring
- **Security automation**: CVE scanning, PII detection, prompt-injection blocking
- **Agent federation**: zero-trust cross-machine collaboration with trust scoring

Building any of these from scratch is multi-week work. They already exist in a public, MIT-licensed repo.

## Why it happens

Operational autonomy ("work forever" per the operator) needs a steady inflow of high-quality capabilities. Without an import loop, the fleet only grows inside-out at the speed of operator-invented tools. With one, the fleet absorbs first-party Anthropic patterns + community-vetted multi-agent stacks.

Ruflo (`github.com/ruvnet/ruflo`, MIT-licensed) is the most-direct fit found in the 2026-05-19 external scout — it bills itself as "multi-agent AI orchestration platform for Claude Code" and installs as a single MCP server.

## Fix or workaround

Two-step adoption (`workaround` until Phase C ships the forks; `fixed` after):

### Step 1 — Wire as MCP (lightest touch; operator-clicked)

```powershell
# Operator runs (lane discipline: master never edits ~/.claude/.mcp.json):
claude mcp add ruflo -- npx ruflo@latest mcp start
```

Then restart Claude Code. After restart, any Claude session can call `ruflo.*` tools (exact tool list discovered via `ToolSearch` post-restart).

### Step 2 — Fork 5-7 highest-value skills into `skills/sk-*/` (own the source)

Per the "work forever" requirement, MCP-only is fragile — upstream npm package changes or the package disappearing breaks Sanctum. The durable model = fork.

Candidate forks (subject to per-skill verification after MCP wires up):

| Ruflo capability | Sanctum skill folder | Why we fork |
|---|---|---|
| Swarm coordination (hierarchical / mesh / adaptive topologies) | `skills/sk-swarm-coord/` | Pair with `_shared-memory/knowledge/cross-agent-coordination.md` |
| Self-learning memory (SONA neural patterns) | `skills/sk-memory-compound/` | Augment the markdown brain with semantic recall |
| Vector memory (AgentDB + HNSW) | `skills/sk-vector-memory/` | Sanctum's librarian currently uses flat grep — vector is upgrade |
| GitHub automation (PR / branch / multi-repo) | `skills/sk-github-automation/` | Replace ad-hoc `git-toolkit.ps1` patterns |
| Code quality (test-gen, gap detection, diff risk) | `skills/sk-code-quality/` | Pair with `codex-companion` peer-review |
| Doc generation / changelog | `skills/sk-doc-gen/` | Pair with `scribe` daily-digest |
| Security automation (CVE scan, PII, prompt-injection) | `skills/sk-security-auto/` | Augment `auditor` bot |

Each fork follows the case-study gate per `_shared-memory/DIRECTIVES.md:7-19`:

1. Copy upstream file(s) into `skills/sk-<slug>/` + add authorship line:
   `> Author: Sinister Sanctum master agent (Claude) :: <date> :: forked from ruflo @ <commit-sha>`
2. Adapt to Sanctum conventions (purple accents, absolute paths, our env vars).
3. Write `_shared-memory/case-studies/<UTC>-<slug>.md` with 5 sections (what-it-is / strengths / weaknesses / better-than-found / recommendation = `KEEP-WITH-CHANGES`).
4. Add row to `skills/_INDEX.md` with `Source = ruflo:<their-slug>`, `Imported = <date>`, `Status = candidate`.
5. **STOP for operator thumb.** No promotion to `fixed` without the gate.

### Verification

After Step 1:
```
ToolSearch select:ruflo
# Expected: ruflo.* schemas returned
```

After Step 2 (per skill):
```bash
ls "D:/Sinister Sanctum/skills/sk-<slug>/"   # README.md + forked source
grep "$slug" "D:/Sinister Sanctum/skills/_INDEX.md"   # row with Source=ruflo:...
ls "D:/Sinister Sanctum/_shared-memory/case-studies/" | grep "$slug"   # verdict file
```

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 12:30 by Sinister Sanctum

Phase 0 verification (read-only WebFetch) confirms:
- URL `github.com/ruvnet/ruflo` resolves; project active
- License: MIT (safe to fork)
- Install: `claude mcp add ruflo -- npx ruflo@latest mcp start`
- Maintained by RuvNet
- Architecture matches Sanctum's existing patterns (swarm, inbox, persistent memory) — minimal adaptation needed

Operator has approved the plan that defines this integration (`C:\Users\Zonia\.claude\plans\review-everything-and-create-cryptic-rose.md`, Phases B + C). Step 1 (MCP wire-up) blocked on operator click. Step 2 (forks) blocked on Step 1 + operator thumbs-up per-skill via case-study workflow.

## See also

- `_shared-memory/external-imports/CANDIDATES.md` — the master list of imports
- `_shared-memory/external-imports/README.md` — the inflow-loop spec
- `_shared-memory/knowledge/cross-agent-coordination.md` — the existing Sanctum pattern Ruflo's swarm augments
- `_shared-memory/knowledge/codex-companion-usage.md` — peer-review pattern; Ruflo's code-quality skill pairs here
- `C:\Users\Zonia\.claude\plans\review-everything-and-create-cryptic-rose.md` — the approved plan
