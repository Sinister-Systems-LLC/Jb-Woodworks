# Sinister CLI Naming Convention — `sinister <subcommand>` umbrella

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Operator directive (verbatim 2026-05-21):** *"our commands will be sinister then the command"* (with jcode `jcode login --provider claude` screenshot)
> **Status:** doctrine, standing-rule

## The rule

Every operator-facing CLI command in the Sinister fleet uses the form:

```
sinister <subcommand> <args...>
```

NOT per-tool standalone command names. NOT verb-noun other orderings. NOT `sinister-<thing>` (the hyphenated form survives as the implementation entry-point but is hidden from operator UX).

## Why

- **Discoverability.** Operator types `sinister` → sees every subcommand. One thing to memorize.
- **jcode-pattern parity.** Operator picked this style after seeing jcode's `jcode <cmd>` UX (`jcode login --provider claude`, `jcode swarm spawn`, `jcode memory write`).
- **Plugin-friendly.** Drop a new tool with the right entry-point; umbrella auto-discovers (v0.2.0).
- **Brand-consistent.** Every command surface carries the Sinister brand explicitly.

## Implementation map

| Operator UX | Implementation |
|---|---|
| `sinister memory ...` | `tools/forge-memory-bridge/` |
| `sinister swarm ...` | `tools/sinister-swarm/` |
| `sinister graph ...` | `tools/memory-graph-render/` |
| `sinister login --provider <X>` | `tools/sinister-login/` (v0.2.0) |
| `sinister freeze ...` | `projects/sinister-freeze/source/` (future) |
| `sinister term ...` | `projects/sinister-term/source/term/` |
| `sinister forge ...` | `projects/sinister-forge/source/forge/` |
| `sinister help [subcmd]` | umbrella built-in |
| `sinister version` | umbrella built-in (per-tool versions) |

## Tool-author rules

If you ship a new tool that exposes an operator-facing CLI:

1. Pick a subcommand name (one word, lowercase, hyphen-free preferred).
2. Implement a `main(argv: list[str]) -> int` callable in your package.
3. Add an entry to `tools/sinister-cli/sinister_cli/__main__.py::SUBCOMMAND_MAP`.
4. **Also keep** your standalone CLI entry-point (`yourtool-cli`) for power-users + scripting — but document `sinister <subcmd>` as the canonical form.
5. Help text for `sinister yoursubcmd --help` should be the same as `yourtool-cli --help` (delegated automatically).

## Anti-patterns this forbids

- ❌ Naming a CLI `sinister-foo` and asking operator to remember it (use `sinister foo` instead)
- ❌ Five different CLI binaries (`forge-memory`, `memory-graph-render`, `sinister-swarm`, etc.) without an umbrella
- ❌ Hidden subcommands not listed in `sinister help`
- ❌ Hard imports requiring every backend installed for ANY subcommand (use graceful-degrade dispatch)
- ❌ Inconsistent flag patterns across subcommands (where possible, follow jcode's `--provider <X>` / `--mode <X>` style)

## Login providers (jcode-login parity targets)

Per operator screenshot — these should land in `sinister login --provider <X>`:

- claude (Anthropic API + Claude Code)
- openai (ChatGPT / GPT-4o / Codex)
- gemini (Google)
- copilot (GitHub Copilot)
- azure (Azure OpenAI)
- alibaba-coding-plan
- fireworks
- minimax
- lmstudio (local)
- ollama (local)
- openai-compatible (custom base URL + key OR no key for local LM servers)

Each provider's tokens land in **Sinister Vault** (`tools/sinister-vault/`) at `vault://providers/<provider>` — never plaintext in env vars per data-sovereignty doctrine.

## Composes with

- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md` — disk-first + MCP-optional applies; dispatcher is a thin import-wrapper
- `_shared-memory/knowledge/jcode-feature-matrix.md` — every row that ships a CLI binds to the umbrella
- `_shared-memory/knowledge/sinister-freeze-project-doctrine.md` — Joe-facing commands also follow `sinister <subcmd>` (no plain-English overrides at the CLI; plain-English is the UX layer ON TOP)
- `tools/sinister-cli/README.md` — implementation reference

## When to revisit

- Operator picks a different naming convention → re-rule + migrate
- A subcommand needs to be removed → flag as `[DEPRECATED]` in help for 1 release, then drop
- A new top-level concept needs a slot (e.g. `sinister vault ...`, `sinister cron ...`) → add to map + brain entry update
