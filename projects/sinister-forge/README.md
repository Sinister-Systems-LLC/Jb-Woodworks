# Sinister Forge

> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-21
> **Lane slug:** `sinister-forge`
> **Branch:** `agent/sinister-forge/<topic>`

Sinister-branded multi-LLM coding-agent harness. Mines jcode's best features (Rust speed, swarm coordination, multi-provider routing, semantic memory graph, mermaid side panels) + pairs with the full Sanctum stack (6 session contracts + 12 Sinister bots + Ruflo + Vault + RKOJ + auto-backup + multi-operator partition).

Operator directive 2026-05-21: *"yea i want everything from jcode paried with all our work to make our sessions start bat file on the new level. I want you to make a proejct out of this and complie all our skills etc, everything needed to work on it and eevrything needs to eventually link to RKOJ workstation. all our branding etc. but i want like all feateures of jcode that thing is fucking awesome"*.

## What we mine from jcode

| jcode feature | Forge equivalent | Why |
|---|---|---|
| TUI (Rust, ~14ms first-frame) | `forge-tui` Rust crate (deferred) | Operator can keep using the bat picker; TUI is a v2 nice-to-have |
| Swarm-mode (agents coordinate via local server) | Wires into existing `_shared-memory/cross-agent/` + `sinister-bus` heartbeats | Adds fast in-memory broadcast on top of filesystem source-of-truth |
| Semantic memory graph (auto-recall + background consolidation) | Ruflo `agentdb_*` (38+ tools already available) | Stop hand-rolling brain entries; wire Ruflo into cold-start contract |
| Multi-provider routing (Claude/Codex/Gemini/Ollama/LM Studio) | Launcher Q5 Agent Host + new `automations/agent-host-routing.md` | Formalize the routing tree per task type |
| Memory demo (`jcode-memory-demo.mp4`) | See `_shared-memory/plans/sinister-forge-2026-05-21/jcode-memory-feature.md` | Inspires the auto-recall pattern |
| OAuth flows for providers | Hand off to Vault MCP | Vault already owns secrets |
| Telemetry-as-research | DISABLED by default; opt-in writes to `_shared-memory/forge-telemetry/<UTC>.jsonl` | We don't ship operator data to any third-party Cloudflare worker |
| Side panels with inline mermaid | `mermaid-rs-renderer` (1jehuang's other win) subprocess | Apache/MIT, no Chromium dependency |

## What stays Sanctum-native

The launcher PS1 + 6 session contracts + 12 Sinister bots + Ruflo + Vault + RKOJ + the 9-project canonical list (Forge = #9) + auto-backup + me/eleno partition + OBLITERATUS at `D:\Research\obliteratus\` (AGPL-quarantined; subprocess invocation only).

## Architecture

```
  Desktop\Sinister Forge.bat
        │
        ▼
  automations\start-sinister-session.ps1  (-Project sinister-forge -Mode forge)
        │
        ▼
  Claude Code (or Codex via Q5) + session-contracts.md + Ruflo MCP + Vault MCP
        │
        ▼
  RKOJ Workstation :5077 (NEW Forge dashboard tab — pending R7 cross-agent ASK)
```

## Phase plan

| Phase | What | Status |
|---|---|---|
| PH0 | Scaffold (this commit) | ✅ |
| PH1 | Clone `mermaid-rs-renderer` to `D:\Research\` | pending |
| PH2 | Clone `agentgrep` to `D:\Research\` | pending |
| PH3 | Audit `Desktop\Github Research\` drops (continuous via watcher) | live |
| PH4 | Add `forge` mode to launcher BuiltinPhrases | pending |
| PH5 | RKOJ Forge dashboard tab (cross-agent ASK to rkoj) | pending |
| PH6 | Multi-provider routing contract (extends AUP-RESPECT) | pending |
| PH7 | `Sinister Forge.bat` on Desktop | ✅ this commit |
| PH8 | Operator smoke | pending |

## License

AGPL-3.0 (Sanctum operator preference). Code ported from jcode (MIT) re-licensed AGPL-3.0 with attribution in `NOTICES.md`. mermaid-rs-renderer (Apache 2.0) same.

## Cross-references

- `_shared-memory/plans/sinister-forge-2026-05-21/plan.md` — R1..R12 forward-plan
- `_shared-memory/plans/sinister-forge-2026-05-21/jehuang-audit.md` — full 1jehuang profile audit
- `automations/session-contracts.md` — 6 binding contracts Forge inherits
- `D:\Research\jcode\` — read-only reference clone
- `C:\Users\Zonia\Desktop\Github Research\jcode-0.12.3\` — operator's pre-downloaded copy
- `C:\Users\Zonia\Desktop\Github Research\mermaid-rs-renderer-0.2.2\` — operator's pre-downloaded copy
- `C:\Users\Zonia\Desktop\Github Research\jcode-memory-demo(3).mp4` — operator's reference video on jcode memory feature (audited at `_shared-memory/plans/sinister-forge-2026-05-21/jcode-memory-feature.md`)
