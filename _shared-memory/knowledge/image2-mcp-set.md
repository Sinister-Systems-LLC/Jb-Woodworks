# Topic: Image 2 MCP set — Playwright + Context7 + Sequential-thinking + KG-memory

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

**Slug:** image2-mcp-set
**First discovered:** 2026-05-19 13:30 by Sinister Sanctum
**Last updated:** 2026-05-19 13:30 by Sinister Sanctum
**Status:** workaround (flips to `fixed` after operator runs `install-mcp-servers.ps1` + Claude Code restart)
**Tags:** mcp, playwright, context7, sequential-thinking, kg-memory, image2, telegram-directive, vendor-mcp, install-script

## Problem

Operator's 2026-05-19 23:25 Telegram directive listed six items as "queue the new directives":

1. **Mcp** (umbrella label)
2. **Playwright** — browser automation
3. **Context7** — live library docs (kill hallucinations)
4. **Sequential thinking** — reasoning scaffold
5. **Codex to challenge Claude** — already shipped (Codex Companion at `tools/codex-companion/`)
6. **Knowledge graph memory** — cross-session persistent KG

Items 2-4 + 6 are all vendor MCP servers that complement Sanctum's existing 19-bot fleet but aren't yet wired. Without them:

- **Playwright:** stealth-browser covers basic automation but lacks structured page interactions (typed selectors, multi-page sequences, recorded traces, screenshot diff). For dashboard testing, payment-flow validation, captcha-laden auth flows.
- **Context7:** when Claude reasons about a library API (npm package, Python lib, .NET, etc.), it relies on its training cutoff. Context7 fetches the LIVE docs at prompt time, killing the "I'm using deprecated v2 API for v5 code" class of hallucination.
- **Sequential thinking:** an explicit reasoning-chain primitive. Useful for complex multi-step prompts where the operator wants to see the decomposition rather than trusting Claude's implicit chain-of-thought.
- **KG-memory:** stores entities + relations in a structured graph (vs. the markdown Sanctum brain which is unstructured). Persists across sessions. Best for "remember the relationships between these 50 actors over 10 sessions."

## Why it happens

The install script (`D:\Sinister Sanctum\automations\install-mcp-servers.ps1`) is **already built and idempotent** (per the file header dated 2026-05-19). It:

1. Backs up `~/.claude/.mcp.json` to `.mcp.json.bak-<UTC>` BEFORE touching it.
2. Adds each of the 4 servers under `mcpServers` (skips if already present).
3. Pre-creates the KG-memory storage path `D:\Sinister\Sinister Skills\01_MEMORY\_kg-memory\` so the memory server has somewhere to write `graph.json`.
4. Writes back via `UTF8Encoding(false)` (no BOM — required for `.mcp.json` parser).
5. Prints the post-install action: **operator must restart Claude Code**.

The reason Image 2's set isn't yet in `.mcp.json`: **operator hasn't run the script**. Lane discipline forbids master from running it (Register-style writes to `.mcp.json` — a bad entry kills every active session; operator owns this file).

## Fix or workaround

### Step 1 — operator runs the install script (3 minutes)

```powershell
# From any PowerShell window:
& "D:\Sinister Sanctum\automations\install-mcp-servers.ps1"
```

The script prompts to keep open or auto-closes in 15s. On success it prints `[ ADD ] playwright`, `[ ADD ] context7`, `[ ADD ] sequential-thinking`, `[ ADD ] memory` (or `[SKIP]` if already present).

### Step 2 — restart Claude Code

Quit Claude Code completely (not just close the window — kill the tray process). Reopen. The 4 new MCP servers load.

### Step 3 — master verifies in next session

```
ToolSearch +playwright
ToolSearch +context7
ToolSearch +sequentialthinking
ToolSearch +memory
```

Each should return tool schemas. If any returns no matches, check `~/.claude/.mcp.json` for the entry, and verify `npx --version` works in the PowerShell env (the servers spawn `npx -y <package>` per the script).

## When to use each (decision tree)

```
Need to interact with a web page?
├── Just need raw HTML / single page → researcher.summarize_url
├── Need anti-detect, undetected Chromium → stealth-browser
├── Need full Playwright API (selectors, recording, multi-page flows) → playwright
└── Need authenticated browser (logged-in session) → stealth-browser → bridge via cookies → playwright

Need to know how a library API works?
├── Mentioned in our brain → grep _shared-memory/knowledge/
├── Standard / older lib (cutoff-safe) → just reason from training
├── Recent / fast-moving lib (Next.js, Astro, etc.) → context7
└── Internal Sanctum tool → tools/<slug>/README.md

Working on a complex multi-step problem?
├── Linear (do X then Y then Z) → just reason directly
├── Branchy (multiple alternatives to evaluate) → sequential-thinking
├── Architecture / design decision → Plan agent (subagent_type=Plan)
└── Cross-agent coordination → inbox + cross-agent-coordination pattern

Need to remember something across sessions?
├── Fix / gotcha / workaround → _shared-memory/knowledge/<slug>.md (markdown brain)
├── Operator directive → _shared-memory/DIRECTIVES.md
├── Progress / milestone → _shared-memory/PROGRESS/<agent>.md
├── Structured entities + relations → memory MCP (KG)
└── Per-bot durable facts → bot.absorb (bot_memory skill)
```

## KG-memory storage path

The script sets `MEMORY_FILE_PATH=D:\Sinister\Sinister Skills\01_MEMORY\_kg-memory\graph.json`. The memory server creates the file on first use. Schema is a JSON-formatted graph of entities + relations. Read upstream at `github.com/modelcontextprotocol/servers/tree/main/src/memory` for the entity/relation schema.

## What they don't replace

- **They don't replace `sinister-bus`** — bus is the orchestrator + audit + memory garden. The new servers are capabilities, not replacements.
- **They don't replace the Sanctum brain** (`_shared-memory/knowledge/`) — the brain stores prose patterns + decisions + reasoning. KG-memory stores structured entities. Both have value.
- **They don't replace `Codex Companion`** — Codex is peer-review (different model family for blind-spot coverage). Sequential-thinking is reasoning decomposition.
- **They don't replace `stealth-browser`** — stealth-browser is the anti-detect tier. Playwright is the structured-API tier. Use both.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum

First brain entry for this set. install-mcp-servers.ps1 confirmed idempotent + ready. Operator has not yet run it (per heartbeat + operator-action-queue audit). When Phase B (Image 2 wire-up) completes, this entry's status flips to `fixed` and the corresponding `externals` rows in `skills/_REGISTRY.yaml` flip from `scouted` to `shipped`.

## Related topics

- [ruflo-mcp-integration](./ruflo-mcp-integration.md) — companion external-import (Phase B + C)
- [cross-agent-coordination](./cross-agent-coordination.md) — the inbox patterns the new MCPs plug into
- [codex-companion-usage](./codex-companion-usage.md) — Codex (the 5th Image 2 item) is already shipped
- `_shared-memory/external-imports/CANDIDATES.md` — master list of external imports
- `skills/_REGISTRY.yaml` — these 4 servers live under `externals:`
- `automations/install-mcp-servers.ps1` — the install script that wires them
