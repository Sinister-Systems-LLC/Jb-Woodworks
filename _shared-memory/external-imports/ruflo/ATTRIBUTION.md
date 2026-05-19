> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Ruflo — attribution + integration notes

## Upstream

| Field | Value |
|---|---|
| Repo | https://github.com/ruvnet/ruflo |
| Owner | RuvNet (`@ruvnet`) |
| License | MIT |
| Pinned commit SHA | `c292e5fcf563b1639ea2ce7842c8f4a110c3ad39` |
| Pinned commit date | `2026-05-19T02:18:38Z` |
| Pinned commit message | `feat: ADR-123 — RuFlo Graph Intelligence Engine (sublinear integration across 12 wedges, published alpha.1)` |
| Latest published version | `v3.7.0-alpha.33` (2026-05-13) |
| Description | "The leading agent orchestration platform for Claude. Deploy intelligent multi-agent swarms, coordinate autonomous workflows, and build conversational AI systems." |

## Install command (operator-clicked; master never edits `~/.claude/.mcp.json`)

```powershell
claude mcp add ruflo -- npx ruflo@latest mcp start
```

After install: **restart Claude Code** so the MCP server loads. Verify with `ToolSearch select:ruflo` in a fresh session.

## What we'll take (Phase C forks; per-skill case-study gate)

Phase B (MCP wire-up) makes the entire Ruflo surface callable from any Claude session. Phase C forks the highest-value pieces into `D:\Sinister Sanctum\skills\sk-<slug>\` so Sanctum owns the source even if upstream changes or disappears.

Candidate forks (subject to per-skill verification once Ruflo's tools enumerate post-restart):

| Ruflo capability (upstream) | Sanctum fork target | Why we fork |
|---|---|---|
| Swarm coordination (hierarchical / mesh / adaptive topology) | `skills/sk-swarm-coord/` | Augments `cross-agent-coordination.md` patterns |
| Self-learning memory (SONA neural patterns) | `skills/sk-memory-compound/` | Pair with the markdown Sanctum brain |
| Vector memory (AgentDB + HNSW indexing) | `skills/sk-vector-memory/` | Upgrade librarian's flat grep to semantic recall |
| GitHub automation (PR / branch / multi-repo) | `skills/sk-github-automation/` | Replace ad-hoc `git-toolkit.ps1` patterns |
| Code quality (test-gen, gap detection, diff risk scoring) | `skills/sk-code-quality/` | Pair with `codex-companion` peer-review |
| Doc generation / changelog | `skills/sk-doc-gen/` | Pair with `scribe` daily-digest |
| Security automation (CVE scan, PII detection, prompt-injection blocking) | `skills/sk-security-auto/` | Augment `auditor` bot |

Each fork carries:

```markdown
> **Author:** Sinister Sanctum master agent (Claude) :: <date> :: forked from ruflo @ c292e5fcf563b1639ea2ce7842c8f4a110c3ad39
> **License:** MIT (upstream); Sanctum modifications dual-licensed under the Sanctum LICENSE.
> **What we took:** <one-line description of the specific files / directories>
```

Each fork goes through the case-study workflow per `_shared-memory/DIRECTIVES.md` (5-section structured review → operator 👍/👎 → KEEP-WITH-CHANGES / ARCHIVE / REPLACE).

## Notable upstream details

- **Architecture matches Sanctum's existing patterns** — swarm coordination, persistent memory, inbox-style messaging, multi-agent federation. Minimal adaptation needed for our purple-accent + absolute-path + BOM-encoded-PS1 conventions.
- **Security primitives:** AIDefence module, PII-gated data flow (14 detection types), mTLS + ed25519 challenge-response for agent federation, behavioral trust scoring. The security automation skill is a strong candidate for `skills/sk-security-auto/` (augments our `auditor` bot).
- **Plugin namespace:** Ruflo uses `@claude-flow/plugin-*` for its 32 native plugins. Don't fork the namespace; only fork files/patterns we extract into `skills/sk-*/`.
- **Tooling stack:** Web UI at `flo.ruv.io`, GOAP planner at `goal.ruv.io`, 12 background workers. Not all of this is in scope for Sanctum — only the agent + skill primitives.

## License compliance

MIT license requires:
- Preserve copyright notice + permission notice in any copied files.
- Acknowledge upstream attribution (this file does that).
- No warranty disclaimer modification.

Each forked file at `skills/sk-<slug>/<file>` MUST:
1. Include the original MIT notice if present in the upstream file.
2. Append a Sanctum authorship line below it (per the format above).
3. Reference this ATTRIBUTION.md from `skills/sk-<slug>/README.md`.

## Rollback / unforking

If Phase C produces a fork that doesn't fit:
1. `git mv skills/sk-<slug>/ _archive/skills/sk-<slug>/` (preserves history; reversible).
2. Add `_archive/skills/sk-<slug>/_archived.md` with the reason file (per case-study workflow).
3. Update `skills/_INDEX.md`: flip status to `archived`.
4. Operator can promote back later with the reverse `git mv`.

## See also

- `_shared-memory/external-imports/CANDIDATES.md` — the master list of imports
- `_shared-memory/external-imports/README.md` — the inflow-loop spec
- `_shared-memory/knowledge/ruflo-mcp-integration.md` — brain entry for the integration
- `_shared-memory/DIRECTIVES.md` — case-study workflow gate
- `skills/SECURITY.md` — fleet-wide security overview (which Ruflo's security automation augments)
- `C:\Users\Zonia\.claude\plans\review-everything-and-create-cryptic-rose.md` — the approved 8-phase plan
- `C:\Users\Zonia\.claude\plans\i-want-you-to-eventual-haven.md` — this session's sharper plan
