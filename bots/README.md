# Sinister Bots â€” fleet overview (LLC scope)

12 MCP-compatible agents that handle recall, audit, classification, scrape,
summarize, and backup tasks across the Sinister projects. Operator pays for
Claude Opus only on creative + multi-step reasoning work; everything else
routes here.

## The fleet

| Bot | Tier | Cost/call | Role |
|---|---|---|---|
| sentinel | 1 (Py) | $0 | Date alarms (Yurikey expiry, deadlines) |
| translator | 1 (Py) | $0 | MCP-tool catalog search across 200+ tools |
| watcher | 1 (Py) | $0 | Source-drift detection (sha + mtime) |
| auditor | 1 (Py) | $0 | Secrets + dedup + freshness scan |
| sinister-bus | 1 (Py) | $0 | Orchestrator + runlog surface + network discovery |
| custodian | 1 (Py) | $0 | Active backup to `D:\_backups\` |
| stealth-browser | 1 (Py + nodriver) | $0 | Undetected Chromium automation |
| triage | 2 (Ollama) | $0 | File classifier (rules fallback) |
| librarian | 2 (Ollama + FAISS) | $0 | RAG over 8,500+ .md archive |
| researcher | 2 (Ollama) | $0 | scrape -> Ollama summarize chain |
| scribe | 3 (Haiku) | ~$0.02 | Daily-digest writer |
| curator | 3 (Haiku) | ~$0.05 | Code-library extraction scout |
| **hacker** *(planned)* | 1 (shell) | $0 | 183-tool pentest dispatcher; pending operator OK |

After install: 19 MCP servers total (12 bots + 7 base servers the operator runs separately).

## Install

```powershell
cd 'D:\Sinister Sanctum'
.\automations\activate-everything.ps1   # registers bots + scaffolds backup
```

Restart Claude Code after. Verify with `sinister-bus.list_network` (expect 19 endpoints).

## Per-bot memory

Each bot directory has:
- `server.py` â€” the MCP server (FastMCP)
- `requirements.txt` â€” minimal deps
- `README.md` â€” operator-facing
- `SYSTEM-PROMPT.md` â€” canonical role (loaded by Tier-2 + Tier-3 bots into LLM prompts)
- `KNOWN-GOTCHAS.md` â€” bot-specific landmines + workarounds
- `learned.md` â€” persisted absorbed facts (operator-reviewable; one fact per line)
- For Tier-3 bots: prompt-caching is wired so first call/5min pays full input, repeats pay 1/10th

See `docs/BOT-MEMORY-PROTOCOL.md` for how absorption works (every `<bot>.absorb(fact, source)` is audit-logged).

## Bot-to-bot integration

See `docs/MCP-NETWORK.md` for the integration map. Highlights:
- `sentinel.check_urgent` -> `eve.notify.telegram` (operator-wired) on critical alarms
- `librarian.search` + `eve.memory.search` -> merged super-search
- `researcher.summarize_url` -> `eve.memory.write` (cache scrapes)
- `custodian` errors -> bus runlog -> scribe's daily digest "What needs attention" section

## Layout under this directory

```
bots/
â”œâ”€â”€ README.md                    you are here
â”œâ”€â”€ _shared/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ bot_memory.py            absorption + retrieval + heartbeat
â”‚   â””â”€â”€ runlog.py                shared runlog manifest reader
â”œâ”€â”€ sentinel/   translator/   watcher/   auditor/   custodian/   sinister-bus/   stealth-browser/
â”œâ”€â”€ triage/   librarian/   researcher/
â”œâ”€â”€ scribe/   curator/
â””â”€â”€ (hacker/ â€” pending)
```

In the LLC repo, this dir is a junction back to
`D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\`. Edits in either place
flow to both.

## TL;DR

- **How we won:** Bot fleet is one MCP-compatible monorepo. Adding a new bot follows the same template every time.
- **What you need to do:**
  - Run `automations\activate-everything.ps1` after first checkout.
  - Set `ANTHROPIC_API_KEY` user env var for Tier-3 bots.
  - Optional: `docker compose up -d` in `12_LLM_ORCHESTRATION/docker/` for Tier-2 bots.
