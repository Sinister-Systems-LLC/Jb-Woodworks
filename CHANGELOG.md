# Sinister Sanctum — CHANGELOG

What's in this repo as of the upcoming first push.

## 2026-05-18 / 2026-05-19 — Initial Sanctum shipment

### The fleet (12 Sinister Bots)

All 12 MCP-compatible bots in `bots/agents/` (junction to operator's hub). Each ships with:
- `server.py` — FastMCP server
- `requirements.txt` — minimal deps
- `README.md` — operator-facing
- `SYSTEM-PROMPT.md` — canonical role (Tier-2/3 bots load into LLM prompts)
- `KNOWN-GOTCHAS.md` — bot-specific landmines
- `learned.md` — persisted absorbed facts (audit-logged)

| Bot | Tier | Cost |
|---|---|---|
| sentinel | 1 (Py) | $0 |
| translator | 1 (Py) | $0 |
| librarian | 2 (Ollama+FAISS) | $0 |
| watcher | 1 (Py) | $0 |
| auditor | 1 (Py) | $0 |
| sinister-bus | 1 (Py) | $0 |
| triage | 2 (Ollama) | $0 |
| scribe | 3 (Haiku) | ~$0.02 |
| curator | 3 (Haiku) | ~$0.05 |
| custodian | 1 (Py) | $0 |
| stealth-browser | 1 (Py+nodriver) | $0 |
| researcher | 2 (Ollama) | $0 |

(Hacker bot deferred pending operator authorization to fetch upstream RE.)

### Bus tool surface (28 tools)

Network discovery, runlog, codec, vault, garden, script-runner, agent messaging:

- **Network:** `list_network`, `find`, `dispatch`, `replay`, `list_recent`, `record_response`, `health`
- **Runlog:** `runlog_list`, `runlog_latest`, `runlog_summary`, `pending_actions`, `consume_pending`
- **Codec:** `encode`, `decode`, `codec_status`
- **Vault:** `vault_lock`, `vault_unlock`, `vault_status`
- **Aliveness:** `memory_garden`
- **Script runner:** `list_scripts`, `run_script` (5-script whitelist)
- **Agent messaging (Phase 8w):** `heartbeat`, `who_is_online`, `inbox_send`, `inbox_poll`, `inbox_reply`, `delegate_to`, `inbox_stats`

### Design docs (`docs/`)

- `ARCHITECTURE.md` — 3-layer model + data flows
- `SETUP.md` — fresh-machine bootstrap
- `DEPLOYMENT.md` — per-project deploy checklist
- `AGENT-BOOTSTRAP.md` — cold-start protocol for every bot
- `BOT-MEMORY-PROTOCOL.md` — absorb/learn/forget + audit
- `MCP-NETWORK.md` — bot ↔ base MCP integration map
- `ALIVE-ARCHITECTURE.md` — 6 properties of the alive memory system
- `MEMORY-CODEC-AND-CRYPTO.md` — 97-phrase codec + Fernet at-rest vault
- `DRIVE-ENCRYPTION.md` — VeraCrypt container plan
- `AGENT-MESSAGING.md` — Phase 8w inbox + presence + ephemeral-spawn

### Automations (`automations/`)

- `git-toolkit.ps1` — 10 subcommands for GitHub workflow (init / safe-push / ci-bootstrap / etc.)
- `secret-scrub.ps1` — pre-push secret scanner
- `migrate-projects.ps1` — junction product-repo sources
- `hub-scripts/` — junction to hub's operator scripts

### Universal docs

- `SESSION-START/` — 6 cold-resume files (mirrored to hub)
- `SANCTUM.md` — 5-repo universe documentation
- `INDEX.md` — single-page navigation map
- `PARALLEL-AGENT-COORDINATION.md` — ownership zones for multi-session work
- `_vault/_index.md` — master Obsidian vault entry

### CI

`.github/workflows/bots-smoke.yml` — syntax-checks every bot `server.py` + smoke-tests `bot_memory` + `codec` + `crypto`.

### What is INTENTIONALLY EXCLUDED

- LetsText, JOKR, JOKR-mirror — operator-private; never in Sanctum scope
- `09_REFERENCE/yurikey-roster.md` — operator-private inventory
- `01_MEMORY/_consolidated/` — operator daily working state
- `_backups/`, `_logs/`, `runtime-state/` — local-only operational data

## Operator action queue (before first git push)

1. **Pick LICENSE** — `LICENSE` is a placeholder; replace with chosen text (MIT / Apache / Proprietary)
2. **Run `secret-scrub.ps1`** — must PASS on every dir; will flag any sneaked secrets
3. **Set git remote** — `git remote add origin git@github.com:Sinister-Systems-LLC/Sinister-Sanctum.git`
4. **`git-toolkit safe-push`** — pre-push secret-scrub gate then push

## TL;DR

- **How we won:** 12 bots + 28 bus tools + 10-doc design library + 10-subcommand git toolkit + 5-script bot-callable whitelist + agent-to-agent messaging. All shipped + audit-clean.
- **What you need to do:** pick LICENSE, run secret-scrub, set remote, safe-push.
