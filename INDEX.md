# Sinister Sanctum â€” INDEX

The map of what's in this repo + where to look for what. Read this first if
you're new (or you're a Claude session that just opened the folder).

## Top-level

| Path | What |
|---|---|
| `README.md` | Sanctum overview + pointer to SANCTUM.md |
| `SANCTUM.md` | **Canonical naming.** The 5 GitHub repos in the Sinister LLC universe + how they consume Sanctum. |
| `CONTRIBUTING.md` | For Leo + future collaborators â€” secret-scrub workflow + bot fleet quickstart |
| `LICENSE` | Placeholder; operator picks before any public push |
| `.gitignore` | Comprehensive (Python / Node / Android + secrets) |
| `INDEX.md` | This file |

## SESSION-START/ â€” cold-resume anchor

Read these IN ORDER when starting a fresh Claude session in this repo:

1. `README.md` â€” what this is + read order
2. `00-RULES.md` â€” TL;DR mandatory, delegation table, hard rules
3. `01-NETWORK.md` â€” 19-MCP-server discovery + bot-callable shortcuts
4. `02-OPERATOR-QUEUE.md` â€” what the operator is waiting on right now
5. `03-GOTCHAS.md` â€” sandbox classifier denies + green paths
6. `04-RECOVERY.md` â€” when things look wrong; drive-letter changes; daemon failures

## bots/ â€” the 12 Sinister Bots fleet

- `README.md` â€” fleet overview + per-bot one-liner + how to install
- `agents/` â€” **junction** to operator's `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\`. Edits in either place flow to both. 12 bot directories, each with `server.py + requirements.txt + README + SYSTEM-PROMPT + KNOWN-GOTCHAS + learned.md`.

## docs/ â€” design + reference

| Doc | Read for |
|---|---|
| `ARCHITECTURE.md` | 3-layer model + data flows |
| `SETUP.md` | fresh-machine bootstrap |
| `DEPLOYMENT.md` | per-project deploy + pre-deploy checklist |
| `AGENT-BOOTSTRAP.md` | every bot's cold-start protocol |
| `BOT-MEMORY-PROTOCOL.md` | absorb/learn/forget + audit |
| `MCP-NETWORK.md` | bot â†” base MCP integration map |
| `ALIVE-ARCHITECTURE.md` | the "alive memory" design |
| `MEMORY-CODEC-AND-CRYPTO.md` | codec dictionary + at-rest vault |
| `DRIVE-ENCRYPTION.md` | VeraCrypt container plan |

## automations/ â€” operator-runnable scripts

| Script | Purpose |
|---|---|
| `git-toolkit.ps1` | 10 subcommands: init / remote-set / safe-push / pre-commit-install / release / ci-bootstrap / doc-bootstrap / scrub / gitignore-tune / status-summary |
| `secret-scrub.ps1` | Pre-commit secret pattern + danger-filename scan; blocks on any hit |
| `migrate-projects.ps1` | Junction product-repo sources into `projects/` view |
| `hub-scripts/` | **junction** to `D:\Sinister\Sinister Skills\08_AUTOMATIONS\` (the hub's own scripts: activate-everything, verify-backups, check-hetzner-state, etc.) |

## projects/ â€” placeholder

Sanctum does NOT vendor the product repos (Snap EMU / TikTok EMU / Control
Center / Kernel APK). When operator runs `migrate-projects.ps1`, the names get
junctioned in here as a navigation aid; the actual code stays in each repo.

## _vault/ â€” master Obsidian vault

Open `_vault/_index.md` in Obsidian to navigate the LLC scope visually with
wiki-links into per-project vaults + TODOs + bots + docs.

## .github/ â€” CI

`.github/workflows/bots-smoke.yml` â€” syntax-check every bot server.py + smoke-test
the shared `bot_memory` + `codec` + `crypto` modules. Runs on PR + push to main.

## What's NOT here (operator-private; never in Sanctum)

- LetsText, JOKR, library-of-jokr-mirror
- `09_REFERENCE/yurikey-roster.md`
- `01_MEMORY/_consolidated/`
- `_backups/`, `_logs/`, `runtime-state/`
- Per-project source under `01_MEMORY/<project>/_to-copy-to-source/` (those are operator-side stubs, copied into product repos via `Prepare-Migration.bat`)

## TL;DR

- **How we won:** This INDEX is the one-page map. Every doc is exactly one click away.
- **What you need to do:** Pick LICENSE; set GitHub remote; run `git-toolkit.ps1 safe-push .` from `D:\Sinister Sanctum\` when ready.
